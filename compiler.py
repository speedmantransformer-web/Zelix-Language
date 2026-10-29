"""Zelix IR, optimizer, and native C backend."""

from __future__ import annotations

import ast
import json
import operator
import os
import platform
import re
import shutil
import subprocess
import tempfile
from dataclasses import dataclass, field, fields, is_dataclass
from pathlib import Path
from typing import Any

from game_backend import GAME_FUNCTIONS, GAME_FUNCTION_IDS, GAME_RUNTIME_C
from project import ProjectError, resolve_project_source


class CompileError(Exception):
    pass


@dataclass
class Expr:
    line: int


@dataclass
class Literal(Expr):
    value: Any


@dataclass
class Variable(Expr):
    name: str


@dataclass
class Input(Expr):
    kind: str
    name: str


@dataclass
class Unary(Expr):
    op: str
    value: Expr


@dataclass
class Binary(Expr):
    op: str
    left: Expr
    right: Expr


@dataclass
class Call(Expr):
    name: str
    args: list[Expr] = field(default_factory=list)


@dataclass
class Stmt:
    line: int


@dataclass
class Create(Stmt):
    name: str
    value: Expr


@dataclass
class Assign(Stmt):
    name: str
    value: Expr


@dataclass
class Display(Stmt):
    value: Expr


@dataclass
class CallStatement(Stmt):
    call: Call


@dataclass
class Return(Stmt):
    value: Expr


@dataclass
class If(Stmt):
    condition: Expr
    body: list[Stmt]
    otherwise: list[Stmt]


@dataclass
class While(Stmt):
    condition: Expr
    body: list[Stmt]


@dataclass
class Repeat(Stmt):
    count: Expr
    body: list[Stmt]


@dataclass
class RangeLoop(Stmt):
    name: str
    start: Expr
    end: Expr
    body: list[Stmt]


@dataclass
class FunctionIR:
    name: str
    params: list[str]
    body: list[Stmt]
    line: int


@dataclass
class ModuleIR:
    functions: list[FunctionIR]
    body: list[Stmt]


class ExpressionIRParser:
    TOKEN_RE = re.compile(
        r'\s*(>=|<=|==|!=|[(),.]|"(?:\\.|[^"\\])*"|\'(?:\\.|[^\'\\])*\'|'
        r'-?\d+(?:\.\d+)?|[A-Za-z_][A-Za-z_0-9]*|.)'
    )
    PHRASES = (
        (("is", "greater", "than", "or", "equal", "to"), "gte", 3),
        (("is", "less", "than", "or", "equal", "to"), "lte", 3),
        (("greater", "than", "or", "equal", "to"), "gte", 3),
        (("less", "than", "or", "equal", "to"), "lte", 3),
        (("is", "greater", "than"), "gt", 3),
        (("is", "less", "than"), "lt", 3),
        (("greater", "than"), "gt", 3),
        (("less", "than"), "lt", 3),
        (("is", "not"), "ne", 3),
        (("is", "equal", "to"), "eq", 3),
        (("divided", "by"), "div", 5),
        (("equals",), "eq", 3),
        (("is",), "eq", 3),
        (("plus",), "add", 4),
        (("minus",), "sub", 4),
        (("times",), "mul", 5),
        (("remainder",), "mod", 5),
        (("and",), "and", 2),
        (("or",), "or", 1),
    )

    def __init__(self, source: str, line: int, functions: set[str]):
        self.source = source.strip()
        self.line = line
        self.functions = functions
        self.tokens = self._tokenize(self.source)
        self.index = 0

    def _tokenize(self, source: str) -> list[str]:
        tokens = []
        pos = 0
        while pos < len(source):
            match = self.TOKEN_RE.match(source, pos)
            if not match:
                raise CompileError(f"Line {self.line}: Invalid expression near {source[pos:pos + 12]!r}")
            token = match.group(1)
            pos = match.end()
            if token.strip() and token not in {",", "."}:
                tokens.append(token)
        return tokens

    def parse(self) -> Expr:
        expression = self._expression(0)
        if self.index != len(self.tokens):
            raise CompileError(f"Line {self.line}: Unexpected token {self.tokens[self.index]!r}")
        return expression

    def _expression(self, min_precedence: int) -> Expr:
        left = self._atom()
        while self.index < len(self.tokens):
            phrase = self._operator()
            if phrase is None:
                break
            op, count, precedence = phrase
            if precedence < min_precedence:
                break
            self.index += count
            right = self._expression(precedence + 1)
            left = Binary(self.line, op, left, right)
        return left

    def _operator(self) -> tuple[str, int, int] | None:
        remaining = tuple(token.lower() for token in self.tokens[self.index:])
        for words, op, precedence in self.PHRASES:
            if remaining[:len(words)] == words:
                return op, len(words), precedence
        return None

    def _atom(self) -> Expr:
        if self.index >= len(self.tokens):
            raise CompileError(f"Line {self.line}: Unexpected end of expression")
        if self.tokens[self.index].lower() == "not":
            self.index += 1
            return Unary(self.line, "not", self._expression(3))
        token = self.tokens[self.index]
        self.index += 1
        lower = token.lower()
        if token == "(":
            expression = self._expression(0)
            if self.index >= len(self.tokens) or self.tokens[self.index] != ")":
                raise CompileError(f"Line {self.line}: Missing closing parenthesis")
            self.index += 1
            return expression
        if lower == "true":
            return Literal(self.line, True)
        if lower == "false":
            return Literal(self.line, False)
        if re.fullmatch(r"-?\d+", token):
            return Literal(self.line, int(token))
        if re.fullmatch(r"-?\d+\.\d+", token):
            return Literal(self.line, float(token))
        if token.startswith(('"', "'")):
            try:
                return Literal(self.line, ast.literal_eval(token))
            except (SyntaxError, ValueError) as exc:
                raise CompileError(f"Line {self.line}: Invalid quoted text") from exc
        if re.fullmatch(r"[A-Za-z_]\w*", token):
            if lower in self.functions:
                return Call(self.line, lower)
            return Variable(self.line, lower)
        raise CompileError(f"Line {self.line}: Unexpected token {token!r}")


