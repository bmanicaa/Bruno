# ESPECIFICAÇÃO TÉCNICA: MODALIDADE LACUNAS (`Filters/Modalidades/Lacunas.md`)

Esta especificação define o padrão determinístico e livre de ambiguidades para a geração e correção de **Exercícios de Preenchimento de Lacunas (Lacunas / 穴埋め)** para qualquer aula do currículo de japonês (N5 e níveis superiores).

---

## ⛔ 1. REGRAS INVIOLÁVEIS (HARD RULES)

1. **Princípio do Foco na Matéria Vigente (Escopo de Avaliação):**
   - A modalidade **Lacunas** testa **exclusivamente** a gramática, partículas, conjugações e vocabulário **novos da Aula X** — os itens listados nos campos `grammar`, `kanji`, `focus_vocab` e `anki_vocab` da Aula X em `JLPTN5.md` (ou ementário correspondente).
   - É **estritamente proibido** colocar lacunas que cobrem ou pontuem itens gramaticais ou vocabulário ensinados exclusivamente em aulas futuras (X+1 em diante).
   - **Exceção para Aulas de Consolidação:** Nas aulas de consolidação (ex: Aula 5, 9, 13, 18, 26, 32), o escopo avaliado abrange todos os itens introduzidos na respectiva fase/bloco de aulas recém-concluído.

2. **Distinção Obrigatória: Conteúdo TESTADO vs. Conteúdo de SCAFFOLDING:**
   - **Conteúdo TESTADO (as lacunas `[ ___ ]`):** Apenas itens novos da Aula X. A resposta esperada na lacuna e pontuada deve exigir a aplicação ativa de um termo que está no `focus_vocab` ou `anki_vocab` da Aula X. É EXPRESSAMENTE PROIBIDO exigir palavras como resposta que não estão formalmente na Aula X.
   - **Conteúdo de SCAFFOLDING (frase-contexto ao redor da lacuna):** Pode utilizar livremente vocabulário e gramática cumulativos (Aulas 1 a X).
   - **ATENÇÃO CRÍTICA / ERRO FATAL:** A palavra usada como scaffolding TAMBÉM deve pertencer ao inventário cumulativo (Aulas 1 a X). A IA NÃO pode introduzir, mesmo como contexto de fundo ou pegadinha, vocabulário inédito. Exemplos de ERROS cometidos: usar おはよう, これ ou しゃいん antes de serem ensinados. Verifique CADA palavra contra a Regra 3.1 de `JLPTN5.md`.
   - **Princípio da Carga Cognitiva (Comprehensible Input / i+1):** O scaffolding deve formar frases naturais, porém a estrutura geral da frase NÃO deve ser complexa ao ponto de ofuscar a lacuna. A energia mental do aluno deve ser gasta resolvendo a lacuna, não decifrando o contexto. O contexto deve ser perfeitamente claro (i+1). O scaffolding **nunca** é pontuado.

3. **Política de Furigana Universal ("Sempre Furigana em Todo Kanji"):**
   - **Garantia de Furigana Universal Irrestrito:** TODO e QUALQUER kanji que aparecer em qualquer lugar do caderno de lacunas (frases-contexto, enunciados, opções, dicas, gabarito e explicações) **DEVE carregar a tag `<ruby>` obrigatoriamente, em todas as ocorrências, sem exceção**. Esta regra é consistente com a política global de furigana definida na Regra 11 de `JLPTN5.md`.
   - **Objetivo Pedagógico:** A modalidade Lacunas visa o treino puro e sem fricção da sintaxe, uso de partículas, conjugações e escolha lexical. A decodificação ou leitura memorizada do kanji **NUNCA** deve atuar como barreira cognitiva ou causa de erro nesta modalidade.
   - **Regra de Aplicação por Palavra Inteira:** A tag `<ruby>` é sempre aplicada sobre a palavra inteira (ex: `<ruby>日本語<rt>にほんご</rt></ruby>`), nunca dividida kanji por kanji.

4. **Sintaxe Determinística de Dicas nas Lacunas (Inline Hint Protocol):**
   - Toda lacuna deve ser identificada por colchetes numerados acompanhados por uma dica in-line em português entre parênteses:
     - **Partícula:** `[ ___ 1 ___ ] (partícula)`
     - **Vocabulário:** `[ ___ 2 ___ ] (dica: "livro")`
     - **Forma Gramatical:** `[ ___ 3 ___ ] (forma: negativo cortês de 食べる)`
     - **Completação Sintática:** `[ ___ 4 ___ ] (expressar razão / causa)`

