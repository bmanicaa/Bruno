# ESPECIFICAÇÃO TÉCNICA: MODALIDADE TESTE / DRILL INTERATIVO (`Filters/Modalidades/Teste.md`)

Esta especificação define o padrão determinístico e livre de ambiguidades para a geração e correção de **Exercícios de Avaliação Interativa & Drills Sintáticos (Teste)** para qualquer aula do currículo de japonês (N5 e níveis superiores).

---

## ⛔ 1. REGRAS INVIOLÁVEIS (HARD RULES)

1. **Princípio do Foco na Matéria Vigente (Escopo de Avaliação):**
   - O teste avalia **exclusivamente** a gramática, kanji e vocabulário **novos da Aula X** — os itens listados nos campos `grammar`, `kanji`, `focus_vocab` e `anki_vocab` da Aula X em `JLPTN5.md`.
   - É **estritamente proibido** cobrar, avaliar ou pontuar conhecimento de gramática, kanji ou vocabulário ensinados em aulas anteriores (1 a X-1). A revisão cumulativa é responsabilidade de outros mecanismos do sistema (Anki, Consolidação, Reading e Review da Aula).
   - É **estritamente proibido** introduzir gramática, kanji ou vocabulário de aulas futuras (X+1 em diante).

2. **Distinção Obrigatória: Conteúdo TESTADO vs. Conteúdo de SCAFFOLDING:**
   - **Conteúdo TESTADO** (o que a questão COBRA do aluno): Apenas itens novos da Aula X. Todo item avaliado e pontuado deve pertencer ao ementário da Aula X.
   - **Conteúdo de SCAFFOLDING** (o que aparece nos enunciados e frases-contexto): Pode utilizar livremente vocabulário e gramática cumulativos (Aulas 1 a X), pois é impossível construir frases japonesas coerentes usando apenas os itens novos da aula. O scaffolding existe para dar contexto natural às questões, **nunca** para ser avaliado.
   - **Justificativa pedagógica:** O *testing effect* (Roediger & Karpicke, 2006) demonstra que o ganho máximo de consolidação de memória ocorre ao forçar o resgate de material recém-codificado. Diluir o teste com matéria antiga enfraquece esse efeito e gera ruído diagnóstico. A revisão espaçada já é coberta pelo Anki diário, pelas 8 aulas de Consolidação, pelo Reading narrativo e pela seção de Review (5 min) no início de cada aula de conteúdo.

3. **Política de Furigana (Sempre Furigana em Todo Kanji):**
   - **Garantia de Furigana Universal:** TODO e QUALQUER kanji que aparecer nos enunciados, opções, frases-contexto, gabaritos e exemplos do teste **DEVE carregar `<ruby>` obrigatoriamente**, em todas as ocorrências, sem exceção.
   - **Foco Pedagógico:** O teste avalia o domínio sintático, conjugação, uso de partículas, gramática e vocabulário. A leitura memorizada de kanji isolado **NUNCA** deve servir como barreira para a resolução das questões.
   - **Regra de Aplicação por Palavra Inteira:** A tag `<ruby>` é sempre aplicada sobre a palavra inteira (ex: `<ruby>日本語<rt>にほんご</rt></ruby>`), nunca dividida kanji por kanji.

4. **Zero Romaji:** Todo texto em japonês utiliza exclusivamente Kana + Kanji. O uso de Romaji é expressamente proibido em qualquer seção do teste ou gabarito.

5. **Campos de Resposta Digitáveis (`> `):**
   - Todas as questões que exigem escrita do aluno contêm obrigatoriamente uma linha em branco antecedida pelo caractere de citação `> ` para digitação limpa em qualquer editor Markdown.

6. **Local de Salvamento:**
   - O caderno de teste é gerado em Markdown no caminho `/Users/bmanica/Documents/GitHub/Bruno/Japones/Practice/N5_P{X}.md`.

---

