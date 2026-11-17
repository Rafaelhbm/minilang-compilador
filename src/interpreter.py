"""Interpretador da MiniLang (percorre a AST) e tabela de símbolos.

CONTRATO:
    SymbolTable — insert/update/lookup/contains (ver docstring da classe)
    Interpreter(output=None, max_iterations=100_000)
        .execute(program: Program) -> None
        output: callable(str) chamado a cada print; padrão = print do Python
        max_iterations: limite de iterações POR execução de um laço (while/for);
                        estourar lança LoopLimitError
    run(source: str, max_iterations=100_000) -> List[str]
        lexer + parser + interpretador; devolve as linhas impressas
    Erros: UndefinedVariableError, TypeMismatchError, DivisionByZeroError,
           LoopLimitError (todas subclasses de SemanticError).

A verificação semântica (seção 4 de docs/gramatica.md) é feita DURANTE a execução:
cada regra de tipo é conferida no momento em que a construção é avaliada. A
justificativa dessa escolha está em docs/relatorio/05_interpretador.md.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Dict, List, Optional, Union

from src.ast_nodes import (
    Assign,
    BinOp,
    Block,
    BoolLiteral,
    For,
    If,
    IntLiteral,
    Print,
    Program,
    UnaryOp,
    Var,
    While,
)
from src.errors import (
    DivisionByZeroError,
    LoopLimitError,
    TypeMismatchError,
    UndefinedVariableError,
)

DEFAULT_MAX_ITERATIONS = 100_000

# Valores da MiniLang em tempo de execução: int do Python para `int`, bool do
# Python para `bool`.
Value = Union[int, bool]


def type_name(value: Value) -> str:
    """Devolve o nome do tipo MiniLang de um valor Python ("int" ou "bool").

    Cuidado: em Python `bool` é subclasse de `int` (isinstance(True, int) é True).
    Por isso usamos `type(value) is ...`, que compara a classe exata e não aceita
    subclasses. Com isinstance, `true` passaria como inteiro.
    """
    if type(value) is bool:
        return "bool"
    if type(value) is int:
        return "int"
    # Não deve acontecer: o interpretador só produz int e bool.
    raise RuntimeError(f"valor de tipo desconhecido: {value!r}")


# ------------------------------------------------------------- tabela de símbolos

@dataclass
class Symbol:
    """Entrada da tabela de símbolos.

    name:  nome da variável
    type:  "int" ou "bool", fixado na primeira atribuição
    value: valor atual
    line:  linha da primeira atribuição (onde a variável foi declarada)
    """
    name: str
    type: str
    value: Value
    line: int


class SymbolTable:
    """Tabela de símbolos de escopo único: dicionário nome -> Symbol.

    A MiniLang não tem declaração explícita nem escopos aninhados (blocos não criam
    escopo), então um único dicionário basta. Operações (todas O(1) em média, pois
    o dict do Python é uma tabela hash):

        insert(name, value, line)  primeira atribuição; fixa o tipo da variável
        update(name, value, line, col)  reatribuição; exige o mesmo tipo
        lookup(name, line, col)    devolve o Symbol; UndefinedVariableError se ausente
        contains(name)             True se a variável já foi atribuída
    """

    def __init__(self):
        self._symbols: Dict[str, Symbol] = {}

    def insert(self, name: str, value: Value, line: int = 0) -> Symbol:
        """Cria a variável. O tipo dela passa a ser o tipo do valor inicial."""
        symbol = Symbol(name=name, type=type_name(value), value=value, line=line)
        self._symbols[name] = symbol
        return symbol

    def update(self, name: str, value: Value, line: int = 0, col: int = 0) -> Symbol:
        """Reatribui uma variável existente, verificando que o tipo não muda."""
        symbol = self.lookup(name, line, col)
        new_type = type_name(value)
        if new_type != symbol.type:
            raise TypeMismatchError(
                f"variável '{name}' é {symbol.type} e não pode receber {new_type}",
                line, col)
        symbol.value = value
        return symbol

    def lookup(self, name: str, line: int = 0, col: int = 0) -> Symbol:
        """Busca a variável; usar uma variável nunca atribuída é erro semântico."""
        if name not in self._symbols:
            raise UndefinedVariableError(f"variável '{name}' não definida", line, col)
        return self._symbols[name]

    def contains(self, name: str) -> bool:
        return name in self._symbols


# ------------------------------------------------------------------ interpretador

class Interpreter:
    """Executa a AST percorrendo-a recursivamente (tree-walking interpreter).

    O despacho é feito por dicionários tipo-do-nó -> método: `exec_*` para comandos
    (alteram o estado, não devolvem valor) e `eval_*` para expressões (devolvem um
    valor int ou bool). Assim cada tipo de nó tem exatamente um método.
    """

    def __init__(self, output: Optional[Callable[[str], None]] = None,
                 max_iterations: int = DEFAULT_MAX_ITERATIONS):
        self.output = output if output is not None else print
        self.max_iterations = max_iterations
        self.symbols = SymbolTable()

        self._statement_handlers = {
            Assign: self.exec_assign,
            Print: self.exec_print,
            Block: self.exec_block,
            If: self.exec_if,
            While: self.exec_while,
            For: self.exec_for,
        }
        self._expression_handlers = {
            IntLiteral: self.eval_int_literal,
            BoolLiteral: self.eval_bool_literal,
            Var: self.eval_var,
            UnaryOp: self.eval_unary_op,
            BinOp: self.eval_bin_op,
        }

    # ------------------------------------------------------------ ponto de entrada

    def execute(self, program: Program) -> None:
        """Executa os comandos do programa em ordem."""
        for statement in program.statements:
            self.exec_statement(statement)

    def exec_statement(self, node) -> None:
        handler = self._statement_handlers.get(type(node))
        if handler is None:
            raise RuntimeError(f"comando desconhecido na AST: {type(node).__name__}")
        handler(node)

    def evaluate(self, node) -> Value:
        handler = self._expression_handlers.get(type(node))
        if handler is None:
            raise RuntimeError(f"expressão desconhecida na AST: {type(node).__name__}")
        return handler(node)

    # ------------------------------------------------------------------ comandos

    def exec_assign(self, node: Assign) -> None:
        # O lado direito é avaliado ANTES de mexer na tabela: em `x = x + 1` com
        # `x` indefinido, o erro tem de ser "variável não definida", e não uma
        # criação silenciosa de `x`.
        value = self.evaluate(node.value)
        if self.symbols.contains(node.name):
            self.symbols.update(node.name, value, node.line, node.col)
        else:
            self.symbols.insert(node.name, value, node.line)

    def exec_print(self, node: Print) -> None:
        value = self.evaluate(node.expr)
        # bool precisa ser testado primeiro: str(True) daria "True", mas a
        # MiniLang imprime "true"/"false".
        if type(value) is bool:
            self.output("true" if value else "false")
        else:
            self.output(str(value))

    def exec_block(self, node: Block) -> None:
        # Blocos não criam escopo: usam a mesma tabela de símbolos.
        for statement in node.statements:
            self.exec_statement(statement)

    def exec_if(self, node: If) -> None:
        if self.eval_condition(node.condition, "if"):
            self.exec_block(node.then_branch)
        elif node.else_branch is not None:
            # else_branch é um Block ou outro If (cadeia else-if); o despacho
            # escolhe o método certo.
            self.exec_statement(node.else_branch)

    def exec_while(self, node: While) -> None:
        iterations = 0
        # A condição é avaliada antes de cada iteração, inclusive a primeira.
        while self.eval_condition(node.condition, "while"):
            iterations += 1
            self.check_loop_limit(iterations, "while", node)
            self.exec_block(node.body)

    def exec_for(self, node: For) -> None:
        # for (init; cond; update) corpo  ≡  init; while (cond) { corpo; update }
        self.exec_assign(node.init)
        iterations = 0
        while self.eval_condition(node.condition, "for"):
            iterations += 1
            self.check_loop_limit(iterations, "for", node)
            self.exec_block(node.body)
            self.exec_assign(node.update)

    # ------------------------------------------------- auxiliares dos comandos

    def eval_condition(self, condition, construct: str) -> bool:
        """Avalia a condição de if/while/for e exige que ela seja bool.

        Não existe conversão implícita int -> bool: `while (x)` com x int é erro.
        """
        value = self.evaluate(condition)
        if type(value) is not bool:
            raise TypeMismatchError(
                f"condição do {construct} deve ser bool, mas é {type_name(value)}",
                condition.line, condition.col)
        return value

    def check_loop_limit(self, iterations: int, construct: str, node) -> None:
        """Interrompe o laço que passar de max_iterations iterações.

        Decidir se um laço termina é o problema da parada (indecidível), então o
        interpretador usa um limite prático e trata o excesso como erro.
        """
        if iterations > self.max_iterations:
            raise LoopLimitError(
                f"laço {construct} excedeu o limite de {self.max_iterations} "
                f"iterações (possível laço infinito)",
                node.line, node.col)

    # ---------------------------------------------------------------- expressões

    def eval_int_literal(self, node: IntLiteral) -> int:
        return node.value

    def eval_bool_literal(self, node: BoolLiteral) -> bool:
        return node.value

    def eval_var(self, node: Var) -> Value:
        return self.symbols.lookup(node.name, node.line, node.col).value

    def eval_unary_op(self, node: UnaryOp) -> int:
        operand = self.evaluate(node.operand)
        if type(operand) is not int:
            raise TypeMismatchError(
                f"operador '{node.op}' unário exige int, mas recebeu {type_name(operand)}",
                node.line, node.col)
        return -operand

    def eval_bin_op(self, node: BinOp) -> Value:
        # Os dois operandos são avaliados (esquerda primeiro) antes da checagem
        # de tipos. A MiniLang não tem operadores de curto-circuito.
        left = self.evaluate(node.left)
        right = self.evaluate(node.right)
        op = node.op

        if op in ("==", "!="):
            # Igualdade aceita int==int ou bool==bool, mas nunca tipos misturados.
            # Sem esta checagem, Python diria `1 == true` -> True (bool é int).
            if type_name(left) != type_name(right):
                raise TypeMismatchError(
                    f"'{op}' exige operandos do mesmo tipo, mas recebeu "
                    f"{type_name(left)} e {type_name(right)}",
                    node.line, node.col)
            return left == right if op == "==" else left != right

        # Todos os demais operadores (aritméticos e relacionais) exigem int e int.
        if type(left) is not int or type(right) is not int:
            raise TypeMismatchError(
                f"operador '{op}' exige int e int, mas recebeu "
                f"{type_name(left)} e {type_name(right)}",
                node.line, node.col)

        if op == "+":
            return left + right
        if op == "-":
            return left - right
        if op == "*":
            return left * right
        if op == "/":
            if right == 0:
                raise DivisionByZeroError("divisão por zero", node.line, node.col)
            return truncated_division(left, right)
        if op == "<":
            return left < right
        if op == ">":
            return left > right
        if op == "<=":
            return left <= right
        if op == ">=":
            return left >= right
        raise RuntimeError(f"operador desconhecido na AST: {op!r}")


def truncated_division(a: int, b: int) -> int:
    """Divisão inteira truncada em direção a zero (como em C e Java).

    O `//` do Python arredonda para baixo (em direção a -infinito):
    -7 // 2 == -4. A MiniLang exige -7 / 2 == -3. Dividimos os valores absolutos
    (onde truncar e arredondar para baixo coincidem) e depois aplicamos o sinal.
    Não usamos int(a / b) porque a divisão em ponto flutuante perde precisão para
    inteiros grandes.
    """
    quotient = abs(a) // abs(b)
    if (a < 0) != (b < 0):
        return -quotient
    return quotient


def run(source: str, max_iterations: int = DEFAULT_MAX_ITERATIONS) -> List[str]:
    from src.parser import parse

    lines: List[str] = []
    Interpreter(output=lines.append, max_iterations=max_iterations).execute(parse(source))
    return lines
