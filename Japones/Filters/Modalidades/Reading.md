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
5. **Escopo de Salvamento Exclusivamente Local (Markdown):** A modalidade Reading gera um arquivo Markdown local em `Practice/N5_P{X}_Reading.md`. **NÃO** executar o script Node de upload para o Google Drive (`upload_to_gdrive.js`), pois este é restrito a aulas de conteúdo em HTML.

---

## ⚙️ 2. ALGORITMO DETERMINÍSTICO DE GERAÇÃO

Ao receber o comando `"Reading Aula X"` (ou `"Leitura Aula X"`), a IA DEVE executar os passos:

1. **Carregar Escopo:** Consultar `JLPTN5.md` (Aula X) e extrair o inventário acumulado (`Cum.G`, `Cum.K`, `Cum.V`) dos arquivos de referência em `Content/`.
2. **Seleção de Vocabulário (Regra dos 50% + Estendido):**
   - **Sessão Base (`Practice/N5_P{X}_Reading.md`):** Incluir obrigatoriamente pelo menos **50% das palavras novas** da Aula X no texto, tecendo a narrativa em conjunto com o vocabulário de revisão (aulas 1 a X-1).
   - **Sessão Estendida (Comando `"Mais Reading Aula X"` / `"Extensão Reading Aula X"`):** Criar uma Segunda Narrativa (`Practice/N5_P{X}_Reading_Parte2.md`) focando nas palavras novas remanescentes que não entraram no primeiro texto.
3. **Redação & Furigana Gradual:** Escrever a história/diálogo aplicando a Regra do Furigana (ruby na 1ª ocorrência da palavra; sem ruby nas ocorrências seguintes).
4. **Compor Exercício & Ocultação de Gabarito:** Gerar de 3 a 5 perguntas de interpretação em português e incluir o gabarito oficial dentro da tag HTML `<details>` (colapsado).
5. **Salvar Arquivo:** Escrever o conteúdo final em `Practice/N5_P{X}_Reading.md` (substituindo `{X}` pelo número da aula).

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

## 🏗️ 4. TEMPLATE CANÔNICO DE SAÍDA (`Practice/N5_P{X}_Reading.md`)

O arquivo DEVE ser salvo em `Practice/N5_P{X}_Reading.md` (onde `{X}` é o número da aula):

```markdown
# 📖 LEITURA: AULA [X] — [TÍTULO DA HISTÓRIA]

> **Nível:** JLPT N5
> **Escopo:** Aula [X] (Cumulativo: Aulas 1 a [X])
> **Tempo Estimado de Leitura:** ~[Y] minutos
> **Tema:** [Breve descrição da cena/história]
> **Status:** ⏳ Pendente

---

## 📜 TEXTO

[Texto narrativo/diálogo com a 1ª ocorrência de cada palavra em kanji formatada com <ruby>Palavra<rt>kana</rt></ruby> e ocorrências subsequentes em Kanji puro]

---

## ❓ COMPREENSÃO DE TEXTO

Responda em português com base no texto acima:

1. [Pergunta factual: quem, o quê, onde ou quando]
   > 

2. [Pergunta de inferência ou contexto de diálogo]
   > 

3. [Pergunta sobre vocabulário ou gramática em contexto]
   > 

---

## 🔍 GABARITO & EXPLICAÇÕES

<details>
<summary><b>👉 Clique aqui para abrir o Gabarito Oficial e Explicações</b></summary>

### Respostas Esperadas:

1. **Resposta:** [...] — *Explicação: [...].*
2. **Resposta:** [...] — *Explicação: [...].*
3. **Resposta:** [...] — *Explicação: [...].*

</details>
```

---

## 🔄 5. FLUXO DE CORREÇÃO PELA IA

Ao receber no chat `"Corrigir Reading Aula X"` ou `"Avalie Practice/N5_PX_Reading.md"`:
1. Ler o arquivo `Practice/N5_P{X}_Reading.md` (ou `N5_P{X}_Reading_Parte2.md`).
2. Avaliar as respostas digitadas pelo estudante após os marcadores `> `.
3. Atribuir nota de 0.0 a 10.0 baseada na precisão de interpretação.
4. Atualizar o cabeçalho no arquivo para `> **Status:** ✅ Corrigido em [DATA] — Nota: [X.X]/10.0`.
5. Enviar feedback didático no chat detalhando acertos e destacando vocabulários e estruturas gramaticais relevantes da aula.
