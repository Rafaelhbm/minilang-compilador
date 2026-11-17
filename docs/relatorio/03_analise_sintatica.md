# 3. Análise sintática

Código: `src/parser.py`. Testes: `tests/validos/test_parser_valido.py`,
`tests/invalidos/test_parser_invalido.py`, `tests/validos/test_ast.py`.

## 3.1 Técnica adotada

O parser é **descendente recursivo preditivo**, ou seja, um analisador **LL(1)** escrito à
mão: lê a entrada da esquerda para a direita (L), constrói uma derivação mais à esquerda
(L) e decide cada passo olhando **um** token à frente (1), o *lookahead*.

Cada não-terminal da EBNF de `docs/gramatica.md` vira uma função com o mesmo nome:

| Não-terminal | Função | Não-terminal | Função |
|---|---|---|---|
| `programa` | `programa()` | `expressao` | `expressao()` |
| `comando` | `comando()` | `igualdade` | `igualdade()` |
| `atribuicao_cmd` | `atribuicao_cmd()` | `relacional` | `relacional()` |
| `atribuicao` | `atribuicao()` | `aditiva` | `aditiva()` |
| `print_cmd` | `print_cmd()` | `multiplicativa` | `multiplicativa()` |
| `if_cmd` | `if_cmd()` | `unaria` | `unaria()` |
| `while_cmd` | `while_cmd()` | `primaria` | `primaria()` |
| `for_cmd` | `for_cmd()` | `bloco` | `bloco()` |

A tradução de cada construção da EBNF para código é mecânica:

| EBNF | Código |
|---|---|
| terminal `"x"` | `self.expect(T.X, contexto)`: consome o token ou lança erro |
| não-terminal `N` | chamada `self.N()` |
| `A \| B` | `if` sobre o token atual: vai para a alternativa cujo FIRST contém o token |
| `{ X }` | `while token atual ∈ FIRST(X): X` |
| `[ X ]` | `if token atual ∈ FIRST(X): X` |

Três funções auxiliares não correspondem a não-terminais: `condicao()` e
`clausulas_for()` são o trecho entre parênteses do cabeçalho de `if`/`while` e de `for`,
separados só para permitir a recuperação de erro local descrita na seção 3.6;
`lista_de_comandos()` é a repetição `{ comando }` usada por `programa` e por `bloco`.

### Por que a gramática é LL(1)

Uma gramática pode ser analisada por um parser preditivo de um token quando:

1. **não tem recursão à esquerda** (senão `A → A α` faria a função `A` chamar a si mesma
   sem consumir token, em laço infinito);
2. **não é ambígua**;
3. em cada ponto de escolha, os conjuntos FIRST das alternativas são **disjuntos**, e,
   onde uma alternativa pode ser vazia (`{ }` e `[ ]`), FIRST do que é opcional é
   **disjunto do FOLLOW** do ponto em que ele aparece.

A gramática da MiniLang atende às três:

1. Nenhuma produção começa pelo próprio não-terminal. As operações binárias, que numa
   gramática "de livro" seriam escritas como `aditiva → aditiva "+" multiplicativa`
   (recursão à esquerda), estão escritas com repetição: `aditiva = multiplicativa { "+"
   multiplicativa }`. A única recursão direta é `unaria = "-" unaria`, que é à direita
   (consome o `-` antes de chamar a si mesma).
2. Não há ambiguidade: a precedência está codificada em níveis de não-terminais (seção
   3.4), as comparações aceitam no máximo um operador por nível, e o corpo de `if`/`else`
   é sempre um bloco com chaves, o que elimina o *dangling else*.
3. Verificação abaixo.

#### Conjuntos FIRST