class ZelixParser:
    FUNCTION_RE = re.compile(r"(?i)^function\s+([A-Za-z_]\w*)(?:\s+taking\s+(.+))?$")
    TEXT_RE = re.compile(r"(?is)^text\s+(.*?)\s+end\s+text$")

    def __init__(self, source: str):
        self.lines = source.splitlines()
        self.function_sources: list[tuple[str, list[str], list[tuple[int, str]], int]] = []
        self.main_lines: list[tuple[int, str]] = []
        self.function_names: set[str] = set()
        self._split_functions()

    def _split_functions(self) -> None:
        index = 0
        while index < len(self.lines):
            text = _clean_line(self.lines[index])
            match = self.FUNCTION_RE.match(text)
            if not match:
                self.main_lines.append((index + 1, self.lines[index]))
                index += 1
                continue
            name = match.group(1).lower()
            if name in GAME_FUNCTIONS:
                raise CompileError(f"Line {index + 1}: {name!r} is a reserved game API function")
            if name in self.function_names:
                raise CompileError(f"Line {index + 1}: Function {name!r} is already defined")
            params = []
            if match.group(2):
                params = [
                    re.sub(r"\s+as\s+\w+$", "", part.strip()).lower()
                    for part in re.split(r"\s+and\s+", match.group(2).strip())
                ]
            if len(set(params)) != len(params):
                raise CompileError(f"Line {index + 1}: Function parameters must be unique")
            end = index + 1
            depth = 1
            while end < len(self.lines):
                candidate = _clean_line(self.lines[end]).lower()
                if candidate.startswith("function "):
                    depth += 1
                elif candidate == "end function":
                    depth -= 1
                    if depth == 0:
                        break
                end += 1
            if end == len(self.lines):
                raise CompileError(f"Line {index + 1}: Function {name} is missing end function")
            numbered_body = [(line + 1, self.lines[line]) for line in range(index + 1, end)]
            self.function_sources.append((name, params, numbered_body, index + 1))
            self.function_names.add(name)
            index = end + 1

    def parse(self) -> ModuleIR:
        body = _StatementParser(self.main_lines, self.function_names, in_function=False).parse()
        functions = [
            FunctionIR(
                name,
                params,
                _StatementParser(lines, self.function_names, in_function=True).parse(),
                line,
            )
            for name, params, lines, line in self.function_sources
        ]
        return ModuleIR(functions, body)


