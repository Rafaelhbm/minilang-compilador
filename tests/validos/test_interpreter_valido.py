"""Testes do interpretador com programas VÁLIDOS.

Duas camadas:
1. Testes unitários com ASTs montadas à mão (não dependem do lexer nem do parser).
2. Testes ponta a ponta via `run(source)` (lexer + parser + interpretador). Enquanto
   o parser não estiver implementado, eles são pulados (skip) em vez de falhar.
"""
from pathlib import Path

import pytest

from src.ast_nodes import (
    Assign, BinOp, Block, BoolLiteral, For, If, IntLiteral, Print, Program,
    UnaryOp, Var, While,
)
from src.interpreter import Interpreter, SymbolTable, run, truncated_division, type_name

RAIZ = Path(__file__).resolve().parents[2]


# ------------------------------------------------------------------ auxiliares

def I(v):
    return IntLiteral(v)


def B(v):
    return BoolLiteral(v)


def V(nome):
    return Var(nome)


def op(o, a, b):
    return BinOp(o, a, b)


def executar(*comandos, max_iterations=100_000):
    """Executa os comandos e devolve (linhas impressas, interpretador)."""
    saida = []
    interp = Interpreter(output=saida.append, max_iterations=max_iterations)
    interp.execute(Program(list(comandos)))
    return saida, interp


def avaliar(expr):
    """Avalia uma expressão isolada num interpretador vazio."""
    return Interpreter(output=lambda s: None).evaluate(expr)


def run_ou_pula(source, **kwargs):
    """Roda ponta a ponta; pula o teste se o parser ainda não existir."""
    try:
        return run(source, **kwargs)
    except NotImplementedError:
        pytest.skip("parser ainda não implementado")


# ------------------------------------------------------------ tabela de símbolos

class TestTabelaDeSimbolos:
    def test_insert_fixa_tipo_e_lookup(self):
        t = SymbolTable()
        t.insert("x", 5, line=1)
        s = t.lookup("x")
        assert (s.name, s.type, s.value, s.line) == ("x", "int", 5, 1)

    def test_insert_bool_fixa_tipo_bool(self):
        t = SymbolTable()
        t.insert("ok", True, line=3)
        assert t.lookup("ok").type == "bool"

    def test_contains(self):
        t = SymbolTable()
        assert not t.contains("x")
        t.insert("x", 0)
        assert t.contains("x")

    def test_update_mesmo_tipo(self):
        t = SymbolTable()
        t.insert("x", 1, line=1)
        t.update("x", 7, line=2)
        s = t.lookup("x")
        assert s.value == 7
        assert s.line == 1  # a linha registrada é a da primeira atribuição


# ------------------------------------------------------- aritmética e precedência

class TestAritmetica:
    def test_soma_subtracao_multiplicacao(self):
        assert avaliar(op("+", I(2), I(3))) == 5
        assert avaliar(op("-", I(2), I(3))) == -1
        assert avaliar(op("*", I(4), I(3))) == 12

    def test_precedencia_na_arvore(self):
        # 1 + 2 * 3: o parser põe o * mais fundo na árvore
        assert avaliar(op("+", I(1), op("*", I(2), I(3)))) == 7
        # (1 + 2) * 3
        assert avaliar(op("*", op("+", I(1), I(2)), I(3))) == 9

    def test_associatividade_a_esquerda(self):
        # 10 - 3 - 2 = (10 - 3) - 2
        assert avaliar(op("-", op("-", I(10), I(3)), I(2))) == 5

    def test_unario(self):
        assert avaliar(UnaryOp("-", I(5))) == -5
        assert avaliar(UnaryOp("-", UnaryOp("-", I(5)))) == 5
        assert avaliar(op("*", UnaryOp("-", I(2)), I(3))) == -6


class TestDivisaoTruncada:
    @pytest.mark.parametrize("a, b, esperado", [
        (7, 2, 3),
        (-7, 2, -3),   # Python daria -4 com //
        (7, -2, -3),
        (-7, -2, 3),
        (6, 3, 2),
        (-6, 3, -2),
        (0, 5, 0),
        (1, 2, 0),
        (-1, 2, 0),
    ])
    def test_divisao(self, a, b, esperado):
        assert avaliar(op("/", I(a), I(b))) == esperado
        assert truncated_division(a, b) == esperado

    def test_inteiros_grandes_sem_perda_de_precisao(self):
        a = 10 ** 30 + 1
        assert truncated_division(a, 1) == a
        assert truncated_division(-a, 1) == -a