| Não-terminal | FIRST |
|---|---|
| `primaria` | `INT`, `true`, `false`, `IDENT`, `(` |
| `unaria` | `-`, `INT`, `true`, `false`, `IDENT`, `(` |
| `multiplicativa`, `aditiva`, `relacional`, `igualdade`, `expressao` | igual a FIRST(`unaria`) |
| `atribuicao`, `atribuicao_cmd` | `IDENT` |
| `print_cmd` | `print` |
| `if_cmd` | `if` |
| `while_cmd` | `while` |
| `for_cmd` | `for` |
| `bloco` | `{` |
| `comando` | `IDENT`, `print`, `if`, `while`, `for`, `{` |
| `programa` | FIRST(`comando`) ∪ { `EOF` } |

#### Conjuntos FOLLOW usados nas decisões

| Não-terminal | FOLLOW |
|---|---|
| `comando` | `IDENT`, `print`, `if`, `while`, `for`, `{`, `}`, `EOF` |
| `if_cmd` | igual a FOLLOW(`comando`) (note que **não** contém `else`) |
| `expressao`, `igualdade` | `)`, `;` |
| `relacional` | `==`, `!=`, `)`, `;` |
| `aditiva` | `<`, `>`, `<=`, `>=`, `==`, `!=`, `)`, `;` |
| `multiplicativa` | `+`, `-`, `<`, `>`, `<=`, `>=`, `==`, `!=`, `)`, `;` |
| `unaria` | `*`, `/`, `+`, `-`, `<`, `>`, `<=`, `>=`, `==`, `!=`, `)`, `;` |

#### Pontos de escolha

| Ponto | Alternativas e seus conjuntos | Disjuntos? |
|---|---|---|
| `comando` | atribuição {`IDENT`} · print {`print`} · if {`if`} · while {`while`} · for {`for`} · bloco {`{`} | sim, um token diferente por alternativa |
| `{ comando }` em `programa` | continuar: FIRST(`comando`) · parar: {`EOF`} | sim |
| `{ comando }` em `bloco` | continuar: FIRST(`comando`) · parar: {`}`} | sim |
| `[ "else" ... ]` | presente: {`else`} · ausente: FOLLOW(`if_cmd`) | sim, `else` ∉ FOLLOW(`if_cmd`) |
| `"else" ( bloco \| if_cmd )` | {`{`} · {`if`} | sim |
| `[ ("=="\|"!=") relacional ]` | {`==`, `!=`} · FOLLOW(`igualdade`) = {`)`, `;`} | sim |
| `[ ("<"\|...) aditiva ]` | {`<`, `>`, `<=`, `>=`} · FOLLOW(`relacional`) | sim |
| `{ ("+"\|"-") multiplicativa }` | {`+`, `-`} · FOLLOW(`aditiva`) | sim |
| `{ ("*"\|"/") unaria }` | {`*`, `/`} · FOLLOW(`multiplicativa`) | sim |
| `unaria` | {`-`} · FIRST(`primaria`) | sim |
| `primaria` | {`INT`} · {`true`} · {`false`} · {`IDENT`} · {`(`} | sim |

Um ponto que costuma gerar dúvida: o `-` aparece em FOLLOW(`multiplicativa`) (como
subtração) e em FIRST(`unaria`) (como menos unário). Isso não é conflito, porque esses
dois conjuntos nunca são comparados na mesma decisão. Em `3 - -1`, `aditiva` vê o
primeiro `-` depois de um operando e decide "continuar a repetição" (subtração); em seguida
chama `multiplicativa → unaria`, que vê o segundo `-` no início de um operando e decide
"menos unário".

## 3.2 Como `while` e `for` são tratados

Cada produção vira uma sequência de chamadas, na mesma ordem dos símbolos:

```
while_cmd = "while" "(" expressao ")" bloco ;
```

```python
def while_cmd(self):
    palavra = self.expect(T.WHILE, "")          # "while"
    condicao = self.cabecalho("while",          # "("  (consumido em cabecalho)
                              lambda: self.condicao("while"))  # expressao ")"
    corpo = self.bloco("do while")              # bloco
    return While(condicao, corpo, palavra.line, palavra.col)
```

