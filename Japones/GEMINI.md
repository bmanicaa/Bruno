# GEMINI.md — JLPT N5 Self-Study Rules & Curriculum

## Purpose

This file is the single source of truth for the JLPT N5 self-study program. It defines the **rules** for study sessions and the **10-lesson curriculum** that turns the raw reference files (`N5_Grammar.md`, `N5_Kanji.md`, `N5_Vocabulary.md`) into a structured, cumulative learning path.

## How This System Works

1. **This file (GEMINI.md)** defines the curriculum: which grammar points, kanji, and vocabulary belong to each lesson, via row references to the data files.
2. **`Lesson.md`** defines the lesson output template: the exact formatting, section structure, and pedagogical standards the AI must follow when generating a lesson.
3. **The data files** (`N5_Grammar.md`, `N5_Kanji.md`, `N5_Vocabulary.md`) contain the raw reference data.

**Workflow:** When generating a lesson, the AI must (1) read the lesson definition here in GEMINI.md, (2) open the referenced rows in the data files to extract the raw content, and (3) format the output following the template in `Lesson.md`.

## Prerequisites

- **Hiragana and Katakana** are assumed to be fully mastered before starting Lesson 1. They are not taught in this curriculum. The student must be able to read all kana fluently.

## Rules

1. Never leave any temporary file or script in this repository.
2. The data reference files live in `Japones/N5_Grammar.md`, `Japones/N5_Kanji.md`, `Japones/N5_Vocabulary.md`. They are read-only reference data — do not modify them during a study session.
3. **Cumulative principle:** Lessons build on each other. Lesson N assumes ALL content from lessons 1 to N-1 is mastered. Example sentences and practice questions for lesson N may freely use grammar, kanji, and vocabulary from lessons 1..N, but must NOT use content from lessons N+1 or beyond.
4. **Row references:** Each lesson references rows in the data files by row number. Before teaching, open the referenced rows and read them.
5. **Lesson teaching format:**
   - **Review (2 min):** Quick recap of the previous lesson's most important points. Show 3-5 review questions. *(Skip for Lesson 1.)*
   - **Grammar (core):** Teach each grammar point — pattern, meaning, usage, contrast, 2-3 example sentences using ONLY cumulative vocabulary.
   - **Kanji:** Present new kanji with onyomi/kunyomi, stroke hints, 2-3 compounds using cumulative vocabulary.
   - **Vocabulary:** Present new words grouped by **semantic theme** (e.g., family, numbers, body, places, food) for easier memorization — regardless of how they are organized by grammatical class in the data files. Include example sentences (cumulative).
   - **Practice (end):** Fill-in-blank, translation, sentence building, or conversation prompts.
6. Never use a grammar point in examples before it has been introduced.
7. Teach in **Portuguese (PT-BR)**. Write Japanese examples with kanji + hiragana reading. All explanations, translations, and instructions must be in Portuguese.
8. **Session commands:** "Lesson N" → teach lesson N. "Review" → cumulative review. "Drill" → generate practice.

## Distribution overview

| Lesson | Theme | Grammar pts | New Kanji | New Vocab | Cumulative grammar | Cumulative kanji | Cumulative vocab |
|---|---|---|---|---|---|---|---|
| 1 | Foundations & Self-Intro | 9 | 8 | 94 | 9 | 8 | 94 |
| 2 | Particles, Existence & Location | 9 | 8 | 120 | 18 | 16 | 214 |
| 3 | Adjectives & Describing | 8 | 8 | 95 | 26 | 24 | 309 |
| 4 | Time, Sequence & Frequency | 9 | 8 | 61 | 35 | 32 | 370 |
| 5 | Wants, Likes & Skills | 8 | 8 | 71 | 43 | 40 | 441 |
| 6 | て-form Actions & States | 8 | 8 | 106 | 51 | 48 | 547 |
| 7 | Obligation & Permission | 9 | 8 | 15 | 60 | 56 | 562 |
| 8 | Invitations & Suggestions | 8 | 8 | 8 | 68 | 64 | 570 |
| 9 | Comparisons & Choice | 7 | 8 | 4 | 75 | 72 | 574 |
| 10 | Connecting & Explaining | 9 | 8 | 70 | 84 | 80 | 644 |

