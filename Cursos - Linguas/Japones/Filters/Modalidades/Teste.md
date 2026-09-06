# ESPECIFICAÇÃO TÉCNICA: MODALIDADE TESTE / QUIZ DE MÚLTIPLA ESCOLHA (`Filters/Modalidades/Teste.md`)

Esta especificação define o padrão determinístico e livre de ambiguidades para a geração e correção de **Testes de Múltipla Escolha** para qualquer aula do currículo de japonês (N5 e níveis superiores).

---

## ⛔ 1. REGRAS INVIOLÁVEIS (HARD RULES)

1. **Princípio do Foco na Matéria Vigente + Revisão Espaçada (Escopo de Avaliação):**
   - **Seções 1 a 5 (80 pts) — matéria vigente.** Avaliam **exclusivamente** a gramática, kanji e vocabulário **novos da Aula X** — a gramática e os kanji listados nos campos `grammar` e `kanji` da Aula X em `JLPTN5.md`, e o vocabulário definido na seção `## Aula X` de `Content/N5_Vocabulary.md`.
   - **Seção 6 (20 pts) — revisão espaçada.** Avalia deliberadamente conteúdo **antigo**, sorteado das Aulas **X-2, X-4 e X-8** (as que existirem), com **prioridade absoluta para os itens listados em `Progress.md` § Itens Fracos**.
   - É **estritamente proibido** introduzir gramática, kanji ou vocabulário de aulas futuras (X+1 em diante).

   > **Por que a Seção 6 existe.** Os `scope` das aulas de consolidação cobrem apenas o bloco imediatamente anterior e **nunca revisitam um bloco mais antigo**: a gramática da Aula 2 é revista na Aula 5 e só reaparece na Aula 32 — 27 semanas depois. Sem esta seção, o Teste não oferece nenhuma recuperação espaçada, e o Anki sozinho não cobria gramática. Espaçamento + interleaving é a alavanca de retenção mais forte disponível; esta seção é onde o sistema a aplica.

2. **Distinção Obrigatória: Conteúdo TESTADO vs. Conteúdo de SCAFFOLDING:**
   - **Conteúdo TESTADO** (o que a questão COBRA do aluno): Apenas itens novos da Aula X. A resposta correta e o principal foco da questão devem pertencer ao ementário da Aula X.
   - **Conteúdo de SCAFFOLDING** (o que aparece nos enunciados e nas opções incorretas/distratores): Pode utilizar livremente vocabulário e gramática cumulativos (Aulas 1 a X), pois é impossível construir frases japonesas naturais apenas com itens novos.

3. **Política de Furigana (Sempre Furigana em Todo Kanji):**
   - **Garantia de Furigana Universal:** TODO e QUALQUER kanji que aparecer nos enunciados, opções de múltipla escolha, gabaritos e exemplos **DEVE carregar `<ruby>` obrigatoriamente**, em todas as ocorrências, sem exceção.
   - **Regra de Aplicação por Palavra Inteira:** A tag `<ruby>` é sempre aplicada sobre a palavra inteira (ex: `<ruby>日本語<rt>にほんご</rt></ruby>`), nunca dividida kanji por kanji.

4. **Zero Romaji:** Todo texto em japonês utiliza exclusivamente Kana + Kanji. O uso de Romaji é expressamente proibido.

5. **Formato Exclusivo de Múltipla Escolha (TESTE = MÚLTIPLA ESCOLHA, NUNCA PROVA ABERTA):**
   - Sob **nenhuma hipótese** o teste deve ser gerado como uma prova escrita aberta ("fill in the blanks", produção livre ou tradução aberta). O formato DEVE ser **exclusivamente um Quiz de Múltipla Escolha** padronizado.
   - Cada questão deve ter obrigatoriamente um enunciado e **4 opções (A, B, C, D)**, listadas com checkboxes Markdown (ex: `- [ ] A)`, `- [ ] B)`).
   - O aluno responderá marcando um "x" na opção correta (ex: `- [x] A)`).

6. **Local de Salvamento:**
   - O caderno de teste é gerado em Markdown no caminho `Practice/N5_P{X}.md`.