```
for_cmd = "for" "(" atribuicao ";" expressao ";" atribuicao ")" bloco ;
```

```python
def for_cmd(self):
    palavra = self.expect(T.FOR, "")                         # "for"
    inicio, condicao, atualizacao = self.cabecalho("for", self.clausulas_for)
    corpo = self.bloco("do for")                             # bloco
    return For(inicio, condicao, atualizacao, corpo, palavra.line, palavra.col)

def clausulas_for(self):
    inicio = self.atribuicao("na inicialização do for ...")  # atribuicao
    self.expect(T.SEMI, "após a inicialização do for ...")   # ";"
    condicao = self.expressao()                              # expressao
    self.expect(T.SEMI, "após a condição do for ...")        # ";"
    atualizacao = self.atribuicao("na atualização do for ...")  # atribuicao
    self.expect(T.RPAREN, "após a atualização do for")       # ")"
    return inicio, condicao, atualizacao
```

As três cláusulas são obrigatórias porque não existe nenhum `if` que permita pulá-las:
cada `expect` exige o seu token, e `atribuicao()` exige começar por `IDENT`. Antes de
chamar `expressao()` para a condição, o código testa se o token está em FIRST(`expressao`);
isso não muda a linguagem reconhecida, só permite a mensagem "esperado expressão na
condição do for" em vez da mensagem genérica.

## 3.3 Árvores sintáticas concretas

A árvore sintática concreta (ou árvore de derivação) mostra **todos** os não-terminais
usados e **todos** os tokens, inclusive parênteses. Abaixo, as expressões são analisadas a
partir de `expressao`.

### `1 + 2 * 3`

```
expressao
└── igualdade
    └── relacional
        └── aditiva
            ├── multiplicativa
            │   └── unaria
            │       └── primaria
            │           └── INT 1
            ├── "+"
            └── multiplicativa
                ├── unaria
                │   └── primaria
                │       └── INT 2
                ├── "*"
                └── unaria
                    └── primaria
                        └── INT 3
```

### `(1 + 2) * 3`

```
expressao
└── igualdade
    └── relacional
        └── aditiva
            └── multiplicativa
                ├── unaria
                │   └── primaria
                │       ├── "("
                │       ├── expressao
                │       │   └── igualdade
                │       │       └── relacional
                │       │           └── aditiva
                │       │               ├── multiplicativa
                │       │               │   └── unaria
                │       │               │       └── primaria
                │       │               │           └── INT 1
                │       │               ├── "+"
                │       │               └── multiplicativa
                │       │                   └── unaria
                │       │                       └── primaria
                │       │                           └── INT 2
                │       └── ")"
                ├── "*"
                └── unaria
                    └── primaria
                        └── INT 3
```

### Por que as árvores diferem

Na primeira, o `+` é filho de `aditiva` e o `*` está dentro do segundo operando de
`aditiva` (um `multiplicativa`). Como o interpretador avalia os filhos antes do pai, `2 * 3`
é calculado primeiro: resultado 7.

Na segunda, o `+` não pode ficar acima do `*`, porque `multiplicativa` só gera operandos
`unaria`, e um `unaria` só contém `+` se passar por `primaria → "(" expressao ")"`. Os
parênteses obrigam a derivação a "subir" de novo até `expressao` dentro do primeiro
operando de `*`. Agora `1 + 2` está abaixo do `*` e é calculado primeiro: resultado 9.

### `while (x > 0) { x = x - 1; }`

Para encurtar, `N ⇒* t` indica uma cadeia de não-terminais unitários
(`aditiva → multiplicativa → unaria → primaria`) que termina no token `t`.

