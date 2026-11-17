"""Testes do lexer com entradas inválidas.

Resultado esperado de cada caso (todos lançam LexicalError; posição = início
do lexema problemático, linha e coluna começando em 1):

| Entrada            | Linha, coluna | Mensagem                                                                 |
|--------------------|---------------|--------------------------------------------------------------------------|
| "@"                | 1, 1          | caractere inválido '@'                                                   |
| "y = x @ 2;"       | 1, 7          | caractere inválido '@'                                                   |
| "1x"               | 1, 1          | número mal formado '1x': identificadores não podem começar com dígito    |
| "x = 12ab + 1;"    | 1, 5          | número mal formado '12ab': identificadores não podem começar com dígito  |
| "3_"               | 1, 1          | número mal formado '3_': ...                                             |
| "/* sem fim"       | 1, 1          | comentário de bloco não fechado (aponta a abertura)                      |
| "x;\n  /* a\n b *" | 2, 3          | comentário de bloco não fechado                                          |
| "!"                | 1, 1          | caractere inválido '!' (o operador de diferença é '!=')                  |
| "!x"               | 1, 1          | idem ('!' sem '=' logo depois)                                           |
| "! ="              | 1, 1          | idem (espaço separa: não forma '!=')                                     |
| "#"                | 1, 1          | caractere inválido '#'                                                   |
| "$"                | 1, 1          | caractere inválido '$'                                                   |
| "a && b"           | 1, 3          | caractere inválido '&' (o primeiro '&')                                  |
| "ç = 1;"           | 1, 1          | caractere inválido 'ç' (fora do ASCII; não é letra da MiniLang)          |
| "x = 1;\n\ty = @;" | 2, 6          | caractere inválido '@' (tab conta como 1 coluna)                         |
"""
from __future__ import annotations

import pytest

from src.errors import LexicalError, MiniLangError
from src.lexer import tokenize


def erro(fonte: str) -> LexicalError:
    with pytest.raises(LexicalError) as info:
        tokenize(fonte)
    return info.value


# --- casos obrigatórios -------------------------------------------------------

def test_arroba():
    e = erro("@")
    assert (e.line, e.col) == (1, 1)
    assert e.message == "caractere inválido '@'"


def test_arroba_no_meio_da_expressao():
    e = erro("y = x @ 2;")
    assert (e.line, e.col) == (1, 7)
    assert "'@'" in e.message


def test_numero_seguido_de_letra():
    e = erro("1x")
    assert (e.line, e.col) == (1, 1)
    assert e.message == ("número mal formado '1x': identificadores não podem "
                         "começar com dígito")


def test_numero_mal_formado_mostra_lexema_inteiro():
    e = erro("x = 12ab + 1;")
    assert (e.line, e.col) == (1, 5)
    assert "'12ab'" in e.message


def test_numero_seguido_de_sublinhado():
    e = erro("3_")
    assert "'3_'" in e.message


def test_comentario_de_bloco_nao_fechado():
    e = erro("/* sem fim")
    assert (e.line, e.col) == (1, 1)
    assert e.message == "comentário de bloco não fechado"


def test_comentario_de_bloco_nao_fechado_aponta_abertura():
    # Termina em '*': o AFD para em COMENT_BLOCO_ESTRELA, que também é erro.
    e = erro("x;\n  /* a\n b *")
    assert (e.line, e.col) == (2, 3)
    assert "não fechado" in e.message


def test_comentario_de_bloco_so_abertura_com_barra():
    # "/*/" não fecha: o '*' da abertura não pode ser reaproveitado.
    e = erro("/*/")
    assert "não fechado" in e.message


# --- outros caracteres inválidos ------------------------------------------------

def test_exclamacao_sozinha():
    e = erro("!")
    assert (e.line, e.col) == (1, 1)
    assert e.message == "caractere inválido '!' (o operador de diferença é '!=')"


@pytest.mark.parametrize("fonte", ["!x", "! =", "if (!ok) {}"])
def test_exclamacao_sem_igual(fonte):
    e = erro(fonte)
    assert "'!='" in e.message
    assert e.col == fonte.index("!") + 1


@pytest.mark.parametrize("c", ["#", "$", "%", "?", "&", "|", "[", "\"", "'", ".", ","])
def test_caracteres_fora_do_alfabeto(c):
    e = erro(c)
    assert (e.line, e.col) == (1, 1)
    assert e.message == f"caractere inválido '{c}'"


def test_e_comercial_duplo():
    e = erro("a && b")
    assert (e.line, e.col) == (1, 3)
    assert e.message == "caractere inválido '&'"


def test_caractere_nao_ascii():
    e = erro("ç = 1;")
    assert (e.line, e.col) == (1, 1)
    assert e.message == "caractere inválido 'ç'"


def test_acento_no_meio_de_identificador():
    # "ação": "a" é IDENT, depois o 'ç' não tem transição a partir de INICIAL.
    e = erro("ação = 1;")
    assert (e.line, e.col) == (1, 2)
    assert "'ç'" in e.message


# --- posição do erro ------------------------------------------------------------

def test_posicao_com_tab_e_varias_linhas():
    e = erro("x = 1;\n\ty = @;")
    assert (e.line, e.col) == (2, 6)


def test_erro_depois_de_comentario_de_bloco_multilinha():
    e = erro("/* a\nb */ x = $")
    assert (e.line, e.col) == (2, 10)


def test_formato_da_mensagem():
    e = erro("x = 1;\ny = x @ 2;")
    assert str(e) == "[Erro léxico] linha 2, coluna 7: caractere inválido '@'"
    assert isinstance(e, MiniLangError)
