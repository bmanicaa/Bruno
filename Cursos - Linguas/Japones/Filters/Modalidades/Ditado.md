# ESPECIFICAÇÃO TÉCNICA: MODALIDADE DITADO (`Filters/Modalidades/Ditado.md`)

Modalidade de **transcrição de áudio externo**. É a única do sistema cujo insumo
**não é gerado por este repositório**.

---

## 🎯 0. PREMISSA — POR QUE ESTA MODALIDADE EXISTE ASSIM

O repositório **não gera áudio, e isso é deliberado.** TTS produz fala limpa, um
locutor só e ritmo uniforme. O 聴解 do JLPT N5 cobra 課題理解, ポイント理解,
発話表現 e 即時応答 — diálogo multi-locutor em velocidade natural, com reduções,
prosódia e sobreposição de turnos. Um módulo de escuta sintético *pareceria*
treino de escuta e treinaria a coisa errada, o que é pior do que não ter nada.

Então a divisão é:

| Papel | Quem faz |
|---|---|
| Fornecer áudio autêntico | **Material externo do estudante** |
| Medir, diagnosticar e registrar | **Este repositório** |

**O ganho pedagógico específico do ditado** é que ele ataca o gargalo real da
escuta em japonês: a fala não tem fronteiras de palavra, e segmentar o fluxo
sonoro é o que quebra o iniciante. O ditado força (a) segmentação, (b)
recuperação de ortografia a partir de fonologia — direção inversa a todo o resto
do curso — e (c) **expõe exatamente o que não foi ouvido**. Numa questão de
múltipla escolha o estudante acerta sem saber se entendeu ou deduziu pelo
contexto; se ele transcreve 「ともだち」 onde era 「ともだちが」, a partícula perdida
fica visível. Sem isso, a escuta externa fica não-medida, e a ilusão de
compreensão é o modo de falha clássico do treino de escuta.

---

## ⛔ 1. REGRAS INVIOLÁVEIS

1. **A IA NUNCA inventa o áudio nem o gabarito.** É proibido "supor" o que o
   material externo dizia. A correção só é exata quando o estudante fornece a
   transcrição oficial (Modo A). Sem ela, vale o Modo B, que **não** produz nota.
2. **Zero Romaji.** A transcrição do estudante é em kana + kanji. Nomes
   estrangeiros vão obrigatoriamente em katakana.
3. **Furigana NÃO se aplica à transcrição do estudante.** Ele escreve como
   ouviu — exigir ruby aqui destruiria o propósito. O furigana volta a valer no
   **gabarito e nas explicações**, que seguem a política universal da Regra 11.
4. **Escopo cumulativo NÃO se aplica ao áudio.** O material externo é escrito
   para um aluno N5 genérico e conterá palavras fora do inventário — isso é
   esperado e saudável (input compreensível tolera desconhecidos). O escopo
   cumulativo governa apenas o que a IA **escreve** nas explicações.
5. **Registro obrigatório em `Progress.md`.** Toda sessão de ditado atualiza a
   tabela § 3 Escuta e, havendo erros, a § Itens Fracos.

---

## ⚙️ 2. GERAÇÃO (`"Ditado Aula X"`)

A IA gera `Practice/N5_P{X}_Ditado.md`: uma folha de transcrição em branco.
Ela **não** contém japonês gerado pela IA — apenas a estrutura.

1. **Não perguntar qual é o material externo.** Ele é privado por decisão do
   estudante e o Ditado funciona sobre qualquer áudio. O campo *Referência* da
   folha é de uso livre — pode ficar em branco.
2. Emitir de **8 a 12 slots** de transcrição (frases ou turnos de diálogo).
3. Emitir o bloco de metadados, a ser preenchido pelo estudante se ele quiser.

---

## 📝 3. TEMPLATE CANÔNICO (`Practice/N5_P{X}_Ditado.md`)