Total: 84 grammar points, 80 kanji, 644 vocabulary items.

## Lesson 1: Foundations & Self-Intro

**Goal:** Introduce yourself, state identity/possession, form basic affirmative/negative/question sentences with the copula.

### Grammar (N5_Grammar.md)
Refs: #2, #20, #79, #11, #34, #21, #52, #59, #77

### Kanji (N5_Kanji.md)
Refs: #1, #2, #4, #6, #8, #9, #10, #13

### Vocabulary (N5_Vocabulary.md) — 94 new words
    - **Pronoun:** #15 あなた, #71 誰, #72 誰か, #84 どこ, #612 私
    - **Noun:** #16 姉, #17 兄, #33 頭, #57 父, #85 どなた, #94 ええ, #97 英語, #107 二人, #108 二つ, #113 外国, #114 外国人, #116 学生, #122 五, #129 歯, #130 八, #132 母, #133 はい, #142 鼻, #172 人, #173 一人, #174 一つ, #176 本, #182 百, #183 一, #190 いくら, #192 今, #194 妹, #202 医者, #209 五つ, #222 十, #231 会社, #237 漢字, #239 体, #248 家庭, #255 家族, #256 警官, #280 子供, #284 九つ, #297 言葉, #303 口, #308 国, #319 今日, #320 兄弟, #322 九, #334 万, #340 目, #349 耳, #356 三つ, #368 六つ, #375 名前, #376 七つ, #388 二, #404 おばあさん, #405 伯母さん, #411 伯父さん, #412 お母さん, #417 奥さん, #418 お巡りさん, #422 お腹, #423 お姉さん, #425 お兄さん, #426 女, #427 女の子, #439 男, #440 男の子, #441 大人, #444 お父さん, #445 弟, #460 零, #466 六, #470 両親, #471 留学生, #479 三, #484 背, #487 生徒, #490 千, #492 先生, #498 四, #499 七, #557 手, #573 友達, #622 八つ, #630 四つ, #643 ゼロ
    - **Adverb:** #90 どうも, #91 どうぞ, #191 いくつ
    - **Conjunction:** #212 じゃあ, #472 さあ

## Lesson 2: Particles, Existence & Location

**Goal:** Say where things/people are, describe location, use particles に/で/へ/を correctly.

### Grammar (N5_Grammar.md)
Refs: #5, #48, #51, #60, #12, #14, #75, #82, #8

### Kanji (N5_Kanji.md)
Refs: #3, #19, #20, #24, #35, #38, #43, #62

### Vocabulary (N5_Vocabulary.md) — 120 new words
    - **Pronoun:** #3 あっち, #4 あちら, #23 あれ, #32 あそこ, #82 どっち, #83 どちら, #87 どれ, #282 ここ, #295 これ, #517 そっち, #518 そちら, #519 そこ, #522 それ
    - **Noun:** #21 アパート, #43 バス, #45 ベッド, #49 ボタン, #50 帽子, #53 病院, #62 地下鉄, #66 台所, #67 大学, #74 出口, #76 電気, #77 電車, #78 電話, #79 デパート, #81 ドア, #98 駅, #100 エレベーター, #103 服, #115 学校, #117 玄関, #120 銀行, #152 橋, #159 辺, #161 部屋, #162 左, #163 東, #164 飛行機, #186 家, #188 池, #197 入口, #205 椅子, #215 自動車, #218 自転車, #225 角, #228 鍵, #229 階段, #236 紙, #245 傘, #274 喫茶店, #275 北, #278 こっち, #279 こちら, #292 コート, #299 交番, #301 公園, #302 交差点, #314 車, #316 靴, #317 靴下, #321 教室, #324 町, #325 窓, #326 前, #343 道, #346 右, #350 南, #354 店, #366 向こう, #367 村, #372 中, #386 ネクタイ, #394 西, #395 庭, #409 お風呂, #413 お金, #438 お手洗い, #454 ポスト, #455 プール, #461 冷蔵庫, #464 レストラン, #467 廊下, #473 財布, #486 セーター, #488 石鹼, #496 シャツ, #497 シャワー, #510 下, #513 食堂, #516 そば, #524 外, #528 スカート, #536 ストーブ, #549 タクシー, #555 建物, #558 テーブル, #565 戸, #567 トイレ, #574 隣, #582 図書館, #590 机, #596 上, #601 後ろ, #605 上着, #615 八百屋, #626 横, #631 洋服, #637 郵便局, #644 ズボン
    - **Pre-noun adjectival:** #18 あの, #86 どの, #288 こんな, #289 この, #520 その
    - **Verb:** #24 ある, #201 居る
    - **Adjective:** #575 遠い
    - **い-adjective:** #61 近い

