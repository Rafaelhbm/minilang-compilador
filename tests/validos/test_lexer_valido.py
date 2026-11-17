"""Testes do lexer com entradas válidas.

Cada teste confere tipo, lexema, valor e/ou posição dos tokens produzidos.
"""
from __future__ import annotations

from pathlib import Path

import pytest

from src.lexer import Lexer, Token, TokenType, tokenize

RAIZ = Path(__file__).resolve().parents[2]


def tipos(fonte: str):
    """Lista de tipos de token, sem o EOF final."""
    toks = tokenize(fonte)
    assert toks[-1].type == TokenType.EOF
    return [t.type for t in toks[:-1]]


def lexemas(fonte: str):
    return [t.lexeme for t in tokenize(fonte)[:-1]]


# --- cada tipo de token ------------------------------------------------------

@pytest.mark.parametrize("fonte, esperado", [
    ("42", TokenType.INT),
    ("true", TokenType.TRUE),
    ("false", TokenType.FALSE),
    ("x", TokenType.IDENT),
    ("_tmp1", TokenType.IDENT),
    ("if", TokenType.IF),
    ("else", TokenType.ELSE),
    ("while", TokenType.WHILE),
    ("for", TokenType.FOR),
    ("print", TokenType.PRINT),
    ("+", TokenType.PLUS),
    ("-", TokenType.MINUS),
    ("*", TokenType.STAR),
    ("/", TokenType.SLASH),
    ("=", TokenType.ASSIGN),
    ("==", TokenType.EQ),
    ("!=", TokenType.NE),
    ("<", TokenType.LT),
    (">", TokenType.GT),
    ("<=", TokenType.LE),
    (">=", TokenType.GE),
    ("(", TokenType.LPAREN),
    (")", TokenType.RPAREN),
    ("{", TokenType.LBRACE),
    ("}", TokenType.RBRACE),
    (";", TokenType.SEMI),
])
def test_cada_tipo_de_token(fonte, esperado):
    toks = tokenize(fonte)
    assert len(toks) == 2
    assert toks[0].type == esperado
    assert toks[0].lexeme == fonte
    assert toks[1].type == TokenType.EOF


def test_valores_dos_literais():
    inteiro, verdadeiro, falso, ident, _eof = tokenize("007 true false x")
    assert inteiro.value == 7 and isinstance(inteiro.value, int)
    assert verdadeiro.value is True
    assert falso.value is False
    assert ident.value is None


def test_entrada_vazia_produz_so_eof():
    toks = tokenize("")
    assert toks == [Token(TokenType.EOF, "", None, 1, 1)]


def test_so_espacos_e_comentarios_produz_so_eof():
    assert tipos("   \t\n  // nada\n /* nada */ \n") == []


def test_classe_lexer_e_funcao_tokenize_equivalentes():
    fonte = "x = 1 + 2;"
    assert Lexer(fonte).tokenize() == tokenize(fonte)


# --- palavras reservadas vs identificadores parecidos -------------------------

@pytest.mark.parametrize("fonte", [
    "whilex", "for_", "iff", "If", "WHILE", "elsewhere", "printf", "truee",
    "false1", "_if", "fo", "whil",
])
def test_identificadores_parecidos_com_reservadas(fonte):
    toks = tokenize(fonte)
    assert toks[0].type == TokenType.IDENT
    assert toks[0].lexeme == fonte


def test_reservada_separada_por_simbolo():
    assert tipos("if(x){") == [TokenType.IF, TokenType.LPAREN, TokenType.IDENT,
                               TokenType.RPAREN, TokenType.LBRACE]


# --- maior casamento (maximal munch) ------------------------------------------

def test_maximal_munch_operadores_compostos():
    assert tipos("<=") == [TokenType.LE]
    assert tipos("==") == [TokenType.EQ]
    assert tipos("!=") == [TokenType.NE]
    assert tipos(">=") == [TokenType.GE]


def test_maximal_munch_x_menor_igual_menos_um():
    assert tipos("x<=-1") == [TokenType.IDENT, TokenType.LE, TokenType.MINUS, TokenType.INT]


def test_tres_iguais_viram_eq_e_assign():
    # O primeiro "==" é o maior prefixo; sobra "=".
    assert tipos("===") == [TokenType.EQ, TokenType.ASSIGN]


def test_espaco_separa_operador_composto():
    assert tipos("< =") == [TokenType.LT, TokenType.ASSIGN]


