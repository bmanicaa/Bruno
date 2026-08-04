# ESPECIFICAÇÃO TÉCNICA E PADRÃO DE EXERCÍCIOS INTERATIVOS (`Filters/Exercises.md`)

---

## 🎯 1. OBJETIVO E VISÃO GERAL DO DOCUMENTO

Este documento é a **Especificação Oficial de Engenharia Pedagógica e Padrão de Exercícios Interativos em Markdown** para o programa de autoestudo JLPT N5.

Ele estabelece as regras para que a Inteligência Artificial geradora produza cadernos de treino interativos na pasta `Practice/N5_PX.md` (onde `X` é o número da aula). 

### Principais Recursos & Filosofia Didática:
1. ✍️ **Espaços em Branco Digitáveis:** Cada questão possui um campo limpo em citação `> ` logo abaixo do enunciado, permitindo que o estudante posicione o cursor e comece a digitar a resposta imediatamente sem ter que apagar texto existente.
2. 🔄 **Fluxo de Avaliação em Par (IA-Pair Review):** Após resolver o exercício no arquivo, o estudante solicita a correção no chat (`"Corrigir Aula X"` / `"Avalie Practice/N5_PX.md"`), e a IA analisa as respostas digitadas após o caractere `>`, atribui nota e fornece feedback detalhado.
3. 🧠 **Recuperação Ativa & Interleaved Practice:** Questões focadas em Active Recall e mistura progressiva (conteúdo da aula atual + revisão cumulativa das aulas anteriores).
4. 🔒 **Gabarito Colapsável Oculto:** O gabarito com explicação detalhada fica no final do arquivo em uma tag `<details>`, permitindo autoavaliação ou conferência pós-feedback.

---

## ⛔ 2. REGRAS INVIOLÁVEIS DE GERAÇÃO

1. **Local e Nomenclatura:** Salvar o arquivo gerado exclusivamente no caminho `/Users/bmanica/Documents/GitHub/Bruno/Japones/Practice/N5_PX.md` (substituindo `X` pelo número da aula).
2. **Escopo Cumulativo Estrito (`JLPTN5.md`):** Consultar as colunas `Cum.G`, `Cum.K`, `Cum.V` da aula correspondente no ementário `JLPTN5.md`. É **estritamente proibido** utilizar gramática, kanji ou vocabulário de aulas futuras.
3. **Formatação de Resposta em Branco:** Todas as perguntas DEVEM ter o bloco de resposta em branco `> ` logo abaixo do enunciado, sem prefixos de texto (ex: NUNCA escrever `✍️ **Sua Resposta:**`).
4. **Sem Romaji:** Todo texto em japonês utiliza Kanji + Kana. Não utilizar Romaji.
5. **Aplicação da Política de Furigana (Sempre Furigana):** Todo kanji em toda questão do caderno traz `<ruby>` com a leitura completa da palavra, sem exceção. Nenhuma questão apresenta kanji sem furigana — o recall ativo de leitura acontece no Anki (frente = kanji sem furigana / verso = leitura + tradução). As questões testam significado, uso e contexto.

---

## 🏗️ 3. TEMPLATE CANÔNICO DE EXERCÍCIOS (`Practice/N5_PX.md`)

O arquivo gerado em `Practice/N5_PX.md` DEVE seguir rigorosamente esta estrutura em Markdown:

```markdown
# ✍️ EXERCÍCIOS DE FIXAÇÃO: AULA [X] — [TÍTULO DA AULA EM PORTUGUÊS]

> **Nível:** JLPT N5
> **Escopo de Conteúdo:** Aula [X] + Revisão Cumulativa (Aulas 1 a [X-1])
> **Tempo Estimado:** ~20 minutos
> **Status:** ⏳ Pendente de Resolução

---

## 1. 🔤 PARTE A: VOCABULÁRIO EM CONTEXTO

### 1.1 Significado & Uso (palavras sempre com furigana)
Escolha/escreva o significado correto da palavra destacada (sempre com furigana) em cada frase:

1. **[Frase em japonês com palavra da aula atual em negrito, com furigana]**
   > 

2. **[Frase em japonês com palavra da aula atual em negrito, com furigana]**
   > 

---

## 2. 🧩 PARTE B: GRAMÁTICA & ESTRUTURAS (PREENCHIMENTO)

Complete as lacunas das orações abaixo com a partícula, cópula ou forma correta:

1. **[Frase com lacuna [ &nbsp;&nbsp; ] para partícula/cópula]**
   > 

2. **[Frase com lacuna [ &nbsp;&nbsp; ] para partícula/cópula]**
   > 

---

## 3. 💬 PARTE C: TRADUÇÃO GUIADA & SINTAXE

Traduza as orações abaixo mantendo o registro polido (です/ます):

1. **[Frase em Português para traduzir em Japonês]**
   > 

2. **[Frase em Japonês para traduzir em Português]**
   > 

---

## 4. ⚠️ PARTE D: CAÇA-ERROS (COMMON PITFALLS)

Identifique o erro gramatical ou de contexto nas frases abaixo e reescreva-as corretamente:

1. ❌ **[Frase propositalmente incorreta baseada nas armadilhas da aula]**
   > 

---

## 5. 🔀 PARTE E: REVISÃO CUMULATIVA (INTERLEAVED PRACTICE)

Exercícios integrando conteúdos de aulas anteriores com a aula atual:

1. **[Exercício combinando gramática da Aula anterior + vocabulário da Aula atual]**
   > 

2. **[Exercício de síntese ou mini-diálogo para completar]**
   > 

---

## 🔍 GABARITO COMENTADO & AVALIAÇÃO

<details>
<summary><b>👉 Clique aqui para abrir o Gabarito Oficial e Explicações</b></summary>

### Respostas Oficiais:

#### Parte A: Vocabulário em Contexto
1. **Resposta:** [Significado em PT-BR] — *Explicação didática*.
2. **Resposta:** [Significado em PT-BR] — *Explicação didática*.

#### Parte B: Gramática & Estruturas
1. **Resposta:** [Item correto] — *Explicação do motivo gramatical*.
2. **Resposta:** [Item correto] — *Explicação do motivo gramatical*.

#### Parte C: Tradução Guiada
1. **Resposta:** [Frase correta em japonês]
2. **Resposta:** [Tradução correta em português]

#### Parte D: Caça-Erros
1. **Resposta:** ✅ [Frase corrigida] — *Explicação de por que a forma original estava incorreta*.

#### Parte E: Revisão Cumulativa
1. **Resposta:** [Solução integrada]
2. **Resposta:** [Solução integrada]

</details>
```

---

## 🔄 4. FLUXO DE INTERAÇÃO & CORREÇÃO PELA IA (AI-PAIR REVIEW)

Quando o estudante enviar a mensagem `"Corrigir Aula X"` ou `"Avalie meu Practice/N5_PX.md"`, a IA deve executar o seguinte procedimento:

1. **Abrir e Ler:** Inspecionar o arquivo `/Users/bmanica/Documents/GitHub/Bruno/Japones/Practice/N5_PX.md`.
2. **Extrair e Analisar:** Comparar as respostas digitadas após os blocos de citação (`> `) com o gabarito oficial.
3. **Retornar Feedback Didático no Chat:**
   - Atribuir uma pontuação final (ex: `8.5 / 10`).
   - Elogiar acertos em estruturas complexas.
   - Fornecer **explicações gramaticais minuciosas** para cada erro ou hesitação.
4. **Atualizar o Arquivo Local:**
   - Alterar o status do cabeçalho em `Practice/N5_PX.md` de `⏳ Pendente` para `✅ Corrigido em [Data] — Nota: X/10`.
   - Adicionar uma seção final `## 📝 Feedback da IA` ao fim do arquivo com o resumo dos comentários.