## ⚙️ 2. TAXONOMIA DE QUESTÕES (AS 6 SEÇÕES FIXAS DO TESTE)

Todo caderno de teste gerado deve conter exatamente as 6 seções a seguir, totalizando **100 pontos**. **Todas as seções avaliam exclusivamente o conteúdo novo da Aula X:**

| Seção | Nome da Seção | Foco Pedagógico | Formato | Pontuação |
|---|---|---|---|---|
| **Seção 1** | **Vocabulário & Kanji** (語彙・漢字) | Tradução PT-BR, significado e uso dos Kanji e Vocabulário Foco/Anki **novos da Aula X** (com furigana em todos os kanji). | Correspondência, identificação de significado e tradução contextual. | **20 pts** |
| **Seção 2** | **Partículas & Conectores** (助詞・接続詞) | Aplicação correta das partículas e conectores **ensinados na Aula X** em contextos situacionais. Frases-contexto podem usar vocabulário cumulativo (scaffolding). | Lacunas `[ ___ ]` com justificativa gramatical em PT-BR. | **20 pts** |
| **Seção 3** | **Transformação Gramatical** (文法変換) | Aplicação das **estruturas gramaticais novas da Aula X** através de transformações de frases: conjugação verbal/adjetival quando aplicável, mas também transformação afirmativa→negativa, declaração→pergunta, troca de partícula com mudança semântica, reestruturação com conectores, ou qualquer modificação estrutural que os pontos gramaticais da aula exijam. | Reescrita de frases, preenchimento de formas e transformação estrutural. | **20 pts** |
| **Seção 4** | **Reorganização Sintática** (並べ替え) | Ordenação correta de blocos de palavras para formar frases que demonstrem domínio das **estruturas gramaticais da Aula X**. | Blocos embaralhados `[ ① / ② / ③ / ④ ]` com indicador da posição marcada. | **10 pts** |
| **Seção 5** | **Tradução Situacional** (表現・翻訳) | Tradução bidirecional (PT-BR ↔ JP) que exija o uso ativo da **gramática e vocabulário novos da Aula X** em cenários práticos contextualizados. | Frases completas contextualizadas. | **15 pts** |
| **Seção 6** | **Aplicação Integrada** (実践・総合) | Produção livre e contextualizada: o aluno deve **sintetizar** os pontos gramaticais e vocabulário **novos da Aula X** em uma situação comunicativa prática (mini-diálogo, descrição de cenário ou resposta situacional). Testa a capacidade de **usar ativamente** o conteúdo novo, não apenas reconhecê-lo. | Produção guiada com cenário situacional em PT-BR e resposta em japonês. | **15 pts** |

---

## ⏱️ 3. ESCALONAMENTO E COMPLEXIDADE POR FASE

O volume de questões e profundidade sintática escalam conforme a fase do currículo descrita em `JLPTN5.md`:

| Fase | Aulas | Itens por Seção (Seções 1-5) | Extensão Média da Frase | Seção 6: Tipo de Produção |
|---|---|---|---|---|
| **Fase 1: Fundações** | 1 a 4 | 3 a 4 itens | 3 a 5 palavras | Completar 2-3 turnos de um micro-diálogo de apresentação usando os itens novos. |
| **Fase 2: Espaço** | 6 a 8 | 4 a 5 itens | 4 a 6 palavras | Descrever a localização de 2-3 objetos/pessoas usando as estruturas novas. |
| **Fase 3: Descrição** | 10 a 12 | 4 a 5 itens | 5 a 8 palavras | Redigir 3-4 frases descrevendo algo ou alguém usando os adjetivos e advérbios novos. |
| **Fase 4: Tempo & Desejos** | 14 a 17 | 5 a 6 itens | 6 a 9 palavras | Escrever um parágrafo curto (3-4 frases) sobre rotina ou desejos usando o vocabulário e gramática novos. |
| **Fase 5: Ações** | 19 a 25 | 5 a 6 itens | 7 a 11 palavras | Construir um mini-diálogo (4-5 turnos) aplicando as conjugações e estruturas verbais novas em contexto. |
| **Fase 6: Comunicação** | 27 a 31 | 6 itens | 8 a 12 palavras | Redigir uma resposta elaborada (4-6 frases) a uma situação social complexa usando as estruturas comunicativas novas. |