5. **Zero Romaji:** Todo texto em japonês utiliza exclusivamente Kana + Kanji com furigana HTML. O uso de Romaji é expressamente proibido em qualquer seção do caderno ou gabarito.

6. **Campos de Resposta Digitáveis (`> `):**
   - Todas as questões contêm obrigatoriamente uma linha antecedida pelo caractere de citação `> ` para digitação limpa em qualquer editor Markdown.

7. **Local de Salvamento:**
   - O caderno de exercícios é gerado em Markdown no caminho `Practice/N5_P{X}_Lacunas.md`.

---

## ⚙️ 2. TAXONOMIA DE QUESTÕES (AS 4 SEÇÕES FIXAS DAS LACUNAS)

Todo caderno de exercícios de lacunas gerado deve conter exatamente as 4 seções a seguir, totalizando **100 pontos** (25 pontos por seção):

| Seção | Nome da Seção | Foco Pedagógico | Formato do Desafio | Pontuação |
|---|---|---|---|---|
| **Seção 1** | **Lacunas de Partícula & Conectores** (助詞・接続詞の穴埋め) | Testar a precisão no encaixe de partículas gramaticais e conectores **ensinados na Aula X**. | Frases com `[ ___ ] (partícula)` para identificação da função sintática e escolha da partícula correta. | **25 pts** |
| **Seção 2** | **Lacunas de Vocabulário & Expressões** (語彙の穴埋め) | Testar a evocação ativa do **vocabulário foco e Anki novo da Aula X** em contexto de frase. | Frases com `[ ___ ] (dica: "tradução em PT-BR")` para preenchimento com o termo correto em japonês. | **25 pts** |
| **Seção 3** | **Lacunas de Forma Gramatical & Conjugação** (文法・活用形の穴埋め) | Testar a capacidade de modificar formas de palavras (conjugação verbal/adjetival, formas negativas, corteses, te, etc.) conforme a **gramática da Aula X**. | Frases com `[ ___ ] (forma: instrução gramatical)` exigindo a transformação e encaixe correto do verbo/adjetivo/estrutura. | **25 pts** |
| **Seção 4** | **Lacunas de Completação Sintática & Discurso** (文脈・構文の穴埋め) | Testar a síntese de estruturas gramaticais complexas e expressões de discurso **novas da Aula X** em contextos comunicativos. | Frases ou micro-diálogos com lacunas mais amplas `[ ___ ] (função comunicativa)` para preenchimento com a estrutura/frase completa. | **25 pts** |

---

## ⏱️ 3. ESCALONAMENTO E COMPLEXIDADE POR FASE

O volume de itens e a complexidade estrutural das frases ajustam-se estritamente conforme a fase do currículo descrita em `JLPTN5.md` (ou ementário equivalente):

| Fase | Aulas | Itens por Seção (Seções 1 a 4) | Extensão Média das Frases | Complexidade do Scaffolding & Contexto |
|---|---|---|---|---|
| **Fase 1: Fundações** | 1 a 4 | 5 itens de 5 pts | 4 a 6 palavras | Frases diretas de apresentação, identificação e posse (SOV simples). |
| **Fase 2: Espaço** | 6 a 8 | 5 itens de 5 pts | 5 a 8 palavras | Frases de localização espacial, existência e deslocamento com múltiplos marcadores. |
| **Fase 3: Descrição** | 10 a 12 | 5 itens de 5 pts | 6 a 9 palavras | Frases com modificação adjetival (い / な), gradação e advérbios de intensidade. |
| **Fase 4: Tempo & Desejos** | 14 a 17 | 5 itens de 5 pts | 7 a 10 palavras | Frases temporais, rotinas diárias e expressões de desejo/preferência (`たい`, `欲しい`). |
| **Fase 5: Ações** | 19 a 25 | 5 itens de 5 pts | 8 a 12 palavras | Frases complexas envolvendo conjugações da forma て, permissão, proibição e sequenciamento de ações. |
| **Fase 6: Comunicação** | 27 a 31 | 5 itens de 5 pts | 10 a 14 palavras | Micro-diálogos situacionais com alternância de registros e estruturas subordinadas. |

---

## 🔄 4. ALGORITMO DETERMINÍSTICO DE GERAÇÃO DA IA

Ao receber o comando `"Lacunas Aula X"` ou `"Preencher Lacunas Aula X"`:

1. **Leitura de Escopo e Construção da Lista Branca (Vocabulary Gate — OBRIGATÓRIO):**
   - Abrir `JLPTN5.md` (ou ementário ativo) e extrair os itens da Aula X (`grammar`, `kanji`, `focus_vocab`, `anki_vocab`).
   - Carregar as especificações de cada item nos arquivos de referência em `Content/`.
   - Mapear os conteúdos novos a serem convertidos em lacunas (itens TESTADOS).
   - Carregar o inventário acumulado completo (Aulas 1 a X) para uso como scaffolding — conforme Regra 3.1 de `JLPTN5.md`.
   - **Verificação crítica**: Confirmar que CADA palavra usada no scaffolding pertence ao inventário cumulativo. Palavras fora do inventário são PROIBIDAS, mesmo que pareçam "básicas" (ex: おはよう, これ — só podem ser usadas se já foram ensinadas em Aulas 1..X).

2. **Geração das Frases & Aplicativo do Furigana:**
   - Compor frases naturais e gramaticalmente perfeitas.
   - Posicionar as lacunas exatamente nos pontos correspondentes ao conteúdo novo da Aula X.
   - Aplicar a tag `<ruby>` em **todos os kanji de todas as palavras** do caderno.

3. **Montagem do Arquivo Markdown:**
   - Criar o arquivo `Practice/N5_P{X}_Lacunas.md`.
   - Inserir o cabeçalho de Metadados e indicar o status `⏳ Pendente`.
   - Adicionar as 4 Seções respeitando a Taxonomia e a Sintaxe de Dicas.
   - Incluir ao final a seção oculta de Gabarito e Explicações Didáticas via `<details><summary>...</summary>`.

4. **Confirmação no Chat:**
   - Responder no chat informando que o caderno `Practice/N5_P{X}_Lacunas.md` foi gerado com sucesso, apresentando o número de lacunas e instruções de preenchimento.

---

## 📝 5. FLUXO DE CORREÇÃO INTERATIVA E AVALIAÇÃO (`"Corrigir Lacunas Aula X"`)

Ao receber o comando `"Corrigir Lacunas Aula X"` ou `"Avalie o Practice/N5_PX_Lacunas.md"`:

1. **Leitura do Caderno:**
   - A IA abre e lê o arquivo `Practice/N5_P{X}_Lacunas.md`.
   - Extrai as respostas fornecidas pelo estudante nas linhas antecedidas por `> `.

2. **Cálculo da Nota (0 a 100 Pts):**
   - Compara cada resposta com a chave de correção do gabarito.
   - Atribui os pontos devidos (cada item vale 5 pts, totalizando 100 pts nas 4 seções).
   - Aceita variações ortográficas válidas em hiragana/katakana/kanji correto, desde que a estrutura gramatical e a partícula alvo estejam 100% corretas.

3. **Atualização do Arquivo Local:**
   - A IA edita o cabeçalho de `Practice/N5_P{X}_Lacunas.md` alterando o status para `✅ Concluído (Nota: YY/100)`.

4. **Feedback Didático no Chat (Diagnóstico de Causa Raiz):**
   - A IA publica no chat um relatório contendo:
     - **Nota Final:** YY/100 (com detalhamento por seção).
     - **Análise Erro a Erro:** Para cada erro, a IA **não deve apenas dar a resposta certa**. Ela deve diagnosticar a *causa do erro sintático* (ex: "Você usou に, indicando que pensou no destino, mas o verbo pede を porque a ação ocorre NO objeto").
     - **Diagnóstico de Padrão:** Se o aluno errar múltiplas vezes o mesmo conceito, a IA deve apontar o padrão e sugerir uma revisão pontual.

---

## 🏗️ 6. TEMPLATE CANÔNICO DE SAÍDA (`Practice/N5_P{X}_Lacunas.md`)

O arquivo gerado deve seguir **exatamente** a estrutura esquemática abaixo. Todos os placeholders entre `[COLCHETES]` devem ser substituídos pela IA com conteúdo real extraído do ementário da aula solicitada. **Nenhum exemplo concreto é fornecido neste template** — a IA deve criar todas as questões e respostas do zero com base no escopo da aula.

