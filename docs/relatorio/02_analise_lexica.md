# Análise léxica

O analisador léxico (`src/lexer.py`) transforma a sequência de caracteres do programa em
uma sequência de tokens, descartando espaços e comentários. Esta seção mostra que ele
reconhece **exatamente** os tokens definidos em `docs/gramatica.md`: nem mais, nem menos.
O argumento segue o caminho clássico da teoria de linguagens formais:

> expressões regulares → união → AFN (Thompson) → AFD (subconjuntos) → AFD mínimo → código

## 1. Expressões regulares de cada token

Com `L = [A-Za-z]` e `D = [0-9]`, cada classe de token tem uma expressão regular rᵢ
(tabela completa na seção "Lexer" da gramática):

| i | Token | rᵢ |
|---|---|---|
| 1 | `INT` | `D+` |
| 2 | `IDENT` | `(L\|_)(L\|D\|_)*` |
| 3–9 | palavras reservadas | `if`, `else`, `while`, `for`, `print`, `true`, `false` |
| 10–25 | operadores e delimitadores | `+`, `-`, `*`, `/`, `=`, `==`, `!=`, `<`, `>`, `<=`, `>=`, `(`, `)`, `{`, `}`, `;` |
| 26 | espaço (descartado) | `( \|\t\|\r\|\n)+` |
| 27 | comentário de linha (descartado) | `//[^\n]*` |
| 28 | comentário de bloco (descartado) | `/\*([^*]\|\*+[^*/])*\*+/` |

O conjunto de lexemas válidos é a **união** R = r₁ | r₂ | … | r₂₈. Como linguagens
regulares são fechadas sob união, L(R) é regular e existe um autômato finito que a
reconhece. Uma entrada válida é um elemento de L(R)\*: uma concatenação de lexemas.

## 2. Do AFN ao AFD mínimo

**Thompson.** Cada rᵢ vira um AFN-ε Nᵢ com um único estado final fᵢ, rotulado com o token
i. Um novo estado inicial s₀ recebe transições ε para o início de cada Nᵢ. O AFN
resultante N reconhece L(R), e cada estado final continua marcado com o seu token.

**Construção de subconjuntos.** Cada estado do AFD D é o conjunto de estados de N
alcançáveis depois de ler um prefixo (fecho-ε). Um estado de D é de aceitação se contém
algum fᵢ, e o token associado é o de **maior prioridade** entre os fᵢ presentes (regra
explicada na seção 3).

**Minimização.** Na minimização por partições, a partição inicial não é apenas
{aceitação, não aceitação}: os estados de aceitação são separados **por token**, porque
dois estados que aceitam tokens diferentes nunca são equivalentes para o lexer. Por isso
`EM_EQ`, `EM_LE`, `EM_MAIS`, `EM_SEMI` etc. continuam distintos, mesmo que nenhum deles
tenha transição de saída. Depois de refinar as partições e agrupar os caracteres que se
comportam igual em todos os estados (as classes de caracteres: letra, dígito, …), chega-se
à tabela de transições da gramática. O código é essa tabela: cada estado é uma constante
com o mesmo nome e cada célula é uma entrada do dicionário `TRANSICOES`.

### Exemplo 1: `<` versus `<=`

r(LT) = `<` e r(LE) = `<=`. Os AFNs de Thompson são
`s → a₁ –<→ f_LT` e `s → b₁ –<→ b₂ –=→ f_LE`. Na construção de subconjuntos:

| Estado do AFD | Conjunto de estados do AFN | Aceita | Com `=` vai para |
|---|---|---|---|
| `INICIAL` | {s, a₁, b₁, … } | — | — |
| `EM_LT` | {f_LT, b₂} | `LT` | `EM_LE` |
| `EM_LE` | {f_LE} | `LE` | — |

Depois de ler `<`, o AFD está ao mesmo tempo "no fim de `LT`" e "no meio de `LE`". Se o
próximo caractere é `=`, a transição existe e o lexer segue para `EM_LE`; caso contrário
para em `EM_LT` e emite `LT`. É assim que `x<=-1` vira `IDENT LE MINUS INT`.

### Exemplo 2: `INT` versus `1x`

A linguagem decide que um número colado a uma letra é erro (e não `INT` seguido de
`IDENT`). Isso é modelado com um estado extra, sem aceitação, alcançado a partir de
`EM_INT`:

```
          D                L | _             L | D | _
INICIAL ─────▶ EM_INT ─────────────▶ NUM_MAL_FORMADO ◀──┐
              ▲  │ D                        └───────────┘
              └──┘
```

`EM_INT` aceita `D+`. Lendo `1x`: `INICIAL –1→ EM_INT –x→ NUM_MAL_FORMADO`; não há mais
caracteres, o estado não é de aceitação → erro léxico "número mal formado '1x'" na coluna
do `1`. Lendo `12+`: `EM_INT` não tem transição com `+`, então emite `INT(12)` e começa um
novo lexema no `+`.

## 3. Justificativa de correção

**(i) Cada estado de aceitação corresponde a uma classe de token.** O dicionário
`ACEITACAO` associa cada estado de aceitação a exatamente um tipo de token (ou a
"descartar"). Pela construção acima, o AFD termina em um estado de aceitação do token t
após ler w se, e somente se, w ∈ L(r_t) e nenhum token de prioridade maior casa w. Por
exemplo, `EM_IDENT` é alcançado exatamente pelas cadeias de `(L|_)(L|D|_)*`.

**(ii) Ambiguidades são resolvidas por duas regras.**

1. *Maior casamento (maximal munch).* O lexer segue transições até não existir nenhuma; o
   lexema emitido é, portanto, o mais longo que o AFD consegue ler. Assim `<=`, `==` e `!=`
   são um token só, e `whilex` é um único `IDENT`, não `WHILE` seguido de `IDENT(x)`. O
   lexer não retrocede para um estado de aceitação anterior: para todos os tokens da
   MiniLang, parar num estado sem aceitação só acontece em entradas que a linguagem
   considera erradas (`!` isolado, `1x`, `/*` sem fim), então o retrocesso nunca é
   necessário para uma entrada válida.
2. *Prioridade das palavras reservadas.* A cadeia `while` pertence a L(r_WHILE) e a
   L(r_IDENT). No AFD obtido pela construção de subconjuntos haveria um caminho
   `w → h → i → l → e` cujo último estado contém os finais de `WHILE` e de `IDENT`; a regra
   de prioridade o rotula como `WHILE`. Os estados intermediários (`w`, `wh`, …) e os que
   saem do caminho (`whilex`, `wh_`) só contêm o final de `IDENT`. A implementação colapsa
   todos esses caminhos no estado `EM_IDENT` e, ao emitir, consulta o lexema na tabela
   `PALAVRAS_RESERVADAS`. É equivalente porque o rótulo de aceitação do estado final
   depende apenas da cadeia lida, e a consulta é feita sobre essa mesma cadeia. A vantagem
   é ter um estado em vez de cerca de 25, e acrescentar uma palavra reservada sem mexer no
   autômato.

**(iii) Toda entrada é particionada em tokens ou rejeitada na posição exata.** O laço
principal recomeça em `INICIAL` na posição seguinte ao fim de cada lexema, e cada
iteração consome pelo menos um caractere ou lança erro (de `INICIAL` só se fica parado se
o caractere não tem transição, o que é o erro "caractere inválido"). Logo o laço termina
e os lexemas emitidos cobrem a entrada inteira, sem sobreposição e sem lacunas. Quando o
AFD para em um estado sem aceitação, o erro é lançado com a linha e coluna guardadas no
**início do lexema**: `@` em `y = x @ 2;` é reportado na coluna 7, e um `/*` sem `*/`
aponta para onde o comentário abriu, não para o fim do arquivo. Linha e coluna são
atualizadas a cada caractere consumido (`\n` incrementa a linha e volta a coluna para 1;
qualquer outro caractere, inclusive tab, soma 1 à coluna).

## 4. Validação

Os testes `tests/validos/test_lexer_valido.py` e `tests/invalidos/test_lexer_invalido.py`
exercitam cada linha da tabela de transições: todos os tipos de token, identificadores
parecidos com palavras reservadas (`whilex`, `for_`, `iff`), maior casamento (`<=`,
`===`, `x<=-1`), as variações de fechamento de comentário de bloco (`/**/`, `/***/`,
`/*/ */`), e cada estado de erro (`@`, `#`, `ç`, `!`, `1x`, `12ab`, `/*` sem fim), sempre
conferindo linha e coluna.
