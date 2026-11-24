# Diário de bordo

Registro do andamento por sprint (ver docs/PLANO.md), incluindo o uso de IA generativa (o que foi pedido, o que
foi aceito, o que foi reescrito e por quê).

**Integrantes:** Rafael Henrique Barreto Martins, David Carvalho, Gabriel Lopes

## Sprint 0 — Fundação (17/11/2026)

### O que foi feito
- Definição do plano de sprints (docs/PLANO.md).
- Estrutura do repositório conforme o enunciado.
- Gramática EBNF, tabela de precedência e 5 exemplos comentados (docs/gramatica.md).
- Contratos entre as fases: tipos de token, nós da AST, hierarquia de erros e API do
  interpretador.

## Sprint 1 — Núcleo do compilador (17/11/2026 a 20/11/2026)

### O que foi feito
- Lexer guiado por AFD, parser descendente recursivo, AST, interpretador e CLI.
- Testes de cada fase, testes de laços e de laço infinito, catálogo de erros e CI.

### Uso de IA
| Pedido à IA | Resultado | Decisão do grupo |
|---|---|---|
| Propor divisão em sprints | Plano em 5 sprints | Aceito com ajustes de datas |
| Rascunho da EBNF com precedência | Gramática LL(1) com um não-terminal por nível | Aceito após revisão formal de conjuntos FIRST/FOLLOW e não associatividade das comparações |
| Lexer guiado por AFD + tabela de transições | Código com 26 estados; tabela do documento gerada a partir do dicionário de transições do código | Reescrito parcialmente: removido retrocesso e adicionado estado `NUM_MAL_FORMADO` para rejeitar `1x` |
| Parser descendente recursivo com modo pânico | Uma função por não-terminal; mensagens "esperado X, encontrado Y" | Reescrito parcialmente: ajustada sincronização para `IDENT =`, recuperação local de cabeçalho e guarda de progresso |
| Interpretador e tabela de símbolos | Despacho por tipo de nó; verificação de tipos em tempo de execução | Reescrito parcialmente: trocado `isinstance` por `type(v) is ...` e implementada `truncated_division` |
| CLI, testes de laço, catálogo de erros, CI | `python -m src` com `--tokens`/`--ast`; 306 testes passando | Aceito após conferência manual das saídas e ajuste de mensagens de diagnóstico |

### Pontos em que a IA quase errou ou precisou de correção (material para o relatório)
Confirmados pelo grupo na revisão do código-fonte (`src/`):

1. **`bool` é subclasse de `int` em Python.** Com `isinstance(v, int)`, a MiniLang aceitaria
   `true + 1`, `-true` e `1 == true`. O interpretador usa `type(v) is int`. Conceito: sistema de
   tipos da linguagem-objeto ≠ sistema de tipos da linguagem de implementação.
2. **Maximal munch com retrocesso transformaria `1x` em `INT(1) IDENT(x)`.** O lexer foi feito
   sem retrocesso e com um estado não final `NUM_MAL_FORMADO`, para que `1x` seja erro léxico.
   Conceito: AFD, estados de aceitação, regra do casamento mais longo.
3. **Sincronizar o modo pânico em qualquer identificador causa erros em cascata** (`print x;`
   gerava um segundo erro falso "esperado '='"). Solução: sincronizar só em `IDENT` seguido de `=`.
   Conceito: FIRST(comando) vs. tokens que também aparecem no meio de expressões.
4. **`;` dentro do cabeçalho do `for`** confundia a sincronização geral; foi criada uma
   recuperação local que pula até o `)` do cabeçalho. Conceito: tokens de sincronização dependem
   do contexto sintático.
5. **Recuperação sem progresso** (um `}` sobrando) levaria a laço infinito no parser; a
   recuperação agora garante consumir ao menos um token.
6. **Divisão inteira:** `//` do Python arredonda para baixo (`-7 // 2 == -4`); a MiniLang
   trunca em direção a zero (`-7 / 2 == -3`).
7. **Erro de contagem de linha** num comentário de exemplo de erro ("linha 5" quando era 4) e
   contagem errada de nós (15 em vez de 17) na árvore concreta do relatório — corrigidos.

### Limitação conhecida (decisão consciente)
- Verificação semântica dinâmica: `if (false) { x = 1 + true; }` não gera erro, porque o ramo
  nunca executa. Discutido em docs/relatorio/05_interpretador.md.

