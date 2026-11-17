# 5. Interpretador e análise semântica

O interpretador (`src/interpreter.py`) recebe a AST produzida pelo parser e a executa
percorrendo a árvore recursivamente (*tree-walking interpreter*). As regras de tipo da
seção 4 de `docs/gramatica.md` são verificadas durante essa execução. Esta seção descreve
a tabela de símbolos, define a semântica operacional da MiniLang, justifica por que o
interpretador aceita exatamente os programas válidos e discute a escolha por verificação
dinâmica.

## 5.1 Tabela de símbolos

### Estrutura

A tabela é um dicionário Python que associa o nome da variável a um registro `Symbol`:

| Campo | Conteúdo |
|---|---|
| `name` | nome da variável |
| `type` | `"int"` ou `"bool"`, fixado na primeira atribuição |
| `value` | valor atual (`int` ou `bool` do Python) |
| `line` | linha da primeira atribuição |

### Operações

| Operação | O que faz | Complexidade (média) |
|---|---|---|
| `insert(nome, valor, linha)` | cria a variável; o tipo é o tipo do valor | O(1) |
| `update(nome, valor, linha, col)` | busca a variável e troca o valor se o tipo for igual; senão `TypeMismatchError` | O(1) |
| `lookup(nome, linha, col)` | devolve o `Symbol`; se o nome não existe, `UndefinedVariableError` | O(1) |
| `contains(nome)` | diz se a variável já foi atribuída | O(1) |

O dicionário do Python é uma tabela hash, então inserção e busca custam O(1) em média
(O(n) no pior caso, com muitas colisões, o que não ocorre na prática com nomes de
variáveis). O custo de uma execução fica dominado pelo número de nós avaliados, não pela
tabela.

### Por que é suficiente

As verificações exigidas pela seção 4 que dependem de variáveis são duas:

1. **Variável usada antes de definida**: basta saber se o nome está na tabela. `lookup`
   faz exatamente isso.
2. **Atribuição com tipo incompatível**: basta lembrar o tipo de cada variável. O campo
   `type` é gravado no `insert` e conferido no `update`.

Não é preciso uma pilha de escopos porque a MiniLang não tem declarações locais nem
funções, e a gramática define que blocos não criam escopo: uma variável criada dentro de
`{ ... }` (inclusive a variável de controle do `for`) continua visível depois do bloco.
Uma pilha de escopos só seria necessária se o mesmo nome pudesse designar variáveis
diferentes em regiões diferentes do programa, e isso não acontece na linguagem. Usar uma
pilha mudaria a semântica: `{ x = 1; } print(x);` passaria a ser erro, contrariando a
definição.

## 5.2 Semântica operacional (natural, *big-step*)

### Notação

- Um **estado** σ é uma função parcial de nomes para pares (tipo, valor). `dom(σ)` é o
  conjunto de variáveis já atribuídas. σ[x ↦ v] é o estado igual a σ, exceto que x vale v.
- Valores: inteiros `n` (tipo `int`) e `true`/`false` (tipo `bool`). `tipo(v)` dá o tipo.
- ⟨e, σ⟩ ⇓ v: a expressão e, no estado σ, avalia para o valor v.
- ⟨c, σ⟩ ⇓ σ': o comando c, executado em σ, termina no estado σ'.
- ⟨c, σ⟩ ⇓ **erro**(E): a execução de c é interrompida com o erro E (uma das classes
  `UndefinedVariableError`, `TypeMismatchError`, `DivisionByZeroError`, `LoopLimitError`).
- A saída de `print` é tratada como efeito colateral: escrevemos `out(s)` na premissa.

Regras são escritas como *premissas / conclusão*. Um erro em qualquer premissa se propaga
para a conclusão (a execução para no primeiro erro); para não repetir dezenas de regras de
propagação, essa convenção fica implícita.

### Expressões