## Lesson 3: Adjectives & Describing

**Goal:** Describe people, objects and situations using い- and な-adjectives, colors, and degree words.

### Grammar (N5_Grammar.md)
Refs: #16, #36, #17, #65, #3, #9, #10, #47

### Kanji (N5_Kanji.md)
Refs: #11, #21, #27, #28, #32, #33, #40, #41

### Vocabulary (N5_Vocabulary.md) — 95 new words
    - **Noun:** #6 赤, #19 青, #55 茶色, #118 元気, #160 下手, #168 暇, #198 色, #199 色々, #220 上手, #258 結構, #311 黒, #337 真っ直ぐ, #344 緑, #507 白, #530 少し, #544 大変, #545 大切, #548 沢山, #554 縦, #642 全部
    - **Pre-noun adjectival:** #60 小さな, #430 大きな
    - **Adjective:** #2 危ない, #7 赤い, #8 明るい, #12 甘い, #20 青い, #34 新しい, #35 暖かい, #37 暑い, #38 厚い, #39 熱い, #59 小さい, #68 大丈夫, #109 太い, #157 速い, #158 早い, #180 細い, #203 忙しい, #206 痛い, #219 丈夫, #244 軽い, #251 可愛い, #263 黄色い, #269 綺麗, #276 汚い, #309 暗い, #336 丸い, #339 不味い, #347 短い, #369 難しい, #370 長い, #390 賑やか, #402 温い, #420 面白い, #428 多い, #429 大きい, #436 遅い, #465 立派, #478 寒い, #508 白い, #512 静か, #539 涼しい, #543 多分, #547 高い, #553 楽しい, #592 詰まらない, #595 強い, #602 薄い, #607 若い, #609 悪い, #618 易しい, #619 安い, #624 良い, #633 弱い
    - **Adverb:** #64 ちょっと, #65 丁度, #70 だんだん, #88 どう, #137 初めて, #384 何故, #526 直ぐに, #627 よく, #635 ゆっくり
    - **Expression:** #364 もう一度
    - **い-adjective:** #106 古い, #167 低い, #169 広い, #312 黒い, #419 重い, #489 狭い, #531 少ない, #593 冷たい, #600 煩い
    - **な-adjective:** #47 便利

## Lesson 4: Time, Sequence & Frequency

**Goal:** Talk about when, how long, and how often things happen.

### Grammar (N5_Grammar.md)
Refs: #23, #29, #30, #76, #27, #28, #19, #35, #42

### Kanji (N5_Kanji.md)
Refs: #7, #14, #17, #18, #23, #36, #37, #42

### Vocabulary (N5_Vocabulary.md) — 61 new words
    - **Pronoun:** #207 いつ
    - **Noun:** #26 朝, #28 明後日, #30 明日, #36 後, #92 土曜日, #110 二日, #119 月曜日, #123 午後, #125 午前, #140 半, #145 半分, #154 二十歳, #156 二十日, #170 昼, #171 昼ご飯, #185 一日, #208 五日, #216 時間, #252 火曜日, #259 今朝, #265 昨日, #266 金曜日, #283 九日, #286 今晩, #287 今月, #290 今週, #298 今年, #318 去年, #328 毎朝, #329 毎晩, #330 毎日, #331 毎週, #332 毎年, #333 毎月, #348 三日, #358 木曜日, #365 六日, #378 七日, #389 日曜日, #442 一昨日, #443 一昨年, #456 来月, #457 来年, #458 来週, #481 再来年, #491 先月, #493 先週, #527 水曜日, #551 誕生日, #568 時計, #569 時, #570 時々, #576 十日, #581 年, #584 一日, #625 四日, #629 夜, #632 八日, #636 昨夜, #638 夕方

