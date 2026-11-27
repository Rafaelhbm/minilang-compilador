# MiniLang — compilador-intérprete didático

Projeto da II Avaliação de **Linguagens Formais e Compiladores** (Unit, Ciência da Computação,
Prof.ª Layse Santos Souza). Implementa lexer, parser descendente recursivo, AST e
interpretador para a linguagem MiniLang.

## Integrantes

- Rafael Henrique Barreto Martins
- David Carvalho
- Gabriel Lopes

## Como executar

Requisito: Python 3.10 ou mais novo.

```bash
python3 -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

Uso da CLI:

```
python -m src ARQUIVO.ml [--tokens] [--ast] [--max-iter N]
```

| Opção | O que faz |
|---|---|
| (nenhuma) | executa o programa e mostra só a saída dos `print` |
| `--tokens` | mostra a tabela de tokens gerada pelo lexer antes de executar |
| `--ast` | mostra a árvore sintática abstrata gerada pelo parser antes de executar |
| `--max-iter N` | limite de iterações por laço (padrão 100000); passar dele gera erro semântico |

Executar um programa:

```
$ python -m src exemplos/programa_valido.ml
30
10
9
...
1
0
```

Ver os tokens (programa `x = 2 * (3 + 1); print(x);`, saída encurtada):

```
$ python -m src ex.ml --tokens
=== Tokens ===
TIPO    LEXEMA  LINHA:COLUNA
------  ------  ------------
IDENT   x       1:1
ASSIGN  =       1:3
INT     2       1:5
STAR    *       1:7
...
EOF     -       3:1
(16 tokens)

=== Saída ===
8
```

`--ast` funciona do mesmo jeito, imprimindo a árvore indentada antes de `=== Saída ===`.
As duas opções podem ser usadas juntas.

Quando o programa tem erro, a mensagem vai para stderr com a linha do código e um `^`
na coluna do problema, e o processo termina com código 1:

```
$ python -m src exemplos/erros/lexico_1_caractere_invalido.ml
[Erro léxico] linha 4, coluna 7: caractere inválido '@'
  4 | y = x @ 2;
            ^
```

Códigos de saída: `0` sucesso, `1` erro da linguagem (léxico, sintático ou semântico),
`2` arquivo inexistente/ilegível ou argumentos inválidos. Há programas com erro de cada
categoria em [exemplos/erros/](exemplos/erros/) e o catálogo completo em
[docs/relatorio/06_catalogo_erros.md](docs/relatorio/06_catalogo_erros.md).

## Testes

```bash
pytest                       # suíte inteira
pytest tests/validos         # só programas e casos válidos
pytest tests/invalidos       # só casos de erro (léxico, sintático, semântico, laço infinito)
pytest tests/validos/test_lacos.py -v   # um arquivo, mostrando cada teste
```

Os testes também rodam no GitHub Actions (Python 3.10 e 3.12) a cada push, configurado em
[.github/workflows/tests.yml](.github/workflows/tests.yml).

## Arquitetura

O programa passa por três fases, cada uma em um módulo, e cada fase só conversa com a
seguinte pelo formato de dados entre elas:

```
código-fonte (.ml)
   │  src/lexer.py        análise léxica: autômato que agrupa caracteres em tokens
   ▼
lista de tokens
   │  src/parser.py       análise sintática: descendente recursivo, um método por regra da gramática
   ▼
AST (src/ast_nodes.py)
   │  src/interpreter.py  percorre a árvore, mantém a tabela de símbolos e faz as checagens semânticas
   ▼
saída do programa
```

- `src/errors.py`: hierarquia de erros (`LexicalError`, `MiniLangSyntaxError`,
  `SemanticError` e subclasses), todos com linha e coluna.
- `src/__main__.py`: a CLI, que encadeia as fases e mostra os resultados intermediários.
- `docs/gramatica.md`: definição formal da linguagem (tokens, EBNF, precedência, tipos).

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
