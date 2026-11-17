// Erro esperado: SEMÂNTICO (variável não definida) na linha 4.
// A inicialização do for define i, mas a condição usa j, que nunca foi atribuída.
soma = 0;
for (i = 0; j < 10; i = i + 1) {
    soma = soma + i;
}
