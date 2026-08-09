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
   3.1 **VOCABULARY GATE (Portão de Vocabulário — Enforcement Mecânico):** Antes de gerar QUALQUER output para a Aula X (aula HTML, Reading, Lacunas, Teste), a IA DEVE executar obrigatoriamente os seguintes passos:
       (a) **Construir o inventário cumulativo**: Abrir o bloco YAML deste arquivo e coletar TODAS as regras de `grammar` e `kanji` das Aulas 1 até X (inclusive) a partir dos seus arquivos em `Content/`. Para o vocabulário, ler a seção 'Aula N' correspondente até a Aula X diretamente no arquivo `Content/N5_Vocabulary.md`.
       (b) **Gerar conteúdo SOMENTE com o inventário**: Toda palavra japonesa, estrutura gramatical, ou kanji presente no output final DEVE pertencer ao inventário construído em (a). Se uma palavra é desejável mas NÃO está no inventário, ela NÃO pode ser usada — a IA deve encontrar uma alternativa cumulativa ou reformular a frase. IMPORTANTE: Conforme Regra 7, ao gerar a seção de Gramática, a IA DEVE priorizar ativamente o uso do vocabulário da Aula X (novo) ensinado na seção de Vocabulário para fixação.
       (c) **Auto-verificação pós-geração**: Após gerar o output, varrer todo o texto japonês e confirmar que nenhuma palavra fora do inventário escapou. Se encontrar uma violação, corrigir antes de salvar/enviar.
       (d) **Exceções permitidas**: Partículas gramaticais (は, が, を, に, で, へ, と, も, か, の, よ, ね, etc.), cópula (です/だ/でした/じゃない), verbos de existência básicos (ある/いる — quando no escopo), pronomes demonstrativos (これ/それ/あれ/この/その/あの — quando no escopo), e expressões de cortesia básica (はい, いいえ, ありがとう, すみません — quando no escopo) são permitidas desde que já tenham sido introduzidas no inventário cumulativo.
4. **Row references:** Each lesson is defined in the `## Curriculum Data (YAML)` section at the end of this file. The YAML block uses row numbers referencing `Content/N5_Grammar.md`, `Content/N5_Kanji.md`, and `Content/N5_Vocabulary.md`. Before teaching, locate the lesson entry in the YAML block, then open the referenced rows in the data files and read them. For consolidation lessons, use the `scope` field to identify which previous content lessons are being reviewed.
5. **Two lesson types:**
   - **📘 Content lessons** teach new grammar, kanji, and vocabulary following Template A in `Filters/HTML/HTML_Lesson.md`.
   - **🔄 Consolidation lessons** review and reinforce the previous 3-4 content lessons following Template B in `Filters/HTML/HTML_Lesson.md`. They introduce NO new content.
6. **Vocabulary unificado:**
   - Todo o vocabulário da aula está perfeitamente delimitado na seção '## Aula X' do arquivo `Content/N5_Vocabulary.md`. Não há mais IDs no arquivo JLPTN5.md. A IA deve ler a lista daquela seção e organizá-la em um único "pool" de palavras a ser ensinado.
   - Na hora de gerar a aula, a IA deve agrupar essas palavras em uma única seção chamada "Vocabulário da Aula", categorizando as palavras semanticamente para melhor didática (ex: agrupar por temas, verbos vs adjetivos, etc). Todo esse vocabulário é o foco da aula e irá para o Anki.