## Lesson 5: Wants, Likes & Skills

**Goal:** Express desires, likes/dislikes, abilities and skills.

### Grammar (N5_Grammar.md)
Refs: #13, #67, #56, #55, #54, #18, #46, #78

### Kanji (N5_Kanji.md)
Refs: #31, #44, #45, #50, #51, #56, #59, #60

### Vocabulary (N5_Vocabulary.md) — 71 new words
    - **Noun:** #10 秋, #14 飴, #27 朝ご飯, #41 晩ご飯, #44 バター, #52 豚肉, #56 茶碗, #89 動物, #93 絵, #95 映画, #96 映画館, #112 冬, #121 ギター, #124 ご飯, #127 牛肉, #128 牛乳, #141 花, #149 春, #151 箸, #195 犬, #204 一緒, #211 嫌, #238 カップ, #241 カレー, #250 川, #261 木, #268 嫌い, #291 コーヒー, #294 コップ, #300 紅茶, #304 果物, #357 水, #371 ナイフ, #382 夏, #383 夏休み, #385 猫, #397 飲み物, #406 お弁当, #408 お茶, #414 お菓子, #424 音楽, #433 お酒, #434 お皿, #449 パン, #452 ペット, #459 ラジオ, #469 料理, #474 魚, #483 砂糖, #506 塩, #514 醬油, #521 空, #529 好き, #533 スポーツ, #534 スプーン, #541 食べ物, #550 卵, #563 テレビ, #577 鳥, #578 鶏肉, #598 海, #603 歌, #614 山, #617 野菜, #639 夕飯
    - **Verb:** #396 登る, #604 歌う
    - **Adjective:** #69 大好き, #179 欲しい
    - **い-adjective:** #240 辛い, #410 美味しい

## Lesson 6: て-form Actions & States

**Goal:** Use the て-form to connect actions, make requests, and describe ongoing/completed states.

### Grammar (N5_Grammar.md)
Refs: #72, #70, #71, #69, #74, #73, #45, #66

### Kanji (N5_Kanji.md)
Refs: #15, #16, #30, #39, #52, #54, #58, #65

### Vocabulary (N5_Vocabulary.md) — 106 new words
    - **Noun:** #143 話, #230 買い物, #463 練習, #475 先, #480 散歩, #494 洗濯, #511 質問, #515 宿題, #525 掃除, #620 休み
    - **Verb:** #1 浴びる, #5 上げる, #9 開ける, #11 開く, #22 洗う, #25 歩く, #31 遊ぶ, #40 会う, #58 違う, #73 出す, #75 出かける, #80 出る, #134 入る, #136 始まる, #139 履く, #144 話す, #153 走る, #155 働く, #165 引く, #166 弾く, #189 行く, #196 入れる, #200 要る, #210 言う, #226 帰る, #227 返す, #232 掛かる, #233 掛ける, #234 書く, #243 借りる, #246 貸す, #249 買う, #260 消す, #262 消える, #264 聞く, #272 切る, #273 着る, #285 困る, #296 答える, #313 来る, #327 曲がる, #338 待つ, #345 磨く, #353 見る, #355 見せる, #362 持つ, #373 鳴く, #374 無くす, #379 並べる, #380 並ぶ, #381 習う, #387 寝る, #398 飲む, #400 乗る, #401 脱ぐ, #407 覚える, #415 起きる, #416 置く, #432 降りる, #435 教える, #437 押す, #446 終わる, #447 泳ぐ, #476 咲く, #501 閉まる, #502 閉める, #503 締める, #505 死ぬ, #509 知る, #532 住む, #537 吸う, #538 座る, #542 食べる, #552 頼む, #556 立つ, #566 飛ぶ, #572 止まる, #579 取る, #580 撮る, #585 疲れる, #586 使う, #587 つける, #588 付ける, #589 着く, #591 作る, #594 勤める, #597 生まれる, #599 売る, #608 分かる, #610 忘れる, #611 渡る, #613 渡す, #616 やる, #621 休む, #623 呼ぶ, #628 読む

## Lesson 7: Obligation & Permission

**Goal:** Express must/must not, permission, and give advice.

### Grammar (N5_Grammar.md)
Refs: #40, #43, #44, #41, #38, #39, #1, #15, #68

