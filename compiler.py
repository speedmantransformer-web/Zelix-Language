"""Zelix IR, optimizer, and native C backend."""

from __future__ import annotations

import ast
import copy
import json
import operator
import os
import platform
import re
import shutil
import subprocess
import tempfile
from dataclasses import fields, is_dataclass
from pathlib import Path
from typing import Any

from game_backend import GAME_FUNCTIONS, GAME_FUNCTION_IDS, GAME_RUNTIME_C
from project import ProjectError, resolve_project_source
from syntax import (
    Assign, Await, Binary, Call, CallStatement, Create, Display, Expr, FunctionIR, If,
    Input, Lexer, Literal, ModuleIR, RangeLoop, Repeat, Return, Spawn, Stmt, Unary,
    Variable, While, parse_source,
)
from typesys import TypeCheckError, TypeChecker, parse_type


class CompileError(Exception):
    pass


class ExpressionIRParser:
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
        try:
            return [
                token.value
                for token in Lexer(source, self.line).tokenize()
                if token.value not in {",", "."}
            ]
        except SyntaxError as exc:
            raise CompileError(str(exc)) from exc

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
    FUNCTION_RE = re.compile(
        r"(?i)^(async\s+)?function\s+([A-Za-z_]\w*)"
        r"(?:<([A-Za-z_]\w*(?:\s*,\s*[A-Za-z_]\w*)*)>)?"
        r"(?:\s+taking\s+(.+?))?(?:\s+returning\s+(.+))?$"
    )
    TEXT_RE = re.compile(r"(?is)^text\s+(.*?)\s+end\s+text$")
    BUILTIN_FUNCTIONS = {
        "list", "map", "set", "tuple", "empty_list", "empty_map", "empty_set",
        "append", "insert", "add_to_set", "put", "get", "remove", "contains",
        "length", "keys", "values", "channel", "send", "receive", "close_channel",
        "sleep", "spawn_thread",
    }

    def __init__(self, source: str):
        self.lines = source.splitlines()
        self.function_sources: list[tuple] = []
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
            name = match.group(2).lower()
            if name in GAME_FUNCTIONS or name in self.BUILTIN_FUNCTIONS:
                raise CompileError(f"Line {index + 1}: {name!r} is a reserved function name")
            if name in self.function_names:
                raise CompileError(f"Line {index + 1}: Function {name!r} is already defined")
            params = []
            param_types = {}
            generic_params = (
                [item.strip() for item in match.group(3).split(",")]
                if match.group(3) else []
            )
            if len(set(generic_params)) != len(generic_params):
                raise CompileError(f"Line {index + 1}: Generic type parameters must be unique")
            if match.group(4):
                for part in re.split(r"\s+and\s+", match.group(4).strip()):
                    parameter = re.fullmatch(
                        r"(?is)\s*([A-Za-z_]\w*)(?:\s+as\s+(.+))?\s*",
                        part,
                    )
                    if not parameter:
                        raise CompileError(
                            f"Line {index + 1}: Invalid parameter declaration {part!r}"
                        )
                    param_name = parameter.group(1).lower()
                    params.append(param_name)
                    if parameter.group(2):
                        try:
                            param_types[param_name] = str(parse_type(parameter.group(2)))
                        except TypeCheckError as exc:
                            raise CompileError(f"Line {index + 1}: {exc}") from exc
            if len(set(params)) != len(params):
                raise CompileError(f"Line {index + 1}: Function parameters must be unique")
            return_type = match.group(5)
            if return_type:
                try:
                    return_type = str(parse_type(return_type))
                except TypeCheckError as exc:
                    raise CompileError(f"Line {index + 1}: {exc}") from exc
            end = index + 1
            depth = 1
            while end < len(self.lines):
                candidate = _clean_line(self.lines[end]).lower()
                if candidate.startswith(("function ", "async function ")):
                    depth += 1
                elif candidate == "end function":
                    depth -= 1
                    if depth == 0:
                        break
                end += 1
            if end == len(self.lines):
                raise CompileError(f"Line {index + 1}: Function {name} is missing end function")
            numbered_body = [(line + 1, self.lines[line]) for line in range(index + 1, end)]
            self.function_sources.append((
                name, params, numbered_body, index + 1, param_types,
                return_type, bool(match.group(1)), generic_params,
            ))
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
                param_types,
                return_type,
                is_async,
                generic_params,
            )
            for name, params, lines, line, param_types, return_type, is_async, generic_params
            in self.function_sources
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
                    type_annotation = None
                else:
                    type_annotation = None
                    typed_value = re.match(r"(?is)^(.+?)\s+with\s+(.+)$", value)
                    if typed_value:
                        try:
                            type_annotation = str(parse_type(typed_value.group(1)))
                            value = typed_value.group(2).strip()
                        except TypeCheckError:
                            pass
                    expr = self._expression(value, line)
                self.index += 1
                statements.append(Create(line, name, expr, type_annotation))
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
            if lower.startswith("await "):
                self.index += 1
                statements.append(CallStatement(line, self._expression(text, line)))
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
        source = _unwrap_parentheses(source.strip())
        await_match = re.match(r"(?is)^await\s+(.+)$", source)
        if await_match:
            return Await(line, self._expression(await_match.group(1), line))
        spawn_match = re.match(r"(?is)^spawn\s+([A-Za-z_]\w*)(?:\s+with\s+(.+))?$", source)
        if spawn_match:
            return Spawn(
                line,
                self._call(spawn_match.group(1), spawn_match.group(2) or "", line),
            )
        text_match = ZelixParser.TEXT_RE.match(source.strip())
        if text_match:
            return Literal(line, text_match.group(1))
        call_match = re.match(
            r"(?is)^([A-Za-z_]\w*)\s+with(?:\s+(.+))?$", source.strip(),
        )
        if call_match and (
            call_match.group(1).lower() in self.functions
            or call_match.group(1).lower() in GAME_FUNCTIONS
            or call_match.group(1).lower() in ZelixParser.BUILTIN_FUNCTIONS
        ):
            return self._call(call_match.group(1), call_match.group(2) or "", line)
        name = source.strip().lower()
        if name in GAME_FUNCTIONS and GAME_FUNCTIONS[name] == 0:
            return self._call(name, "", line)
        callable_names = self.functions | {
            name for name, arity in GAME_FUNCTIONS.items() if arity == 0
        }
        return ExpressionIRParser(source, line, callable_names).parse()

    def _call(self, name: str, source: str, line: int) -> Call:
        name = name.lower()
        if (
            name not in self.functions and name not in GAME_FUNCTIONS
            and name not in ZelixParser.BUILTIN_FUNCTIONS
        ):
            raise CompileError(f"Line {line}: Unknown function {name!r}")
        parts = _split_call_arguments(source)
        if name in GAME_FUNCTIONS and len(parts) != GAME_FUNCTIONS[name]:
            raise CompileError(
                f"Line {line}: Game API {name} expects {GAME_FUNCTIONS[name]} "
                f"arguments, got {len(parts)}"
            )
        if name == "spawn_thread":
            if not parts or not re.fullmatch(r"[A-Za-z_]\w*", parts[0]):
                raise CompileError(
                    f"Line {line}: spawn_thread expects a function name followed by arguments"
                )
            arguments = [Literal(line, parts[0].lower())]
            arguments.extend(self._expression(part, line) for part in parts[1:])
            return Call(line, name, arguments)
        return Call(line, name, [self._expression(part, line) for part in parts])


