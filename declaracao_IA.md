# Declaração de uso de IA generativa

Em conformidade com a Portaria CNPq nº 2.664/2026, declaramos que **utilizamos** ferramentas
de IA generativa neste projeto, como copiloto de desenvolvimento. Todo código, gramática e
texto gerado com apoio de IA foi revisado, testado e é explicável por todos os integrantes.

## (i) Ferramenta e modelo

| Ferramenta | Modelo / versão | Interface |
|---|---|---|
| Claude Code (Anthropic) | Claude Opus 5.5 (`claude-opus-5-5`) e Claude Fable 5.2 (`claude-fable-5-2`) | Extensão do VS Code |

## (ii) e (iii) Etapas e finalidade

| Etapa | Uso da IA | Finalidade |
|---|---|---|
| Planejamento | Leitura do enunciado e divisão em sprints | Organizar o cronograma de 4 semanas |
| Gramática (item a) | Rascunho da EBNF, tabela de precedência e exemplos | Ponto de partida revisado e ajustado pelo grupo |
| Lexer (item b) | Geração do código e da tabela de transições | Copiloto de implementação; revisão do autômato pelo grupo |
| Parser e AST (itens c, d) | Geração do parser descendente recursivo | Copiloto de implementação; verificação manual de precedência |
| Interpretador (item e) | Geração do interpretador e da tabela de símbolos | Copiloto de implementação; revisão da semântica |
| Testes (item g) | Sugestão de casos de borda | Ampliar a cobertura; resultados conferidos manualmente |
| Relatório | _a preencher pelo grupo_ | _a preencher_ |

O registro detalhado de cada uso (o que foi aceito, reescrito ou descartado) está em
[docs/diario_de_bordo.md](docs/diario_de_bordo.md) e a análise crítica em `docs/relatorio.pdf`.