7. **Lesson teaching format (content lessons):**
   - **Review (5 min):** Quick recap of the previous lesson's most important points. Show 3-5 review questions. *(Skip for Lesson 1.)*
   - **Kanji:** Present new kanji as **compositional reading keys** (chaves de leitura composicional): glyph + **core idea** (conceito semântico, not a simple translation) + radical as mnemonic hook + 2-3 words from cumulative vocabulary showing **explicit compositional breakdown** (e.g., 外(fora) + 国(país) + 人(pessoa) → "estrangeiro"), each tagged with the lesson where the word appears [Aula N]. When all words containing the kanji belong to future lessons, include a bridging note. For opaque compositions (jukujikun), show only translation + note "composição irregular". The reading is learned exclusively through words — NEVER drill onyomi/kunyomi or stroke counts. Mnemonic and confusion warnings are CONDITIONAL — include only when they add genuine value at the current level.
   - **Vocabulário da Aula:** Apresentar todo o pool de palavras (Focus + Anki) agrupado por **tema semântico/didático**, com traduções e collocations.
   - **Grammar (core):** Teach each grammar point — pattern, meaning, usage, contrast, 2-3 example sentences. **ATENÇÃO:** Os exemplos gramaticais DEVEM **priorizar ativamente** o uso do vocabulário novo recém-ensinado na seção anterior para garantir a fixação, completando com vocabulário cumulativo das aulas passadas para maior fluidez e naturalidade.
   - **Anki card (reading recall engine):** for each kanji word — **front = word in kanji WITHOUT furigana** / **back = kana reading + PT-BR translation**. This is the ONLY place in the system where kanji appears without furigana. Pure-kana words use a simple card (front = kana / back = translation).
   - **Practice (end):** Exercises including **interleaved** questions mixing current and past content.
8. Never use a grammar point in examples before it has been introduced.
9. Teach in **Portuguese (PT-BR)**. Write Japanese examples with kanji + hiragana reading. All explanations, translations, and instructions must be in Portuguese.
10. **Session commands:** 
    - `"Lesson N"` / `"Aula N"` / `"Inicie a aula N"` → gera a aula completa em HTML no Google Drive seguindo `Filters/Modalidades/Lesson.md` e o formato em `Filters/HTML/HTML_Lesson.md`.
    - `"Exercícios Aula N"` / `"Drill Aula N"` → gera o caderno de exercícios interativo em Markdown em `Practice/N5_PN.md` seguindo `Filters/Exercises.md`.
    - `"Reading Aula N"` / `"Leitura Aula N"` → gera o treino de leitura narrativa em HTML (salvo em `Practice/N5_PN_Reading.html` e enviado ao Google Drive) seguindo as regras e fluxos descritos em `Filters/Modalidades/Reading.md` e o formato em `Filters/HTML/HTML_reading.md`. A correção/discussão deste módulo acontece diretamente no chat.
    - `"Lacunas Aula N"` / `"Preencher Lacunas Aula N"` → gera o caderno de exercícios de lacunas em Markdown em `Practice/N5_PN_Lacunas.md` seguindo `Filters/Exercises.md` → `Filters/Modalidades/Lacunas.md`.
    - `"Corrigir Aula N"` / `"Avalie o Practice/N5_PN.md"` → lê o arquivo de exercícios `Practice/N5_PN.md`, corrige as respostas digitadas pelo estudante, atribui nota e dá feedback detalhado no chat. (Nota: não usado para Reading).
    - `"Corrigir Lacunas Aula N"` → lê o arquivo `Practice/N5_PN_Lacunas.md`, corrige as respostas digitadas, atribui nota (0-100) e dá feedback com diagnóstico de causa raiz no chat.
