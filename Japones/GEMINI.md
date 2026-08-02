# GEMINI.md — JLPT N5 Self-Study Rules & Curriculum (32 Lessons)

## Purpose

This file is the single source of truth for the JLPT N5 self-study program. It defines the **rules** for study sessions and the **32-lesson curriculum** (24 content + 8 consolidation) that turns the raw reference files (`N5_Grammar.md`, `N5_Kanji.md`, `N5_Vocabulary.md`) into a structured, cumulative learning path optimized for a busy adult learner studying **1 lesson per week** with **Anki** support.

## How This System Works

1. **This file (GEMINI.md)** defines the curriculum: which grammar points, kanji, and vocabulary belong to each lesson, via row references to the data files.
2. **`Lesson.md`** defines the lesson output templates: formatting, section structure, and pedagogical standards for both content and consolidation lessons.
3. **The data files** (`N5_Grammar.md`, `N5_Kanji.md`, `N5_Vocabulary.md`) contain the raw reference data.

**Workflow:** When generating a lesson, the AI must (1) read the lesson definition here in GEMINI.md, (2) open the referenced rows in the data files to extract the raw content, and (3) format the output following the appropriate template in `Lesson.md`.

## Prerequisites

- **Hiragana and Katakana** are assumed to be fully mastered before starting Lesson 1. They are not taught in this curriculum. The student must be able to read all kana fluently.

## Student Profile

- **Occupation:** Medical resident (neurosurgery) — very limited study time
- **Pace:** 1 lesson per week (may extend to 2 weeks during heavy rotations)
- **SRS Tool:** Anki for daily vocabulary reinforcement (~10 min/day)
- **Target session:** ~50-60 minutes per content lesson, ~45 minutes per consolidation lesson

## Rules

1. Never leave any temporary file or script in this repository.
2. The data reference files live in `N5_Grammar.md`, `N5_Kanji.md`, `N5_Vocabulary.md`. They are read-only reference data — do not modify them during a study session.
3. **Cumulative principle:** Lessons build on each other. Lesson N assumes ALL content from lessons 1 to N-1 is mastered. Example sentences and practice questions for lesson N may freely use grammar, kanji, and vocabulary from lessons 1..N, but must NOT use content from lessons N+1 or beyond.
4. **Row references:** Each lesson references rows in the data files by row number. Before teaching, open the referenced rows and read them.
5. **Two lesson types:**
   - **📘 Content lessons** teach new grammar, kanji, and vocabulary following Template A in `Lesson.md`.
   - **🔄 Consolidation lessons** review and reinforce the previous 3-4 content lessons following Template B in `Lesson.md`. They introduce NO new content.
6. **Vocabulary classification:**
   - **Focus (~15 words):** Fully taught in the lesson body with 4-layer examples, collocations, and nuances.
   - **Anki (~12 words):** Listed in a reference table. The student adds them to Anki and reviews throughout the week.
7. **Lesson teaching format (content lessons):**
   - **Review (5 min):** Quick recap of the previous lesson's most important points. Show 3-5 review questions. *(Skip for Lesson 1.)*
   - **Grammar (core):** Teach each grammar point — pattern, meaning, usage, contrast, 2-3 example sentences using ONLY cumulative vocabulary.
   - **Kanji:** Present new kanji with onyomi/kunyomi, stroke hints, 2-3 compounds using cumulative vocabulary.
   - **Focus Vocabulary:** Present focus words grouped by **semantic theme** with full examples.
   - **Anki Vocabulary:** Present Anki words in a reference table.
   - **Practice (end):** Exercises including **interleaved** questions mixing current and past content.