```
comando
└── while_cmd
    ├── "while"
    ├── "("
    ├── expressao
    │   └── igualdade
    │       └── relacional
    │           ├── aditiva ⇒* IDENT x
    │           ├── ">"
    │           └── aditiva ⇒* INT 0
    ├── ")"
    └── bloco
        ├── "{"
        ├── comando
        │   └── atribuicao_cmd
        │       ├── atribuicao
        │       │   ├── IDENT x
        │       │   ├── "="
        │       │   └── expressao ⇒ igualdade ⇒ relacional ⇒ aditiva
        │       │       ├── multiplicativa ⇒* IDENT x
        │       │       ├── "-"
        │       │       └── multiplicativa ⇒* INT 1
        │       └── ";"
        └── "}"
```

### `for (i = 0; i < 3; i = i + 1) { print(i); }`

```
comando
└── for_cmd
    ├── "for"
    ├── "("
    ├── atribuicao                      ← cláusula 1: inicialização
    │   ├── IDENT i
    │   ├── "="
    │   └── expressao ⇒* INT 0
    ├── ";"
    ├── expressao                       ← cláusula 2: condição
    │   └── igualdade
    │       └── relacional
    │           ├── aditiva ⇒* IDENT i
    │           ├── "<"
    │           └── aditiva ⇒* INT 3
    ├── ";"
    ├── atribuicao                      ← cláusula 3: atualização
    │   ├── IDENT i
    │   ├── "="
    │   └── expressao ⇒ igualdade ⇒ relacional ⇒ aditiva
    │       ├── multiplicativa ⇒* IDENT i
    │       ├── "+"
    │       └── multiplicativa ⇒* INT 1
    ├── ")"
    └── bloco
        ├── "{"
        ├── comando
        │   └── print_cmd
        │       ├── "print"
        │       ├── "("
        │       ├── expressao ⇒* IDENT i
        │       ├── ")"
        │       └── ";"
        └── "}"
```

## 3.4 Justificativa formal

### Precedência

Numere os níveis da cadeia `igualdade (6) → relacional (5) → aditiva (4) →
multiplicativa (3) → unaria (2) → primaria (1)`. Cada não-terminal de nível *k* só
introduz operadores do nível *k*, e seus operandos são do nível *k − 1*.

**Lema.** Na árvore gerada por um não-terminal de nível *k*, todo operador de nível maior
que *k* (menor precedência) está dentro de um par de parênteses.

*Prova por indução em k.* Base (*k* = 1, `primaria`): as alternativas são um token
isolado ou `"(" expressao ")"`; qualquer operador aparece dentro dos parênteses. Passo:
suponha válido para *k − 1*. Um não-terminal de nível *k* produz operandos de nível
*k − 1* separados por operadores de nível *k*. Pela hipótese, os operandos só contêm
operadores de nível maior que *k − 1* dentro de parênteses; os operadores de nível *k*
que ele mesmo introduz não são maiores que *k*. Logo, os de nível maior que *k* estão
todos entre parênteses. ∎

**Consequência.** Em `1 + 2 * 3`, o `*` (nível 3) não pode ser introduzido por `aditiva`
(nível 4), e um operando de `multiplicativa` não pode conter `+` sem parênteses. Então
a única árvore possível tem o nó `+` acima do nó `*`; como a avaliação é em pós-ordem
(filhos antes do pai), o operador de maior precedência é aplicado primeiro.

### Associatividade à esquerda

`aditiva` e `multiplicativa` são implementadas com laço:

```python
esquerda = self.multiplicativa()
while self.check(T.PLUS, T.MINUS):
    op = self.advance()
    direita = self.multiplicativa()
    esquerda = BinOp(op.lexeme, esquerda, direita)
```

**Invariante do laço:** no início de cada volta, depois de ler `o₁ op₁ o₂ … opₙ₋₁ oₙ`,
`esquerda` é a árvore `(…((o₁ op₁ o₂) op₂ o₃) … opₙ₋₁ oₙ)`. Vale antes da primeira volta
(`esquerda = o₁`). Se vale no início de uma volta, ao ler `opₙ oₙ₊₁` o novo `esquerda` é
`BinOp(opₙ, árvore anterior, oₙ₊₁)`, que tem a mesma forma com um termo a mais. Por
indução, ao sair do laço a árvore está agrupada à esquerda. Assim `10 - 3 - 2` vira
`(10 - 3) - 2 = 5`, e `8 / 4 / 2` vira `(8 / 4) / 2 = 1`.