11. **POLÍTICA DE FURIGANA — SEMPRE RUBY (Regra Principal):** Todo texto japonês gerado nas aulas e exercícios em Markdown (tabelas de vocabulário, exemplos com 4 camadas, diálogos, Teste, Lacunas, gabaritos) segue esta regra determinística: **toda palavra que contenha kanji recebe `<ruby>` em TODA ocorrência, sem exceção.** Não existe distinção de "níveis" de kanji para fins de furigana — todos são tratados igualmente. **Exceção única — Modalidade Reading:** A modalidade de Leitura Narrativa (`Filters/Modalidades/Reading.md`) utiliza furigana gradual (ruby apenas na **primeira ocorrência** de cada palavra com kanji no texto) para estimular o resgate ativo de memória. Essa é a única exceção autorizada à política de furigana universal.
    - **Sempre furigana:** Cada ocorrência de uma palavra com kanji carrega `<ruby>`, independente de quantas vezes a palavra apareça na aula e independente de o kanji pertencer ou não aos 80 formais de `Content/N5_Kanji.md`.
    - **Kana puro nunca ruby:** Palavras sem kanji (あなた, はい, partículas...) são escritas sem `<ruby>`.
    - O ruby usa a leitura completa da palavra sobre a palavra inteira (para vocabulário, copiar da coluna `Leitura (Kana)` de `Content/N5_Vocabulary.md`). **Nunca** dividir o ruby kanji por kanji — isso quebra leituras irregulares como `今日` = きょう, `大人` = おとな, `時々` = ときどき.
    - **Active recall de leitura pertence ao Anki:** Os cards de Anki (frente = kanji SEM furigana / verso = leitura + tradução) são o único mecanismo de recuperação ativa de leitura no sistema, com espaçamento otimizado.
    - A regra cumulativa (regra 3) continua valendo para palavras e gramática.
12. **CONTRATO DE EXPECTATIVA DA AULA (promessa honesta):** Cada aula de conteúdo declara no cabeçalho exatamente quais kanji formais ela ensina (3-4 por aula, conforme `Aula (intro)` em `Content/N5_Kanji.md`). Os kanji formais da aula são ensinados como **âncoras de reconhecimento** (forma → significado, com o radical como gancho mnemônico; a leitura é aprendida nas palavras) — **nunca** cobrar onyomi/kunyomi memorizados nem contagem de traços. Todos os demais kanji que aparecerem na aula são exclusivamente de reconhecimento (leitura) e sempre carregam furigana. **Proibido** criar exercícios que exijam ESCREVER kanji — o exame N5 não testa produção escrita. Exercícios podem cobrar kanji apenas em leitura (reconhecimento). A seção de kanji é um **primer composicional de 2 minutos** — não uma seção de estudo. O título "Chaves de Leitura" comunica ao aluno que o objetivo é entender a lógica de construção de palavras, não decorar kanji isolados.
13. **Geração HTML & Upload Direto no Google Drive:** Ao receber a instrução de iniciar uma aula ("Lesson X" / "Aula X"), **NÃO** imprima o texto completo da aula na conversa do chat nem salve arquivos locais permanentes. Em vez disso:
    - (a) Gerar a aula completa em formato HTML5 puro com CSS3 embutido, seguindo rigorosamente a arquitetura e especificações de `Filters/HTML/HTML_Lesson.md`.
    - (b) Salvar temporariamente o código HTML gerado e executar o script de upload para o Google Drive:
      `node "/Users/bmanica/Documents/GitHub/Bruno/Google Workspace/Drive/scripts/upload_to_gdrive.js" "<caminho_do_arquivo_html_temp>" "N5_LX.html"`
      (o script executará a **validação automática de ruby** — regra 11, conforme `Filters/HTML/HTML_Lesson.md` §4.6 — **ANTES** do upload e **BLOQUEARÁ** o envio se o arquivo reprovar em qualquer checagem. Somente arquivos aprovados são enviados para a pasta `Meu Drive > Aulas > Japones` como `N5_LX.html`, sem converter para Google Doc. Se a validação falhar, corrija o HTML conforme `Filters/HTML/HTML_Lesson.md` §4.6 e tente novamente).
    - (c) Após a confirmação do upload, apagar o arquivo temporário local (respeitando a Regra 1 de não deixar arquivos temporários no repositório).
    - (d) Responda no chat com uma mensagem curta de confirmação informando que a aula foi gerada em formato HTML e enviada ao Google Drive com sucesso.
