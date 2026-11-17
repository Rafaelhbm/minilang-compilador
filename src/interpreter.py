"""Interpretador da MiniLang (percorre a AST) e tabela de símbolos.

CONTRATO:
    SymbolTable — insert/lookup/contains (ver docstring da classe)
    Interpreter(output=None, max_iterations=100_000)
        .execute(program: Program) -> None
        output: callable(str) chamado a cada print; padrão = print do Python
        max_iterations: limite de iterações POR execução de um laço (while/for);
                        estourar lança LoopLimitError
    run(source: str, max_iterations=100_000) -> List[str]
        lexer + parser + interpretador; devolve as linhas impressas
    Erros: UndefinedVariableError, TypeMismatchError, DivisionByZeroError,
           LoopLimitError (todas subclasses de SemanticError).
"""
from __future__ import annotations

from typing import Callable, List, Optional

from src.ast_nodes import Program

DEFAULT_MAX_ITERATIONS = 100_000


class SymbolTable:
    def __init__(self):
        raise NotImplementedError  # Sprint 1 — agente do interpretador


class Interpreter:
    def __init__(self, output: Optional[Callable[[str], None]] = None,
                 max_iterations: int = DEFAULT_MAX_ITERATIONS):
        self.output = output if output is not None else print
        self.max_iterations = max_iterations

    def execute(self, program: Program) -> None:
        raise NotImplementedError  # Sprint 1 — agente do interpretador


def run(source: str, max_iterations: int = DEFAULT_MAX_ITERATIONS) -> List[str]:
    from src.parser import parse

    lines: List[str] = []
    Interpreter(output=lines.append, max_iterations=max_iterations).execute(parse(source))
    return lines
