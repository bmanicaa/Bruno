# 📊 Progress.md — Estado do Curso e Memória de Erros

> **Este arquivo é ESTADO, não documentação.** É a única memória persistente do
> sistema. Antes de gerar qualquer artefato novo, a IA **DEVE** lê-lo; depois de
> qualquer correção, **DEVE** atualizá-lo. Sem ele o sistema é um gerador de
> material que esquece tudo; com ele, consegue re-testar o que você errou.

**Última atualização:** 2026-09-06 (reatribuição ótima dos 80 kanji + 円 acrescentado ao vocabulário)
**Aula atual:** 4 (próxima a ser gerada)
**Ritmo:** 1 aula/semana (pode esticar para 2 em plantão pesado)

---

## 1. Mapa de Progresso

Legenda: ✅ concluído · 🟡 gerado, não feito · ⬜ não gerado · `—` não se aplica

| Aula | Tipo | Título | Aula HTML | Anki | Reading | Teste | Lacunas | Ditado |
|:---:|:---:|---|:---:|:---:|:---:|:---:|:---:|:---:|
| 1 | 📘 | Eu Sou — Copula & Perguntas | ✅ | ✅ 25 | ⬜ | ⬜ | ⬜ | ⬜ |
| 2 | 📘 | Não Sou — Negação & Posse | ✅ | ✅ 27 | ✅ | ⬜ | ⬜ | ⬜ |
| 3 | 📘 | Minha Família & Números | ✅ | ✅ 30 | ✅ | ⬜ | ✅ **90/100** | ⬜ |
| 4 | 📘 | Meu Mundo — Conexões, Contexto & Intensidade | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ |
| 5 | 🔄 | Consolidação — Aulas 1-4 | ⬜ | — | ⬜ | ⬜ | ⬜ | ⬜ |

*(as Aulas 6-32 seguem não iniciadas; acrescente a linha quando gerar)*

**Cards de gramática no Anki:** Aulas 1-3 → 19 cards (`Anki/N5_G{1,2,3}_Gramatica.tsv`)
**Cards de vocabulário:** 82, todos com leitura (TTS) e frase de exemplo
**Gabarito do Lacunas 3:** ✅ presente (adicionado retroativamente; a spec o exigia e ele faltava)

---

## 2. Itens Fracos (o que a revisão espaçada deve priorizar)

Esta é a seção que a **Seção 6 do Teste** (Revisão Espaçada) consome. Cada item
carrega a aula de origem, o diagnóstico de causa raiz e quantas vezes reapareceu.

| Item | Aula | Diagnóstico de causa raiz | Erros | Status |
|---|:---:|---|:---:|:---:|
| `が` adversativo **sem dica** | 3 | **A regra está aprendida, o gatilho não.** Na Seção 3 Q3, com a dica "conector adversativo", acertou; na Seção 1 Q4, com a dica neutra "(partícula)", respondeu "Não sei". Ou seja: reconhece o `が` de "mas" quando alguém nomeia a função, mas não o deduz **pela posição** (depois de です/ます → conjunção; depois de substantivo → sujeito). O treino indicado não é reexplicar a regra — é exposição a itens **sem** dica de função. | 1 | ⚠️ ativo |
| `は` contrastivo | 3 | Usou `が` onde o contraste entre dois membros da família pedia `は` (「兄は医者です。弟は学生です」). `が` aponta *quem* (informação nova); `は` **contrapõe** dois tópicos já em pauta. Em frases paralelas comparando membros de um mesmo grupo, `は` nos dois lados. | 1 | ⚠️ ativo |

> **Padrão detectado:** os dois erros têm a mesma raiz — a fronteira `は`/`が`.
> Não é vocabulário nem conjugação: as Seções 2 e 3 saíram 25/25. Priorize
> `tag:gramatica::ga-mas` e `tag:gramatica::wa-topico` no Anki, e garanta
> cobertura na Aula 5 (Consolidação), cujo escopo já inclui a Aula 3.
>
> **Instrução específica para a Seção 6 do Teste:** ao re-testar o `が`
> adversativo, use dica **neutra** ("partícula"), nunca "conector adversativo" —
> a dica nomeada já foi acertada e não mede nada.

### Itens dominados (saíram da rotação de revisão dirigida)

*(vazio — nada foi promovido ainda; um item sai daqui após 2 acertos consecutivos
em modalidades diferentes)*

---

## 3. Escuta (material EXTERNO)

A escuta **não é gerada por este repositório** — decisão deliberada. TTS produz
fala limpa, um locutor e ritmo uniforme; o 聴解 do N5 cobra diálogo multi-locutor
em velocidade natural, com reduções. Um módulo sintético pareceria treino de
escuta e treinaria a coisa errada.

O que o repositório faz é **registrar e corrigir**, não gerar.

**O material externo é privado e deliberadamente não identificado aqui.** O
sistema não precisa saber qual é: o Ditado funciona sobre qualquer áudio, e o
registro abaixo é opcional e auto-preenchido por você, se e quando quiser.

| Semana | Referência (livre) | Minutos | Ditado feito? |
|:---:|---|:---:|:---:|
| — | — | — | — |

> **Regras para a IA nesta seção:**
> - **Nunca perguntar** qual é o material externo, nem pedir que seja nomeado.
>   A coluna *Referência* é de uso livre do estudante (ex.: "unidade 5", "faixa 12",
>   ou em branco) e serve só para ele se localizar.
> - Preencher uma linha **apenas** quando o estudante relatar uma sessão de escuta
>   ou pedir uma correção de Ditado. Não inferir, não estimar, não completar.
> - **Não emitir alertas** de ausência de escuta. O estudante decidiu gerir essa
>   frente por fora, e essa decisão é definitiva — cobrar seria ruído.
>
> Para contexto, não para cobrança: o 聴解 vale 60 dos 180 pontos do N5 e tem
> mínimo seccional próprio. É a razão de a escuta importar; a gestão dela é sua.

---

## 4. Protocolo de Atualização (para a IA)

**Leitura obrigatória** antes de gerar: Teste, Lacunas, Consolidação e Ditado.

**Escrita obrigatória** após cada correção:

1. Atualizar a célula correspondente no **Mapa de Progresso** com a nota.
2. Para cada erro, criar ou incrementar uma linha em **Itens Fracos**, sempre
   com **diagnóstico de causa raiz** — nunca apenas "errou a partícula".
   Se o item já existe, incrementar `Erros` e manter o diagnóstico mais preciso.
3. Após **2 acertos consecutivos em modalidades diferentes**, mover o item para
   *Itens dominados*.
4. Se surgirem 3+ erros com a mesma raiz, registrar um **Padrão detectado** em
   negrito abaixo da tabela e apontar a tag do Anki correspondente.
5. Atualizar `Última atualização` e `Aula atual`.

**Regra de honestidade:** nunca registre aqui uma nota ou uma sessão que não
tenha acontecido de fato. Este arquivo só vale se refletir a realidade — um
progresso inflado corrompe a revisão dirigida, que é justamente o que ele existe
para alimentar.