14. **Geração e Correção Interativa de Exercícios (`Practice/`):** O sistema possui múltiplas modalidades de exercícios, todas roteadas via `Filters/Exercises.md`. Ao receber qualquer comando de exercício (`"Exercícios Aula X"`, `"Drill Aula X"`, `"Lacunas Aula X"`, etc.), a IA deve consultar `Filters/Exercises.md` para identificar a modalidade correta e seguir a especificação técnica correspondente em `Filters/Modalidades/`. Os arquivos gerados são salvos em `Practice/` com campos de resposta em branco digitáveis (`> `). Ao receber o comando de correção correspondente (`"Corrigir Aula X"`, `"Corrigir Lacunas Aula X"`, etc.), a IA lê o arquivo local, analisa as respostas digitadas pelo aluno após o caractere `>`, fornece nota e feedback didático detalhado no chat e atualiza o status do arquivo.

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

O bloco abaixo define as 32 aulas do currículo em formato estruturado. Os números em `grammar`, `kanji`, `focus_vocab` e `anki_vocab` são referências de linha (row #) aos arquivos em `Content/`. Para aulas de consolidação, `scope` lista as aulas de conteúdo cobertas na revisão. **Nota Importante para a IA geradora**: Embora o vocabulário esteja dividido no YAML entre `focus_vocab` e `anki_vocab` por razões de estrutura de dados legada, na geração da aula em HTML eles DEVEM ser consolidados em um único "pool" e ensinados juntos na Seção "Vocabulário da Aula" conforme a Regra 6.

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

    vocab: "Consultar N5_Vocabulary.md"

  2:
    type: content
    phase: 1
    title: "Não Sou — Negação, Posse & Inclusão"
    objective: "Negar identidade com じゃない, expressar posse com の, e adicionar com も. Aprender prefixos de polidez お/ご."
    grammar: [20, 52, 34, 59]
    kanji: [4, 9, 6, 76]

    vocab: "Consultar N5_Vocabulary.md"

  3:
    type: content
    phase: 1
    title: "Minha Família & Números"
    objective: "Contar de 1 a 10.000, usar が como marcador de sujeito, intensificar com とても, e apresentar alternativas com か〜か."
    grammar: [11, 77, 22]
    kanji: [26, 22, 37]

    vocab: "Consultar N5_Vocabulary.md"

  4:
    type: content
    phase: 1
    title: "Meu Mundo — Conexões & Contexto"
    objective: "Listar com と (completo) e や (exemplos), limitar com だけ, e perguntar tipo com どんな. Vocabulário de corpo e identidade."
    grammar: [75, 82, 3, 8]
    kanji: [42, 36, 29]

    vocab: "Consultar N5_Vocabulary.md"

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

    vocab: "Consultar N5_Vocabulary.md"

  7:
    type: content
    phase: 2
    title: "Existe Aqui — ある・いる & Demonstrativos"
    objective: "Expressar existência de coisas (がある) e seres vivos (がいる), usar demonstrativos (これ/それ/あれ), e perguntar "por quê" (どうして)."
    grammar: [12, 14, 9]
    kanji: [10, 43, 62]

    vocab: "Consultar N5_Vocabulary.md"

  8:
    type: content
    phase: 2
    title: "Pela Cidade — Locais & Transporte"
    objective: "Nomear locais urbanos, meios de transporte, e itens da casa. Usar ね para confirmação, をください para pedir, はどうですか para opiniões e どうやって para perguntar o meio."
    grammar: [47, 61, 81, 10]
    kanji: [25, 52, 41, 57]

    vocab: "Consultar N5_Vocabulary.md"

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

    vocab: "Consultar N5_Vocabulary.md"

  11:
    type: content
    phase: 3
    title: "Adjetivos-な, Cores & Contrastes"
    objective: "Dominar adjetivos-な (な+N, じゃない), cores, e conectores de contraste でも e しかし."
    grammar: [36, 6, 62]
    kanji: [27, 28, 40, 70]

    vocab: "Consultar N5_Vocabulary.md"

  12:
    type: content
    phase: 3
    title: "Mais Descrições, Advérbios & Ênfase"
    objective: "Aprender advérbios de grau e modo, usar よ para ênfase, e conectores そして/それから para sequenciar ideias."
    grammar: [83, 64, 63]
    kanji: [21, 34, 31]

    vocab: "Consultar N5_Vocabulary.md"

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

    vocab: "Consultar N5_Vocabulary.md"

  15:
    type: content
    phase: 4
    title: "Frequência & Sequência Temporal"
    objective: "Falar sobre frequência (まだ/もう), hábitos, e marcar tempo com とき. Vocabulário de períodos relativos."
    grammar: [27, 35, 76]
    kanji: [23, 5, 7, 55]

    vocab: "Consultar N5_Vocabulary.md"

  16:
    type: content
    phase: 4
    title: "Gostos, Desejos & Comida"
    objective: "Expressar gostos (のが好き), desejos por coisas (がほしい) e ações (〜たい), e explicar com んです. Vocabulário de comida."
    grammar: [56, 13, 67, 46]
    kanji: [64, 54, 44]

    vocab: "Consultar N5_Vocabulary.md"

  17:
    type: content
    phase: 4
    title: "Habilidades, Natureza & Estações"
    objective: "Falar sobre habilidades (上手/下手) e ações conjuntas (一緒に). Vocabulário de natureza e estações."
    grammar: [55, 54, 18]
    kanji: [56, 45, 50]

    vocab: "Consultar N5_Vocabulary.md"

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

    vocab: "Consultar N5_Vocabulary.md"

  20:
    type: content
    phase: 5
    title: "て-form: Progresso & Experiência"
    objective: "Usar ている (ação em progresso/estado), てから (depois de fazer), たことがある (experiência passada) e まだ〜ていません (ainda não). Mais verbos de ação."
    grammar: [70, 71, 66, 28]
    kanji: [16, 63, 49, 75]

    vocab: "Consultar N5_Vocabulary.md"

  21:
    type: content
    phase: 5
    title: "て-form: Permissão & Proibição"
    objective: "Pedir e dar permissão (てもいい) e proibir (てはいけない/ちゃいけない)."
    grammar: [74, 73, 1]
    kanji: [65, 58, 51]

    vocab: "Consultar N5_Vocabulary.md"

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

    vocab: "Consultar N5_Vocabulary.md"

  24:
    type: content
    phase: 5
    title: "Verbos do Cotidiano (Parte 2)"
    objective: "Listar ações representativas com たり〜たり, dar conselhos com ほうがいい, usar ないで (sem fazer), e けど (mas)."
    grammar: [68, 15, 38, 25]
    kanji: [78, 66, 69]

    vocab: "Consultar N5_Vocabulary.md"

  25:
    type: content
    phase: 5
    title: "Mais Verbos & Objetos do Dia-a-dia"
    objective: "Pedir para NÃO fazer com ないでください, contrastar formalmente com けれども. Vocabulário de objetos e vestuário."
    grammar: [39, 26, 69]
    kanji: [19, 20, 46]

    vocab: "Consultar N5_Vocabulary.md"

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

    vocab: "Consultar N5_Vocabulary.md"

  28:
    type: content
    phase: 6
    title: "Convites & Sugestões"
    objective: "Fazer convites (ませんか), propor ações conjuntas (ましょう), oferecer ajuda (ましょうか), e dispensar obrigação (なくてもいい)."
    grammar: [31, 32, 33, 41]
    kanji: [47, 48, 53]

    vocab: "Consultar N5_Vocabulary.md"

  29:
    type: content
    phase: 6
    title: "Comparações & Contrastes"
    objective: "Comparar (は〜より, より〜ほうが), superlativar (一番, の中で一番), e vocabulário escolar."
    grammar: [17, 57, 80, 84]
    kanji: [68, 61, 73]

    vocab: "Consultar N5_Vocabulary.md"

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

    vocab: "Consultar N5_Vocabulary.md"

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