class _StatementParser:
    def __init__(self, lines: list[tuple[int, str]], functions: set[str], in_function: bool):
        self.lines = lines
        self.functions = functions
        self.in_function = in_function
        self.index = 0

    def parse(self, terminators: tuple[str, ...] = ()) -> list[Stmt]:
        statements = []
        while self.index < len(self.lines):
            line, raw = self.lines[self.index]
            text = _clean_line(raw)
            lower = text.lower()
            if not text or text.startswith("#"):
                self.index += 1
                continue
            if lower in terminators:
                break
            if lower.startswith("function ") or lower in {"end function", "end if", "end loop", "otherwise"}:
                raise CompileError(f"Line {line}: Unexpected block terminator or nested function")

            if lower.startswith("if "):
                self.index += 1
                body = self.parse(("otherwise", "end if"))
                otherwise = []
                if self.index < len(self.lines) and _clean_line(self.lines[self.index][1]).lower() == "otherwise":
                    self.index += 1
                    otherwise = self.parse(("end if",))
                self._consume_end("end if", line)
                statements.append(If(line, self._expression(text[3:], line), body, otherwise))
                continue
            if lower.startswith("while "):
                self.index += 1
                body = self.parse(("end loop",))
                self._consume_end("end loop", line)
                statements.append(While(line, self._expression(text[6:], line), body))
                continue
            if lower.startswith("repeat with "):
                match = re.match(r"(?is)^repeat\s+with\s+([A-Za-z_]\w*)\s+from\s+(.+?)\s+to\s+(.+)$", text)
                if not match:
                    raise CompileError(f"Line {line}: Expected: repeat with item from start to end")
                self.index += 1
                body = self.parse(("end loop",))
                self._consume_end("end loop", line)
                statements.append(RangeLoop(
                    line, match.group(1).lower(), self._expression(match.group(2), line),
                    self._expression(match.group(3), line), body,
                ))
                continue
            if lower.startswith("repeat "):
                match = re.match(r"(?is)^repeat\s+(.+?)\s+times$", text)
                if not match:
                    raise CompileError(f"Line {line}: Expected: repeat expression times")
                self.index += 1
                body = self.parse(("end loop",))
                self._consume_end("end loop", line)
                statements.append(Repeat(line, self._expression(match.group(1), line), body))
                continue
            if lower.startswith("create "):
                match = re.match(r"(?is)^create\s+([A-Za-z_]\w*)\s+as\s+(.+)$", text)
                if not match:
                    raise CompileError(f"Line {line}: Expected: create name as expression")
                name, value = match.group(1).lower(), match.group(2).strip()
                input_match = re.match(r"(?i)^input\s+(text|number)$", value)
                if input_match:
                    expr = Input(line, input_match.group(1).lower(), name)
                else:
                    expr = self._expression(value, line)
                self.index += 1
                statements.append(Create(line, name, expr))
                continue
            if lower.startswith("display "):
                value = text[8:].strip()
                if value.lower().startswith("text ") and not ZelixParser.TEXT_RE.match(value):
                    expr = Literal(line, value[5:])
                else:
                    expr = self._expression(value, line)
                self.index += 1
                statements.append(Display(line, expr))
                continue
            if lower.startswith("call "):
                match = re.match(r"(?is)^call\s+([A-Za-z_]\w*)(?:\s+with\s+(.+))?$", text)
                if not match:
                    raise CompileError(f"Line {line}: Expected: call function [with arguments]")
                call = self._call(match.group(1), match.group(2) or "", line)
                self.index += 1
                statements.append(CallStatement(line, call))
                continue
            if lower.startswith("return "):
                if not self.in_function:
                    raise CompileError(f"Line {line}: return can only be used inside a function")
                self.index += 1
                statements.append(Return(line, self._expression(text[7:].strip(), line)))
                continue
            match = re.match(r"(?is)^([A-Za-z_]\w*)\s+becomes\s+(.+)$", text)
            if match:
                self.index += 1
                statements.append(Assign(line, match.group(1).lower(), self._expression(match.group(2), line)))
                continue
            raise CompileError(f"Line {line}: Unknown statement: {text!r}")
        return statements

    def _consume_end(self, expected: str, start_line: int) -> None:
        if self.index >= len(self.lines) or _clean_line(self.lines[self.index][1]).lower() != expected:
            raise CompileError(f"Line {start_line}: Missing {expected}")
        self.index += 1

    def _expression(self, source: str, line: int) -> Expr:
        text_match = ZelixParser.TEXT_RE.match(source.strip())
        if text_match:
            return Literal(line, text_match.group(1))
        call_match = re.match(r"(?is)^([A-Za-z_]\w*)\s+with\s+(.+)$", source.strip())
        if call_match and (
            call_match.group(1).lower() in self.functions
            or call_match.group(1).lower() in GAME_FUNCTIONS
        ):
            return self._call(call_match.group(1), call_match.group(2), line)
        name = source.strip().lower()
        if name in GAME_FUNCTIONS and GAME_FUNCTIONS[name] == 0:
            return self._call(name, "", line)
        callable_names = self.functions | {
            name for name, arity in GAME_FUNCTIONS.items() if arity == 0
        }
        return ExpressionIRParser(source, line, callable_names).parse()

    def _call(self, name: str, source: str, line: int) -> Call:
        name = name.lower()
        if name not in self.functions and name not in GAME_FUNCTIONS:
            raise CompileError(f"Line {line}: Unknown function {name!r}")
        parts = (
            re.split(r"\s+and\s+", source.strip(), flags=re.IGNORECASE)
            if source.strip() else []
        )
        if name in GAME_FUNCTIONS and len(parts) != GAME_FUNCTIONS[name]:
            raise CompileError(
                f"Line {line}: Game API {name} expects {GAME_FUNCTIONS[name]} "
                f"arguments, got {len(parts)}"
            )
        return Call(line, name, [self._expression(part, line) for part in parts])


def optimize(module: ModuleIR) -> ModuleIR:
    module.body = _optimize_statements(module.body)
    for function in module.functions:
        function.body = _optimize_statements(function.body)
    return module


def _fold(expr: Expr) -> Expr:
    if isinstance(expr, Unary):
        expr.value = _fold(expr.value)
        if isinstance(expr.value, Literal) and expr.op == "not":
            return Literal(expr.line, not bool(expr.value.value))
    elif isinstance(expr, Binary):
        expr.left = _fold(expr.left)
        expr.right = _fold(expr.right)
        if isinstance(expr.left, Literal) and isinstance(expr.right, Literal):
            funcs = {
                "add": operator.add, "sub": operator.sub, "mul": operator.mul,
                "div": operator.truediv, "mod": operator.mod, "eq": operator.eq,
                "ne": operator.ne, "gt": operator.gt, "lt": operator.lt,
                "gte": operator.ge, "lte": operator.le,
                "and": lambda a, b: bool(a) and bool(b),
                "or": lambda a, b: bool(a) or bool(b),
            }
            try:
                return Literal(expr.line, funcs[expr.op](expr.left.value, expr.right.value))
            except (ArithmeticError, TypeError, ValueError):
                pass
    elif isinstance(expr, Call):
        expr.args = [_fold(argument) for argument in expr.args]
    return expr


