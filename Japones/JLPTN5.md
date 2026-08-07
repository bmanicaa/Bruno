# JLPTN5.md — JLPT N5 Self-Study Rules & Curriculum (32 Lessons)

## Purpose

This file is the single source of truth for the JLPT N5 self-study program. It defines the **rules** for study sessions and the **32-lesson curriculum** (24 content + 8 consolidation) that turns the raw reference files (`Content/N5_Grammar.md`, `Content/N5_Kanji.md`, `Content/N5_Vocabulary.md`) into a structured, cumulative learning path optimized for a busy adult learner studying **1 lesson per week** with **Anki** support.

## How This System Works

1. **This file (JLPTN5.md)** defines the curriculum: which grammar points, kanji, and vocabulary belong to each lesson, via row references to the data files in `Content/`.
2. **`Filters/Modalidades/Lesson.md`** and **`Filters/HTML/HTML_Lesson.md`** define the lesson pedagogical rules and output specifications: CSS master styling, HTML5 structure, furigana rules, and canonical skeletons for both content and consolidation lessons.
3. **The data files** (`Content/N5_Grammar.md`, `Content/N5_Kanji.md`, `Content/N5_Vocabulary.md`) contain the raw reference data.

**Workflow:** When generating a lesson, the AI must (1) read the lesson definition here in `JLPTN5.md`, (2) open the referenced rows in the data files in `Content/` to extract the raw content, and (3) format the output in HTML following the canonical specifications in `Filters/Modalidades/Lesson.md` and `Filters/HTML/HTML_Lesson.md`.

## Prerequisites

- **Hiragana and Katakana** are assumed to be fully mastered before starting Lesson 1. They are not taught in this curriculum. The student must be able to read all kana fluently.

## Student Profile

- **Occupation:** Medical resident (neurosurgery) — very limited study time
- **Pace:** 1 lesson per week (may extend to 2 weeks during heavy rotations)
- **SRS Tool:** Anki for daily vocabulary reinforcement (~10 min/day)
- **Target session:** ~50-60 minutes per content lesson, ~45 minutes per consolidation lesson

## Rules

1. Never leave any temporary file or script in this repository.
2. The data reference files live in `Content/N5_Grammar.md`, `Content/N5_Kanji.md`, `Content/N5_Vocabulary.md`. They are read-only reference data — do not modify them during a study session.
3. **Cumulative principle:** Lessons build on each other. Lesson N assumes ALL content from lessons 1 to N-1 is mastered. Example sentences and practice questions for lesson N may freely use grammar, kanji, and vocabulary from lessons 1..N, but must NOT use content from lessons N+1 or beyond.
4. **Row references:** Each lesson is defined in the `## Curriculum Data (YAML)` section at the end of this file. The YAML block uses row numbers referencing `Content/N5_Grammar.md`, `Content/N5_Kanji.md`, and `Content/N5_Vocabulary.md`. Before teaching, locate the lesson entry in the YAML block, then open the referenced rows in the data files and read them. For consolidation lessons, use the `scope` field to identify which previous content lessons are being reviewed.
5. **Two lesson types:**
   - **📘 Content lessons** teach new grammar, kanji, and vocabulary following Template A in `Filters/HTML/HTML_Lesson.md`.
   - **🔄 Consolidation lessons** review and reinforce the previous 3-4 content lessons following Template B in `Filters/HTML/HTML_Lesson.md`. They introduce NO new content.
6. **Vocabulary classification:**
   - **Focus (12-15 words):** Fully taught in the lesson body with 4-layer examples, collocations, and nuances.
   - **Anki (6-16 words):** Listed in a reference table. The student adds them to Anki and reviews throughout the week.
7. **Lesson teaching format (content lessons):**
   - **Review (5 min):** Quick recap of the previous lesson's most important points. Show 3-5 review questions. *(Skip for Lesson 1.)*
   - **Grammar (core):** Teach each grammar point — pattern, meaning, usage, contrast, 2-3 example sentences using ONLY cumulative vocabulary.
   - **Kanji:** Present new kanji as **recognition anchors** (âncoras de reconhecimento): glyph + meaning + radical as a mnemonic hook + 2-3 words/compounds using cumulative vocabulary. The reading is learned exclusively through the words — NEVER drill memorized onyomi/kunyomi or stroke counts (JLPT N5 does not test writing). Stroke count appears only as an optional note for handwriting.
   - **Focus Vocabulary:** Present focus words grouped by **semantic theme** with full examples.
   - **Anki Vocabulary:** Present Anki words in a reference table.
   - **Anki card (reading recall engine):** for each kanji word — **front = word in kanji WITHOUT furigana** / **back = kana reading + PT-BR translation**. This is the ONLY place in the system where kanji appears without furigana. Pure-kana words use a simple card (front = kana / back = translation).
   - **Practice (end):** Exercises including **interleaved** questions mixing current and past content.