def optimize(module: ModuleIR, inline: bool = True) -> ModuleIR:
    module.body = _optimize_statements(module.body)
    for function in module.functions:
        function.body = _optimize_statements(function.body)
    if inline:
        _inline_small_functions(module)
    return module


def _unwrap_parentheses(source: str) -> str:
    while source.startswith("(") and source.endswith(")"):
        depth = 0
        quoted = None
        escaped = False
        encloses_all = True
        for index, character in enumerate(source):
            if quoted:
                if escaped:
                    escaped = False
                elif character == "\\":
                    escaped = True
                elif character == quoted:
                    quoted = None
                continue
            if character in {"'", '"'}:
                quoted = character
            elif character == "(":
                depth += 1
            elif character == ")":
                depth -= 1
                if depth == 0 and index != len(source) - 1:
                    encloses_all = False
                    break
        if not encloses_all or depth != 0:
            break
        source = source[1:-1].strip()
    return source


def _split_call_arguments(source: str) -> list[str]:
    arguments = []
    start = 0
    depth = 0
    index = 0
    while index < len(source):
        character = source[index]
        if character in {"'", '"'}:
            quote = character
            index += 1
            while index < len(source):
                if source[index] == "\\":
                    index += 2
                elif source[index] == quote:
                    index += 1
                    break
                else:
                    index += 1
            continue
        if re.match(r"(?i)text\s+", source[index:]):
            end = re.search(r"(?i)\bend\s+text\b", source[index:])
            if end:
                index += end.end()
                continue
        if character == "(":
            depth += 1
            index += 1
            continue
        if character == ")":
            depth = max(0, depth - 1)
            index += 1
            continue
        if (
            depth == 0
            and source[index:index + 3].lower() == "and"
            and (index == 0 or source[index - 1].isspace())
            and (index + 3 == len(source) or source[index + 3].isspace())
        ):
            arguments.append(source[start:index].strip())
            index += 3
            start = index
            continue
        index += 1
    if source[start:].strip():
        arguments.append(source[start:].strip())
    return arguments


def _expression_cost(expression: Expr) -> int:
    if isinstance(expression, (Literal, Variable)):
        return 1
    if isinstance(expression, Unary):
        return 1 + _expression_cost(expression.value)
    if isinstance(expression, Binary):
        return 1 + _expression_cost(expression.left) + _expression_cost(expression.right)
    if isinstance(expression, Await):
        return 100
    if isinstance(expression, Spawn):
        return 100
    return 100


def _substitute_expression(
    expression: Expr,
    substitutions: dict[str, Expr],
    call_line: int,
) -> Expr:
    if isinstance(expression, Variable):
        replacement = substitutions.get(expression.name)
        if replacement is None:
            return Variable(call_line, expression.name)
        return _reline_expression(copy.deepcopy(replacement), call_line)
    if isinstance(expression, Unary):
        return Unary(
            call_line, expression.op,
            _substitute_expression(expression.value, substitutions, call_line),
        )
    if isinstance(expression, Binary):
        return Binary(
            call_line, expression.op,
            _substitute_expression(expression.left, substitutions, call_line),
            _substitute_expression(expression.right, substitutions, call_line),
        )
    return _reline_expression(copy.deepcopy(expression), call_line)


def _reline_expression(expression: Expr, line: int) -> Expr:
    expression.line = line
    if isinstance(expression, Unary):
        expression.value = _reline_expression(expression.value, line)
    elif isinstance(expression, Binary):
        expression.left = _reline_expression(expression.left, line)
        expression.right = _reline_expression(expression.right, line)
    return expression


def _inline_small_functions(module: ModuleIR) -> None:
    candidates = {}
    for function in module.functions:
        if len(function.body) != 1 or not isinstance(function.body[0], Return):
            continue
        expression = function.body[0].value
        if _expression_cost(expression) > 12:
            continue
        names = _expression_variables(expression)
        if names <= set(function.params):
            candidates[function.name] = (function.params, expression)

    def inline(expression: Expr, depth: int = 0) -> Expr:
        if isinstance(expression, Unary):
            expression.value = inline(expression.value, depth)
        elif isinstance(expression, Binary):
            expression.left = inline(expression.left, depth)
            expression.right = inline(expression.right, depth)
        elif isinstance(expression, Call):
            expression.args = [inline(argument, depth) for argument in expression.args]
            candidate = candidates.get(expression.name)
            if candidate and depth < 8 and all(
                isinstance(argument, (Literal, Variable)) for argument in expression.args
            ):
                parameters, body = candidate
                if len(parameters) == len(expression.args):
                    substitutions = dict(zip(parameters, expression.args))
                    return inline(
                        _substitute_expression(body, substitutions, expression.line),
                        depth + 1,
                    )
        return expression

    def visit(statements: list[Stmt]) -> None:
        for statement in statements:
            if isinstance(statement, (Create, Assign, Display, Return)):
                statement.value = inline(statement.value)
            elif isinstance(statement, CallStatement):
                statement.call = inline(statement.call)
            elif isinstance(statement, If):
                statement.condition = inline(statement.condition)
                visit(statement.body)
                visit(statement.otherwise)
            elif isinstance(statement, (While, Repeat)):
                if isinstance(statement, While):
                    statement.condition = inline(statement.condition)
                else:
                    statement.count = inline(statement.count)
                visit(statement.body)
            elif isinstance(statement, RangeLoop):
                statement.start = inline(statement.start)
                statement.end = inline(statement.end)
                visit(statement.body)

    for function in module.functions:
        visit(function.body)
    visit(module.body)