8. Never use a grammar point in examples before it has been introduced.
9. Teach in **Portuguese (PT-BR)**. Write Japanese examples with kanji + hiragana reading. All explanations, translations, and instructions must be in Portuguese.
10. **Session commands:** "Lesson N" → teach lesson N. "Review" → cumulative review. "Drill" → generate practice.

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
| 2 | 📘 | 1 | Não Sou — Negação & Posse | 4 | 3 | 15 | 12 | 7 | 6 | 52 |
| 3 | 📘 | 1 | Minha Família & Números | 3 | 3 | 15 | 13 | 10 | 9 | 80 |
| 4 | 📘 | 1 | Meu Mundo — Conexões & Contexto | 4 | 3 | 15 | 12 | 14 | 12 | 107 |
| 5 | 🔄 | 1 | Consolidação — Aulas 1-4 | — | — | — | — | 14 | 12 | 107 |
| 6 | 📘 | 2 | Partículas de Lugar & Movimento | 4 | 4 | 15 | 12 | 18 | 16 | 134 |
| 7 | 📘 | 2 | Existe Aqui — ある・いる | 4 | 3 | 15 | 12 | 22 | 19 | 161 |
| 8 | 📘 | 2 | Pela Cidade — Locais & Transporte | 3 | 3 | 15 | 13 | 25 | 22 | 189 |
| 9 | 🔄 | 2 | Consolidação — Aulas 6-8 | — | — | — | — | 25 | 22 | 189 |
| 10 | 📘 | 3 | Adjetivos-い — Descrevendo o Mundo | 3 | 3 | 15 | 12 | 28 | 25 | 216 |
| 11 | 📘 | 3 | Adjetivos-な & Cores | 3 | 4 | 15 | 13 | 31 | 29 | 244 |
| 12 | 📘 | 3 | Mais Descrições & Advérbios | 3 | 3 | 15 | 12 | 34 | 32 | 271 |
| 13 | 🔄 | 3 | Consolidação — Aulas 10-12 | — | — | — | — | 34 | 32 | 271 |
| 14 | 📘 | 4 | Calendário & Datas | 3 | 4 | 15 | 12 | 37 | 36 | 298 |
| 15 | 📘 | 4 | Frequência & Sequência | 4 | 3 | 15 | 11 | 41 | 39 | 324 |
| 16 | 📘 | 4 | Gostos, Desejos & Comida | 4 | 3 | 15 | 12 | 45 | 42 | 351 |
| 17 | 📘 | 4 | Habilidades & Natureza | 3 | 3 | 15 | 12 | 48 | 45 | 378 |
| 18 | 🔄 | 4 | Consolidação — Aulas 14-17 | — | — | — | — | 48 | 45 | 378 |
| 19 | 📘 | 5 | Verbos & て-form: Fundamentos | 4 | 3 | 15 | 12 | 52 | 48 | 405 |
| 20 | 📘 | 5 | て-form: Pedidos & Progresso | 3 | 4 | 15 | 12 | 55 | 52 | 432 |
| 21 | 📘 | 5 | て-form: Permissão & Estado | 3 | 3 | 15 | 12 | 58 | 55 | 459 |
| 22 | 🔄 | 5 | Consolidação — Aulas 19-21 | — | — | — | — | 58 | 55 | 459 |
| 23 | 📘 | 5 | Verbos do Cotidiano (Parte 1) | 3 | 3 | 15 | 12 | 61 | 58 | 486 |
| 24 | 📘 | 5 | Verbos do Cotidiano (Parte 2) | 4 | 3 | 15 | 12 | 65 | 61 | 513 |
| 25 | 📘 | 5 | Mais Verbos & Atividades | 3 | 3 | 15 | 12 | 68 | 64 | 540 |
| 26 | 🔄 | 5 | Consolidação — Aulas 23-25 | — | — | — | — | 68 | 64 | 540 |
| 27 | 📘 | 6 | Obrigação & Proibição | 4 | 3 | 15 | 10 | 72 | 67 | 565 |
| 28 | 📘 | 6 | Convites & Sugestões | 4 | 3 | 15 | 10 | 76 | 70 | 590 |
| 29 | 📘 | 6 | Comparações & Contrastes | 4 | 3 | 15 | 10 | 80 | 73 | 615 |
| 30 | 🔄 | 6 | Consolidação — Aulas 27-29 | — | — | — | — | 80 | 73 | 615 |
| 31 | 📘 | 6 | Conectando Ideias & Explicações | 4 | 4 | 15 | 14 | 84 | 77 | 644 |
| 32 | 🔄 | — | Revisão Final & Simulado N5 | — | — | — | — | 84 | 77 | 644 |

Total: 84 grammar points, 77 kanji (direct instruction) + 3 kanji (reviewed via compounds), 644 vocabulary items.

---

# FASE 1: FUNDAÇÕES — "Quem sou eu"

---

## Aula 1: 📘 Eu Sou — Copula, は & Perguntas

**Objetivo:** Apresentar-se, afirmar identidade com です/だ, marcar o tópico com は, e formar perguntas com か.

### Gramática (N5_Grammar.md)
Refs: #2 (da/desu), #79 (wa), #21 (ka)

### Kanji (N5_Kanji.md)
Refs: #2 (一), #8 (二), #13 (三)

### Vocabulário Foco (N5_Vocabulary.md) — 15 palavras
- **Pronomes:** #612 私, #15 あなた
- **Identidade:** #375 名前, #172 人, #116 学生, #492 先生
- **Básico:** #176 本, #97 英語, #308 国, #319 今日, #192 今
- **Expressões:** #133 はい, #94 ええ, #90 どうも, #91 どうぞ

### Vocabulário Anki (N5_Vocabulary.md) — 10 palavras
#113 外国, #114 外国人, #237 漢字, #297 言葉, #471 留学生, #487 生徒, #231 会社, #202 医者, #212 じゃあ, #472 さあ

---

## Aula 2: 📘 Não Sou — Negação, Posse & Inclusão

**Objetivo:** Negar identidade com じゃない, expressar posse com の, e adicionar com も. Aprender prefixos de polidez お/ご.

### Gramática (N5_Grammar.md)
Refs: #20 (janai/dewa nai), #52 (no), #34 (mo), #59 (o/go)

### Kanji (N5_Kanji.md)
Refs: #4 (人), #9 (本), #6 (大)