8. Never use a grammar point in examples before it has been introduced.
9. Teach in **Portuguese (PT-BR)**. Write Japanese examples with kanji + hiragana reading. All explanations, translations, and instructions must be in Portuguese.
10. **Session commands:** 
    - `"Lesson N"` / `"Aula N"` / `"Inicie a aula N"` → gera a aula completa em HTML no Google Drive seguindo `Filters/Modalidades/Lesson.md` e o formato em `Filters/HTML/HTML_Lesson.md`.
    - `"Exercícios Aula N"` / `"Drill Aula N"` → gera o caderno de exercícios interativo em Markdown em `Practice/N5_PN.md` seguindo `Filters/Exercises.md`.
    - `"Reading Aula N"` / `"Leitura Aula N"` → gera o treino de leitura narrativa em HTML (salvo em `Practice/N5_PN_Reading.html` e enviado ao Google Drive) seguindo as regras e fluxos descritos em `Filters/Modalidades/Reading.md` e o formato em `Filters/HTML/HTML_reading.md`. A correção/discussão deste módulo acontece diretamente no chat.
    - `"Corrigir Aula N"` / `"Avalie o Practice/N5_PN.md"` → lê o arquivo de exercícios `Practice/N5_PN.md`, corrige as respostas digitadas pelo estudante, atribui nota e dá feedback detalhado no chat. (Nota: não usado para Reading).
11. **POLÍTICA DE KANJI EM DOIS NÍVEIS (Furigana/Ruby):** Todo texto japonês gerado nas aulas (tabelas de vocabulário, exemplos com 4 camadas, diálogos, exercícios, gabaritos) segue esta regra determinística. A autoridade é a lista de 80 kanji formais de `Content/N5_Kanji.md`, usando a coluna `Aula (intro)` para saber quando cada kanji formal é introduzido.
    - **Nível 1 — Kanji Formal (os 80 da lista):** a partir da SUA aula de introdução (`Aula (intro)` ≤ aula atual), o kanji é de responsabilidade do aluno (escrever + ler) e recebe ruby **apenas na primeira ocorrência por aula**; nas demais ocorrências, escrever sem ruby para ativar a recuperação ativa da memória.
    - **Nível 2 — Kanji de Reconhecimento (todos os demais):** inclui (a) qualquer kanji FORA dos 80 e (b) kanji dos 80 cuja aula de introdução ainda não chegou. Nunca são cobrados para escrita — apenas leitura passiva — e **DEVEM receber ruby em TODA ocorrência, sem exceção**, inclusive em palavras de aulas anteriores.
    **Aplicação (regra por PALAVRA, nunca kanji a kanji):**
    - Se **todos** os kanji da palavra são Nível 1 já introduzidos → ruby só na primeira ocorrência da palavra na aula.
    - Se a palavra contém **qualquer** kanji de Nível 2 → a palavra inteira leva ruby em **toda** ocorrência.
    - O ruby usa a leitura completa da palavra sobre a palavra inteira (para vocabulário, copiar da coluna `Leitura (Kana)` de `Content/N5_Vocabulary.md`). **Nunca** dividir o ruby kanji por kanji — isso quebra leituras irregulares como `今日` = きょう, `大人` = おとな, `時々` = ときどき.
    - A regra cumulativa (regra 3) continua valendo para palavras e gramática; este tratamento de ruby é o que resolve a exposição de kanji.
