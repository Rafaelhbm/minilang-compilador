# 6. Catálogo de erros

Cada fase do compilador detecta uma categoria de erro e lança a exceção correspondente
de `src/errors.py`. Todas as mensagens seguem o mesmo formato:

```
[Erro <categoria>] linha L, coluna C: <mensagem>
```

Na CLI (`python -m src`), a mensagem vai para a saída de erro (stderr), seguida da linha
do código-fonte com um `^` sob a coluna apontada, e o processo termina com código 1.
Nenhum erro da linguagem mostra traceback do Python.

## 6.1 Tabela de erros por categoria

### Léxicos (`LexicalError`, lançados por `src/lexer.py`)

| Mensagem | Causa | Exemplo |
|---|---|---|
| `caractere inválido '@'` | o caractere não inicia nenhum token: o AFD não tem transição a partir do estado inicial | `y = x @ 2;` |
| `caractere inválido '!' (o operador de diferença é '!=')` | `!` sozinho; só existe como parte de `!=` | `if (!x) { }` |
| `número mal formado '1x': identificadores não podem começar com dígito` | dígitos seguidos de letra ou `_` | `1x = 5;` |
| `comentário de bloco não fechado` | `/*` sem o `*/` correspondente até o fim do arquivo | `/* comentário` |

### Sintáticos (`MiniLangSyntaxError`, lançados por `src/parser.py`)

| Mensagem | Causa | Exemplo |
|---|---|---|
| `esperado ';' após a condição do for (o for exige inicialização; condição; atualização), encontrado ')'` | `for` sem a cláusula de atualização | `for (i = 0; i < 10) { }` |
| `esperado expressão após '+', encontrado ';'` | operador binário sem o operando da direita | `x = (1 + ;` |
| `operadores de comparação não são associativos; use parênteses, ex.: (a < b) == c (encontrado '<' depois de uma comparação)` | duas comparações encadeadas no mesmo nível | `x = 1 < 2 < 3;` |
| `esperado ';' após a atribuição, encontrado 'print'` | `;` faltando no fim do comando | `x = 1` (sem `;`) seguido de `print(x);` |
| `esperado ';' após a atribuição, encontrado '=' (atribuição é comando, não expressão; ...)` | atribuição encadeada | `x = 1 = 2;` |
| `esperado ')' para fechar o print, encontrado ';'` | parêntese não fechado | `print(y;` |
| `esperado '}' para fechar o bloco aberto na linha 1, encontrado fim do arquivo` | bloco sem `}` | `if (true) { x = 1;` |
| `esperado início de comando (identificador, 'print', 'if', 'while', 'for' ou '{'), encontrado '}'` | token que não pode começar um comando | `}` solto |

### Semânticos (`SemanticError` e subclasses, lançados por `src/interpreter.py`)

| Exceção | Mensagem | Causa | Exemplo |
|---|---|---|---|
| `TypeMismatchError` | `condição do while deve ser bool, mas é int` | condição de `if`/`while`/`for` não booleana (não há conversão int → bool) | `while (x) { }` com `x` int |
| `TypeMismatchError` | `operador '+' exige int e int, mas recebeu int e bool` | aritmética ou comparação relacional com `bool` | `print(1 + true);` |
| `TypeMismatchError` | `'==' exige operandos do mesmo tipo, mas recebeu int e bool` | igualdade entre tipos diferentes | `print(1 == true);` |
| `TypeMismatchError` | `operador '-' unário exige int, mas recebeu bool` | negação de `bool` | `print(-true);` |
| `TypeMismatchError` | `variável 'x' é int e não pode receber bool` | reatribuição com tipo diferente do fixado na primeira atribuição | `x = 1; x = true;` |
| `UndefinedVariableError` | `variável 'j' não definida` | uso de variável nunca atribuída | `for (i = 0; j < 10; i = i + 1) { }` |
| `DivisionByZeroError` | `divisão por zero` | divisor avaliado como 0 | `print(a / b);` com `b = 0` |
| `LoopLimitError` | `laço while excedeu o limite de 1000 iterações (possível laço infinito)` | laço passou de `max_iterations` iterações (N permitidas, a N+1-ésima estoura) | `while (true) { }` com `--max-iter 1000` |

## 6.2 Demonstração com os programas de `exemplos/erros/`

Cada arquivo tem no topo um comentário com o erro esperado. Saídas reais, obtidas com
`python -m src <arquivo>` (o comentário inicial de cada arquivo ocupa as primeiras linhas,
por isso os erros aparecem a partir da linha 3 ou 4).

O teste `tests/invalidos/test_exemplos_de_erro.py` lê esse comentário de cada arquivo,
roda o programa pela CLI e confere categoria, linha e coluna (quando informada), código
de saída 1 e ausência de traceback. Se o compilador mudar e um exemplo deixar de produzir
o erro anunciado, a suíte falha.

### Léxicos

