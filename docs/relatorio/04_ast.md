# 4. Árvore Sintática Abstrata (AST)

Código: `src/ast_nodes.py` (classes e `format_tree`), construída por `src/parser.py`.
Testes: `tests/validos/test_ast.py`.

## 4.1 Definição dos nós

Cada nó é uma `dataclass` do Python. Todos têm, além dos campos abaixo, `line` e `col`:
a posição no código-fonte, usada nas mensagens de erro semântico. Para quase todos os nós
é a posição do primeiro token da construção; em `BinOp` é a do operador (o ponto mais útil
para apontar, por exemplo, uma divisão por zero). `line`/`col` não entram na comparação de
igualdade, então dois nós com a mesma estrutura são iguais mesmo vindo de posições
diferentes; isso permite que os testes comparem árvores inteiras.

### Expressões

| Classe | Campos | Significado |
|---|---|---|
| `IntLiteral` | `value: int` | Constante inteira (`42`). |
| `BoolLiteral` | `value: bool` | Constante `true` ou `false`. |
| `Var` | `name: str` | Leitura do valor de uma variável. |
| `UnaryOp` | `op: str` (sempre `"-"`), `operand: Expr` | Menos unário: `-operand`. |
| `BinOp` | `op: str`, `left: Expr`, `right: Expr` | Operação binária: aritmética (`+ - * /`) ou comparação (`< > <= >= == !=`). |

### Comandos

| Classe | Campos | Significado |
|---|---|---|
| `Assign` | `name: str`, `value: Expr` | Atribuição `name = value`. Também é o tipo da inicialização e da atualização do `For`. |
| `Print` | `expr: Expr` | Avalia `expr` e imprime o resultado. |
| `Block` | `statements: List[Stmt]` | Sequência de comandos entre chaves. Não cria escopo. |
| `If` | `condition: Expr`, `then_branch: Block`, `else_branch: Block \| If \| None` | Condicional. `else_branch` é `None` (sem `else`), um `Block` (`else { }`) ou outro `If` (`else if`). |
| `While` | `condition: Expr`, `body: Block` | Laço com teste no início: enquanto `condition` for `true`, executa `body`. |
| `For` | `init: Assign`, `condition: Expr`, `update: Assign`, `body: Block` | Laço com três cláusulas: executa `init` uma vez; enquanto `condition` for `true`, executa `body` e depois `update`. |
| `Program` | `statements: List[Stmt]` | Raiz: comandos do programa na ordem do fonte. |

Os tipos `Expr` e `Stmt` são uniões das classes de cada tabela.

Formalmente, a AST é descrita por esta gramática abstrata (sem tokens de pontuação):

```
Program = Stmt*
Stmt    = Assign(name, Expr) | Print(Expr) | Block(Stmt*)
        | If(Expr, Block, (Block | If)?) | While(Expr, Block)
        | For(Assign, Expr, Assign, Block)
Expr    = IntLiteral(int) | BoolLiteral(bool) | Var(name)
        | UnaryOp("-", Expr) | BinOp(op, Expr, Expr)
```

## 4.2 Árvore concreta × AST

A **árvore sintática concreta** (seção 3.3) registra a derivação completa: cada
não-terminal usado e cada token lido. A **AST** guarda só o que é necessário para dar
significado ao programa.

Comparação para `1 + 2 * 3`:

```
Árvore concreta (17 nós)                    AST (5 nós)

expressao                                   BinOp +
└── igualdade                               ├── IntLiteral 1
    └── relacional                          └── BinOp *
        └── aditiva                             ├── IntLiteral 2
            ├── multiplicativa                  └── IntLiteral 3
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

### O que é eliminado e por que nada necessário se perde

| Eliminado | Por que não faz falta |
|---|---|
| **Parênteses** `( )` | Servem só para forçar o agrupamento durante a análise. Depois disso, o agrupamento está na forma da árvore: em `(1 + 2) * 3` o `BinOp +` é filho do `BinOp *`. Não existe nó "Parênteses". |
| **`;`** | Marca o fim de um comando para o parser. Na AST cada comando já é um nó separado na lista `statements`. |
| **Chaves** `{ }` | Delimitam o bloco para o parser. Na AST o bloco é o nó `Block`, e os comandos dentro dele são seus filhos. |
| **Palavras-chave** (`if`, `else`, `while`, `for`, `print`) | Indicam ao parser qual construção começa. Na AST isso é o **tipo** do nó (`If`, `While`, `For`, `Print`). O `else` vira o campo `else_branch`. |
| **`=` da atribuição** e operadores como tokens | O `=` é implícito no nó `Assign`. O operador de uma operação vira o campo `op`. |
| **Cadeia de não-terminais unitários** (`expressao → igualdade → relacional → aditiva → multiplicativa → unaria → primaria`) | Existe na gramática só para codificar a precedência. Uma vez construída a árvore, a precedência já está na posição dos nós (o operador avaliado primeiro fica mais fundo), e os níveis intermediários sem operador não carregam informação. |

O critério é: tudo o que o interpretador precisa para executar o programa continua na
AST. Para avaliar uma expressão basta saber o operador e os operandos, na ordem certa; para
executar um comando basta saber seu tipo e suas partes. A ordem dos comandos é a ordem das
listas. O que foi descartado só ajudava o parser a decidir a estrutura, e essa estrutura
está preservada.

O que a AST **acrescenta** à árvore concreta: os papéis das partes têm nome (`condition`,
`body`, `init`, `update`), em vez de dependerem da posição entre tokens, e os nós guardam
`line`/`col` para as mensagens de erro semântico.

## 4.3 Visualização: `format_tree`

`format_tree(no)` devolve a árvore em texto indentado. É usado pela opção `--ast` da linha
de comando e para gerar os diagramas deste relatório. Folhas mostram o valor
(`IntLiteral 5`, `Var n`), operações mostram o operador (`BinOp +`), e os filhos de `If`,
`While` e `For` recebem um rótulo com seu papel (`condição:`, `corpo:` etc.).

### AST de um programa completo com laços

Programa:

```
n = 5;
fat = 1;
for (i = 1; i <= n; i = i + 1) {
    fat = fat * i;
}
while (n > 0) {
    if (n == 3) { print(fat); } else { print(-n); }
    n = n - 1;
}
```

Saída de `format_tree`:

```
Program
├── Assign n
│   └── IntLiteral 5
├── Assign fat
│   └── IntLiteral 1
├── For
│   ├── inicialização: Assign i
│   │   └── IntLiteral 1
│   ├── condição: BinOp <=
│   │   ├── Var i
│   │   └── Var n
│   ├── atualização: Assign i
│   │   └── BinOp +
│   │       ├── Var i
│   │       └── IntLiteral 1
│   └── corpo: Block
│       └── Assign fat
│           └── BinOp *
│               ├── Var fat
│               └── Var i
└── While
    ├── condição: BinOp >
    │   ├── Var n
    │   └── IntLiteral 0
    └── corpo: Block
        ├── If
        │   ├── condição: BinOp ==
        │   │   ├── Var n
        │   │   └── IntLiteral 3
        │   ├── então: Block
        │   │   └── Print
        │   │       └── Var fat
        │   └── senão: Block
        │       └── Print
        │           └── UnaryOp -
        │               └── Var n
        └── Assign n
            └── BinOp -
                ├── Var n
                └── IntLiteral 1
```

Observe que o `For` tem exatamente quatro filhos, um para cada parte da produção
`for_cmd` que importa para a execução (as três cláusulas e o corpo); os dois `;` e os
parênteses do cabeçalho não aparecem.
