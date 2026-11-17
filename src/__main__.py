"""Interface de linha de comando da MiniLang.

Uso:
    python -m src ARQUIVO.ml [--tokens] [--ast] [--max-iter N]

Sem flags, o programa é executado e só a saída dos `print` aparece.
Com `--tokens` e/ou `--ast`, a CLI mostra o resultado das fases intermediárias
(lista de tokens do lexer e árvore do parser) antes da execução, para que dê para
acompanhar o caminho código-fonte -> tokens -> AST -> saída.

Códigos de saída:
    0  programa executado sem erros
    1  erro da linguagem (léxico, sintático ou semântico)
    2  problema com o arquivo (inexistente ou ilegível) ou argumentos inválidos
"""
from __future__ import annotations

import argparse
import sys
from typing import List, Optional

from src.ast_nodes import format_tree
from src.errors import MiniLangError, MiniLangSyntaxError
from src.interpreter import DEFAULT_MAX_ITERATIONS, Interpreter
from src.lexer import Token, tokenize
from src.parser import Parser


def criar_parser_argumentos() -> argparse.ArgumentParser:
    """Define os argumentos aceitos pela CLI."""
    ap = argparse.ArgumentParser(
        prog="python -m src",
        description="Compilador-intérprete da linguagem MiniLang.",
    )
    ap.add_argument("arquivo", help="caminho do programa MiniLang (.ml)")
    ap.add_argument("--tokens", action="store_true",
                    help="mostra a tabela de tokens produzida pelo lexer")
    ap.add_argument("--ast", action="store_true",
                    help="mostra a árvore sintática abstrata produzida pelo parser")
    ap.add_argument("--max-iter", type=int, default=DEFAULT_MAX_ITERATIONS, metavar="N",
                    help="limite de iterações por laço (padrão: %(default)s)")
    return ap


def titulo(texto: str) -> None:
    """Imprime um cabeçalho simples para separar as fases na saída."""
    print(f"=== {texto} ===")


def imprimir_tokens(tokens: List[Token]) -> None:
    """Imprime os tokens em forma de tabela com colunas alinhadas."""
    linhas = []
    for tok in tokens:
        # O EOF não tem texto; mostramos um traço para a coluna não ficar vazia.
        lexema = tok.lexeme if tok.lexeme else "-"
        linhas.append((tok.type.name, lexema, f"{tok.line}:{tok.col}"))

    cabecalho = ("TIPO", "LEXEMA", "LINHA:COLUNA")
    # Largura de cada coluna = maior texto entre o cabeçalho e os valores.
    largura_tipo = max(len(cabecalho[0]), *(len(l[0]) for l in linhas))
    largura_lexema = max(len(cabecalho[1]), *(len(l[1]) for l in linhas))

    def formatar(tipo: str, lexema: str, posicao: str) -> str:
        return f"{tipo:<{largura_tipo}}  {lexema:<{largura_lexema}}  {posicao}"

    print(formatar(*cabecalho))
    print(formatar("-" * largura_tipo, "-" * largura_lexema, "-" * len(cabecalho[2])))
    for linha in linhas:
        print(formatar(*linha))
    print(f"({len(tokens)} tokens)")


def mostrar_trecho(fonte: str, linha: Optional[int], coluna: Optional[int]) -> None:
    """Mostra, em stderr, a linha do código onde o erro ocorreu com um ^ embaixo
    da coluna. Se a posição for desconhecida ou inválida, não mostra nada."""
    if linha is None:
        return
    linhas_fonte = fonte.splitlines()
    if not (1 <= linha <= len(linhas_fonte)):
        return
    texto = linhas_fonte[linha - 1]
    prefixo = f"  {linha} | "
    print(prefixo + texto, file=sys.stderr)
    if coluna is not None and coluna >= 1:
        # Tabulações são preservadas para o ^ ficar alinhado com o caractere certo.
        recuo = "".join("\t" if c == "\t" else " " for c in texto[:coluna - 1])
        print(" " * len(prefixo) + recuo + "^", file=sys.stderr)


def relatar_erro(erro: MiniLangError, fonte: str) -> None:
    """Imprime o erro da linguagem em stderr. Um erro sintático pode carregar
    vários diagnósticos (recuperação em modo pânico); todos são mostrados."""
    if isinstance(erro, MiniLangSyntaxError):
        diagnosticos = list(erro.errors)
    else:
        diagnosticos = [erro]
    for diag in diagnosticos:
        print(diag.format(), file=sys.stderr)
        mostrar_trecho(fonte, diag.line, diag.col)
    if len(diagnosticos) > 1:
        print(f"{len(diagnosticos)} erros sintáticos encontrados.", file=sys.stderr)


def main(argv: Optional[List[str]] = None) -> int:
    args = criar_parser_argumentos().parse_args(argv)

    try:
        with open(args.arquivo, encoding="utf-8") as f:
            fonte = f.read()
    except FileNotFoundError:
        print(f"Erro: arquivo não encontrado: {args.arquivo}", file=sys.stderr)
        return 2
    except OSError as e:
        print(f"Erro: não foi possível ler {args.arquivo}: {e.strerror}", file=sys.stderr)
        return 2

    mostrar_fases = args.tokens or args.ast
    try:
        # Fase 1: análise léxica
        tokens = tokenize(fonte)
        if args.tokens:
            titulo("Tokens")
            imprimir_tokens(tokens)
            print()

        # Fase 2: análise sintática (constrói a AST)
        programa = Parser(tokens).parse()
        if args.ast:
            titulo("AST")
            print(format_tree(programa))
            print()

        # Fase 3: interpretação (as checagens semânticas acontecem aqui)
        if mostrar_fases:
            titulo("Saída")
        # flush=True para a saída do programa não se misturar com mensagens de
        # erro em stderr quando os dois fluxos vão para o mesmo terminal.
        interpretador = Interpreter(output=lambda s: print(s, flush=True),
                                    max_iterations=args.max_iter)
        interpretador.execute(programa)
    except MiniLangError as erro:
        sys.stdout.flush()
        relatar_erro(erro, fonte)
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