### Vocabulário Foco (N5_Vocabulary.md) — 15 palavras
- **Família (própria):** #57 父, #132 母, #17 兄, #16 姉, #445 弟, #194 妹
- **Família (alheia):** #444 お父さん, #412 お母さん, #425 お兄さん, #423 お姉さん
- **Relações:** #255 家族, #470 両親, #320 兄弟, #280 子供, #573 友達

### Vocabulário Anki (N5_Vocabulary.md) — 12 palavras
#404 おばあさん, #405 伯母さん, #411 伯父さん, #417 奥さん, #418 お巡りさん, #256 警官, #248 家庭, #439 男, #426 女, #440 男の子, #427 女の子, #441 大人

---

## Aula 3: 📘 Minha Família & Números

**Objetivo:** Contar de 1 a 10.000, usar が como marcador de sujeito, intensificar com とても, e apresentar alternativas com か〜か.

### Gramática (N5_Grammar.md)
Refs: #11 (ga), #77 (totemo), #22 (ka~ka)

### Kanji (N5_Kanji.md)
Refs: #26 (四), #22 (五), #37 (六)

### Vocabulário Foco (N5_Vocabulary.md) — 15 palavras
- **Números cardinais:** #183 一, #388 二, #479 三, #498 四, #122 五, #466 六, #499 七, #130 八, #322 九, #222 十
- **Números grandes:** #182 百, #490 千, #334 万, #460 零, #643 ゼロ

### Vocabulário Anki (N5_Vocabulary.md) — 13 palavras
#174 一つ, #108 二つ, #356 三つ, #630 四つ, #209 五つ, #368 六つ, #376 七つ, #622 八つ, #284 九つ, #173 一人, #107 二人, #191 いくつ, #190 いくら

---

## Aula 4: 📘 Meu Mundo — Conexões & Contexto

**Objetivo:** Listar com と (completo) e や (exemplos), limitar com だけ, e perguntar tipo com どんな. Vocabulário de corpo e identidade.

### Gramática (N5_Grammar.md)
Refs: #75 (to), #82 (ya), #3 (dake), #8 (donna)

### Kanji (N5_Kanji.md)
Refs: #42 (七), #36 (八), #29 (九)

### Vocabulário Foco (N5_Vocabulary.md) — 15 palavras
- **Corpo:** #33 頭, #340 目, #349 耳, #142 鼻, #303 口, #129 歯, #557 手, #29 足, #484 背, #422 お腹, #239 体
- **Perguntas:** #71 誰, #72 誰か, #84 どこ, #85 どなた

### Vocabulário Anki (N5_Vocabulary.md) — 12 palavras
#7 十, #184 一番, #421 同じ, #640 有名, #178 本当, #258 結構, #530 少し, #548 沢山, #554 縦, #642 全部, #207 いつ, #377 何

---

## Aula 5: 🔄 Consolidação — Aulas 1 a 4

**Escopo:** Revisão ativa de todo conteúdo das Aulas 1 a 4 (cumulativo).
Seguir Template B de `Lesson.md`.

**Conteúdo coberto:**
- Gramática: です/だ, じゃない, は, か, の, も, お/ご, が, とても, か〜か, と, や, だけ, どんな (14 pontos)
- Kanji: 一, 二, 三, 四, 五, 六, 七, 八, 九, 人, 本, 大 (12 kanji)
- Vocabulário: 107 palavras

---

# FASE 2: ESPAÇO — "Onde estou"

---

## Aula 6: 📘 Partículas de Lugar & Movimento

**Objetivo:** Dominar に (destino/tempo/existência), で (local da ação/meio), を (objeto direto), e に/へ (direção).

### Gramática (N5_Grammar.md)
Refs: #48 (ni), #5 (de), #60 (wo), #51 (ni/e)

### Kanji (N5_Kanji.md)
Refs: #3 (国), #24 (上), #38 (下), #35 (外)

### Vocabulário Foco (N5_Vocabulary.md) — 15 palavras
- **Locais básicos:** #186 家, #161 部屋, #66 台所, #117 玄関, #395 庭
- **Posições:** #596 上, #510 下, #372 中, #524 外, #326 前, #601 後ろ
- **Direções:** #346 右, #162 左, #574 隣, #516 そば

### Vocabulário Anki (N5_Vocabulary.md) — 12 palavras
#626 横, #366 向こう, #159 辺, #225 角, #343 道, #302 交差点, #152 橋, #324 町, #367 村, #555 建物, #197 入口, #74 出口

---

## Aula 7: 📘 Existe Aqui — ある・いる & Demonstrativos

**Objetivo:** Expressar existência de coisas (がある) e seres vivos (がいる), usar demonstrativos (これ/それ/あれ), e perguntar "por quê" e "como".

### Gramática (N5_Grammar.md)
Refs: #12 (ga arimasu), #14 (ga imasu), #9 (doushite), #10 (douyatte)

### Kanji (N5_Kanji.md)
Refs: #10 (中), #43 (山), #62 (木)

