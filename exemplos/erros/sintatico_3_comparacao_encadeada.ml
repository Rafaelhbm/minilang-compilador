// Erro esperado: SINTÁTICO na linha 4.
// Comparações não são associativas: 1 < 2 < 3 não pertence à linguagem.
// Para comparar o resultado de uma comparação, use parênteses: (1 < 2) == true.
x = 1 < 2 < 3;
print(x);
