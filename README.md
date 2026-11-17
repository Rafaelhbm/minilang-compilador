# MiniLang — compilador-intérprete didático

Projeto da II Avaliação de **Linguagens Formais e Compiladores** (Unit, Ciência da Computação,
Prof.ª Layse Santos Souza). Implementa lexer, parser descendente recursivo, AST e
interpretador para a linguagem MiniLang.

## Integrantes

- _Nome 1_ — _matrícula_
- _Nome 2_ — _matrícula_
- _Nome 3_ — _matrícula_

## Como executar

Requisito: Python 3.9 ou mais novo.

```bash
python3 -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt

python -m src exemplos/programa_valido.ml
python -m src exemplos/programa_invalido.ml
```

## Testes

```bash
pytest
```

## Declaração de uso de IA

Usamos **Claude Code** (Anthropic; modelos Claude Opus 5.5 e Claude Fable 5.2) como copiloto.
Detalhes por etapa em [declaracao_IA.md](declaracao_IA.md) e no
[diário de bordo](docs/diario_de_bordo.md).

## Estrutura

```
docs/        gramática, relatório, diário de bordo, vídeo
exemplos/    programas .ml de demonstração
src/         lexer, parser, AST, interpretador
tests/       validos/ e invalidos/
```
