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
| **📖 Leitura (Reading)** | Leitura narrativa/diálogo (3 a 12 min) com furigana gradual (1ª ocorrência) e questões de compreensão. | [Reading.md](file:///Users/bmanica/Documents/GitHub/Bruno/Japones/Filters/Modalidades/Reading.md) | `"Reading Aula X"` / `"Leitura Aula X"` |
| **✍️ Caderno Canônico (Treino Geral)** | Exercícios de 5 partes (Vocabulário, Gramática, Tradução, Caça-Erros, Revisão). | [Exercises_bckp.md](file:///Users/bmanica/Documents/GitHub/Bruno/Japones/Filters/Exercises_bckp.md) | `"Exercícios Aula X"` / `"Drill Aula X"` |

---

## 🔄 Fluxo de Invocação pela IA

Ao receber um comando de exercício no chat (ex: `"Reading Aula 1"`):
1. A IA identifica a modalidade solicitada.
2. A IA abre a especificação técnica correspondente em `Filters/Modalidades/[Modalidade].md`.
3. A IA lê as restrições cumulativas em `JLPTN5.md` para a aula especificada.
4. A IA gera o arquivo de treino correspondente na pasta `Practice/`.
