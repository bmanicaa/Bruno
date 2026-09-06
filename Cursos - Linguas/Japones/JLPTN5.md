# JLPTN5.md — JLPT N5 Self-Study Rules & Curriculum (32 Lessons)

## Purpose

This file is the single source of truth for the JLPT N5 self-study program. It defines the **rules** for study sessions and the **32-lesson curriculum** (24 content + 8 consolidation) that turns the raw reference files (`Content/N5_Grammar.md`, `Content/N5_Kanji.md`, `Content/N5_Vocabulary.md`) into a structured, cumulative learning path optimized for a busy adult learner studying **1 lesson per week** with **Anki** support.

## How This System Works

1. **This file (JLPTN5.md)** defines the curriculum: which grammar points, kanji, and vocabulary belong to each lesson, via row references to the data files in `Content/`.
2. **`Filters/Modalidades/Lesson.md`** and **`Filters/HTML/HTML_Lesson.md`** define the lesson pedagogical rules and output specifications: CSS master styling, HTML5 structure, furigana rules, and canonical skeletons for both content and consolidation lessons.
3. **The data files** (`Content/N5_Grammar.md`, `Content/N5_Kanji.md`, `Content/N5_Vocabulary.md`) contain the raw reference data.
4. **`Progress.md`** is the **state** of the course — which lessons are done, the grades, and the § Itens Fracos list with root-cause diagnoses. It is the system's only memory between sessions: without it the system generates material and forgets it; with it, it can re-test what the student actually got wrong. Every modality **reads** it before generating and **writes** it after grading.
5. **`scripts/`** holds the permanent tooling:
   - `validate_artifact.js` — fonte única de verdade das regras de ruby/furigana e do Vocabulary Gate. Roda em HTML, Markdown e TSV.
   - `audit_curriculum.js` — **auditoria estrutural, pré-voo obrigatório.** Confere cobertura de gramática/kanji, sincronia YAML × Content/, ensinabilidade de cada kanji, colunas cumulativas da tabela, taxonomia dos subtítulos, caminhos mortos, comandos sem rota e contradições entre specs. Rode antes de gerar qualquer aula.
   - `optimize_kanji.js` — reatribui kanji→aula por matching de custo mínimo. Só reexecute se `Content/` mudar.
   - `build_anki.js`, `seed_gramatica.js`, `exemplos_vocab.js` — geração dos decks.

**Workflow:** When generating a lesson, the AI must (1) read the lesson definition here in `JLPTN5.md`, (2) open the referenced rows in the data files in `Content/` to extract the raw content, and (3) format the output in HTML following the canonical specifications in `Filters/Modalidades/Lesson.md` and `Filters/HTML/HTML_Lesson.md`.

## Prerequisites

- **Hiragana and Katakana** are assumed to be fully mastered before starting Lesson 1. They are not taught in this curriculum. The student must be able to read all kana fluently.

## Student Profile

- **Occupation:** Medical resident (neurosurgery) — very limited study time
- **Pace:** 1 lesson per week (may extend to 2 weeks during heavy rotations)
- **SRS Tool:** Anki for daily vocabulary reinforcement (~10 min/day)
- **Target session:** ~50-60 minutes per content lesson, ~45 minutes per consolidation lesson

## Rules

1. Never leave any **temporary** file or scratch script in this repository. This does **not** apply to `scripts/`, which is permanent, versioned tooling (`validate_artifact.js`, `build_anki.js`, `seed_gramatica.js`) — nor to `Progress.md`, which is persistent state.
   1.1 **AUDITORIA DE PRÉ-VOO:** Antes de gerar qualquer aula, execute `node scripts/audit_curriculum.js`. Ele falha se o currículo estiver fora de sincronia. Nenhuma aula deve ser gerada sobre dados inconsistentes.
   1.2 **VALIDAÇÃO MECÂNICA OBRIGATÓRIA:** Antes de entregar qualquer artefato (HTML, Markdown ou TSV), execute `node scripts/validate_artifact.js <arquivo>` e corrija **todo** erro bloqueante. O upload ao Drive roda o mesmo validador e bloqueia o envio; artefatos Markdown e TSV não passam pelo upload, portanto a execução manual é a única barreira que existe para eles.