### Vocabulário Foco (N5_Vocabulary.md) — 15 palavras
- **Demonstrativos (isso):** #295 これ, #522 それ, #23 あれ, #282 ここ, #519 そこ, #32 あそこ
- **Demonstrativos (qual):** #87 どれ, #82 どっち, #83 どちら
- **Pré-nominais:** #289 この, #520 その, #18 あの, #86 どの
- **Verbos:** #24 ある, #201 居る

### Vocabulário Anki (N5_Vocabulary.md) — 12 palavras
#3 あっち, #4 あちら, #517 そっち, #518 そちら, #278 こっち, #279 こちら, #288 こんな, #163 東, #394 西, #275 北, #350 南, #565 戸

---

## Aula 8: 📘 Pela Cidade — Locais & Transporte

**Objetivo:** Nomear locais urbanos, meios de transporte, e itens da casa. Usar ね para confirmação, をください para pedir, はどうですか para opiniões.

### Gramática (N5_Grammar.md)
Refs: #47 (ne), #61 (o kudasai), #81 (wa dou desu ka)

### Kanji (N5_Kanji.md)
Refs: #25 (東), #52 (川), #41 (小)

### Vocabulário Foco (N5_Vocabulary.md) — 15 palavras
- **Locais:** #115 学校, #67 大学, #53 病院, #98 駅, #582 図書館, #301 公園, #464 レストラン, #354 店, #120 銀行
- **Transporte:** #314 車, #77 電車, #43 バス, #549 タクシー, #164 飛行機, #62 地下鉄

### Vocabulário Anki (N5_Vocabulary.md) — 13 palavras
#79 デパート, #274 喫茶店, #513 食堂, #637 郵便局, #299 交番, #321 教室, #455 プール, #21 アパート, #205 椅子, #590 机, #558 テーブル, #325 窓, #81 ドア

---

## Aula 9: 🔄 Consolidação — Aulas 6 a 8

**Escopo:** Revisão ativa de todo conteúdo das Aulas 6 a 8 (cumulativo desde Aula 1).
Seguir Template B de `Lesson.md`.

---

# FASE 3: DESCRIÇÃO — "Como é"

---

## Aula 10: 📘 Adjetivos-い — Descrevendo o Mundo

**Objetivo:** Dominar adjetivos-い: forma afirmativa, negativa (〜くない), passada (〜かった), e modificação de substantivos.

### Gramática (N5_Grammar.md)
Refs: #16 (i-adjectives), #65 (sugiru), #37 (naa)

### Kanji (N5_Kanji.md)
Refs: #11 (長), #32 (高), #33 (円)

### Vocabulário Foco (N5_Vocabulary.md) — 15 palavras
- **Tamanho/Forma:** #429 大きい, #59 小さい, #370 長い, #347 短い, #547 高い, #167 低い, #109 太い, #180 細い
- **Qualidade:** #34 新しい, #106 古い, #624 良い, #609 悪い, #369 難しい, #618 易しい, #420 面白い

### Vocabulário Anki (N5_Vocabulary.md) — 12 palavras
#619 安い, #244 軽い, #419 重い, #169 広い, #489 狭い, #595 強い, #633 弱い, #157 速い, #158 早い, #436 遅い, #602 薄い, #592 詰まらない

---

## Aula 11: 📘 Adjetivos-な, Cores & Contrastes

**Objetivo:** Dominar adjetivos-な (な+N, じゃない), cores, e conectores de contraste でも e しかし.

### Gramática (N5_Grammar.md)
Refs: #36 (na-adjectives), #6 (demo), #62 (shikashi)

### Kanji (N5_Kanji.md)
Refs: #27 (今), #28 (金), #40 (気), #70 (白)

### Vocabulário Foco (N5_Vocabulary.md) — 15 palavras
- **な-adjectives:** #269 綺麗, #512 静か, #390 賑やか, #118 元気, #68 大丈夫, #219 丈夫, #465 立派, #47 便利, #168 暇
- **Cores:** #6 赤, #7 赤い, #19 青, #20 青い, #311 黒, #312 黒い

### Vocabulário Anki (N5_Vocabulary.md) — 13 palavras
#507 白, #508 白い, #263 黄色い, #344 緑, #55 茶色, #198 色, #199 色々, #430 大きな, #60 小さな, #160 下手, #220 上手, #545 大切, #544 大変

---

## Aula 12: 📘 Mais Descrições, Advérbios & Ênfase

**Objetivo:** Aprender advérbios de grau e modo, usar よ para ênfase, e conectores そして/それから para sequenciar ideias.

### Gramática (N5_Grammar.md)
Refs: #83 (yo), #64 (soshite), #63 (sore kara)

### Kanji (N5_Kanji.md)
Refs: #21 (生), #34 (子), #31 (学)

### Vocabulário Foco (N5_Vocabulary.md) — 15 palavras
- **Sensações térmicas:** #37 暑い, #478 寒い, #35 暖かい, #539 涼しい, #39 熱い, #593 冷たい, #402 温い
- **Advérbios:** #64 ちょっと, #65 丁度, #70 だんだん, #88 どう, #137 初めて, #384 何故, #526 直ぐに, #635 ゆっくり

