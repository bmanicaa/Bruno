# 🗺️ MAPA DE MODALIDADES DE EXERCÍCIOS (`Filters/Exercises.md`)

Este arquivo atua como o **roteador principal e mapa de navegação** para o sistema de exercícios de japonês (JLPT N5, N4, N3, etc.). Ele direciona a IA para a especificação detalhada de cada modalidade de treino armazenada na pasta [Filters/Modalidades/](./Modalidades).

---

## 📌 Regra Global Inherit (Todas as Modalidades)

Todas as modalidades sob esta arquitetura herdam obrigatoriamente as seguintes restrições:

- **Escopo Cumulativo Estrito (`{CURRICULUM_FILE}`):** É **estritamente proibido** utilizar gramática, kanji ou vocabulário de aulas futuras. A IA deve consultar o ementário do nível ativo (`JLPTN5.md`, `JLPTN4.md`, etc.) da aula solicitada e utilizar exclusivamente o inventário acumulado até aquela aula (colunas `Cum.G`, `Cum.K`, `Cum.V`).
  - *Exceção única:* a modalidade **Ditado**, cujo insumo é áudio externo não controlado pelo repositório. Ver `Modalidades/Ditado.md` §1.4.
- **Validação Mecânica Obrigatória (`scripts/validate_artifact.js`):** Antes de entregar QUALQUER artefato (HTML, Markdown ou TSV), a IA **DEVE** executar
  `node scripts/validate_artifact.js <arquivo>` e corrigir todos os erros bloqueantes. O upload ao Drive já roda o mesmo validador e **bloqueia** o envio; para artefatos Markdown, que não passam pelo upload, a execução manual é a única barreira.
- **Estado Persistente (`Progress.md`):** Toda modalidade **lê** `Progress.md` antes de gerar e **atualiza** `Progress.md` após corrigir. É a única memória do sistema entre sessões.

---

## 📚 Índice de Modalidades Disponíveis

| Modalidade | Descrição / Foco | Arquivo de Especificação | Comando no Chat |
|---|---|---|---|
| **📖 Leitura (Reading)** | Leitura imersiva (História + Diálogo) em HTML (Google Drive) com furigana gradual (1ª ocorrência) e compreensão. | [Reading.md](./Modalidades/Reading.md) | `"Reading Aula X"` / `"Mais Reading Aula X"` (2ª narrativa, vocabulário remanescente) |
| **🧪 Teste / Drill Interativo** | Múltipla escolha em Markdown, **6 seções, 25 questões de 4 pts (100 pts)**: Vocabulário & Kanji, Partículas & Conectores, Gramática & Conjugação, Compreensão Situacional, Interpretação e **🔁 Revisão Espaçada**. As Seções 1-5 (80 pts) cobram só a Aula X; a Seção 6 (20 pts) cobra conteúdo antigo, priorizando `Progress.md` § Itens Fracos. | [Teste.md](./Modalidades/Teste.md) | `"Exercícios Aula X"` / `"Drill Aula X"` / `"Teste Aula X"` |
| **🧩 Lacunas (Preenchimento)** | Treino focado em gramática, partículas, conjugação e vocabulário da **matéria vigente** (Aula X) em Markdown (100 pts), 4 seções, sempre com **furigana universal em todo kanji**. | [Lacunas.md](./Modalidades/Lacunas.md) | `"Lacunas Aula X"` / `"Preencher Lacunas Aula X"` |
| **🎧 Ditado (書き取り)** | Transcrição de **áudio EXTERNO** (o repositório não gera áudio). Mede segmentação da fala, partículas átonas e ortografia; classifica cada erro numa taxonomia de 6 tipos. Nota só existe quando há transcrição oficial. | [Ditado.md](./Modalidades/Ditado.md) | `"Ditado Aula X"` / `"Corrigir Ditado Aula X"` |

---

## 🔄 Fluxo de Invocação e Correção pela IA

Ao receber um comando de exercício ou correção no chat (ex: `"Reading Aula 1"`, `"Exercícios N4 Aula 5"`, `"Lacunas Aula 1"` ou `"Corrigir Lacunas Aula 1"`):
1. A IA identifica a modalidade e o nível solicitados.
2. A IA abre a especificação técnica correspondente em `Filters/Modalidades/[Modalidade].md`.
3. A IA lê as restrições cumulativas no ementário mestre ativo (`JLPTN5.md`, `JLPTN4.md`, etc.) para a aula especificada.
4. A IA lê `Progress.md` — obrigatório para o Teste (Seção 6) e para o Ditado (§ 3 Escuta).
5. Para a modalidade **Reading**: gera o arquivo HTML em `Practice/{NIVEL}_P{X}_Reading.html`, realiza o upload para o Google Drive e conduz a interpretação no chat.
6. Para a modalidade **Teste**: gera o caderno Markdown em `Practice/{NIVEL}_P{X}.md` com 6 seções (25 questões × 4 pts). Ao receber `"Corrigir Aula X"`, lê as respostas, avalia (0-100 pts), atualiza o status no arquivo, **atualiza `Progress.md`** e envia feedback no chat separando matéria nova (Seções 1-5) de retenção (Seção 6).
7. Para a modalidade **Lacunas**: gera o caderno Markdown em `Practice/{NIVEL}_P{X}_Lacunas.md` com 4 seções de lacunas (100 pts) e furigana universal. Ao receber `"Corrigir Lacunas Aula X"`, lê as respostas digitadas (`> `), calcula a nota (0-100 pts), atualiza o status no arquivo, **atualiza `Progress.md`** e envia relatório didático detalhado com diagnóstico no chat.
8. Para a modalidade **Ditado**: gera a folha em `Practice/{NIVEL}_P{X}_Ditado.md`. Ao receber `"Corrigir Ditado Aula X"`, aplica o Modo A (com transcrição oficial → nota) ou o Modo B (sem → diagnóstico sem nota), classifica os erros na taxonomia de 6 tipos e **atualiza `Progress.md` § 3 Escuta**.
9. **Antes de entregar**, a IA executa `node scripts/validate_artifact.js <arquivo gerado>` e corrige todo erro bloqueante.