12. **CONTRATO DE EXPECTATIVA DA AULA (promessa honesta):** Cada aula de conteúdo declara no cabeçalho exatamente quais kanji formais ela ensina (3-4 por aula, conforme `Aula (intro)` em `Content/N5_Kanji.md`). Os kanji formais da aula são ensinados como **âncoras de reconhecimento** (forma → significado, com o radical como gancho mnemônico; a leitura é aprendida nas palavras) — **nunca** cobrar onyomi/kunyomi memorizados nem contagem de traços. Todos os demais kanji que aparecerem na aula são exclusivamente de reconhecimento (leitura) e sempre carregam furigana. **Proibido** criar exercícios que exijam ESCREVER kanji de Nível 2 ou kanji formais ainda não introduzidos; eles só podem ser cobrados em leitura (reconhecimento).
13. **Geração HTML & Upload Direto no Google Drive:** Ao receber a instrução de iniciar uma aula ("Lesson X" / "Aula X"), **NÃO** imprima o texto completo da aula na conversa do chat nem salve arquivos locais permanentes. Em vez disso:
    - (a) Gerar a aula completa em formato HTML5 puro com CSS3 embutido, seguindo rigorosamente a arquitetura e especificações de `Filters/HTML/HTML_Lesson.md`.
    - (b) Salvar temporariamente o código HTML gerado e executar o script de upload para o Google Drive:
      `node "/Users/bmanica/Documents/GitHub/Bruno/Google Workspace/Drive/scripts/upload_to_gdrive.js" "<caminho_do_arquivo_html_temp>" "N5_LX.html"`
      (o script executará a **validação automática de ruby** — regra 11, conforme `Filters/HTML/HTML_Lesson.md` §4.6 — **ANTES** do upload e **BLOQUEARÁ** o envio se o arquivo reprovar em qualquer checagem. Somente arquivos aprovados são enviados para a pasta `Meu Drive > Aulas > Japones` como `N5_LX.html`, sem converter para Google Doc. Se a validação falhar, corrija o HTML conforme `Filters/HTML/HTML_Lesson.md` §4.6 e tente novamente).
    - (c) Após a confirmação do upload, apagar o arquivo temporário local (respeitando a Regra 1 de não deixar arquivos temporários no repositório).
    - (d) Responda no chat com uma mensagem curta de confirmação informando que a aula foi gerada em formato HTML e enviada ao Google Drive com sucesso.
14. **Geração e Correção Interativa de Exercícios (`Practice/`):** Ao receber o comando de exercícios (`"Exercícios Aula X"` / `"Drill Aula X"`), a IA deve gerar o caderno em Markdown no caminho `/Users/bmanica/Documents/GitHub/Bruno/Japones/Practice/N5_PX.md` seguindo rigorosamente a especificação em `Filters/Exercises.md`. O arquivo contém campos de resposta em branco digitáveis (`> `). Quando o estudante solicitar a correção (`"Corrigir Aula X"` / `"Avalie o Practice/N5_PX.md"`), a IA lê o arquivo local, analisa as respostas digitadas pelo aluno após o caractere `>`, fornece nota e feedback didático detalhado no chat e atualiza o status do arquivo.

## Curriculum Structure: 6 Phases

| Phase | Theme | Lessons | Content | Consolidation |
|:---:|---|---|:---:|:---:|
| 1 | **Fundações** — "Quem sou eu" | 1-5 | 4 | 1 |
| 2 | **Espaço** — "Onde estou" | 6-9 | 3 | 1 |
| 3 | **Descrição** — "Como é" | 10-13 | 3 | 1 |
| 4 | **Tempo & Desejos** — "Quando / O que quero" | 14-18 | 4 | 1 |
| 5 | **Ações** — "O que faço" | 19-26 | 6 | 2 |
| 6 | **Comunicação** — "Como me expresso" | 27-32 | 4 | 2 |
| | **Total** | **32** | **24** | **8** |

## Distribution Overview