# ----------------------------------------------------------------- comparações

class TestComparacoes:
    @pytest.mark.parametrize("o, a, b, esperado", [
        ("<", 1, 2, True), ("<", 2, 2, False),
        (">", 3, 2, True), (">", 2, 3, False),
        ("<=", 2, 2, True), ("<=", 3, 2, False),
        (">=", 2, 2, True), (">=", 1, 2, False),
        ("==", 2, 2, True), ("==", 2, 3, False),
        ("!=", 2, 3, True), ("!=", 2, 2, False),
    ])
    def test_comparacao_int(self, o, a, b, esperado):
        r = avaliar(op(o, I(a), I(b)))
        assert r is esperado  # devolve bool de verdade, não 0/1

    def test_igualdade_de_bools(self):
        assert avaliar(op("==", B(True), B(True))) is True
        assert avaliar(op("==", B(True), B(False))) is False
        assert avaliar(op("!=", B(True), B(False))) is True
        assert avaliar(op("!=", B(False), B(False))) is False

    def test_comparacao_dentro_de_igualdade(self):
        # (1 < 2) == true
        assert avaliar(op("==", op("<", I(1), I(2)), B(True))) is True


# --------------------------------------------------------------------- tipos

class TestTipos:
    def test_type_name_distingue_bool_de_int(self):
        # isinstance(True, int) é True em Python; type_name não pode cair nisso.
        assert isinstance(True, int)
        assert type_name(True) == "bool"
        assert type_name(False) == "bool"
        assert type_name(1) == "int"
        assert type_name(0) == "int"

    def test_tipos_preservados_na_tabela(self):
        _, interp = executar(
            Assign("n", I(1)),
            Assign("b", op("<", I(1), I(2))),
        )
        assert interp.symbols.lookup("n").type == "int"
        assert type(interp.symbols.lookup("n").value) is int
        assert interp.symbols.lookup("b").type == "bool"
        assert type(interp.symbols.lookup("b").value) is bool

    def test_bool_nao_vira_int_no_print(self):
        saida, _ = executar(Print(B(True)), Print(B(False)), Print(I(1)), Print(I(0)))
        assert saida == ["true", "false", "1", "0"]

    def test_resultado_da_comparacao_e_bool_e_nao_int(self):
        r = avaliar(op("==", I(1), I(1)))
        assert type(r) is bool

    def test_reatribuicao_bool_mantem_bool(self):
        saida, interp = executar(
            Assign("b", B(True)),
            Assign("b", op(">", I(1), I(2))),
            Print(V("b")),
        )
        assert saida == ["false"]
        assert interp.symbols.lookup("b").type == "bool"


# ------------------------------------------------------------------- comandos