2. The data reference files live in `Content/N5_Grammar.md`, `Content/N5_Kanji.md`, `Content/N5_Vocabulary.md`. They are read-only reference data — do not modify them during a study session.
3. **Cumulative principle:** Lessons build on each other. Lesson N assumes ALL content from lessons 1 to N-1 is mastered. Example sentences and practice questions for lesson N may freely use grammar, kanji, and vocabulary from lessons 1..N, but must NOT use content from lessons N+1 or beyond.
   3.1 **VOCABULARY GATE (Portão de Vocabulário — Enforcement Mecânico):** Antes de gerar QUALQUER output para a Aula X (aula HTML, Reading, Lacunas, Teste), a IA DEVE executar obrigatoriamente os seguintes passos:
       (a) **Construir o inventário cumulativo**: Abrir o bloco YAML deste arquivo e coletar TODAS as regras de `grammar` e `kanji` das Aulas 1 até X (inclusive) a partir dos seus arquivos em `Content/`. Para o vocabulário, ler a seção 'Aula N' correspondente até a Aula X diretamente no arquivo `Content/N5_Vocabulary.md`.
       (b) **Gerar conteúdo SOMENTE com o inventário**: Toda palavra japonesa, estrutura gramatical, ou kanji presente no output final DEVE pertencer ao inventário construído em (a). Se uma palavra é desejável mas NÃO está no inventário, ela NÃO pode ser usada — a IA deve encontrar uma alternativa cumulativa ou reformular a frase. IMPORTANTE: Conforme Regra 7, ao gerar a seção de Gramática, a IA DEVE priorizar ativamente o uso do vocabulário da Aula X (novo) ensinado na seção de Vocabulário para fixação.
       (c) **Auto-verificação pós-geração**: Após gerar o output, varrer todo o texto japonês e confirmar que nenhuma palavra fora do inventário escapou. Se encontrar uma violação, corrigir antes de salvar/enviar.
       (d) **Exceções permitidas**: Partículas gramaticais (は, が, を, に, で, へ, と, も, か, の, よ, ね, etc.), cópula (です/だ/でした/じゃない), verbos de existência básicos (ある/いる — quando no escopo), pronomes demonstrativos (これ/それ/あれ/この/その/あの — quando no escopo), e expressões de cortesia básica (はい, いいえ, ありがとう, すみません — quando no escopo) são permitidas desde que já tenham sido introduzidas no inventário cumulativo.
4. **Row references:** Each lesson is defined in the `## Curriculum Data (YAML)` section at the end of this file. The YAML block uses row numbers referencing `Content/N5_Grammar.md` and `Content/N5_Kanji.md`. The vocabulary of each lesson is NOT referenced by row numbers — it is defined directly in the `## Aula X` sections of `Content/N5_Vocabulary.md` (see Rule 6). Before teaching, locate the lesson entry in the YAML block, then open the referenced rows in the data files and read them. For consolidation lessons, use the `scope` field to identify which previous content lessons are being reviewed, and the `review_prior` field (presente nas consolidações 13, 18, 22, 26 e 30) to identify an OLDER block that gets a second pass. `scope` é o bloco recém-concluído; `review_prior` é o bloco de 8-12 aulas atrás, que sem isso só reapareceria na Aula 32.
5. **Two lesson types:**
   - **📘 Content lessons** teach new grammar, kanji, and vocabulary following Template A in `Filters/HTML/HTML_Lesson.md`.
   - **🔄 Consolidation lessons** review and reinforce the previous 3-4 content lessons (`scope`) following Template B in `Filters/HTML/HTML_Lesson.md`. They introduce NO new content. A partir da Aula 13, também retomam um bloco mais antigo via `review_prior` — ver Regra 4.
6. **Vocabulary unificado:**
   - Todo o vocabulário da aula está perfeitamente delimitado na seção '## Aula X' do arquivo `Content/N5_Vocabulary.md`. Não há mais IDs no arquivo JLPTN5.md. A IA deve ler a lista daquela seção e organizá-la em um único "pool" de palavras a ser ensinado.
   - Na hora de gerar a aula, a IA deve ensinar essas palavras em uma única seção chamada "Vocabulário da Aula", **preservando e utilizando EXATAMENTE os subtítulos semânticos (`###`) que já organizam o vocabulário em `Content/N5_Vocabulary.md`** — o agrupamento já vem pronto no arquivo de dados e NÃO deve ser recalculado, reorganizado nem renomeado (a taxonomia canônica está documentada na intro do próprio arquivo). Todo esse vocabulário é o foco da aula e irá para o Anki.
   - **⚠️ AVISO DE MANUTENÇÃO (SINGLE SOURCE OF TRUTH):** O mapeamento aula→vocabulário vive EXCLUSIVAMENTE em `Content/N5_Vocabulary.md` (seções `## Aula N`). Qualquer alteração na numeração, no escopo ou na ordem das aulas de conteúdo em `JLPTN5.md` DEVE ser refletida naquele arquivo (mover palavras, criar/excluir seções) para manter o inventário cumulativo correto. Aulas de consolidação (5, 9, 13, 18, 22, 26, 30, 32) não introduzem vocabulário e, portanto, não possuem seção própria no arquivo.
