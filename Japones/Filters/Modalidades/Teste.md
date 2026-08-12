# ESPECIFICAÇÃO TÉCNICA: MODALIDADE TESTE / QUIZ DE MÚLTIPLA ESCOLHA (`Filters/Modalidades/Teste.md`)

Esta especificação define o padrão determinístico e livre de ambiguidades para a geração e correção de **Testes de Múltipla Escolha** para qualquer aula do currículo de japonês (N5 e níveis superiores).

---

## ⛔ 1. REGRAS INVIOLÁVEIS (HARD RULES)

1. **Princípio do Foco na Matéria Vigente (Escopo de Avaliação):**
   - O teste avalia **exclusivamente** a gramática, kanji e vocabulário **novos da Aula X** — a gramática e os kanji listados nos campos `grammar` e `kanji` da Aula X em `JLPTN5.md`, e o vocabulário definido na seção `## Aula X` de `Content/N5_Vocabulary.md`.
   - É **estritamente proibido** cobrar, avaliar ou pontuar conhecimento de gramática, kanji ou vocabulário ensinados em aulas anteriores (1 a X-1). A revisão cumulativa é responsabilidade de outros mecanismos do sistema.
   - É **estritamente proibido** introduzir gramática, kanji ou vocabulário de aulas futuras (X+1 em diante).

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
   - O caderno de teste é gerado em Markdown no caminho `/Users/bmanica/Documents/GitHub/Bruno/Japones/Practice/N5_P{X}.md`.

7. **PROIBIDO DAR A RESPOSTA NA DICA OU ENUNCIADO (ANTI-SPOILER RULE):**
   - As perguntas, dicas ou placeholders (ex: `___`) NUNCA podem entregar a resposta gramatical ou a intenção da questão mastigada.
   - O aluno deve deduzir a função pelo contexto do enunciado, não lendo a resposta disfarçada de instrução.

---

## ⚙️ 2. TAXONOMIA DE QUESTÕES (AS 5 SEÇÕES DO TESTE)

Todo caderno de teste gerado deve conter as 5 seções a seguir, totalizando **100 pontos**. Todas as seções são estritamente de múltipla escolha e focam exclusivamente no conteúdo novo da Aula X:

| Seção | Nome da Seção | Foco Pedagógico | Formato | Pontuação |
|---|---|---|---|---|
| **Seção 1** | **Vocabulário & Kanji** | Identificação do significado correto ou da leitura em contexto (usando itens **novos da Aula X**). | Escolha a tradução ou uso correto (A, B, C, D). | **20 pts** |
| **Seção 2** | **Partículas & Conectores** | Aplicação correta das partículas e conectores **ensinados na Aula X**. | Frase com lacuna `___`. Escolha a alternativa (A, B, C, D) que preenche corretamente. | **20 pts** |
| **Seção 3** | **Gramática & Conjugação** | Aplicação das **estruturas gramaticais e conjugações novas da Aula X**. | Escolha a forma verbal/adjetival ou estrutura gramatical adequada (A, B, C, D). | **20 pts** |
| **Seção 4** | **Compreensão Situacional** | Identificar a frase ou resposta mais apropriada para um contexto prático, usando a **matéria da Aula X**. | Cenário descrito em PT-BR. Escolha a resposta correta em japonês (A, B, C, D). | **20 pts** |
| **Seção 5** | **Interpretação (Reading Check)** | Leitura de um pequeno trecho ou diálogo (1 a 3 frases) focado nos **itens da Aula X** para atestar compreensão sintática. | Texto em japonês + Pergunta. Escolha a alternativa correta (A, B, C, D). | **20 pts** |

---

## 🔄 3. ALGORITMO DETERMINÍSTICO DE GERAÇÃO DA IA

Ao receber o comando `"Exercícios Aula X"`, `"Drill Aula X"` ou `"Teste Aula X"`:

1. **Leitura de Escopo (Foco na Aula X):**
   - Abrir `JLPTN5.md` e extrair a definição da Aula X.
   - Identificar os itens **novos** da aula (conteúdo a ser TESTADO).
   - Carregar o acumulado para uso como scaffolding.

