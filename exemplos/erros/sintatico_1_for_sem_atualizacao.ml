// Erro esperado: SINTÁTICO na linha 4.
// O for exige três cláusulas; depois da condição o parser espera ';' e encontra ')'.
soma = 0;
for (i = 0; i < 10) {
    soma = soma + i;
}
print(soma);