7. **Lesson teaching format (content lessons):**
   - **Review (5 min):** Quick recap of the previous lesson's most important points. Show 3-5 review questions. *(Skip for Lesson 1.)*
   - **Kanji:** Present new kanji as **compositional reading keys** (chaves de leitura composicional): glyph + **core idea** (conceito semântico, not a simple translation) + radical as mnemonic hook + **as many words from the cumulative vocabulary as actually exist, up to 3**, showing **explicit compositional breakdown** (e.g., 外(fora) + 国(país) + 人(pessoa) → "estrangeiro"), each tagged with the lesson where the word appears [Aula N].
     - **Contrato honesto sobre a quantidade de palavras:** a atribuição kanji→aula foi otimizada (`scripts/optimize_kanji.js`) para maximizar as palavras disponíveis. Depois da otimização: **59 dos 80 kanji têm 2+ palavras**, **21 têm exatamente 1**, e **nenhum tem zero**. Os 21 de uma palavra são um **teto estrutural do próprio vocabulário**, não um defeito de sequenciamento: esses kanji (中, 長, 間, 東, 高, 北, 川, 千, 西, 校, 語, 土, 南, 天, 火, 右, 読, 友, 左, 雨, 円) aparecem em **uma única palavra em toda a lista de 645**. Nenhuma reordenação lhes dá duas. Uma palavra sólida é ensino suficiente — não invente palavras para cumprir cota.
     - **Nota de bridging:** o mecanismo continua documentado, mas **não deve mais ser necessário** — nenhum kanji estreia sem palavra. Se você se vir precisando dele, isso indica que os dados saíram de sincronia; rode `node scripts/audit_curriculum.js`. For opaque compositions (jukujikun), show only translation + note "composição irregular". The reading is learned exclusively through words — NEVER drill onyomi/kunyomi or stroke counts. Mnemonic and confusion warnings are CONDITIONAL — include only when they add genuine value at the current level.
   - **Vocabulário da Aula:** Apresentar todo o pool de palavras da Aula X (seção `## Aula X` de `Content/N5_Vocabulary.md`) **respeitando os subtítulos semânticos (`###`) já definidos no arquivo de dados** (preservar nomes e agrupamentos, sem reorganizar), com traduções e collocations.
   - **Grammar (core):** Teach each grammar point — pattern, meaning, usage, contrast, 2-3 example sentences. **ATENÇÃO:** Os exemplos gramaticais DEVEM **priorizar ativamente** o uso do vocabulário novo recém-ensinado na seção anterior para garantir a fixação, completando com vocabulário cumulativo das aulas passadas para maior fluidez e naturalidade.
   - **Anki card:** for each kanji word — **front = word in kanji WITH furigana** / **back = PT-BR translation** (ou leitura + tradução). Todos os kanjis recebem furigana. Pure-kana words use a simple card (front = kana / back = translation).
   - **Practice (end):** Exercises including **interleaved** questions mixing current and past content.
