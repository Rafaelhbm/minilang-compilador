# Plano de sprints

Apresentação/arguição: **01/12/2026**. Vídeo: até **29/11/2026** (2 dias antes).

| Sprint | Período | Entregas | Itens do enunciado |
|---|---|---|---|
| 0 — Fundação | 17/11 | Repositório, gramática, contratos entre fases, exemplos | a |
| 1 — Núcleo do compilador | 17/11 – 20/11 | Lexer, parser, AST, interpretador, CLI, testes de cada fase | b, c, d, e |
| 2 — Erros e testes | 21/11 – 23/11 | Catálogo de erros, suíte de borda dos laços, laço infinito, CI | f, g |
| 3 — Relatório | 24/11 – 27/11 | relatorio.pdf (seções técnicas + 2–3 pág. da pesquisa sobre IA), diário, declaração de IA | a–g |
| 4 — Vídeo e arguição | 27/11 – 30/11 | apresentacao.mp4, ensaio da arguição (cada um explica qualquer fase) | h |

## Divisão do trabalho de implementação (Sprint 1)

| Frente | Arquivos | Agente |
|---|---|---|
| A — Lexer e autômato | src/lexer.py, docs/gramatica.md (seção Lexer), tests/*/test_lexer_*.py | Opus |
| B — Parser e AST | src/parser.py, src/ast_nodes.py (format_tree), tests/*/test_parser_*.py, tests/validos/test_ast.py | Fable |
| C — Interpretador e semântica | src/interpreter.py, tests/*/test_interpreter_*.py | Fable |
| D — CLI, laços e infraestrutura | src/__main__.py, tests/validos/test_lacos.py, tests/invalidos/test_laco_infinito.py, README, CI | Opus |

Cada frente também escreve sua seção do relatório em `docs/relatorio/`.

## Divisão sugerida para a arguição

Cada integrante deve saber explicar **todas** as fases, mas pode liderar uma:
- Integrante 1: lexer (expressões regulares → AFD) e catálogo de erros léxicos.
- Integrante 2: gramática, parser descendente recursivo, AST.
- Integrante 3: interpretador, tabela de símbolos, semântica dos laços.