```markdown
# 🎧 DITADO: AULA [X]

> **Nível:** JLPT N5
> **Modalidade:** Ditado (書き取り) — transcrição de áudio EXTERNO
> **Referência (opcional, uso livre):** [ex.: "unidade 5" — ou deixe em branco]
> **Transcrição oficial disponível?** [ ] Sim  [ ] Não
> **Tempo estimado:** ~15 min
> **Status:** ⏳ Pendente

## Como usar
1. Ouça o trecho inteiro **uma vez**, sem escrever nada.
2. Ouça de novo, pausando, e transcreva em kana + kanji (o que souber escrever).
3. Ouça uma terceira vez para revisar. **Não** consulte a transcrição antes de terminar.
4. Marque com `?` qualquer trecho que não conseguiu decifrar — isso é dado, não fracasso.

---

## ✍️ TRANSCRIÇÃO

1. > 
2. > 
3. > 
[... até 8-12 slots ...]

---

## 🔎 AUTO-RELATO (preencher antes da correção)

- **Trechos em que travei:** > 
- **Palavras que reconheci de ouvido mas não soube escrever:** > 
- **Velocidade percebida:** [ ] confortável  [ ] no limite  [ ] rápido demais
```

---

## 🔄 4. CORREÇÃO (`"Corrigir Ditado Aula X"`)

### Modo A — com transcrição oficial (preferencial)

O estudante cola a transcrição oficial no chat ou no arquivo.

1. **Diff token a token** entre a transcrição do estudante e a oficial.
2. Classificar **cada** divergência num destes tipos — a taxonomia é o produto
   principal desta modalidade:

   | Tipo | O que significa | Exemplo |
   |---|---|---|
   | `segmentação` | Cortou a cadeia sonora no lugar errado | ouviu 「これは」 como 「こ れば」 |
   | `partícula` | Omitiu ou trocou partícula átona | 「ともだち__」 em vez de 「ともだちが」 |
   | `flexão` | Errou a terminação verbal/adjetival | 「たべます」 → 「たべました」 |
   | `léxico` | Não conhecia a palavra | deixou `?` |
   | `ortografia` | Ouviu certo, escreveu errado | 「じゃ」/「ぢゃ」, vogal longa |
   | `fonológico` | Confusão de contraste sonoro | だ/ら, つ/す, ん final |

3. **Nota:** percentual de tokens corretos, com o detalhamento por tipo.
4. **Diagnóstico de causa raiz**, não lista de erros. Se 4 das 6 falhas forem
   `partícula`, o problema não é vocabulário — é que partículas átonas
   desaparecem na fala conectada, e o treino indicado é outro.

### Modo B — sem transcrição oficial

1. **Declarar explicitamente** que não há gabarito e que **não haverá nota**.
2. Analisar a transcrição como texto: apontar sequências agramaticais, partículas
   ausentes, formas verbais impossíveis — erros detectáveis sem conhecer o áudio.
3. **Proibido afirmar o que o áudio dizia.** Formular como hipótese:
   "「がっこう いきます」 está agramatical — faltou uma partícula; pelo contexto,
   provavelmente 「へ」 ou 「に」. Confira no áudio."
4. Registrar em `Progress.md` como sessão realizada, sem nota.

---

## 📊 5. ATUALIZAÇÃO DE `Progress.md` (OBRIGATÓRIA)

1. Nova linha em § 3 Escuta: semana, referência (se o estudante deu uma), minutos, `Ditado: sim`. **Nunca** perguntar ou inferir qual é o material.
2. Cada tipo de erro recorrente vira linha em § Itens Fracos, com o tipo da
   taxonomia no diagnóstico (ex.: "`partícula` — が/を átonos somem na fala
   conectada; reconhece na leitura, perde na escuta").
3. Marcar a célula `Ditado` da Aula X no Mapa de Progresso.

---

## ⏱️ 6. ESCALONAMENTO

| Fase | Aulas | Slots | Extensão por slot |
|---|---|:---:|---|
| 1-2 | 1-9 | 8 | Frase curta ou saudação (4-8 moras) |
| 3-4 | 10-18 | 10 | Frase completa com adjetivo ou marcador temporal |
| 5-6 | 19-32 | 12 | Turno de diálogo com 2 orações |

> O escalonamento vale para a **folha de transcrição**. A dificuldade real vem
> do áudio externo, que o repositório não controla — se o material estiver
> muito acima ou abaixo do nível, isso aparece no auto-relato de velocidade
> percebida e deve ser sinalizado no chat.