8. Never use a grammar point in examples before it has been introduced.
9. Teach in **Portuguese (PT-BR)**. Write Japanese examples with kanji + hiragana reading. All explanations, translations, and instructions must be in Portuguese.
10. **Session commands:** 
    - `"Lesson N"` / `"Aula N"` / `"Inicie a aula N"` → gera a aula completa em HTML no Google Drive seguindo `Filters/Modalidades/Lesson.md` e o formato em `Filters/HTML/HTML_Lesson.md`.
    - `"Exercícios Aula N"` / `"Drill Aula N"` → gera o caderno de exercícios interativo em Markdown em `Practice/N5_PN.md` seguindo `Filters/Exercises.md`.
    - `"Mais Reading Aula N"` → gera uma SEGUNDA narrativa em `Practice/N5_PN_Reading_Parte2.html` focada no vocabulário da Aula N que sobrou da primeira leitura (Reading.md §2.2).
    - `"Reading Aula N"` / `"Leitura Aula N"` → gera o treino de leitura narrativa em HTML (salvo em `Practice/N5_PN_Reading.html` e enviado ao Google Drive) seguindo as regras e fluxos descritos em `Filters/Modalidades/Reading.md` e o formato em `Filters/HTML/HTML_reading.md`. A correção/discussão deste módulo acontece diretamente no chat.
    - `"Lacunas Aula N"` / `"Preencher Lacunas Aula N"` → gera o caderno de exercícios de lacunas em Markdown em `Practice/N5_PN_Lacunas.md` seguindo `Filters/Exercises.md` → `Filters/Modalidades/Lacunas.md`.
    - `"Corrigir Aula N"` / `"Avalie o Practice/N5_PN.md"` → lê o arquivo de exercícios `Practice/N5_PN.md`, corrige as respostas digitadas pelo estudante, atribui nota e dá feedback detalhado no chat. (Nota: não usado para Reading).
    - `"Corrigir Lacunas Aula N"` → lê o arquivo `Practice/N5_PN_Lacunas.md`, corrige as respostas digitadas, atribui nota (0-100) e dá feedback com diagnóstico de causa raiz no chat.
    - `"Ditado Aula N"` → gera a folha de transcrição em `Practice/N5_PN_Ditado.md` seguindo `Filters/Modalidades/Ditado.md`. O **áudio é externo** — o repositório não gera áudio (ver Ditado.md §0).
    - `"Corrigir Ditado Aula N"` → corrige a transcrição: Modo A (com transcrição oficial → nota + diff por tipo de erro) ou Modo B (sem → diagnóstico sem nota). Atualiza `Progress.md` § 3 Escuta.
    - **Todo comando de correção atualiza `Progress.md`** (Mapa de Progresso + § Itens Fracos com diagnóstico de causa raiz). Isso não é opcional: é o que permite à Seção 6 do Teste re-testar o que foi errado.
11. **POLÍTICA DE FURIGANA — SEMPRE RUBY (Regra Principal):** Todo texto japonês gerado nas aulas e exercícios em Markdown (tabelas de vocabulário, exemplos com 3 camadas, diálogos, Teste, Lacunas, gabaritos) segue esta regra determinística: **toda palavra que contenha kanji recebe `<ruby>` em TODA ocorrência, sem exceção.** Não existe distinção de "níveis" de kanji para fins de furigana — todos são tratados igualmente. **Exceção única — Modalidade Reading:** A modalidade de Leitura Narrativa (`Filters/Modalidades/Reading.md`) utiliza furigana gradual (ruby apenas na **primeira ocorrência** de cada palavra com kanji no texto) para estimular o resgate ativo de memória. Essa é a única exceção autorizada à política de furigana universal.
    - **Sempre furigana:** Cada ocorrência de uma palavra com kanji carrega `<ruby>`, independente de quantas vezes a palavra apareça na aula e independente de o kanji pertencer ou não aos 80 formais de `Content/N5_Kanji.md`.
    - **Kana puro nunca ruby:** Palavras sem kanji (あなた, はい, partículas...) são escritas sem `<ruby>`.
    - O ruby usa a leitura completa da palavra sobre a palavra inteira (para vocabulário, copiar da coluna `Leitura (Kana)` de `Content/N5_Vocabulary.md`). **Nunca** dividir o ruby kanji por kanji — isso quebra leituras irregulares como `今日` = きょう, `大人` = おとな, `時々` = ときどき.
    - **Active recall no Anki:** Os cards de Anki agora possuem furigana na frente (frente = kanji COM furigana / verso = tradução). O recall ativo agora abrange todo o conteúdo, sem a restrição de kanji sem furigana.
    - A regra cumulativa (regra 3) continua valendo para palavras e gramática.