### Vocabulário Anki (N5_Vocabulary.md) — 12 palavras
#2 危ない, #8 明るい, #309 暗い, #12 甘い, #339 不味い, #203 忙しい, #206 痛い, #251 可愛い, #276 汚い, #336 丸い, #607 若い, #38 厚い

---

## Aula 13: 🔄 Consolidação — Aulas 10 a 12

**Escopo:** Revisão ativa de todo conteúdo das Aulas 10 a 12 (cumulativo desde Aula 1).
Seguir Template B de `Lesson.md`.

---

# FASE 4: TEMPO & DESEJOS — "Quando" e "O que quero"

---

## Aula 14: 📘 Calendário & Datas

**Objetivo:** Expressar dias da semana, meses, datas, e usar から (de/porque), まで (até), いつも (sempre).

### Gramática (N5_Grammar.md)
Refs: #23 (kara), #29 (made), #19 (itsumo)

### Kanji (N5_Kanji.md)
Refs: #1 (日), #14 (時), #17 (月), #18 (分)

### Vocabulário Foco (N5_Vocabulary.md) — 15 palavras
- **Dias da semana:** #389 日曜日, #119 月曜日, #252 火曜日, #527 水曜日, #358 木曜日, #266 金曜日, #92 土曜日
- **Períodos:** #26 朝, #170 昼, #629 夜, #638 夕方, #123 午後, #125 午前
- **Tempo:** #216 時間, #569 時

### Vocabulário Anki (N5_Vocabulary.md) — 12 palavras
#185 一日, #110 二日, #348 三日, #625 四日, #208 五日, #365 六日, #378 七日, #632 八日, #283 九日, #576 十日, #156 二十日, #584 一日(tsuitachi)

---

## Aula 15: 📘 Frequência & Sequência Temporal

**Objetivo:** Falar sobre frequência (まだ/もう), hábitos, e marcar tempo com とき. Vocabulário de períodos relativos.

### Gramática (N5_Grammar.md)
Refs: #27 (mada), #28 (mada~te imasen), #35 (mou), #76 (toki)

### Kanji (N5_Kanji.md)
Refs: #23 (間), #5 (年), #7 (十)

### Vocabulário Foco (N5_Vocabulary.md) — 14 palavras
- **Frequência:** #330 毎日, #328 毎朝, #329 毎晩, #331 毎週, #333 毎月, #332 毎年, #570 時々
- **Relativo:** #265 昨日, #30 明日, #28 明後日, #318 去年, #298 今年, #457 来年
- **Extras:** #568 時計, #140 半

### Vocabulário Anki (N5_Vocabulary.md) — 11 palavras
#259 今朝, #286 今晩, #287 今月, #290 今週, #491 先月, #493 先週, #456 来月, #458 来週, #442 一昨日, #443 一昨年, #481 再来年

---

## Aula 16: 📘 Gostos, Desejos & Comida

**Objetivo:** Expressar gostos (のが好き), desejos por coisas (がほしい) e ações (〜たい), e explicar com んです. Vocabulário de comida.

### Gramática (N5_Grammar.md)
Refs: #56 (no ga suki), #13 (ga hoshii), #67 (tai), #46 (ndesu)

### Kanji (N5_Kanji.md)
Refs: #64 (食), #54 (水), #44 (話)

### Vocabulário Foco (N5_Vocabulary.md) — 15 palavras
- **Sentimentos:** #529 好き, #69 大好き, #268 嫌い, #211 嫌, #179 欲しい
- **Comida:** #124 ご飯, #27 朝ご飯, #171 昼ご飯, #41 晩ご飯, #639 夕飯, #449 パン, #550 卵, #392 肉, #474 魚, #617 野菜

### Vocabulário Anki (N5_Vocabulary.md) — 12 palavras
#304 果物, #52 豚肉, #127 牛肉, #578 鶏肉, #483 砂糖, #506 塩, #514 醬油, #44 バター, #241 カレー, #541 食べ物, #397 飲み物, #469 料理

---

## Aula 17: 📘 Habilidades, Natureza & Estações

**Objetivo:** Falar sobre habilidades (上手/下手), ações conjuntas (一緒に), e planos (つもり). Vocabulário de natureza e estações.

### Gramática (N5_Grammar.md)
Refs: #55 (no ga jouzu), #54 (no ga heta), #18 (issho ni)

### Kanji (N5_Kanji.md)
Refs: #56 (男), #45 (女), #50 (先)

### Vocabulário Foco (N5_Vocabulary.md) — 15 palavras
- **Bebidas:** #291 コーヒー, #300 紅茶, #408 お茶, #128 牛乳, #433 お酒, #357 水
- **Natureza:** #141 花, #261 木, #250 川, #598 海, #614 山, #521 空
- **Estações:** #149 春, #382 夏, #10 秋, #112 冬

### Vocabulário Anki (N5_Vocabulary.md) — 12 palavras
#204 一緒, #195 犬, #385 猫, #577 鳥, #89 動物, #452 ペット, #383 夏休み, #93 絵, #95 映画, #96 映画館, #424 音楽, #533 スポーツ