---

## 🔄 4. ALGORITMO DETERMINÍSTICO DE GERAÇÃO DA IA

Ao receber o comando `"Exercícios Aula X"` ou `"Drill Aula X"` ou `"Teste Aula X"`:

1. **Leitura de Escopo (Foco na Aula X):**
   - Abrir `JLPTN5.md` e extrair a definição da Aula X: `grammar`, `kanji`, `focus_vocab` e `anki_vocab`.
   - Ler as linhas correspondentes em `Content/N5_Grammar.md`, `Content/N5_Kanji.md` e `Content/N5_Vocabulary.md`.
   - Identificar os itens **novos** da aula (conteúdo a ser TESTADO).
   - Carregar o acumulado (`Cum.G`, `Cum.K`, `Cum.V`) apenas para uso como scaffolding nos enunciados.

2. **Montagem da Estrutura:**
   - Gerar o arquivo `/Users/bmanica/Documents/GitHub/Bruno/Japones/Practice/N5_P{X}.md`.
   - Incluir o cabeçalho Markdown com Metadados e Status `⏳ Pendente`.
   - Compor as 6 Seções seguindo a Taxonomia, garantindo que **todo item avaliado pertença à Aula X**.
   - Aplicar a Regra do Furigana Oculto nos alvos testados.

3. **Inclusão de Gabarito Oculto:**
   - Incluir ao final do arquivo a seção `<details><summary><b>👉 Clique aqui para abrir o Gabarito Oficial e Explicações</b></summary>...` contendo as respostas exatas e explicações pedagógicas sintéticas em PT-BR para cada item.

4. **Notificação no Chat:**
   - Responder no chat confirmando a criação do arquivo em `Practice/N5_P{X}.md` com o resumo do teste e orientações de preenchimento.

---

## 📝 5. FLUXO DE CORREÇÃO INTERATIVA E AVALIAÇÃO (`"Corrigir Aula X"`)

Ao receber o comando `"Corrigir Aula X"` ou `"Avalie o Practice/N5_PX.md"`:

1. **Leitura das Respostas:**
   - A IA abre e lê o arquivo `/Users/bmanica/Documents/GitHub/Bruno/Japones/Practice/N5_P{X}.md`.
   - Extrai todo o texto digitado pelo estudante após as linhas de resposta `> `.

2. **Cálculo da Nota & Correção:**
   - Avalia cada item de acordo com a chave de correção oficial.
   - Calcula a nota de 0 a 100 com base no peso das seções.
   - Tolera pequenas variações de kana/espaçamento, mas exige precisão sintática e de partículas.

3. **Atualização do Arquivo Local:**
   - A IA edita o cabeçalho do arquivo `Practice/N5_P{X}.md` atualizando o campo `> **Status:**` para `✅ Concluído (Nota: YY/100)`.

4. **Feedback Detalhado no Chat:**
   - A IA envia uma resposta no chat estruturada da seguinte forma:
     - **Nota Final:** YY/100 (com diagnóstico por seção).
     - **Pontos Fortes:** Conceitos da Aula X dominados com clareza.
     - **Análise de Erros (se houver):** Explicação detalhada de cada erro cometido, apontando o motivo gramatical e a regra da Aula X envolvida.
     - **Recomendação de Estudo:** Sugestão de revisão direcionada para os pontos fracos identificados dentro do conteúdo da Aula X.

---

## 🏗️ 6. TEMPLATE CANÔNICO DE SAÍDA (`Practice/N5_P{X}.md`)