def _optimize_statements(statements: list[Stmt]) -> list[Stmt]:
    result = []
    for statement in statements:
        if isinstance(statement, (Create, Assign, Display, Return)):
            statement.value = _fold(statement.value)
        elif isinstance(statement, CallStatement):
            statement.call = _fold(statement.call)
        elif isinstance(statement, If):
            statement.condition = _fold(statement.condition)
            statement.body = _optimize_statements(statement.body)
            statement.otherwise = _optimize_statements(statement.otherwise)
            if isinstance(statement.condition, Literal):
                result.extend(statement.body if bool(statement.condition.value) else statement.otherwise)
                continue
        elif isinstance(statement, While):
            statement.condition = _fold(statement.condition)
            statement.body = _optimize_statements(statement.body)
            if isinstance(statement.condition, Literal) and not bool(statement.condition.value):
                continue
        elif isinstance(statement, Repeat):
            statement.count = _fold(statement.count)
            statement.body = _optimize_statements(statement.body)
            if isinstance(statement.count, Literal) and statement.count.value == 0:
                continue
        elif isinstance(statement, RangeLoop):
            statement.start = _fold(statement.start)
            statement.end = _fold(statement.end)
            statement.body = _optimize_statements(statement.body)
        result.append(statement)
    return result


def format_ir(module: ModuleIR) -> str:
    lines = ["module zelix"]

    def emit(statements: list[Stmt], depth: int) -> None:
        prefix = "  " * depth
        for statement in statements:
            if isinstance(statement, Create):
                lines.append(f"{prefix}%{statement.name} = create {_format_expr(statement.value)}")
            elif isinstance(statement, Assign):
                lines.append(f"{prefix}%{statement.name} = {_format_expr(statement.value)}")
            elif isinstance(statement, Display):
                lines.append(f"{prefix}display {_format_expr(statement.value)}")
            elif isinstance(statement, CallStatement):
                lines.append(f"{prefix}call {_format_expr(statement.call)}")
            elif isinstance(statement, Return):
                lines.append(f"{prefix}return {_format_expr(statement.value)}")
            elif isinstance(statement, If):
                lines.append(f"{prefix}branch {_format_expr(statement.condition)}")
                emit(statement.body, depth + 1)
                if statement.otherwise:
                    lines.append(f"{prefix}else")
                    emit(statement.otherwise, depth + 1)
            elif isinstance(statement, While):
                lines.append(f"{prefix}loop while {_format_expr(statement.condition)}")
                emit(statement.body, depth + 1)
            elif isinstance(statement, Repeat):
                lines.append(f"{prefix}loop {_format_expr(statement.count)} times")
                emit(statement.body, depth + 1)
            elif isinstance(statement, RangeLoop):
                lines.append(f"{prefix}loop %{statement.name} from {_format_expr(statement.start)} to {_format_expr(statement.end)}")
                emit(statement.body, depth + 1)

    for function in module.functions:
        lines.append(f"function @{function.name}({', '.join('%' + p for p in function.params)})")
        emit(function.body, 1)
    emit(module.body, 0)
    return "\n".join(lines)


def _format_expr(expr: Expr) -> str:
    if isinstance(expr, Literal):
        return json.dumps(expr.value, ensure_ascii=False)
    if isinstance(expr, Variable):
        return f"%{expr.name}"
    if isinstance(expr, Input):
        return f"input.{expr.kind} %{expr.name}"
    if isinstance(expr, Unary):
        return f"{expr.op} {_format_expr(expr.value)}"
    if isinstance(expr, Binary):
        return f"({expr.op} {_format_expr(expr.left)}, {_format_expr(expr.right)})"
    if isinstance(expr, Call):
        return f"@{expr.name}({', '.join(_format_expr(arg) for arg in expr.args)})"
    raise CompileError(f"Unsupported IR expression: {type(expr).__name__}")


