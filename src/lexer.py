"""Analisador léxico da MiniLang.

CONTRATO (não alterar nomes sem atualizar parser e testes):
    TokenType   — enum com os tipos de token de docs/gramatica.md
    Token       — (type, lexeme, value, line, col)
    Lexer(src).tokenize() -> List[Token]   (último token é sempre EOF)
    tokenize(src) -> List[Token]
    Erros: lança src.errors.LexicalError com linha/coluna.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum, auto
from typing import List, Optional

from src.errors import LexicalError  # noqa: F401  (usado na implementação)


class TokenType(Enum):
    # literais e identificador
    INT = auto()
    TRUE = auto()
    FALSE = auto()
    IDENT = auto()
    # palavras reservadas
    IF = auto()
    ELSE = auto()
    WHILE = auto()
    FOR = auto()
    PRINT = auto()
    # operadores
    PLUS = auto()
    MINUS = auto()
    STAR = auto()
    SLASH = auto()
    ASSIGN = auto()
    EQ = auto()
    NE = auto()
    LT = auto()
    GT = auto()
    LE = auto()
    GE = auto()
    # delimitadores
    LPAREN = auto()
    RPAREN = auto()
    LBRACE = auto()
    RBRACE = auto()
    SEMI = auto()
    # fim
    EOF = auto()


@dataclass(frozen=True)
class Token:
    type: TokenType
    lexeme: str
    value: object = None   # int para INT, bool para TRUE/FALSE, None nos demais
    line: int = 1
    col: int = 1


class Lexer:
    def __init__(self, source: str):
        self.source = source

    def tokenize(self) -> List[Token]:
        raise NotImplementedError  # Sprint 1 — agente do lexer


def tokenize(source: str) -> List[Token]:
    return Lexer(source).tokenize()
