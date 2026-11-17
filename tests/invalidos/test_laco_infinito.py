"""Proteção contra laço infinito.

RESULTADO ESPERADO
------------------
Decidir se um laço termina é o problema da parada, que é indecidível; por isso o
interpretador não tenta "detectar" laço infinito. Ele conta as iterações de cada laço
e, ao passar de um limite, interrompe o programa com LoopLimitError (um SemanticError).

Regra do limite (contrato em src/interpreter.py: "limite de iterações POR execução
de um laço"):
  - com max_iterations = N, um laço pode executar o corpo N vezes;
  - a tentativa de iniciar a (N+1)-ésima iteração lança LoopLimitError;
  - ou seja, o erro acontece quando o número de iterações seria > N (não >= N);
  - a contagem é por execução do laço: cada vez que um laço começa, o contador
    volta a zero. Um laço interno que roda 3 vezes em cada volta do externo
    nunca acumula iterações das voltas anteriores.
  - o que foi impresso antes do estouro continua impresso (o erro não desfaz a saída).
  - sem max_iterations explícito vale DEFAULT_MAX_ITERATIONS.
"""
import time

import pytest

from src.errors import LoopLimitError, SemanticError
from src.interpreter import DEFAULT_MAX_ITERATIONS, Interpreter, run
from src.parser import parse


def executar_coletando(source, max_iterations):
    """Executa o programa guardando a saída numa lista, para podermos ver o que foi
    impresso mesmo que a execução termine com erro. Devolve (saida, erro)."""
    saida = []
    erro = None
    try:
        Interpreter(output=saida.append, max_iterations=max_iterations).execute(parse(source))
    except LoopLimitError as e:
        erro = e
    return saida, erro


# ------------------------------------------------------------ laços que nunca terminam

def test_while_true_estoura_limite_rapido():
    inicio = time.perf_counter()
    with pytest.raises(LoopLimitError):
        run("while (true) { }", max_iterations=1000)
    assert time.perf_counter() - inicio < 1.0


def test_for_sem_progresso_estoura_limite_rapido():
    # A atualização i = i não muda nada: i < 10 é sempre verdadeiro.
    inicio = time.perf_counter()
    with pytest.raises(LoopLimitError):
        run("for (i = 0; i < 10; i = i) { }", max_iterations=1000)
    assert time.perf_counter() - inicio < 1.0


def test_laco_infinito_por_variavel_que_se_afasta_da_condicao():
    # x cresce, mas a condição espera x chegar a zero: nunca acontece.
    src = "x = 1; while (x != 0) { x = x + 1; }"
    with pytest.raises(LoopLimitError):
        run(src, max_iterations=500)


def test_loop_limit_error_e_erro_semantico_com_posicao():
    with pytest.raises(SemanticError) as info:
        run("x = 0;\nwhile (true) { x = x + 1; }", max_iterations=10)
    assert isinstance(info.value, LoopLimitError)
    assert info.value.format().startswith("[Erro semântico]")
    # A posição apontada é a do laço (linha 2).
    assert info.value.line == 2


# ------------------------------------------------------------ saída antes do estouro

def test_saida_produzida_antes_do_limite_e_preservada():
    src = """
    print(0);
    x = 1;
    while (true) {
        print(x);
        x = x + 1;
    }
    """
    saida, erro = executar_coletando(src, max_iterations=3)
    assert isinstance(erro, LoopLimitError)
    # print(0) antes do laço e as 3 iterações permitidas.
    assert saida == ["0", "1", "2", "3"]


# ------------------------------------------------------------ limite padrão

def test_limite_padrao_existe_e_e_positivo():
    assert isinstance(DEFAULT_MAX_ITERATIONS, int)
    assert DEFAULT_MAX_ITERATIONS > 0


def test_limite_padrao_e_usado_quando_nao_informado():
    assert Interpreter().max_iterations == DEFAULT_MAX_ITERATIONS
    with pytest.raises(LoopLimitError):
        run("while (true) { }")


# ------------------------------------------------------------ fronteira do limite

def test_while_com_exatamente_n_iteracoes_nao_estoura():
    # O corpo roda 5 vezes (x = 0..4) com limite 5: permitido.
    src = "x = 0; while (x < 5) { x = x + 1; } print(x);"
    assert run(src, max_iterations=5) == ["5"]


def test_while_com_n_mais_1_iteracoes_estoura():
    # O mesmo laço precisa de 5 iterações; com limite 4 a 5ª estoura.
    src = "x = 0; while (x < 5) { print(x); x = x + 1; }"
    saida, erro = executar_coletando(src, max_iterations=4)
    assert isinstance(erro, LoopLimitError)
    assert saida == ["0", "1", "2", "3"]


def test_for_com_exatamente_n_iteracoes_nao_estoura():
    src = "for (i = 0; i < 5; i = i + 1) { } print(i);"
    assert run(src, max_iterations=5) == ["5"]


def test_for_com_n_mais_1_iteracoes_estoura():
    with pytest.raises(LoopLimitError):
        run("for (i = 0; i < 5; i = i + 1) { }", max_iterations=4)


def test_laco_com_zero_iteracoes_e_limite_zero_nao_estoura():
    # Nenhuma iteração acontece, então nenhuma ultrapassa o limite.
    assert run("while (false) { } print(1);", max_iterations=0) == ["1"]


def test_limite_e_por_execucao_do_laco_e_nao_acumula():
    # O laço interno roda 3 vezes em cada uma das 3 voltas do externo (9 no total).
    # Com limite 3 isso é permitido, porque o contador reinicia a cada execução.
    src = """
    total = 0;
    for (i = 0; i < 3; i = i + 1) {
        for (j = 0; j < 3; j = j + 1) {
            total = total + 1;
        }
    }
    print(total);
    """
    assert run(src, max_iterations=3) == ["9"]


def test_dois_lacos_em_sequencia_tem_contadores_independentes():
    src = """
    x = 0; while (x < 4) { x = x + 1; }
    y = 0; while (y < 4) { y = y + 1; }
    print(x + y);
    """
    assert run(src, max_iterations=4) == ["8"]