```
                                       x ∈ dom(σ)    σ(x) = v
(Int)  ⟨n, σ⟩ ⇓ n       (Var)  ─────────────────────────────
(Bool) ⟨true, σ⟩ ⇓ true          ⟨x, σ⟩ ⇓ v
       ⟨false, σ⟩ ⇓ false

                  x ∉ dom(σ)
(Var-Erro)  ─────────────────────────────────────
            ⟨x, σ⟩ ⇓ erro(UndefinedVariableError)

            ⟨e, σ⟩ ⇓ n    (n inteiro)               ⟨e, σ⟩ ⇓ b    (b booleano)
(Neg)     ─────────────────────────      (Neg-Erro) ─────────────────────────────────
            ⟨-e, σ⟩ ⇓ −n                            ⟨-e, σ⟩ ⇓ erro(TypeMismatchError)

            ⟨e1, σ⟩ ⇓ n1   ⟨e2, σ⟩ ⇓ n2   (n1, n2 inteiros)   ⊕ ∈ {+, -, *}
(Arit)    ─────────────────────────────────────────────────────────────────
            ⟨e1 ⊕ e2, σ⟩ ⇓ n1 ⊕ n2

            ⟨e1, σ⟩ ⇓ n1   ⟨e2, σ⟩ ⇓ n2   (inteiros)   n2 ≠ 0
(Div)     ───────────────────────────────────────────────────────
            ⟨e1 / e2, σ⟩ ⇓ sinal(n1·n2) · ⌊|n1| / |n2|⌋

            ⟨e1, σ⟩ ⇓ n1   ⟨e2, σ⟩ ⇓ 0
(Div-Zero)───────────────────────────────────────
            ⟨e1 / e2, σ⟩ ⇓ erro(DivisionByZeroError)

            ⟨e1, σ⟩ ⇓ n1   ⟨e2, σ⟩ ⇓ n2   (inteiros)   ◁ ∈ {<, >, <=, >=}
(Rel)     ─────────────────────────────────────────────────────────────
            ⟨e1 ◁ e2, σ⟩ ⇓ (n1 ◁ n2)          (resultado true ou false)

            ⟨e1, σ⟩ ⇓ v1   ⟨e2, σ⟩ ⇓ v2   tipo(v1) = tipo(v2)
(Eq)      ───────────────────────────────────────────────────    (análoga para !=)
            ⟨e1 == e2, σ⟩ ⇓ (v1 = v2)

            ⟨e1, σ⟩ ⇓ v1   ⟨e2, σ⟩ ⇓ v2   tipo(v1) ≠ int ou tipo(v2) ≠ int   op ∈ {+,-,*,/,<,>,<=,>=}
(Op-Erro) ───────────────────────────────────────────────────────────────────────────────
            ⟨e1 op e2, σ⟩ ⇓ erro(TypeMismatchError)

            ⟨e1, σ⟩ ⇓ v1   ⟨e2, σ⟩ ⇓ v2   tipo(v1) ≠ tipo(v2)   op ∈ {==, !=}
(Eq-Erro) ───────────────────────────────────────────────────────────────
            ⟨e1 op e2, σ⟩ ⇓ erro(TypeMismatchError)
```

