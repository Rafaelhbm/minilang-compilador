"""Programas sintaticamente inválidos: o parser deve rejeitar com mensagem clara.

Resultado esperado de cada caso (todos lançam MiniLangSyntaxError):

| Entrada                              | Posição  | Mensagem (trecho)                                         |
|--------------------------------------|----------|-----------------------------------------------------------|
| for (i = 0; i < 10) { }              | 1:19     | esperado ';' após a condição do for (...), encontrado ')' |
| x = (1 + ;                           | 1:10     | esperado expressão após '+', encontrado ';'               |
| x = 1 < 2 < 3;                       | 1:11     | operadores de comparação não são associativos             |
| x = a == b == c;                     | 1:12     | operadores de comparação não são associativos             |
| for (; i < 10; i = i + 1) { }        | 1:6      | esperado identificador na inicialização do for            |
| for (i = 0; ; i = i + 1) { }         | 1:13     | esperado expressão na condição do for                     |
| for (i = 0; i < 10; ) { }            | 1:21     | esperado identificador na atualização do for              |
| while x > 0 { ... }                  | 1:7      | esperado '(' após 'while', encontrado 'x'                 |
| while (x > 0) { x = x - 1;  (EOF)    | 1:27     | esperado '}' para fechar o bloco ..., encontrado fim do arquivo |
| x = 1 <nova linha> y = 2;            | 2:1      | esperado ';' após a atribuição, encontrado 'y'            |
| print x;                             | 1:7      | esperado '(' após 'print'                                 |
| else { x = 1; }                      | 1:1      | 'else' sem 'if' correspondente                            |
| x = y = 1;                           | 1:7      | atribuição é comando, não expressão                       |
| print(x = 1);                        | 1:9      | atribuição é comando, não expressão                       |
| if (x > 0) print(x);                 | 1:12     | esperado '{' para abrir o corpo do if                     |
| x + 1;                               | 1:3      | esperado '=' após 'x'                                     |
| } (sobrando no nível do programa)    | 1:1      | esperado início de comando                                |
| três comandos com erro + um correto  | —        | exatamente 3 erros (recuperação em modo pânico)           |
| exemplos/programa_invalido.ml        | 6:19     | esperado ';' após a condição do for                       |
"""
from pathlib import Path

import pytest

from src.errors import MiniLangSyntaxError
from src.lexer import Token, TokenType as T
from src.parser import Parser, parse

RAIZ = Path(__file__).resolve().parents[2]


def erro_de(fonte: str) -> MiniLangSyntaxError:
    with pytest.raises(MiniLangSyntaxError) as info:
        parse(fonte)
    return info.value


def unico_erro(fonte: str) -> MiniLangSyntaxError:
    """Para entradas com um único engano: exige exatamente um diagnóstico, o que
    também prova que a recuperação não gerou erros em cascata."""
    erro = erro_de(fonte)
    assert len(erro.errors) == 1, [str(e) for e in erro.errors]
    return erro


# ---------------------------------------------------------------- obrigatórios

def test_for_sem_atualizacao():
    erro = unico_erro("for (i = 0; i < 10) { }")
    assert (erro.line, erro.col) == (1, 19)
    assert erro.message == ("esperado ';' após a condição do for (o for exige "
                            "inicialização; condição; atualização), encontrado ')'")


def test_expressao_incompleta():
    erro = unico_erro("x = (1 + ;")
    assert (erro.line, erro.col) == (1, 10)
    assert erro.message == "esperado expressão após '+', encontrado ';'"


def test_comparacao_relacional_encadeada():
    erro = unico_erro("x = 1 < 2 < 3;")
    assert (erro.line, erro.col) == (1, 11)
    assert "operadores de comparação não são associativos; use parênteses" in erro.message


# ---------------------------------------------------------------- demais casos

def test_igualdade_encadeada():
    erro = unico_erro("x = a == b == c;")
    assert (erro.line, erro.col) == (1, 12)
    assert "não são associativos" in erro.message


def test_comparacao_encadeada_na_condicao_do_if():
    erro = unico_erro("if (a == b == c) { x = 1; }")
    assert "não são associativos" in erro.message


def test_for_com_inicializacao_vazia():
    erro = unico_erro("for (; i < 10; i = i + 1) { }")
    assert (erro.line, erro.col) == (1, 6)
    assert erro.message.startswith("esperado identificador na inicialização do for")
    assert erro.message.endswith("encontrado ';'")


def test_for_com_condicao_vazia():
    erro = unico_erro("for (i = 0; ; i = i + 1) { }")
    assert (erro.line, erro.col) == (1, 13)
    assert erro.message.startswith("esperado expressão na condição do for")


def test_for_com_atualizacao_vazia():
    erro = unico_erro("for (i = 0; i < 10; ) { }")
    assert (erro.line, erro.col) == (1, 21)
    assert erro.message.startswith("esperado identificador na atualização do for")
    assert erro.message.endswith("encontrado ')'")


def test_for_sem_ponto_e_virgula_entre_condicao_e_atualizacao():
    erro = unico_erro("for (i = 0; i < 10 i = i + 1) { }")
    assert "esperado ';' após a condição do for" in erro.message
    assert erro.message.endswith("encontrado 'i'")


