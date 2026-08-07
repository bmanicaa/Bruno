# ESPECIFICAÇÃO TÉCNICA: MODALIDADE READING (`Filters/Modalidades/Reading.md`)

Esta especificação define o padrão determinístico para a geração de exercícios de **Leitura Compreensiva & Narrativa (Reading)** para qualquer aula do currículo N5.

---

## ⛔ 1. REGRAS INVIOLÁVEIS

1. **Princípio da Lista Branca (Escopo Cumulativo Estrito):** Utilizar **exclusivamente** itens das colunas `Cum.G`, `Cum.K` e `Cum.V` acumulados até a `Aula X` em `JLPTN5.md`. Proibida a introdução de gramática, partículas ou vocabulário de aulas futuras.
2. **Política de Furigana por Recuperação Ativa (Primeira Ocorrência):**
   - Na modalidade Reading (treinamento), a tag `<ruby>` deve ser aplicada **apenas na PRIMEIRA ocorrência** de cada palavra com kanji no texto.
   - Ocorrências subsequentes da mesma palavra/kanji ao longo do texto **DEVEM aparecer SEM furigana**, estimulando o resgate ativo de memória pelo estudante.
   - *Regra de Aplicação:* A tag `<ruby>` é sempre aplicada sobre a **palavra inteira** (ex: `<ruby>日本語<rt>にほんご</rt></ruby>`), nunca dividida kanji por kanji.
3. **Zero Romaji:** Todo texto em japonês utiliza exclusivamente Kana + Kanji com furigana HTML.
4. **Registro Linguístico:** Respeitar o nível de polidez (`です/ます` vs. casual) autorizado pelo escopo acumulado.
5. **Escopo de Salvamento em HTML e Google Drive:** A modalidade Reading gera um arquivo em formato HTML baseado no template especificado em `Filters/HTML/HTML_reading.md`. O arquivo deve ser salvo localmente em `Practice/N5_P{X}_Reading.html` e a IA **DEVE** executar o script Node de upload para o Google Drive (`upload_to_gdrive.js`).

---

## ⚙️ 2. ALGORITMO DETERMINÍSTICO DE GERAÇÃO

Ao receber o comando `"Reading Aula X"` (ou `"Leitura Aula X"`), a IA DEVE executar os passos:

1. **Carregar Escopo:** Consultar `JLPTN5.md` (Aula X) e extrair o inventário acumulado (`Cum.G`, `Cum.K`, `Cum.V`) dos arquivos de referência em `Content/`.
2. **Seleção de Vocabulário (Regra dos 50% + Estendido):**
   - **Sessão Base (`Practice/N5_P{X}_Reading.html`):** Incluir obrigatoriamente pelo menos **50% do vocabulário foco (`focus_vocab`) novo** da Aula X no texto, tecendo a narrativa em conjunto com o vocabulário de revisão (aulas 1 a X-1). O vocabulário de Anki (`anki_vocab`) não entra nessa exigência.
   - **Sessão Estendida (Comando `"Mais Reading Aula X"` / `"Extensão Reading Aula X"`):** Criar uma Segunda Narrativa (`Practice/N5_P{X}_Reading_Parte2.html`) focando nas palavras foco novas remanescentes que não entraram no primeiro texto.
3. **Redação & Furigana Gradual:** Escrever a história/diálogo aplicando a Regra do Furigana (ruby na 1ª ocorrência da palavra; sem ruby nas ocorrências seguintes).
4. **Compor Exercício:** Gerar de 3 a 5 perguntas de interpretação em português.
5. **Gerar HTML:** Formatando as informações usando a estrutura e CSS definidos em `Filters/HTML/HTML_reading.md`.
6. **Salvar e Upload:** Escrever o conteúdo final em `Practice/N5_P{X}_Reading.html` e executar o script de upload para o Google Drive: `node "/Users/bmanica/Documents/GitHub/Bruno/Google Workspace/Drive/scripts/upload_to_gdrive.js" "/Users/bmanica/Documents/GitHub/Bruno/Japones/Practice/N5_P{X}_Reading.html" "N5_P{X}_Reading.html"`. A discussão e correção ocorrerão interativamente via chat.

---

## ⏱️ 3. ESCALONAMENTO DE EXTENSÃO DO TEXTO

O tamanho da narrativa ajusta-se estritamente pela quantidade de frases e faixa de caracteres em japonês:

| Faixa de Aulas | Frases Alvo (Texto Base) | Caracteres Japonês Alvo | Tempo Estimado (Aluno) | Formato Narrativo Recomendado |
|---|---|---|---|---|
| **Aulas 1 a 4** | **4 a 6 frases** | ~80 – 120 caracteres | 3 – 5 min | Micro-diálogos de apresentação e trocas simples. |
| **Aulas 5 a 13** | **7 a 10 frases** | ~150 – 250 caracteres | 5 – 8 min | Diálogos expandidos e relatos de rotina diária. |
| **Aulas 14 a 24** | **12 a 16 frases** | ~300 – 450 caracteres | 8 – 10 min | Adaptações de contos populares ou narrativas curtas. |
| **Aulas 25 a 32** | **18 a 25 frases** | ~500 – 700 caracteres | 10 – 12 min | Contos folclóricos completos ou diálogos multi-personagem. |

---

## 🏗️ 4. TEMPLATE CANÔNICO DE SAÍDA (`Practice/N5_P{X}_Reading.html`)

A estrutura do arquivo HTML é definida rigorosamente em `Filters/HTML/HTML_reading.md`. Consulte-o para detalhes estruturais e visuais.

---

## 🔄 5. FLUXO DE CORREÇÃO E DISCUSSÃO NO CHAT

Diferente dos exercícios tradicionais, a correção do Reading não envolve ler um arquivo modificado pelo estudante. O estudante acessará e lerá a versão impressa ou hospedada do HTML, e interará diretamente com a IA no chat:

1. A IA apresenta, no chat, as perguntas de interpretação geradas.
2. O estudante responde pelo chat.
3. A IA avalia a precisão da resposta.
4. A IA envia feedback didático no chat detalhando acertos, explicando conceitos relevantes e fornecendo o gabarito oficial em caso de erros ou se solicitado.