Se a regra fosse escrita com recursão à direita (`aditiva = multiplicativa [ "+" aditiva ]`),
a mesma técnica produziria `10 - (3 - 2) = 9`, que está errado. Por isso a escolha é
o laço, e não a recursão.

O menos unário é o único caso em que a recursão à direita está correta: `- - 1` deve ser
`-(-(1))`, e `unaria = "-" unaria` produz exatamente isso.

### Não associatividade das comparações

`relacional = aditiva [ op_rel aditiva ]` usa `[ ]` (zero ou um), não `{ }`. Depois de
`1 < 2`, a parte opcional já foi usada; o próximo símbolo esperado está em
FOLLOW(`relacional`) = {`==`, `!=`, `)`, `;`}. O token `<` não está nesse conjunto, nem
em nenhum outro ponto de continuação, então `1 < 2 < 3` **não pertence à linguagem**. O
parser detecta isso exatamente nesse ponto e, em vez da mensagem genérica, informa
"operadores de comparação não são associativos; use parênteses". O mesmo vale para
`a == b == c` em `igualdade`. Comparações de níveis diferentes continuam válidas:
`a < b == c > d` é `(a < b) == (c > d)`.

### Reconhecimento de `while` e `for`

`while_cmd` e `for_cmd` são as únicas produções de `comando` que começam por `while` e
`for`, respectivamente; ao ver esses tokens, `comando()` chama a função correspondente,
que consome os símbolos da produção na ordem (seção 3.2). Uma entrada é aceita como
`while`/`for` se e somente se a sequência de `expect` e chamadas termina sem erro, o que
corresponde a existir uma derivação `comando ⇒ while_cmd ⇒* entrada` (ou `for_cmd`).
Como em cada passo só havia uma escolha possível (LL(1)), essa derivação é única.

### Rejeição dos exemplos 3 e 4 de `docs/gramatica.md`

**Exemplo 3** — `for (i = 0; i < 10) { soma = soma + i; }`

Derivação (mais à esquerda) até o ponto do erro; `•` marca a posição do parser:

```
comando ⇒ for_cmd
        ⇒ "for" "(" atribuicao ";" expressao ";" atribuicao ")" bloco
        ⇒* "for" "(" i = 0 ";" i < 10 • ";" atribuicao ")" bloco
```

Depois de `i < 10`, `relacional` já usou sua parte opcional e `expressao` termina (o
token `)` está em FOLLOW(`expressao`)). O próximo símbolo da forma sentencial é o terminal
`";"`, mas o token é `)`. Como o terminal não casa e não há outra alternativa para
`for_cmd`, não existe derivação de `programa` para essa entrada. Mensagem:

```
[Erro sintático] linha 2, coluna 19: esperado ';' após a condição do for
(o for exige inicialização; condição; atualização), encontrado ')'
```

(no arquivo `exemplos/programa_invalido.ml` o `for` está na linha 6, coluna 19.)

**Exemplo 4** — `x = (1 + ;`

```
comando ⇒ atribuicao_cmd ⇒ atribuicao ";" ⇒ IDENT "=" expressao ";"
        ⇒* x "=" "(" expressao ")" ";"
        ⇒* x "=" "(" multiplicativa "+" multiplicativa ")" ";"
        ⇒* x "=" "(" 1 "+" • multiplicativa ")" ";"
```

Depois do `+`, `aditiva` exige uma `multiplicativa`, cujo primeiro token deve estar em
FIRST(`multiplicativa`) = {`-`, `INT`, `true`, `false`, `IDENT`, `(`}. O token é `;`, que
não está no conjunto. Mensagem:

