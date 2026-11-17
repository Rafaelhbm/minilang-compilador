"""Testes de borda dos laços (while e for), executando programas completos com run().

Cada teste confere a lista de linhas impressas, que é o comportamento observável
do programa.
"""
from src.interpreter import run


# ------------------------------------------------------------ while: quantas vezes executa

def test_while_condicao_falsa_na_entrada_nao_executa():
    src = """
    x = 0;
    while (x > 0) {
        print(x);
    }
    print(99);
    """
    assert run(src) == ["99"]


def test_while_executa_uma_vez():
    src = """
    x = 1;
    while (x > 0) {
        print(x);
        x = x - 1;
    }
    """
    assert run(src) == ["1"]


def test_while_executa_n_vezes():
    src = """
    x = 5;
    while (x > 0) {
        print(x);
        x = x - 1;
    }
    """
    assert run(src) == ["5", "4", "3", "2", "1"]


def test_while_condicao_depende_de_variavel_alterada_no_corpo():
    # A condição não usa um contador: depende de "achou", que muda dentro do corpo.
    src = """
    n = 1;
    achou = false;
    while (achou == false) {
        n = n * 3;
        if (n > 50) {
            achou = true;
        }
    }
    print(n);
    """
    # 3, 9, 27, 81 -> para no primeiro valor maior que 50
    assert run(src) == ["81"]


def test_while_com_literal_false_nao_executa():
    assert run("while (false) { print(1); } print(2);") == ["2"]


# ------------------------------------------------------------ for: quantas vezes executa

def test_for_condicao_falsa_na_entrada_nao_executa():
    src = """
    for (i = 10; i < 5; i = i + 1) {
        print(i);
    }
    print(i);
    """
    # O corpo não roda, mas a inicialização roda: i existe e vale 10.
    assert run(src) == ["10"]


def test_for_executa_uma_vez():
    src = """
    for (i = 0; i < 1; i = i + 1) {
        print(i);
    }
    """
    assert run(src) == ["0"]


def test_for_executa_n_vezes():
    src = """
    for (i = 0; i < 4; i = i + 1) {
        print(i);
    }
    """
    assert run(src) == ["0", "1", "2", "3"]


# ------------------------------------------------------------ for: formas de atualização

def test_for_atualizacao_de_dois_em_dois():
    src = """
    for (i = 0; i < 10; i = i + 2) {
        print(i);
    }
    """
    assert run(src) == ["0", "2", "4", "6", "8"]


def test_for_atualizacao_multiplicando():
    src = """
    for (i = 1; i <= 100; i = i * 2) {
        print(i);
    }
    """
    assert run(src) == ["1", "2", "4", "8", "16", "32", "64"]


def test_for_decrescente():
    src = """
    for (i = 3; i > 0; i = i - 1) {
        print(i);
    }
    """
    assert run(src) == ["3", "2", "1"]


def test_for_decrescente_ate_negativo():
    src = """
    for (i = 1; i >= -2; i = i - 1) {
        print(i);
    }
    """
    assert run(src) == ["1", "0", "-1", "-2"]


def test_for_variavel_de_controle_modificada_no_corpo():
    # O corpo soma 2 em i e a atualização soma mais 1: cada volta avança 3.
    src = """
    for (i = 0; i < 10; i = i + 1) {
        print(i);
        i = i + 2;
    }
    """
    assert run(src) == ["0", "3", "6", "9"]


def test_for_variavel_de_controle_ja_existente_e_reatribuida():
    # A inicialização do for é uma atribuição comum: sobrescreve o valor anterior.
    src = """
    i = 100;
    for (i = 0; i < 2; i = i + 1) {
        print(i);
    }
    """
    assert run(src) == ["0", "1"]


# ------------------------------------------------------------ valor depois do laço

def test_for_valor_da_variavel_de_controle_depois_do_laco():
    # A última atualização deixa i = 5, que torna a condição falsa e encerra o laço.
    src = """
    for (i = 0; i < 5; i = i + 1) {
    }
    print(i);
    """
    assert run(src) == ["5"]


def test_for_valor_depois_do_laco_com_passo_que_ultrapassa_o_limite():
    src = """
    for (i = 0; i < 10; i = i + 3) {
    }
    print(i);
    """
    # 0, 3, 6, 9 -> 12 torna a condição falsa
    assert run(src) == ["12"]


def test_while_valor_da_variavel_depois_do_laco():
    src = """
    x = 7;
    while (x > 2) {
        x = x - 2;
    }
    print(x);
    """
    # 7 -> 5 -> 3 -> 1
    assert run(src) == ["1"]


# ------------------------------------------------------------ laços aninhados

def test_for_aninhado_tabuada():
    src = """
    for (i = 1; i <= 3; i = i + 1) {
        for (j = 1; j <= 3; j = j + 1) {
            print(i * j);
        }
    }
    """
    assert run(src) == ["1", "2", "3", "2", "4", "6", "3", "6", "9"]


def test_laco_interno_reinicia_a_cada_volta_do_externo():
    # Conta quantas vezes o corpo interno executa: 3 voltas externas x 4 internas.
    src = """
    total = 0;
    for (i = 0; i < 3; i = i + 1) {
        j = 0;
        while (j < 4) {
            total = total + 1;
            j = j + 1;
        }
    }
    print(total);
    """
    assert run(src) == ["12"]


def test_laco_interno_depende_da_variavel_do_externo():
    # Triângulo: a volta i do laço externo faz i voltas no interno.
    src = """
    for (i = 1; i <= 3; i = i + 1) {
        linha = 0;
        for (j = 0; j < i; j = j + 1) {
            linha = linha * 10 + 1;
        }
        print(linha);
    }
    """
    assert run(src) == ["1", "11", "111"]