2. **Montagem da Estrutura:**
   - Gerar o arquivo em `/Users/bmanica/Documents/GitHub/Bruno/Japones/Practice/N5_P{X}.md`.
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
   - A IA abre e lê o arquivo `/Users/bmanica/Documents/GitHub/Bruno/Japones/Practice/N5_P{X}.md`.
   - Analisa quais checkboxes foram marcadas com `x` ou `X` pelo aluno (ex: `- [x] A)` ou `- [X] A)`).

2. **Cálculo da Nota & Correção:**
   - Compara as alternativas assinaladas com a chave de correção oficial.
   - Calcula a nota (de 0 a 100).

3. **Atualização do Arquivo Local:**
   - A IA edita o cabeçalho do arquivo `Practice/N5_P{X}.md` atualizando o campo `> **Status:**` para `✅ Concluído (Nota: YY/100)`.

4. **Feedback Detalhado no Chat:**
   - Fornece a Nota Final.
   - Para as questões erradas, explica de forma cirúrgica por que o distrator escolhido estava incorreto e revisa a regra da Aula X correspondente à opção certa.
   - Oferece um diagnóstico de quais pontos da Aula X precisam de mais revisão.

---

## 🏗️ 5. TEMPLATE CANÔNICO DE SAÍDA (`Practice/N5_P{X}.md`)

```markdown
# 🧪 TESTE DE FIXAÇÃO (MÚLTIPLA ESCOLHA): AULA [X] — [TÍTULO DA AULA]

> **Nível:** JLPT N5
> **Escopo Avaliado:** Aula [X] (conteúdo novo: [N] gramática, [N] kanji, [N] vocabulário)
> **Instruções:** Este é um teste de múltipla escolha. Marque a alternativa correta colocando um 'x' entre os colchetes, assim: `- [x] A)`.
> **Status:** ⏳ Pendente

---

## 📝 SEÇÃO 1: VOCABULÁRIO & KANJI (20 PONTOS)

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

## 📝 SEÇÃO 2: PARTÍCULAS & CONECTORES (20 PONTOS)

1. Qual partícula preenche corretamente a lacuna abaixo?
[Frase com scaffolding] ___ [Continuação da frase].
- [ ] A) [Partícula Incorreta]
- [ ] B) [Partícula Correta da Aula X]
- [ ] C) [Partícula Incorreta]
- [ ] D) [Partícula Incorreta]

---

## 📝 SEÇÃO 3: GRAMÁTICA & CONJUGAÇÃO (20 PONTOS)

1. Selecione a forma correta para completar a frase usando a gramática da Aula X:
[Frase contextualizando a estrutura].
- [ ] A) [Forma Incorreta]
- [ ] B) [Forma Incorreta]
- [ ] C) [Forma Incorreta]
- [ ] D) [Forma Correta da Aula X]

---

## 📝 SEÇÃO 4: COMPREENSÃO SITUACIONAL (20 PONTOS)

1. **Cenário:** [Breve situação descrita em PT-BR]. O que você diria ou qual frase melhor descreve isso, aplicando a matéria nova?
- [ ] A) [Opção em Japonês Incorreta]
- [ ] B) [Opção em Japonês Correta]
- [ ] C) [Opção em Japonês Incorreta]
- [ ] D) [Opção em Japonês Incorreta]

---

## 📝 SEÇÃO 5: INTERPRETAÇÃO (20 PONTOS)

1. Leia o trecho abaixo e responda à pergunta:
[Pequeno texto ou diálogo em japonês contendo os novos itens gramaticais/vocabulário da Aula X]
**Pergunta:** [Pergunta de compreensão em PT-BR baseada na mecânica nova]?
- [ ] A) [Alternativa Incorreta]
- [ ] B) [Alternativa Incorreta]
- [ ] C) [Alternativa Correta]
- [ ] D) [Alternativa Incorreta]

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

</details>
```