Os dois operandos são sempre avaliados, o esquerdo primeiro, antes da checagem de tipos
(não há curto-circuito na linguagem). Na regra (Div), a fórmula define a divisão
**truncada em direção a zero**: −7 / 2 = −3 e 7 / −2 = −3. O operador `//` do Python
arredonda para −∞ (−7 // 2 = −4), por isso o código usa `truncated_division`, que divide
os valores absolutos e reaplica o sinal.

### Comandos

```
              ⟨e, σ⟩ ⇓ v    x ∉ dom(σ)
(Atrib-Nova) ─────────────────────────────
              ⟨x = e, σ⟩ ⇓ σ[x ↦ (tipo(v), v)]

              ⟨e, σ⟩ ⇓ v    x ∈ dom(σ)    tipo(σ(x)) = tipo(v)
(Atrib-Reat) ─────────────────────────────────────────────────
              ⟨x = e, σ⟩ ⇓ σ[x ↦ (tipo(v), v)]

              ⟨e, σ⟩ ⇓ v    x ∈ dom(σ)    tipo(σ(x)) ≠ tipo(v)
(Atrib-Erro) ─────────────────────────────────────────────────
              ⟨x = e, σ⟩ ⇓ erro(TypeMismatchError)

              ⟨e, σ⟩ ⇓ v    out(texto(v))      texto(n) = decimal de n,
(Print)      ─────────────────────────────     texto(true) = "true", texto(false) = "false"
              ⟨print(e), σ⟩ ⇓ σ

(Bloco-Vazio) ⟨{ }, σ⟩ ⇓ σ

              ⟨c1, σ⟩ ⇓ σ1    ⟨{ c2 … ck }, σ1⟩ ⇓ σ'
(Seq)        ─────────────────────────────────────────
              ⟨{ c1 c2 … ck }, σ⟩ ⇓ σ'
```

O programa inteiro é tratado como uma sequência, partindo do estado vazio ∅.

```
              ⟨e, σ⟩ ⇓ true    ⟨B1, σ⟩ ⇓ σ'
(If-V)       ─────────────────────────────────
              ⟨if (e) B1 else S2, σ⟩ ⇓ σ'

              ⟨e, σ⟩ ⇓ false    ⟨S2, σ⟩ ⇓ σ'
(If-F)       ─────────────────────────────────          (S2 é um bloco ou outro if;
              ⟨if (e) B1 else S2, σ⟩ ⇓ σ'               sem else, S2 = { })

              ⟨e, σ⟩ ⇓ n    (n inteiro)
(If-Erro)    ───────────────────────────────────────
              ⟨if (e) B1 else S2, σ⟩ ⇓ erro(TypeMismatchError)
```

Para os laços, a regra precisa de um contador k de iterações já executadas e do limite
L = `max_iterations` (padrão 100 000). Escrevemos `while_k`; o programa começa em
`while_0`.

```
              ⟨e, σ⟩ ⇓ false
(While-F)    ─────────────────────────
              ⟨while_k (e) B, σ⟩ ⇓ σ

              ⟨e, σ⟩ ⇓ true    k + 1 ≤ L    ⟨B, σ⟩ ⇓ σ1    ⟨while_{k+1} (e) B, σ1⟩ ⇓ σ'
(While-V)    ───────────────────────────────────────────────────────────────────────────
              ⟨while_k (e) B, σ⟩ ⇓ σ'

              ⟨e, σ⟩ ⇓ true    k + 1 > L
(While-Lim)  ─────────────────────────────────────────
              ⟨while_k (e) B, σ⟩ ⇓ erro(LoopLimitError)

              ⟨e, σ⟩ ⇓ n    (n inteiro)
(While-Erro) ─────────────────────────────────────────
              ⟨while_k (e) B, σ⟩ ⇓ erro(TypeMismatchError)
```

A regra (While-V) é recursiva: a conclusão aparece de novo como premissa, com o estado
atualizado. Num laço sem o limite, um `while (true) { }` não teria árvore de derivação
finita, ou seja, não haveria σ' com ⟨c, σ⟩ ⇓ σ' (a semântica natural não distingue
"não termina" de "fica preso"). O contador k garante que toda execução tem derivação
finita, terminando em um estado ou em `erro(LoopLimitError)`.

O `for` é definido em duas etapas: executa a inicialização uma única vez e então repete
teste, corpo e atualização.

```
              ⟨a_init, σ⟩ ⇓ σ0    ⟨for_0 (e; a_upd) B, σ0⟩ ⇓ σ'
(For)        ──────────────────────────────────────────────────
              ⟨for (a_init; e; a_upd) B, σ⟩ ⇓ σ'

              ⟨e, σ⟩ ⇓ false
(For-F)      ─────────────────────────────
              ⟨for_k (e; a_upd) B, σ⟩ ⇓ σ

              ⟨e, σ⟩ ⇓ true   k+1 ≤ L   ⟨B, σ⟩ ⇓ σ1   ⟨a_upd, σ1⟩ ⇓ σ2   ⟨for_{k+1} (e; a_upd) B, σ2⟩ ⇓ σ'
(For-V)      ───────────────────────────────────────────────────────────────────────────────────────
              ⟨for_k (e; a_upd) B, σ⟩ ⇓ σ'
```

(For-Lim) e (For-Erro) são idênticas às do `while`.

**Equivalência com `while`.** Afirmamos que, para todo σ,

    ⟨for (a_init; e; a_upd) B, σ⟩ ⇓ R   se e somente se   ⟨a_init; while (e) { B a_upd }, σ⟩ ⇓ R

onde R é um estado ou um erro. Prova, por indução no número de iterações:

- Pela regra (Seq), o lado direito executa `a_init` levando σ a σ0, exatamente como a
  premissa de (For). Resta mostrar que `for_k (e; a_upd) B` em σ0 e `while_k (e) { B a_upd }`
  em σ0 produzem o mesmo resultado.
- Se ⟨e, σ0⟩ ⇓ false: (For-F) e (While-F) devolvem σ0.
- Se e não é `bool`: (For-Erro) e (While-Erro) dão o mesmo erro. Idem para o limite.
- Se ⟨e, σ0⟩ ⇓ true e k+1 ≤ L: (While-V) executa o bloco `{ B a_upd }`, que por (Seq)
  significa ⟨B, σ0⟩ ⇓ σ1 e ⟨a_upd, σ1⟩ ⇓ σ2 — as mesmas premissas de (For-V) — e
  continua em `while_{k+1}` a partir de σ2, enquanto (For-V) continua em `for_{k+1}` a
  partir de σ2. Pela hipótese de indução, os dois produzem o mesmo resultado.

O código segue essa equivalência literalmente: `exec_for` executa `node.init` e depois um
laço `while` do Python com condição, corpo e `node.update`. Uma consequência é que a
variável de controle continua existindo depois do laço com o valor que tornou a condição
falsa (escopo único).

## 5.3 O interpretador aceita exatamente os programas válidos

Chamamos de **semanticamente válido** um programa sintaticamente correto cuja execução,
de acordo com as regras da seção 4, nunca viola uma regra de tipo, nunca usa variável
indefinida, nunca divide por zero e cujos laços terminam dentro do limite. Pelas regras da
seção 5.2, isso é o mesmo que dizer que existe uma derivação ⟨P, ∅⟩ ⇓ σ' sem erro.

A justificativa tem duas direções.

**(1) Todo programa inválido é rejeitado.** Análise de casos sobre cada linha da tabela
da seção 4, apontando o ponto do código que faz a verificação:

| Regra da seção 4 | Verificação no código | Erro |
|---|---|---|
| `+ - * /` exigem `int, int` | `eval_bin_op`: `type(left) is not int or type(right) is not int` | `TypeMismatchError` |
| `/` exige divisor ≠ 0 | `eval_bin_op`: `if right == 0` (o divisor já foi avaliado, então vale para `x / (y - y)`) | `DivisionByZeroError` |
| `-a` exige `int` | `eval_unary_op`: `type(operand) is not int` | `TypeMismatchError` |
| `< > <= >=` exigem `int, int` | mesma checagem dos aritméticos em `eval_bin_op` | `TypeMismatchError` |
| `== !=` exigem mesmo tipo | `eval_bin_op`: `type_name(left) != type_name(right)` | `TypeMismatchError` |
| condição de `if` é `bool` | `exec_if` → `eval_condition(..., "if")` | `TypeMismatchError` |
| condição de `while` é `bool` | `exec_while` → `eval_condition(..., "while")`, antes de **cada** iteração | `TypeMismatchError` |
| condição de `for` é `bool` | `exec_for` → `eval_condition(..., "for")`, antes de cada iteração | `TypeMismatchError` |
| uso de `x` exige `x` atribuída | `eval_var` → `SymbolTable.lookup` | `UndefinedVariableError` |
| `x = e` mantém o tipo de `x` | `exec_assign` → `SymbolTable.update` | `TypeMismatchError` |
| laço termina | `check_loop_limit` em `exec_while` e `exec_for` | `LoopLimitError` |

Casos que merecem atenção:

- **Laço com condição não booleana** (`while (x)` com `x` int). Como a condição é
  avaliada antes da primeira iteração, o erro sai antes de o corpo rodar uma única vez.
  Como os tipos das variáveis são fixos, uma condição que é `bool` na primeira avaliação
  continua `bool` nas seguintes; mesmo assim o código checa a cada iteração, o que segue
  a regra (While-Erro) sem depender desse argumento.
- **Variável de controle não definida** (`for (i = 0; j < 10; i = i + 1)`). A
  inicialização cria `i`, mas a condição usa `j`. Ao avaliar a condição pela primeira vez,
  `eval_var` chama `lookup("j")`, que não encontra o nome e lança
  `UndefinedVariableError` com a posição de `j`. O mesmo acontece se o nome errado estiver
  na atualização (`i = k + 1`), na primeira vez que a atualização é executada.
- **`x = x + 1` com `x` indefinido.** O lado direito é avaliado antes de qualquer
  alteração na tabela, então o erro é "variável não definida", e não a criação de `x`.
- **`bool` como subclasse de `int` no Python.** `isinstance(True, int)` é `True` e
  `True + 1 == 2`. Se o código usasse `isinstance`, `true + 1`, `-true`, `1 == true` e
  `x = true` com `x` int seriam aceitos. Toda verificação usa `type(v) is int` /
  `type(v) is bool`, que comparam a classe exata. Há testes específicos para cada caso.

Como cada regra que pode falhar tem um ponto de verificação executado **exatamente** no
momento em que a construção é avaliada, se um programa viola uma regra, a execução chega
nesse ponto e lança o erro correspondente.

Uma ressalva importante: a verificação é feita **no caminho executado**. Um erro de tipo
dentro de um ramo que nunca executa (por exemplo, `if (false) { x = 1 + true; }`) não é
detectado. Com a definição de validade acima (baseada na execução, como as regras da
seção 5.2), esse programa é válido: não existe derivação que use a regra (Op-Erro). Uma
análise estática o rejeitaria. A seção 5.4 discute essa diferença.

**(2) Todo programa válido é executado corretamente.** Se nenhuma verificação falha,
cada método `exec_*`/`eval_*` faz exatamente o que a regra de sucesso correspondente
prescreve (atribuição grava na tabela, `if` escolhe o ramo pela condição, `while` repete
enquanto a condição é `true`, operadores calculam com a semântica de inteiros de precisão
arbitrária do Python, divisão truncada por `truncated_division`). Nenhum erro é lançado
fora das situações listadas na tabela acima, então nenhum programa válido é rejeitado.
Os inteiros do Python não têm limite de tamanho, portanto não existe estouro aritmético.

**O limite de iterações.** Decidir, para um programa arbitrário, se um laço termina é o
**problema da parada**, que Turing provou ser indecidível: não existe algoritmo que
responda corretamente para todos os programas. Como a MiniLang tem variáveis inteiras sem
limite, atribuição e `while`, ela consegue simular uma máquina de contadores e portanto
herda essa indecidibilidade. Por isso o interpretador não tenta provar terminação; ele
conta as iterações de cada execução de um laço e, ao passar de `max_iterations`
(100 000 por padrão, configurável), lança `LoopLimitError`. O limite é prático: rejeita
todos os laços infinitos, mas também rejeitaria um laço finito que precisasse de mais de
100 000 iterações. O contador é por execução de laço (cada `while`/`for` começa do zero
ao ser executado), não global.

## 5.4 Decisão: verificação dinâmica em vez de análise estática

Optamos por verificar as regras semânticas **durante a execução**, no próprio
interpretador, em vez de uma passada de análise estática (verificador de tipos) antes de
executar.

**Vantagens da verificação dinâmica neste projeto:**

- **Um único percurso da AST.** O código de cada nó avalia e verifica no mesmo lugar, o
  que deixa o interpretador pequeno e fácil de explicar.
- **Alguns erros só são detectáveis em execução.** Divisão por zero com divisor calculado
  (`x / (y - y)`) e laço que não termina não podem ser decididos estaticamente em geral
  (o segundo é o problema da parada). Esses erros precisariam de checagem dinâmica de
  qualquer forma.
- **Mensagens com valores concretos e posição exata**, pois o erro é detectado no nó que
  o causou.
- **Corresponde diretamente à semântica operacional** da seção 5.2, em que os erros são
  regras de avaliação.

**Limitações:**

- **Erros em código não executado passam despercebidos** (`if (false) { x = 1 + true; }`).
- **Execução parcial antes do erro:** em `print(1); print(y);` o `1` é impresso antes do
  erro de variável indefinida.
- **Custo em tempo de execução:** cada operação verifica tipos, inclusive em todas as
  iterações de um laço.

**Como seria a alternativa estática.** Como o tipo de toda variável é fixado na primeira
atribuição e nunca muda, seria possível inferir tipos antes de executar, percorrendo a AST
com uma tabela nome → tipo. A dificuldade está na definição de "atribuída antes do uso":
com `if (c) { x = 1; } print(x);`, a variável pode ou não existir dependendo de `c`, e o
verificador precisaria de análise de fluxo (variáveis definidas em todos os caminhos) e
tomaria uma decisão conservadora, rejeitando programas que em execução funcionariam.

**Por que esta escolha.** A gramática define a validade semântica pelas regras de tipo
aplicadas às construções, e o enunciado pede um interpretador que execute programas e
reporte erros semânticos. A verificação dinâmica implementa essas regras de forma direta
e completa para os caminhos executados, cobre os erros que só aparecem em execução, e
mantém o código defensável. A análise estática fica registrada como extensão possível:
ela seria uma passada adicional, sem mudar o interpretador.
