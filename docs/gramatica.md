# Definição formal da MiniLang

Este documento é a referência única da linguagem. Lexer, parser, AST e interpretador
seguem exatamente o que está aqui; qualquer mudança na linguagem começa por este arquivo.

## 1. Alfabeto (tokens)

O alfabeto de entrada Σ do lexer é o conjunto de caracteres ASCII imprimíveis mais
espaço, tabulação, `\r` e `\n`. O alfabeto da gramática (símbolos terminais) é o
conjunto de **tokens** produzidos pelo lexer:

| Categoria | Tokens |
|---|---|
| Literais | `INT` (ex.: `42`), `TRUE` (`true`), `FALSE` (`false`) |
| Identificador | `IDENT` (ex.: `x`, `soma`, `_tmp1`) |
| Palavras reservadas | `IF` `ELSE` `WHILE` `FOR` `PRINT` |
| Aritméticos | `PLUS` `+` · `MINUS` `-` · `STAR` `*` · `SLASH` `/` |
| Comparação | `LT` `<` · `GT` `>` · `LE` `<=` · `GE` `>=` · `EQ` `==` · `NE` `!=` |
| Atribuição | `ASSIGN` `=` |
| Delimitadores | `LPAREN` `(` · `RPAREN` `)` · `LBRACE` `{` · `RBRACE` `}` · `SEMI` `;` |
| Fim de entrada | `EOF` |

Descartados pelo lexer (não viram tokens): espaços em branco, comentários de linha
`// ...` até o fim da linha e, como extensão, comentários de bloco `/* ... */`
(não aninhados). Um `/*` sem o `*/` correspondente é **erro léxico**.