---

## Aula 18: 🔄 Consolidação — Aulas 14 a 17

**Escopo:** Revisão ativa de todo conteúdo das Aulas 14 a 17 (cumulativo desde Aula 1).
Seguir Template B de `Lesson.md`.

---

# FASE 5: AÇÕES — "O que faço"

---

## Aula 19: 📘 Verbos & て-form: Fundamentos

**Objetivo:** Aprender os primeiros verbos essenciais, formar o て-form dos 3 grupos, e usar てください (pedido), なる (tornar-se), e 前に (antes de).

### Gramática (N5_Grammar.md)
Refs: #72 (te kudasai), #45 (naru), #30 (mae ni), #53 (no desu)

### Kanji (N5_Kanji.md)
Refs: #15 (行), #39 (来), #30 (入)

### Vocabulário Foco (N5_Vocabulary.md) — 15 palavras
- **Movimento:** #189 行く, #313 来る, #226 帰る, #80 出る, #134 入る, #25 歩く, #153 走る
- **Cotidiano básico:** #542 食べる, #398 飲む, #353 見る, #264 聞く, #234 書く, #628 読む, #387 寝る, #415 起きる

### Vocabulário Anki (N5_Vocabulary.md) — 12 palavras
#144 話す, #210 言う, #608 分かる, #509 知る, #407 覚える, #610 忘れる, #586 使う, #200 要る, #296 答える, #381 習う, #435 教える, #155 働く

---

## Aula 20: 📘 て-form: Pedidos & Progresso

**Objetivo:** Usar ている (ação em progresso/estado), てから (depois de fazer), e たことがある (experiência passada). Mais verbos de ação.

### Gramática (N5_Grammar.md)
Refs: #70 (te iru), #71 (te kara), #66 (ta koto ga aru)

### Kanji (N5_Kanji.md)
Refs: #16 (見), #63 (聞), #49 (書), #75 (読)

### Vocabulário Foco (N5_Vocabulary.md) — 15 palavras
- **Ações domésticas:** #22 洗う, #525 掃除, #494 洗濯, #591 作る, #249 買う, #599 売る
- **Ações com objetos:** #9 開ける, #11 開く, #502 閉める, #501 閉まる, #260 消す, #262 消える
- **Interação:** #40 会う, #338 待つ, #623 呼ぶ

### Vocabulário Anki (N5_Vocabulary.md) — 12 palavras
#230 買い物, #463 練習, #515 宿題, #511 質問, #480 散歩, #143 話, #620 休み, #500 仕事, #221 授業, #46 勉強, #475 先, #36 後

---

## Aula 21: 📘 て-form: Permissão, Proibição & Estado

**Objetivo:** Pedir e dar permissão (てもいい), proibir (てはいけない/ちゃいけない), e descrever estado resultante (てある).

### Gramática (N5_Grammar.md)
Refs: #74 (temo ii), #73 (te wa ikenai), #1 (cha ikenai)

### Kanji (N5_Kanji.md)
Refs: #65 (車), #58 (電), #51 (名)

### Vocabulário Foco (N5_Vocabulary.md) — 15 palavras
- **Transporte (ações):** #400 乗る, #432 降りる, #572 止まる, #566 飛ぶ, #327 曲がる, #611 渡る
- **Vestir/Corpo:** #273 着る, #139 履く, #401 脱ぐ, #503 締める, #1 浴びる
- **Dar/Receber:** #5 上げる, #246 貸す, #243 借りる, #613 渡す

### Vocabulário Anki (N5_Vocabulary.md) — 12 palavras
#215 自動車, #218 自転車, #100 エレベーター, #229 階段, #467 廊下, #409 お風呂, #413 お金, #473 財布, #228 鍵, #245 傘, #236 紙, #103 服

---

## Aula 22: 🔄 Consolidação — Aulas 19 a 21

**Escopo:** Revisão ativa de todo conteúdo das Aulas 19 a 21 (cumulativo desde Aula 1).
Seguir Template B de `Lesson.md`.

---

## Aula 23: 📘 Verbos do Cotidiano (Parte 1)

**Objetivo:** Usar に行く (ir para fazer), にする (decidir), e んです (explicação). Verbos de rotina e casa.

### Gramática (N5_Grammar.md)
Refs: #49 (ni iku), #50 (ni suru), #78 (tsumori)

### Kanji (N5_Kanji.md)
Refs: #59 (校), #60 (語), #12 (出)

### Vocabulário Foco (N5_Vocabulary.md) — 15 palavras
- **Ações domésticas:** #416 置く, #362 持つ, #579 取る, #556 立つ, #538 座る, #437 押す, #165 引く
- **Cozinha/Refeição:** #151 箸, #534 スプーン, #371 ナイフ, #102 フォーク, #294 コップ, #238 カップ, #56 茶碗, #434 お皿

### Vocabulário Anki (N5_Vocabulary.md) — 12 palavras
#232 掛かる, #233 掛ける, #379 並べる, #380 並ぶ, #73 出す, #196 入れる, #587 つける, #588 付ける, #75 出かける, #589 着く, #594 勤める, #532 住む

