# ESPECIFICAÇÃO TÉCNICA: MODALIDADE READING (`Filters/Modalidades/Reading.md`)

Esta especificação define o padrão determinístico universal para a geração de exercícios de **Leitura Compreensiva & Narrativa (Reading)** para qualquer nível do programa de japonês (JLPT N5, N4, N3, etc.).

---

## ⛔ 1. REGRAS INVIOLÁVEIS (UNIVERSAIS)

1. **Princípio da Lista Branca (Escopo Cumulativo Estrito):** Utilizar **exclusivamente** o vocabulário, kanji e gramática acumulados até a `Aula X` conforme definidos no ementário do nível ativo (ex: `JLPTN5.md`, `JLPTN4.md`). Proibida a introdução de estruturas ou palavras de aulas futuras do respectivo nível.
2. **Política de Furigana por Recuperação Ativa (Primeira Ocorrência):**
   - Na modalidade Reading (treinamento), a tag `<ruby>` deve ser aplicada **apenas na PRIMEIRA ocorrência** de cada palavra com kanji no texto.
   - Ocorrências subsequentes da mesma palavra/kanji ao longo do texto **DEVEM aparecer SEM furigana**, estimulando o resgate ativo de memória pelo estudante.
   - *Regra de Aplicação:* A tag `<ruby>` é sempre aplicada sobre a **palavra inteira** (ex: `<ruby>日本語<rt>にほんご</rt></ruby>`), nunca dividida kanji por kanji.
   - *Kana puro:* Palavras compostas exclusivamente de hiragana/katakana nunca recebem `<ruby>`.
3. **Zero Romaji e Obrigação do Katakana:** Todo texto em japonês utiliza exclusivamente Kana + Kanji com furigana HTML na 1ª ocorrência. Nomes estrangeiros, palavras ocidentais ou termos que a IA não saiba traduzir **DEVEM ser escritos obrigatoriamente em Katakana** (ex: "Bruno" -> ブルーノ). O uso de Romaji (caracteres latinos) no texto japonês é estritamente proibido.
4. **Registro Linguístico:** Respeitar o nível de polidez (`です/ます` vs. casual) autorizado pelo escopo acumulado da aula.
5. **Salvamento Paramétrico em HTML e Google Drive:** A modalidade Reading gera um arquivo HTML baseado em `Filters/HTML/HTML_reading.md`. O arquivo é salvo localmente em `Practice/{NIVEL}_P{X}_Reading.html` (ex: `N5_P1_Reading.html`, `N4_P10_Reading.html`) e a IA **DEVE** executar o script de upload para o Google Drive (`upload_to_gdrive.js`).

---

## ⚙️ 2. ALGORITMO DETERMINÍSTICO DE GERAÇÃO

Ao receber o comando de leitura no chat (ex: `"Reading Aula X"`, `"Reading N4 Aula X"`), a IA DEVE executar os passos:

1. **Carregar Escopo do Nível Ativo:** Consultar o ementário mestre vigente (`JLPTN5.md` para N5, `JLPTN4.md` para N4) e extrair o inventário acumulado até a Aula X.
1.5 **Análise Prévia de Inventário e Validação Semântica (Vocabulary Gate — OBRIGATÓRIO):**
   - Antes de redigir qualquer texto, construir a **lista branca completa** de palavras e gramática disponíveis (inventário cumulativo até Aula X, conforme Regra 3.1 de `JLPTN5.md`).
   - Analisar o inventário e identificar: (a) quais palavras têm potencial narrativo, (b) quais estruturas gramaticais permitem construir frases complexas, (c) qual tipo de cenário/história é viável.
   - **Validação Semântica:** É proibido agrupar palavras apenas porque pertencem à lista se a frase não fizer sentido lógico no mundo real (ex: "Eu sou uma empresa").
   - **Planejamento Estratégico ANTES da redação:** A IA **DEVE** gerar um breve parágrafo (pensamento) explicitando a estratégia narrativa que adotará com as palavras disponíveis, garantindo que o texto fará sentido. Se o inventário for limitado, priorizar simplicidade extrema com coerência.
   - **Regra de ouro:** É preferível um texto curto, coerente e 100% dentro do inventário a um texto longo que não faça sentido ou introduza palavras inéditas.
2. **Seleção de Vocabulário (Regra dos 50% + Estendido):**
   - **Sessão Base (`Practice/{NIVEL}_P{X}_Reading.html`):** Incluir pelo menos **50% do vocabulário foco novo** da Aula X no texto, integrando-o com o vocabulário acumulado de revisão.
   - **Sessão Estendida (`"Mais Reading Aula X"`):** Criar uma Segunda Narrativa (`Practice/{NIVEL}_P{X}_Reading_Parte2.html`) focando no vocabulário remanescente.
3. **Redação Orgânica (Narrativa Mista) & Furigana Gradual:** Escrever o texto de forma fluida, intercalando descrições, narrativas e diálogos de maneira natural (como em um livro/conto). Aplicar furigana apenas na 1ª ocorrência das palavras com kanji.
4. **Compor Exercício:** Gerar de 4 a 6 perguntas de interpretação profunda em português.
5. **Gerar HTML, Salvar e Upload:** Formatando conforme `Filters/HTML/HTML_reading.md`, salvando em `Practice/{NIVEL}_P{X}_Reading.html` e executando o upload para o Google Drive via `upload_to_gdrive.js`. A discussão ocorrerá interativamente via chat.

---

## ⏱️ 3. ESCALONAMENTO DE EXTENSÃO DO TEXTO & ESTRUTURA ORGÂNICA

Todo exercício de Reading DEVE seguir uma **Estrutura Orgânica**:
- **Narrativa Intercalada:** O texto não deve ser separado artificialmente em "Parte 1" e "Parte 2". Deve ser uma única obra coesa que flua naturalmente entre descrições em 1ª ou 3ª pessoa (cenário, ações) e **diálogos incorporados** no meio da história.
- **Naturalidade Literária:** Tratar o texto como um fragmento de um livro, conto ou mangá leve, mantendo o dinamismo.

O tamanho ajusta-se estritamente ao estágio de maturidade da ementa do nível ativo:

| Estágio de Progresso do Nível | Frases Alvo (Texto Base) | Caracteres Japonês Alvo | Tempo Estimado (Aluno) | Formato Narrativo Orgânico |
|---|---|---|---|---|
| **Estágio Inicial** *(Primeiras 15% das aulas do nível)* | **12 a 18 frases** | ~400 – 600 caracteres | ~10 min | Cenário simples intercalado com diálogos curtos de cortesia |
| **Estágio Intermediário** *(Aulas centrais do nível)* | **25 a 35 frases** | ~700 – 1.000 caracteres | ~20 min | História coesa fluindo para diálogos práticos (compras, encontros) |
| **Estágio Avançado** *(Fase final do nível / Consolidado)* | **50 a 80 frases** | ~1.800 – 2.800 caracteres | **~40 min** | **Leitura Imersiva Completa:** Conto rico com conversas dinâmicas multi-personagem |

---

## 🏗️ 4. TEMPLATE CANÔNICO DE SAÍDA (`Practice/{NIVEL}_P{X}_Reading.html`)

A estrutura do arquivo HTML é definida rigorosamente em `Filters/HTML/HTML_reading.md`. Consulte-o para detalhes estruturais e visuais.

---

## 🔄 5. FLUXO DE CORREÇÃO E DISCUSSÃO NO CHAT

1. A IA apresenta, no chat, as perguntas de interpretação geradas.
2. O estudante responde pelo chat.
3. A IA avalia a precisão da resposta e fornece feedback didático detalhado no chat.