Expressões regulares de cada token e a tabela de transições do autômato estão na
seção [Lexer](#lexer).

## 2. Gramática EBNF

Notação: `{ X }` = zero ou mais repetições, `[ X ]` = opcional, `( A | B )` = alternativa,
terminais entre aspas ou em MAIÚSCULAS (nome do token).

```ebnf
programa        = { comando } EOF ;

comando         = atribuicao_cmd
                | print_cmd
                | if_cmd
                | while_cmd
                | for_cmd
                | bloco ;

atribuicao_cmd  = atribuicao ";" ;
atribuicao      = IDENT "=" expressao ;
print_cmd       = "print" "(" expressao ")" ";" ;
if_cmd          = "if" "(" expressao ")" bloco [ "else" ( bloco | if_cmd ) ] ;
while_cmd       = "while" "(" expressao ")" bloco ;
for_cmd         = "for" "(" atribuicao ";" expressao ";" atribuicao ")" bloco ;
bloco           = "{" { comando } "}" ;

(* expressões: um nível de não-terminal por nível de precedência,
   do menos prioritário (topo) para o mais prioritário (base) *)
expressao       = igualdade ;
igualdade       = relacional [ ( "==" | "!=" ) relacional ] ;
relacional      = aditiva [ ( "<" | ">" | "<=" | ">=" ) aditiva ] ;
aditiva         = multiplicativa { ( "+" | "-" ) multiplicativa } ;
multiplicativa  = unaria { ( "*" | "/" ) unaria } ;
unaria          = "-" unaria | primaria ;
primaria        = INT | "true" | "false" | IDENT | "(" expressao ")" ;
```

Observações de projeto:

- As três cláusulas do `for` são obrigatórias (`atribuicao ";" expressao ";" atribuicao`):
  não existe produção que derive cláusula vazia, então `for (i = 0; i < 10) { }` não
  pertence à linguagem.
- O corpo de `if`, `else`, `while` e `for` é sempre um `bloco` com chaves. Isso elimina
  a ambiguidade do *dangling else* sem regra extra.
- Atribuição é **comando**, não expressão: `x = y = 1;` e `print(x = 1);` são inválidos.
- A gramática é LL(1): em cada ponto de escolha, o próximo token decide a produção
  (`IDENT` → atribuição, `print`/`if`/`while`/`for`/`{` → o comando correspondente).

## 3. Precedência e associatividade

Da **maior** para a **menor** precedência:

| Nível | Operadores | Associatividade | Não-terminal |
|---|---|---|---|
| 1 | `( )` agrupamento | — | `primaria` |
| 2 | `-` unário | à direita (prefixo) | `unaria` |
| 3 | `*` `/` | à esquerda | `multiplicativa` |
| 4 | `+` `-` binários | à esquerda | `aditiva` |
| 5 | `<` `>` `<=` `>=` | não associativo | `relacional` |
| 6 | `==` `!=` | não associativo | `igualdade` |

- **Precedência**: quanto mais "fundo" o não-terminal na cadeia
  `igualdade → relacional → aditiva → multiplicativa → unaria → primaria`, maior a
  precedência. Em `1 + 2 * 3`, o `*` só pode aparecer dentro de `multiplicativa`, que
  é filho de `aditiva`, logo é avaliado primeiro.
- **Associatividade à esquerda** (`+ - * /`): a repetição `{ op operando }` é construída
  como laço que dobra para a esquerda, então `10 - 3 - 2` = `(10 - 3) - 2` = 5.
- **Não associativo** (comparações): o `[ op operando ]` permite no máximo um operador
  por nível, então `1 < 2 < 3` é **erro sintático**; para comparar resultados use
  parênteses: `(1 < 2) == true`.

## 4. Regras semânticas (tipos)

Tipos: `int` e `bool`. Não há conversão implícita entre eles.

| Construção | Exige | Resultado |
|---|---|---|
| `a + b`, `a - b`, `a * b` | `int`, `int` | `int` |
| `a / b` | `int`, `int`, `b ≠ 0` | `int` (divisão inteira **truncada em direção a zero**: `-7 / 2 = -3`) |
| `-a` | `int` | `int` |
| `a < b`, `>`, `<=`, `>=` | `int`, `int` | `bool` |
| `a == b`, `a != b` | mesmo tipo | `bool` |
| condição de `if` / `while` / `for` | `bool` | — |
| uso de variável `x` | `x` já atribuída | tipo de `x` |
| `x = e` | se `x` já existe, `e` tem o mesmo tipo de `x` | — |
| `print(e)` | qualquer tipo | imprime `42`, `true` ou `false` |

Tabela de símbolos única (sem escopo aninhado: blocos não criam escopo). O tipo de uma
variável é fixado na primeira atribuição.

## 5. Programas de exemplo

### Exemplo 1 — válido

```
// soma dos números de 0 a 4 e contagem regressiva
x = 3;
soma = 0;
for (i = 0; i < 5; i = i + 1) {
    soma = soma + i;
}
while (x > 0) {
    print(x);
    x = x - 1;
}
if (soma == 10) { print(true); } else { print(false); }
```

**Justificativa:** todo comando deriva de `comando`; o `for` tem as três cláusulas exigidas
por `for_cmd`; as condições `i < 5`, `x > 0` e `soma == 10` são `bool`; toda variável é
atribuída antes do uso. Saída: `3`, `2`, `1`, `true`.

### Exemplo 2 — inválido (léxico)

```
x = 10;
y = x @ 2;
```

**Justificativa:** o caractere `@` não pertence a nenhuma expressão regular de token; o
autômato do lexer não tem transição a partir do estado inicial com `@`, então a entrada é
rejeitada na **análise léxica** (linha 2, coluna 7) antes de qualquer análise sintática.

### Exemplo 3 — inválido (sintático, laço mal formado)

```
soma = 0;
for (i = 0; i < 10) {
    soma = soma + i;
}
```

**Justificativa:** `for_cmd` exige `atribuicao ";" expressao ";" atribuicao`. Depois de
`i < 10` o parser espera `;` e encontra `)`. Não há derivação de `programa` que gere essa
sequência de tokens, logo a cadeia não pertence a L(MiniLang). Erro na **análise sintática**.

### Exemplo 4 — inválido (sintático, expressão incompleta)

```
x = (1 + ;
```

**Justificativa:** após `+`, `aditiva` exige uma `multiplicativa`, que por sua vez começa
em `primaria` (`INT`, `true`, `false`, `IDENT` ou `(`). O token `;` não está em
FIRST(`primaria`), então a derivação falha. Erro na **análise sintática**.

### Exemplo 5 — inválido (semântico, laço com condição não booleana)

```
x = 5;
while (x) {
    x = x - 1;
}
```

**Justificativa:** sintaticamente correto (`while "(" expressao ")" bloco`, e `x` é uma
`expressao`). Porém a regra semântica da seção 4 exige condição do tipo `bool`, e `x` é
`int`. A MiniLang não tem conversão implícita de inteiro para booleano, então o programa é
rejeitado na **análise semântica** com erro de tipo incompatível.

## Lexer

Implementação: `src/lexer.py`. O código é a transcrição direta do autômato desta seção:
os nomes de estados e classes de caracteres são os mesmos, e cada célula da tabela de
transições é uma entrada do dicionário `TRANSICOES`. A justificativa formal (expressões
regulares → AFN → AFD → código) está em `docs/relatorio/02_analise_lexica.md`.

### Tabela de tokens

Notação das expressões regulares: `[a-z]` classe de caracteres, `*` zero ou mais,
`+` uma ou mais, `|` alternativa, `.` qualquer caractere, `[^x]` qualquer caractere
exceto `x`. Abreviações: `L = [A-Za-z]` (letras ASCII), `D = [0-9]`.

| Tipo | Padrão (expressão regular) | Exemplo |
|---|---|---|
| `INT` | `D+` | `42`, `007` (valor 7) |
| `IDENT` | `(L \| _)(L \| D \| _)*`, exceto as palavras reservadas | `x`, `soma`, `_tmp1`, `whilex` |
| `TRUE` | `true` | `true` |
| `FALSE` | `false` | `false` |
| `IF` | `if` | `if` |
| `ELSE` | `else` | `else` |
| `WHILE` | `while` | `while` |
| `FOR` | `for` | `for` |
| `PRINT` | `print` | `print` |
| `PLUS` | `\+` | `+` |
| `MINUS` | `-` | `-` |
| `STAR` | `\*` | `*` |
| `SLASH` | `/` | `/` |
| `ASSIGN` | `=` | `=` |
| `EQ` | `==` | `==` |
| `NE` | `!=` | `!=` |
| `LT` | `<` | `<` |
| `GT` | `>` | `>` |
| `LE` | `<=` | `<=` |
| `GE` | `>=` | `>=` |
| `LPAREN` | `\(` | `(` |
| `RPAREN` | `\)` | `)` |
| `LBRACE` | `\{` | `{` |
| `RBRACE` | `\}` | `}` |
| `SEMI` | `;` | `;` |
| `EOF` | (fim da entrada) | — |
| *descartado:* espaço | `( \| \t \| \r \| \n)+` | `"  \n\t"` |
| *descartado:* comentário de linha | `//[^\n]*` | `// soma` |
| *descartado:* comentário de bloco | `/\*([^*] \| \*+[^*/])*\*+/` | `/* a * b */` |

Atributos dos tokens: `INT` tem `value` = inteiro; `TRUE`/`FALSE` têm `value` = `True`/
`False`; os demais têm `value = None`. `line` e `col` são a posição do **primeiro**
caractere do lexema, a partir de 1; tabulação conta como 1 coluna. O último token é
sempre `EOF`, posicionado logo depois do último caractere.

### Classes de caracteres (colunas da tabela)

| Classe | Caracteres |
|---|---|
| letra | `a`–`z`, `A`–`Z` (somente ASCII; `ç`, `á` etc. são "outro") |
| dígito | `0`–`9` |
| `_ = ! < > / * + -` | cada um é a sua própria classe |
| `( ) { } ;` | cada um é a sua própria classe; agrupados numa coluna só para a tabela caber |
| espaço/tab | espaço, `\t`, `\r` |
| `\n` | quebra de linha |
| outro | qualquer outro caractere (`@`, `#`, `$`, `&`, `ç`, ...) |

### Estados do AFD

Estado inicial: `INICIAL`. Estados de aceitação aparecem *em itálico* na tabela.

| Estado | Aceita? | Significado (o que já foi lido no lexema atual) |
|---|---|---|
| `INICIAL` | não | nada; o próximo caractere decide qual token começa |
| `EM_IDENT` | `IDENT` (ou palavra reservada) | `(L\|_)(L\|D\|_)*` |
| `EM_INT` | `INT` | `D+` |
| `NUM_MAL_FORMADO` | não (erro) | `D+(L\|_)(L\|D\|_)*`, ex.: `1x`, `12ab` |
| `EM_ATRIB` | `ASSIGN` | `=` |
| `EM_EQ` | `EQ` | `==` |
| `EM_EXCL` | não (erro se parar aqui) | `!` |
| `EM_NE` | `NE` | `!=` |
| `EM_LT` / `EM_LE` | `LT` / `LE` | `<` / `<=` |
| `EM_GT` / `EM_GE` | `GT` / `GE` | `>` / `>=` |
| `EM_BARRA` | `SLASH` | `/` |
| `EM_MAIS`, `EM_MENOS`, `EM_ASTERISCO` | `PLUS`, `MINUS`, `STAR` | `+`, `-`, `*` |
| `EM_LPAREN`, `EM_RPAREN`, `EM_LBRACE`, `EM_RBRACE`, `EM_SEMI` | o delimitador correspondente | `(`, `)`, `{`, `}`, `;` |
| `EM_ESPACO` | descarta | um ou mais espaços, tabs, `\r`, `\n` |
| `COMENT_LINHA` | descarta | `//` seguido de qualquer coisa exceto `\n` |
| `COMENT_BLOCO` | não (erro se a entrada acabar) | `/*` e o conteúdo, sem `*` pendente |
| `COMENT_BLOCO_ESTRELA` | não (erro se a entrada acabar) | dentro do bloco, o último caractere lido foi `*` |
| `COMENT_BLOCO_FIM` | descarta | o comentário de bloco inteiro, até `*/` |

### Tabela de transições

Linhas = estados, colunas = classes de caracteres. "—" = não há transição.

| Estado | letra | dígito | `_` | `=` | `!` | `<` | `>` | `/` | `*` | `+` | `-` | `( ) { } ;` | espaço/tab | `\n` | outro |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| → INICIAL | EM_IDENT | EM_INT | EM_IDENT | EM_ATRIB | EM_EXCL | EM_LT | EM_GT | EM_BARRA | EM_ASTERISCO | EM_MAIS | EM_MENOS | ¹ | EM_ESPACO | EM_ESPACO | — |
| *EM_IDENT* | EM_IDENT | EM_IDENT | EM_IDENT | — | — | — | — | — | — | — | — | — | — | — | — |
| *EM_INT* | NUM_MAL_FORMADO | EM_INT | NUM_MAL_FORMADO | — | — | — | — | — | — | — | — | — | — | — | — |
| NUM_MAL_FORMADO | NUM_MAL_FORMADO | NUM_MAL_FORMADO | NUM_MAL_FORMADO | — | — | — | — | — | — | — | — | — | — | — | — |
| *EM_ATRIB* | — | — | — | EM_EQ | — | — | — | — | — | — | — | — | — | — | — |
| EM_EXCL | — | — | — | EM_NE | — | — | — | — | — | — | — | — | — | — | — |
| *EM_LT* | — | — | — | EM_LE | — | — | — | — | — | — | — | — | — | — | — |
| *EM_GT* | — | — | — | EM_GE | — | — | — | — | — | — | — | — | — | — | — |
| *EM_BARRA* | — | — | — | — | — | — | — | COMENT_LINHA | COMENT_BLOCO | — | — | — | — | — | — |
| *EM_ESPACO* | — | — | — | — | — | — | — | — | — | — | — | — | EM_ESPACO | EM_ESPACO | — |
| *COMENT_LINHA* | COMENT_LINHA | COMENT_LINHA | COMENT_LINHA | COMENT_LINHA | COMENT_LINHA | COMENT_LINHA | COMENT_LINHA | COMENT_LINHA | COMENT_LINHA | COMENT_LINHA | COMENT_LINHA | COMENT_LINHA | COMENT_LINHA | — | COMENT_LINHA |
| COMENT_BLOCO | COMENT_BLOCO | COMENT_BLOCO | COMENT_BLOCO | COMENT_BLOCO | COMENT_BLOCO | COMENT_BLOCO | COMENT_BLOCO | COMENT_BLOCO | COMENT_BLOCO_ESTRELA | COMENT_BLOCO | COMENT_BLOCO | COMENT_BLOCO | COMENT_BLOCO | COMENT_BLOCO | COMENT_BLOCO |
| COMENT_BLOCO_ESTRELA | COMENT_BLOCO | COMENT_BLOCO | COMENT_BLOCO | COMENT_BLOCO | COMENT_BLOCO | COMENT_BLOCO | COMENT_BLOCO | COMENT_BLOCO_FIM | COMENT_BLOCO_ESTRELA | COMENT_BLOCO | COMENT_BLOCO | COMENT_BLOCO | COMENT_BLOCO | COMENT_BLOCO | COMENT_BLOCO |
| *EM_EQ*, *EM_NE*, *EM_LE*, *EM_GE*, *EM_MAIS*, *EM_MENOS*, *EM_ASTERISCO*, *EM_LPAREN*, *EM_RPAREN*, *EM_LBRACE*, *EM_RBRACE*, *EM_SEMI*, *COMENT_BLOCO_FIM* ² | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — |

¹ A partir de `INICIAL`: `(` → `EM_LPAREN`, `)` → `EM_RPAREN`, `{` → `EM_LBRACE`,
`}` → `EM_RBRACE`, `;` → `EM_SEMI` (um estado por caractere; no código são cinco
colunas separadas).
² Estados distintos, agrupados numa linha porque nenhum deles tem transição de saída.
Não podem ser fundidos: cada um aceita um tipo de token diferente.

### Como o autômato é executado

Para cada lexema, o lexer parte de `INICIAL` e segue transições enquanto existir uma
para o próximo caractere. Quando não há transição (ou a entrada acabou):

- estado de aceitação → emite o token (ou descarta, para espaço e comentários) e volta
  a `INICIAL` no caractere seguinte;
- estado sem aceitação → erro léxico na posição de início do lexema:

| Parou em | Mensagem |
|---|---|
| `INICIAL` (caractere sem transição) | `caractere inválido '@'` |
| `EM_EXCL` | `caractere inválido '!' (o operador de diferença é '!=')` |
| `NUM_MAL_FORMADO` | `número mal formado '1x': identificadores não podem começar com dígito` |
| `COMENT_BLOCO` / `COMENT_BLOCO_ESTRELA` | `comentário de bloco não fechado` (posição do `/*`) |

**Maior casamento (maximal munch).** Como o autômato só para quando não há mais
transição, ele sempre consome o lexema mais longo possível: em `<=` ele passa por
`EM_LT` mas continua com `=` até `EM_LE`, produzindo um único `LE`, e não `LT` seguido de
`ASSIGN`. Pelo mesmo motivo `===` vira `EQ` e `ASSIGN`, e `x<=-1` vira
`IDENT LE MINUS INT`. O lexer **não retrocede** para um estado de aceitação anterior; é
isso que faz `1x` ser erro (o AFD vai de `EM_INT` para `NUM_MAL_FORMADO`) em vez de virar
`INT(1) IDENT(x)`.

**Palavras reservadas.** O AFD reconhece `if`, `while`, `true` etc. como `IDENT`
(estado `EM_IDENT`). Ao emitir o token, o lexema é consultado na tabela
`PALAVRAS_RESERVADAS`; se estiver lá, o tipo passa a ser o da palavra (`IF`, `WHILE`,
`TRUE`, ...). Isso dá o mesmo resultado que um AFD com um caminho de estados próprio para
cada palavra: como a consulta é feita sobre o lexema **completo** (já obtido por maior
casamento), `whilex`, `for_` e `iff` continuam sendo `IDENT`. A justificativa está no
relatório.
