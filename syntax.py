"""Shared Zelix lexer and syntax tree used by validation, compilation, and execution."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class Token:
    kind: str
    value: str
    line: int
    column: int


class Lexer:
    TOKEN_RE = re.compile(
        r'\s*(>=|<=|==|!=|[(),.]|"(?:\\.|[^"\\])*"|\'(?:\\.|[^\'\\])*\'|'
        r'-?\d+(?:\.\d+)?|[A-Za-z_][A-Za-z_0-9]*|.)'
    )

    def __init__(self, source: str, line: int = 1):
        self.source = source
        self.line = line

    def tokenize(self) -> list[Token]:
        tokens = []
        position = 0
        while position < len(self.source):
            match = self.TOKEN_RE.match(self.source, position)
            if not match:
                raise SyntaxError(f"Line {self.line}: Invalid token near {self.source[position:position + 12]!r}")
            value = match.group(1)
            start = match.start(1)
            position = match.end()
            if not value.strip():
                continue
            if value.startswith(('"', "'")):
                kind = "STRING"
            elif re.fullmatch(r"-?\d+(?:\.\d+)?", value):
                kind = "NUMBER"
            elif re.fullmatch(r"[A-Za-z_]\w*", value):
                kind = "WORD"
            else:
                kind = "PUNCTUATION"
            tokens.append(Token(kind, value, self.line, start + 1))
        return tokens


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
class Await(Expr):
    value: Expr


@dataclass
class Spawn(Expr):
    call: Call


@dataclass
class Stmt:
    line: int


@dataclass
class Create(Stmt):
    name: str
    value: Expr
    type_annotation: str | None = None


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
    param_types: dict[str, str] = field(default_factory=dict)
    return_type: str | None = None
    is_async: bool = False
    generic_params: list[str] = field(default_factory=list)


@dataclass
class ModuleIR:
    functions: list[FunctionIR]
    body: list[Stmt]


def parse_source(source: str) -> ModuleIR:
    """Parse source with the canonical compiler parser and return its shared AST."""
    from compiler import ZelixParser

    return ZelixParser(source).parse()
