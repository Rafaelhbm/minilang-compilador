# 1. Introdução

Este relatório apresenta o projeto, a fundamentação teórica, a implementação e a análise crítica do desenvolvimento do compilador-intérprete **MiniLang**, elaborado para a II Avaliação da disciplina de **Linguagens Formais e Compiladores** (Curso de Ciência da Computação — Universidade Tiradentes, sob orientação da Prof.ª Layse Santos Souza).

## 1.1 Contexto e motivação

No ensino introdutório de compiladores, estudantes frequentemente enfrentam uma barreira conceitual durante a transição entre a teoria de linguagens formais (expressões regulares, autômatos finitos e gramáticas livres de contexto) e a execução efetiva de um programa. Quando as etapas são estudadas de forma isolada, sem uma ferramenta que torne visíveis as estruturas intermediárias, muitos alunos perdem o engajamento antes de compreender como o código-fonte se transforma em computação.

Para atender à demanda de uma plataforma educacional voltada a esse público, projetamos e implementamos o compilador-intérprete da **MiniLang**: uma linguagem imperativa didática, minimalista e rigorosamente especificada, cujo pipeline permite inspecionar cada fase de tradução e execução de ponta a ponta.

## 1.2 Escopo da linguagem MiniLang

A MiniLang foi definida formalmente (`docs/gramatica.md`) para cobrir os mecanismos fundamentais de uma linguagem estruturada sem introduzir complexidade acidental:

- **Tipos de dados:** inteiros (`int`, ex.: `42`) e booleanos (`bool`, `true` e `false`), com tipagem forte e sem coerção implícita entre tipos.
- **Variáveis e escopo:** atribuição dinâmica com fixação de tipo na primeira escrita, operando sobre uma tabela de símbolos de escopo global único.
- **Operadores e precedência:** operadores aritméticos (`+`, `-`, `*`, `/`, além de `-` unário), relacionais (`<`, `>`, `<=`, `>=`) e de igualdade (`==`, `!=`), organizados em níveis hierárquicos de precedência e associatividade.
- **Estruturas de controle e saída:** blocos delimitados por chaves (`{ ... }`), condicionais (`if` / `else`), laços condicionais (`while`), laços contados com três cláusulas obrigatórias (`for`) e comando de saída (`print`).
- **Diagnóstico de erros:** detecção precisa (com linha, coluna e indicador visual no código-fonte) nas fases léxica, sintática e semântica, além de proteção contra laços infinitos por limite configurável de iterações.

## 1.3 Arquitetura do compilador-intérprete

O sistema foi implementado em Python 3 utilizando exclusivamente a biblioteca padrão no núcleo do compilador (e `pytest` para a suíte automatizada de 325 testes). A arquitetura segue o modelo clássico em estágios desacoplados, onde cada módulo comunica-se com o seguinte por meio de contratos de dados bem definidos:

```
código-fonte (.ml)
   │  src/lexer.py        Análise léxica: AFD determinístico sem retrocesso
   ▼
lista de tokens (Token)
   │  src/parser.py       Análise sintática: descendente recursivo LL(1) com modo pânico
   ▼
AST (src/ast_nodes.py)
   │  src/interpreter.py  Análise semântica dinâmica e execução sobre a árvore
   ▼
saída padrão / diagnósticos de erro (src/errors.py)
```

A interface de linha de comando (`src/__main__.py`) orquestra esse fluxo e oferece as opções `--tokens` e `--ast` para exibir, respectivamente, a tabela de tokens produzida pelo lexer e a Árvore Sintática Abstrata gerada pelo parser antes da execução do programa.

## 1.4 Organização deste documento

As seções seguintes detalham cada componente do projeto conforme as etapas exigidas:

- **Seção 2 (Análise léxica):** expressões regulares, construção do Autômato Finito Determinístico (AFD), regra do maior casamento e justificativa formal de reconhecimento (`src/lexer.py`).
- **Seção 3 (Análise sintática):** propriedade LL(1) da gramática EBNF, árvores sintáticas concretas, demonstração de precedência e associatividade, recuperação em modo pânico e comparação com análise ascendente LR(1)/LALR(1) (`src/parser.py`).
- **Seção 4 (Árvore Sintática Abstrata):** definição formal dos nós, abstração em relação à árvore concreta e visualização estrutural (`src/ast_nodes.py`).
- **Seção 5 (Interpretador e análise semântica):** estrutura da tabela de símbolos, semântica operacional *big-step*, justificativa de correção e discussão entre verificação dinâmica e análise estática (`src/interpreter.py`).
- **Seção 6 (Catálogo de erros):** taxonomia de erros léxicos, sintáticos e semânticos, demonstrações executadas e estratégia de diagnóstico por fase (`src/errors.py`).
- **Seção 7 (Análise crítica do uso de IA generativa e fundamentação teórica):** resposta à questão de pesquisa do projeto, análise de acertos e falhas da IA com trechos de código revisados e síntese dos conceitos teóricos aplicados.