class CGenerator:
    OPS = {
        "add": "Z_ADD", "sub": "Z_SUB", "mul": "Z_MUL", "div": "Z_DIV",
        "mod": "Z_MOD", "eq": "Z_EQ", "ne": "Z_NE", "gt": "Z_GT",
        "lt": "Z_LT", "gte": "Z_GTE", "lte": "Z_LTE", "and": "Z_AND",
        "or": "Z_OR",
    }

    def __init__(self, module: ModuleIR):
        self.module = module
        self.lines: list[str] = []
        self.indent = 0
        self.global_names = sorted(_defined_names(module.body))
        self.function_map = {function.name: function for function in module.functions}
        self.current_vars: dict[str, str] = {}
        self.loop_id = 0
        self.has_game_api = _uses_game_api(module)

    def generate(self) -> str:
        self.lines = [
            "#include <ctype.h>", "#include <math.h>", "#include <stdbool.h>",
            "#include <stdio.h>", "#include <stdlib.h>", "#include <string.h>", "",
            "typedef enum { Z_NONE, Z_NUMBER, Z_BOOLEAN, Z_STRING } ZType;",
            "typedef struct { ZType type; double number; const char *string; } Value;",
            "enum { Z_ADD, Z_SUB, Z_MUL, Z_DIV, Z_MOD, Z_EQ, Z_NE, Z_GT, Z_LT, Z_GTE, Z_LTE, Z_AND, Z_OR };",
            "static Value z_none(void) { Value v; v.type = Z_NONE; v.number = 0; v.string = NULL; return v; }",
            "static Value z_num(double n) { Value v; v.type = Z_NUMBER; v.number = n; v.string = NULL; return v; }",
            "static Value z_bool(int b) { Value v; v.type = Z_BOOLEAN; v.number = b != 0; v.string = NULL; return v; }",
            "static Value z_str(const char *s) { Value v; v.type = Z_STRING; v.number = 0; v.string = s; return v; }",
            "static void z_fail(int line, const char *message) {",
            "    fprintf(stderr, \"Zelix error: Line %d: %s\\n\", line, message);",
            "    exit(1);",
            "}",
            "static int z_call_depth = 0;",
            "static Value z_leave(Value value) { --z_call_depth; return value; }",
            "static int z_truth(Value v) {",
            "    if (v.type == Z_BOOLEAN || v.type == Z_NUMBER) return v.number != 0;",
            "    if (v.type == Z_STRING) return v.string[0] != '\\0';",
            "    return 0;",
            "}",
            "static double z_number(Value v, int line) {",
            "    if (v.type == Z_NUMBER || v.type == Z_BOOLEAN) return v.number;",
            "    z_fail(line, \"Expected a number\"); return 0;",
            "}",
            "static const char *z_text(Value v, char *buffer, size_t size) {",
            "    if (v.type == Z_STRING) return v.string;",
            "    if (v.type == Z_BOOLEAN) return v.number ? \"True\" : \"False\";",
            "    if (v.type == Z_NONE) return \"None\";",
            "    snprintf(buffer, size, \"%.15g\", v.number); return buffer;",
            "}",
            "static void z_print(Value v) {",
            "    char buffer[64]; puts(z_text(v, buffer, sizeof buffer));",
            "}",
            "static char *z_copy(const char *s) {",
            "    size_t n = strlen(s) + 1; char *copy = (char *)malloc(n);",
            "    if (!copy) { fputs(\"Zelix error: out of memory\\n\", stderr); exit(1); }",
            "    memcpy(copy, s, n); return copy;",
            "}",
            "static Value z_binary(int op, Value a, Value b, int line) {",
            "    if (op == Z_AND) return z_bool(z_truth(a) && z_truth(b));",
            "    if (op == Z_OR) return z_bool(z_truth(a) || z_truth(b));",
            "    if (op == Z_ADD && a.type == Z_STRING && b.type == Z_STRING) {",
            "        size_t n = strlen(a.string) + strlen(b.string) + 1;",
            "        char *joined = (char *)malloc(n);",
            "        if (!joined) { fputs(\"Zelix error: out of memory\\n\", stderr); exit(1); }",
            "        snprintf(joined, n, \"%s%s\", a.string, b.string); return z_str(joined);",
            "    }",
            "    if (op == Z_EQ || op == Z_NE) {",
            "        int equal = 0;",
            "        if (a.type == Z_STRING && b.type == Z_STRING) equal = strcmp(a.string, b.string) == 0;",
            "        else if ((a.type == Z_NUMBER || a.type == Z_BOOLEAN) &&",
            "                 (b.type == Z_NUMBER || b.type == Z_BOOLEAN)) equal = a.number == b.number;",
            "        else if (a.type == b.type) equal = 1;",
            "        return z_bool(op == Z_EQ ? equal : !equal);",
            "    }",
            "    if ((op == Z_GT || op == Z_LT || op == Z_GTE || op == Z_LTE) &&",
            "        a.type == Z_STRING && b.type == Z_STRING) {",
            "        int order = strcmp(a.string, b.string);",
            "        if (op == Z_GT) return z_bool(order > 0);",
            "        if (op == Z_LT) return z_bool(order < 0);",
            "        if (op == Z_GTE) return z_bool(order >= 0);",
            "        return z_bool(order <= 0);",
            "    }",
            "    double x = z_number(a, line), y = z_number(b, line);",
            "    switch (op) {",
            "        case Z_ADD: return z_num(x + y); case Z_SUB: return z_num(x - y);",
            "        case Z_MUL: return z_num(x * y);",
            "        case Z_DIV: if (y == 0) z_fail(line, \"Cannot divide by zero\"); return z_num(x / y);",
            "        case Z_MOD: {",
            "            if (y == 0) z_fail(line, \"Cannot divide by zero\");",
            "            double r = fmod(x, y); if (r != 0 && ((r < 0) != (y < 0))) r += y;",
            "            return z_num(r);",
            "        }",
            "        case Z_GT: return z_bool(x > y); case Z_LT: return z_bool(x < y);",
            "        case Z_GTE: return z_bool(x >= y); case Z_LTE: return z_bool(x <= y);",
            "    }",
            "    z_fail(line, \"Invalid operator\"); return z_none();",
            "}",
            "static Value z_input(int numeric, int line, const char *name) {",
            "    char buffer[4096]; printf(\"%s: \", name); fflush(stdout);",
            "    if (!fgets(buffer, sizeof buffer, stdin)) z_fail(line, \"Could not read input\");",
            "    buffer[strcspn(buffer, \"\\r\\n\")] = '\\0';",
            "    if (!numeric) return z_str(z_copy(buffer));",
            "    char *end = NULL; double value = strtod(buffer, &end);",
            "    while (end && isspace((unsigned char)*end)) ++end;",
            "    if (end == buffer || !end || *end) z_fail(line, \"Expected a number from input\");",
            "    return z_num(value);",
            "}",
            "",
        ]
        if self.has_game_api:
            self.lines.extend(GAME_RUNTIME_C.strip().splitlines())
            self.lines.append("")
        for name in self.global_names:
            ident = self._ident(name)
            self._emit(f"static Value g_{ident} = {{ Z_NONE, 0, NULL }};")
            self._emit(f"static bool init_g_{ident} = false;")
        if self.global_names:
            self._emit("")
        for function in self.module.functions:
            args = ", ".join(f"Value a{index}" for index in range(len(function.params))) or "void"
            self._emit(f"static Value fn_{self._ident(function.name)}({args});")
        if self.module.functions:
            self._emit("")
        for function in self.module.functions:
            self._emit_function(function)
        self._emit("int main(void) {")
        self.indent = 1
        self.current_vars = {
            name: f"g_{self._ident(name)}" for name in self.global_names
        }
        self._emit_statements(self.module.body)
        if self.has_game_api:
            self._emit("z_game_shutdown();")
        self._emit("return 0;")
        self.indent = 0
        self._emit("}")
        return "\n".join(self.lines) + "\n"

    def _emit_function(self, function: FunctionIR) -> None:
        args = ", ".join(f"Value a{index}" for index in range(len(function.params))) or "void"
        self._emit(f"static Value fn_{self._ident(function.name)}({args}) {{")
        self.indent = 1
        self._emit(f"if (z_call_depth >= 200) z_fail({function.line}, \"Maximum function call depth exceeded\");")
        self._emit("++z_call_depth;")
        names = sorted(_defined_names(function.body) | set(function.params) | set(self.global_names))
        self.current_vars = {name: f"v_{self._ident(name)}" for name in names}
        for name in names:
            ident = self._ident(name)
            self._emit(f"Value v_{ident} = z_none();")
            self._emit(f"bool init_v_{ident} = false;")
            if name in self.global_names:
                self._emit(f"v_{ident} = g_{ident}; init_v_{ident} = init_g_{ident};")
        for index, name in enumerate(function.params):
            ident = self._ident(name)
            self._emit(f"v_{ident} = a{index}; init_v_{ident} = true;")
        self._emit_statements(function.body)
        self._emit("return z_leave(z_none());")
        self.indent = 0
        self._emit("}")
        self._emit("")

    def _emit_statements(self, statements: list[Stmt]) -> None:
        for statement in statements:
            if isinstance(statement, Create):
                slot, initialized = self._slot(statement.name, statement.line)
                self._emit(f"if ({initialized}) z_fail({statement.line}, \"Variable already exists\");")
                self._emit(f"{slot} = {self._expr(statement.value)}; {initialized} = true;")
            elif isinstance(statement, Assign):
                slot, initialized = self._slot(statement.name, statement.line)
                self._emit(f"if (!{initialized}) z_fail({statement.line}, \"Unknown variable\");")
                self._emit(f"{slot} = {self._expr(statement.value)};")
            elif isinstance(statement, Display):
                self._emit(f"z_print({self._expr(statement.value)});")
            elif isinstance(statement, CallStatement):
                self._emit(f"(void){self._expr(statement.call)};")
            elif isinstance(statement, Return):
                self._emit(f"return z_leave({self._expr(statement.value)});")
            elif isinstance(statement, If):
                self._emit(f"if (z_truth({self._expr(statement.condition)})) {{")
                self.indent += 1
                self._emit_statements(statement.body)
                self.indent -= 1
                if statement.otherwise:
                    self._emit("} else {")
                    self.indent += 1
                    self._emit_statements(statement.otherwise)
                    self.indent -= 1
                self._emit("}")
            elif isinstance(statement, While):
                loop = self.loop_id
                self.loop_id += 1
                self._emit(f"long long _while_{loop} = 0;")
                self._emit(f"while (z_truth({self._expr(statement.condition)})) {{")
                self.indent += 1
                self._emit_statements(statement.body)
                self._emit(f"if (++_while_{loop} > 1000000) z_fail({statement.line}, \"Loop exceeded one million iterations\");")
                self.indent -= 1
                self._emit("}")
            elif isinstance(statement, Repeat):
                loop = self.loop_id
                self.loop_id += 1
                self._emit(f"long long _repeat_{loop} = z_repeat_count({self._expr(statement.count)}, {statement.line});")
                self._emit(f"for (long long _i_{loop} = 0; _i_{loop} < _repeat_{loop}; ++_i_{loop}) {{")
                self.indent += 1
                self._emit_statements(statement.body)
                self.indent -= 1
                self._emit("}")
            elif isinstance(statement, RangeLoop):
                slot, initialized = self._slot(statement.name, statement.line)
                loop = self.loop_id
                self.loop_id += 1
                self._emit(f"long long _start_{loop} = (long long)z_number({self._expr(statement.start)}, {statement.line});")
                self._emit(f"long long _end_{loop} = (long long)z_number({self._expr(statement.end)}, {statement.line});")
                self._emit(f"for (long long _i_{loop} = _start_{loop}; _i_{loop} <= _end_{loop}; ++_i_{loop}) {{")
                self.indent += 1
                self._emit(f"{slot} = z_num((double)_i_{loop}); {initialized} = true;")
                self._emit_statements(statement.body)
                self.indent -= 1
                self._emit("}")

    def _expr(self, expr: Expr) -> str:
        if isinstance(expr, Literal):
            if isinstance(expr.value, bool):
                return f"z_bool({1 if expr.value else 0})"
            if isinstance(expr.value, (int, float)):
                return f"z_num({float(expr.value)!r})"
            if isinstance(expr.value, str):
                return f"z_str({json.dumps(expr.value, ensure_ascii=True)})"
            return "z_none()"
        if isinstance(expr, Variable):
            slot, initialized = self._slot(expr.name, expr.line)
            return f"z_get({slot}, {initialized}, {expr.line})"
        if isinstance(expr, Input):
            return f"z_input({1 if expr.kind == 'number' else 0}, {expr.line}, {json.dumps(expr.name)})"
        if isinstance(expr, Unary):
            if expr.op == "not":
                return f"z_bool(!z_truth({self._expr(expr.value)}))"
        if isinstance(expr, Binary):
            return (
                f"z_binary({self.OPS[expr.op]}, {self._expr(expr.left)}, "
                f"{self._expr(expr.right)}, {expr.line})"
            )
        if isinstance(expr, Call):
            if expr.name in GAME_FUNCTIONS:
                args = ", ".join(self._expr(argument) for argument in expr.args)
                arguments = f"(Value[]){{ {args} }}" if args else "NULL"
                return (
                    f"z_game({GAME_FUNCTION_IDS[expr.name]}, {len(expr.args)}, "
                    f"{arguments}, {expr.line})"
                )
            function = self.function_map[expr.name]
            if len(expr.args) != len(function.params):
                raise CompileError(
                    f"Line {expr.line}: Function {expr.name} expects {len(function.params)} "
                    f"arguments, got {len(expr.args)}"
                )
            args = ", ".join(self._expr(argument) for argument in expr.args)
            return f"fn_{self._ident(expr.name)}({args})"
        raise CompileError(f"Line {expr.line}: Unsupported expression")

    def _slot(self, name: str, line: int) -> tuple[str, str]:
        if name not in self.current_vars:
            raise CompileError(f"Line {line}: Unknown variable {name!r}")
        variable = self.current_vars[name]
        return variable, f"init_{variable}"

    def _ident(self, name: str) -> str:
        return re.sub(r"\W", "_", name)

    def _emit(self, text: str) -> None:
        self.lines.append("    " * self.indent + text)


