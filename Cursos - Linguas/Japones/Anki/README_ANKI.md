# 🃏 Anki v2 — Tipos de Nota, Templates e Importação

Este arquivo é a especificação do lado Anki do curso. Ele existe porque o deck
legado (notetype `Básico`, 2 campos, sem tags, sem áudio) tinha três limitações
estruturais:

1. **A gramática não entrava no Anki.** Só vocabulário. Como nenhuma aula de
   consolidação revisita um bloco anterior (os `scope` cobrem apenas o bloco
   imediatamente anterior), a gramática da Aula 2 só reaparecia na Aula 32 —
   **27 semanas** sem nenhuma recuperação. O deck `N5 Gramática` fecha isso.
2. **Sem tags**, era impossível cumprir a promessa do Template B
   ("revise os itens ⚠️/❌ com prioridade no deck Anki") — não havia como filtrar.
3. **Só a direção reconhecimento (JP→PT).** A direção de produção (PT→JP) nunca
   era treinada, e conhecimento só-de-reconhecimento não transfere para produção.

---

## 1. Tipos de nota

### `N5 Vocab` — 4 campos

| # | Campo | Conteúdo |
|---|---|---|
| 1 | `Palavra` | Palavra com `<ruby>` (ex.: `<ruby>会社<rt>かいしゃ</rt></ruby>`) |
| 2 | `Significado` | Tradução PT-BR, sem o prefixo de leitura |
| 3 | `Leitura` | **Kana puro** — é o campo que alimenta o TTS |
| 4 | `Exemplo` | Frase de contexto com ruby. **Preenchido nos 81 cards das Aulas 1-3** e obrigatório daqui em diante. As frases vivem em `scripts/exemplos_vocab.js`. |

As tags vêm da coluna 5 do TSV (`#tags column:5`) e caem nas tags nativas do Anki.

### `N5 Gramática` — 4 campos

| # | Campo | Conteúdo |
|---|---|---|
| 1 | `Frase` | Frase com lacuna `___` + função comunicativa entre parênteses |
| 2 | `Resposta` | A forma que preenche a lacuna |
| 3 | `Estrutura` | Fórmula sintática (ex.: `N1 + の + N2`) |
| 4 | `Explicacao` | Por que é essa forma, com o contraste relevante |

> Campos **sem acento** de propósito (`Explicacao`): nomes de campo com acento
> funcionam, mas complicam referências em templates e filtros de busca.

---

## 2. Templates dos cartões

### `N5 Vocab` — Cartão 1: Reconhecimento (JP → PT)

**Frente**
```html
<div class="ja">{{Palavra}}</div>
{{tts ja_JP:Leitura}}
```

**Verso**
```html
{{FrontSide}}
<hr id="answer">
<div class="pt">{{Significado}}</div>
{{#Exemplo}}<div class="ex">{{Exemplo}}</div>{{/Exemplo}}
```

### `N5 Vocab` — Cartão 2: Produção (PT → JP)

**Frente**
```html
<div class="pt">{{Significado}}</div>
<div class="hint">— escreva em japonês —</div>
```

**Verso**
```html
{{FrontSide}}
<hr id="answer">
<div class="ja">{{Palavra}}</div>
<div class="kana">{{Leitura}}</div>
{{tts ja_JP:Leitura}}
```

### `N5 Gramática` — cartão único

**Frente**
```html
<div class="ja">{{Frase}}</div>
```

**Verso**
```html
{{FrontSide}}
<hr id="answer">
<div class="resp">{{Resposta}}</div>
<div class="est">{{Estrutura}}</div>
<div class="exp">{{Explicacao}}</div>
```

### CSS (o mesmo para os dois tipos)

```css
.card {
  font-family: "Noto Sans JP", "Hiragino Sans", sans-serif;
  font-size: 22px;
  text-align: center;
  color: black;
  background-color: white;
}
.ja   { font-size: 40px; line-height: 2.0; }
.pt   { font-size: 24px; }
.kana { font-size: 20px; color: #777; margin-top: 6px; }
.resp { font-size: 34px; color: #0284c7; margin: 10px 0; }
.est  { font-size: 18px; color: #777; font-family: monospace; }
.exp  { font-size: 18px; margin-top: 14px; text-align: left; line-height: 1.6; }
.ex   { font-size: 20px; color: #666; margin-top: 14px; }
.hint { font-size: 14px; color: #999; margin-top: 8px; }
ruby rt { font-size: 0.5em; color: #888; font-weight: normal; }

.nightMode .card { color: #eee; background-color: #1a1a1a; }
.nightMode .kana, .nightMode .est, .nightMode .ex { color: #999; }
.nightMode .resp { color: #38bdf8; }
.nightMode ruby rt { color: #999; }
```

---

## 3. Áudio: TTS nativo, sem arquivos