12. **CONTRATO DE EXPECTATIVA DA AULA (promessa honesta):** Cada aula de conteúdo declara no cabeçalho exatamente quais kanji formais ela ensina (3-4 por aula, conforme `Aula (intro)` em `Content/N5_Kanji.md`). Os kanji formais da aula são ensinados como **âncoras de reconhecimento** (forma → significado, com o radical como gancho mnemônico; a leitura é aprendida nas palavras) — **nunca** cobrar onyomi/kunyomi memorizados nem contagem de traços. Todos os demais kanji que aparecerem na aula são exclusivamente de reconhecimento (leitura) e sempre carregam furigana. **Proibido** criar exercícios que exijam ESCREVER kanji — o exame N5 não testa produção escrita. Exercícios podem cobrar kanji apenas em leitura (reconhecimento). A seção de kanji é um **primer composicional de 2 minutos** — não uma seção de estudo. O título "Chaves de Leitura" comunica ao aluno que o objetivo é entender a lógica de construção de palavras, não decorar kanji isolados.
13. **MACRO "GERAR AULA" (HTML, Anki & Upload):** Ao receber a instrução "Lesson X" / "Aula X", **NÃO** imprima a aula no chat. A IA DEVE OBRIGATORIAMENTE executar o seguinte pipeline eficiente e silencioso:
    - (a) **HTML:** Gerar a aula completa em HTML5 com CSS embutido (`Filters/HTML/HTML_Lesson.md`).
    - (b) **Upload HTML:** Salvar em um arquivo HTML temporário local e fazer upload executando o script: `node "../Google Workspace/Drive/scripts/upload_to_gdrive.js" "<temp_html_path>" "N5_LX.html"` — caminho **relativo à raiz do curso** (`Cursos - Linguas/Japones/`), para sobreviver a reorganizações de pasta. O script executa `scripts/validate_artifact.js` e **bloqueia** o upload se a validação reprovar; corrija o HTML e repita.
    - (c) **Anki TSV — vocabulário:** Gerar `Anki/N5_LX_Anki.tsv` no formato v2 especificado em `Anki/README_ANKI.md`: cabeçalhos `#separator:tab`, `#html:true`, `#notetype:N5 Vocab`, `#deck:Japonês::N5::Vocabulário`, `#tags column:5`; colunas `Palavra` (com ruby) · `Significado` · `Leitura` (kana puro, alimenta o TTS) · `Exemplo` (frase de contexto — **obrigatória da Aula 4 em diante**) · `Tags` (`aula::NN fase::N tipo::vocab`).
    - (d) **Anki TSV — gramática:** Gerar `Anki/N5_GX_Gramatica.tsv` com **2 cards por ponto gramatical** da aula, notetype `N5 Gramática`, colunas `Frase` (com lacuna + função comunicativa) · `Resposta` · `Estrutura` · `Explicacao` · `Tags`. **Este passo não é opcional:** sem ele a gramática fica sem nenhuma repetição espaçada, já que os `scope` das consolidações nunca revisitam um bloco anterior.
    - (e) **Validação:** Rodar `node scripts/validate_artifact.js` nos três artefatos e corrigir todo erro bloqueante antes de concluir.
    - (f) **Progress.md:** Marcar a Aula X como gerada no Mapa de Progresso.
    - (g) **Conclusão:** Apagar o arquivo HTML temporário e responder no chat com UMA mensagem curta confirmando o ID do GDrive e a criação dos dois TSVs. A tarefa só está concluída após entregar os TRÊS artefatos.
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