def test_while_sem_parenteses():
    erro = unico_erro("while x > 0 { x = x - 1; }")
    assert (erro.line, erro.col) == (1, 7)
    assert erro.message == "esperado '(' após 'while', encontrado 'x'"


def test_while_sem_fecha_parentese():
    erro = unico_erro("while (x > 0 { x = 1; }")
    assert erro.message == "esperado ')' após a condição do while, encontrado '{'"


def test_bloco_nao_fechado():
    erro = unico_erro("while (x > 0) { x = x - 1;")
    assert (erro.line, erro.col) == (1, 27)
    assert erro.message == ("esperado '}' para fechar o bloco aberto na linha 1, "
                            "encontrado fim do arquivo")


def test_ponto_e_virgula_faltando():
    erro = unico_erro("x = 1\ny = 2;")
    assert (erro.line, erro.col) == (2, 1)
    assert erro.message == "esperado ';' após a atribuição, encontrado 'y'"


def test_print_sem_parenteses():
    erro = unico_erro("print x;")
    assert (erro.line, erro.col) == (1, 7)
    assert erro.message.startswith("esperado '(' após 'print'")


def test_else_sem_if():
    erro = unico_erro("else { x = 1; }")
    assert (erro.line, erro.col) == (1, 1)
    assert "'else' sem 'if' correspondente" in erro.message


def test_atribuicao_como_expressao():
    erro = unico_erro("x = y = 1;")
    assert (erro.line, erro.col) == (1, 7)
    assert "atribuição é comando, não expressão" in erro.message


def test_atribuicao_dentro_do_print():
    erro = unico_erro("print(x = 1);")
    assert (erro.line, erro.col) == (1, 9)
    assert "atribuição é comando, não expressão" in erro.message


def test_if_sem_chaves():
    erro = unico_erro("if (x > 0) print(x);")
    assert (erro.line, erro.col) == (1, 12)
    assert erro.message == ("esperado '{' para abrir o corpo do if (o corpo deve estar "
                            "entre chaves), encontrado 'print'")


def test_expressao_solta_nao_e_comando():
    erro = unico_erro("x + 1;")
    assert erro.message.startswith("esperado '=' após 'x'")


def test_fecha_chave_sobrando():
    erro = unico_erro("}\nx = 1;")
    assert erro.message.startswith("esperado início de comando")
    assert erro.message.endswith("encontrado '}'")


def test_parentese_nao_fechado_cita_onde_foi_aberto():
    erro = unico_erro("x = (1 + 2;")
    assert erro.message == "esperado ')' para fechar o '(' da linha 1, coluna 5, encontrado ';'"


def test_fim_do_arquivo_no_meio_da_expressao():
    erro = unico_erro("x = 1 +")
    assert erro.message == "esperado expressão após '+', encontrado fim do arquivo"


def test_mensagem_formatada_com_categoria_e_posicao():
    erro = unico_erro("x = (1 + ;")
    assert str(erro) == ("[Erro sintático] linha 1, coluna 10: "
                         "esperado expressão após '+', encontrado ';'")


# ---------------------------------------------------------------- recuperação

def test_recuperacao_reporta_varios_erros_sem_espurios():
    fonte = "x = ;\nprint(;\ny = 1 +;\nz = 3;"
    erro = erro_de(fonte)
    posicoes = [(e.line, e.col) for e in erro.errors]
    assert posicoes == [(1, 5), (2, 7), (3, 8)]   # um por linha errada; z = 3; é aceito
    # O erro principal é o primeiro da lista.
    assert (erro.line, erro.col) == (1, 5)
    assert erro.message == erro.errors[0].message


def test_recuperacao_no_cabecalho_do_for_ainda_analisa_o_corpo():
    fonte = "for (i = 0; i < 10) { soma = ; }\nprint(soma);"
    erro = erro_de(fonte)
    mensagens = [e.message for e in erro.errors]
    assert len(mensagens) == 2
    assert mensagens[0].startswith("esperado ';' após a condição do for")
    assert mensagens[1] == "esperado expressão após '=', encontrado ';'"


def test_recuperacao_dentro_de_bloco():
    fonte = "while (x > 0) {\n  x = ;\n  y = 2\n}\nz = 1 < 2 < 3;"
    erro = erro_de(fonte)
    assert [e.line for e in erro.errors] == [2, 4, 5]


def test_recuperacao_termina_com_lixo_no_fim():
    # Garantia de progresso: tokens que não iniciam comando são descartados um a um.
    erro = erro_de(") ) ) ;")
    assert len(erro.errors) >= 1


def test_tokens_montados_a_mao_sem_lexer():
    tokens = [
        Token(T.PRINT, "print", None, 1, 1), Token(T.IDENT, "x", None, 1, 7),
        Token(T.SEMI, ";", None, 1, 8), Token(T.EOF, "", None, 1, 9),
    ]
    with pytest.raises(MiniLangSyntaxError) as info:
        Parser(tokens).parse()
    assert info.value.message.startswith("esperado '(' após 'print'")


def test_programa_invalido_de_exemplo():
    fonte = (RAIZ / "exemplos" / "programa_invalido.ml").read_text(encoding="utf-8")
    erro = unico_erro(fonte)
    assert (erro.line, erro.col) == (6, 19)
    assert "esperado ';' após a condição do for" in erro.message
