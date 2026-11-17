"""Analisador sintático descendente recursivo da MiniLang.

CONTRATO:
    Parser(tokens).parse() -> ast_nodes.Program
    parse(source: str) -> ast_nodes.Program        (lexer + parser)
    Erros: lança src.errors.MiniLangSyntaxError; `.errors` lista todos os
    diagnósticos encontrados (recuperação em modo pânico).

Técnica: análise descendente recursiva preditiva, LL(1). Existe uma função para cada
não-terminal da EBNF de docs/gramatica.md, com o mesmo nome. Cada função olha apenas o
token atual (um token de lookahead) para decidir qual produção seguir. Isso funciona
porque a gramática não tem recursão à esquerda e, em cada ponto de escolha, os conjuntos
FIRST das alternativas são disjuntos (ver docs/relatorio/03_analise_sintatica.md).

Única exceção ao lookahead de um token: na sincronização do modo pânico, olhamos dois
tokens (IDENT seguido de '=') para reconhecer o início de uma atribuição. Isso é só
recuperação de erro; o reconhecimento de programas corretos continua LL(1).
"""
from __future__ import annotations

from typing import Callable, List, Optional, Union

from src.ast_nodes import (
    Assign, BinOp, Block, BoolLiteral, Expr, For, If, IntLiteral, Print, Program,
    Stmt, UnaryOp, Var, While,
)
from src.errors import MiniLangSyntaxError
from src.lexer import Token, TokenType, tokenize

T = TokenType

# FIRST(comando): os tokens que podem iniciar um comando. É o conjunto usado para
# escolher a produção de `comando` e também como ponto de sincronização.
FIRST_COMANDO = {T.IDENT, T.PRINT, T.IF, T.WHILE, T.FOR, T.LBRACE}

# FIRST(expressao) = FIRST(unaria) = { "-" } ∪ FIRST(primaria).
FIRST_EXPRESSAO = {T.MINUS, T.INT, T.TRUE, T.FALSE, T.IDENT, T.LPAREN}

# Operadores de cada nível de precedência.
OPS_IGUALDADE = {T.EQ, T.NE}
OPS_RELACIONAL = {T.LT, T.GT, T.LE, T.GE}
OPS_ADITIVA = {T.PLUS, T.MINUS}
OPS_MULTIPLICATIVA = {T.STAR, T.SLASH}

# Como cada tipo de token aparece nas mensagens "esperado X".
DESCRICAO = {
    T.INT: "número inteiro", T.TRUE: "'true'", T.FALSE: "'false'",
    T.IDENT: "identificador",
    T.IF: "'if'", T.ELSE: "'else'", T.WHILE: "'while'", T.FOR: "'for'",
    T.PRINT: "'print'",
    T.PLUS: "'+'", T.MINUS: "'-'", T.STAR: "'*'", T.SLASH: "'/'",
    T.ASSIGN: "'='", T.EQ: "'=='", T.NE: "'!='",
    T.LT: "'<'", T.GT: "'>'", T.LE: "'<='", T.GE: "'>='",
    T.LPAREN: "'('", T.RPAREN: "')'", T.LBRACE: "'{'", T.RBRACE: "'}'",
    T.SEMI: "';'", T.EOF: "fim do arquivo",
}

# Lembrete repetido nas mensagens de erro do cabeçalho do for.
FORMATO_FOR = "(o for exige inicialização; condição; atualização)"


def descrever(token: Token) -> str:
    """Texto do token encontrado, para a parte "encontrado Y" das mensagens."""
    if token.type == T.EOF:
        return "fim do arquivo"
    return "'" + token.lexeme + "'"


