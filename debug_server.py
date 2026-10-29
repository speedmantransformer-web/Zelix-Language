"""Line-oriented debug control channel for the Zelix interpreter."""

from __future__ import annotations

import contextlib
import json
import queue
import re
import sys
import threading
from pathlib import Path
from typing import Any


class DebuggerStopped(Exception):
    pass


class DebugController:
    def __init__(
        self,
        source_path: Path,
        input_stream: Any = None,
        output_stream: Any = None,
        stop_on_entry: bool = True,
    ):
        self.source_path = source_path.resolve()
        self.input_stream = input_stream or sys.stdin
        self.output_stream = output_stream or sys.stdout
        self.commands: queue.Queue[dict[str, Any] | None] = queue.Queue()
        self.output_lock = threading.Lock()
        self.state_lock = threading.Lock()
        self.breakpoints: set[int] = set()
        self.frames: list[dict[str, Any]] = []
        self.mode = "entry" if stop_on_entry else "continue"
        self.origin_line = 0
        self.origin_depth = 0
        self.pause_requested = False
        self.started = False
        self.exception_stack: list[dict[str, Any]] | None = None
        self.configured = threading.Event()
        self.reader = threading.Thread(target=self._read_commands, daemon=True)

    def start(self) -> None:
        self.reader.start()

    def send(self, message: dict[str, Any]) -> None:
        with self.output_lock:
            self.output_stream.write(json.dumps(message, ensure_ascii=False) + "\n")
            self.output_stream.flush()

    def _read_commands(self) -> None:
        for raw in self.input_stream:
            try:
                message = json.loads(raw)
            except json.JSONDecodeError:
                self.send({"event": "error", "message": "Invalid debugger command"})
                continue
            if isinstance(message, dict):
                self.commands.put(message)
                if message.get("command") == "configure":
                    self.configured.set()
        self.commands.put(None)
        self.configured.set()

    def wait_until_configured(self) -> None:
        self.configured.wait()

    def push_frame(self, name: str, env: dict[str, Any], line: int) -> None:
        self.frames.append({"name": name, "env": env, "line": line})

    def pop_frame(self) -> None:
        if len(self.frames) > 1:
            self.frames.pop()

    @staticmethod
    def _json_value(value: Any) -> Any:
        if value is None or isinstance(value, (str, int, float, bool)):
            return value
        return repr(value)

    def _snapshot(self, line: int, env: dict[str, Any]) -> list[dict[str, Any]]:
        if not self.frames:
            self.push_frame("main", env, line)
        self.frames[-1]["line"] = line
        return [
            {
                "name": frame["name"],
                "line": frame["line"],
                "locals": {
                    str(name): self._json_value(value)
                    for name, value in frame["env"].items()
                },
            }
            for frame in reversed(self.frames)
        ]

    def capture_exception(self) -> None:
        if self.frames:
            frame = self.frames[-1]
            self.exception_stack = self._snapshot(frame["line"], frame["env"])

    def _apply_command(self, command: dict[str, Any]) -> None:
        action = command.get("command")
        if action == "breakpoints":
            lines = command.get("lines", [])
            with self.state_lock:
                self.breakpoints = {
                    line for line in lines
                    if isinstance(line, int) and line > 0
                }
        elif action == "resume":
            mode = command.get("mode")
            if mode not in {"continue", "next", "stepIn", "stepOut"}:
                self.send({"event": "error", "message": "Unsupported debugger step mode"})
                return
            with self.state_lock:
                self.mode = mode
                self.origin_line = int(command.get("line", 0))
                self.origin_depth = int(command.get("depth", 0))
                self.pause_requested = False
        elif action == "configure":
            return
        elif action == "pause":
            with self.state_lock:
                self.pause_requested = True
        elif action == "terminate":
            raise DebuggerStopped()

    def _drain_commands(self) -> None:
        while True:
            try:
                command = self.commands.get_nowait()
            except queue.Empty:
                return
            if command is None:
                raise DebuggerStopped()
            self._apply_command(command)

    def _stop_reason(self, line: int, depth: int) -> str | None:
        with self.state_lock:
            if not self.started:
                self.started = True
                if self.mode == "entry":
                    return "entry"
            if self.pause_requested:
                self.pause_requested = False
                return "pause"
            if self.mode == "stepIn":
                return "step"
            if self.mode == "next" and depth <= self.origin_depth and line != self.origin_line:
                return "step"
            if self.mode == "stepOut" and depth < self.origin_depth:
                return "step"
            if self.mode == "continue" and line in self.breakpoints:
                return "breakpoint"
        return None

    def before_statement(self, line: int, env: dict[str, Any]) -> None:
        self._drain_commands()
        depth = max(0, len(self.frames) - 1)
        reason = self._stop_reason(line, depth)
        if reason is None:
            return

        frames = self._snapshot(line, env)
        self.send({
            "event": "stopped",
            "reason": reason,
            "line": line,
            "stack": frames,
        })
        while True:
            command = self.commands.get()
            if command is None:
                raise DebuggerStopped()
            self._apply_command(command)
            if command.get("command") in {"resume", "terminate"}:
                return

    def program_output(self, text: str) -> None:
        if text:
            self.send({"event": "output", "category": "stdout", "output": text})


class DebugOutput:
    def __init__(self, controller: DebugController):
        self.controller = controller

    def write(self, text: str) -> int:
        self.controller.program_output(text)
        return len(text)

    def flush(self) -> None:
        pass


def run_debug_server(source_path: str | Path, stop_on_entry: bool = True) -> int:
    path = Path(source_path).resolve()
    controller = DebugController(path, stop_on_entry=stop_on_entry)
    controller.start()
    controller.wait_until_configured()
    try:
        from zelix import Interpreter

        interpreter = Interpreter(debugger=controller)
        with contextlib.redirect_stdout(DebugOutput(controller)):
            interpreter.run_file(path)
    except DebuggerStopped:
        controller.send({"event": "terminated", "exitCode": 0})
        return 0
    except Exception as exc:
        message = str(exc)
        match = re.search(r"\bLine\s+(\d+):", message)
        line = int(match.group(1)) if match else (
            controller.frames[-1]["line"] if controller.frames else 1
        )
        controller.send({
            "event": "exception",
            "message": message,
            "line": line,
            "stack": controller.exception_stack or controller._snapshot(
                line,
                controller.frames[-1]["env"] if controller.frames else {},
            ),
        })
        controller.send({"event": "terminated", "exitCode": 1})
        return 1
    controller.send({"event": "terminated", "exitCode": 0})
    return 0