7. **PROIBIDO DAR A RESPOSTA NA DICA OU ENUNCIADO (ANTI-SPOILER RULE):**
   - As perguntas, dicas ou placeholders (ex: `___`) NUNCA podem entregar a resposta gramatical ou a intenção da questão mastigada.
   - O aluno deve deduzir a função pelo contexto do enunciado, não lendo a resposta disfarçada de instrução.

---

## ⚙️ 2. TAXONOMIA DE QUESTÕES (AS 6 SEÇÕES DO TESTE)

Todo caderno de teste gerado deve conter as **6 seções** a seguir, totalizando **100 pontos** em **25 questões de 4 pontos cada**. Todas as seções são estritamente de múltipla escolha:

| Seção | Nome da Seção | Foco Pedagógico | Formato | Questões | Pontuação |
|---|---|---|---|:---:|---|
| **Seção 1** | **Vocabulário & Kanji** | Identificação do significado correto ou da leitura em contexto (usando itens **novos da Aula X**). | Escolha a tradução ou uso correto (A, B, C, D). | 4 | **16 pts** |
| **Seção 2** | **Partículas & Conectores** | Aplicação correta das partículas e conectores **ensinados na Aula X**. | Frase com lacuna `___`. Escolha a alternativa (A, B, C, D) que preenche corretamente. | 4 | **16 pts** |
| **Seção 3** | **Gramática & Conjugação** | Aplicação das **estruturas gramaticais e conjugações novas da Aula X**. | Escolha a forma verbal/adjetival ou estrutura gramatical adequada (A, B, C, D). | 4 | **16 pts** |
| **Seção 4** | **Compreensão Situacional** | Identificar a frase ou resposta mais apropriada para um contexto prático, usando a **matéria da Aula X**. | Cenário descrito em PT-BR. Escolha a resposta correta em japonês (A, B, C, D). | 4 | **16 pts** |
| **Seção 5** | **Interpretação (Reading Check)** | Leitura de um pequeno trecho ou diálogo (1 a 3 frases) focado nos **itens da Aula X** para atestar compreensão sintática. | Texto em japonês + Pergunta. Escolha a alternativa correta (A, B, C, D). | 4 | **16 pts** |
| **Seção 6** | **🔁 Revisão Espaçada** | Recuperação de conteúdo **ANTIGO** — Aulas X-2, X-4, X-8. **Prioridade absoluta para os itens de `Progress.md` § Itens Fracos.** | Formato livre entre os das Seções 1-5, escolhido conforme o item revisado (A, B, C, D). | 5 | **20 pts** |

### Regra de composição da Seção 6

1. Ler `Progress.md` § **Itens Fracos**. Cada item com status ⚠️ ativo **DEVE**
   gerar pelo menos uma questão, até o limite de 5.
2. Se sobrarem vagas, completar sorteando das Aulas X-2, X-4 e X-8 (as que
   existirem), preferindo pontos gramaticais que **não** apareceram em nenhuma
   consolidação desde que foram ensinados.
3. Se `Progress.md` não existir ou estiver vazio, usar apenas o critério (2) e
   registrar no chat que a revisão dirigida ainda não tem dados.
4. **Nunca** repetir literalmente a questão que originou o erro — cobre o mesmo
   ponto em contexto novo. Reconhecer a questão de cor não é recuperação.

---

## 🔄 3. ALGORITMO DETERMINÍSTICO DE GERAÇÃO DA IA

Ao receber o comando `"Exercícios Aula X"`, `"Drill Aula X"` ou `"Teste Aula X"`:

1. **Leitura de Escopo (Foco na Aula X):**
   - Abrir `JLPTN5.md` e extrair a definição da Aula X.
   - Identificar os itens **novos** da aula (conteúdo a ser TESTADO nas Seções 1-5).
   - Carregar o acumulado para uso como scaffolding.
   - **Abrir `Progress.md`** e extrair a seção § Itens Fracos — é o insumo obrigatório da Seção 6.

2. **Montagem da Estrutura:**
   - Gerar o arquivo em `Practice/N5_P{X}.md`.
   - Incluir o cabeçalho Markdown com Metadados e Status `⏳ Pendente`.
   - Gerar as questões de múltipla escolha (A, B, C, D) seguindo a Taxonomia.
   - Criar **distratores (opções incorretas) plausíveis** baseados em erros gramaticais comuns (ex: partícula errada, conjugação imperfeita, erro de nível de polidez), utilizando o conteúdo acumulado.
   - Aplicar a Regra do Furigana em todos os kanjis.

