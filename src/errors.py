"""Hierarquia de erros da MiniLang.

Cada fase do compilador lança a sua categoria de erro:

    MiniLangError
    ├── LexicalError            (lexer)
    ├── MiniLangSyntaxError     (parser)
    └── SemanticError           (interpretador)
        ├── UndefinedVariableError
        ├── TypeMismatchError
        ├── DivisionByZeroError
        └── LoopLimitError

Todas as mensagens seguem o formato:
    [Erro <categoria>] linha L, coluna C: <mensagem>
"""
from __future__ import annotations

from typing import List, Optional


class MiniLangError(Exception):
    """Erro base. `line`/`col` começam em 1; podem ser None quando desconhecidos."""

    category = "desconhecido"

    def __init__(self, message: str, line: Optional[int] = None, col: Optional[int] = None):
        self.message = message
        self.line = line
        self.col = col
        super().__init__(self.format())

    def format(self) -> str:
        where = ""
        if self.line is not None:
            where = f" linha {self.line}"
            if self.col is not None:
                where += f", coluna {self.col}"
            where += ":"
        else:
            where = ":"
        return f"[Erro {self.category}]{where} {self.message}"


class LexicalError(MiniLangError):
    category = "léxico"


class MiniLangSyntaxError(MiniLangError):
    """Erro sintático. `errors` guarda todos os diagnósticos coletados com
    recuperação em modo pânico; a mensagem principal é a do primeiro."""

    category = "sintático"

    def __init__(self, message: str, line: Optional[int] = None, col: Optional[int] = None,
                 errors: Optional[List["MiniLangSyntaxError"]] = None):
        super().__init__(message, line, col)
        self.errors: List[MiniLangSyntaxError] = errors if errors is not None else [self]


class SemanticError(MiniLangError):
    category = "semântico"


class UndefinedVariableError(SemanticError):
    pass


class TypeMismatchError(SemanticError):
    pass


class DivisionByZeroError(SemanticError):
    pass


class LoopLimitError(SemanticError):
    """Laço excedeu o limite de iterações (proteção contra laço infinito)."""