def _defined_names(statements: list[Stmt]) -> set[str]:
    names: set[str] = set()
    for statement in statements:
        if isinstance(statement, Create):
            names.add(statement.name)
        elif isinstance(statement, RangeLoop):
            names.add(statement.name)
            names.update(_defined_names(statement.body))
        elif isinstance(statement, (If, While, Repeat)):
            names.update(_defined_names(statement.body))
            if isinstance(statement, If):
                names.update(_defined_names(statement.otherwise))
    return names


def _uses_game_api(value: Any) -> bool:
    if isinstance(value, Call) and value.name in GAME_FUNCTIONS:
        return True
    if isinstance(value, (list, tuple)):
        return any(_uses_game_api(item) for item in value)
    if is_dataclass(value):
        return any(_uses_game_api(getattr(value, item.name)) for item in fields(value))
    return False


def _clean_line(line: str) -> str:
    stripped = line.strip()
    if stripped.endswith(".") and not stripped.lower().startswith(("create ", "display text ")):
        stripped = stripped[:-1].rstrip()
    return stripped


def _add_runtime_helpers(c_source: str) -> str:
    marker = "static Value z_binary("
    helper = (
        "static Value z_get(Value value, bool initialized, int line) {\n"
        "    if (!initialized) z_fail(line, \"Unknown variable\"); return value;\n"
        "}\n"
        "static long long z_repeat_count(Value value, int line) {\n"
        "    double n = z_number(value, line);\n"
        "    if (n < 0 || floor(n) != n) z_fail(line, \"Repeat count must be a non-negative whole number\");\n"
        "    return n > 1000000 ? 1000000 : (long long)n;\n"
        "}\n"
    )
    return c_source.replace(marker, helper + marker, 1)


