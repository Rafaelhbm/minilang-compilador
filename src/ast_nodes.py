"""Nós da Árvore Sintática Abstrata (AST) da MiniLang.

Cada classe corresponde a uma construção que importa para a execução. O que existe só
para guiar a análise sintática (parênteses, `;`, chaves, palavras-chave, a cadeia de
não-terminais de precedência) não vira nó: a estrutura da árvore já codifica isso.

`line`/`col` indicam a posição do início da construção no código-fonte e são usados nas
mensagens de erro semântico. Não participam da comparação de igualdade entre nós
(compare=False), para que testes possam comparar árvores pela estrutura.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional, Union


# ---------------------------------------------------------------- expressões

@dataclass
class IntLiteral:
    value: int
    line: int = field(default=0, compare=False)
    col: int = field(default=0, compare=False)


@dataclass
class BoolLiteral:
    value: bool
    line: int = field(default=0, compare=False)
    col: int = field(default=0, compare=False)


@dataclass
class Var:
    name: str
    line: int = field(default=0, compare=False)
    col: int = field(default=0, compare=False)


@dataclass
class UnaryOp:
    op: str  # "-"
    operand: "Expr"
    line: int = field(default=0, compare=False)
    col: int = field(default=0, compare=False)


@dataclass
class BinOp:
    op: str  # "+", "-", "*", "/", "<", ">", "<=", ">=", "==", "!="
    left: "Expr"
    right: "Expr"
    line: int = field(default=0, compare=False)
    col: int = field(default=0, compare=False)


Expr = Union[IntLiteral, BoolLiteral, Var, UnaryOp, BinOp]


# ---------------------------------------------------------------- comandos

@dataclass
class Assign:
    name: str
    value: Expr
    line: int = field(default=0, compare=False)
    col: int = field(default=0, compare=False)


@dataclass
class Print:
    expr: Expr
    line: int = field(default=0, compare=False)
    col: int = field(default=0, compare=False)


@dataclass
class Block:
    statements: List["Stmt"]
    line: int = field(default=0, compare=False)
    col: int = field(default=0, compare=False)


@dataclass
class If:
    condition: Expr
    then_branch: Block
    else_branch: Optional[Union[Block, "If"]] = None
    line: int = field(default=0, compare=False)
    col: int = field(default=0, compare=False)


@dataclass
class While:
    condition: Expr
    body: Block
    line: int = field(default=0, compare=False)
    col: int = field(default=0, compare=False)


@dataclass
class For:
    init: Assign
    condition: Expr
    update: Assign
    body: Block
    line: int = field(default=0, compare=False)
    col: int = field(default=0, compare=False)


Stmt = Union[Assign, Print, Block, If, While, For]


@dataclass
class Program:
    statements: List[Stmt]
    line: int = field(default=1, compare=False)
    col: int = field(default=1, compare=False)


# ---------------------------------------------------------------- visualização

def format_tree(node: object) -> str:
    """Devolve a AST em texto indentado (usado pela CLI `--ast` e no relatório).

    A implementar na Sprint 1 (agente do parser/AST).
    """
    raise NotImplementedError