`{{tts ja_JP:Leitura}}` usa a voz japonesa **do próprio aparelho**. Não há
arquivos de áudio no repositório, nenhuma API e nenhum custo.

**Por que o campo `Leitura` e não `Palavra`:** os filtros `furigana:`/`kana:` do
Anki só entendem a notação de colchetes (`漢字[かんじ]`), não o `<ruby>` HTML que
este curso usa. Passar `Palavra` ao TTS faria o motor ler a base **e** o `<rt>`.
`Leitura` já é kana puro, então sai limpo.

**Disponibilidade de voz:**

| Plataforma | Situação |
|---|---|
| Android / iOS | Voz japonesa nativa disponível (no iOS, Kyoko). Funciona de imediato. |
| Windows | **Este PC não tem voz japonesa instalada** — só pt-BR e en-US (verificado). Para habilitar: Configurações → Hora e idioma → Idioma → Adicionar idioma → 日本語, marcando "Fala". |

Se não houver voz, o Anki apenas não toca nada — o cartão continua funcionando.

**Limitação honesta:** o TTS de aparelho erra **acento tonal** com alguma
frequência, principalmente em compostos e homógrafos (箸 vs 橋). No N5 isso
raramente bloqueia compreensão, mas não trate o TTS como referência de pitch.
E TTS **não é treino de 聴解**: fala limpa, um locutor, ritmo uniforme. A escuta
de verdade (fala conectada, multi-locutor) fica com o material externo.

---

## 4. Importação

### Primeira vez (criar os tipos de nota)

1. **Ferramentas → Gerenciar tipos de notas → Adicionar → Clonar: Básico**;
   nomeie `N5 Vocab`. Em **Campos**, deixe exatamente:
   `Palavra`, `Significado`, `Leitura`, `Exemplo`.
   Em **Cartões**, crie os dois cartões da seção 2 e cole o CSS.
2. Repita para `N5 Gramática`, com os campos
   `Frase`, `Resposta`, `Estrutura`, `Explicacao` e o cartão único.
3. **Arquivo → Importar** cada `.tsv`. Os cabeçalhos `#notetype:`, `#deck:` e
   `#tags column:5` já vêm no arquivo — o Anki lê tudo sozinho.

### Migrando as notas que você já estudou

As Aulas 1-3 já foram importadas no notetype `Básico`. Para **não perder o
histórico de revisão**:

> Navegador → selecione as notas do deck antigo → **Notas → Alterar tipo de
> nota** → destino `N5 Vocab` → mapeie `Frente`→`Palavra`, `Verso`→`Significado`,
> deixe `Leitura` e `Exemplo` vazios. Depois reimporte os TSVs: o Anki casa pelo
> primeiro campo e preenche `Leitura`, `Exemplo` e as tags.

O caminho alternativo (apagar o deck e reimportar) é mais simples, mas
**zera o agendamento** dos 81 cards já em circulação.

### FSRS

Recomendado ligar: **Opções do deck → Agendamento avançado → FSRS**. O
agendador clássico (SM-2) usa intervalos fixos; o FSRS ajusta por card a partir
do seu histórico real. Para quem estuda em janelas irregulares — plantão,
semanas puladas — a diferença é relevante, porque o FSRS lida melhor com atrasos
do que o SM-2, que penaliza o card atrasado de forma indiscriminada.

---

## 5. Convenção de tags

```
aula::01 … aula::32      ← qual aula introduziu o item
fase::1 … fase::6        ← fase do currículo
tipo::vocab | tipo::gramatica
gramatica::<slug>        ← só no deck de gramática (ex.: gramatica::wa-topico)
```

Isso é o que torna possível o estudo dirigido prometido no Template B. Exemplos
de busca no Anki:

```
tag:aula::02 tag:tipo::gramatica     → só a gramática da Aula 2
tag:fase::1 is:due                   → tudo da Fase 1 que está vencido
tag:gramatica::wa-topico             → todos os cards de は
prop:due>0 tag:tipo::gramatica       → gramática pendente, para um baralho filtrado
```

---

## 6. Regeneração

```bash
node scripts/build_anki.js          # converte/normaliza + injeta as frases de exemplo
node scripts/seed_gramatica.js      # regenera os TSVs de gramática
node scripts/validate_artifact.js Anki/*.tsv    # valida ruby/furigana
```

`build_anki.js` lê as frases de `scripts/exemplos_vocab.js` e avisa quais palavras
ainda estão sem exemplo. É idempotente: rodar de novo sobre um arquivo já
convertido não o corrompe. Ele também deduplica pela palavra-base — foi assim que apareceram
as 3 duplicatas de `四`, `五` e `六` no TSV da Aula 3, que o Anki não detectaria
sozinho porque compara o campo bruto, e as leituras diferiam.