class Parser:
    def __init__(self, tokens: List[Token]):
        self.tokens = list(tokens)
        # O contrato do lexer garante EOF no final. Testes que montam tokens à mão
        # podem esquecer; sem EOF o parser leria além do fim da lista.
        if not self.tokens or self.tokens[-1].type != T.EOF:
            ultimo = self.tokens[-1] if self.tokens else None
            linha = ultimo.line if ultimo else 1
            coluna = (ultimo.col + len(ultimo.lexeme)) if ultimo else 1
            self.tokens.append(Token(T.EOF, "", None, linha, coluna))
        self.pos = 0
        # Todos os erros sintáticos encontrados, na ordem em que apareceram.
        self.errors: List[MiniLangSyntaxError] = []

    # ------------------------------------------------------------ utilitários

    def atual(self) -> Token:
        """Token de lookahead (ainda não consumido)."""
        return self.tokens[self.pos]

    def seguinte(self) -> Token:
        """Token depois do atual. Usado apenas na sincronização (IDENT seguido de '=')."""
        if self.pos + 1 < len(self.tokens):
            return self.tokens[self.pos + 1]
        return self.tokens[-1]

    def anterior(self) -> Optional[Token]:
        """Último token consumido; serve para dizer "após '+'" nas mensagens."""
        if self.pos == 0:
            return None
        return self.tokens[self.pos - 1]

    def check(self, *tipos: TokenType) -> bool:
        return self.atual().type in tipos

    def advance(self) -> Token:
        """Consome o token atual. Nunca passa do EOF, para que nenhum laço leia
        fora da lista."""
        token = self.atual()
        if token.type != T.EOF:
            self.pos += 1
        return token

    def error(self, mensagem: str, token: Optional[Token] = None) -> MiniLangSyntaxError:
        """Registra um diagnóstico e o devolve para ser lançado com `raise`.

        Registrar aqui (e não no ponto em que a exceção é capturada) garante que cada
        erro entra na lista exatamente uma vez, mesmo que a exceção seja relançada.
        """
        if token is None:
            token = self.atual()
        erro = MiniLangSyntaxError(mensagem, token.line, token.col)
        self.errors.append(erro)
        return erro

    def expect(self, tipo: TokenType, contexto: str) -> Token:
        """Consome um token do tipo exigido pela produção ou lança erro sintático.

        `contexto` completa a mensagem: "esperado ';' <contexto>, encontrado ')'".
        """
        if self.check(tipo):
            return self.advance()
        esperado = DESCRICAO[tipo] + (" " + contexto if contexto else "")
        raise self.error("esperado {}, encontrado {}".format(esperado, descrever(self.atual())))

    # ------------------------------------------------------------ ponto de entrada

    def parse(self) -> Program:
        programa = self.programa()
        if self.errors:
            primeiro = self.errors[0]
            raise MiniLangSyntaxError(primeiro.message, primeiro.line, primeiro.col,
                                      errors=list(self.errors))
        return programa

    # ------------------------------------------------------------ comandos

    def programa(self) -> Program:
        """programa = { comando } EOF ;"""
        comandos = self.lista_de_comandos(dentro_de_bloco=False)
        self.expect(T.EOF, "no fim do programa")
        return Program(comandos, 1, 1)

    def lista_de_comandos(self, dentro_de_bloco: bool) -> List[Stmt]:
        """A repetição `{ comando }` de `programa` e de `bloco`.

        A repetição para quando o token atual não pode iniciar mais um comando:
        em `programa` isso é EOF; em `bloco` é '}' (ou EOF, se o bloco não foi
        fechado). '}' e EOF estão em FOLLOW de `{ comando }` e fora de FIRST(comando),
        então a decisão de continuar ou parar é LL(1).

        Aqui fica o tratamento de erro em nível de comando: se um comando falhar,
        o erro já foi registrado; sincronizamos e seguimos para o próximo comando.
        """
        comandos: List[Stmt] = []
        while not self.check(T.EOF) and not (dentro_de_bloco and self.check(T.RBRACE)):
            inicio = self.pos
            try:
                comando = self.comando()
                if comando is not None:
                    comandos.append(comando)
            except MiniLangSyntaxError:
                self.sincronizar()
                # Garantia de progresso: se a sincronização parou no mesmo token em
                # que o comando começou (ex.: '}' sobrando no nível do programa),
                # descartamos esse token; senão o laço repetiria o mesmo erro para sempre.
                if self.pos == inicio:
                    self.advance()
        return comandos

    def comando(self) -> Optional[Stmt]:
        """comando = atribuicao_cmd | print_cmd | if_cmd | while_cmd | for_cmd | bloco ;

        Escolha LL(1): cada alternativa começa por um token diferente.
        """
        token = self.atual()
        if token.type == T.IDENT:
            return self.atribuicao_cmd()
        if token.type == T.PRINT:
            return self.print_cmd()
        if token.type == T.IF:
            return self.if_cmd()
        if token.type == T.WHILE:
            return self.while_cmd()
        if token.type == T.FOR:
            return self.for_cmd()
        if token.type == T.LBRACE:
            return self.bloco("")
        if token.type == T.ELSE:
            # 'else' não está em FIRST(comando): só pode aparecer logo após o bloco
            # de um if. Mensagem específica porque é um engano comum.
            raise self.error("'else' sem 'if' correspondente (o 'else' deve vir logo "
                             "depois do bloco do if)")
        raise self.error("esperado início de comando (identificador, 'print', 'if', "
                         "'while', 'for' ou '{{'), encontrado {}".format(descrever(token)))

    def atribuicao_cmd(self) -> Assign:
        """atribuicao_cmd = atribuicao ";" ;"""
        atribuicao = self.atribuicao(
            "(um comando que começa por identificador é uma atribuição)")
        if self.check(T.ASSIGN):
            # Caso de `x = y = 1;`: depois de `x = y` a gramática exige ';'.
            raise self.error("esperado ';' após a atribuição, encontrado '=' (atribuição "
                             "é comando, não expressão; escreva dois comandos separados)")
        self.expect(T.SEMI, "após a atribuição")
        return atribuicao

    def atribuicao(self, contexto: str) -> Assign:
        """atribuicao = IDENT "=" expressao ;

        Usada por atribuicao_cmd e pelas cláusulas de inicialização e atualização do
        for; `contexto` diz qual delas está sendo analisada, para a mensagem de erro.
        """
        nome = self.expect(T.IDENT, contexto)
        self.expect(T.ASSIGN, "após '{}' {}".format(nome.lexeme, contexto))
        valor = self.expressao()
        return Assign(nome.lexeme, valor, nome.line, nome.col)

    def print_cmd(self) -> Print:
        """print_cmd = "print" "(" expressao ")" ";" ;"""
        palavra = self.expect(T.PRINT, "")
        self.expect(T.LPAREN, "após 'print' (use print(expressão);)")
        valor = self.expressao()
        if self.check(T.ASSIGN):
            raise self.error("esperado ')' para fechar o print, encontrado '=' (atribuição "
                             "é comando, não expressão; atribua antes e imprima a variável)")
        self.expect(T.RPAREN, "para fechar o print")
        self.expect(T.SEMI, "após o print")
        return Print(valor, palavra.line, palavra.col)

    def if_cmd(self) -> If:
        """if_cmd = "if" "(" expressao ")" bloco [ "else" ( bloco | if_cmd ) ] ;

        O `[ "else" ... ]` é decidido pelo lookahead: se o token após o bloco é
        'else', a parte opcional está presente; caso contrário (qualquer token de
        FOLLOW(if_cmd), que não contém 'else') ela está ausente.
        """
        palavra = self.expect(T.IF, "")
        condicao = self.cabecalho("if", lambda: self.condicao("if"))
        entao = self.bloco("do if")
        senao: Optional[Union[Block, If]] = None
        if self.check(T.ELSE):
            self.advance()
            if self.check(T.IF):
                senao = self.if_cmd()         # else if: um if aninhado no ramo else
            elif self.check(T.LBRACE):
                senao = self.bloco("do else")
            else:
                raise self.error("esperado '{{' ou 'if' após 'else', encontrado {}".format(
                    descrever(self.atual())))
        return If(condicao, entao, senao, palavra.line, palavra.col)

    def while_cmd(self) -> While:
        """while_cmd = "while" "(" expressao ")" bloco ;

        Corresponde 1 para 1 à produção: expect('while'), expect('('), expressao,
        expect(')'), bloco.
        """
        palavra = self.expect(T.WHILE, "")
        condicao = self.cabecalho("while", lambda: self.condicao("while"))
        corpo = self.bloco("do while")
        return While(condicao, corpo, palavra.line, palavra.col)

    def for_cmd(self) -> For:
        """for_cmd = "for" "(" atribuicao ";" expressao ";" atribuicao ")" bloco ;

        As três cláusulas são obrigatórias: cada `expect(';')` exige o separador e
        cada cláusula exige começar por um token do seu FIRST.
        """
        palavra = self.expect(T.FOR, "")
        inicio, condicao, atualizacao = self.cabecalho("for", self.clausulas_for)
        corpo = self.bloco("do for")
        return For(inicio, condicao, atualizacao, corpo, palavra.line, palavra.col)

    def clausulas_for(self):
        """Parte `atribuicao ";" expressao ";" atribuicao ")"` do cabeçalho do for
        (o '(' é consumido por `cabecalho`). Devolve (inicio, condicao, atualizacao)."""
        inicio = self.atribuicao("na inicialização do for " + FORMATO_FOR)
        self.expect(T.SEMI, "após a inicialização do for " + FORMATO_FOR)
        if not self.check(*FIRST_EXPRESSAO):
            # Verificamos FIRST(expressao) aqui só para dar uma mensagem que fale da
            # condição do for, em vez da mensagem genérica de expressão.
            raise self.error("esperado expressão na condição do for {}, encontrado {}"
                             .format(FORMATO_FOR, descrever(self.atual())))
        condicao = self.expressao()
        self.expect(T.SEMI, "após a condição do for " + FORMATO_FOR)
        atualizacao = self.atribuicao("na atualização do for " + FORMATO_FOR)
        self.expect(T.RPAREN, "após a atualização do for")
        return inicio, condicao, atualizacao

    def condicao(self, dono: str) -> Expr:
        """Parte `expressao ")"` do cabeçalho de if e while (o '(' é consumido por
        `cabecalho`)."""
        resultado = self.expressao()
        self.expect(T.RPAREN, "após a condição do " + dono)
        return resultado

    def cabecalho(self, dono: str, conteudo: Callable[[], object]):
        """Analisa `"(" ... ")"` do cabeçalho de if, while ou for.

        Recuperação local: se houver erro dentro dos parênteses, descartamos tokens
        até o ')' que fecha o cabeçalho e continuamos no corpo. Assim, erros dentro do
        corpo também são reportados, e o ';' interno do for não é confundido com o
        fim de um comando (o que geraria erros em cascata).
        """
        self.expect(T.LPAREN, "após '{}'".format(dono))
        try:
            return conteudo()
        except MiniLangSyntaxError as erro:
            self.recuperar_cabecalho()
            if not self.check(T.LBRACE):
                # Sem corpo à vista: deixamos a sincronização geral agir, sem
                # reportar um segundo erro ("esperado '{'") que seria só consequência.
                raise erro
            self.bloco("do " + dono)   # analisa o corpo só para achar erros nele
            raise erro

    def bloco(self, dono: str) -> Block:
        """bloco = "{" { comando } "}" ;"""
        if dono:
            contexto = "para abrir o corpo {} (o corpo deve estar entre chaves)".format(dono)
        else:
            contexto = "para abrir o bloco"
        abre = self.expect(T.LBRACE, contexto)
        comandos = self.lista_de_comandos(dentro_de_bloco=True)
        self.expect(T.RBRACE, "para fechar o bloco aberto na linha {}".format(abre.line))
        return Block(comandos, abre.line, abre.col)

    # ------------------------------------------------------------ expressões
    # Um não-terminal por nível de precedência, do menos prioritário (expressao)
    # para o mais prioritário (primaria).

    def expressao(self) -> Expr:
        """expressao = igualdade ;"""
        return self.igualdade()

    def igualdade(self) -> Expr:
        """igualdade = relacional [ ( "==" | "!=" ) relacional ] ;

        `[ ]` e não `{ }`: no máximo um operador neste nível (não associativo).
        """
        esquerda = self.relacional()
        if self.check(*OPS_IGUALDADE):
            op = self.advance()
            direita = self.relacional()
            esquerda = BinOp(op.lexeme, esquerda, direita, op.line, op.col)
            if self.check(*OPS_IGUALDADE):
                raise self.error(self.mensagem_nao_associativo())
        return esquerda

    def relacional(self) -> Expr:
        """relacional = aditiva [ ( "<" | ">" | "<=" | ">=" ) aditiva ] ;"""
        esquerda = self.aditiva()
        if self.check(*OPS_RELACIONAL):
            op = self.advance()
            direita = self.aditiva()
            esquerda = BinOp(op.lexeme, esquerda, direita, op.line, op.col)
            if self.check(*OPS_RELACIONAL):
                raise self.error(self.mensagem_nao_associativo())
        return esquerda

    def mensagem_nao_associativo(self) -> str:
        return ("operadores de comparação não são associativos; use parênteses, "
                "ex.: (a < b) == c (encontrado {} depois de uma comparação)"
                .format(descrever(self.atual())))

    def aditiva(self) -> Expr:
        """aditiva = multiplicativa { ( "+" | "-" ) multiplicativa } ;

        Associatividade à esquerda: a cada volta do laço, o resultado acumulado vira
        o filho esquerdo do novo BinOp. `10 - 3 - 2` vira ((10 - 3) - 2).
        """
        esquerda = self.multiplicativa()
        while self.check(*OPS_ADITIVA):
            op = self.advance()
            direita = self.multiplicativa()
            esquerda = BinOp(op.lexeme, esquerda, direita, op.line, op.col)
        return esquerda

    def multiplicativa(self) -> Expr:
        """multiplicativa = unaria { ( "*" | "/" ) unaria } ;  (mesmo laço da aditiva)"""
        esquerda = self.unaria()
        while self.check(*OPS_MULTIPLICATIVA):
            op = self.advance()
            direita = self.unaria()
            esquerda = BinOp(op.lexeme, esquerda, direita, op.line, op.col)
        return esquerda

    def unaria(self) -> Expr:
        """unaria = "-" unaria | primaria ;

        Aqui a recursão à direita é o que queremos: `- - 1` é -(-(1)).
        """
        if self.check(T.MINUS):
            op = self.advance()
            operando = self.unaria()
            return UnaryOp("-", operando, op.line, op.col)
        return self.primaria()

    def primaria(self) -> Expr:
        """primaria = INT | "true" | "false" | IDENT | "(" expressao ")" ;"""
        token = self.atual()
        if token.type == T.INT:
            self.advance()
            return IntLiteral(token.value if token.value is not None else int(token.lexeme),
                              token.line, token.col)
        if token.type in (T.TRUE, T.FALSE):
            self.advance()
            return BoolLiteral(token.type == T.TRUE, token.line, token.col)
        if token.type == T.IDENT:
            self.advance()
            return Var(token.lexeme, token.line, token.col)
        if token.type == T.LPAREN:
            self.advance()
            interna = self.expressao()
            self.expect(T.RPAREN, "para fechar o '(' da linha {}, coluna {}".format(
                token.line, token.col))
            # Os parênteses não viram nó: a estrutura da árvore já registra o agrupamento.
            return interna
        # O token não está em FIRST(primaria): não há como começar uma expressão aqui.
        anterior = self.anterior()
        onde = " após '{}'".format(anterior.lexeme) if anterior is not None else ""
        raise self.error("esperado expressão{}, encontrado {}".format(onde, descrever(token)))

    # ------------------------------------------------------------ recuperação

    def sincronizar(self) -> None:
        """Modo pânico: descarta tokens até um ponto seguro para recomeçar.

        Pontos de sincronização:
          - ';'  → fim do comando com erro: consumimos e paramos;
          - '}'  → fim do bloco: paramos sem consumir, para o bloco fechar;
          - 'print', 'if', 'while', 'for', '{' → início de comando: paramos;
          - IDENT seguido de '=' → início de atribuição: paramos.
            (Um IDENT sozinho não basta, porque identificadores aparecem no meio de
            expressões; parar neles produziria erros em cascata.)
          - EOF → nada mais a descartar.
        """
        while not self.check(T.EOF):
            if self.check(T.SEMI):
                self.advance()
                return
            if self.check(T.RBRACE, T.PRINT, T.IF, T.WHILE, T.FOR, T.LBRACE):
                return
            if self.check(T.IDENT) and self.seguinte().type == T.ASSIGN:
                return
            self.advance()

    def recuperar_cabecalho(self) -> None:
        """Descarta tokens até o ')' que fecha o cabeçalho de if/while/for (contando
        parênteses aninhados) e o consome. Para antes, sem consumir, em '{', '}',
        palavra-chave de comando ou EOF, pois eles nunca aparecem dentro de parênteses
        (provavelmente o ')' é que está faltando)."""
        profundidade = 0
        while not self.check(T.EOF, T.LBRACE, T.RBRACE, T.PRINT, T.IF, T.WHILE, T.FOR):
            token = self.advance()
            if token.type == T.LPAREN:
                profundidade += 1
            elif token.type == T.RPAREN:
                if profundidade == 0:
                    return
                profundidade -= 1


def parse(source: str) -> Program:
    return Parser(tokenize(source)).parse()