def compile_source(
    source: str,
    source_path: Path,
    output_path: Path | None = None,
    compiler: str | None = None,
    debug: bool = False,
) -> Path:
    try:
        source = resolve_project_source(source, source_path)
    except ProjectError as exc:
        raise CompileError(str(exc)) from exc
    system = platform.system()
    if system not in {"Windows", "Linux"}:
        raise CompileError(f"Native compilation is not supported on {system}; Windows and Linux are supported")
    module = optimize(ZelixParser(source).parse())
    code_generator = CGenerator(module)
    generated = _add_runtime_helpers(code_generator.generate())
    if compiler:
        compiler_path = shutil.which(compiler) or (compiler if Path(compiler).is_file() else None)
    else:
        candidates = ("cl", "clang", "gcc") if system == "Windows" else ("cc", "gcc", "clang")
        compiler_path = next((shutil.which(candidate) for candidate in candidates if shutil.which(candidate)), None)
    if not compiler_path:
        raise CompileError(
            "No native C compiler found. Install MSVC Build Tools, clang, or GCC and ensure it is on PATH."
        )
    output = output_path or source_path.with_suffix(".exe" if system == "Windows" else "")
    output = output.resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    compiler_name = Path(compiler_path).name.lower()
    is_msvc = system == "Windows" and compiler_name in {"cl", "cl.exe", "clang-cl", "clang-cl.exe"}
    raylib_include = os.environ.get("RAYLIB_INCLUDE_DIR")
    raylib_library = os.environ.get("RAYLIB_LIB_DIR")

    def compiler_command(c_path: Path) -> list[str]:
        if is_msvc:
            command = [compiler_path, "/nologo", "/std:c11"]
            command.extend(["/Zi", "/Od"] if debug else ["/O2"])
            if code_generator.has_game_api and raylib_include:
                command.append(f"/I{raylib_include}")
            command.extend([f"/Fe{output}", str(c_path)])
            if code_generator.has_game_api:
                command.append("/link")
                if debug:
                    command.append("/DEBUG")
                if raylib_library:
                    command.append(f"/LIBPATH:{raylib_library}")
                command.extend([
                    "raylib.lib", "winmm.lib", "gdi32.lib", "opengl32.lib",
                    "user32.lib", "shell32.lib", "ws2_32.lib",
                ])
            elif debug:
                command.extend(["/link", "/DEBUG"])
            return command

        command = [
            compiler_path, "-std=c11",
            *(["-g", "-O0"] if debug else ["-O2"]),
            str(c_path), "-o", str(output),
        ]
        if code_generator.has_game_api and raylib_include:
            command.extend(["-I", raylib_include])
        if raylib_library:
            command.extend(["-L", raylib_library])
        if system == "Windows" and code_generator.has_game_api:
            command.extend(["-lraylib", "-lopengl32", "-lgdi32", "-lwinmm", "-lws2_32", "-lm"])
        elif system == "Linux":
            if code_generator.has_game_api:
                command.extend(["-lraylib", "-lGL", "-lm", "-lpthread", "-ldl", "-lrt", "-lX11"])
            else:
                command.append("-lm")
        elif code_generator.has_game_api:
            command.extend(["-lraylib", "-lm"])
        elif system == "Windows":
            command.append("-lm")
        return command

    try:
        if debug:
            c_path = output.with_name(output.name + ".zelix.c")
            c_path.write_text(generated, encoding="utf-8")
            command = compiler_command(c_path)
            result = subprocess.run(command, capture_output=True, text=True, check=False)
        else:
            with tempfile.TemporaryDirectory(prefix="zelix-") as temp_dir:
                c_path = Path(temp_dir) / "program.c"
                c_path.write_text(generated, encoding="utf-8")
                command = compiler_command(c_path)
                result = subprocess.run(command, capture_output=True, text=True, check=False)
    except OSError as exc:
        raise CompileError(f"Could not write generated source or run native compiler: {exc}") from exc
    if result.returncode:
        diagnostics = (result.stderr or result.stdout).strip()
        raise CompileError(
            f"Native compiler failed with exit code {result.returncode}"
            + (f":\n{diagnostics}" if diagnostics else "")
        )
    return output


