"""Testes do interpretador com programas SEMANTICAMENTE INVÁLIDOS.

Todos estes programas são sintaticamente corretos; o erro só aparece na execução,
quando a regra semântica (seção 4 de docs/gramatica.md) é verificada.

Resultado esperado de cada caso (classe do erro — posição reportada):

  while (x) com x int ............ TypeMismatchError  — posição da condição
      "condição do while deve ser bool, mas é int"
  for (i = 0; i; ...) ............ TypeMismatchError  — posição da condição
      "condição do for deve ser bool, mas é int"
  if (1) ......................... TypeMismatchError  — posição da condição
      "condição do if deve ser bool, mas é int"
  for (i = 0; j < 10; i = i + 1) . UndefinedVariableError — posição de `j`
      "variável 'j' não definida"
  for (i = 0; i < 3; k = k + 1) .. UndefinedVariableError — posição de `k` (na atualização)
  print(y) com y nunca atribuída . UndefinedVariableError — posição de `y`
  x = x + 1 com x indefinida ..... UndefinedVariableError (não cria x silenciosamente)
  10 / 0 ......................... DivisionByZeroError — posição do operador binário
  x / (y - y) .................... DivisionByZeroError (divisor zero calculado)
  1 + true ....................... TypeMismatchError — "operador '+' exige int e int, mas recebeu int e bool"
  true < 1 ....................... TypeMismatchError — "operador '<' exige int e int, ..."
  1 == true ...................... TypeMismatchError — "'==' exige operandos do mesmo tipo, mas recebeu int e bool"
  x = 1; x = true; ............... TypeMismatchError — posição da 2ª atribuição
      "variável 'x' é int e não pode receber bool"
  -true .......................... TypeMismatchError — "operador '-' unário exige int, mas recebeu bool"
  while (true) {} ................ LoopLimitError — posição do while
      "laço while excedeu o limite de N iterações (possível laço infinito)"

Os testes unitários montam a AST à mão com line/col explícitos, então verificam a
posição exata. Os testes ponta a ponta (via parser) verificam a linha e, quando a
posição é inequívoca (uma variável isolada), também a coluna.
"""
import pytest

from src.ast_nodes import (
    Assign, BinOp, Block, BoolLiteral, For, If, IntLiteral, Print, Program,
    UnaryOp, Var, While,
)
from src.errors import (
    DivisionByZeroError, LoopLimitError, SemanticError, TypeMismatchError,
    UndefinedVariableError,
)
from src.interpreter import Interpreter, SymbolTable, run


def executar(*comandos, max_iterations=100_000):
    saida = []
    Interpreter(output=saida.append, max_iterations=max_iterations).execute(
        Program(list(comandos)))
    return saida


def run_ou_pula(source, **kwargs):
    try:
        return run(source, **kwargs)
    except NotImplementedError:
        pytest.skip("parser ainda não implementado")


def i_mais_1():
    return Assign("i", BinOp("+", Var("i"), IntLiteral(1)))


# ------------------------------------------------------------ tabela de símbolos

class TestTabelaDeSimbolos:
    def test_lookup_ausente(self):
        with pytest.raises(UndefinedVariableError) as e:
            SymbolTable().lookup("y", 4, 2)
        assert (e.value.line, e.value.col) == (4, 2)

    def test_update_tipo_diferente(self):
        t = SymbolTable()
        t.insert("x", 1)
        with pytest.raises(TypeMismatchError):
            t.update("x", True)

    def test_update_int_em_variavel_bool(self):
        # O caso perigoso: True é int em Python, mas int não pode ir para bool.
        t = SymbolTable()
        t.insert("b", True)
        with pytest.raises(TypeMismatchError):
            t.update("b", 1)


# --------------------------------------------------- condições não booleanas

