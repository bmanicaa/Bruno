# ESPECIFICAÇÃO TÉCNICA: TEMPLATE HTML PARA READING (`Filters/HTML/HTML_reading.md`)

Este arquivo define a estrutura canônica e o design (CSS) dos exercícios de Leitura (Reading). Todos os exercícios gerados pela IA sob o comando `"Reading Aula N"` (ou `"Leitura Aula N"`) **DEVEM** aderir rigorosamente à estrutura canônica abaixo.

---

## 1. OBJETIVO DO TEMPLATE

O objetivo deste template é gerar um documento HTML estético, otimizado para leitura em telas grandes (desktop/tablet), dispositivos móveis e, fundamentalmente, preparado para impressão (tema limpo, controle de quebras de página). Ele integra um botão para alternar entre o tema claro e AMOLED.

---

## 2. REQUISITOS OBRIGATÓRIOS DO HTML/CSS

1. **Arquivo único (Self-Contained):** Todo o CSS e JavaScript deve estar incluído dentro das tags `<style>` e `<script>` do documento final. Nenhum link externo pode ser usado.
2. **Tema Limpo e Legível:** O texto deve ter uma fonte ampla e confortável para leitura, com amplo espaçamento entre linhas (line-height).
3. **Furiganas:** O documento de leitura aplica a regra: Furigana (ruby) na PRIMEIRA ocorrência de cada palavra com kanji.
4. **Perguntas de Compreensão:** Uma seção listando perguntas de interpretação sobre o texto.
5. **Gabarito não incluído (novo fluxo):** Como a interação acontecerá pelo chat, não há necessidade de esconder o gabarito no arquivo final.
6. **Layout para Impressão:** Todo conteúdo importante deve usar propriedades de impressão apropriadas, como `page-break-inside: avoid` e margens limpas. Ocultar os botões de controle na impressão (`@media print`).

---

## 3. ESTRUTURA CANÔNICA DO ARQUIVO HTML

O documento gerado deve ter a seguinte estrutura básica:

