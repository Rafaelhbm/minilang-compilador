"""Analisador sintático descendente recursivo da MiniLang.

CONTRATO:
    Parser(tokens).parse() -> ast_nodes.Program
    parse(source: str) -> ast_nodes.Program        (lexer + parser)
    Erros: lança src.errors.MiniLangSyntaxError; `.errors` lista todos os
    diagnósticos encontrados (recuperação em modo pânico).
"""
from __future__ import annotations

from typing import List

from src.ast_nodes import Program
from src.lexer import Token, tokenize


class Parser:
    def __init__(self, tokens: List[Token]):
        self.tokens = tokens

    def parse(self) -> Program:
        raise NotImplementedError  # Sprint 1 — agente do parser


def parse(source: str) -> Program:
    return Parser(tokenize(source)).parse()