class TestCondicaoNaoBooleana:
    def test_while_int(self):
        prog = [
            Assign("x", IntLiteral(5, 1, 5), 1, 1),
            While(Var("x", 2, 8),
                  Block([Assign("x", BinOp("-", Var("x"), IntLiteral(1)))]), 2, 1),
        ]
        with pytest.raises(TypeMismatchError) as e:
            executar(*prog)
        assert e.value.message == "condição do while deve ser bool, mas é int"
        assert (e.value.line, e.value.col) == (2, 8)

    def test_for_int(self):
        laco = For(Assign("i", IntLiteral(0)), Var("i", 1, 13), i_mais_1(), Block([]), 1, 1)
        with pytest.raises(TypeMismatchError) as e:
            executar(laco)
        assert e.value.message == "condição do for deve ser bool, mas é int"
        assert (e.value.line, e.value.col) == (1, 13)

    def test_if_int(self):
        with pytest.raises(TypeMismatchError) as e:
            executar(If(IntLiteral(1, 3, 5), Block([]), None, 3, 1))
        assert e.value.message == "condição do if deve ser bool, mas é int"
        assert (e.value.line, e.value.col) == (3, 5)

    def test_else_if_int(self):
        prog = If(BoolLiteral(False), Block([]), If(IntLiteral(0, 2, 10), Block([])))
        with pytest.raises(TypeMismatchError) as e:
            executar(prog)
        assert (e.value.line, e.value.col) == (2, 10)

    def test_condicao_mudando_de_tipo_nao_ocorre(self):
        # O tipo de uma variável é fixo, então uma condição bool continua bool.
        # Aqui garantimos que a falha acontece antes de executar qualquer corpo.
        saida = []
        with pytest.raises(TypeMismatchError):
            Interpreter(output=saida.append).execute(Program([
                While(IntLiteral(1), Block([Print(IntLiteral(9))]))]))
        assert saida == []


# ----------------------------------------------------- variáveis indefinidas

class TestVariavelIndefinida:
    def test_print_indefinida(self):
        with pytest.raises(UndefinedVariableError) as e:
            executar(Print(Var("y", 1, 7), 1, 1))
        assert e.value.message == "variável 'y' não definida"
        assert (e.value.line, e.value.col) == (1, 7)

    def test_atribuicao_usa_a_propria_variavel_indefinida(self):
        with pytest.raises(UndefinedVariableError):
            executar(Assign("x", BinOp("+", Var("x", 1, 5), IntLiteral(1))))

    def test_for_variavel_de_controle_indefinida_na_condicao(self):
        # for (i = 0; j < 10; i = i + 1) {}
        laco = For(Assign("i", IntLiteral(0)),
                   BinOp("<", Var("j", 1, 13), IntLiteral(10)), i_mais_1(), Block([]), 1, 1)
        with pytest.raises(UndefinedVariableError) as e:
            executar(laco)
        assert e.value.message == "variável 'j' não definida"
        assert (e.value.line, e.value.col) == (1, 13)

    def test_for_variavel_indefinida_na_atualizacao(self):
        # for (i = 0; i < 3; i = k + 1) {}
        laco = For(Assign("i", IntLiteral(0)), BinOp("<", Var("i"), IntLiteral(3)),
                   Assign("i", BinOp("+", Var("k", 1, 24), IntLiteral(1))), Block([]))
        with pytest.raises(UndefinedVariableError) as e:
            executar(laco)
        assert e.value.message == "variável 'k' não definida"
        assert (e.value.line, e.value.col) == (1, 24)


# -------------------------------------------------------------- divisão por zero

class TestDivisaoPorZero:
    def test_literal_zero(self):
        with pytest.raises(DivisionByZeroError) as e:
            executar(Print(BinOp("/", IntLiteral(10), IntLiteral(0), 2, 9)))
        assert e.value.message == "divisão por zero"
        assert (e.value.line, e.value.col) == (2, 9)

    def test_divisor_calculado(self):
        # x / (y - y)
        prog = [
            Assign("x", IntLiteral(10)),
            Assign("y", IntLiteral(3)),
            Assign("z", BinOp("/", Var("x"), BinOp("-", Var("y"), Var("y")), 3, 7)),
        ]
        with pytest.raises(DivisionByZeroError) as e:
            executar(*prog)
        assert (e.value.line, e.value.col) == (3, 7)