---

## Aula 24: 📘 Verbos do Cotidiano (Parte 2)

**Objetivo:** Listar ações representativas com たり〜たり, dar conselhos com ほうがいい, usar ないで (sem fazer), e けど (mas).

### Gramática (N5_Grammar.md)
Refs: #68 (tari~tari), #15 (hou ga ii), #38 (naide), #25 (kedo)

### Kanji (N5_Kanji.md)
Refs: #78 (休), #66 (何), #69 (毎)

### Vocabulário Foco (N5_Vocabulary.md) — 15 palavras
- **Atividades:** #31 遊ぶ, #447 泳ぐ, #396 登る, #604 歌う, #166 弾く, #345 磨く, #621 休む
- **Ações diversas:** #552 頼む, #285 困る, #374 無くす, #505 死ぬ, #373 鳴く, #476 咲く, #585 疲れる, #597 生まれる

### Vocabulário Anki (N5_Vocabulary.md) — 12 palavras
#459 ラジオ, #563 テレビ, #121 ギター, #603 歌, #406 お弁当, #414 お菓子, #14 飴, #240 辛い, #410 美味しい, #428 多い, #531 少ない, #600 煩い

---

## Aula 25: 📘 Mais Verbos & Objetos do Dia-a-dia

**Objetivo:** Pedir para NÃO fazer com ないでください, contrastar formalmente com けれども. Vocabulário de objetos e vestuário.

### Gramática (N5_Grammar.md)
Refs: #39 (naide kudasai), #26 (keredo mo), #69 (te aru)

### Kanji (N5_Kanji.md)
Refs: #19 (後), #20 (前), #46 (北)

### Vocabulário Foco (N5_Vocabulary.md) — 15 palavras
- **Verbos restantes:** #58 違う, #227 返す, #355 見せる, #580 撮る, #272 切る, #537 吸う, #136 始まる, #446 終わる, #616 やる
- **Vestuário:** #316 靴, #317 靴下, #50 帽子, #386 ネクタイ, #528 スカート, #292 コート

### Vocabulário Anki (N5_Vocabulary.md) — 12 palavras
#496 シャツ, #605 上着, #631 洋服, #644 ズボン, #486 セーター, #488 石鹼, #497 シャワー, #461 冷蔵庫, #536 ストーブ, #454 ポスト, #567 トイレ, #438 お手洗い

---

## Aula 26: 🔄 Consolidação — Aulas 23 a 25

**Escopo:** Revisão ativa de todo conteúdo das Aulas 23 a 25 (cumulativo desde Aula 1).
Seguir Template B de `Lesson.md`.

---

# FASE 6: COMUNICAÇÃO — "Como me expresso"

---

## Aula 27: 📘 Obrigação & Proibição

**Objetivo:** Expressar obrigação (ないといけない, なくてはいけない, なくてはならない, なくちゃ) em diferentes níveis de formalidade. Vocabulário de clima e obrigações.

### Gramática (N5_Grammar.md)
Refs: #40 (naito ikenai), #43 (nakute wa ikenai), #44 (nakute wa naranai), #42 (nakucha)

### Kanji (N5_Kanji.md)
Refs: #71 (天), #80 (雨), #67 (南)

### Vocabulário Foco (N5_Vocabulary.md) — 15 palavras
- **Clima:** #562 天気, #13 雨, #634 雪, #253 風, #147 晴れ, #306 曇り
- **Verbos de clima:** #148 晴れる, #307 曇る, #104 吹く, #105 降る
- **Obrigações:** #359 門, #315 薬, #254 風邪, #54 病気, #305 下さい

### Vocabulário Anki (N5_Vocabulary.md) — 10 palavras
#543 多分, #337 真っ直ぐ, #364 もう一度, #627 よく, #247 方, #571 所, #281 声, #361 物, #360 問題, #193 意味

---

## Aula 28: 📘 Convites & Sugestões

**Objetivo:** Fazer convites (ませんか), propor ações conjuntas (ましょう), oferecer ajuda (ましょうか), e dispensar obrigação (なくてもいい).

### Gramática (N5_Grammar.md)
Refs: #31 (masen ka), #32 (mashou), #33 (mashouka), #41 (naku temo ii)

### Kanji (N5_Kanji.md)
Refs: #47 (午), #48 (百), #53 (千)

### Vocabulário Foco (N5_Vocabulary.md) — 15 palavras
- **Viagem:** #468 旅行, #181 ホテル, #267 切符, #546 大使館, #393 荷物
- **Comunicação:** #78 電話, #76 電気, #495 写真, #561 手紙, #277 切手, #131 葉書
- **Expressões:** #187 いかが, #523 それでは, #448 パーティー, #214 自分

### Vocabulário Anki (N5_Vocabulary.md) — 10 palavras
#581 年, #145 半分, #154 二十歳, #636 昨夜, #391 日記, #551 誕生日, #257 結婚, #431 大勢, #351 皆さん, #352 みんな

---

## Aula 29: 📘 Comparações & Contrastes