| Aula | Tipo | Fase | Tema | Gram | Kanji | Foco | Anki | Cum.G | Cum.K | Cum.V |
|:---:|:---:|:---:|---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| 1 | 📘 | 1 | Eu Sou — Copula & Perguntas | 3 | 3 | 15 | 10 | 3 | 3 | 25 |
| 2 | 📘 | 1 | Não Sou — Negação & Posse | 4 | 4 | 15 | 12 | 7 | 7 | 52 |
| 3 | 📘 | 1 | Minha Família & Números | 3 | 3 | 15 | 14 | 10 | 10 | 81 |
| 4 | 📘 | 1 | Meu Mundo — Conexões & Contexto | 4 | 3 | 15 | 10 | 14 | 13 | 106 |
| 5 | 🔄 | 1 | Consolidação — Aulas 1-4 | — | — | — | — | 14 | 13 | 106 |
| 6 | 📘 | 2 | Partículas de Lugar & Movimento | 3 | 4 | 15 | 16 | 17 | 17 | 137 |
| 7 | 📘 | 2 | Existe Aqui — ある・いる & Demonstrativos | 3 | 3 | 15 | 12 | 20 | 20 | 164 |
| 8 | 📘 | 2 | Pela Cidade — Locais & Transporte | 4 | 4 | 15 | 16 | 24 | 24 | 195 |
| 9 | 🔄 | 2 | Consolidação — Aulas 6-8 | — | — | — | — | 24 | 24 | 195 |
| 10 | 📘 | 3 | Adjetivos-い — Descrevendo o Mundo | 3 | 3 | 15 | 12 | 27 | 27 | 222 |
| 11 | 📘 | 3 | Adjetivos-な & Cores | 3 | 4 | 15 | 13 | 30 | 31 | 250 |
| 12 | 📘 | 3 | Mais Descrições & Advérbios | 3 | 3 | 15 | 13 | 33 | 34 | 278 |
| 13 | 🔄 | 3 | Consolidação — Aulas 10-12 | — | — | — | — | 33 | 34 | 278 |
| 14 | 📘 | 4 | Calendário & Datas | 3 | 4 | 15 | 12 | 36 | 38 | 305 |
| 15 | 📘 | 4 | Frequência & Sequência | 3 | 4 | 15 | 11 | 39 | 42 | 331 |
| 16 | 📘 | 4 | Gostos, Desejos & Comida | 4 | 3 | 15 | 15 | 43 | 45 | 361 |
| 17 | 📘 | 4 | Habilidades & Natureza | 3 | 3 | 15 | 15 | 46 | 48 | 391 |
| 18 | 🔄 | 4 | Consolidação — Aulas 14-17 | — | — | — | — | 46 | 48 | 391 |
| 19 | 📘 | 5 | Verbos & Conjugação: Fundamentos | 4 | 3 | 12 | 6 | 50 | 51 | 409 |
| 20 | 📘 | 5 | て-form: Progresso & Experiência | 4 | 4 | 15 | 12 | 54 | 55 | 436 |
| 21 | 📘 | 5 | て-form: Permissão & Estado | 3 | 3 | 15 | 12 | 57 | 58 | 463 |
| 22 | 🔄 | 5 | Consolidação — Aulas 19-21 | — | — | — | — | 57 | 58 | 463 |
| 23 | 📘 | 5 | Verbos do Cotidiano (Parte 1) | 4 | 3 | 15 | 12 | 61 | 61 | 490 |
| 24 | 📘 | 5 | Verbos do Cotidiano (Parte 2) | 4 | 3 | 15 | 12 | 65 | 64 | 517 |
| 25 | 📘 | 5 | Mais Verbos & Objetos do Dia-a-dia | 3 | 3 | 15 | 12 | 68 | 67 | 544 |
| 26 | 🔄 | 5 | Consolidação — Aulas 23-25 | — | — | — | — | 68 | 67 | 544 |
| 27 | 📘 | 6 | Obrigação & Proibição | 4 | 3 | 15 | 10 | 72 | 70 | 569 |
| 28 | 📘 | 6 | Convites & Sugestões | 4 | 3 | 15 | 10 | 76 | 73 | 594 |
| 29 | 📘 | 6 | Comparações & Contrastes | 4 | 3 | 15 | 9 | 80 | 76 | 618 |
| 30 | 🔄 | 6 | Consolidação — Aulas 27-29 | — | — | — | — | 80 | 76 | 618 |
| 31 | 📘 | 6 | Conectando Ideias & Explicações | 4 | 4 | 15 | 11 | 84 | 80 | 644 |
| 32 | 🔄 | — | Revisão Final & Simulado N5 | — | — | — | — | 84 | 80 | 644 |

Total: 84 grammar points, 80 kanji, 644 vocabulary items (todas as linhas do arquivo-fonte atribuídas exatamente uma vez a uma única aula).

---

## Curriculum Data (YAML)