### Decisões técnicas
- Comparações não associativas (`1 < 2 < 3` é erro sintático) para não misturar `bool` com `int`.
- Divisão inteira truncada em direção a zero (como em C/Java), não `//` do Python (que arredonda para baixo).
- Comentários de bloco `/* */` como extensão, para que exista o erro "comentário não fechado".
- Tipo da variável fixado na primeira atribuição.

### Dificuldades / próximos passos
- **Dificuldades:** Evitar vazamentos semânticos do Python (tipagem dinâmica de `bool` e divisão inteira por piso) e calibrar os pontos de sincronização do parser para não gerar diagnósticos falsos em cascata.
- **Próximos passos:** Consolidar o catálogo de erros, ampliar testes de borda e automatizar a execução via GitHub Actions.

## Sprint 2 — Erros e testes (21/11/2026 a 23/11/2026)

### O que foi feito
- Catálogo de erros por categoria (léxico, sintático, semântico) com mensagem, causa e
  exemplo de cada um (docs/relatorio/06_catalogo_erros.md).
- 9 programas de demonstração em exemplos/erros/, 3 por categoria, cada um com o erro
  esperado (categoria, linha e coluna) anunciado no comentário da primeira linha.
- Novo teste tests/invalidos/test_exemplos_de_erro.py: roda cada exemplo pela CLI e
  confere se o erro produzido é o anunciado (categoria, linha, coluna, código de saída 1,
  sem traceback). Assim o catálogo e os exemplos não ficam desatualizados.
- Suíte de borda dos laços (tests/validos/test_lacos.py): zero, uma e N iterações, passo
  diferente de 1, laço decrescente, variável de controle alterada no corpo, valor depois
  do laço, laços aninhados.
- Laço infinito (tests/invalidos/test_laco_infinito.py): limite exato N (passa) e N+1
  (erro), contadores independentes por laço, saída anterior ao erro preservada.
- CI no GitHub Actions com Python 3.10 e 3.12 (o 3.9 saiu do runner Ubuntu atual).
- Total: 325 testes passando.

### Uso de IA
| Pedido à IA | Resultado | Decisão do grupo |
|---|---|---|
| Teste que valide os exemplos de erro contra o comentário de cada arquivo | Teste parametrizado com 19 casos | Aceito após verificação das linhas, colunas e códigos de saída esperados |
| Atualizar README e diário da sprint | Correção da versão do Python no README e este registro | Aceito e complementado pelo grupo com as decisões técnicas de cada sprint |

### Dificuldades / próximos passos
- **Dificuldades:** Garantir sincronia exata entre os números de linha dos arquivos em `exemplos/erros/` e as saídas documentadas no catálogo de erros.
- **Próximos passos:** Concluir a redação do relatório final (introdução e análise crítica do uso de IA), atualizar `declaracao_IA.md` e gerar `docs/relatorio.pdf`.

## Sprint 3 — Relatório (24/11/2026 a 27/11/2026)

### O que foi feito
- Revisão técnica completa das seções de análise léxica (`02`), análise sintática (`03`), AST (`04`), interpretador (`05`) e catálogo de erros (`06`) em confronto com o código-fonte em `src/`.
- Redação da introdução (`docs/relatorio/01_introducao.md`) contextualizando o cenário educacional e a arquitetura em estágios.
- Redação da análise crítica do uso de IA generativa e fundamentação teórica (`docs/relatorio/07_uso_de_ia.md`), respondendo à pergunta de pesquisa com 4 exemplos concretos de código revisados pelo grupo.
- Atualização de `docs/diario_de_bordo.md` e `declaracao_IA.md` em conformidade com a Portaria CNPq nº 2.664/2026.
- Compilação do documento final unificado em `docs/relatorio.pdf`.

### Uso de IA
| Pedido à IA | Resultado | Decisão do grupo |
|---|---|---|
| Estruturar introdução e seção de análise crítica do uso de IA a partir dos registros do diário e do código em `src/` | Textos de `01_introducao.md` e `07_uso_de_ia.md` com exemplos reais do projeto | Revisado e validado pelo grupo para garantir fidelidade ao código implementado e aos conceitos da disciplina |

### Dificuldades / próximos passos
- **Dificuldades:** Sintetizar a análise crítica da IA em 2 a 3 páginas mantendo rigor teórico e exemplos reais de código.
- **Próximos passos:** Gravar o vídeo de demonstração (`docs/apresentacao.mp4`) até 29/11/2026 e ensaiar todas as fases para a arguição individual de 01/12/2026.

## Sprint 4 — Vídeo e arguição (27/11/2026 a 30/11/2026)

_preencher após gravação do vídeo_