# ------------------------------------------------------- tipos incompatíveis

class TestTipoIncompativel:
    def test_soma_int_bool(self):
        with pytest.raises(TypeMismatchError) as e:
            executar(Print(BinOp("+", IntLiteral(1), BoolLiteral(True), 1, 9)))
        assert e.value.message == "operador '+' exige int e int, mas recebeu int e bool"
        assert (e.value.line, e.value.col) == (1, 9)

    @pytest.mark.parametrize("o", ["-", "*", "/"])
    def test_outros_aritmeticos(self, o):
        with pytest.raises(TypeMismatchError):
            executar(Print(BinOp(o, BoolLiteral(True), IntLiteral(1))))

    def test_bool_mais_bool(self):
        # Em Python True + True == 2; na MiniLang é erro.
        with pytest.raises(TypeMismatchError):
            executar(Print(BinOp("+", BoolLiteral(True), BoolLiteral(True))))

    @pytest.mark.parametrize("o", ["<", ">", "<=", ">="])
    def test_comparacao_com_bool(self, o):
        with pytest.raises(TypeMismatchError) as e:
            executar(Print(BinOp(o, BoolLiteral(True), IntLiteral(1), 1, 3)))
        assert e.value.message == f"operador '{o}' exige int e int, mas recebeu bool e int"

    def test_comparacao_bool_bool(self):
        # Em Python False < True é válido; na MiniLang não.
        with pytest.raises(TypeMismatchError):
            executar(Print(BinOp("<", BoolLiteral(False), BoolLiteral(True))))

    @pytest.mark.parametrize("o", ["==", "!="])
    def test_igualdade_mista(self, o):
        # Em Python 1 == True é True; na MiniLang tipos misturados são erro.
        with pytest.raises(TypeMismatchError) as e:
            executar(Print(BinOp(o, IntLiteral(1), BoolLiteral(True), 1, 9)))
        assert e.value.message == f"'{o}' exige operandos do mesmo tipo, mas recebeu int e bool"
        assert (e.value.line, e.value.col) == (1, 9)

    def test_reatribuicao_int_para_bool(self):
        prog = [Assign("x", IntLiteral(1), 1, 1), Assign("x", BoolLiteral(True), 2, 1)]
        with pytest.raises(TypeMismatchError) as e:
            executar(*prog)
        assert e.value.message == "variável 'x' é int e não pode receber bool"
        assert (e.value.line, e.value.col) == (2, 1)

    def test_reatribuicao_bool_para_int(self):
        prog = [Assign("b", BoolLiteral(True), 1, 1), Assign("b", IntLiteral(1), 2, 1)]
        with pytest.raises(TypeMismatchError) as e:
            executar(*prog)
        assert e.value.message == "variável 'b' é bool e não pode receber int"

    def test_menos_true(self):
        with pytest.raises(TypeMismatchError) as e:
            executar(Print(UnaryOp("-", BoolLiteral(True), 1, 7)))
        assert e.value.message == "operador '-' unário exige int, mas recebeu bool"
        assert (e.value.line, e.value.col) == (1, 7)


# ------------------------------------------------------------------ laço infinito

class TestLimiteDeIteracoes:
    def test_while_true(self):
        with pytest.raises(LoopLimitError) as e:
            executar(While(BoolLiteral(True), Block([]), 4, 1), max_iterations=50)
        assert e.value.message == \
            "laço while excedeu o limite de 50 iterações (possível laço infinito)"
        assert (e.value.line, e.value.col) == (4, 1)

    def test_for_que_nunca_termina(self):
        # for (i = 0; i >= 0; i = i + 1) {}
        laco = For(Assign("i", IntLiteral(0)), BinOp(">=", Var("i"), IntLiteral(0)),
                   i_mais_1(), Block([]), 1, 1)
        with pytest.raises(LoopLimitError) as e:
            executar(laco, max_iterations=50)
        assert "laço for excedeu o limite de 50" in e.value.message

    def test_uma_iteracao_alem_do_limite(self):
        # 6 iterações com limite 5 -> erro (5 iterações passa, ver testes válidos)
        laco = For(Assign("i", IntLiteral(0)), BinOp("<", Var("i"), IntLiteral(6)),
                   i_mais_1(), Block([]))
        with pytest.raises(LoopLimitError):
            executar(laco, max_iterations=5)


