// Erro esperado: SEMÂNTICO (tipo incompatível) na linha 4.
// A condição do while precisa ser bool; x é int e não há conversão implícita.
x = 5;
while (x) {
    x = x - 1;
}
