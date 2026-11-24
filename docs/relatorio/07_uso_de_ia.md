# 7. Análise crítica do uso de IA generativa e fundamentação teórica

Em conformidade com as diretrizes do projeto e com a Portaria CNPq nº 2.664/2026 (registrada em `declaracao_IA.md` e detalhada em `docs/diario_de_bordo.md`), a equipe utilizou a ferramenta **Claude Code** (Anthropic; modelos Claude Opus 5.5 e Claude Fable 5.2) como copiloto durante o desenvolvimento, além de apoio para revisão e estruturação documental. Todo artefato gerado passou por inspeção técnica, refatoração e validação automatizada pelos integrantes do grupo.

Esta seção responde à questão central da investigação:

> *"Em que etapas da construção de um compilador a IA generativa foi mais útil e onde ela introduziu erros que exigiram correção humana?"*

---

## 7.1 Etapas em que a IA generativa foi mais útil

A produtividade obtida com o uso da IA mostrou-se diretamente proporcional ao grau de formalização prévia do problema:

1. **Estruturação de código repetitivo (*boilerplate*) e estruturas de dados:** A geração das classes imutáveis da AST (`@dataclass` em `src/ast_nodes.py`), da hierarquia de exceções (`src/errors.py`) e do formatador tabular da CLI (`src/__main__.py`) ocorreu com alta precisão, pois envolvia padrões idiomáticos bem estabelecidos em Python.
2. **Tradução mecânica de especificações formais:** Uma vez definidas pelo grupo a gramática EBNF e a tabela de transições do autômato em `docs/gramatica.md`, a IA converteu rapidamente cada regra não-terminal em métodos recursivos (`src/parser.py`) e cada par `(estado, classe)` no dicionário `TRANSICOES` (`src/lexer.py`).
3. **Expansão da suíte de testes e casos de borda:** A IA acelerou a criação dos 325 testes automatizados (`tests/validos/` e `tests/invalidos/`), sugerindo combinações de borda para laços com 0, 1 e $N$ iterações, aninhamento de blocos e validação parametrizada dos exemplos de erro.

---

## 7.2 Onde a IA introduziu erros ou falhas conceituais (exemplos concretos)

Embora eficiente na escrita sintática de código Python, a IA tende a aplicar heurísticas da **linguagem de implementação** (Python) que violam a **semântica formal da linguagem-objeto** (MiniLang), além de adotar estratégias ingênuas de recuperação de erros. A seguir, documentamos quatro casos concretos identificados e corrigidos durante a revisão do grupo.

### Exemplo 1: Subtipagem `bool` $\subset$ `int` no sistema de tipos do Python (`src/interpreter.py`)

- **Problema introduzido pela IA:** Na primeira versão do verificador de tipos do interpretador, a IA gerou checagens utilizando `isinstance(value, int)`. Em Python, `bool` é subclasse de `int` (`isinstance(True, int) == True` e `True + 1 == 2`). Como consequência, o interpretador aceitava operações semanticamente inválidas na MiniLang, como `true + 1`, `-true`, `1 == true` e `while (1) { ... }`.
- **Correção humana e justificativa:** Substituímos todas as verificações de tipo por comparação estrita de identidade de classe (`type(value) is int` e `type(value) is bool`), isolando o sistema de tipos da linguagem-objeto do modelo de herança da linguagem hospedeira:

```python
# Trecho revisado em src/interpreter.py (linhas 51-62 e 246-254)
def type_name(value: Value) -> str:
    if type(value) is bool:
        return "bool"
    if type(value) is int:
        return "int"
    raise RuntimeError(f"valor de tipo desconhecido: {value!r}")

# Na avaliação de operadores aritméticos e relacionais (eval_bin_op):
if type(left) is not int or type(right) is not int:
    raise TypeMismatchError(
        f"operador '{op}' exige int e int, mas recebeu "
        f"{type_name(left)} e {type_name(right)}",
        node.line, node.col)
```

