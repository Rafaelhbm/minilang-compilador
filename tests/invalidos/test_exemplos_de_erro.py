"""Confere cada programa de exemplos/erros/ contra o erro que ele mesmo anuncia.

A primeira linha de cada exemplo diz o erro esperado, por exemplo:

    // Erro esperado: LÉXICO na linha 4, coluna 7.
    // Erro esperado: SEMÂNTICO (divisão por zero) na linha 6.

O teste roda o arquivo pela CLI e verifica: código de saída 1, categoria e linha
(e a coluna, quando informada) na mensagem, e nenhum traceback do Python. Assim o
catálogo de erros (docs/relatorio/06_catalogo_erros.md) e os exemplos não podem
ficar desatualizados em relação ao compilador sem que a suíte acuse.
"""
import os
import re
import subprocess
import sys
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parents[2]
PASTA_ERROS = RAIZ / "exemplos" / "erros"

CABECALHO = re.compile(
    r"^// Erro esperado: (?P<categoria>LÉXICO|SINTÁTICO|SEMÂNTICO)\b.*?"
    r"na linha (?P<linha>\d+)(?:, coluna (?P<coluna>\d+))?"
)

NOME_NA_MENSAGEM = {"LÉXICO": "léxico", "SINTÁTICO": "sintático", "SEMÂNTICO": "semântico"}
PREFIXO_DO_ARQUIVO = {"LÉXICO": "lexico_", "SINTÁTICO": "sintatico_", "SEMÂNTICO": "semantico_"}

EXEMPLOS = sorted(PASTA_ERROS.glob("*.ml"))


def esperado(arquivo: Path):
    primeira_linha = arquivo.read_text(encoding="utf-8").splitlines()[0]
    casamento = CABECALHO.match(primeira_linha)
    assert casamento, f"{arquivo.name}: primeira linha fora do formato 'Erro esperado'"
    return casamento.group("categoria"), casamento.group("linha"), casamento.group("coluna")


def rodar_cli(arquivo: Path):
    return subprocess.run(
        [sys.executable, "-m", "src", str(arquivo)],
        cwd=RAIZ,
        capture_output=True,
        text=True,
        encoding="utf-8",
        timeout=30,
        env={**os.environ, "PYTHONIOENCODING": "utf-8"},
    )


def test_existem_tres_exemplos_de_cada_categoria():
    for categoria, prefixo in PREFIXO_DO_ARQUIVO.items():
        arquivos = [a for a in EXEMPLOS if a.name.startswith(prefixo)]
        assert len(arquivos) == 3, f"esperados 3 exemplos {categoria}, há {len(arquivos)}"


@pytest.mark.parametrize("arquivo", EXEMPLOS, ids=lambda a: a.stem)
def test_nome_do_arquivo_bate_com_a_categoria_anunciada(arquivo):
    categoria, _, _ = esperado(arquivo)
    assert arquivo.name.startswith(PREFIXO_DO_ARQUIVO[categoria])


@pytest.mark.parametrize("arquivo", EXEMPLOS, ids=lambda a: a.stem)
def test_exemplo_produz_o_erro_anunciado(arquivo):
    categoria, linha, coluna = esperado(arquivo)
    resultado = rodar_cli(arquivo)

    assert resultado.returncode == 1, resultado.stderr
    assert "Traceback" not in resultado.stderr

    inicio = f"[Erro {NOME_NA_MENSAGEM[categoria]}] linha {linha}"
    if coluna is not None:
        inicio += f", coluna {coluna}:"
    assert inicio in resultado.stderr, resultado.stderr
    # A linha do código e o ^ apontando a coluna vêm logo depois da mensagem.
    assert "^" in resultado.stderr
