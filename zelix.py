#!/usr/bin/env python3
"""Zelix 0.2.0: a line-oriented interpreter and native compiler."""

from __future__ import annotations
import argparse
import asyncio
import ast
import concurrent.futures
from contextvars import ContextVar
import operator
import queue
import re
import sys
import threading
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Protocol

from compiler import CompileError, compile_file, emit_ir_file, validate_file, validate_source
from game_backend import GAME_FUNCTIONS
from project import ProjectError, init_project, install_project, project_entry, resolve_project_source
from syntax import (
    Assign, Await, Binary, Call, CallStatement, Create, Display, Expr, If, Input, Lexer,
    Literal, RangeLoop, Repeat, Return, Spawn, Stmt, Unary, Variable, While,
    parse_source,
)
from typesys import TypeChecker, TypeCheckError

VERSION = "0.3.0"

class ZelixError(Exception):
    pass

@dataclass
class Function:
    name: str
    params: list[str]
    body: list[Stmt]
    line: int
    is_async: bool = False

class ReturnSignal(Exception):
    def __init__(self, value: Any):
        self.value = value


class Channel:
    def __init__(self, capacity: int):
        self.messages: queue.Queue[Any] = queue.Queue(maxsize=capacity)
        self.closed = False
        self.lock = threading.Lock()
        self.closed_event = threading.Event()

    def send(self, value: Any, line: int) -> None:
        while True:
            with self.lock:
                if self.closed:
                    raise ZelixError(f"Line {line}: Cannot send to a closed channel")
                try:
                    self.messages.put_nowait(value)
                    return
                except queue.Full:
                    pass
            self.closed_event.wait(0.01)

    async def async_send(self, value: Any, line: int) -> None:
        while True:
            with self.lock:
                if self.closed:
                    raise ZelixError(f"Line {line}: Cannot send to a closed channel")
                try:
                    self.messages.put_nowait(value)
                    return
                except queue.Full:
                    pass
            await asyncio.sleep(0.001)

    def receive(self, line: int) -> Any:
        while True:
            try:
                return self.messages.get(timeout=0.1)
            except queue.Empty:
                with self.lock:
                    if self.closed:
                        raise ZelixError(f"Line {line}: Channel is closed and empty")

    async def async_receive(self, line: int) -> Any:
        while True:
            try:
                return self.messages.get_nowait()
            except queue.Empty:
                with self.lock:
                    if self.closed:
                        raise ZelixError(f"Line {line}: Channel is closed and empty")
                await asyncio.sleep(0.001)

    def close(self, line: int) -> None:
        with self.lock:
            if self.closed:
                raise ZelixError(f"Line {line}: Channel is already closed")
            self.closed = True
            self.closed_event.set()

class Debugger(Protocol):
    def before_statement(self, line: int, env: dict[str, Any]) -> None: ...
    def push_frame(self, name: str, env: dict[str, Any], line: int) -> None: ...
    def pop_frame(self) -> None: ...
    def capture_exception(self) -> None: ...

def clean_line(line: str) -> str:
    # Periods are optional statement terminators. Preserve periods inside text blocks.
    stripped = line.strip()
    if stripped.endswith(".") and not stripped.lower().startswith(("create ", "display text ")):
        stripped = stripped[:-1].rstrip()
    return stripped

def split_text_literal(source: str) -> tuple[str, str] | None:
    match = re.match(r"(?is)^text\s+(.*?)\s+end\s+text$", source.strip())
    if match:
        return ("text", match.group(1))
    return None