3. **Inclusão de Gabarito Oculto:**
   - Incluir ao final a seção `<details><summary><b>👉 Clique aqui para abrir o Gabarito Oficial e Explicações</b></summary>...` contendo as respostas exatas e explicações pedagógicas sintéticas em PT-BR, indicando a lógica da opção certa e o erro dos principais distratores.

4. **Notificação no Chat:**
   - Responder no chat confirmando a criação do arquivo e lembrando o aluno de usar o "x" entre colchetes para marcar a resposta.

---

## 📝 4. FLUXO DE CORREÇÃO INTERATIVA E AVALIAÇÃO (`"Corrigir Aula X"`)

Ao receber o comando `"Corrigir Aula X"` ou `"Avalie o Practice/N5_PX.md"`:

1. **Leitura das Respostas:**
   - A IA abre e lê o arquivo `Practice/N5_P{X}.md`.
   - Analisa quais checkboxes foram marcadas com `x` ou `X` pelo aluno (ex: `- [x] A)` ou `- [X] A)`).

2. **Cálculo da Nota & Correção:**
   - Compara as alternativas assinaladas com a chave de correção oficial.
   - Calcula a nota (de 0 a 100).

3. **Atualização do Arquivo Local:**
   - A IA edita o cabeçalho do arquivo `Practice/N5_P{X}.md` atualizando o campo `> **Status:**` para `✅ Concluído (Nota: YY/100)`.

4. **Atualização de `Progress.md` (OBRIGATÓRIA):**
   - Marcar a célula `Teste` da Aula X no Mapa de Progresso com a nota.
   - Para **cada erro**, criar ou incrementar uma linha em § Itens Fracos, com **diagnóstico de causa raiz** — nunca apenas "errou a partícula".
   - Para cada item da Seção 6 **acertado**, incrementar o contador de acertos; após 2 acertos consecutivos em modalidades diferentes, mover para *Itens dominados*.
   - Seguir integralmente o § 4 Protocolo de Atualização de `Progress.md`.

5. **Feedback Detalhado no Chat:**
   - Fornece a Nota Final, com o recorte **Seções 1-5 (matéria nova) vs. Seção 6 (retenção)** separado — são diagnósticos diferentes: errar a Seção 6 indica esquecimento, não incompreensão.
   - Para as questões erradas, explica de forma cirúrgica por que o distrator escolhido estava incorreto e revisa a regra correspondente à opção certa.
   - Oferece um diagnóstico de quais pontos precisam de mais revisão e qual tag do Anki atacar (ver `Anki/README_ANKI.md` § 5).

---

## 🏗️ 5. TEMPLATE CANÔNICO DE SAÍDA (`Practice/N5_P{X}.md`)

