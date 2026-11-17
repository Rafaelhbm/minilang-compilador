"""Nós da Árvore Sintática Abstrata (AST) da MiniLang.

Cada classe corresponde a uma construção que importa para a execução. O que existe só
para guiar a análise sintática (parênteses, `;`, chaves, palavras-chave, a cadeia de
não-terminais de precedência) não vira nó: a estrutura da árvore já codifica isso.

`line`/`col` indicam a posição do início da construção no código-fonte e são usados nas
mensagens de erro semântico. Exceções: em BinOp a posição é a do operador (é o
ponto mais útil para apontar, por exemplo, uma divisão por zero) e em Program é sempre
linha 1, coluna 1. Os campos line/col não participam da comparação de igualdade entre nós
(compare=False), para que testes possam comparar árvores pela estrutura.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional, Tuple, Union


# ---------------------------------------------------------------- expressões

@dataclass
class IntLiteral:
    """Constante inteira. `value`: o valor já convertido para int."""

    value: int
    line: int = field(default=0, compare=False)
    col: int = field(default=0, compare=False)


@dataclass
class BoolLiteral:
    """Constante `true`/`false`. `value`: True ou False."""

    value: bool
    line: int = field(default=0, compare=False)
    col: int = field(default=0, compare=False)


@dataclass
class Var:
    """Uso de uma variável numa expressão. `name`: o identificador."""

    name: str
    line: int = field(default=0, compare=False)
    col: int = field(default=0, compare=False)


@dataclass
class UnaryOp:
    """Menos unário. `op`: sempre "-"; `operand`: a expressão negada."""

    op: str  # "-"
    operand: "Expr"
    line: int = field(default=0, compare=False)
    col: int = field(default=0, compare=False)


@dataclass
class BinOp:
    """Operação binária. `op`: o operador; `left`/`right`: operandos esquerdo e direito.
    A ordem de avaliação e o agrupamento ficam na forma da árvore."""

    op: str  # "+", "-", "*", "/", "<", ">", "<=", ">=", "==", "!="
    left: "Expr"
    right: "Expr"
    line: int = field(default=0, compare=False)
    col: int = field(default=0, compare=False)


Expr = Union[IntLiteral, BoolLiteral, Var, UnaryOp, BinOp]


# ---------------------------------------------------------------- comandos

@dataclass
class Assign:
    """Atribuição `name = value`. Também usada nas cláusulas de inicialização e
    atualização do For."""

    name: str
    value: Expr
    line: int = field(default=0, compare=False)
    col: int = field(default=0, compare=False)


@dataclass
class Print:
    """Comando `print(expr)`."""

    expr: Expr
    line: int = field(default=0, compare=False)
    col: int = field(default=0, compare=False)


@dataclass
class Block:
    """Sequência de comandos entre chaves. Não cria escopo novo."""

    statements: List["Stmt"]
    line: int = field(default=0, compare=False)
    col: int = field(default=0, compare=False)


@dataclass
class If:
    """`if (condition) then_branch else else_branch`. `else_branch` é None (sem else),
    um Block (else { ... }) ou outro If (else if ...)."""

    condition: Expr
    then_branch: Block
    else_branch: Optional[Union[Block, "If"]] = None
    line: int = field(default=0, compare=False)
    col: int = field(default=0, compare=False)


@dataclass
class While:
    """`while (condition) body`: testa `condition` antes de cada execução de `body`."""

    condition: Expr
    body: Block
    line: int = field(default=0, compare=False)
    col: int = field(default=0, compare=False)


@dataclass
class For:
    """`for (init; condition; update) body`: executa `init` uma vez; enquanto
    `condition` for verdadeira, executa `body` e depois `update`."""

    init: Assign
    condition: Expr
    update: Assign
    body: Block
    line: int = field(default=0, compare=False)
    col: int = field(default=0, compare=False)


Stmt = Union[Assign, Print, Block, If, While, For]


@dataclass
class Program:
    """Raiz da árvore: a lista de comandos do programa, na ordem do fonte."""

    statements: List[Stmt]
    line: int = field(default=1, compare=False)
    col: int = field(default=1, compare=False)


# ---------------------------------------------------------------- visualização

def format_tree(node: object) -> str:
    """Devolve a AST em texto indentado (usado pela CLI `--ast` e no relatório).

    Exemplo para `x = 1 + 2 * 3;`:

        Program
        └── Assign x
            └── BinOp +
                ├── IntLiteral 1
                └── BinOp *
                    ├── IntLiteral 2
                    └── IntLiteral 3

    Nos comandos com mais de um filho de papéis diferentes (If, While, For), cada
    filho recebe um rótulo ("condição:", "corpo:" ...) para deixar claro o papel dele.
    """
    linhas = [_rotulo(node)]
    _formatar_filhos(node, "", linhas)
    return "\n".join(linhas)


def _rotulo(node: object) -> str:
    """Texto da linha de um nó: nome da classe mais o dado que ele carrega."""
    if isinstance(node, IntLiteral):
        return "IntLiteral {}".format(node.value)
    if isinstance(node, BoolLiteral):
        return "BoolLiteral {}".format("true" if node.value else "false")
    if isinstance(node, Var):
        return "Var {}".format(node.name)
    if isinstance(node, (UnaryOp, BinOp)):
        return "{} {}".format(type(node).__name__, node.op)
    if isinstance(node, Assign):
        return "Assign {}".format(node.name)
    return type(node).__name__   # Program, Block, Print, If, While, For


def _filhos(node: object) -> List[Tuple[str, object]]:
    """Lista (rótulo do papel, nó filho) na ordem em que devem ser impressos."""
    if isinstance(node, (Program, Block)):
        return [("", s) for s in node.statements]
    if isinstance(node, UnaryOp):
        return [("", node.operand)]
    if isinstance(node, BinOp):
        return [("", node.left), ("", node.right)]
    if isinstance(node, Assign):
        return [("", node.value)]
    if isinstance(node, Print):
        return [("", node.expr)]
    if isinstance(node, If):
        filhos = [("condição: ", node.condition), ("então: ", node.then_branch)]
        if node.else_branch is not None:
            filhos.append(("senão: ", node.else_branch))
        return filhos
    if isinstance(node, While):
        return [("condição: ", node.condition), ("corpo: ", node.body)]
    if isinstance(node, For):
        return [("inicialização: ", node.init), ("condição: ", node.condition),
                ("atualização: ", node.update), ("corpo: ", node.body)]
    return []   # literais e variáveis são folhas


def _formatar_filhos(node: object, prefixo: str, linhas: List[str]) -> None:
    """Acrescenta em `linhas` os filhos de `node`, desenhando os ramos.

    `prefixo` é o que vem antes do ramo em cada linha: "│   " enquanto o ancestral
    ainda tem irmãos abaixo, "    " quando o ancestral foi o último filho.
    """
    filhos = _filhos(node)
    for i, (papel, filho) in enumerate(filhos):
        ultimo = i == len(filhos) - 1
        ramo = "└── " if ultimo else "├── "
        linhas.append(prefixo + ramo + papel + _rotulo(filho))
        _formatar_filhos(filho, prefixo + ("    " if ultimo else "│   "), linhas)
