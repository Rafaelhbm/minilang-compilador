# Diário de bordo

Registro semanal do andamento, incluindo o uso de IA generativa (o que foi pedido, o que
foi aceito, o que foi reescrito e por quê).

## Semana 1 — 17/11/2026 a 23/11/2026

**Responsáveis:** _integrante 1_, _integrante 2_, _integrante 3_

### O que foi feito
- Leitura do enunciado e definição do plano de sprints (docs/PLANO.md).
- Estrutura do repositório conforme o enunciado.
- Gramática EBNF, tabela de precedência e 5 exemplos comentados (docs/gramatica.md).
- Contratos entre as fases: tipos de token, nós da AST, hierarquia de erros e API do
  interpretador.

### Uso de IA
| Pedido à IA | Resultado | Decisão do grupo |
|---|---|---|
| Ler o enunciado e propor sprints | Plano em 5 sprints | Aceito com ajustes de datas |
| Rascunho da EBNF com precedência | Gramática LL(1) com um não-terminal por nível | _revisar: aceito / reescrito?_ |

### Decisões técnicas
- Comparações não associativas (`1 < 2 < 3` é erro sintático) para não misturar `bool` com `int`.
- Divisão inteira truncada em direção a zero (como em C/Java), não `//` do Python (que arredonda para baixo).
- Comentários de bloco `/* */` como extensão, para que exista o erro "comentário não fechado".
- Tipo da variável fixado na primeira atribuição.

### Dificuldades / próximos passos
- _preencher_

## Semana 2 — 24/11/2026 a 30/11/2026

_preencher_