class ExpressionParser:
    """Recursive-descent expression parser. Operators are words, not punctuation."""
    PRECEDENCE = {
        "or": 1, "and": 2,
        "is": 3, "equals": 3, "not": 3, "greater": 3, "less": 3,
        "plus": 4, "minus": 4,
        "times": 5, "divided": 5, "remainder": 5,
    }

    def __init__(self, source: str, env: dict[str, Any]):
        self.env = env
        self.tokens = self._tokenize(source)
        self.i = 0

    def _tokenize(self, source: str) -> list[str]:
        try:
            return [
                token.value
                for token in Lexer(source).tokenize()
                if token.value not in {",", "."}
            ]
        except SyntaxError as exc:
            raise ZelixError(str(exc)) from exc

    def peek(self) -> str | None:
        return self.tokens[self.i] if self.i < len(self.tokens) else None

    def take(self) -> str:
        tok = self.peek()
        if tok is None:
            raise ZelixError("Unexpected end of expression")
        self.i += 1
        return tok

    def match(self, *words: str) -> bool:
        if self.peek() is not None and self.peek().lower() in words:
            self.i += 1
            return True
        return False

    def parse(self) -> Any:
        value = self.expression(0)
        if self.peek() is not None:
            raise ZelixError(f"Unexpected word {self.peek()!r} in expression")
        return value

    def expression(self, min_prec: int) -> Any:
        left = self.atom()
        while self.peek() is not None:
            op = self.peek().lower()
            # Multiword operators are handled as phrases.
            phrase = self._operator_phrase()
            if phrase is None:
                break
            op_name, consumed, prec = phrase
            if prec < min_prec:
                break
            self.i += consumed
            right = self.expression(prec + 1)
            left = self.apply(op_name, left, right)
        return left

    def _operator_phrase(self):
        remaining = [x.lower() for x in self.tokens[self.i:self.i+6]]
        phrases = [
            (["is", "greater", "than", "or", "equal", "to"], "gte", 3, 6),
            (["is", "less", "than", "or", "equal", "to"], "lte", 3, 6),
            (["greater", "than", "or", "equal", "to"], "gte", 3, 5),
            (["less", "than", "or", "equal", "to"], "lte", 3, 5),
            (["is", "greater", "than"], "gt", 3, 3),
            (["is", "less", "than"], "lt", 3, 3),
            (["greater", "than"], "gt", 3, 2),
            (["less", "than"], "lt", 3, 2),
            (["is", "not"], "ne", 3, 2),
            (["divided", "by"], "div", 5, 2),
            (["is", "equal", "to"], "eq", 3, 3),
            (["equals"], "eq", 3, 1),
            (["is"], "eq", 3, 1),
            (["plus"], "add", 4, 1),
            (["minus"], "sub", 4, 1),
            (["times"], "mul", 5, 1),
            (["remainder"], "mod", 5, 1),
            (["and"], "and", 2, 1),
            (["or"], "or", 1, 1),
        ]
        for words, name, prec, count in phrases:
            if remaining[:len(words)] == words:
                return name, count, prec
        return None

    def atom(self) -> Any:
        if self.match("not"):
            return not bool(self.expression(3))
        tok = self.take()
        low = tok.lower()
        if low == "true":
            return True
        if low == "false":
            return False
        if re.fullmatch(r"-?\d+", tok):
            return int(tok)
        if re.fullmatch(r"-?\d+\.\d+", tok):
            return float(tok)
        if tok.startswith(('"', "'")):
            try:
                return ast.literal_eval(tok)
            except Exception as exc:
                raise ZelixError(f"Invalid quoted text: {tok}") from exc
        if low in self.env:
            return self.env[low]
        # Keep text declarations explicit. Unknown names are likely typos.
        raise ZelixError(f"Unknown variable {tok!r}")

    @staticmethod
    def apply(op: str, a: Any, b: Any) -> Any:
        ops = {
            "add": operator.add, "sub": operator.sub, "mul": operator.mul,
            "div": operator.truediv, "mod": operator.mod,
            "eq": operator.eq, "ne": operator.ne, "gt": operator.gt,
            "lt": operator.lt, "gte": operator.ge, "lte": operator.le,
            "and": lambda x, y: bool(x) and bool(y),
            "or": lambda x, y: bool(x) or bool(y),
        }
        try:
            return ops[op](a, b)
        except ZeroDivisionError:
            raise ZelixError("Cannot divide by zero")
        except TypeError as exc:
            raise ZelixError(f"Invalid operands for {op}: {a!r} and {b!r}") from exc