```markdown
# 🧪 TESTE DE FIXAÇÃO: AULA [X] — [TÍTULO DA AULA]

> **Nível:** JLPT N5
> **Escopo Avaliado:** Aula [X] (conteúdo novo: [N] gramática, [N] kanji, [N] vocabulário foco, [N] vocabulário Anki)
> **Scaffolding:** Vocabulário e gramática cumulativos das Aulas 1 a [X] podem aparecer nos enunciados, mas NÃO são avaliados.
> **Tempo Estimado:** ~15 a 20 minutos
> **Status:** ⏳ Pendente

---

## 📝 SEÇÃO 1: VOCABULÁRIO & KANJI (20 PONTOS)

Responda às questões de leitura e significado dos termos **novos desta aula**:

1. Escreva o significado em PT-BR e forneça um exemplo de uso para o termo: <ruby>[Kanji Nível 1 novo da Aula X]<rt>[Leitura]</rt></ruby>
   > 

2. Traduza o seguinte vocabulário foco **da Aula X** para o japonês (Kana ou Kanji): [Palavra em PT-BR]
   > 

---

## 📝 SEÇÃO 2: PARTÍCULAS & CONECTORES (20 PONTOS)

Preencha as lacunas com a partícula/conector **ensinado na Aula X** e indique a função gramatical em português:

1. [Frase em Japonês usando scaffolding cumulativo com lacuna [ ___ ] no ponto gramatical novo]
   > Partícula: 
   > Função: 

---

## 📝 SEÇÃO 3: TRANSFORMAÇÃO GRAMATICAL (20 PONTOS)

Aplique as estruturas gramaticais **da Aula X** transformando as frases conforme solicitado:

1. [Instrução de transformação gramatical conforme o conteúdo da Aula X — ex: "Transforme em pergunta usando か", "Reescreva na forma negativa usando じゃない", "Conjugue para a forma て", etc.]:
   > 

---

## 📝 SEÇÃO 4: REORGANIZAÇÃO SINTÁTICA (10 PONTOS)

Reordene os blocos numerados para formar uma frase correta que demonstre o uso da **gramática da Aula X**:

1. [ ① / ② / ③ / ④ ]
   > Frase completa: 

---

## 📝 SEÇÃO 5: TRADUÇÃO SITUACIONAL (15 PONTOS)

Traduza as frases usando a **gramática e vocabulário novos da Aula X**, mantendo o registro e polidez adequados:

1. [Frase em Português que exija o uso de estrutura gramatical/vocabulário da Aula X]
   > 

---

## 📝 SEÇÃO 6: APLICAÇÃO INTEGRADA (15 PONTOS)

Use os pontos gramaticais e vocabulário **novos da Aula X** para responder à situação abaixo. Escreva em japonês:

**Cenário:** [Descrição de uma situação comunicativa prática em PT-BR que exija a síntese dos itens novos da Aula X]

> 

---

## 🔍 GABARITO & EXPLICAÇÕES

<details>
<summary><b>👉 Clique aqui para abrir o Gabarito Oficial e Explicações</b></summary>

### Gabarito Detalhado:

#### Seção 1: Vocabulário & Kanji
1. **Resposta:** [Kana] — [Significado PT-BR]. *Explicação: ...*

#### Seção 2: Partículas & Conectores
1. **Resposta:** [Partícula] — *Explicação: ...*

#### Seção 3: Transformação Gramatical
1. **Resposta:** [Frase Transformada] — *Explicação: ...*

#### Seção 4: Reorganização Sintática
1. **Resposta:** [Frase Correta] — *Explicação: ...*

#### Seção 5: Tradução Situacional
1. **Resposta:** [Frase em Japonês] — *Explicação: ...*

#### Seção 6: Aplicação Integrada
1. **Resposta Modelo:** [Produção esperada em Japonês] — *Explicação e variações aceitas: ...*

</details>
```