# ----------------------------------------------------------------- ponta a ponta

class TestPontaAPonta:
    def test_exemplo_5_while_com_int(self):
        fonte = "x = 5;\nwhile (x) {\n    x = x - 1;\n}\n"
        with pytest.raises(TypeMismatchError) as e:
            run_ou_pula(fonte)
        assert e.value.message == "condição do while deve ser bool, mas é int"
        assert (e.value.line, e.value.col) == (2, 8)

    def test_for_condicao_int(self):
        with pytest.raises(TypeMismatchError) as e:
            run_ou_pula("for (i = 0; i; i = i + 1) { }")
        assert e.value.message == "condição do for deve ser bool, mas é int"
        assert (e.value.line, e.value.col) == (1, 13)

    def test_if_condicao_int(self):
        with pytest.raises(TypeMismatchError) as e:
            run_ou_pula("x = 1;\nif (x) { print(x); }")
        assert e.value.message == "condição do if deve ser bool, mas é int"
        assert (e.value.line, e.value.col) == (2, 5)

    def test_for_variavel_de_controle_nao_definida(self):
        with pytest.raises(UndefinedVariableError) as e:
            run_ou_pula("for (i = 0; j < 10; i = i + 1) { }")
        assert e.value.message == "variável 'j' não definida"
        assert (e.value.line, e.value.col) == (1, 13)

    def test_variavel_nao_definida(self):
        with pytest.raises(UndefinedVariableError) as e:
            run_ou_pula("x = 1;\nprint(y);")
        assert (e.value.line, e.value.col) == (2, 7)

    def test_divisao_por_zero_calculada(self):
        with pytest.raises(DivisionByZeroError) as e:
            run_ou_pula("x = 10;\ny = 4;\nz = x / (y - y);")
        assert e.value.line == 3

    def test_soma_int_bool(self):
        with pytest.raises(TypeMismatchError) as e:
            run_ou_pula("x = 1 + true;")
        assert e.value.message == "operador '+' exige int e int, mas recebeu int e bool"
        assert e.value.line == 1

    def test_comparacao_bool(self):
        with pytest.raises(TypeMismatchError):
            run_ou_pula("b = true < 1;")

    def test_igualdade_mista(self):
        with pytest.raises(TypeMismatchError) as e:
            run_ou_pula("print(1 == true);")
        assert e.value.message == "'==' exige operandos do mesmo tipo, mas recebeu int e bool"

    def test_reatribuicao_tipo_diferente(self):
        with pytest.raises(TypeMismatchError) as e:
            run_ou_pula("x = 1;\nx = true;")
        assert e.value.message == "variável 'x' é int e não pode receber bool"
        assert (e.value.line, e.value.col) == (2, 1)

    def test_menos_true(self):
        with pytest.raises(TypeMismatchError):
            run_ou_pula("print(-true);")

    def test_laco_infinito(self):
        with pytest.raises(LoopLimitError) as e:
            run_ou_pula("x = 0;\nwhile (true) { x = x + 1; }", max_iterations=100)
        assert e.value.line == 2

    def test_saida_parcial_antes_do_erro(self):
        # O que foi impresso antes do erro já foi emitido (execução dinâmica).
        saida = []
        try:
            from src.parser import parse
            programa = parse("print(1);\nprint(y);")
        except NotImplementedError:
            pytest.skip("parser ainda não implementado")
        with pytest.raises(UndefinedVariableError):
            Interpreter(output=saida.append).execute(programa)
        assert saida == ["1"]

    def test_todos_sao_erros_semanticos(self):
        for cls in (UndefinedVariableError, TypeMismatchError, DivisionByZeroError,
                    LoopLimitError):
            assert issubclass(cls, SemanticError)
