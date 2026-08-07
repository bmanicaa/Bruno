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
3. **Zero Romaji:** Todo texto em japonês utiliza exclusivamente Kana + Kanji com furigana HTML na 1ª ocorrência.
4. **Registro Linguístico:** Respeitar o nível de polidez (`です/ます` vs. casual) autorizado pelo escopo acumulado da aula.
5. **Salvamento Paramétrico em HTML e Google Drive:** A modalidade Reading gera um arquivo HTML baseado em `Filters/HTML/HTML_reading.md`. O arquivo é salvo localmente em `Practice/{NIVEL}_P{X}_Reading.html` (ex: `N5_P1_Reading.html`, `N4_P10_Reading.html`) e a IA **DEVE** executar o script de upload para o Google Drive (`upload_to_gdrive.js`).

---

## ⚙️ 2. ALGORITMO DETERMINÍSTICO DE GERAÇÃO

Ao receber o comando de leitura no chat (ex: `"Reading Aula X"`, `"Reading N4 Aula X"`), a IA DEVE executar os passos:

1. **Carregar Escopo do Nível Ativo:** Consultar o ementário mestre vigente (`JLPTN5.md` para N5, `JLPTN4.md` para N4) e extrair o inventário acumulado até a Aula X.
2. **Seleção de Vocabulário (Regra dos 50% + Estendido):**
   - **Sessão Base (`Practice/{NIVEL}_P{X}_Reading.html`):** Incluir pelo menos **50% do vocabulário foco novo** da Aula X no texto, integrando-o com o vocabulário acumulado de revisão.
   - **Sessão Estendida (`"Mais Reading Aula X"`):** Criar uma Segunda Narrativa (`Practice/{NIVEL}_P{X}_Reading_Parte2.html`) focando no vocabulário remanescente.
3. **Redação da Estrutura Dupla (História + Diálogo) & Furigana Gradual:** Escrever o texto respeitando a estrutura obrigatória (Parte 1: História + Parte 2: Diálogo) e aplicando furigana apenas na 1ª ocorrência das palavras com kanji.
4. **Compor Exercício:** Gerar de 4 a 6 perguntas de interpretação profunda em português.
5. **Gerar HTML, Salvar e Upload:** Formatando conforme `Filters/HTML/HTML_reading.md`, salvando em `Practice/{NIVEL}_P{X}_Reading.html` e executando o upload para o Google Drive via `upload_to_gdrive.js`. A discussão ocorrerá interativamente via chat.

---

## ⏱️ 3. ESCALONAMENTO DE EXTENSÃO DO TEXTO & ESTRUTURA DUPLA OBRIGATÓRIA

Todo exercício de Reading DEVE conter obrigatoriamente uma **Estrutura Dupla**:
- **Parte 1 (A História / Narrativa):** Texto narrativo em 3ª ou 1ª pessoa contextualizando o ambiente, tema, clima ou fatos.
- **Parte 2 (O Diálogo Conversacional):** Conversação em turnos entre personagens interagindo dentro do cenário da narrativa.

O tamanho combinado (Parte 1 + Parte 2) ajusta-se estritamente ao estágio de maturidade da ementa do nível ativo:

| Estágio de Progresso do Nível | Frases Alvo (Texto Base) | Caracteres Japonês Alvo | Tempo Estimado (Aluno) | Formato Narrativo & Diálogo |
|---|---|---|---|---|
| **Estágio Inicial** *(Primeiras 15% das aulas do nível)* | **12 a 18 frases** | ~400 – 600 caracteres | ~10 min | História de apresentação/base + Diálogo de cortesia |
| **Estágio Intermediário** *(Aulas centrais do nível)* | **25 a 35 frases** | ~700 – 1.000 caracteres | ~20 min | Narrativa de rotina/local + Diálogo de compras/transporte |
| **Estágio Avançado** *(Fase final do nível / Consolidado)* | **50 a 80 frases** | ~1.800 – 2.800 caracteres | **~40 min** | **Leitura Imersiva Completa:** Conto/Crônica denso + Diálogo longo multi-personagem |

---

## 🏗️ 4. TEMPLATE CANÔNICO DE SAÍDA (`Practice/{NIVEL}_P{X}_Reading.html`)

A estrutura do arquivo HTML é definida rigorosamente em `Filters/HTML/HTML_reading.md`. Consulte-o para detalhes estruturais e visuais.

---

## 🔄 5. FLUXO DE CORREÇÃO E DISCUSSÃO NO CHAT

1. A IA apresenta, no chat, as perguntas de interpretação geradas.
2. O estudante responde pelo chat.
3. A IA avalia a precisão da resposta e fornece feedback didático detalhado no chat.
