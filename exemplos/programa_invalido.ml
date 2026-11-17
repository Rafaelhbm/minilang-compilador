// Programa inválido: o for não tem a cláusula de atualização.
// Resultado esperado: erro sintático na linha 6 — esperado ';' depois da
// condição do for, encontrado ')'.
soma = 0;

for (i = 0; i < 10) {
    soma = soma + i;
}

print(soma);