```html
<!DOCTYPE html>
<html lang="pt-BR" data-theme="light">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Reading: Aula X — JLPT N5</title>
  <style>
    /* VARIÁVEIS DO TEMA CLARO */
    :root[data-theme="light"] {
      --bg-color: #f7f9fb;
      --text-color: #2b2b2b;
      --card-bg: #ffffff;
      --border-color: #e2e8f0;
      --primary-color: #3b82f6;
      --badge-blue: #ebf8ff;
      --badge-blue-text: #2b6cb0;
      --badge-green: #f0fff4;
      --badge-green-text: #2f855a;
      --ruby-color: #64748b;
    }

    /* VARIÁVEIS DO TEMA ESCURO (AMOLED) */
    :root[data-theme="amoled"] {
      --bg-color: #000000;
      --text-color: #e0e0e0;
      --card-bg: #0a0a0a;
      --border-color: #222222;
      --primary-color: #3b82f6;
      --badge-blue: #1e3a8a;
      --badge-blue-text: #93c5fd;
      --badge-green: #064e3b;
      --badge-green-text: #6ee7b7;
      --ruby-color: #9ca3af;
    }

    * {
      box-sizing: border-box;
      margin: 0;
      padding: 0;
    }

    body {
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
      background-color: var(--bg-color);
      color: var(--text-color);
      line-height: 1.8;
      padding: 1.5rem;
      max-width: 900px;
      margin: 0 auto;
      transition: background-color 0.3s, color 0.3s;
    }

    /* HEADER */
    .header-card {
      background-color: var(--card-bg);
      border: 1px solid var(--border-color);
      border-radius: 12px;
      padding: 1.5rem;
      margin-bottom: 2rem;
      box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
    }
    .header-top-row {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 1rem;
    }
    .meta-badges {
      display: flex;
      gap: 0.5rem;
      flex-wrap: wrap;
    }
    .badge {
      padding: 0.2rem 0.6rem;
      border-radius: 999px;
      font-size: 0.75rem;
      font-weight: 600;
      text-transform: uppercase;
    }
    .badge-blue { background: var(--badge-blue); color: var(--badge-blue-text); }
    .badge-green { background: var(--badge-green); color: var(--badge-green-text); }

    .theme-toggle-btn {
      background: var(--primary-color);
      color: white;
      border: none;
      border-radius: 6px;
      padding: 0.4rem 0.8rem;
      font-size: 0.8rem;
      font-weight: 600;
      cursor: pointer;
      transition: background 0.2s;
    }
    .theme-toggle-btn:hover {
      opacity: 0.9;
    }

    h1 {
      font-size: 1.6rem;
      margin-bottom: 0.5rem;
    }

    /* TEXTO NARRATIVO */
    .story-card {
      background-color: var(--card-bg);
      border: 1px solid var(--border-color);
      border-radius: 12px;
      padding: 2rem;
      margin-bottom: 2rem;
      box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
    }
    .ja-text {
      font-size: 1.6rem;
      line-height: 2.4;
      font-family: "Hiragino Kaku Gothic Pro", "Meiryo", sans-serif;
    }

    ruby {
      ruby-align: center;
    }
    rt {
      font-size: 0.7rem;
      color: var(--ruby-color);
      user-select: none;
    }

    /* PERGUNTAS */
    .questions-card {
      background-color: var(--card-bg);
      border: 1px solid var(--border-color);
      border-radius: 12px;
      padding: 1.5rem;
      margin-bottom: 2rem;
      box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
    }
    .questions-card h2 {
      font-size: 1.3rem;
      margin-bottom: 1rem;
      border-bottom: 2px solid var(--border-color);
      padding-bottom: 0.5rem;
    }
    .questions-list {
      list-style-position: inside;
    }
    .questions-list li {
      margin-bottom: 1rem;
      font-size: 1.1rem;
    }

    /* OTIMIZAÇÃO PARA IMPRESSÃO */
    @media print {
      body {
        background-color: white !important;
        color: black !important;
        padding: 0;
      }
      .header-card, .story-card, .questions-card {
        border: none !important;
        box-shadow: none !important;
        background-color: white !important;
        padding: 0 !important;
        margin-bottom: 1.5rem !important;
      }
      .theme-toggle-btn {
        display: none !important;
      }
      .ja-text {
        font-size: 1.4rem;
        line-height: 2;
      }
    }
  </style>
</head>
<body>

  <header class="header-card">
    <div class="header-top-row">
      <div class="meta-badges">
        <span class="badge badge-blue">Nível JLPT N5</span>
        <span class="badge badge-green">⏳ ~[Y] Minutos</span>
      </div>
      <div>
        <button class="theme-toggle-btn" onclick="toggleTheme()" id="themeBtn">🌙 AMOLED Black</button>
      </div>
    </div>
    <h1>📖 LEITURA: AULA [X] — [TÍTULO]</h1>
    <div>
      <strong>🎯 Escopo:</strong> Aula [X] (Cumulativo: Aulas 1 a [X])<br>
      <strong>📝 Tema:</strong> [Breve descrição]
    </div>
  </header>

  <section class="story-card">
    <div class="ja-text">
      <!-- O texto japonês vai aqui. Lembre-se: furigana (ruby) na PRIMEIRA ocorrência de cada palavra com kanji. Depois apenas o kanji. -->
    </div>
  </section>

  <section class="questions-card">
    <h2>❓ COMPREENSÃO DE TEXTO</h2>
    <p style="margin-bottom: 1rem; font-style: italic;">Responda às seguintes perguntas e discuta com a IA no chat para receber feedback e o gabarito detalhado.</p>
    <ol class="questions-list">
      <li>[Pergunta factual: quem, o quê, onde ou quando]</li>
      <li>[Pergunta de inferência ou contexto de diálogo]</li>
      <li>[Pergunta sobre vocabulário ou gramática em contexto]</li>
    </ol>
  </section>

  <script>
    function toggleTheme() {
      const html = document.documentElement;
      const btn = document.getElementById('themeBtn');
      if (html.getAttribute('data-theme') === 'light') {
        html.setAttribute('data-theme', 'amoled');
        btn.innerHTML = '☀️ Light / Print';
      } else {
        html.setAttribute('data-theme', 'light');
        btn.innerHTML = '🌙 AMOLED Black';
      }
    }
  </script>
</body>
</html>
```