### Exemplo 2: Semântica da divisão inteira (`//` vs. truncamento para zero) (`src/interpreter.py`)

- **Problema introduzido pela IA:** Para implementar o operador `/`, a IA utilizou diretamente o operador `left // right` do Python. Contudo, o `//` do Python realiza divisão inteira com arredondamento para $-\infty$ (*floor division*), resultando em `-7 // 2 == -4`. Na especificação da MiniLang (alinhada a C e Java), a divisão inteira deve truncar em direção a zero (`-7 / 2 == -3`). Além disso, usar `int(left / right)` introduziria perda de precisão por ponto flutuante em inteiros grandes.
- **Correção humana e justificativa:** Implementamos a função `truncated_division`, que opera sobre os valores absolutos (onde piso e truncamento coincidem) e restaura o sinal algebricamente:

```python
# Trecho revisado em src/interpreter.py (linhas 273-286)
def truncated_division(a: int, b: int) -> int:
    quotient = abs(a) // abs(b)
    if (a < 0) != (b < 0):
        return -quotient
    return quotient
```

### Exemplo 3: Regra do maior casamento e rejeição de números mal formados (`src/lexer.py`)

- **Problema introduzido pela IA:** Em implementações genéricas de analisadores léxicos com retrocesso (*backtracking*) para o último estado de aceitação, a entrada `1x` faz o autômato aceitar `INT(1)` ao ler `1`, recuar ao encontrar `x` e emitir um segundo token `IDENT(x)`. Na MiniLang, identificadores não podem iniciar com dígitos e a concatenação `1x` deve ser rejeitada já na análise léxica.
- **Correção humana e justificativa:** Eliminamos o retrocesso no laço `tokenize()` e introduzimos o estado não-final `NUM_MAL_FORMADO` na tabela `TRANSICOES`. Ao ler uma letra ou `_` imediatamente após dígitos (`EM_INT`), o AFD transita para `NUM_MAL_FORMADO`, consome o restante do lexema inválido para diagnóstico completo e dispara `LexicalError`:

```python
# Trecho revisado em src/lexer.py (linhas 163-171 e 254-269)
(EM_INT, DIGITO): EM_INT,
(EM_INT, LETRA): NUM_MAL_FORMADO,
(EM_INT, SUBLINHADO): NUM_MAL_FORMADO,
(NUM_MAL_FORMADO, LETRA): NUM_MAL_FORMADO,
(NUM_MAL_FORMADO, DIGITO): NUM_MAL_FORMADO,
(NUM_MAL_FORMADO, SUBLINHADO): NUM_MAL_FORMADO,
```

### Exemplo 4: Erros em cascata na sincronização em modo pânico (`src/parser.py`)

- **Problema introduzido pela IA:** No rascunho inicial da recuperação em modo pânico (`sincronizar()`), a IA incluiu `TokenType.IDENT` isolado como token de sincronização, partindo da premissa de que atribuições começam por identificador. Porém, identificadores também ocorrem no interior de expressões: em um comando inválido como `print x;` (sem parênteses), o parser descartava `print`, parava em `x` e tentava analisá-lo como atribuição, gerando um segundo erro falso (`esperado '='`). Adicionalmente, o `;` interno do cabeçalho do `for` interrompia prematuramente a sincronização, e um `}` sobrando no nível global podia causar laço sem progresso.
- **Correção humana e justificativa:** Refinamos `sincronizar()` para exigir *lookahead* de dois tokens (`IDENT` seguido de `=`), criamos `recuperar_cabecalho()` para isolar erros dentro de parênteses de `if`/`while`/`for` e adicionamos uma guarda de progresso (`if self.pos == inicio: self.advance()`) em `lista_de_comandos()`:

