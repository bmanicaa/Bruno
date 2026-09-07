# 📱 MODALIDADE TRANSVERSAL: VERSÃO E-READER (`Filters/Modalidades/EPUB.md`)

## 🎯 MISSÃO

Converter **qualquer artefato de estudo do curso** — aula, Reading, Teste, Lacunas
ou Ditado — num **EPUB 3** legível no Kindle Paperwhite, com o **furigana
preservado**.

Esta modalidade é **transversal**: ela não gera conteúdo novo, não define
pedagogia e não tem escopo cumulativo próprio. Ela **converte de formato** um
artefato que já existe. Toda a decisão didática já foi tomada pela modalidade que
produziu o arquivo-fonte.

**Ferramenta:** `scripts/build_epub.js` · **Contrato técnico:** `Filters/HTML/HTML_Lesson.md` §4.7

---

## ⚡ QUANDO RODA: AUTOMÁTICO PARA A AULA, SOB DEMANDA PARA O RESTO

| Artefato | Quando o EPUB é gerado |
|---|---|
| **📘 Aula** (`N5_L{X}.html`) | **AUTOMÁTICO.** Sai junto com o HTML no pipeline da Regra 13(b2) de `JLPTN5.md`. Não precisa ser pedido. |
| 📖 Reading · 🧪 Teste · 🧩 Lacunas · 🎧 Ditado | **SOB DEMANDA.** Só quando o estudante pedir, com um dos comandos abaixo. |

A assimetria é deliberada: a aula é o material que se lê de ponta a ponta e é o
caso de uso central do e-reader. Os exercícios têm valor no Kindle, mas geram
arquivo toda semana e nem sempre serão lidos lá — gerar sempre seria lixo no
Drive.

---

## 💬 COMANDOS NO CHAT

| Comando | Ação |
|---|---|
| `"EPUB Aula X"` / `"Kindle Aula X"` | Converte a **aula** `N5_L{X}.html`. |
| `"EPUB Reading Aula X"` / `"Kindle Reading Aula X"` | Converte `Practice/N5_P{X}_Reading.html`. |
| `"EPUB Teste Aula X"` / `"Kindle Teste Aula X"` | Converte `Practice/N5_P{X}.md`. |
| `"EPUB Lacunas Aula X"` / `"Kindle Lacunas Aula X"` | Converte `Practice/N5_P{X}_Lacunas.md`. |
| `"EPUB Ditado Aula X"` / `"Kindle Ditado Aula X"` | Converte `Practice/N5_P{X}_Ditado.md`. |

Sem modalidade explícita (`"EPUB Aula 4"`), o alvo é a **aula**.

```bash
node scripts/build_epub.js <arquivo.html|.md> --upload --nome-drive "<nome>.epub"
```

Se o HTML da aula não estiver mais em disco (a Regra 13(g) apaga o temporário),
baixe-o do Drive antes de converter.

---

## 🔀 FONTE → MODO DO VALIDADOR

O modo é inferido do nome do arquivo e determina a política de furigana aplicada
no EPUB — a **mesma** do artefato de origem, nunca uma política própria:

| Fonte | Formato | Modo | Política de furigana |
|---|---|---|---|
| `N5_L{X}.html` | HTML | `lesson` | Universal |
| `N5_P{X}_Reading.html` | HTML | `reading` | **Gradual** (só a 1ª ocorrência) |
| `N5_P{X}.md` (Teste) | Markdown | `markdown` | Universal |
| `N5_P{X}_Lacunas.md` | Markdown | `markdown` | Universal |
| `N5_P{X}_Ditado.md` | Markdown | `markdown` | Universal |

Markdown e HTML entram pelo **mesmo pipeline**: o Markdown é renderizado para
HTML primeiro e daí em diante o tratamento é idêntico.

---

## ⛔ HARD RULES

1. **O EPUB é DERIVADO, nunca escrito à mão.** A fonte da verdade continua sendo
   o `.html` / `.md`. Mudou o conteúdo? Regere o EPUB. **Nunca** edite o `.epub`.
2. **Regra 11 continua valendo.** `build_epub.js` roda o mesmo
   `scripts/validate_artifact.js` dos demais artefatos **antes** de escrever o
   arquivo. Erro bloqueante ⇒ nenhum `.epub` é escrito e o script sai com código
   1. Corrija a **fonte** e regere as duas versões — nunca "conserte" só o EPUB.
3. **Esta modalidade NÃO lê nem escreve `Progress.md`.** Ela não avalia nada e
   não produz nota. O estado de cada artefato pertence à modalidade que o gerou.
4. **Nada de conteúdo novo.** Se a conversão exigir inventar, reescrever ou
   resumir qualquer trecho japonês, isso é um defeito da fonte, não uma licença
   para editar no caminho.

---

## ⚠️ LIMITES HONESTOS DO E-READER

Estes limites são do aparelho, não do conversor. Estão documentados aqui para
que ninguém prometa ao estudante o que o Kindle não faz:

- **Não dá para digitar respostas.** Os campos `> Resposta N:` viram linhas de
  escrita marcadas, para responder mentalmente ou no papel. A resposta **oficial
  continua sendo digitada no `.md`, no computador** — é ele que os comandos
  `"Corrigir ..."` leem.
- **Não há botão de esconder o gabarito.** O `<details>` do Markdown vira um
  **capítulo próprio**, com quebra de página e aviso no topo: chega-se a ele de
  propósito pelo sumário, não por descuido ao virar a página.
- **O Ditado não leva áudio.** O EPUB é só a folha de transcrição; o áudio
  continua externo (`Ditado.md` §0).
- **Não existe o botão de ocultar furigana** da aula HTML: sem JavaScript, o
  ruby fica sempre visível. Para autoteste de leitura, use o **Reading**, cuja
  política gradual já anota só a 1ª ocorrência.

---

## 📲 COMO LEVAR PARA O KINDLE

Baixe o `.epub` do Drive e envie por **Send to Kindle** (e-mail `@kindle.com`,
app desktop ou `read.amazon.com`). A Amazon converte para KFX preservando o ruby.
Cópia direta por USB **não** funciona: o Paperwhite não lê EPUB sem conversão.

> Se o furigana não aparecer no aparelho, regere com `--idioma ja` — ver a nota
> em `Filters/HTML/HTML_Lesson.md` §4.7.
