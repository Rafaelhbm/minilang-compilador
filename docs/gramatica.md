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

> Seção a ser preenchida na Sprint 1 (tabela de tokens com tipo, padrão e exemplo; tabela
> de transições do autômato).