```
$ python -m src exemplos/erros/lexico_1_caractere_invalido.ml
[Erro léxico] linha 4, coluna 7: caractere inválido '@'
  4 | y = x @ 2;
            ^
[código de saída: 1]

$ python -m src exemplos/erros/lexico_2_identificador_comecando_com_digito.ml
[Erro léxico] linha 4, coluna 1: número mal formado '1x': identificadores não podem começar com dígito
  4 | 1x = 5;
      ^
[código de saída: 1]

$ python -m src exemplos/erros/lexico_3_comentario_nao_fechado.ml
[Erro léxico] linha 4, coluna 1: comentário de bloco não fechado
  4 | /* este comentário
      ^
[código de saída: 1]
```

No terceiro caso, o erro aponta para onde o comentário **começa** (linha 4), e não para
o fim do arquivo, onde o lexer percebeu o problema. É a posição útil para quem corrige.

### Sintáticos

```
$ python -m src exemplos/erros/sintatico_1_for_sem_atualizacao.ml
[Erro sintático] linha 4, coluna 19: esperado ';' após a condição do for (o for exige inicialização; condição; atualização), encontrado ')'
  4 | for (i = 0; i < 10) {
                        ^
[código de saída: 1]

$ python -m src exemplos/erros/sintatico_2_expressao_incompleta.ml
[Erro sintático] linha 3, coluna 10: esperado expressão após '+', encontrado ';'
  3 | x = (1 + ;
               ^
[código de saída: 1]

$ python -m src exemplos/erros/sintatico_3_comparacao_encadeada.ml
[Erro sintático] linha 4, coluna 11: operadores de comparação não são associativos; use parênteses, ex.: (a < b) == c (encontrado '<' depois de uma comparação)
  4 | x = 1 < 2 < 3;
                ^
[código de saída: 1]
```

Recuperação em modo pânico com mais de um erro no mesmo arquivo (programa auxiliar, fora
de `exemplos/erros/`):

```
x = 1 +;
y = 2;
print(y;
z = 3;
```

```
[Erro sintático] linha 1, coluna 8: esperado expressão após '+', encontrado ';'
  1 | x = 1 +;
             ^
[Erro sintático] linha 3, coluna 8: esperado ')' para fechar o print, encontrado ';'
  3 | print(y;
             ^
2 erros sintáticos encontrados.
```

O parser registrou o erro da linha 1, descartou tokens até o `;`, analisou `y = 2;`
normalmente e encontrou o segundo erro na linha 3. Nenhum erro falso foi gerado na linha
2 nem na 4.

### Semânticos

```
$ python -m src exemplos/erros/semantico_1_while_nao_booleano.ml
[Erro semântico] linha 4, coluna 8: condição do while deve ser bool, mas é int
  4 | while (x) {
             ^
[código de saída: 1]

$ python -m src exemplos/erros/semantico_2_variavel_nao_definida_no_for.ml
[Erro semântico] linha 4, coluna 13: variável 'j' não definida
  4 | for (i = 0; j < 10; i = i + 1) {
                  ^
[código de saída: 1]

$ python -m src exemplos/erros/semantico_3_divisao_por_zero.ml
10
[Erro semântico] linha 6, coluna 9: divisão por zero
  6 | print(a / b);
              ^
[código de saída: 1]
```

No terceiro caso, o `10` aparece porque o `print(a)` da linha 5 já tinha executado: os
erros semânticos são detectados durante a execução, e o que foi impresso antes continua
impresso.

## 6.3 Estratégia de diagnóstico e recuperação por fase

As três fases tratam erros de formas diferentes. A escolha de cada uma depende do que a
fase sabe sobre a entrada no momento em que o erro aparece.

### Léxico: para no primeiro erro

O lexer lança `LexicalError` no primeiro caractere que o autômato não consegue consumir
e não tenta continuar.

Por quê:

- **Não há um ponto seguro para recomeçar.** Depois de um caractere inválido, o lexer
  não sabe o que a pessoa quis escrever. Em `1x`, ela queria um identificador `x1`, um
  número `1` e esqueceu um operador, ou outra coisa? Qualquer palpite (pular o caractere,
  partir em dois tokens) inventa uma sequência de tokens que não está no arquivo.
- **Erros inventados contaminam o parser.** Se o lexer pulasse o `@` de `y = x @ 2;`, o
  parser receberia `y = x 2;` e reportaria um erro sintático que não existe. No caso do
  comentário não fechado é pior: não há como saber onde o comentário deveria terminar,
  então todo o resto do arquivo fica sem sentido.
- **Erros léxicos são raros e fáceis de corrigir.** Costumam ser um caractere digitado
  errado. Corrigir um e rodar de novo custa pouco; a fase seguinte (sintática) é que
  costuma ter vários erros por arquivo e se beneficia de recuperação.
- **Uma fase só começa com a entrada válida da anterior.** Como o parser recebe a lista
  completa de tokens, parar no primeiro erro léxico garante que ele nunca analise uma
  lista de tokens incompleta ou adivinhada.