```markdown
# 🧪 TESTE DE FIXAÇÃO (MÚLTIPLA ESCOLHA): AULA [X] — [TÍTULO DA AULA]

> **Nível:** JLPT N5
> **Escopo — Seções 1-5 (80 pts):** Aula [X] (conteúdo novo: [N] gramática, [N] kanji, [N] vocabulário)
> **Escopo — Seção 6 (20 pts):** Revisão espaçada das Aulas [X-2], [X-4], [X-8] + itens de `Progress.md` § Itens Fracos
> **Estrutura:** 25 questões × 4 pts = 100 pts
> **Instruções:** Este é um teste de múltipla escolha. Marque a alternativa correta colocando um 'x' entre os colchetes, assim: `- [x] A)`.
> **Status:** ⏳ Pendente

---

## 📝 SEÇÃO 1: VOCABULÁRIO & KANJI (16 PONTOS)

1. Qual é o significado correto da palavra <ruby>[Palavra em Kanji nova da Aula X]<rt>[Kana]</rt></ruby>?
- [ ] A) [Distrator 1]
- [ ] B) [Resposta Correta]
- [ ] C) [Distrator 2]
- [ ] D) [Distrator 3]

2. Como se diz "[Palavra em PT-BR da Aula X]" em japonês?
- [ ] A) [Distrator 1]
- [ ] B) [Distrator 2]
- [ ] C) [Resposta Correta]
- [ ] D) [Distrator 3]

---

## 📝 SEÇÃO 2: PARTÍCULAS & CONECTORES (16 PONTOS)

1. Qual partícula preenche corretamente a lacuna abaixo?
[Frase com scaffolding] ___ [Continuação da frase].
- [ ] A) [Partícula Incorreta]
- [ ] B) [Partícula Correta da Aula X]
- [ ] C) [Partícula Incorreta]
- [ ] D) [Partícula Incorreta]

---

## 📝 SEÇÃO 3: GRAMÁTICA & CONJUGAÇÃO (16 PONTOS)

1. Selecione a forma correta para completar a frase usando a gramática da Aula X:
[Frase contextualizando a estrutura].
- [ ] A) [Forma Incorreta]
- [ ] B) [Forma Incorreta]
- [ ] C) [Forma Incorreta]
- [ ] D) [Forma Correta da Aula X]

---

## 📝 SEÇÃO 4: COMPREENSÃO SITUACIONAL (16 PONTOS)

1. **Cenário:** [Breve situação descrita em PT-BR]. O que você diria ou qual frase melhor descreve isso, aplicando a matéria nova?
- [ ] A) [Opção em Japonês Incorreta]
- [ ] B) [Opção em Japonês Correta]
- [ ] C) [Opção em Japonês Incorreta]
- [ ] D) [Opção em Japonês Incorreta]

---

## 📝 SEÇÃO 5: INTERPRETAÇÃO (16 PONTOS)

1. Leia o trecho abaixo e responda à pergunta:
[Pequeno texto ou diálogo em japonês contendo os novos itens gramaticais/vocabulário da Aula X]
**Pergunta:** [Pergunta de compreensão em PT-BR baseada na mecânica nova]?
- [ ] A) [Alternativa Incorreta]
- [ ] B) [Alternativa Incorreta]
- [ ] C) [Alternativa Correta]
- [ ] D) [Alternativa Incorreta]

---

## 🔁 SEÇÃO 6: REVISÃO ESPAÇADA (20 PONTOS)

> Esta seção **não** cobra a Aula [X]. Ela cobra o que você aprendeu semanas
> atrás e pode ter esquecido. Errar aqui é sinal de retenção, não de
> compreensão — e é exatamente essa a informação que o sistema precisa.

[GERAR 5 QUESTÕES. Cada uma deve declarar sua origem entre colchetes.]

1. **[Aula N — {ponto revisado}]** [Enunciado no formato mais adequado ao item]
- [ ] A) [Distrator]
- [ ] B) [Resposta Correta]
- [ ] C) [Distrator]
- [ ] D) [Distrator]

[NOTAS PARA A IA GERADORA:]
- Todo item com status ⚠️ ativo em `Progress.md` § Itens Fracos DEVE aparecer aqui (até 5).
- Vagas restantes: sortear das Aulas X-2, X-4, X-8, preferindo pontos que não
  apareceram em nenhuma consolidação desde que foram ensinados.
- **Nunca** reutilizar literalmente a questão que originou o erro — mesmo ponto,
  contexto novo.

---

## 🔍 GABARITO & EXPLICAÇÕES

<details>
<summary><b>👉 Clique aqui para abrir o Gabarito Oficial e Explicações</b></summary>

### Gabarito Detalhado:

#### Seção 1: Vocabulário & Kanji
1. **Resposta:** B) [Resposta Correta]. *Explicação: ...*
2. **Resposta:** C) [Resposta Correta]. *Explicação: ...*

#### Seção 2: Partículas & Conectores
1. **Resposta:** B) [Partícula Correta]. *Explicação: ...*

#### Seção 3: Gramática & Conjugação
1. **Resposta:** D) [Forma Correta]. *Explicação: ...*

#### Seção 4: Compreensão Situacional
1. **Resposta:** B) [Opção Correta]. *Explicação: ...*

#### Seção 5: Interpretação
1. **Resposta:** C) [Alternativa Correta]. *Explicação: ...*

#### Seção 6: Revisão Espaçada
1. **Resposta:** [Correta] — *revisão da Aula N.* *Explicação: [regra relembrada + por que o distrator é tentador para quem esqueceu].*

</details>
```