| Aula | Tipo | Fase | Tema | Gram | Kanji | Vocab | Cum.G | Cum.K | Cum.V |
|:---:|:---:|:---:|---|:---:|:---:|:---:|:---:|:---:|:---:|
| 1 | 📘 | 1 | Eu Sou — Copula & Perguntas | 3 | 3 | 25 | 3 | 3 | 25 |
| 2 | 📘 | 1 | Não Sou — Negação & Posse | 4 | 4 | 27 | 7 | 7 | 52 |
| 3 | 📘 | 1 | Minha Família & Números | 2 | 3 | 30 | 9 | 10 | 82 |
| 4 | 📘 | 1 | Meu Mundo — Conexões, Contexto & Intensidade | 5 | 3 | 25 | 14 | 13 | 107 |
| 5 | 🔄 | 1 | Consolidação — Aulas 1-4 | — | — | — | 14 | 13 | 107 |
| 6 | 📘 | 2 | Partículas de Lugar & Movimento | 3 | 4 | 31 | 17 | 17 | 138 |
| 7 | 📘 | 2 | Existe Aqui — ある・いる & Demonstrativos | 3 | 3 | 27 | 20 | 20 | 165 |
| 8 | 📘 | 2 | Pela Cidade — Locais & Transporte | 4 | 4 | 31 | 24 | 24 | 196 |
| 9 | 🔄 | 2 | Consolidação — Aulas 6-8 | — | — | — | 24 | 24 | 196 |
| 10 | 📘 | 3 | Adjetivos-い — Descrevendo o Mundo | 3 | 3 | 27 | 27 | 27 | 223 |
| 11 | 📘 | 3 | Adjetivos-な & Cores | 3 | 4 | 28 | 30 | 31 | 251 |
| 12 | 📘 | 3 | Mais Descrições & Advérbios | 3 | 3 | 28 | 33 | 34 | 279 |
| 13 | 🔄 | 3 | Consolidação — Aulas 10-12 | — | — | — | 33 | 34 | 279 |
| 14 | 📘 | 4 | Calendário & Datas | 3 | 4 | 27 | 36 | 38 | 306 |
| 15 | 📘 | 4 | Frequência & Sequência | 3 | 4 | 26 | 39 | 42 | 332 |
| 16 | 📘 | 4 | Gostos, Desejos & Comida | 4 | 3 | 30 | 43 | 45 | 362 |
| 17 | 📘 | 4 | Habilidades & Natureza | 3 | 3 | 30 | 46 | 48 | 392 |
| 18 | 🔄 | 4 | Consolidação — Aulas 14-17 | — | — | — | 46 | 48 | 392 |
| 19 | 📘 | 5 | Verbos & Conjugação: Fundamentos | 4 | 3 | 18 | 50 | 51 | 410 |
| 20 | 📘 | 5 | て-form: Progresso & Experiência | 4 | 4 | 27 | 54 | 55 | 437 |
| 21 | 📘 | 5 | て-form: Permissão & Estado | 3 | 3 | 27 | 57 | 58 | 464 |
| 22 | 🔄 | 5 | Consolidação — Aulas 19-21 | — | — | — | 57 | 58 | 464 |
| 23 | 📘 | 5 | Verbos do Cotidiano (Parte 1) | 4 | 3 | 27 | 61 | 61 | 491 |
| 24 | 📘 | 5 | Verbos do Cotidiano (Parte 2) | 4 | 3 | 27 | 65 | 64 | 518 |
| 25 | 📘 | 5 | Mais Verbos & Objetos do Dia-a-dia | 3 | 3 | 27 | 68 | 67 | 545 |
| 26 | 🔄 | 5 | Consolidação — Aulas 23-25 | — | — | — | 68 | 67 | 545 |
| 27 | 📘 | 6 | Obrigação & Proibição | 4 | 3 | 25 | 72 | 70 | 570 |
| 28 | 📘 | 6 | Convites & Sugestões | 4 | 3 | 25 | 76 | 73 | 595 |
| 29 | 📘 | 6 | Comparações & Contrastes | 4 | 3 | 24 | 80 | 76 | 619 |
| 30 | 🔄 | 6 | Consolidação — Aulas 27-29 | — | — | — | 80 | 76 | 619 |
| 31 | 📘 | 6 | Conectando Ideias & Explicações | 4 | 4 | 26 | 84 | 80 | 645 |
| 32 | 🔄 | — | Revisão Final & Simulado N5 | — | — | — | 84 | 80 | 645 |

Total: 84 grammar points, 80 kanji, 644 vocabulary items (todas as linhas do arquivo-fonte atribuídas exatamente uma vez a uma única aula).

---

## Curriculum Data (YAML)