class TestComandos:
    def test_atribuicao_e_print(self):
        saida, _ = executar(Assign("x", I(3)), Print(op("+", V("x"), I(1))))
        assert saida == ["4"]

    def test_bloco_nao_cria_escopo(self):
        saida, _ = executar(
            Block([Assign("x", I(1))]),
            Print(V("x")),
        )
        assert saida == ["1"]

    def test_if_verdadeiro(self):
        saida, _ = executar(If(B(True), Block([Print(I(1))]), Block([Print(I(2))])))
        assert saida == ["1"]

    def test_if_falso_executa_else(self):
        saida, _ = executar(If(B(False), Block([Print(I(1))]), Block([Print(I(2))])))
        assert saida == ["2"]

    def test_if_falso_sem_else(self):
        saida, _ = executar(If(B(False), Block([Print(I(1))])))
        assert saida == []

    @pytest.mark.parametrize("x, esperado", [(1, "1"), (2, "2"), (3, "0")])
    def test_else_if(self, x, esperado):
        # if (x == 1) { print(1); } else if (x == 2) { print(2); } else { print(0); }
        prog = If(op("==", V("x"), I(1)), Block([Print(I(1))]),
                  If(op("==", V("x"), I(2)), Block([Print(I(2))]),
                     Block([Print(I(0))])))
        saida, _ = executar(Assign("x", I(x)), prog)
        assert saida == [esperado]

    def test_while_contagem_regressiva(self):
        saida, _ = executar(
            Assign("x", I(3)),
            While(op(">", V("x"), I(0)),
                  Block([Print(V("x")), Assign("x", op("-", V("x"), I(1)))])),
        )
        assert saida == ["3", "2", "1"]

    def test_while_condicao_falsa_desde_o_inicio(self):
        saida, _ = executar(While(B(False), Block([Print(I(1))])))
        assert saida == []

    def test_for_soma(self):
        saida, interp = executar(
            Assign("soma", I(0)),
            For(Assign("i", I(0)), op("<", V("i"), I(5)), Assign("i", op("+", V("i"), I(1))),
                Block([Assign("soma", op("+", V("soma"), V("i")))])),
            Print(V("soma")),
            Print(V("i")),
        )
        # a variável de controle continua existindo após o laço (escopo único)
        assert saida == ["10", "5"]

    def test_for_zero_iteracoes_ainda_executa_init(self):
        saida, interp = executar(
            For(Assign("i", I(10)), op("<", V("i"), I(5)), Assign("i", op("+", V("i"), I(1))),
                Block([Print(V("i"))])),
        )
        assert saida == []
        assert interp.symbols.lookup("i").value == 10

    def test_laco_exatamente_no_limite_e_permitido(self):
        # max_iterations = 5 e o laço faz 5 iterações: não deve dar erro.
        saida, _ = executar(
            For(Assign("i", I(0)), op("<", V("i"), I(5)), Assign("i", op("+", V("i"), I(1))),
                Block([Print(V("i"))])),
            max_iterations=5,
        )
        assert saida == ["0", "1", "2", "3", "4"]

    def test_limite_e_por_execucao_de_laco(self):
        # dois laços seguidos de 5 iterações cada com limite 5: o contador zera.
        laco = While(op("<", V("x"), I(5)), Block([Assign("x", op("+", V("x"), I(1)))]))
        _, interp = executar(Assign("x", I(0)), laco, Assign("x", I(0)), laco,
                             max_iterations=5)
        assert interp.symbols.lookup("x").value == 5


# --------------------------------------------------------------- ponta a ponta

class TestPontaAPonta:
    def test_programa_valido_exemplo(self):
        # Saída conferida à mão:
        #   y = 2 * (10 + 5) = 30                     -> 30
        #   while x de 10 até 1                       -> 10 9 8 7 6 5 4 3 2 1
        #   soma = 0+1+2+3+4 = 10; 10 > 20 é false    -> 0
        fonte = (RAIZ / "exemplos" / "programa_valido.ml").read_text(encoding="utf-8")
        esperado = ["30"] + [str(n) for n in range(10, 0, -1)] + ["0"]
        assert run_ou_pula(fonte) == esperado

    def test_exemplo_1_da_gramatica(self):
        fonte = """
        x = 3;
        soma = 0;
        for (i = 0; i < 5; i = i + 1) {
            soma = soma + i;
        }
        while (x > 0) {
            print(x);
            x = x - 1;
        }
        if (soma == 10) { print(true); } else { print(false); }
        """
        assert run_ou_pula(fonte) == ["3", "2", "1", "true"]

    def test_precedencia_e_divisao(self):
        fonte = """
        print(1 + 2 * 3);
        print((1 + 2) * 3);
        print(10 - 3 - 2);
        print(-7 / 2);
        print(7 / -2);
        print(-(2 + 3));
        """
        assert run_ou_pula(fonte) == ["7", "9", "5", "-3", "-3", "-5"]

    def test_comparacoes_e_bools(self):
        fonte = """
        b = 1 < 2;
        print(b);
        print(b == true);
        print((3 >= 4) != false);
        print(2 == 2);
        """
        assert run_ou_pula(fonte) == ["true", "true", "false", "true"]

    def test_else_if(self):
        fonte = """
        x = 2;
        if (x == 1) { print(1); } else if (x == 2) { print(2); } else { print(3); }
        """
        assert run_ou_pula(fonte) == ["2"]

    def test_fatorial(self):
        fonte = """
        n = 5;
        f = 1;
        while (n > 1) { f = f * n; n = n - 1; }
        print(f);
        """
        assert run_ou_pula(fonte) == ["120"]