class Interpreter:
    def __init__(self, debugger: Debugger | None = None):
        self.env: dict[str, Any] = {}
        self.functions: dict[str, Function] = {}
        self._call_depth: ContextVar[int] = ContextVar("zelix_call_depth", default=0)
        self.debugger = debugger

    def error(self, line_no: int, message: str):
        raise ZelixError(f"Line {line_no}: {message}")

    def run_file(self, path: Path):
        try:
            if path.is_dir():
                path = project_entry(path)
            source = path.read_text(encoding="utf-8")
        except ProjectError as exc:
            raise ZelixError(str(exc)) from exc
        except OSError as exc:
            raise ZelixError(f"Cannot read {path}: {exc}") from exc
        try:
            source = resolve_project_source(source, path)
        except ProjectError as exc:
            raise ZelixError(str(exc)) from exc
        module = parse_source(source)
        try:
            TypeChecker(module).check()
        except TypeCheckError as exc:
            raise ZelixError(str(exc)) from exc
        self.functions = {
            function.name: Function(
                function.name, function.params, function.body, function.line,
                function.is_async,
            )
            for function in module.functions
        }
        try:
            asyncio.get_running_loop()
        except RuntimeError:
            asyncio.run(self._run_module(module))
        else:
            raise ZelixError("run_file cannot start inside an active asyncio event loop")

    async def _run_module(self, module):
        if self.debugger:
            self.debugger.push_frame("main", self.env, 1)
        await self.execute(module.body, self.env)

    async def eval_expr(self, expression: Expr, env: dict[str, Any]) -> Any:
        if isinstance(expression, Literal):
            return expression.value
        if isinstance(expression, Variable):
            if expression.name not in env:
                self.error(expression.line, f"Unknown variable {expression.name!r}")
            return env[expression.name]
        if isinstance(expression, Input):
            if self.debugger:
                self.error(expression.line, "Interactive input is not supported while debugging")
            prompt = input(f"{expression.name}: ")
            if expression.kind == "number":
                try:
                    return float(prompt) if "." in prompt else int(prompt)
                except ValueError:
                    self.error(expression.line, f"Expected a number, got {prompt!r}")
            return prompt
        if isinstance(expression, Unary):
            return not bool(await self.eval_expr(expression.value, env))
        if isinstance(expression, Binary):
            left = await self.eval_expr(expression.left, env)
            right = await self.eval_expr(expression.right, env)
            return ExpressionParser.apply(expression.op, left, right)
        if isinstance(expression, Await):
            if self.debugger:
                self.error(expression.line, "Async tasks are not supported while debugging")
            awaited = await self.eval_expr(expression.value, env)
            if isinstance(awaited, concurrent.futures.Future):
                awaited = asyncio.wrap_future(awaited)
            if not hasattr(awaited, "__await__"):
                self.error(expression.line, "await expects an async task")
            try:
                return await awaited
            except ZelixError:
                raise
            except Exception as exc:
                self.error(expression.line, f"Async task failed: {exc}")
        if isinstance(expression, Spawn):
            if self.debugger:
                self.error(expression.line, "Concurrent tasks are not supported while debugging")
            args = [await self.eval_expr(argument, env) for argument in expression.call.args]
            function = self.functions[expression.call.name]
            if function.is_async:
                coroutine = self.call_function(expression.call.name, args)
            else:
                coroutine = asyncio.to_thread(
                    self._run_thread_function, expression.call.name, args,
                )
            return asyncio.create_task(coroutine)
        if isinstance(expression, Call):
            if expression.name in GAME_FUNCTIONS:
                self.error(
                    expression.line,
                    "Game API calls require native compilation with Raylib",
                )
            if expression.name == "spawn_thread":
                if self.debugger:
                    self.error(expression.line, "Concurrent tasks are not supported while debugging")
                if not expression.args or not isinstance(expression.args[0], Literal):
                    self.error(
                        expression.line,
                        "spawn_thread expects a function name followed by arguments",
                    )
                target = str(expression.args[0].value)
                args = [
                    await self.eval_expr(argument, env)
                    for argument in expression.args[1:]
                ]
                if target not in self.functions:
                    self.error(expression.line, f"Unknown thread function {target!r}")
                if self.functions[target].is_async:
                    self.error(expression.line, "spawn_thread requires a synchronous function")
                return asyncio.create_task(
                    asyncio.to_thread(self._run_thread_function, target, args)
                )
            args = [await self.eval_expr(argument, env) for argument in expression.args]
            if expression.name in {
                "list", "map", "set", "tuple", "empty_list", "empty_map",
                "empty_set", "append", "insert", "add_to_set", "put", "get",
                "remove", "contains",
                "length", "keys", "values", "channel", "send", "receive",
                "close_channel", "sleep",
            }:
                if expression.name == "channel":
                    if (
                        len(args) != 1 or isinstance(args[0], bool)
                        or not isinstance(args[0], int)
                    ):
                        self.error(expression.line, "channel expects a whole-number capacity")
                    if args[0] < 0 or args[0] > 1_000_000:
                        self.error(
                            expression.line,
                            "Channel capacity must be between 0 and 1000000",
                        )
                    return Channel(args[0])
                if expression.name == "send":
                    if len(args) != 2:
                        self.error(expression.line, "send expects a channel and a value")
                    return asyncio.create_task(
                        self._send_channel(args[0], args[1], expression.line)
                    )
                if expression.name == "receive":
                    if len(args) != 1:
                        self.error(expression.line, "receive expects a channel")
                    return asyncio.create_task(
                        self._receive_channel(args[0], expression.line)
                    )
                if expression.name == "close_channel":
                    if len(args) != 1 or not isinstance(args[0], Channel):
                        self.error(expression.line, "close_channel expects a channel")
                    args[0].close(expression.line)
                    return None
                if expression.name == "sleep":
                    if (
                        len(args) != 1 or isinstance(args[0], bool)
                        or not isinstance(args[0], (int, float))
                    ):
                        self.error(expression.line, "sleep expects a duration in seconds")
                    if not 0 <= args[0] <= 86400:
                        self.error(
                            expression.line,
                            "sleep duration must be from 0 to 86400 seconds",
                        )
                    return asyncio.create_task(asyncio.sleep(args[0]))
                return self.call_builtin(expression.name, args, expression.line)
            function = self.functions.get(expression.name)
            if function is None:
                self.error(expression.line, f"Unknown function {expression.name!r}")
            if self.debugger and function.is_async:
                self.error(expression.line, "Async tasks are not supported while debugging")
            result = self.call_function(expression.name, args)
            return asyncio.create_task(result) if function.is_async else await result
        self.error(expression.line, f"Unsupported expression: {type(expression).__name__}")

    async def _send_channel(self, channel: Any, value: Any, line: int):
        if not isinstance(channel, Channel):
            self.error(line, "send expects a channel")
        await channel.async_send(value, line)
        return None

    async def _receive_channel(self, channel: Any, line: int):
        if not isinstance(channel, Channel):
            self.error(line, "receive expects a channel")
        return await channel.async_receive(line)

    def _run_thread_function(self, name: str, args: list[Any]) -> Any:
        child = Interpreter()
        child.functions = self.functions
        return asyncio.run(child.call_function(name, args))

    def call_builtin(self, name: str, args: list[Any], line: int) -> Any:
        try:
            if name == "list":
                return list(args)
            if name == "empty_list":
                return []
            if name == "tuple":
                return tuple(args)
            if name == "set":
                return set(args)
            if name == "empty_set":
                return set()
            if name == "map":
                if len(args) % 2:
                    self.error(line, "map expects alternating key and value arguments")
                return dict(zip(args[::2], args[1::2]))
            if name == "empty_map":
                return {}
            if name == "append":
                args[0].append(args[1])
                return None
            if name == "add_to_set":
                args[0].add(args[1])
                return None
            if name == "put":
                args[0][args[1]] = args[2]
                return None
            if name == "insert":
                index = self._collection_index(args[1], len(args[0]), line, allow_end=True)
                args[0].insert(index, args[2])
                return None
            if name == "get":
                collection, key = args
                if isinstance(collection, dict):
                    return collection[key]
                if isinstance(collection, (list, tuple)):
                    return collection[self._collection_index(key, len(collection), line)]
                self.error(line, "get expects a list, map, or tuple")
            if name == "remove":
                collection, key = args
                if isinstance(collection, list):
                    collection.pop(self._collection_index(key, len(collection), line))
                elif isinstance(collection, dict):
                    del collection[key]
                elif isinstance(collection, set):
                    collection.remove(key)
                else:
                    self.error(line, "remove expects a list, map, or set")
                return None
            if name == "contains":
                return args[1] in args[0]
            if name == "length":
                return len(args[0])
            if name == "keys":
                return list(args[0].keys())
            if name == "values":
                return list(args[0].values())
        except (IndexError, KeyError, TypeError, ValueError) as exc:
            self.error(line, f"Invalid {name} operation: {exc}")
        return None

    def _collection_index(self, value: Any, length: int, line: int, allow_end=False) -> int:
        if isinstance(value, bool) or not isinstance(value, int):
            self.error(line, "Collection index must be a whole number")
        upper = length if allow_end else length - 1
        if value < 0 or value > upper:
            self.error(line, f"Collection index {value} is out of range")
        return value

    async def call_function(self, name: str, args: list[Any]) -> Any:
        fn = self.functions[name]
        if len(args) != len(fn.params):
            self.error(fn.line, f"Function {name} expects {len(fn.params)} arguments, got {len(args)}")
        depth = self._call_depth.get()
        if depth >= 200:
            raise ZelixError("Maximum function call depth exceeded")
        local_env = dict(self.env)
        local_env.update(zip(fn.params, args))
        depth_token = self._call_depth.set(depth + 1)
        if self.debugger:
            self.debugger.push_frame(name, local_env, fn.line)
        try:
            try:
                await self.execute(fn.body, local_env, in_function=True)
            except ReturnSignal as ret:
                return ret.value
            return None
        except Exception:
            if self.debugger:
                self.debugger.capture_exception()
            raise
        finally:
            if self.debugger:
                self.debugger.pop_frame()
            self._call_depth.reset(depth_token)

    async def execute(self, statements: list[Stmt], env: dict[str, Any], in_function=False):
        iterations = 0
        for statement in statements:
            if self.debugger:
                self.debugger.before_statement(statement.line, env)
            if isinstance(statement, Create):
                if statement.name in env:
                    self.error(statement.line, f"Variable {statement.name!r} already exists")
                env[statement.name] = await self.eval_expr(statement.value, env)
            elif isinstance(statement, Assign):
                if statement.name not in env:
                    self.error(statement.line, f"Unknown variable {statement.name!r}")
                env[statement.name] = await self.eval_expr(statement.value, env)
            elif isinstance(statement, Display):
                print(await self.eval_expr(statement.value, env))
            elif isinstance(statement, CallStatement):
                await self.eval_expr(statement.call, env)
            elif isinstance(statement, Return):
                if not in_function:
                    self.error(statement.line, "return can only be used inside a function")
                raise ReturnSignal(await self.eval_expr(statement.value, env))
            elif isinstance(statement, If):
                branch = (
                    statement.body
                    if await self.eval_expr(statement.condition, env)
                    else statement.otherwise
                )
                await self.execute(branch, env, in_function)
            elif isinstance(statement, While):
                while await self.eval_expr(statement.condition, env):
                    await self.execute(statement.body, env, in_function)
                    iterations += 1
                    if iterations > 1_000_000:
                        self.error(statement.line, "Loop exceeded one million iterations")
            elif isinstance(statement, Repeat):
                count = await self.eval_expr(statement.count, env)
                if not isinstance(count, int) or count < 0:
                    self.error(statement.line, "Repeat count must be a non-negative whole number")
                for _ in range(min(count, 1_000_000)):
                    await self.execute(statement.body, env, in_function)
            elif isinstance(statement, RangeLoop):
                start = int(await self.eval_expr(statement.start, env))
                end = int(await self.eval_expr(statement.end, env))
                for value in range(start, end + 1):
                    env[statement.name] = value
                    await self.execute(statement.body, env, in_function)