```python
# Trecho revisado em src/parser.py (linhas 383-402)
def sincronizar(self) -> None:
    while not self.check(T.EOF):
        if self.check(T.SEMI):
            self.advance()
            return
        if self.check(T.RBRACE, T.PRINT, T.IF, T.WHILE, T.FOR, T.LBRACE):
            return
        if self.check(T.IDENT) and self.seguinte().type == T.ASSIGN:
            return
        self.advance()
```

---

## 7.3 Fundamentação teórica e decisões de projeto

Cada módulo do compilador materializa conceitos formais estudados na disciplina, orientando tanto as escolhas adotadas quanto o descarte de alternativas:

- **Linguagens Regulares e Autômatos Finitos Determinísticos (Lexer):** Com base no Teorema de Kleene e nas construções de Thompson e de subconjuntos, a união das expressões regulares dos tokens da MiniLang define uma linguagem regular reconhecível por um AFD. Optamos por codificar explicitamente a tabela de transições (`TRANSICOES`) em vez de utilizar o módulo `re` de Python, garantindo determinismo em tempo $O(n)$, aplicação estrita da regra do maior casamento (*maximal munch*) e equivalência formal entre a tabela documentada e o código. Palavras reservadas são resolvidas após a aceitação em `EM_IDENT` via tabela de consulta, evitando a explosão de estados sem alterar a linguagem reconhecida.
- **Gramáticas Livres de Contexto e Análise Preditiva LL(1) (Parser):** A gramática em EBNF foi projetada sem recursão à esquerda e sem ambiguidades: a precedência entre operadores foi estratificada em seis níveis de não-terminais (`igualdade` $\rightarrow$ `relacional` $\rightarrow$ `aditiva` $\rightarrow$ `multiplicativa` $\rightarrow$ `unaria` $\rightarrow$ `primaria`), a associatividade à esquerda foi obtida convertendo repetições `{ ... }` em laços `while` com acumulação à esquerda, e o problema clássico do *dangling else* foi eliminado exigindo blocos com chaves `{ ... }` em todos os corpos de `if`, `else`, `while` e `for`. Descartamos analisadores ascendentes (`LR(1)`/`LALR(1)`), pois exigiriam geradores externos e tabelas `ACTION/GOTO` opacas que dificultariam a emissão de mensagens de erro contextualizadas em português.
- **Árvore Sintática Abstrata vs. Concreta (AST):** Enquanto a árvore de derivação concreta preserva símbolos auxiliares da gramática (parênteses, ponto e vírgula, chaves e cadeias de produções unitárias), a AST retém apenas os construtos com significado operacional, codificando a ordem de avaliação na própria topologia da árvore.
- **Semântica Operacional *Big-Step* e Indecidibilidade (Interpretador):** A execução foi formalizada por regras de inferência natural ($\langle c, \sigma \rangle \Downarrow \sigma'$) sobre um ambiente $\sigma$ implementado como tabela hash de escopo único ($O(1)$ médio). Optamos pela verificação semântica dinâmica em vez de análise estática para manter um único percurso sobre a AST e tratar uniformemente erros que só se manifestam em tempo de execução (como divisão por zero em expressões calculadas). Por fim, como a MiniLang possui aritmética inteira ilimitada e laços condicionais (`while`), ela é Turing-completa e herda a indecidibilidade do **Problema da Parada**; assim, em vez de tentar provar terminação estaticamente, adotamos um limitador prático de iterações (`max_iterations = 100_000`) que interrompe execuções divergentes com `LoopLimitError`.

---

## 7.4 Síntese conclusiva

A experiência demonstrou que a IA generativa atua como um acelerador expressivo na estruturação de código, na escrita de testes e na transcrição de regras formais já estabilizadas, mas **não substitui o domínio teórico do engenheiro de compiladores**. Todas as falhas críticas detectadas — vazamento de subtipagem da linguagem hospedeira, semântica de arredondamento, retrocesso indevido no autômato e sincronização ruidosa no parser — exigiram fundamentação em teoria de autômatos, gramáticas LL(1) e semântica de linguagens para serem diagnosticadas e corrigidas.