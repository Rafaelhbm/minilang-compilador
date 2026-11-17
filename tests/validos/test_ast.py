"""Construção da AST: forma da árvore, posições e visualização com format_tree."""
from src.ast_nodes import (
    Assign, BinOp, Block, For, IntLiteral, Print, UnaryOp, Var, While, format_tree,
)
from src.parser import parse


def expr_de(fonte: str):
    return parse("x = " + fonte + ";").statements[0].value


def test_ast_de_1_mais_2_vezes_3():
    assert expr_de("1 + 2 * 3") == BinOp(
        "+", IntLiteral(1), BinOp("*", IntLiteral(2), IntLiteral(3)))


def test_ast_de_parenteses_nao_tem_no_proprio():
    # O agrupamento aparece na forma da árvore; não existe nó "Parenteses".
    assert expr_de("(1 + 2) * 3") == BinOp(
        "*", BinOp("+", IntLiteral(1), IntLiteral(2)), IntLiteral(3))


def test_ast_de_subtracao_encadeada():
    assert expr_de("10 - 3 - 2") == BinOp(
        "-", BinOp("-", IntLiteral(10), IntLiteral(3)), IntLiteral(2))


def test_ast_de_unario():
    assert expr_de("-x * 2") == BinOp("*", UnaryOp("-", Var("x")), IntLiteral(2))


def test_ast_do_for_com_tres_clausulas():
    laco = parse("for (i = 0; i < 10; i = i + 1) { print(i); }").statements[0]
    assert laco == For(
        init=Assign("i", IntLiteral(0)),
        condition=BinOp("<", Var("i"), IntLiteral(10)),
        update=Assign("i", BinOp("+", Var("i"), IntLiteral(1))),
        body=Block([Print(Var("i"))]),
    )
    assert isinstance(laco.init, Assign)
    assert isinstance(laco.condition, BinOp)
    assert isinstance(laco.update, Assign)
    assert isinstance(laco.body, Block)


def test_ast_do_while():
    laco = parse("while (x > 0) { x = x - 1; }").statements[0]
    assert laco == While(BinOp(">", Var("x"), IntLiteral(0)),
                         Block([Assign("x", BinOp("-", Var("x"), IntLiteral(1)))]))


def test_line_col_preenchidos():
    fonte = "x = 1;\nfor (i = 0; i < 3; i = i + 1) {\n  print(x / i);\n}"
    programa = parse(fonte)
    atrib, laco = programa.statements
    assert (atrib.line, atrib.col) == (1, 1)
    assert (atrib.value.line, atrib.value.col) == (1, 5)
    assert (laco.line, laco.col) == (2, 1)
    assert (laco.init.line, laco.init.col) == (2, 6)
    assert (laco.condition.line, laco.condition.col) == (2, 15)   # o operador '<'
    assert (laco.update.line, laco.update.col) == (2, 20)
    assert (laco.body.line, laco.body.col) == (2, 31)
    impressao = laco.body.statements[0]
    assert (impressao.line, impressao.col) == (3, 3)
    divisao = impressao.expr
    assert (divisao.line, divisao.col) == (3, 11)                 # o operador '/'
    assert (divisao.left.line, divisao.left.col) == (3, 9)


def test_format_tree_de_expressao():
    esperado = (
        "Program\n"
        "└── Assign x\n"
        "    └── BinOp +\n"
        "        ├── IntLiteral 1\n"
        "        └── BinOp *\n"
        "            ├── IntLiteral 2\n"
        "            └── IntLiteral 3"
    )
    assert format_tree(parse("x = 1 + 2 * 3;")) == esperado


def test_format_tree_de_programa_com_lacos_e_if():
    fonte = """
    for (i = 0; i < 2; i = i + 1) { print(i); }
    while (true) { x = -1; }
    if (x == 1) { print(x); } else { print(false); }
    """
    esperado = (
        "Program\n"
        "├── For\n"
        "│   ├── inicialização: Assign i\n"
        "│   │   └── IntLiteral 0\n"
        "│   ├── condição: BinOp <\n"
        "│   │   ├── Var i\n"
        "│   │   └── IntLiteral 2\n"
        "│   ├── atualização: Assign i\n"
        "│   │   └── BinOp +\n"
        "│   │       ├── Var i\n"
        "│   │       └── IntLiteral 1\n"
        "│   └── corpo: Block\n"
        "│       └── Print\n"
        "│           └── Var i\n"
        "├── While\n"
        "│   ├── condição: BoolLiteral true\n"
        "│   └── corpo: Block\n"
        "│       └── Assign x\n"
        "│           └── UnaryOp -\n"
        "│               └── IntLiteral 1\n"
        "└── If\n"
        "    ├── condição: BinOp ==\n"
        "    │   ├── Var x\n"
        "    │   └── IntLiteral 1\n"
        "    ├── então: Block\n"
        "    │   └── Print\n"
        "    │       └── Var x\n"
        "    └── senão: Block\n"
        "        └── Print\n"
        "            └── BoolLiteral false"
    )
    assert format_tree(parse(fonte)) == esperado


def test_format_tree_de_no_isolado():
    assert format_tree(IntLiteral(7)) == "IntLiteral 7"
    assert format_tree(BinOp("-", Var("a"), Var("b"))) == "BinOp -\n├── Var a\n└── Var b"