def compile_file(
    source_path: Path,
    output_path: Path | None = None,
    compiler: str | None = None,
    debug: bool = False,
) -> tuple[Path, str]:
    try:
        source = source_path.read_text(encoding="utf-8")
    except OSError as exc:
        raise CompileError(f"Cannot read {source_path}: {exc}") from exc
    try:
        source = resolve_project_source(source, source_path)
    except ProjectError as exc:
        raise CompileError(str(exc)) from exc
    module = optimize(ZelixParser(source).parse())
    ir = format_ir(module)
    output = compile_source(source, source_path, output_path, compiler, debug)
    return output, ir


def emit_ir_file(source_path: Path) -> str:
    try:
        source = source_path.read_text(encoding="utf-8")
    except OSError as exc:
        raise CompileError(f"Cannot read {source_path}: {exc}") from exc
    try:
        source = resolve_project_source(source, source_path)
    except ProjectError as exc:
        raise CompileError(str(exc)) from exc
    return format_ir(optimize(ZelixParser(source).parse()))


def validate_source(source: str) -> None:
    module = optimize(ZelixParser(source).parse())
    CGenerator(module).generate()


def validate_file(source_path: Path) -> None:
    if source_path.is_dir():
        from project import project_entry

        try:
            source_path = project_entry(source_path)
        except ProjectError as exc:
            raise CompileError(str(exc)) from exc
    try:
        source = source_path.read_text(encoding="utf-8")
    except OSError as exc:
        raise CompileError(f"Cannot read {source_path}: {exc}") from exc
    try:
        source = resolve_project_source(source, source_path)
    except ProjectError as exc:
        raise CompileError(str(exc)) from exc
    validate_source(source)