### Sintático: modo pânico com tokens de sincronização

O parser não para no primeiro erro. Ele registra o diagnóstico, descarta tokens até um
**ponto de sincronização** e continua a análise a partir dali. No fim, se houve algum
erro, lança um único `MiniLangSyntaxError` cuja lista `.errors` traz todos os
diagnósticos, e a CLI imprime todos.

Pontos de sincronização (método `sincronizar` em `src/parser.py`):

- `;`: fim do comando com erro; é consumido e a análise recomeça no comando seguinte;
- `}`: fim de bloco; para sem consumir, para o bloco que está aberto poder fechar;
- `print`, `if`, `while`, `for`, `{`: começo de um comando novo;
- `IDENT` seguido de `=`: começo de uma atribuição (um `IDENT` sozinho não basta,
  porque identificadores aparecem no meio de expressões e parar neles geraria erros em
  cascata);
- `EOF`.

Há também `recuperar_cabecalho`, que descarta até o `)` que fecha o cabeçalho de
`if`/`while`/`for`, para aproveitar o bloco do corpo mesmo quando a condição tem erro.

Por quê:

- **Aqui existe um ponto seguro para recomeçar.** Diferente do lexer, a gramática da
  MiniLang tem delimitadores que separam comandos: todo comando simples termina em `;` e
  todo bloco termina em `}`, e os comandos compostos começam por palavras reservadas.
  Esses tokens são pontos onde o parser sabe exatamente em qual regra está
  (`comando`), então continuar dali não depende de adivinhar a intenção de quem escreveu.
- **Vários erros por execução.** Num programa com três `;` esquecidos, o aluno vê os três
  de uma vez em vez de corrigir, rodar, corrigir, rodar. É a estratégia descrita na
  literatura de compiladores (Aho et al., *Compilers*, seção 4.1.4) justamente por ser
  simples de implementar num parser descendente recursivo e não entrar em laço infinito:
  ela só descarta tokens, nunca insere.
- **Os tokens escolhidos evitam erros em cascata.** Um erro falso que aparece só porque a
  recuperação parou no lugar errado atrapalha mais do que ajuda. Por isso o `IDENT`
  sozinho não sincroniza e o `}` não é consumido (consumi-lo deixaria o bloco externo sem
  fechamento e geraria um segundo erro falso).
- **Garantia de progresso.** Se a sincronização parar no mesmo token em que o comando
  com erro começou (por exemplo, um `}` sobrando no nível do programa), o parser descarta
  esse token antes de tentar de novo; assim a recuperação sempre
  avança e termina.
- **Nenhuma AST com erro é executada.** Com qualquer erro sintático, o parser lança a
  exceção em vez de devolver a árvore. A recuperação serve só para diagnosticar mais; a
  árvore parcial não é confiável e não vai para o interpretador.

### Semântico: para na primeira violação em tempo de execução

As checagens semânticas (tipos, variável definida, divisão por zero, limite de iterações)
são feitas pelo interpretador enquanto ele percorre a AST. Na primeira violação ele lança
a subclasse de `SemanticError` correspondente e a execução termina. O que já foi impresso
continua impresso.

Por quê:

- **Depois de uma violação, o estado do programa não tem sentido.** Se `a / b` com
  `b = 0` não produz valor, o que guardar na variável que receberia o resultado? Se
  `x = true` falha porque `x` é `int`, `x` continua com o valor antigo ou muda de tipo?
  Qualquer escolha faria o programa continuar com valores que ele não calculou, e os
  erros seguintes seriam consequência dessa escolha, não do código do aluno.
- **Os valores só existem durante a execução.** A divisão por zero e o laço infinito
  dependem de valores calculados em tempo de execução: no exemplo, `b` só vale 0 porque
  a linha 4 executou. Como a MiniLang é interpretada e as variáveis não têm tipo declarado
  (o tipo é fixado na primeira atribuição), a forma mais direta de saber o tipo e o valor
  de uma expressão é avaliá-la.
- **Comportamento previsível para quem usa.** Parar na primeira violação é o mesmo que
  fazem Python e outras linguagens interpretadas: a saída antes do erro é exatamente a de
  um programa que executou até aquele ponto.
- **Laço infinito precisa de limite, não de detecção.** Decidir se um laço termina é o
  problema da parada, que é indecidível. O interpretador conta as iterações de cada
  execução de um laço e, com `max_iterations = N`, permite N iterações e lança
  `LoopLimitError` na N+1-ésima (testado em `tests/invalidos/test_laco_infinito.py`).

Limitação assumida: como a checagem acontece na execução, um erro de tipo num trecho que
nunca executa não é reportado. Por exemplo, `if (false) { print(1 + true); } print(7);`
imprime `7` sem erro. Uma análise semântica estática (percorrer a AST inteira verificando
tipos antes de executar) resolveria isso, mas exigiria inferir o tipo de cada variável em
todos os caminhos do programa, o que fica fora do escopo deste trabalho.