**Objetivo:** Comparar (は〜より, より〜ほうが), superlativar (一番, の中で一番), e vocabulário escolar.

### Gramática (N5_Grammar.md)
Refs: #17 (ichiban), #57 (no naka de ichiban), #80 (wa~yori), #84 (yori~hou ga)

### Kanji (N5_Kanji.md)
Refs: #68 (万), #61 (土), #73 (火)

### Vocabulário Foco (N5_Vocabulary.md) — 15 palavras
- **Escrita/Escola:** #99 鉛筆, #48 ボールペン, #335 万年筆, #451 ペン, #399 ノート, #63 地図, #217 辞書, #213 字引, #504 新聞, #641 雑誌
- **Objetos:** #235 カメラ, #242 カレンダー, #342 眼鏡, #293 コピー, #564 テスト

### Vocabulário Anki (N5_Vocabulary.md) — 9 palavras
#310 クラス, #477 作文, #450 ページ, #51 文章, #615 八百屋, #575 遠い, #61 近い, #363 もっと, #270 キログラム

---

## Aula 30: 🔄 Consolidação — Aulas 27 a 29

**Escopo:** Revisão ativa de todo conteúdo das Aulas 27 a 29 (cumulativo desde Aula 1).
Seguir Template B de `Lesson.md`.

---

## Aula 31: 📘 Conectando Ideias & Explicações

**Objetivo:** Dar razões com ので, conjecturar com だろう/でしょう, e descrever métodos com 方. Vocabulário restante do N5.

### Gramática (N5_Grammar.md)
Refs: #58 (node), #4 (darou), #7 (deshou), #24 (kata)

### Kanji (N5_Kanji.md)
Refs: #72 (母), #79 (父), #74 (右), #77 (左)

### Vocabulário Foco (N5_Vocabulary.md) — 15 palavras
- **Objetos restantes:** #138 箱, #177 本棚, #224 花瓶, #135 灰皿, #453 ポケット, #223 かばん, #111 封筒, #146 ハンカチ, #323 マッチ
- **Medidas:** #341 メートル, #271 キロメートル, #126 グラム
- **Mídia:** #559 テープ, #560 テープレコーダー, #462 レコード

### Vocabulário Anki (N5_Vocabulary.md) — 13 palavras
#101 フィルム, #535 スリッパ, #606 ワイシャツ, #485 背広, #540 たばこ, #403 ニュース, #175 ほか, #583 次, #49 ボタン, #150 貼る, #482 差す, #55 半

---

## Aula 32: 🔄 Revisão Final & Simulado N5

**Escopo:** Revisão geral de TODO o conteúdo do currículo (Aulas 1 a 31).
Seguir Template B de `Lesson.md`, com as seguintes adições:

**Formato especial desta aula:**
1. **Recall completo** de todos os 77 kanji
2. **Exercício de gramática** cobrindo todas as 84 estruturas em formato de simulado
3. **Diálogo longo** (10+ turnos) integrando vocabulário e gramática de todas as fases
4. **Autodiagnóstico final** com plano de revisão para itens fracos
5. **Mini-simulado N5** com questões no formato oficial do JLPT

---

## Cumulative Mastery Tracker

| After Lesson | Grammar | Kanji | Vocab |
|:---:|:---:|:---:|:---:|
| 1 | 3 | 3 | 25 |
| 2 | 7 | 6 | 52 |
| 3 | 10 | 9 | 80 |
| 4 | 14 | 12 | 107 |
| 5 (consol) | 14 | 12 | 107 |
| 6 | 18 | 16 | 134 |
| 7 | 22 | 19 | 161 |
| 8 | 25 | 22 | 189 |
| 9 (consol) | 25 | 22 | 189 |
| 10 | 28 | 25 | 216 |
| 11 | 31 | 29 | 244 |
| 12 | 34 | 32 | 271 |
| 13 (consol) | 34 | 32 | 271 |
| 14 | 37 | 36 | 298 |
| 15 | 41 | 39 | 324 |
| 16 | 45 | 42 | 351 |
| 17 | 48 | 45 | 378 |
| 18 (consol) | 48 | 45 | 378 |
| 19 | 52 | 48 | 405 |
| 20 | 55 | 52 | 432 |
| 21 | 58 | 55 | 459 |
| 22 (consol) | 58 | 55 | 459 |
| 23 | 61 | 58 | 486 |
| 24 | 65 | 61 | 513 |
| 25 | 68 | 64 | 540 |
| 26 (consol) | 68 | 64 | 540 |
| 27 | 72 | 67 | 565 |
| 28 | 76 | 70 | 590 |
| 29 | 80 | 73 | 615 |
| 30 (consol) | 80 | 73 | 615 |
| 31 | 84 | 77 | 644 |
| 32 (consol) | 84 | 77 | 644 |

**Session commands:**
- "Lesson N" → teach lesson N (cumulative scope).
- "Review" → cumulative review of everything covered so far.
- "Drill" → generate practice material from cumulative content.
- "Continue" → resume the last lesson practice section.