```
[Erro sintático] linha 1, coluna 10: esperado expressão após '+', encontrado ';'
```

## 3.5 Mensagens de erro

As mensagens seguem o formato "esperado X, encontrado Y", citando o contexto (qual
construção estava sendo analisada) e o lexema encontrado, ou "fim do arquivo". Exemplos
reais (todos cobertos por testes):

| Entrada | Mensagem |
|---|---|
| `for (i = 0; i < 10) { }` | esperado ';' após a condição do for (o for exige inicialização; condição; atualização), encontrado ')' |
| `for (; i < 10; i = i + 1) { }` | esperado identificador na inicialização do for (...), encontrado ';' |
| `x = (1 + ;` | esperado expressão após '+', encontrado ';' |
| `x = 1 < 2 < 3;` | operadores de comparação não são associativos; use parênteses, ex.: (a < b) == c (...) |
| `while x > 0 { }` | esperado '(' após 'while', encontrado 'x' |
| `while (x > 0) { x = 1;` | esperado '}' para fechar o bloco aberto na linha 1, encontrado fim do arquivo |
| `x = y = 1;` | esperado ';' após a atribuição, encontrado '=' (atribuição é comando, não expressão; ...) |
| `if (x > 0) print(x);` | esperado '{' para abrir o corpo do if (o corpo deve estar entre chaves), encontrado 'print' |
| `else { }` | 'else' sem 'if' correspondente (o 'else' deve vir logo depois do bloco do if) |

## 3.6 Recuperação de erros: modo pânico

Parar no primeiro erro obriga o programador a corrigir um erro por vez. Com recuperação,
o parser reporta vários erros numa única execução. Ao final, se houve algum erro, é
lançado um `MiniLangSyntaxError` cuja mensagem é a do primeiro erro e cujo atributo
`errors` contém a lista completa.

**Funcionamento.**

1. Ao encontrar um token inesperado, o parser registra o diagnóstico (função `error`) e
   lança uma exceção, que desfaz as chamadas recursivas da expressão ou comando em
   andamento.
2. A exceção é capturada em `lista_de_comandos`, isto é, no laço `{ comando }` mais
   interno (o do bloco atual ou o do programa).
3. `sincronizar()` descarta tokens até um **token de sincronização**:
   - `;` — fim do comando com erro; é consumido;
   - `}` — fim do bloco; não é consumido, para que o bloco feche normalmente;
   - `print`, `if`, `while`, `for`, `{` — início de comando; não é consumido;
   - `IDENT` seguido de `=` — início de atribuição. Um `IDENT` sozinho não serve, porque
     identificadores aparecem no meio de expressões (em `print x;` pararíamos no `x` e
     geraríamos um segundo erro, falso);
   - `EOF`.
4. A análise continua no próximo comando.

**Recuperação no cabeçalho de `if`/`while`/`for`.** Dentro dos parênteses do cabeçalho do
`for` há `;` que não terminam comando. Se um erro ali disparasse a sincronização geral, o
parser pararia no primeiro `;` interno e tentaria ler `i < 10; ...` como comando, gerando
erros em cascata. Por isso `cabecalho()` captura o erro antes, descarta tokens até o `)`
que fecha o cabeçalho (contando parênteses aninhados) e, se o próximo token for `{`,
analisa o corpo normalmente. Assim, em

```
for (i = 0; i < 10) { soma = ; }
```

são reportados exatamente dois erros: o `;` que falta no cabeçalho e a expressão que falta
no corpo.

**Garantias.**

- *Terminação:* `advance()` nunca passa do `EOF`, e todos os laços de descarte param no
  `EOF`. Se a sincronização parar no mesmo token em que o comando com erro começou (por
  exemplo, um `}` sobrando no nível do programa), `lista_de_comandos` descarta esse token,
  então toda volta do laço consome pelo menos um token.
