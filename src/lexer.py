"""Analisador léxico da MiniLang.

CONTRATO (não alterar nomes sem atualizar parser e testes):
    TokenType   — enum com os tipos de token de docs/gramatica.md
    Token       — (type, lexeme, value, line, col)
    Lexer(src).tokenize() -> List[Token]   (último token é sempre EOF)
    tokenize(src) -> List[Token]
    Erros: lança src.errors.LexicalError com linha/coluna.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum, auto
from typing import List, Optional

from src.errors import LexicalError


class TokenType(Enum):
    # literais e identificador
    INT = auto()
    TRUE = auto()
    FALSE = auto()
    IDENT = auto()
    # palavras reservadas
    IF = auto()
    ELSE = auto()
    WHILE = auto()
    FOR = auto()
    PRINT = auto()
    # operadores
    PLUS = auto()
    MINUS = auto()
    STAR = auto()
    SLASH = auto()
    ASSIGN = auto()
    EQ = auto()
    NE = auto()
    LT = auto()
    GT = auto()
    LE = auto()
    GE = auto()
    # delimitadores
    LPAREN = auto()
    RPAREN = auto()
    LBRACE = auto()
    RBRACE = auto()
    SEMI = auto()
    # fim
    EOF = auto()


@dataclass(frozen=True)
class Token:
    type: TokenType
    lexeme: str
    value: object = None   # int para INT, bool para TRUE/FALSE, None nos demais
    line: int = 1
    col: int = 1


# ---------------------------------------------------------------------------
# Autômato finito determinístico (AFD) do lexer
#
# O código abaixo é a transcrição direta da tabela de transições documentada em
# docs/gramatica.md, seção "Lexer". Cada estado tem o mesmo nome aqui e lá, e
# cada entrada do dicionário TRANSICOES é uma célula da tabela. Não usamos o
# módulo `re` de propósito: a justificativa formal do relatório (expressões
# regulares -> AFN -> AFD -> código) só vale se o código for o próprio AFD.
# ---------------------------------------------------------------------------

# --- Classes de caracteres (colunas da tabela) ------------------------------
# Agrupar caracteres em classes deixa a tabela pequena: todas as letras se
# comportam igual em todos os estados, então viram uma coluna só.
LETRA = "letra"
DIGITO = "dígito"
SUBLINHADO = "_"
IGUAL = "="
EXCLAMACAO = "!"
MENOR = "<"
MAIOR = ">"
BARRA = "/"
ASTERISCO = "*"
MAIS = "+"
MENOS = "-"
ABRE_PAR = "("
FECHA_PAR = ")"
ABRE_CHAVE = "{"
FECHA_CHAVE = "}"
PONTO_VIRGULA = ";"
ESPACO = "espaço/tab"
NOVA_LINHA = "\\n"
OUTRO = "outro"

TODAS_AS_CLASSES = [
    LETRA, DIGITO, SUBLINHADO, IGUAL, EXCLAMACAO, MENOR, MAIOR, BARRA,
    ASTERISCO, MAIS, MENOS, ABRE_PAR, FECHA_PAR, ABRE_CHAVE, FECHA_CHAVE,
    PONTO_VIRGULA, ESPACO, NOVA_LINHA, OUTRO,
]

# Caracteres que são, cada um, a sua própria classe.
_CLASSE_DO_SIMBOLO = {
    "_": SUBLINHADO, "=": IGUAL, "!": EXCLAMACAO, "<": MENOR, ">": MAIOR,
    "/": BARRA, "*": ASTERISCO, "+": MAIS, "-": MENOS,
    "(": ABRE_PAR, ")": FECHA_PAR, "{": ABRE_CHAVE, "}": FECHA_CHAVE,
    ";": PONTO_VIRGULA,
    " ": ESPACO, "\t": ESPACO, "\r": ESPACO,
    "\n": NOVA_LINHA,
}


def classificar(c: str) -> str:
    """Devolve a classe (coluna da tabela) do caractere `c`.

    Letras e dígitos são testados por faixa ASCII, e não com str.isalpha() /
    str.isdigit(): em Python 'ç'.isalpha() é True e '²'.isdigit() é True, mas
    esses caracteres não fazem parte do alfabeto da MiniLang.
    """
    if "a" <= c <= "z" or "A" <= c <= "Z":
        return LETRA
    if "0" <= c <= "9":
        return DIGITO
    return _CLASSE_DO_SIMBOLO.get(c, OUTRO)


# --- Estados (linhas da tabela) ---------------------------------------------
INICIAL = "INICIAL"                 # q0: início de um novo lexema
EM_IDENT = "EM_IDENT"               # leu [A-Za-z_][A-Za-z0-9_]*
EM_INT = "EM_INT"                   # leu [0-9]+
NUM_MAL_FORMADO = "NUM_MAL_FORMADO" # leu dígitos seguidos de letra/_ (erro)
EM_ATRIB = "EM_ATRIB"               # leu "="
EM_EQ = "EM_EQ"                     # leu "=="
EM_EXCL = "EM_EXCL"                 # leu "!" (ainda não é token)
EM_NE = "EM_NE"                     # leu "!="
EM_LT = "EM_LT"                     # leu "<"
EM_LE = "EM_LE"                     # leu "<="
EM_GT = "EM_GT"                     # leu ">"
EM_GE = "EM_GE"                     # leu ">="
EM_BARRA = "EM_BARRA"               # leu "/" (divisão ou início de comentário)
EM_MAIS = "EM_MAIS"                 # leu "+"
EM_MENOS = "EM_MENOS"               # leu "-"
EM_ASTERISCO = "EM_ASTERISCO"       # leu "*"
EM_LPAREN = "EM_LPAREN"             # leu "("
EM_RPAREN = "EM_RPAREN"             # leu ")"
EM_LBRACE = "EM_LBRACE"             # leu "{"
EM_RBRACE = "EM_RBRACE"             # leu "}"
EM_SEMI = "EM_SEMI"                 # leu ";"
EM_ESPACO = "EM_ESPACO"             # leu espaços, tabs e quebras de linha
COMENT_LINHA = "COMENT_LINHA"       # dentro de "// ..." (até antes do \n)
COMENT_BLOCO = "COMENT_BLOCO"       # dentro de "/* ..."
COMENT_BLOCO_ESTRELA = "COMENT_BLOCO_ESTRELA"  # dentro do bloco, acabou de ler "*"
COMENT_BLOCO_FIM = "COMENT_BLOCO_FIM"          # leu o "*/" de fechamento


# --- Tabela de transições: (estado, classe) -> próximo estado ----------------
# Par ausente = "—" na tabela do documento = não há transição.
TRANSICOES = {
    # Estado inicial: o primeiro caractere decide qual token está começando.
    (INICIAL, LETRA): EM_IDENT,
    (INICIAL, SUBLINHADO): EM_IDENT,
    (INICIAL, DIGITO): EM_INT,
    (INICIAL, IGUAL): EM_ATRIB,
    (INICIAL, EXCLAMACAO): EM_EXCL,
    (INICIAL, MENOR): EM_LT,
    (INICIAL, MAIOR): EM_GT,
    (INICIAL, BARRA): EM_BARRA,
    (INICIAL, ASTERISCO): EM_ASTERISCO,
    (INICIAL, MAIS): EM_MAIS,
    (INICIAL, MENOS): EM_MENOS,
    (INICIAL, ABRE_PAR): EM_LPAREN,
    (INICIAL, FECHA_PAR): EM_RPAREN,
    (INICIAL, ABRE_CHAVE): EM_LBRACE,
    (INICIAL, FECHA_CHAVE): EM_RBRACE,
    (INICIAL, PONTO_VIRGULA): EM_SEMI,
    (INICIAL, ESPACO): EM_ESPACO,
    (INICIAL, NOVA_LINHA): EM_ESPACO,
    # (INICIAL, OUTRO) não existe: '@', '#', 'ç' etc. são rejeitados.

    # Identificador: letras, dígitos e '_' depois do primeiro caractere.
    (EM_IDENT, LETRA): EM_IDENT,
    (EM_IDENT, DIGITO): EM_IDENT,
    (EM_IDENT, SUBLINHADO): EM_IDENT,

    # Inteiro: mais dígitos continuam o número. Letra ou '_' colada no número
    # leva a um estado de erro (ver comentário em NUM_MAL_FORMADO).
    (EM_INT, DIGITO): EM_INT,
    (EM_INT, LETRA): NUM_MAL_FORMADO,
    (EM_INT, SUBLINHADO): NUM_MAL_FORMADO,

    # NUM_MAL_FORMADO não é de aceitação. Ele continua consumindo letras,
    # dígitos e '_' só para que a mensagem de erro mostre o lexema inteiro
    # ("12ab", e não apenas "12a").
    (NUM_MAL_FORMADO, LETRA): NUM_MAL_FORMADO,
    (NUM_MAL_FORMADO, DIGITO): NUM_MAL_FORMADO,
    (NUM_MAL_FORMADO, SUBLINHADO): NUM_MAL_FORMADO,

    # Operadores de dois caracteres: o '=' depois de '=', '!', '<', '>'.
    (EM_ATRIB, IGUAL): EM_EQ,
    (EM_EXCL, IGUAL): EM_NE,
    (EM_LT, IGUAL): EM_LE,
    (EM_GT, IGUAL): EM_GE,

    # '/' pode ser divisão, início de comentário de linha ou de bloco.
    (EM_BARRA, BARRA): COMENT_LINHA,
    (EM_BARRA, ASTERISCO): COMENT_BLOCO,

    # Espaços em branco consecutivos formam um único lexema descartado.
    (EM_ESPACO, ESPACO): EM_ESPACO,
    (EM_ESPACO, NOVA_LINHA): EM_ESPACO,

    # Comentário de bloco: '*' pode ser o começo do fechamento "*/".
    (COMENT_BLOCO_ESTRELA, ASTERISCO): COMENT_BLOCO_ESTRELA,  # "**/" também fecha
    (COMENT_BLOCO_ESTRELA, BARRA): COMENT_BLOCO_FIM,
}

# Comentários aceitam qualquer caractere (inclusive acentos, que estão na
# classe OUTRO). Em vez de escrever 19 linhas iguais, geramos as transições
# "para todas as classes, exceto...". Na tabela do documento elas aparecem
# como células preenchidas uma a uma.
for _classe in TODAS_AS_CLASSES:
    if _classe != NOVA_LINHA:
        TRANSICOES[(COMENT_LINHA, _classe)] = COMENT_LINHA
    if _classe != ASTERISCO:
        TRANSICOES[(COMENT_BLOCO, _classe)] = COMENT_BLOCO
    else:
        TRANSICOES[(COMENT_BLOCO, _classe)] = COMENT_BLOCO_ESTRELA
    if _classe not in (ASTERISCO, BARRA):
        TRANSICOES[(COMENT_BLOCO_ESTRELA, _classe)] = COMENT_BLOCO


# --- Estados de aceitação ----------------------------------------------------
# Cada estado de aceitação corresponde a exatamente uma classe de token.
# DESCARTAR marca lexemas que são reconhecidos mas não viram token
# (espaço em branco e comentários).
DESCARTAR = "descartar"

ACEITACAO = {
    EM_IDENT: TokenType.IDENT,   # depois consultamos PALAVRAS_RESERVADAS
    EM_INT: TokenType.INT,
    EM_ATRIB: TokenType.ASSIGN,
    EM_EQ: TokenType.EQ,
    EM_NE: TokenType.NE,
    EM_LT: TokenType.LT,
    EM_LE: TokenType.LE,
    EM_GT: TokenType.GT,
    EM_GE: TokenType.GE,
    EM_BARRA: TokenType.SLASH,
    EM_MAIS: TokenType.PLUS,
    EM_MENOS: TokenType.MINUS,
    EM_ASTERISCO: TokenType.STAR,
    EM_LPAREN: TokenType.LPAREN,
    EM_RPAREN: TokenType.RPAREN,
    EM_LBRACE: TokenType.LBRACE,
    EM_RBRACE: TokenType.RBRACE,
    EM_SEMI: TokenType.SEMI,
    EM_ESPACO: DESCARTAR,
    COMENT_LINHA: DESCARTAR,
    COMENT_BLOCO_FIM: DESCARTAR,
}

# Palavras reservadas. O AFD reconhece todas como identificador e esta tabela
# reclassifica o lexema. É equivalente a ter no AFD um caminho próprio para
# cada palavra (ver docs/relatorio/02_analise_lexica.md), com bem menos estados.
PALAVRAS_RESERVADAS = {
    "if": TokenType.IF,
    "else": TokenType.ELSE,
    "while": TokenType.WHILE,
    "for": TokenType.FOR,
    "print": TokenType.PRINT,
    "true": TokenType.TRUE,
    "false": TokenType.FALSE,
}


class Lexer:
    def __init__(self, source: str):
        self.source = source
        self.pos = 0       # índice do próximo caractere a ler
        self.linha = 1     # linha do próximo caractere (começa em 1)
        self.coluna = 1    # coluna do próximo caractere (começa em 1; tab = 1)

    def tokenize(self) -> List[Token]:
        """Particiona a entrada em tokens, simulando o AFD uma vez por lexema.

        Regra de parada (maior casamento): a partir de INICIAL, seguimos
        transições enquanto existirem. Quando não há transição para o próximo
        caractere (ou a entrada acabou), olhamos o estado atual:
          - de aceitação  -> o lexema lido é um token (ou é descartado);
          - não aceitação -> erro léxico.
        Não há retrocesso para um estado de aceitação anterior. Para os tokens
        da MiniLang isso nunca é necessário, e é justamente o que faz "1x" ser
        erro em vez de virar INT(1) seguido de IDENT(x).
        """
        tokens: List[Token] = []
        self.pos, self.linha, self.coluna = 0, 1, 1

        while self.pos < len(self.source):
            # Posição de início do lexema: é ela que vai no token e nos erros.
            inicio = self.pos
            linha_inicio, coluna_inicio = self.linha, self.coluna

            estado = INICIAL
            while self.pos < len(self.source):
                classe = classificar(self.source[self.pos])
                proximo = TRANSICOES.get((estado, classe))
                if proximo is None:
                    break
                estado = proximo
                self._avancar()

            lexema = self.source[inicio:self.pos]
            tipo = ACEITACAO.get(estado)
            if tipo is None:
                self._erro(estado, lexema, linha_inicio, coluna_inicio)
            if tipo == DESCARTAR:
                continue
            tokens.append(self._criar_token(tipo, lexema, linha_inicio, coluna_inicio))

        tokens.append(Token(TokenType.EOF, "", None, self.linha, self.coluna))
        return tokens

    def _avancar(self) -> None:
        """Consome um caractere atualizando linha e coluna."""
        if self.source[self.pos] == "\n":
            self.linha += 1
            self.coluna = 1
        else:
            self.coluna += 1
        self.pos += 1

    @staticmethod
    def _criar_token(tipo: TokenType, lexema: str, linha: int, coluna: int) -> Token:
        if tipo == TokenType.IDENT:
            # Prioridade das palavras reservadas sobre identificadores.
            tipo = PALAVRAS_RESERVADAS.get(lexema, TokenType.IDENT)
        valor: object = None
        if tipo == TokenType.INT:
            valor = int(lexema)
        elif tipo == TokenType.TRUE:
            valor = True
        elif tipo == TokenType.FALSE:
            valor = False
        return Token(tipo, lexema, valor, linha, coluna)

    def _erro(self, estado: str, lexema: str, linha: int, coluna: int) -> None:
        """Lança LexicalError conforme o estado (não de aceitação) em que o AFD parou."""
        if estado == INICIAL:
            # Nenhuma transição a partir de q0: o caractere não inicia token algum.
            c = self.source[self.pos]
            raise LexicalError(f"caractere inválido '{c}'", linha, coluna)
        if estado == EM_EXCL:
            raise LexicalError(
                "caractere inválido '!' (o operador de diferença é '!=')", linha, coluna)
        if estado == NUM_MAL_FORMADO:
            raise LexicalError(
                f"número mal formado '{lexema}': identificadores não podem começar com dígito",
                linha, coluna)
        if estado in (COMENT_BLOCO, COMENT_BLOCO_ESTRELA):
            # Esses estados têm transição para toda classe; só param no fim da entrada.
            raise LexicalError("comentário de bloco não fechado", linha, coluna)
        # Não deve acontecer: todo estado sem aceitação está tratado acima.
        raise LexicalError(f"erro léxico inesperado no estado {estado}", linha, coluna)


def tokenize(source: str) -> List[Token]:
    return Lexer(source).tokenize()