### Kanji (N5_Kanji.md)
Refs: #25, #29, #46, #55, #57, #67, #68, #71

### Vocabulary (N5_Vocabulary.md) — 15 new words
    - **Noun:** #13 雨, #46 勉強, #147 晴れ, #221 授業, #253 風, #306 曇り, #359 門, #500 仕事, #562 天気, #634 雪
    - **Verb:** #104 吹く, #105 降る, #148 晴れる, #307 曇る
    - **Expression:** #305 下さい

## Lesson 8: Invitations & Suggestions

**Goal:** Invite, offer, suggest, and respond politely.

### Grammar (N5_Grammar.md)
Refs: #31, #32, #33, #61, #49, #50, #81, #63

### Kanji (N5_Kanji.md)
Refs: #12, #22, #26, #34, #47, #48, #53, #63

### Vocabulary (N5_Vocabulary.md) — 8 new words
    - **Noun:** #181 ホテル, #267 切符, #393 荷物, #448 パーティー, #468 旅行, #546 大使館
    - **Adverb:** #187 いかが
    - **Expression:** #523 それでは

## Lesson 9: Comparisons & Choice

**Goal:** Compare two or more things and express preferences.

### Grammar (N5_Grammar.md)
Refs: #84, #80, #57, #6, #25, #62, #64

### Kanji (N5_Kanji.md)
Refs: #5, #49, #61, #64, #66, #69, #70, #72

### Vocabulary (N5_Vocabulary.md) — 4 new words
    - **Noun:** #184 一番, #421 同じ, #640 有名
    - **Adverb:** #363 もっと

## Lesson 10: Connecting & Explaining

**Goal:** Connect sentences, give reasons, explain situations, and handle more complex expression.

### Grammar (N5_Grammar.md)
Refs: #58, #4, #7, #24, #26, #22, #37, #83, #53

### Kanji (N5_Kanji.md)
Refs: #73, #74, #75, #76, #77, #78, #79, #80

### Vocabulary (N5_Vocabulary.md) — 70 new words
    - **Pronoun:** #214 自分
    - **Noun:** #29 足, #42 番号, #48 ボールペン, #51 文章, #54 病気, #63 地図, #99 鉛筆, #101 フィルム, #102 フォーク, #111 封筒, #126 グラム, #131 葉書, #135 灰皿, #138 箱, #146 ハンカチ, #175 ほか, #177 本棚, #178 本当, #193 意味, #213 字引, #217 辞書, #223 かばん, #224 花瓶, #235 カメラ, #242 カレンダー, #247 方, #254 風邪, #257 結婚, #270 キログラム, #271 キロメートル, #277 切手, #281 声, #293 コピー, #310 クラス, #315 薬, #323 マッチ, #335 万年筆, #341 メートル, #342 眼鏡, #351 皆さん, #352 みんな, #360 問題, #361 物, #377 何, #391 日記, #392 肉, #399 ノート, #403 ニュース, #431 大勢, #450 ページ, #451 ペン, #453 ポケット, #462 レコード, #477 作文, #485 背広, #495 写真, #504 新聞, #535 スリッパ, #540 たばこ, #559 テープ, #560 テープレコーダー, #561 手紙, #564 テスト, #571 所, #583 次, #606 ワイシャツ, #641 雑誌
    - **Verb:** #150 貼る, #482 差す

---
## Cumulative Mastery Tracker

| After Lesson | Grammar mastered | Kanji mastered | Vocab mastered |
|---|---|---|---|
| 1 | 9 | 8 | 94 |
| 2 | 18 | 16 | 214 |
| 3 | 26 | 24 | 309 |
| 4 | 35 | 32 | 370 |
| 5 | 43 | 40 | 441 |
| 6 | 51 | 48 | 547 |
| 7 | 60 | 56 | 562 |
| 8 | 68 | 64 | 570 |
| 9 | 75 | 72 | 574 |
| 10 | 84 | 80 | 644 |

**Session commands:**
- "Lesson N" → teach lesson N (cumulative scope).
- "Review" → cumulative review of everything covered so far.
- "Drill" → generate practice material from cumulative content.
- "Continue" → resume the last lesson practice section.
