// Erro esperado: LÉXICO na linha 4, coluna 1.
// Identificadores não podem começar com dígito: "1x" não é INT nem IDENT
// (um número colado a uma letra é rejeitado pelo lexer).
1x = 5;
print(1x);
