# Diário de bordo

Registro semanal do andamento, incluindo o uso de IA generativa (o que foi pedido, o que
foi aceito, o que foi reescrito e por quê).

## Semana 1 — 17/11/2026 a 23/11/2026

**Responsáveis:** Rafael Henrique Barreto Martins, David Carvalho, _terceiro integrante_

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
| Lexer guiado por AFD + tabela de transições | Código com 26 estados; tabela do documento gerada a partir do dicionário de transições do código | _revisar_ |
| Parser descendente recursivo com modo pânico | Uma função por não-terminal; mensagens "esperado X, encontrado Y" | _revisar_ |
| Interpretador e tabela de símbolos | Despacho por tipo de nó; verificação de tipos em tempo de execução | _revisar_ |
| CLI, testes de laço, catálogo de erros, CI | `python -m src` com `--tokens`/`--ast`; 306 testes passando | _revisar_ |

### Pontos em que a IA quase errou ou precisou de correção (material para o relatório)
Registrados a partir dos relatos dos agentes de IA; o grupo deve confirmar cada um lendo o código.

1. **`bool` é subclasse de `int` em Python.** Com `isinstance(v, int)`, a MiniLang aceitaria
   `true + 1`, `-true` e `1 == true`. O interpretador usa `type(v) is int`. Conceito: sistema de
   tipos da linguagem-objeto ≠ sistema de tipos da linguagem de implementação.
2. **Maximal munch com retrocesso transformaria `1x` em `INT(1) IDENT(x)`.** O lexer foi feito
   sem retrocesso e com um estado não final `NUM_MAL_FORMADO`, para que `1x` seja erro léxico.
   Conceito: AFD, estados de aceitação, regra do casamento mais longo.
3. **Sincronizar o modo pânico em qualquer identificador causa erros em cascata** (`print x;`
   gerava um segundo erro falso "esperado '='"). Solução: sincronizar só em `IDENT` seguido de `=`.
   Conceito: FIRST(comando) vs. tokens que também aparecem no meio de expressões.
4. **`;` dentro do cabeçalho do `for`** confundia a sincronização geral; foi criada uma
   recuperação local que pula até o `)` do cabeçalho. Conceito: tokens de sincronização dependem
   do contexto sintático.
5. **Recuperação sem progresso** (um `}` sobrando) levaria a laço infinito no parser; a
   recuperação agora garante consumir ao menos um token.
6. **Divisão inteira:** `//` do Python arredonda para baixo (`-7 // 2 == -4`); a MiniLang
   trunca em direção a zero (`-7 / 2 == -3`).
7. **Erro de contagem de linha** num comentário de exemplo de erro ("linha 5" quando era 4) e
   contagem errada de nós (15 em vez de 17) na árvore concreta do relatório — corrigidos.

### Limitação conhecida (decisão consciente)
- Verificação semântica dinâmica: `if (false) { x = 1 + true; }` não gera erro, porque o ramo
  nunca executa. Discutido em docs/relatorio/05_interpretador.md.

### Decisões técnicas
- Comparações não associativas (`1 < 2 < 3` é erro sintático) para não misturar `bool` com `int`.
- Divisão inteira truncada em direção a zero (como em C/Java), não `//` do Python (que arredonda para baixo).
- Comentários de bloco `/* */` como extensão, para que exista o erro "comentário não fechado".
- Tipo da variável fixado na primeira atribuição.

### Dificuldades / próximos passos
- _preencher_

## Semana 2 — 24/11/2026 a 30/11/2026

_preencher_