def _expression_variables(expression: Expr) -> set[str]:
    if isinstance(expression, Variable):
        return {expression.name}
    if isinstance(expression, Unary):
        return _expression_variables(expression.value)
    if isinstance(expression, Binary):
        return _expression_variables(expression.left) | _expression_variables(expression.right)
    return set()


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
    elif isinstance(expr, Await):
        expr.value = _fold(expr.value)
    elif isinstance(expr, Spawn):
        expr.call = _fold(expr.call)
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
    if isinstance(expr, Await):
        return f"await {_format_expr(expr.value)}"
    if isinstance(expr, Spawn):
        return f"spawn {_format_expr(expr.call)}"
    raise CompileError(f"Unsupported IR expression: {type(expr).__name__}")


class CGenerator:
    OPS = {
        "add": "Z_ADD", "sub": "Z_SUB", "mul": "Z_MUL", "div": "Z_DIV",
        "mod": "Z_MOD", "eq": "Z_EQ", "ne": "Z_NE", "gt": "Z_GT",
        "lt": "Z_LT", "gte": "Z_GTE", "lte": "Z_LTE", "and": "Z_AND",
        "or": "Z_OR",
    }

    def __init__(self, module: ModuleIR, asset_root: Path | None = None):
        self.module = module
        self.lines: list[str] = []
        self.indent = 0
        self.global_names = sorted(_defined_names(module.body))
        self.function_map = {function.name: function for function in module.functions}
        self.current_vars: dict[str, str] = {}
        self.loop_id = 0
        self.has_game_api = _uses_game_api(module)
        self.asset_root = (asset_root or Path.cwd()).resolve()

    def generate(self) -> str:
        self.lines = [
            "#define _POSIX_C_SOURCE 199309L",
            "#include <ctype.h>", "#include <errno.h>", "#include <math.h>", "#include <stdbool.h>",
            "#include <stdio.h>", "#include <stdlib.h>", "#include <string.h>",
            "#include <stdint.h>", "#include <stdatomic.h>",
            "#include <time.h>",
            "#ifdef _WIN32", "#include <windows.h>",
            "typedef CRITICAL_SECTION ZMutex; typedef CONDITION_VARIABLE ZCondition;",
            "typedef HANDLE ZThread;",
            "#else", "#include <pthread.h>",
            "typedef pthread_mutex_t ZMutex; typedef pthread_cond_t ZCondition;",
            "typedef pthread_t ZThread;", "#endif", "",
            "typedef enum { Z_NONE, Z_NUMBER, Z_BOOLEAN, Z_STRING, Z_LIST, Z_MAP, Z_SET, Z_TUPLE, Z_TASK, Z_CHANNEL } ZType;",
            "typedef struct Value Value;",
            "typedef struct ZTask ZTask; typedef struct ZChannel ZChannel;",
            "typedef struct ZCollection { ZType type; size_t length, capacity; Value *items; struct ZCollection *next; } ZCollection;",
            "struct Value { ZType type; double number; const char *string; ZCollection *collection; ZTask *task; ZChannel *channel; };",
            "typedef Value (*ZTaskFunction)(Value *, int);",
            "struct ZTask { ZThread thread; ZMutex lock; bool joined; ZTaskFunction function; Value result; Value *args; int argc; struct ZTask *next; };",
            "struct ZChannel { ZMutex lock; ZCondition changed; bool closed, bounded; size_t capacity, length, head; Value *items; struct ZChannel *next; };",
            "enum { Z_ADD, Z_SUB, Z_MUL, Z_DIV, Z_MOD, Z_EQ, Z_NE, Z_GT, Z_LT, Z_GTE, Z_LTE, Z_AND, Z_OR };",
            "static ZCollection *z_collections = NULL;",
            "static ZTask *z_tasks = NULL; static ZChannel *z_channels = NULL;",
            "static atomic_flag z_registry_lock = ATOMIC_FLAG_INIT;",
            "static void z_task_cleanup(void); static void z_channel_cleanup(void);",
            "static void z_lock_registry(void) { while (atomic_flag_test_and_set_explicit(&z_registry_lock, memory_order_acquire)) { } }",
            "static void z_unlock_registry(void) { atomic_flag_clear_explicit(&z_registry_lock, memory_order_release); }",
            "#ifdef _WIN32",
            "static void z_mutex_init(ZMutex *m) { InitializeCriticalSection(m); }",
            "static void z_mutex_destroy(ZMutex *m) { DeleteCriticalSection(m); }",
            "static void z_mutex_lock(ZMutex *m) { EnterCriticalSection(m); }",
            "static void z_mutex_unlock(ZMutex *m) { LeaveCriticalSection(m); }",
            "static void z_condition_init(ZCondition *c) { InitializeConditionVariable(c); }",
            "static void z_condition_destroy(ZCondition *c) { (void)c; }",
            "static void z_condition_wait(ZCondition *c, ZMutex *m) { (void)SleepConditionVariableCS(c, m, INFINITE); }",
            "static void z_condition_wake(ZCondition *c) { WakeAllConditionVariable(c); }",
            "#else",
            "static void z_mutex_init(ZMutex *m) { (void)pthread_mutex_init(m, NULL); }",
            "static void z_mutex_destroy(ZMutex *m) { (void)pthread_mutex_destroy(m); }",
            "static void z_mutex_lock(ZMutex *m) { (void)pthread_mutex_lock(m); }",
            "static void z_mutex_unlock(ZMutex *m) { (void)pthread_mutex_unlock(m); }",
            "static void z_condition_init(ZCondition *c) { (void)pthread_cond_init(c, NULL); }",
            "static void z_condition_destroy(ZCondition *c) { (void)pthread_cond_destroy(c); }",
            "static void z_condition_wait(ZCondition *c, ZMutex *m) { (void)pthread_cond_wait(c, m); }",
            "static void z_condition_wake(ZCondition *c) { (void)pthread_cond_broadcast(c); }",
            "#endif",
            "static char **z_owned_strings = NULL; static size_t z_owned_string_count = 0;",
            "static atomic_bool z_runtime_failed = false;",
            "static Value z_none(void) { Value v = { Z_NONE, 0, NULL, NULL, NULL, NULL }; return v; }",
            "static Value z_num(double n) { Value v = { Z_NUMBER, n, NULL, NULL, NULL, NULL }; return v; }",
            "static Value z_bool(int b) { Value v = { Z_BOOLEAN, b != 0, NULL, NULL, NULL, NULL }; return v; }",
            "static Value z_str(const char *s) { Value v = { Z_STRING, 0, s, NULL, NULL, NULL }; return v; }",
            "static void *z_alloc(size_t size) {",
            "    void *p = malloc(size ? size : 1); if (!p) { fputs(\"Zelix error: out of memory\\n\", stderr); exit(1); }",
            "    z_lock_registry();",
            "    char **next = (char **)realloc(z_owned_strings, (z_owned_string_count + 1) * sizeof(char *));",
            "    if (!next) { z_unlock_registry(); free(p); fputs(\"Zelix error: out of memory\\n\", stderr); exit(1); }",
            "    z_owned_strings = next; z_owned_strings[z_owned_string_count++] = (char *)p; z_unlock_registry(); return p;",
            "}",
            "static void z_runtime_cleanup(void) {",
            "    if (atomic_load_explicit(&z_runtime_failed, memory_order_acquire)) return;",
            "    z_task_cleanup(); z_channel_cleanup();",
            "    while (z_collections) { ZCollection *next = z_collections->next; free(z_collections->items); free(z_collections); z_collections = next; }",
            "    for (size_t i = 0; i < z_owned_string_count; ++i) free(z_owned_strings[i]);",
            "    free(z_owned_strings); z_owned_strings = NULL; z_owned_string_count = 0;",
            "}",
            "static void z_fail(int line, const char *message) {",
            "    atomic_store_explicit(&z_runtime_failed, true, memory_order_release);",
            "    fprintf(stderr, \"Zelix error: Line %d: %s\\n\", line, message);",
            "    exit(1);",
            "}",
            "#ifdef _WIN32",
            "static DWORD WINAPI z_task_entry(LPVOID context) { ZTask *task = (ZTask *)context; task->result = task->function(task->args, task->argc); return 0; }",
            "#else",
            "static void *z_task_entry(void *context) { ZTask *task = (ZTask *)context; task->result = task->function(task->args, task->argc); return NULL; }",
            "#endif",
            "static Value z_task_spawn(ZTaskFunction function, int argc, Value *args, int line) {",
            "    ZTask *task = (ZTask *)calloc(1, sizeof(ZTask)); if (!task) z_fail(line, \"Out of memory creating task\");",
            "    task->function = function; task->argc = argc; task->result = z_none(); z_mutex_init(&task->lock);",
            "    if (argc) { task->args = (Value *)malloc((size_t)argc * sizeof(Value)); if (!task->args) z_fail(line, \"Out of memory copying task arguments\"); memcpy(task->args, args, (size_t)argc * sizeof(Value)); }",
            "    z_lock_registry(); task->next = z_tasks; z_tasks = task; z_unlock_registry();",
            "#ifdef _WIN32",
            "    task->thread = CreateThread(NULL, 0, z_task_entry, task, 0, NULL); if (!task->thread) z_fail(line, \"Could not start task thread\");",
            "#else",
            "    if (pthread_create(&task->thread, NULL, z_task_entry, task) != 0) z_fail(line, \"Could not start task thread\");",
            "#endif",
            "    Value result = { Z_TASK, 0, NULL, NULL, task, NULL }; return result;",
            "}",
            "static Value z_task_await(Value value, int line) {",
            "    if (value.type != Z_TASK || !value.task) z_fail(line, \"await expects a task\"); ZTask *task = value.task;",
            "    z_mutex_lock(&task->lock); if (!task->joined) {",
            "#ifdef _WIN32",
            "        (void)WaitForSingleObject(task->thread, INFINITE); CloseHandle(task->thread);",
            "#else",
            "        if (pthread_join(task->thread, NULL) != 0) z_fail(line, \"Could not join task\");",
            "#endif",
            "        task->joined = true;",
            "    } z_mutex_unlock(&task->lock); return task->result;",
            "}",
            "static void z_task_cleanup(void) {",
            "    for (;;) { z_lock_registry(); ZTask *task = z_tasks; if (task) z_tasks = task->next; z_unlock_registry(); if (!task) break; z_mutex_lock(&task->lock); if (!task->joined) {",
            "#ifdef _WIN32",
            "        (void)WaitForSingleObject(task->thread, INFINITE); CloseHandle(task->thread);",
            "#else",
            "        (void)pthread_join(task->thread, NULL);",
            "#endif",
            "        task->joined = true; } z_mutex_unlock(&task->lock); z_mutex_destroy(&task->lock); free(task->args); free(task); }",
            "}",
            "#ifdef _MSC_VER", "#define Z_THREAD_LOCAL __declspec(thread)",
            "#else", "#define Z_THREAD_LOCAL _Thread_local", "#endif",
            "static Z_THREAD_LOCAL int z_call_depth = 0;",
            "static Value z_leave(Value value) { --z_call_depth; return value; }",
            "static int z_truth(Value v) {",
            "    if (v.type == Z_BOOLEAN || v.type == Z_NUMBER) return v.number != 0;",
            "    if (v.type == Z_STRING) return v.string[0] != '\\0';",
            "    if (v.type == Z_LIST || v.type == Z_MAP || v.type == Z_SET || v.type == Z_TUPLE) return v.collection && v.collection->length != 0;",
            "    if (v.type == Z_TASK) return v.task != NULL;",
            "    if (v.type == Z_CHANNEL) return v.channel != NULL;",
            "    return 0;",
            "}",
            "static double z_number(Value v, int line) {",
            "    if (v.type == Z_NUMBER || v.type == Z_BOOLEAN) return v.number;",
            "    z_fail(line, \"Expected a number\"); return 0;",
            "}",
            "static Value z_channel_create(Value capacity_value, int line) {",
            "    double numeric = z_number(capacity_value, line); if (!isfinite(numeric) || floor(numeric) != numeric || numeric < 0 || numeric > 1000000) z_fail(line, \"Channel capacity must be a whole number from 0 to 1000000\");",
            "    ZChannel *channel = (ZChannel *)calloc(1, sizeof(ZChannel)); if (!channel) z_fail(line, \"Out of memory creating channel\");",
            "    channel->bounded = numeric > 0; channel->capacity = channel->bounded ? (size_t)numeric : 4; channel->items = (Value *)malloc(channel->capacity * sizeof(Value)); if (!channel->items) z_fail(line, \"Out of memory allocating channel buffer\");",
            "    z_mutex_init(&channel->lock); z_condition_init(&channel->changed); z_lock_registry(); channel->next = z_channels; z_channels = channel; z_unlock_registry();",
            "    Value result = { Z_CHANNEL, 0, NULL, NULL, NULL, channel }; return result;",
            "}",
            "static Value z_channel_send(Value *args, int argc, int line) {",
            "    if (argc != 2 || args[0].type != Z_CHANNEL || !args[0].channel) z_fail(line, \"send expects a channel and a value\"); ZChannel *c = args[0].channel; z_mutex_lock(&c->lock);",
            "    while (c->bounded && c->length == c->capacity && !c->closed) z_condition_wait(&c->changed, &c->lock); if (c->closed) z_fail(line, \"Cannot send to a closed channel\");",
            "    if (!c->bounded && c->length == c->capacity) { if (c->capacity > SIZE_MAX / 2 / sizeof(Value)) z_fail(line, \"Channel capacity overflow\"); size_t capacity = c->capacity * 2; Value *items = (Value *)malloc(capacity * sizeof(Value)); if (!items) z_fail(line, \"Out of memory growing channel\"); for (size_t i = 0; i < c->length; ++i) items[i] = c->items[(c->head + i) % c->capacity]; free(c->items); c->items = items; c->capacity = capacity; c->head = 0; }",
            "    c->items[(c->head + c->length) % c->capacity] = args[1]; ++c->length; z_condition_wake(&c->changed); z_mutex_unlock(&c->lock); return z_none();",
            "}",
            "static Value z_channel_receive(Value *args, int argc, int line) {",
            "    if (argc != 1 || args[0].type != Z_CHANNEL || !args[0].channel) z_fail(line, \"receive expects a channel\"); ZChannel *c = args[0].channel; z_mutex_lock(&c->lock);",
            "    while (!c->length && !c->closed) z_condition_wait(&c->changed, &c->lock); if (!c->length) z_fail(line, \"Channel is closed and empty\"); Value result = c->items[c->head]; c->head = (c->head + 1) % c->capacity; --c->length; z_condition_wake(&c->changed); z_mutex_unlock(&c->lock); return result;",
            "}",
            "static Value z_channel_close(Value value, int line) {",
            "    if (value.type != Z_CHANNEL || !value.channel) z_fail(line, \"close_channel expects a channel\"); ZChannel *c = value.channel; z_mutex_lock(&c->lock); if (c->closed) z_fail(line, \"Channel is already closed\"); c->closed = true; z_condition_wake(&c->changed); z_mutex_unlock(&c->lock); return z_none();",
            "}",
            "static Value z_async_send(Value *args, int argc) { if (argc != 3) z_fail(0, \"Invalid send task\"); return z_channel_send(args, 2, (int)z_number(args[2], 0)); }",
            "static Value z_async_receive(Value *args, int argc) { if (argc != 2) z_fail(0, \"Invalid receive task\"); return z_channel_receive(args, 1, (int)z_number(args[1], 0)); }",
            "static Value z_async_sleep(Value *args, int argc) {",
            "    if (argc != 2) z_fail(0, \"Invalid sleep task\"); double seconds = z_number(args[0], 0); int line = (int)z_number(args[1], 0); if (!isfinite(seconds) || seconds < 0 || seconds > 86400) z_fail(line, \"sleep duration must be from 0 to 86400 seconds\");",
            "#ifdef _WIN32",
            "    Sleep((DWORD)(seconds * 1000.0));",
            "#else",
            "    struct timespec request = { (time_t)seconds, (long)((seconds - floor(seconds)) * 1000000000.0) }; int result; do { result = nanosleep(&request, &request); } while (result != 0 && errno == EINTR); if (result != 0) z_fail(line, \"sleep failed\");",
            "#endif",
            "    return z_none();",
            "}",
            "static void z_channel_cleanup(void) { ZChannel *c = z_channels; while (c) { ZChannel *next = c->next; z_condition_destroy(&c->changed); z_mutex_destroy(&c->lock); free(c->items); free(c); c = next; } z_channels = NULL; }",
            "static const char *z_text(Value v, char *buffer, size_t size) {",
            "    if (v.type == Z_STRING) return v.string;",
            "    if (v.type == Z_BOOLEAN) return v.number ? \"True\" : \"False\";",
            "    if (v.type == Z_NONE) return \"None\";",
            "    if (v.type == Z_TASK) return \"Task\";",
            "    if (v.type == Z_CHANNEL) return \"Channel\";",
            "    snprintf(buffer, size, \"%.15g\", v.number); return buffer;",
            "}",
            "static void z_print(Value v) {",
            "    char buffer[64]; puts(z_text(v, buffer, sizeof buffer));",
            "}",
            "static char *z_copy(const char *s) {",
            "    size_t n = strlen(s) + 1; char *copy = (char *)z_alloc(n);",
            "    memcpy(copy, s, n); return copy;",
            "}",
            "static int z_value_equal(Value a, Value b) {",
            "    if (a.type != b.type) return 0;",
            "    if (a.type == Z_STRING) return strcmp(a.string, b.string) == 0;",
            "    if (a.type == Z_NUMBER || a.type == Z_BOOLEAN) return a.number == b.number;",
            "    if (a.type == Z_NONE) return 1;",
            "    return a.collection == b.collection;",
            "}",
            "static Value z_collection(ZType type, size_t count, Value *items, int line) {",
            "    if ((type == Z_MAP && count % 2) || (type == Z_MAP && count / 2 > SIZE_MAX / sizeof(Value))) z_fail(line, \"Invalid map size\");",
            "    ZCollection *collection = (ZCollection *)calloc(1, sizeof(ZCollection));",
            "    if (!collection) z_fail(line, \"Out of memory allocating collection\");",
            "    collection->type = type; z_lock_registry(); collection->next = z_collections; z_collections = collection; z_unlock_registry();",
            "    collection->capacity = count; collection->length = 0;",
            "    if (count) { collection->items = (Value *)malloc(count * sizeof(Value)); if (!collection->items) z_fail(line, \"Out of memory allocating collection items\"); }",
            "    if (type == Z_SET) { for (size_t i = 0; i < count; ++i) { bool found = false; for (size_t j = 0; j < collection->length; ++j) if (z_value_equal(collection->items[j], items[i])) found = true; if (!found) collection->items[collection->length++] = items[i]; } }",
            "    else if (type == Z_MAP) { for (size_t i = 0; i < count; i += 2) { size_t found = collection->length; for (size_t j = 0; j < collection->length; ++j) if (z_value_equal(collection->items[j * 2], items[i])) { found = j; break; } if (found < collection->length) collection->items[found * 2 + 1] = items[i + 1]; else { collection->items[collection->length * 2] = items[i]; collection->items[collection->length * 2 + 1] = items[i + 1]; ++collection->length; } } }",
            "    else { if (count) memcpy(collection->items, items, count * sizeof(Value)); collection->length = count; }",
            "    Value result = { type, 0, NULL, collection, NULL, NULL }; return result;",
            "}",
            "static size_t z_collection_index(Value index, size_t length, int line, bool allow_end) {",
            "    double number = z_number(index, line); if (!isfinite(number) || floor(number) != number || number < 0 || number > (double)SIZE_MAX) z_fail(line, \"Collection index must be a non-negative whole number\");",
            "    size_t value = (size_t)number; if (allow_end ? value > length : value >= length) z_fail(line, \"Collection index is out of range\"); return value;",
            "}",
            "static Value z_collection_call(const char *name, int argc, Value *args, int line) {",
            "    if (!strcmp(name, \"list\")) return z_collection(Z_LIST, (size_t)argc, args, line);",
            "    if (!strcmp(name, \"tuple\")) return z_collection(Z_TUPLE, (size_t)argc, args, line);",
            "    if (!strcmp(name, \"set\")) return z_collection(Z_SET, (size_t)argc, args, line);",
            "    if (!strcmp(name, \"map\")) return z_collection(Z_MAP, (size_t)argc, args, line);",
            "    if (!strcmp(name, \"empty_list\")) return z_collection(Z_LIST, 0, NULL, line);",
            "    if (!strcmp(name, \"empty_set\")) return z_collection(Z_SET, 0, NULL, line);",
            "    if (!strcmp(name, \"empty_map\")) return z_collection(Z_MAP, 0, NULL, line);",
            "    ZCollection *c = argc > 0 ? args[0].collection : NULL;",
            "    if (argc > 0 && args[0].type != Z_LIST && args[0].type != Z_MAP && args[0].type != Z_SET && args[0].type != Z_TUPLE) z_fail(line, \"Expected a collection\");",
            "    if (!strcmp(name, \"length\")) return z_num(c ? (double)c->length : 0);",
            "    if (!strcmp(name, \"append\")) { if (argc != 2 || args[0].type != Z_LIST) z_fail(line, \"append expects a list and a value\"); if (c->length == c->capacity) { size_t capacity = c->capacity ? c->capacity * 2 : 4; if (capacity < c->capacity || capacity > SIZE_MAX / sizeof(Value)) z_fail(line, \"List capacity overflow\"); Value *items = (Value *)realloc(c->items, capacity * sizeof(Value)); if (!items) z_fail(line, \"Out of memory growing list\"); c->items = items; c->capacity = capacity; } c->items[c->length++] = args[1]; return z_none(); }",
            "    if (!strcmp(name, \"add_to_set\")) { if (argc != 2 || args[0].type != Z_SET) z_fail(line, \"add_to_set expects a set and an element\"); for (size_t i = 0; i < c->length; ++i) if (z_value_equal(c->items[i], args[1])) return z_none(); if (c->length == c->capacity) { size_t capacity = c->capacity ? c->capacity * 2 : 4; if (capacity < c->capacity || capacity > SIZE_MAX / sizeof(Value)) z_fail(line, \"Set capacity overflow\"); Value *items = (Value *)realloc(c->items, capacity * sizeof(Value)); if (!items) z_fail(line, \"Out of memory growing set\"); c->items = items; c->capacity = capacity; } c->items[c->length++] = args[1]; return z_none(); }",
            "    if (!strcmp(name, \"put\")) { if (argc != 3 || args[0].type != Z_MAP) z_fail(line, \"put expects a map, key, and value\"); for (size_t i = 0; i < c->length; ++i) if (z_value_equal(c->items[i * 2], args[1])) { c->items[i * 2 + 1] = args[2]; return z_none(); } if (c->length == c->capacity / 2) { size_t capacity = c->capacity ? c->capacity * 2 : 4; if (capacity < c->capacity || capacity > SIZE_MAX / sizeof(Value)) z_fail(line, \"Map capacity overflow\"); Value *items = (Value *)realloc(c->items, capacity * sizeof(Value)); if (!items) z_fail(line, \"Out of memory growing map\"); c->items = items; c->capacity = capacity; } c->items[c->length * 2] = args[1]; c->items[c->length * 2 + 1] = args[2]; ++c->length; return z_none(); }",
            "    if (!strcmp(name, \"insert\")) { if (argc != 3 || args[0].type != Z_LIST) z_fail(line, \"insert expects a list, index, and value\"); size_t at = z_collection_index(args[1], c->length, line, true); if (c->length == c->capacity) { size_t capacity = c->capacity ? c->capacity * 2 : 4; if (capacity < c->capacity || capacity > SIZE_MAX / sizeof(Value)) z_fail(line, \"List capacity overflow\"); Value *items = (Value *)realloc(c->items, capacity * sizeof(Value)); if (!items) z_fail(line, \"Out of memory growing list\"); c->items = items; c->capacity = capacity; } memmove(c->items + at + 1, c->items + at, (c->length - at) * sizeof(Value)); c->items[at] = args[2]; ++c->length; return z_none(); }",
            "    if (!strcmp(name, \"get\")) { if (argc != 2) z_fail(line, \"get expects a collection and key\"); if (args[0].type == Z_MAP) { for (size_t i = 0; i < c->length; ++i) if (z_value_equal(c->items[i * 2], args[1])) return c->items[i * 2 + 1]; z_fail(line, \"Map key not found\"); } if (args[0].type == Z_LIST || args[0].type == Z_TUPLE) return c->items[z_collection_index(args[1], c->length, line, false)]; z_fail(line, \"get expects a list, map, or tuple\"); }",
            "    if (!strcmp(name, \"contains\")) { if (argc != 2) z_fail(line, \"contains expects a collection and value\"); if (args[0].type == Z_MAP) { for (size_t i = 0; i < c->length; ++i) if (z_value_equal(c->items[i * 2], args[1])) return z_bool(1); } else { for (size_t i = 0; i < c->length; ++i) if (z_value_equal(c->items[i], args[1])) return z_bool(1); } return z_bool(0); }",
            "    if (!strcmp(name, \"keys\") || !strcmp(name, \"values\")) { if (argc != 1 || args[0].type != Z_MAP) z_fail(line, \"keys and values expect a map\"); Value *items = c->length ? (Value *)malloc(c->length * sizeof(Value)) : NULL; if (c->length && !items) z_fail(line, \"Out of memory reading map\"); for (size_t i = 0; i < c->length; ++i) items[i] = c->items[i * 2 + (!strcmp(name, \"values\"))]; Value result = z_collection(Z_LIST, c->length, items, line); free(items); return result; }",
            "    if (!strcmp(name, \"remove\")) { if (argc != 2) z_fail(line, \"remove expects a collection and key\"); if (args[0].type == Z_LIST) { size_t at = z_collection_index(args[1], c->length, line, false); memmove(c->items + at, c->items + at + 1, (c->length - at - 1) * sizeof(Value)); --c->length; return z_none(); } if (args[0].type == Z_MAP) { for (size_t i = 0; i < c->length; ++i) if (z_value_equal(c->items[i * 2], args[1])) { memmove(c->items + i * 2, c->items + (i + 1) * 2, (c->length - i - 1) * 2 * sizeof(Value)); --c->length; return z_none(); } z_fail(line, \"Map key not found\"); } if (args[0].type == Z_SET) { for (size_t i = 0; i < c->length; ++i) if (z_value_equal(c->items[i], args[1])) { memmove(c->items + i, c->items + i + 1, (c->length - i - 1) * sizeof(Value)); --c->length; return z_none(); } z_fail(line, \"Set value not found\"); } z_fail(line, \"remove expects a mutable collection\"); }",
            "    z_fail(line, \"Unknown collection operation\"); return z_none();",
            "}",
            "static Value z_binary(int op, Value a, Value b, int line) {",
            "    if (op == Z_AND) return z_bool(z_truth(a) && z_truth(b));",
            "    if (op == Z_OR) return z_bool(z_truth(a) || z_truth(b));",
            "    if (op == Z_ADD && a.type == Z_STRING && b.type == Z_STRING) {",
            "        size_t n = strlen(a.string) + strlen(b.string) + 1;",
            "        char *joined = (char *)z_alloc(n);",
            "        snprintf(joined, n, \"%s%s\", a.string, b.string); return z_str(joined);",
            "    }",
            "    if (op == Z_EQ || op == Z_NE) {",
            "        int equal = 0;",
            "        if (a.type == Z_STRING && b.type == Z_STRING) equal = strcmp(a.string, b.string) == 0;",
            "        else if ((a.type == Z_NUMBER || a.type == Z_BOOLEAN) &&",
            "                 (b.type == Z_NUMBER || b.type == Z_BOOLEAN)) equal = a.number == b.number;",
            "        else if (a.type == b.type) equal = (a.type == Z_LIST || a.type == Z_MAP || a.type == Z_SET || a.type == Z_TUPLE) ? a.collection == b.collection : 1;",
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
            asset_root = str(self.asset_root).replace("\\", "/")
            self.lines.append(f"#define Z_ASSET_ROOT {json.dumps(asset_root, ensure_ascii=True)}")
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
            self._emit(
                f"static Value z_task_fn_{self._ident(function.name)}(Value *args, int argc);"
            )
        if self.module.functions:
            self._emit("")
        for function in self.module.functions:
            self._emit_function(function)
        for function in self.module.functions:
            self._emit_task_wrapper(function)
        self._emit("int main(void) {")
        self.indent = 1
        self._emit("atexit(z_runtime_cleanup);")
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

    def _emit_task_wrapper(self, function: FunctionIR) -> None:
        name = self._ident(function.name)
        self._emit(f"static Value z_task_fn_{name}(Value *args, int argc) {{")
        self.indent = 1
        self._emit(
            f"if (argc != {len(function.params)}) z_fail({function.line}, "
            f"\"Function {function.name} expects {len(function.params)} task arguments\");"
        )
        values = ", ".join(f"args[{index}]" for index in range(len(function.params)))
        self._emit(f"return fn_{name}({values});")
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
            if expr.name == "spawn_thread":
                if not expr.args or not isinstance(expr.args[0], Literal):
                    raise CompileError(
                        f"Line {expr.line}: spawn_thread expects a function name and arguments"
                    )
                target = str(expr.args[0].value)
                args = ", ".join(self._expr(argument) for argument in expr.args[1:])
                arguments = f"(Value[]){{ {args} }}" if args else "NULL"
                return (
                    f"z_task_spawn(z_task_fn_{self._ident(target)}, "
                    f"{len(expr.args) - 1}, {arguments}, {expr.line})"
                )
            if expr.name in ZelixParser.BUILTIN_FUNCTIONS:
                args = ", ".join(self._expr(argument) for argument in expr.args)
                arguments = f"(Value[]){{ {args} }}" if args else "NULL"
                if expr.name == "channel":
                    if len(expr.args) != 1:
                        raise CompileError(f"Line {expr.line}: channel expects a capacity")
                    return f"z_channel_create({args}, {expr.line})"
                if expr.name == "send":
                    return (
                        f"z_task_spawn(z_async_send, 3, "
                        f"(Value[]){{ {args}, z_num({expr.line}) }}, {expr.line})"
                    )
                if expr.name == "receive":
                    return (
                        f"z_task_spawn(z_async_receive, 2, "
                        f"(Value[]){{ {args}, z_num({expr.line}) }}, {expr.line})"
                    )
                if expr.name == "sleep":
                    return (
                        f"z_task_spawn(z_async_sleep, 2, "
                        f"(Value[]){{ {args}, z_num({expr.line}) }}, {expr.line})"
                    )
                if expr.name == "close_channel":
                    if len(expr.args) != 1:
                        raise CompileError(
                            f"Line {expr.line}: close_channel expects one channel"
                        )
                    return (
                        f"z_channel_close({self._expr(expr.args[0])}, {expr.line})"
                    )
                return (
                    f"z_collection_call({json.dumps(expr.name)}, {len(expr.args)}, "
                    f"{arguments}, {expr.line})"
                )
            function = self.function_map[expr.name]
            if len(expr.args) != len(function.params):
                raise CompileError(
                    f"Line {expr.line}: Function {expr.name} expects {len(function.params)} "
                    f"arguments, got {len(expr.args)}"
                )
            args = ", ".join(self._expr(argument) for argument in expr.args)
            if function.is_async:
                arguments = f"(Value[]){{ {args} }}" if args else "NULL"
                return (
                    f"z_task_spawn(z_task_fn_{self._ident(expr.name)}, "
                    f"{len(expr.args)}, {arguments}, {expr.line})"
                )
            return f"fn_{self._ident(expr.name)}({args})"
        if isinstance(expr, Await):
            return f"z_task_await({self._expr(expr.value)}, {expr.line})"
        if isinstance(expr, Spawn):
            target = expr.call.name
            args = ", ".join(self._expr(argument) for argument in expr.call.args)
            arguments = f"(Value[]){{ {args} }}" if args else "NULL"
            return (
                f"z_task_spawn(z_task_fn_{self._ident(target)}, "
                f"{len(expr.call.args)}, {arguments}, {expr.line})"
            )
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


def _validate_asset_paths(module: ModuleIR, asset_root: Path) -> None:
    supported_extensions = {
        "load_texture": {
            ".bmp", ".gif", ".hdr", ".jpeg", ".jpg", ".pic", ".pgm",
            ".png", ".pnm", ".ppm", ".psd", ".qoi", ".tga",
        },
        "load_sound": {".flac", ".mod", ".mp3", ".ogg", ".wav", ".xm"},
    }

    def visit(value: Any) -> None:
        if isinstance(value, Call):
            if value.name in supported_extensions and value.args and isinstance(value.args[0], Literal):
                asset = value.args[0].value
                if isinstance(asset, str):
                    path = Path(asset)
                    candidate = path if path.is_absolute() else asset_root / path
                    extension = candidate.suffix.lower()
                    if extension not in supported_extensions[value.name]:
                        allowed = ", ".join(sorted(supported_extensions[value.name]))
                        raise CompileError(
                            f"Line {value.line}: Unsupported {value.name[5:]} asset format "
                            f"{extension or '(no extension)'!r}; expected one of {allowed}"
                        )
                    if not candidate.is_file():
                        raise CompileError(
                            f"Line {value.line}: Asset {asset!r} does not exist "
                            f"relative to {asset_root}"
                        )
            for argument in value.args:
                visit(argument)
        elif isinstance(value, (list, tuple)):
            for item in value:
                visit(item)
        elif is_dataclass(value):
            for item in fields(value):
                visit(getattr(value, item.name))

    visit(module)


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
    module = parse_source(source)
    _check_types(module)
    module = optimize(module, inline=not debug)
    asset_root = source_path.resolve().parent
    _validate_asset_paths(module, asset_root)
    code_generator = CGenerator(module, asset_root=asset_root)
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
                command.extend(["-lm", "-pthread"])
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
    module = parse_source(source)
    _check_types(module)
    module = optimize(module, inline=not debug)
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
    module = parse_source(source)
    _check_types(module)
    module = optimize(module)
    return format_ir(module)


def validate_source(source: str, asset_root: Path | None = None) -> None:
    module = parse_source(source)
    _check_types(module)
    module = optimize(module)
    if asset_root is not None:
        _validate_asset_paths(module, Path(asset_root).resolve())
    CGenerator(module, asset_root=asset_root).generate()


def _check_types(module: ModuleIR) -> None:
    try:
        TypeChecker(module).check()
    except TypeCheckError as exc:
        raise CompileError(str(exc)) from exc


def validate_file(source_path: Path, asset_root: Path | None = None) -> None:
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
    validate_source(source, asset_root or source_path.resolve().parent)