O bloco abaixo define as 32 aulas do currículo em formato estruturado. Os números em `grammar` e `kanji` são referências de linha (row #) aos arquivos em `Content/N5_Grammar.md` e `Content/N5_Kanji.md`. O vocabulário NÃO faz parte do YAML — ele está definido nas seções `## Aula N` de `Content/N5_Vocabulary.md` (ver Regra 6). Para aulas de consolidação, `scope` lista as aulas de conteúdo cobertas na revisão. **Nota Importante para a IA geradora**: Todo o vocabulário da Aula X (seção `## Aula X` de `Content/N5_Vocabulary.md`) constitui um único "pool" que DEVE ser ensinado por completo, junto, na Seção "Vocabulário da Aula", conforme a Regra 6.

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
    kanji: [3, 35, 60]

    vocab: "Consultar N5_Vocabulary.md"

  2:
    type: content
    phase: 1
    title: "Não Sou — Negação, Posse & Inclusão"
    objective: "Negar identidade com じゃない, expressar posse com の, e adicionar com も. Aprender prefixos de polidez お/ご."
    grammar: [20, 52, 34, 59]
    kanji: [45, 56, 72, 76]

    vocab: "Consultar N5_Vocabulary.md"

  3:
    type: content
    phase: 1
    title: "Minha Família & Números"
    objective: "Contar de 1 a 10.000, usar が como marcador de sujeito, e apresentar alternativas com か〜か."
    grammar: [11, 22]
    kanji: [29, 33, 53]
    # NOTA: とても (grammar #77) foi MOVIDO daqui para a Aula 4. Motivo: とても
    # modifica adjetivos, e os primeiros adjetivos só entram na Aula 4 — ensiná-lo
    # aqui obrigava a construções marginais (とても + substantivo). Na Aula 4 ele
    # tem o que modificar. Não use とても em material da Aula 3.

    vocab: "Consultar N5_Vocabulary.md"

  4:
    type: content
    phase: 1
    title: "Meu Mundo — Conexões, Contexto & Intensidade"
    objective: "Listar com と (completo) e や (exemplos), limitar com だけ, perguntar tipo com どんな, e intensificar com とても — agora que há adjetivos para ele modificar. Vocabulário de corpo e identidade."
    grammar: [75, 82, 3, 8, 77]
    kanji: [2, 9, 51]
    # とても (#77) veio da Aula 3: ele modifica adjetivos, que estreiam aqui.

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
    kanji: [10, 20, 74, 77]

    vocab: "Consultar N5_Vocabulary.md"

  7:
    type: content
    phase: 2
    title: "Existe Aqui — ある・いる & Demonstrativos"
    objective: "Expressar existência de coisas (がある) e seres vivos (がいる), usar demonstrativos (これ/それ/あれ), e perguntar "por quê" (どうして)."
    grammar: [12, 14, 9]
    kanji: [25, 46, 57]

    vocab: "Consultar N5_Vocabulary.md"

  8:
    type: content
    phase: 2
    title: "Pela Cidade — Locais & Transporte"
    objective: "Nomear locais urbanos, meios de transporte, e itens da casa. Usar ね para confirmação, をください para pedir, はどうですか para opiniões e どうやって para perguntar o meio."
    grammar: [47, 61, 81, 10]
    kanji: [15, 31, 59, 67]

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
    kanji: [11, 22, 32]

    vocab: "Consultar N5_Vocabulary.md"

  11:
    type: content
    phase: 3
    title: "Adjetivos-な, Cores & Contrastes"
    objective: "Dominar adjetivos-な (な+N, じゃない), cores, e conectores de contraste でも e しかし."
    grammar: [36, 6, 62]
    kanji: [6, 13, 41, 70]

    vocab: "Consultar N5_Vocabulary.md"

  12:
    type: content
    phase: 3
    title: "Mais Descrições, Advérbios & Ênfase"
    objective: "Aprender advérbios de grau e modo, usar よ para ênfase, e conectores そして/それから para sequenciar ideias."
    grammar: [83, 64, 63]
    kanji: [4, 66, 79]

    vocab: "Consultar N5_Vocabulary.md"

  13:
    type: consolidation
    phase: 3
    title: "Consolidação — Aulas 10 a 12"
    scope: [10, 11, 12]
    review_prior: [1, 2, 3, 4]

  # ═══════════════════════════════════════════
  # FASE 4: TEMPO & DESEJOS — "Quando / O que quero"
  # ═══════════════════════════════════════════

  14:
    type: content
    phase: 4
    title: "Calendário & Datas"
    objective: "Expressar dias da semana e datas, e usar から (de/porque), まで (até), いつも (sempre)."
    grammar: [23, 29, 19]
    kanji: [1, 23, 26, 73]

    vocab: "Consultar N5_Vocabulary.md"

  15:
    type: content
    phase: 4
    title: "Frequência & Sequência Temporal"
    objective: "Falar sobre frequência (まだ/もう), hábitos, e marcar tempo com とき. Vocabulário de períodos relativos."
    grammar: [27, 35, 76]
    kanji: [14, 17, 27, 39]

    vocab: "Consultar N5_Vocabulary.md"

  16:
    type: content
    phase: 4
    title: "Gostos, Desejos & Comida"
    objective: "Expressar gostos (のが好き), desejos por coisas (がほしい) e ações (〜たい), e explicar com んです. Vocabulário de comida."
    grammar: [56, 13, 67, 46]
    kanji: [37, 54, 64]

    vocab: "Consultar N5_Vocabulary.md"

  17:
    type: content
    phase: 4
    title: "Habilidades, Natureza & Estações"
    objective: "Falar sobre habilidades (上手/下手) e ações conjuntas (一緒に). Vocabulário de natureza e estações."
    grammar: [55, 54, 18]
    kanji: [43, 52, 62]

    vocab: "Consultar N5_Vocabulary.md"

  18:
    type: consolidation
    phase: 4
    title: "Consolidação — Aulas 14 a 17"
    scope: [14, 15, 16, 17]
    review_prior: [6, 7, 8]

  # ═══════════════════════════════════════════
  # FASE 5: AÇÕES — "O que faço"
  # ═══════════════════════════════════════════

  19:
    type: content
    phase: 5
    title: "Verbos & Conjugação: Fundamentos"
    objective: "Sistematizar a conjugação dos 3 grupos de verbos (ます/て/ない/た), marcar o objeto com を, e usar てください (pedido), まえに (antes de) e のです (explicação formal). Esta aula inclui o MÓDULO DE CONJUGAÇÃO (seção 3E do Template A)."
    grammar: [72, 60, 53, 30]
    kanji: [5, 61, 75]

    vocab: "Consultar N5_Vocabulary.md"

  20:
    type: content
    phase: 5
    title: "て-form: Progresso & Experiência"
    objective: "Usar ている (ação em progresso/estado), てから (depois de fazer), たことがある (experiência passada) e まだ〜ていません (ainda não). Mais verbos de ação."
    grammar: [70, 71, 66, 28]
    kanji: [19, 44, 47, 50]

    vocab: "Consultar N5_Vocabulary.md"

  21:
    type: content
    phase: 5
    title: "て-form: Permissão & Proibição"
    objective: "Pedir e dar permissão (てもいい) e proibir (てはいけない/ちゃいけない)."
    grammar: [74, 73, 1]
    kanji: [28, 38, 65]

    vocab: "Consultar N5_Vocabulary.md"

  22:
    type: consolidation
    phase: 5
    title: "Consolidação — Aulas 19 a 21"
    scope: [19, 20, 21]
    review_prior: [10, 11, 12]

  23:
    type: content
    phase: 5
    title: "Verbos do Cotidiano (Parte 1)"
    objective: "Usar に行く (ir para fazer), にする (decidir), つもり (intenção) e なる (tornar-se). Verbos de rotina e casa."
    grammar: [49, 50, 78, 45]
    kanji: [12, 30, 69]

    vocab: "Consultar N5_Vocabulary.md"

  24:
    type: content
    phase: 5
    title: "Verbos do Cotidiano (Parte 2)"
    objective: "Listar ações representativas com たり〜たり, dar conselhos com ほうがいい, usar ないで (sem fazer), e けど (mas)."
    grammar: [68, 15, 38, 25]
    kanji: [21, 42, 78]

    vocab: "Consultar N5_Vocabulary.md"

  25:
    type: content
    phase: 5
    title: "Mais Verbos & Objetos do Dia-a-dia"
    objective: "Pedir para NÃO fazer com ないでください, contrastar formalmente com けれども. Vocabulário de objetos e vestuário."
    grammar: [39, 26, 69]
    kanji: [16, 24, 34]

    vocab: "Consultar N5_Vocabulary.md"

  26:
    type: consolidation
    phase: 5
    title: "Consolidação — Aulas 23 a 25"
    scope: [23, 24, 25]
    review_prior: [14, 15, 16, 17]

  # ═══════════════════════════════════════════
  # FASE 6: COMUNICAÇÃO — "Como me expresso"
  # ═══════════════════════════════════════════

  27:
    type: content
    phase: 6
    title: "Obrigação & Proibição"
    objective: "Expressar obrigação (ないといけない, なくてはいけない, なくてはならない, なくちゃ) em diferentes níveis de formalidade. Vocabulário de clima e obrigações."
    grammar: [40, 43, 44, 42]
    kanji: [40, 71, 80]

    vocab: "Consultar N5_Vocabulary.md"

  28:
    type: content
    phase: 6
    title: "Convites & Sugestões"
    objective: "Fazer convites (ませんか), propor ações conjuntas (ましょう), oferecer ajuda (ましょうか), e dispensar obrigação (なくてもいい)."
    grammar: [31, 32, 33, 41]
    kanji: [7, 8, 55]

    vocab: "Consultar N5_Vocabulary.md"

  29:
    type: content
    phase: 6
    title: "Comparações & Contrastes"
    objective: "Comparar (は〜より, より〜ほうが), superlativar (一番, の中で一番), e vocabulário escolar."
    grammar: [17, 57, 80, 84]
    kanji: [36, 48, 49]

    vocab: "Consultar N5_Vocabulary.md"

  30:
    type: consolidation
    phase: 6
    title: "Consolidação — Aulas 27 a 29"
    scope: [27, 28, 29]
    review_prior: [19, 20, 21]

  31:
    type: content
    phase: 6
    title: "Conectando Ideias & Explicações"
    objective: "Dar razões com ので, conjecturar com だろう/でしょう, e descrever métodos com 方. Vocabulário restante do N5."
    grammar: [58, 4, 7, 24]
    kanji: [18, 58, 63, 68]

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
