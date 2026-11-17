"""Testes da CLI (`python -m src`), executada como um processo separado.

Rodar a CLI via subprocess testa o que o usuário realmente vê: o texto em stdout,
as mensagens em stderr e o código de saída do processo.
"""
import os
import subprocess
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
EXEMPLOS = RAIZ / "exemplos"


def rodar_cli(*argumentos):
    """Executa `python -m src <argumentos>` na raiz do repositório."""
    return subprocess.run(
        [sys.executable, "-m", "src", *argumentos],
        cwd=RAIZ,
        capture_output=True,
        text=True,
        encoding="utf-8",
        timeout=30,
        # Garante UTF-8 nos acentos ("Saída", "léxico") em qualquer sistema.
        env={**os.environ, "PYTHONIOENCODING": "utf-8"},
    )


SAIDA_PROGRAMA_VALIDO = ["30", "10", "9", "8", "7", "6", "5", "4", "3", "2", "1", "0"]


def test_programa_valido_executa_com_codigo_0():
    r = rodar_cli(str(EXEMPLOS / "programa_valido.ml"))
    assert r.returncode == 0, r.stderr
    assert r.stdout.splitlines() == SAIDA_PROGRAMA_VALIDO
    assert r.stderr == ""


def test_programa_invalido_sai_com_codigo_1_e_erro_sintatico():
    r = rodar_cli(str(EXEMPLOS / "programa_invalido.ml"))
    assert r.returncode == 1
    assert "[Erro sintático] linha 6" in r.stderr
    assert "Traceback" not in r.stderr
    # A linha do código é mostrada com o marcador ^.
    assert "for (i = 0; i < 10) {" in r.stderr
    assert "^" in r.stderr
    # Nada do programa é executado quando a análise sintática falha.
    assert r.stdout == ""


def test_flag_tokens_mostra_tabela_antes_da_saida():
    r = rodar_cli(str(EXEMPLOS / "programa_valido.ml"), "--tokens")
    assert r.returncode == 0, r.stderr
    saida = r.stdout
    assert "=== Tokens ===" in saida
    assert "TIPO" in saida and "LEXEMA" in saida and "LINHA:COLUNA" in saida
    # Primeiro comando do arquivo: x = 10; na linha 3.
    assert any(l.split()[:3] == ["IDENT", "x", "3:1"] for l in saida.splitlines() if l.strip())
    assert "EOF" in saida
    # A tabela vem antes da saída do programa.
    assert saida.index("=== Tokens ===") < saida.index("=== Saída ===")
    assert saida.split("=== Saída ===")[1].split() == SAIDA_PROGRAMA_VALIDO


def test_flag_ast_mostra_arvore_antes_da_saida():
    r = rodar_cli(str(EXEMPLOS / "programa_valido.ml"), "--ast")
    assert r.returncode == 0, r.stderr
    saida = r.stdout
    assert "=== AST ===" in saida
    assert "Program" in saida and "For" in saida and "While" in saida
    assert saida.index("=== AST ===") < saida.index("=== Saída ===")
    assert saida.split("=== Saída ===")[1].split() == SAIDA_PROGRAMA_VALIDO


def test_flags_tokens_e_ast_juntas():
    r = rodar_cli(str(EXEMPLOS / "programa_valido.ml"), "--tokens", "--ast")
    assert r.returncode == 0, r.stderr
    s = r.stdout
    assert s.index("=== Tokens ===") < s.index("=== AST ===") < s.index("=== Saída ===")


def test_arquivo_inexistente_sai_com_codigo_2():
    r = rodar_cli("nao_existe.ml")
    assert r.returncode == 2
    assert "arquivo não encontrado" in r.stderr
    assert "nao_existe.ml" in r.stderr
    assert "Traceback" not in r.stderr


def test_erro_semantico_sai_com_codigo_1_e_preserva_saida_anterior(tmp_path):
    programa = tmp_path / "div.ml"
    programa.write_text("print(1);\nx = 10 / 0;\n", encoding="utf-8")
    r = rodar_cli(str(programa))
    assert r.returncode == 1
    assert r.stdout.splitlines() == ["1"]
    assert "[Erro semântico] linha 2" in r.stderr
    assert "Traceback" not in r.stderr


def test_erro_lexico_sai_com_codigo_1(tmp_path):
    programa = tmp_path / "lex.ml"
    programa.write_text("x = 10;\ny = x @ 2;\n", encoding="utf-8")
    r = rodar_cli(str(programa))
    assert r.returncode == 1
    assert "[Erro léxico] linha 2, coluna 7" in r.stderr
    # O ^ fica embaixo do @ (coluna 7).
    linhas = r.stderr.splitlines()
    i = next(k for k, l in enumerate(linhas) if l.endswith("y = x @ 2;"))
    assert linhas[i + 1].index("^") == linhas[i].index("@")


def test_max_iter_interrompe_laco_infinito(tmp_path):
    programa = tmp_path / "loop.ml"
    programa.write_text("while (true) { }\n", encoding="utf-8")
    r = rodar_cli(str(programa), "--max-iter", "50")
    assert r.returncode == 1
    assert "[Erro semântico]" in r.stderr
    assert "Traceback" not in r.stderr