def test_numero_longo_e_um_unico_token():
    toks = tokenize("123456")
    assert len(toks) == 2 and toks[0].value == 123456


def test_identificador_com_digitos_no_meio():
    assert lexemas("a1b2 c_3") == ["a1b2", "c_3"]


def test_expressao_sem_espacos():
    assert lexemas("soma=soma+i*2/(x-1);") == [
        "soma", "=", "soma", "+", "i", "*", "2", "/", "(", "x", "-", "1", ")", ";"]


# --- comentários ----------------------------------------------------------------

def test_comentario_de_linha_ate_o_fim_da_linha():
    assert lexemas("x = 1; // comentário com acento\ny = 2;") == [
        "x", "=", "1", ";", "y", "=", "2", ";"]


def test_comentario_de_linha_no_fim_do_arquivo_sem_quebra():
    assert lexemas("x // fim") == ["x"]


def test_comentario_de_bloco_em_varias_linhas():
    fonte = "a /* linha 1\nlinha 2 * / ainda dentro\n */ b"
    toks = tokenize(fonte)
    assert [t.lexeme for t in toks[:-1]] == ["a", "b"]
    assert (toks[1].line, toks[1].col) == (3, 5)


@pytest.mark.parametrize("fonte", ["a/**/b", "a/***/b", "a/* ** */b", "a/*/ */b"])
def test_variacoes_de_fechamento_do_bloco(fonte):
    assert lexemas(fonte) == ["a", "b"]


def test_bloco_nao_aninha():
    # O primeiro "*/" fecha o comentário; o resto vira tokens.
    assert lexemas("/* a /* b */ c */") == ["c", "*", "/"]


def test_barra_sozinha_e_divisao():
    assert tipos("a / b") == [TokenType.IDENT, TokenType.SLASH, TokenType.IDENT]


def test_comentario_dentro_de_comentario_de_linha():
    assert lexemas("// /* nao abre bloco\nx") == ["x"]


# --- linha e coluna -------------------------------------------------------------

def test_linha_e_coluna_comecam_em_1():
    t = tokenize("x")[0]
    assert (t.line, t.col) == (1, 1)


def test_posicoes_em_varias_linhas():
    fonte = "x = 10;\n  if (x >= 2) {\n}"
    pos = [(t.lexeme, t.line, t.col) for t in tokenize(fonte)]
    assert pos == [
        ("x", 1, 1), ("=", 1, 3), ("10", 1, 5), (";", 1, 7),
        ("if", 2, 3), ("(", 2, 6), ("x", 2, 7), (">=", 2, 9), ("2", 2, 12),
        (")", 2, 13), ("{", 2, 15),
        ("}", 3, 1),
        ("", 3, 2),  # EOF logo depois do último caractere
    ]


def test_tab_conta_como_uma_coluna():
    t = tokenize("\t\tx")[0]
    assert (t.line, t.col) == (1, 3)


def test_crlf_trata_retorno_de_carro_como_espaco():
    toks = tokenize("x\r\ny")
    assert [(t.lexeme, t.line, t.col) for t in toks[:-1]] == [("x", 1, 1), ("y", 2, 1)]


def test_eof_e_sempre_o_ultimo():
    for fonte in ["", "x", "x;\n", "// c"]:
        toks = tokenize(fonte)
        assert toks[-1].type == TokenType.EOF
        assert sum(t.type == TokenType.EOF for t in toks) == 1


# --- programa de exemplo inteiro --------------------------------------------------

def test_programa_valido_de_exemplo_tokeniza():
    fonte = (RAIZ / "exemplos" / "programa_valido.ml").read_text(encoding="utf-8")
    toks = tokenize(fonte)
    assert toks[-1].type == TokenType.EOF
    usados = {t.type for t in toks}
    for esperado in [TokenType.WHILE, TokenType.FOR, TokenType.IF, TokenType.ELSE,
                     TokenType.PRINT, TokenType.LT,
                     TokenType.GT, TokenType.INT, TokenType.IDENT]:
        assert esperado in usados
    # Primeiro token real está na linha 3 (as duas primeiras são comentário).
    assert (toks[0].lexeme, toks[0].line, toks[0].col) == ("x", 3, 1)


def test_programa_invalido_de_exemplo_e_lexicamente_valido():
    # O erro desse programa é sintático; o lexer deve aceitá-lo.
    fonte = (RAIZ / "exemplos" / "programa_invalido.ml").read_text(encoding="utf-8")
    assert tokenize(fonte)[-1].type == TokenType.EOF
