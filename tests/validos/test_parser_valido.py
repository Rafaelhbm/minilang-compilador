"""Programas sintaticamente válidos: o parser deve aceitar e montar a árvore certa.

Para verificar precedência e associatividade de forma legível, convertemos a expressão
da AST em texto totalmente parentizado (função `parentizar`).
"""
from pathlib import Path

from src.ast_nodes import (
    Assign, BinOp, Block, BoolLiteral, For, If, IntLiteral, Print, UnaryOp, Var, While,
)
from src.lexer import Token, TokenType as T
from src.parser import Parser, parse

RAIZ = Path(__file__).resolve().parents[2]


def parentizar(expr) -> str:
    """Escreve a expressão com parênteses em toda operação, revelando o agrupamento."""
    if isinstance(expr, IntLiteral):
        return str(expr.value)
    if isinstance(expr, BoolLiteral):
        return "true" if expr.value else "false"
    if isinstance(expr, Var):
        return expr.name
    if isinstance(expr, UnaryOp):
        return "(-" + parentizar(expr.operand) + ")"
    return "(" + parentizar(expr.left) + " " + expr.op + " " + parentizar(expr.right) + ")"


def expr_de(fonte: str):
    """Analisa `x = <fonte>;` e devolve a expressão do lado direito."""
    programa = parse("x = " + fonte + ";")
    return programa.statements[0].value


# ---------------------------------------------------------------- precedência

def test_multiplicacao_tem_precedencia_sobre_soma():
    assert parentizar(expr_de("1 + 2 * 3")) == "(1 + (2 * 3))"


def test_parenteses_mudam_a_precedencia():
    assert parentizar(expr_de("(1 + 2) * 3")) == "((1 + 2) * 3)"


def test_aritmetica_tem_precedencia_sobre_comparacao():
    assert parentizar(expr_de("a + 1 < b * 2")) == "((a + 1) < (b * 2))"


def test_relacional_tem_precedencia_sobre_igualdade():
    assert parentizar(expr_de("a < b == c > d")) == "((a < b) == (c > d))"


# ---------------------------------------------------------------- associatividade

def test_subtracao_associa_a_esquerda():
    assert parentizar(expr_de("10 - 3 - 2")) == "((10 - 3) - 2)"


def test_divisao_associa_a_esquerda():
    assert parentizar(expr_de("8 / 4 / 2")) == "((8 / 4) / 2)"


def test_soma_e_subtracao_misturadas_associam_a_esquerda():
    assert parentizar(expr_de("1 - 2 + 3 - 4")) == "(((1 - 2) + 3) - 4)"


# ---------------------------------------------------------------- unário

def test_menos_unario_duplo():
    assert parentizar(expr_de("- - 1")) == "(-(-1))"


def test_menos_unario_tem_precedencia_sobre_multiplicacao():
    assert parentizar(expr_de("-x * 2")) == "((-x) * 2)"


def test_menos_unario_depois_de_operador_binario():
    assert parentizar(expr_de("3 - -1")) == "(3 - (-1))"


# ---------------------------------------------------------------- comparações

def test_comparacao_encadeada_com_parenteses_e_valida():
    assert parentizar(expr_de("(1 < 2) == true")) == "((1 < 2) == true)"


def test_todos_os_operadores_de_comparacao():
    for op in ["<", ">", "<=", ">=", "==", "!="]:
        expr = expr_de("a " + op + " b")
        assert isinstance(expr, BinOp) and expr.op == op


# ---------------------------------------------------------------- comandos

def test_print():
    programa = parse("print(1 + 2);")
    assert isinstance(programa.statements[0], Print)


def test_if_sem_else():
    comando = parse("if (x > 0) { print(x); }").statements[0]
    assert isinstance(comando, If)
    assert comando.else_branch is None


def test_if_com_else():
    comando = parse("if (x > 0) { print(x); } else { print(0); }").statements[0]
    assert isinstance(comando.then_branch, Block)
    assert isinstance(comando.else_branch, Block)


def test_else_if_vira_if_aninhado_no_ramo_else():
    fonte = "if (x > 0) { y = 1; } else if (x < 0) { y = 2; } else { y = 3; }"
    comando = parse(fonte).statements[0]
    assert isinstance(comando.else_branch, If)
    assert isinstance(comando.else_branch.else_branch, Block)


def test_blocos_aninhados():
    programa = parse("{ { { x = 1; } } y = 2; }")
    externo = programa.statements[0]
    assert isinstance(externo, Block)
    assert isinstance(externo.statements[0], Block)
    assert isinstance(externo.statements[0].statements[0], Block)
    assert isinstance(externo.statements[1], Assign)


def test_bloco_vazio():
    assert parse("{ }").statements[0] == Block([])


def test_programa_vazio():
    assert parse("").statements == []


def test_while():
    comando = parse("while (x > 0) { x = x - 1; }").statements[0]
    assert isinstance(comando, While)
    assert parentizar(comando.condition) == "(x > 0)"
    assert len(comando.body.statements) == 1


def test_for_com_as_tres_clausulas():
    comando = parse("for (i = 0; i < 10; i = i + 1) { print(i); }").statements[0]
    assert isinstance(comando, For)
    assert comando.init == Assign("i", IntLiteral(0))
    assert parentizar(comando.condition) == "(i < 10)"
    assert comando.update.name == "i"
    assert parentizar(comando.update.value) == "(i + 1)"
    assert isinstance(comando.body.statements[0], Print)


def test_lacos_aninhados():
    fonte = """
    for (i = 0; i < 3; i = i + 1) {
        j = 0;
        while (j < i) {
            if (j == 1) { print(j); }
            j = j + 1;
        }
    }
    """
    laco = parse(fonte).statements[0]
    interno = laco.body.statements[1]
    assert isinstance(interno, While)
    assert isinstance(interno.body.statements[0], If)


def test_comentarios_sao_ignorados():
    programa = parse("// comentário\nx = 1; /* bloco */ print(x);")
    assert len(programa.statements) == 2


def test_parser_aceita_tokens_montados_a_mao():
    # Independe do lexer: garante que o parser trabalha só com a lista de tokens.
    tokens = [
        Token(T.IDENT, "x", None, 1, 1), Token(T.ASSIGN, "=", None, 1, 3),
        Token(T.INT, "2", 2, 1, 5), Token(T.STAR, "*", None, 1, 7),
        Token(T.INT, "3", 3, 1, 9), Token(T.SEMI, ";", None, 1, 10),
        Token(T.EOF, "", None, 1, 11),
    ]
    programa = Parser(tokens).parse()
    assert programa.statements[0] == Assign("x", BinOp("*", IntLiteral(2), IntLiteral(3)))


def test_programa_valido_de_exemplo():
    fonte = (RAIZ / "exemplos" / "programa_valido.ml").read_text(encoding="utf-8")
    programa = parse(fonte)
    tipos = [type(c).__name__ for c in programa.statements]
    assert tipos == ["Assign", "Assign", "Print", "While", "Assign", "For", "If"]
    assert parentizar(programa.statements[1].value) == "(2 * (x + 5))"
