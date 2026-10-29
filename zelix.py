#!/usr/bin/env python3
"""Zelix 0.2.0: a line-oriented interpreter and native compiler."""

from __future__ import annotations
import argparse
import ast
import operator
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Protocol

from compiler import CompileError, compile_file, emit_ir_file, validate_file, validate_source
from project import ProjectError, init_project, install_project, project_entry, resolve_project_source

VERSION = "0.2.0"

class ZelixError(Exception):
    pass

@dataclass
class Function:
    name: str
    params: list[str]
    body: list[tuple[int, str]]
    line: int

class ReturnSignal(Exception):
    def __init__(self, value: Any):
        self.value = value

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
    TOKEN_RE = re.compile(
        r'\s*(>=|<=|==|!=|[(),.]|"(?:\\.|[^"\\])*"|\'(?:\\.|[^\'\\])*\'|'
        r'-?\d+(?:\.\d+)?|[A-Za-z_][A-Za-z_0-9]*|.)'
    )
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
        tokens = []
        pos = 0
        while pos < len(source):
            m = self.TOKEN_RE.match(source, pos)
            if not m:
                raise ZelixError(f"Could not read expression near {source[pos:pos+12]!r}")
            tok = m.group(1)
            pos = m.end()
            if tok.strip() == "":
                continue
            if tok in {",", "."}:
                continue
            tokens.append(tok)
        return tokens

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
        self.call_depth = 0
        self.debugger = debugger

    def error(self, line_no: int, message: str):
        raise ZelixError(f"Line {line_no}: {message}")

    def load_functions(self, lines: list[str]):
        i = 0
        while i < len(lines):
            s = clean_line(lines[i])
            m = re.match(r"(?i)^function\s+([A-Za-z_]\w*)(?:\s+taking\s+(.+))?$", s)
            if not m:
                i += 1
                continue
            name = m.group(1).lower()
            params = []
            if m.group(2):
                params = [x.strip().lower() for x in re.split(r"\s+and\s+", m.group(2).strip())]
                params = [re.sub(r"\s+as\s+\w+$", "", p).strip() for p in params]
            start = i + 1
            depth = 1
            j = start
            while j < len(lines):
                t = clean_line(lines[j]).lower()
                if t.startswith("function "):
                    depth += 1
                if t == "end function":
                    depth -= 1
                    if depth == 0:
                        break
                j += 1
            if j >= len(lines):
                self.error(i + 1, f"Function {name} is missing end function")
            self.functions[name] = Function(name, params, [(k+1, lines[k]) for k in range(start, j)], i+1)
            i = j + 1

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
        lines = source.splitlines()
        self.load_functions(lines)
        numbered = [(i+1, line) for i, line in enumerate(lines)]
        if self.debugger:
            self.debugger.push_frame("main", self.env, 1)
        # Top-level function definitions are skipped during execution.
        self.execute(numbered, self.env)

    def eval_expr(self, source: str, env: dict[str, Any]) -> Any:
        text = split_text_literal(source)
        if text:
            return text[1]
        # Support function calls: name with arg and arg.
        call = re.match(r"(?is)^([A-Za-z_]\w*)\s+with\s+(.+)$", source.strip())
        if call and call.group(1).lower() in self.functions:
            args = [self.eval_expr(part.strip(), env) for part in re.split(r"\s+and\s+", call.group(2).strip())]
            return self.call_function(call.group(1).lower(), args)
        return ExpressionParser(source, env).parse()

    def call_function(self, name: str, args: list[Any]) -> Any:
        fn = self.functions[name]
        if len(args) != len(fn.params):
            self.error(fn.line, f"Function {name} expects {len(fn.params)} arguments, got {len(args)}")
        if self.call_depth >= 200:
            raise ZelixError("Maximum function call depth exceeded")
        local_env = dict(self.env)
        local_env.update(zip(fn.params, args))
        self.call_depth += 1
        if self.debugger:
            self.debugger.push_frame(name, local_env, fn.line)
        try:
            try:
                self.execute(fn.body, local_env, in_function=True)
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
            self.call_depth -= 1

    def execute(self, lines: list[tuple[int, str]], env: dict[str, Any], in_function=False):
        i = 0
        while i < len(lines):
            line_no, raw = lines[i]
            s = clean_line(raw)
            if not s or s.startswith("#"):
                i += 1
                continue
            low = s.lower()
            if low.startswith("function "):
                j = i + 1
                depth = 1
                while j < len(lines):
                    candidate = clean_line(lines[j][1] if isinstance(lines[j], tuple) else lines[j]).lower()
                    if candidate.startswith("function "):
                        depth += 1
                    elif candidate == "end function":
                        depth -= 1
                        if depth == 0:
                            break
                    j += 1
                if j >= len(lines):
                    self.error(line_no, "Function is missing end function")
                i = j + 1
                continue

            if low in {"end if", "end loop", "end function"} or low == "otherwise":
                i += 1
                continue

            if self.debugger:
                self.debugger.before_statement(line_no, env)

            if low.startswith("if "):
                end, otherwise_at = self.find_block(lines, i, "if")
                cond = s[3:].strip()
                result = bool(self.eval_expr(cond, env))
                if result:
                    self.execute(lines[i+1:(otherwise_at if otherwise_at is not None else end)], env, in_function)
                elif otherwise_at is not None:
                    self.execute(lines[otherwise_at+1:end], env, in_function)
                i = end + 1
                continue

            if low.startswith("while "):
                end, _ = self.find_block(lines, i, "loop")
                cond = s[6:].strip()
                iterations = 0
                while bool(self.eval_expr(cond, env)):
                    self.execute(lines[i+1:end], env, in_function)
                    iterations += 1
                    if iterations > 1_000_000:
                        self.error(line_no, "Loop exceeded one million iterations")
                i = end + 1
                continue

            if low.startswith("repeat "):
                m = re.match(r"(?i)^repeat\s+(.+?)\s+times$", s)
                if m:
                    end, _ = self.find_block(lines, i, "loop")
                    count = self.eval_expr(m.group(1), env)
                    if not isinstance(count, int) or count < 0:
                        self.error(line_no, "Repeat count must be a non-negative whole number")
                    for _ in range(min(count, 1_000_000)):
                        self.execute(lines[i+1:end], env, in_function)
                    i = end + 1
                    continue

            if low.startswith("create "):
                m = re.match(r"(?is)^create\s+([A-Za-z_]\w*)\s+as\s+(.+)$", s)
                if not m:
                    self.error(line_no, "Expected: create name as expression")
                name, expr = m.group(1).lower(), m.group(2).strip()
                if name in env:
                    self.error(line_no, f"Variable {name!r} already exists")
                input_match = re.match(r"(?i)^input\s+(text|number)$", expr)
                if input_match:
                    if self.debugger:
                        self.error(line_no, "Interactive input is not supported while debugging")
                    prompt = input(f"{name}: ")
                    if input_match.group(1).lower() == "number":
                        try:
                            value = float(prompt) if "." in prompt else int(prompt)
                        except ValueError:
                            self.error(line_no, f"Expected a number, got {prompt!r}")
                    else:
                        value = prompt
                else:
                    value = self.eval_expr(expr, env)
                env[name] = value
                i += 1
                continue

            if low.startswith("display "):
                expr = s[8:].strip()
                if expr.lower().startswith("text "):
                    lit = split_text_literal(expr + " end text") if not expr.lower().endswith("end text") else split_text_literal(expr)
                    if lit:
                        print(lit[1])
                    else:
                        print(expr[5:])
                elif expr.lower().startswith("text "):
                    print(expr[5:])
                elif expr.lower().startswith("text "):
                    print(expr[5:])
                else:
                    try:
                        print(self.eval_expr(expr, env))
                    except ZelixError:
                        # `display text Hello world` is a convenient output form.
                        if re.match(r"(?i)^text\s+", expr):
                            print(re.sub(r"(?i)^text\s+", "", expr))
                        else:
                            raise
                i += 1
                continue

            if low.startswith("call "):
                call_expr = s[5:].strip()
                m = re.match(r"(?is)^([A-Za-z_]\w*)\s+with\s+(.+)$", call_expr)
                if not m:
                    self.error(line_no, "Expected: call function with argument and argument")
                args = [self.eval_expr(p.strip(), env) for p in re.split(r"\s+and\s+", m.group(2).strip())]
                self.call_function(m.group(1).lower(), args)
                i += 1
                continue

            if low.startswith("return "):
                if not in_function:
                    self.error(line_no, "return can only be used inside a function")
                raise ReturnSignal(self.eval_expr(s[7:].strip(), env))

            # Assignment: variable becomes expression.
            m = re.match(r"(?is)^([A-Za-z_]\w*)\s+becomes\s+(.+)$", s)
            if m:
                name, expr = m.group(1).lower(), m.group(2).strip()
                if name not in env:
                    self.error(line_no, f"Unknown variable {name!r}")
                env[name] = self.eval_expr(expr, env)
                i += 1
                continue

            # Counted loop: repeat with item from start to end
            m = re.match(r"(?is)^repeat\s+with\s+([A-Za-z_]\w*)\s+from\s+(.+?)\s+to\s+(.+)$", s)
            if m:
                end, _ = self.find_block(lines, i, "loop")
                var = m.group(1).lower()
                start_value = int(self.eval_expr(m.group(2), env))
                end_value = int(self.eval_expr(m.group(3), env))
                for value in range(start_value, end_value + 1):
                    env[var] = value
                    self.execute(lines[i+1:end], env, in_function)
                i = end + 1
                continue

            self.error(line_no, f"Unknown statement: {s!r}")

    def find_block(self, lines, start, kind):
        depth = 1
        otherwise_at = None
        for j in range(start + 1, len(lines)):
            s = clean_line(lines[j][1] if isinstance(lines[j], tuple) else lines[j]).lower()
            if kind == "if":
                if s.startswith("if "):
                    depth += 1
                elif s == "end if":
                    depth -= 1
                    if depth == 0:
                        return j, otherwise_at
                elif s == "otherwise" and depth == 1:
                    otherwise_at = j
            else:
                if s.startswith(("while ", "repeat ")):
                    depth += 1
                elif s == "end loop":
                    depth -= 1
                    if depth == 0:
                        return j, None
        raise ZelixError(f"Line {lines[start][0]}: Missing block terminator for {kind}")

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
            if not args.file:
                source = resolve_project_source(sys.stdin.read(), Path.cwd())
                validate_source(source)
            else:
                validate_file(Path(args.file))
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
