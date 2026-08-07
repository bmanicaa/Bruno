# 🗺️ MAPA DE MODALIDADES DE EXERCÍCIOS (`Filters/Exercises.md`)

Este arquivo atua como o **roteador principal e mapa de navegação** para o sistema de exercícios de japonês N5. Ele direciona a IA para a especificação detalhada de cada modalidade de treino armazenada na pasta [Filters/Modalidades/](file:///Users/bmanica/Documents/GitHub/Bruno/Japones/Filters/Modalidades).

---

## 📌 Regra Global Inherit (Todas as Modalidades)

Todas as modalidades sob esta arquitetura herdam obrigatoriamente a seguinte restrição:
- **Escopo Cumulativo Estrito (`JLPTN5.md`):** É **estritamente proibido** utilizar gramática, kanji ou vocabulário de aulas futuras. A IA deve consultar o ementário `JLPTN5.md` da aula solicitada e utilizar exclusivamente o inventário acumulado até aquela aula (colunas `Cum.G`, `Cum.K`, `Cum.V`).

---

## 📚 Índice de Modalidades Disponíveis

| Modalidade | Descrição / Foco | Arquivo de Especificação | Comando no Chat |
|---|---|---|---|
| **📖 Leitura (Reading)** | Leitura narrativa/diálogo (3 a 12 min) em HTML (Google Drive) com furigana gradual (1ª ocorrência) e compreensão. | [Reading.md](file:///Users/bmanica/Documents/GitHub/Bruno/Japones/Filters/Modalidades/Reading.md) | `"Reading Aula X"` / `"Leitura Aula X"` |
| **🧪 Teste / Drill Interativo** | Avaliação focada na **matéria vigente** (Aula X) em Markdown, 6 seções (100 pts): Vocabulário, Partículas, Conjugação, Sintaxe, Tradução e Aplicação Integrada. Não cumulativo — revisão é responsabilidade do Anki, Consolidação e Reading. | [Teste.md](file:///Users/bmanica/Documents/GitHub/Bruno/Japones/Filters/Modalidades/Teste.md) | `"Exercícios Aula X"` / `"Drill Aula X"` / `"Teste Aula X"` |
| **🧩 Lacunas (Preenchimento)** | Treino focado em gramática, partículas, conjugação e vocabulário da **matéria vigente** (Aula X) em Markdown (100 pts), 4 seções, sempre com **furigana universal em todo kanji**. | [Lacunas.md](file:///Users/bmanica/Documents/GitHub/Bruno/Japones/Filters/Modalidades/Lacunas.md) | `"Lacunas Aula X"` / `"Preencher Lacunas Aula X"` |

---

## 🔄 Fluxo de Invocação e Correção pela IA

Ao receber um comando de exercício ou correção no chat (ex: `"Reading Aula 1"`, `"Exercícios Aula 1"`, `"Lacunas Aula 1"` ou `"Corrigir Lacunas Aula 1"`):
1. A IA identifica a modalidade solicitada.
2. A IA abre a especificação técnica correspondente em `Filters/Modalidades/[Modalidade].md`.
3. A IA lê as restrições cumulativas em `JLPTN5.md` para a aula especificada.
4. Para a modalidade **Reading**: gera o arquivo HTML em `Practice/N5_P{X}_Reading.html`, realiza o upload para o Google Drive e conduz a interpretação no chat.
5. Para a modalidade **Teste**: gera o caderno Markdown em `Practice/N5_P{X}.md` com campos digitáveis (`> `). Ao receber `"Corrigir Aula X"`, lê as respostas, avalia (0-100 pts), atualiza o status no arquivo e envia feedback didático detalhado no chat.
6. Para a modalidade **Lacunas**: gera o caderno Markdown em `Practice/N5_P{X}_Lacunas.md` com 4 seções de lacunas (100 pts) e furigana universal. Ao receber `"Corrigir Lacunas Aula X"`, lê as respostas digitadas (`> `), calcula a nota (0-100 pts), atualiza o status no arquivo e envia relatório didático detalhado com diagnóstico no chat.