- *Sem cascata:* cada erro é registrado uma única vez, no ponto em que é detectado; ao
  relançar a mesma exceção ninguém registra de novo. Depois de uma falha no cabeçalho,
  se não houver `{` à vista, o parser não reclama de "esperado '{'", porque esse segundo
  erro seria só consequência do primeiro. Os testes verificam, para cada entrada com um
  único engano, que `len(e.errors) == 1`.

**Por que modo pânico.** É a estratégia mais simples que funciona bem com um parser
descendente recursivo: não exige alterar a gramática, é fácil de explicar e garante
terminação. As alternativas são mais trabalhosas: a recuperação em nível de frase (inserir
ou trocar o token que falta e continuar) pode entrar em laço se a correção escolhida for
ruim; as produções de erro exigem acrescentar regras à gramática para cada engano previsto.
A desvantagem do modo pânico é descartar parte da entrada, o que pode esconder um erro que
esteja dentro do trecho descartado; numa linguagem pequena, com `;` e `}` frequentes, o
trecho perdido costuma ser curto.

## 3.7 Comparação com análise ascendente (LR(1) / LALR(1))

Um parser **ascendente** (*bottom-up*) constrói a árvore das folhas para a raiz. Ele mantém
uma pilha e, a cada token, consulta uma tabela que manda fazer *shift* (empilhar o token)
ou *reduce* (substituir o lado direito de uma produção, no topo da pilha, pelo
não-terminal do lado esquerdo). LR(1) usa um token de lookahead e estados que são
conjuntos de itens LR(1); LALR(1) junta estados com o mesmo núcleo, gerando tabelas bem
menores, e é o que geradores como **yacc**, **bison** e **PLY** (Python) produzem.

| Aspecto | Descendente recursivo LL(1) (adotado) | LR(1) / LALR(1) |
|---|---|---|
| Classe de gramáticas | Menor: proíbe recursão à esquerda e exige FIRST/FOLLOW disjuntos | Maior: toda gramática LL(1) é LR(1); aceita recursão à esquerda |
| Como se escreve | À mão, uma função por não-terminal | Normalmente gerado por ferramenta a partir da gramática |
| Precedência/associatividade | Codificada em níveis da gramática e laços | Pode usar gramática ambígua + declarações `%left`, `%right`, `%nonassoc` |
| Tabelas | Nenhuma; a "tabela" está nos `if` do código | Tabelas ACTION/GOTO com centenas de entradas, difíceis de ler à mão |
| Mensagens de erro | Fáceis de contextualizar: sabemos em que função (construção) estamos | Mais difíceis: o erro aparece como "nenhuma ação para este estado e token" |
| Recuperação | Modo pânico simples, em qualquer função | Token especial `error` nas produções (yacc/bison) |
| Depuração | Passo a passo num depurador comum | Exige entender estados do autômato e conflitos shift-reduce/reduce-reduce |
| Dependências | Nenhuma | Ferramenta externa (PLY, por exemplo) |

**Vantagens do LR.** Reconhece mais gramáticas, então permitiria escrever
`aditiva → aditiva "+" multiplicativa` diretamente e resolver precedência com declarações
em vez de níveis de não-terminais. Detecta o erro no mesmo ponto (prefixo viável), e o
gerador avisa sobre ambiguidades como conflitos na tabela.

**Limitações do LR.** O comportamento fica escondido nas tabelas geradas: é difícil
explicar por que um estado tem tal ação, e mensagens de erro com contexto exigem
trabalho extra. Conflitos shift-reduce precisam ser entendidos e resolvidos. Acrescenta
uma dependência fora da biblioteca padrão.

**Por que não foi escolhido.** A gramática da MiniLang já é LL(1) (seção 3.1), então o
poder extra do LR não é necessário. O parser descendente recursivo segue a EBNF linha a
linha, o que facilita conferir a correspondência gramática ↔ código, defender cada
decisão na arguição e produzir mensagens como "esperado ';' após a condição do for". Além
disso, o projeto deve usar só a biblioteca padrão do Python.