O bloco abaixo define as 32 aulas do currículo em formato estruturado. Os números em `grammar`, `kanji`, `focus_vocab` e `anki_vocab` são referências de linha (row #) aos arquivos em `Content/`. Para aulas de consolidação, `scope` lista as aulas de conteúdo cobertas na revisão.

```yaml
lessons:

  # ═══════════════════════════════════════════
  # FASE 1: FUNDAÇÕES — "Quem sou eu"
  # ═══════════════════════════════════════════

  1:
    type: content
    phase: 1
    title: "Eu Sou — Copula, は & Perguntas"
    objective: "Apresentar-se, afirmar identidade com です/だ, marcar o tópico com は, e formar perguntas com か."
    grammar: [2, 79, 21]
    kanji: [2, 8, 13]
    focus_vocab:
      "Pronomes": [612, 15]
      "Identidade": [375, 172, 116, 492]
      "Básico": [176, 97, 308, 319, 192]
      "Expressões": [133, 94, 90, 91]
    anki_vocab: [113, 114, 237, 297, 471, 487, 231, 202, 212, 472]

  2:
    type: content
    phase: 1
    title: "Não Sou — Negação, Posse & Inclusão"
    objective: "Negar identidade com じゃない, expressar posse com の, e adicionar com も. Aprender prefixos de polidez お/ご."
    grammar: [20, 52, 34, 59]
    kanji: [4, 9, 6, 76]
    focus_vocab:
      "Família (própria)": [57, 132, 17, 16, 445, 194]
      "Família (alheia)": [444, 412, 425, 423]
      "Relações": [255, 470, 320, 280, 573]
    anki_vocab: [404, 405, 411, 417, 418, 256, 248, 439, 426, 440, 427, 441]

  3:
    type: content
    phase: 1
    title: "Minha Família & Números"
    objective: "Contar de 1 a 10.000, usar が como marcador de sujeito, intensificar com とても, e apresentar alternativas com か〜か."
    grammar: [11, 77, 22]
    kanji: [26, 22, 37]
    focus_vocab:
      "Números cardinais": [183, 388, 479, 498, 122, 466, 499, 130, 322, 222]
      "Números grandes": [182, 490, 334, 460, 643]
    anki_vocab: [174, 108, 356, 630, 209, 368, 376, 622, 284, 173, 107, 191, 190, 42]

  4:
    type: content
    phase: 1
    title: "Meu Mundo — Conexões & Contexto"
    objective: "Listar com と (completo) e や (exemplos), limitar com だけ, e perguntar tipo com どんな. Vocabulário de corpo e identidade."
    grammar: [75, 82, 3, 8]
    kanji: [42, 36, 29]
    focus_vocab:
      "Corpo": [33, 340, 349, 142, 303, 129, 557, 29, 484, 422, 239]
      "Perguntas": [71, 72, 84, 85]
    anki_vocab: [184, 421, 640, 178, 258, 530, 548, 642, 207, 377]

  5:
    type: consolidation
    phase: 1
    title: "Consolidação — Aulas 1 a 4"
    scope: [1, 2, 3, 4]

  # ═══════════════════════════════════════════
  # FASE 2: ESPAÇO — "Onde estou"
  # ═══════════════════════════════════════════

  6:
    type: content
    phase: 2
    title: "Partículas de Lugar & Movimento"
    objective: "Dominar に (destino/tempo), で (meio/local de ação) e に/へ (direção), com o primeiro núcleo de verbos de movimento (Verbo-Core)."
    grammar: [48, 5, 51]
    kanji: [3, 24, 38, 35]
    focus_vocab:
      "Verbo-Core": [189, 313, 226, 25, 153]
      "Locais básicos": [186, 161]
      "Posições": [596, 510, 372, 524]
      "Direções": [346, 162]
      "Transporte": [43, 77]
    anki_vocab: [117, 66, 395, 326, 601, 574, 516, 626, 554, 366, 225, 343, 302, 152, 197, 74]

  7:
    type: content
    phase: 2
    title: "Existe Aqui — ある・いる & Demonstrativos"
    objective: "Expressar existência de coisas (がある) e seres vivos (がいる), usar demonstrativos (これ/それ/あれ), e perguntar "por quê" (どうして)."
    grammar: [12, 14, 9]
    kanji: [10, 43, 62]
    focus_vocab:
      "Demonstrativos (isso)": [295, 522, 23, 282, 519, 32]
      "Demonstrativos (qual)": [87, 82, 83]
      "Pré-nominais": [289, 520, 18, 86]
      "Verbos": [24, 201]
    anki_vocab: [3, 4, 517, 518, 278, 279, 288, 163, 394, 275, 350, 565]

  8:
    type: content
    phase: 2
    title: "Pela Cidade — Locais & Transporte"
    objective: "Nomear locais urbanos, meios de transporte, e itens da casa. Usar ね para confirmação, をください para pedir, はどうですか para opiniões e どうやって para perguntar o meio."
    grammar: [47, 61, 81, 10]
    kanji: [25, 52, 41, 57]
    focus_vocab:
      "Locais": [115, 67, 53, 98, 582, 301, 464, 354, 120, 79, 274]
      "Transporte": [314, 549, 164, 62]
    anki_vocab: [513, 637, 299, 321, 455, 21, 205, 590, 558, 325, 81, 324, 367, 555, 159, 45]

  9:
    type: consolidation
    phase: 2
    title: "Consolidação — Aulas 6 a 8"
    scope: [6, 7, 8]

  # ═══════════════════════════════════════════
  # FASE 3: DESCRIÇÃO — "Como é"
  # ═══════════════════════════════════════════

  10:
    type: content
    phase: 3
    title: "Adjetivos-い — Descrevendo o Mundo"
    objective: "Dominar adjetivos-い: forma afirmativa, negativa (〜くない), passada (〜かった), e modificação de substantivos."
    grammar: [16, 65, 37]
    kanji: [11, 32, 33]
    focus_vocab:
      "Tamanho/Forma": [429, 59, 370, 347, 547, 167, 109, 180]
      "Qualidade": [34, 106, 624, 609, 369, 618, 420]
    anki_vocab: [619, 244, 419, 169, 489, 595, 633, 157, 158, 436, 602, 592]

  11:
    type: content
    phase: 3
    title: "Adjetivos-な, Cores & Contrastes"
    objective: "Dominar adjetivos-な (な+N, じゃない), cores, e conectores de contraste でも e しかし."
    grammar: [36, 6, 62]
    kanji: [27, 28, 40, 70]
    focus_vocab:
      "な-adjectives": [269, 512, 390, 118, 68, 219, 465, 47, 168]
      "Cores": [6, 7, 19, 20, 311, 312]
    anki_vocab: [507, 508, 263, 344, 55, 198, 199, 430, 60, 160, 220, 545, 544]

  12:
    type: content
    phase: 3
    title: "Mais Descrições, Advérbios & Ênfase"
    objective: "Aprender advérbios de grau e modo, usar よ para ênfase, e conectores そして/それから para sequenciar ideias."
    grammar: [83, 64, 63]
    kanji: [21, 34, 31]
    focus_vocab:
      "Sensações térmicas": [37, 478, 35, 539, 39, 593, 402]
      "Advérbios": [64, 65, 70, 88, 137, 384, 526, 635]
    anki_vocab: [2, 8, 309, 12, 339, 203, 206, 251, 276, 336, 607, 38, 553]

  13:
    type: consolidation
    phase: 3
    title: "Consolidação — Aulas 10 a 12"
    scope: [10, 11, 12]

  # ═══════════════════════════════════════════
  # FASE 4: TEMPO & DESEJOS — "Quando / O que quero"
  # ═══════════════════════════════════════════

  14:
    type: content
    phase: 4
    title: "Calendário & Datas"
    objective: "Expressar dias da semana e datas, e usar から (de/porque), まで (até), いつも (sempre)."
    grammar: [23, 29, 19]
    kanji: [1, 14, 17, 18]
    focus_vocab:
      "Dias da semana": [389, 119, 252, 527, 358, 266, 92]
      "Períodos": [26, 170, 629, 638, 123, 125]
      "Tempo": [216, 569]
    anki_vocab: [185, 110, 348, 625, 208, 365, 378, 632, 283, 576, 156, 584]

  15:
    type: content
    phase: 4
    title: "Frequência & Sequência Temporal"
    objective: "Falar sobre frequência (まだ/もう), hábitos, e marcar tempo com とき. Vocabulário de períodos relativos."
    grammar: [27, 35, 76]
    kanji: [23, 5, 7, 55]
    focus_vocab:
      "Frequência": [330, 328, 329, 331, 333, 332, 570]
      "Relativo": [265, 30, 28, 318, 298, 457]
      "Extras": [568, 140]
    anki_vocab: [259, 286, 287, 290, 491, 493, 456, 458, 442, 443, 481]

  16:
    type: content
    phase: 4
    title: "Gostos, Desejos & Comida"
    objective: "Expressar gostos (のが好き), desejos por coisas (がほしい) e ações (〜たい), e explicar com んです. Vocabulário de comida."
    grammar: [56, 13, 67, 46]
    kanji: [64, 54, 44]
    focus_vocab:
      "Sentimentos": [529, 69, 268, 211, 179]
      "Comida": [124, 27, 171, 41, 639, 392, 474, 617]
      "Comer e Beber": [542, 398]
    anki_vocab: [304, 52, 127, 578, 483, 506, 514, 44, 241, 541, 397, 469, 449, 550, 357]

  17:
    type: content
    phase: 4
    title: "Habilidades, Natureza & Estações"
    objective: "Falar sobre habilidades (上手/下手) e ações conjuntas (一緒に). Vocabulário de natureza e estações."
    grammar: [55, 54, 18]
    kanji: [56, 45, 50]
    focus_vocab:
      "Bebidas": [291, 408, 128, 433]
      "Natureza": [141, 250, 598, 614, 521]
      "Estações": [149, 382, 10, 112]
      "Habilidades": [144, 234]
    anki_vocab: [300, 261, 188, 204, 195, 385, 577, 89, 452, 383, 93, 95, 96, 424, 533]

  18:
    type: consolidation
    phase: 4
    title: "Consolidação — Aulas 14 a 17"
    scope: [14, 15, 16, 17]

  # ═══════════════════════════════════════════
  # FASE 5: AÇÕES — "O que faço"
  # ═══════════════════════════════════════════

  19:
    type: content
    phase: 5
    title: "Verbos & Conjugação: Fundamentos"
    objective: "Sistematizar a conjugação dos 3 grupos de verbos (ます/て/ない/た), marcar o objeto com を, e usar てください (pedido), まえに (antes de) e のです (explicação formal). Esta aula inclui o MÓDULO DE CONJUGAÇÃO (seção 3E do Template A)."
    grammar: [72, 60, 53, 30]
    kanji: [15, 39, 30]
    focus_vocab:
      "Cotidiano básico": [80, 134, 353, 264, 628, 387, 415]
      "Verbos essenciais": [210, 608, 407, 586, 155]
    anki_vocab: [509, 610, 200, 296, 381, 435]

  20:
    type: content
    phase: 5
    title: "て-form: Progresso & Experiência"
    objective: "Usar ている (ação em progresso/estado), てから (depois de fazer), たことがある (experiência passada) e まだ〜ていません (ainda não). Mais verbos de ação."
    grammar: [70, 71, 66, 28]
    kanji: [16, 63, 49, 75]
    focus_vocab:
      "Ações domésticas": [22, 525, 494, 591, 249, 599]
      "Ações com objetos": [9, 11, 502, 501, 260, 262]
      "Interação": [40, 338, 623]
    anki_vocab: [230, 463, 515, 511, 480, 143, 620, 500, 221, 46, 475, 36]

  21:
    type: content
    phase: 5
    title: "て-form: Permissão & Proibição"
    objective: "Pedir e dar permissão (てもいい) e proibir (てはいけない/ちゃいけない)."
    grammar: [74, 73, 1]
    kanji: [65, 58, 51]
    focus_vocab:
      "Transporte (ações)": [400, 432, 572, 566, 327, 611]
      "Vestir/Corpo": [273, 139, 401, 503, 1]
      "Dar/Receber": [5, 246, 243, 613]
    anki_vocab: [215, 218, 100, 229, 467, 409, 413, 473, 228, 245, 236, 103]

  22:
    type: consolidation
    phase: 5
    title: "Consolidação — Aulas 19 a 21"
    scope: [19, 20, 21]

  23:
    type: content
    phase: 5
    title: "Verbos do Cotidiano (Parte 1)"
    objective: "Usar に行く (ir para fazer), にする (decidir), つもり (intenção) e なる (tornar-se). Verbos de rotina e casa."
    grammar: [49, 50, 78, 45]
    kanji: [59, 60, 12]
    focus_vocab:
      "Ações domésticas": [416, 362, 579, 556, 538, 437, 165]
      "Cozinha/Refeição": [151, 534, 371, 102, 294, 238, 56, 434]
    anki_vocab: [232, 233, 379, 380, 73, 196, 587, 588, 75, 589, 594, 532]

  24:
    type: content
    phase: 5
    title: "Verbos do Cotidiano (Parte 2)"
    objective: "Listar ações representativas com たり〜たり, dar conselhos com ほうがいい, usar ないで (sem fazer), e けど (mas)."
    grammar: [68, 15, 38, 25]
    kanji: [78, 66, 69]
    focus_vocab:
      "Atividades": [31, 447, 396, 604, 166, 345, 621]
      "Ações diversas": [552, 285, 374, 505, 373, 476, 585, 597]
    anki_vocab: [459, 563, 121, 603, 406, 414, 14, 240, 410, 428, 531, 600]

  25:
    type: content
    phase: 5
    title: "Mais Verbos & Objetos do Dia-a-dia"
    objective: "Pedir para NÃO fazer com ないでください, contrastar formalmente com けれども. Vocabulário de objetos e vestuário."
    grammar: [39, 26, 69]
    kanji: [19, 20, 46]
    focus_vocab:
      "Verbos restantes": [58, 227, 355, 580, 272, 537, 136, 446, 616]
      "Vestuário": [316, 317, 50, 386, 528, 292]
    anki_vocab: [496, 605, 631, 644, 486, 488, 497, 461, 536, 454, 567, 438]

  26:
    type: consolidation
    phase: 5
    title: "Consolidação — Aulas 23 a 25"
    scope: [23, 24, 25]

  # ═══════════════════════════════════════════
  # FASE 6: COMUNICAÇÃO — "Como me expresso"
  # ═══════════════════════════════════════════

  27:
    type: content
    phase: 6
    title: "Obrigação & Proibição"
    objective: "Expressar obrigação (ないといけない, なくてはいけない, なくてはならない, なくちゃ) em diferentes níveis de formalidade. Vocabulário de clima e obrigações."
    grammar: [40, 43, 44, 42]
    kanji: [71, 80, 67]
    focus_vocab:
      "Clima": [562, 13, 634, 253, 147, 306]
      "Verbos de clima": [148, 307, 104, 105]
      "Obrigações": [359, 315, 254, 54, 305]
    anki_vocab: [543, 337, 364, 627, 247, 571, 281, 361, 360, 193]

  28:
    type: content
    phase: 6
    title: "Convites & Sugestões"
    objective: "Fazer convites (ませんか), propor ações conjuntas (ましょう), oferecer ajuda (ましょうか), e dispensar obrigação (なくてもいい)."
    grammar: [31, 32, 33, 41]
    kanji: [47, 48, 53]
    focus_vocab:
      "Viagem": [468, 181, 267, 546, 393]
      "Comunicação": [78, 76, 495, 561, 277, 131]
      "Expressões": [187, 523, 448, 214]
    anki_vocab: [581, 145, 154, 636, 391, 551, 257, 431, 351, 352]

  29:
    type: content
    phase: 6
    title: "Comparações & Contrastes"
    objective: "Comparar (は〜より, より〜ほうが), superlativar (一番, の中で一番), e vocabulário escolar."
    grammar: [17, 57, 80, 84]
    kanji: [68, 61, 73]
    focus_vocab:
      "Escrita/Escola": [99, 48, 335, 451, 399, 63, 217, 213, 504, 641]
      "Objetos": [235, 242, 342, 293, 564]
    anki_vocab: [310, 477, 450, 51, 615, 575, 61, 363, 270]

  30:
    type: consolidation
    phase: 6
    title: "Consolidação — Aulas 27 a 29"
    scope: [27, 28, 29]

  31:
    type: content
    phase: 6
    title: "Conectando Ideias & Explicações"
    objective: "Dar razões com ので, conjecturar com だろう/でしょう, e descrever métodos com 方. Vocabulário restante do N5."
    grammar: [58, 4, 7, 24]
    kanji: [72, 79, 74, 77]
    focus_vocab:
      "Objetos restantes": [138, 177, 224, 135, 453, 223, 111, 146, 323]
      "Medidas": [341, 271, 126]
      "Mídia": [559, 560, 462]
    anki_vocab: [101, 535, 606, 485, 540, 403, 175, 583, 49, 150, 482]

  32:
    type: consolidation
    phase: null
    title: "Revisão Final & Simulado N5"
    scope: [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31]
    special_format:
      - "Recall completo de todos os 80 kanji"
      - "Exercício de gramática cobrindo todas as 84 estruturas em formato de simulado"
      - "Diálogo longo (10+ turnos) integrando vocabulário e gramática de todas as fases"
      - "Autodiagnóstico final com plano de revisão para itens fracos"
      - "Mini-simulado N5 com questões no formato oficial do JLPT"
```