```markdown
# 🧩 EXERCÍCIO DE LACUNAS: AULA [X] — [TÍTULO DA AULA]

> **Nível:** [NÍVEL DO EMENTÁRIO — ex: JLPT N5]
> **Modalidade:** Lacunas (穴埋め - Preenchimento de Frases)
> **Escopo Avaliado:** Aula [X] (conteúdo novo: [N] gramática, [N] partículas, [N] vocabulário)
> **Política de Furigana:** Universal Irrestrito (todos os kanji possuem furigana <ruby>)
> **Tempo Estimado:** ~15 a 20 minutos
> **Status:** ⏳ Pendente

---

## 📝 SEÇÃO 1: LACUNAS DE PARTÍCULA & CONECTORES (25 PONTOS)

Preencha a lacuna `[ ___ ]` com a partícula ou conector adequado **ensinado na Aula [X]**:

[GERAR 5 QUESTÕES. Cada questão segue este formato esquemático:]

[N]. <ruby>[PALAVRA_SCAFFOLDING]<rt>[LEITURA]</rt></ruby> [ ___ N ___ ] (partícula) <ruby>[PALAVRA_SCAFFOLDING]<rt>[LEITURA]</rt></ruby> [TERMINAÇÃO_SCAFFOLDING]。
   > Resposta [N]: 

[NOTAS PARA A IA GERADORA:]
- A lacuna DEVE exigir uma partícula ou conector NOVO da Aula [X].
- O scaffolding ao redor da lacuna pode usar vocabulário cumulativo (Aulas 1 a [X]).
- Aplicar furigana <ruby> em TODA palavra com kanji, sem exceção.

---

## 📝 SEÇÃO 2: LACUNAS DE VOCABULÁRIO & EXPRESSÕES (25 PONTOS)

Preencha a lacuna `[ ___ ]` com o vocabulário correto em japonês **da Aula [X]** conforme a dica:

[GERAR 5 QUESTÕES. Cada questão segue este formato esquemático:]

[N]. [FRASE_SCAFFOLDING_COM_FURIGANA] [ ___ N ___ ] (dica: "[TRADUÇÃO_PT-BR_DO_VOCAB_ALVO]") [CONTINUAÇÃO_SCAFFOLDING]。
   > Resposta [N]: 

[NOTAS PARA A IA GERADORA:]
- A lacuna DEVE exigir um termo de vocabulário NOVO da Aula [X] (focus_vocab ou anki_vocab).
- A dica em português deve ser suficiente para o aluno identificar a palavra japonesa correta.

---

## 📝 SEÇÃO 3: LACUNAS DE FORMA GRAMATICAL & CONJUGAÇÃO (25 PONTOS)

Complete a lacuna `[ ___ ]` adaptando a forma gramatical exigida **pela Aula [X]**:

[GERAR 5 QUESTÕES. Cada questão segue este formato esquemático:]

[N]. [FRASE_SCAFFOLDING_COM_FURIGANA] [ ___ N ___ ] (forma: [INSTRUÇÃO_GRAMATICAL — ex: "negativo cortês de [VERBO]", "passado de [ADJ]", etc.])。
   > Resposta [N]: 

[NOTAS PARA A IA GERADORA:]
- A lacuna DEVE exigir uma transformação gramatical conforme as REGRAS NOVAS da Aula [X].
- A instrução entre parênteses deve ser precisa e inequívoca.

---

## 📝 SEÇÃO 4: LACUNAS DE COMPLETAÇÃO SINTÁTICA & DISCURSO (25 PONTOS)

Preencha a lacuna `[ ___ ]` com a estrutura gramatical completa **da Aula [X]** para dar sentido à frase:

[GERAR 5 QUESTÕES. Cada questão segue este formato esquemático:]

[N]. [FRASE_OU_MICRO-DIÁLOGO_SCAFFOLDING_COM_FURIGANA] [ ___ N ___ ] (expressar [FUNÇÃO_COMUNICATIVA — ex: "concordância", "razão/causa", "pedido cortês", etc.])。
   > Resposta [N]: 

[NOTAS PARA A IA GERADORA:]
- A lacuna DEVE exigir uma ESTRUTURA GRAMATICAL COMPLETA nova da Aula [X].
- A resposta esperada pode conter múltiplas palavras (ex: uma oração subordinada, uma forma verbal composta).

---

## 🔍 GABARITO & EXPLICAÇÕES

<details>
<summary><b>👉 Clique aqui para abrir o Gabarito Oficial e Explicações</b></summary>

### Gabarito Detalhado:

[A IA DEVE gerar o gabarito completo com a seguinte estrutura para CADA seção:]

#### Seção [N]: [NOME_DA_SEÇÃO]
[N]. **Resposta:** [RESPOSTA_CORRETA_EM_JAPONÊS] — *Explicação: [JUSTIFICATIVA_GRAMATICAL_EM_PT-BR, explicando POR QUE esta é a resposta correta e qual regra da Aula [X] fundamenta a escolha.]*

</details>
```