def main(argv: list[str] | None = None):
    arguments = list(sys.argv[1:] if argv is None else argv)
    if arguments and arguments[0] in {"init", "install"}:
        project_parser = argparse.ArgumentParser(prog=f"zelix {arguments[0]}")
        project_parser.add_argument("path", nargs="?", default=".", help="Project directory")
        command = arguments[0]
        options = project_parser.parse_args(arguments[1:])
        try:
            if command == "init":
                manifest, entry = init_project(Path(options.path))
                print(f"Created {manifest}")
                print(f"Created {entry}")
            else:
                lockfile = install_project(Path(options.path))
                print(f"Updated {lockfile}")
            return 0
        except ProjectError as exc:
            print(f"Zelix error: {exc}", file=sys.stderr)
            return 1

    parser = argparse.ArgumentParser(description="Zelix interpreter and native compiler")
    parser.add_argument("file", nargs="?", help="Path to a .zelix source file")
    parser.add_argument("--version", action="store_true", help="Print version")
    parser.add_argument("--compile", action="store_true", help="Compile a Zelix file to a native executable")
    parser.add_argument("-o", "--output", help="Set the native executable path")
    parser.add_argument("--cc", help="Choose the C compiler executable")
    parser.add_argument("--emit-ir", action="store_true", help="Print optimized Zelix IR")
    parser.add_argument("--check", action="store_true", help="Validate source without executing or compiling")
    parser.add_argument(
        "--asset-root", type=Path,
        help="Resolve literal game asset paths relative to this directory when validating stdin",
    )
    parser.add_argument("--debug", action="store_true", help="Build an unoptimized native executable with debug symbols")
    parser.add_argument("--debug-server", metavar="FILE", help=argparse.SUPPRESS)
    parser.add_argument("--debug-no-stop-on-entry", action="store_true", help=argparse.SUPPRESS)
    args = parser.parse_args(arguments)
    if args.version:
        print(f"Zelix {VERSION}")
        return 0
    if args.debug_server:
        from debug_server import run_debug_server

        return run_debug_server(args.debug_server, stop_on_entry=not args.debug_no_stop_on_entry)
    try:
        if args.check:
            asset_root = args.asset_root or Path.cwd()
            if not args.file:
                source = resolve_project_source(sys.stdin.read(), Path.cwd())
                validate_source(source, asset_root)
            else:
                validate_file(Path(args.file), args.asset_root)
            return 0
        if not args.file:
            parser.print_help()
            return 2
        source_path = Path(args.file)
        if source_path.is_dir():
            source_path = project_entry(source_path)
        if args.compile:
            output, ir = compile_file(
                source_path,
                Path(args.output) if args.output else None,
                args.cc,
                args.debug,
            )
            if args.emit_ir:
                print(ir)
            print(f"Compiled to {output}")
        elif args.emit_ir:
            print(emit_ir_file(source_path))
        else:
            Interpreter().run_file(source_path)
        return 0
    except (ZelixError, CompileError, ProjectError) as exc:
        print(f"Zelix error: {exc}", file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        print("\nExecution interrupted.", file=sys.stderr)
        return 130

if __name__ == "__main__":
    raise SystemExit(main())
