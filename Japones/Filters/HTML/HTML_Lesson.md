# ESPECIFICAÇÃO TÉCNICA E TEMPLATE HTML/CSS CANÔNICO PARA AULAS DO JLPT N5 (`Filters/HTML/HTML_Lesson.md`)

---

## 🎯 1. OBJETIVO E VISÃO GERAL DO DOCUMENTO

Este documento é o **Padrão Absoluto de Engenharia Front-end e Especificação Pedagógica Definitiva** para a geração das 32 Aulas do Curso Preparatório JLPT N5 em formato **HTML5 puro com CSS3 embutido**. 

Ele serve como filtro e especificação completa para que a Inteligência Artificial geradora produza qualquer uma das 32 aulas (seja **📘 Aula de Conteúdo - Template A** ou **🔄 Aula de Consolidação - Template B**) mantendo 100% de consistência visual, zero bugs de CSS, e recursos pedagógicos interativos de alto nível.

### Principais Recursos Técnicos & Didáticos Incluídos:
1. 🌑 **AMOLED Pitch Black Theme (`data-theme="amoled"`):** Fundo 100% preto puro (`#000000`) para telas OLED/AMOLED de dispositivos móveis.
2. ☀️ **Light & Print-Friendly Theme (`data-theme="light"` / `@media print`):** Fundo branco limpo, contraste elevado e otimização para **impressão em papel ou PDF** (sem desperdício de tinta e sem quebra imprópria de páginas).
3. 🔤 **Furigana Interactive Toggle (Modo Estudo / Active Recall):** Botão para Ocultar/Exibir o Furigana (`<rt>`) sob demanda, permitindo que o aluno teste a leitura de memória antes de conferir.
4. 📘 **Suporte a Template A (Conteúdo)** & 🔄 **Template B (Consolidação):** Cobertura completa para aulas normais e aulas de revisão/consolidação (com Recall Rápido, Autodiagnóstico e Exercícios Interleaved).
5. 🧩 **Suporte a Componentes Especiais:** Módulo de Conjugação Verbal (Aula 19 - Seção 3E), Verbo-Core (Aula 6+), Badges de Grupos Verbaism, Callouts Didáticos (`Note`, `Tip`, `Warning`, `Pitfall`) e Simulado N5 (Aula 32).

---

## 🎨 2. ARQUITETURA DE DESIGN & CSS MASTER DUAL-THEME (`master-styles`)

### 2.1 CSS Master Completo (Pronto para Inserção no `<head>`)

```css
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Noto+Sans+JP:wght@400;500;700&display=swap');

/* --- TEMA 1: AMOLED PITCH BLACK (DEFAULT PARA TELAS) --- */
:root, [data-theme="amoled"] {
  --bg-main: #000000;          /* Preto Puro AMOLED (0% emissão de luz) */
  --bg-card: #121212;          /* Container Escuro Profundo */
  --bg-card-subtle: #1a1a1a;   /* Sub-container OLED */
  --border-color: #2d2d2d;     /* Bordas de Baixo Contraste */
  --border-light: #3d3d3d;
  
  --text-main: #ffffff;        /* Texto Branco Limpo */
  --text-muted: #a0a0a0;       /* Texto Secundário */
  --text-dim: #707070;
  
  --accent-blue: #38bdf8;      /* Sky 400 */
  --accent-blue-bg: rgba(56, 189, 248, 0.12);
  
  --accent-green: #4ade80;     /* Green 400 */
  --accent-green-bg: rgba(74, 222, 128, 0.12);
  
  --accent-yellow: #facc15;    /* Yellow 400 */
  --accent-yellow-bg: rgba(250, 204, 21, 0.12);
  
  --accent-red: #f87171;       /* Red 400 */
  --accent-red-bg: rgba(248, 113, 113, 0.12);
  
  --accent-purple: #c084fc;    /* Purple 400 */
  --accent-purple-bg: rgba(192, 132, 252, 0.12);
}

/* --- TEMA 2: LIGHT / PRINT-FRIENDLY (PARA IMPRESSÃO E ESTUDO DIURNO) --- */
[data-theme="light"] {
  --bg-main: #ffffff;          /* Branco Puro */
  --bg-card: #f8fafc;          /* Slate 50 */
  --bg-card-subtle: #f1f5f9;   /* Slate 100 */
  --border-color: #cbd5e1;     /* Slate 300 */
  --border-light: #94a3b8;     /* Slate 400 */
  
  --text-main: #0f172a;        /* Texto Slate Escuro */
  --text-muted: #475569;       /* Slate 600 */
  --text-dim: #64748b;         /* Slate 500 */
  
  --accent-blue: #0284c7;      /* Sky 600 - Alto contraste no claro */
  --accent-blue-bg: rgba(2, 132, 199, 0.08);
  
  --accent-green: #16a34a;     /* Green 600 */
  --accent-green-bg: rgba(22, 163, 74, 0.08);
  
  --accent-yellow: #d97706;    /* Amber 600 (Leitura legível no fundo claro) */
  --accent-yellow-bg: rgba(217, 119, 6, 0.08);
  
  --accent-red: #dc2626;       /* Red 600 */
  --accent-red-bg: rgba(220, 38, 38, 0.08);
  
  --accent-purple: #9333ea;    /* Purple 600 */
  --accent-purple-bg: rgba(147, 51, 234, 0.08);
}

/* Reset Básico e Fontes Global */
* {
  box-sizing: border-box;
  margin: 0;
  padding: 0;
}

body {
  background-color: var(--bg-main);
  color: var(--text-main);
  font-family: 'Inter', 'Noto Sans JP', sans-serif;
  line-height: 1.6;
  padding: 1.5rem 1rem;
  max-width: 900px;
  margin: 0 auto;
  transition: background-color 0.2s ease, color 0.2s ease;
}

/* --- BOTÕES DE CONTROLE NO HEADER --- */
.control-btn-group {
  display: flex;
  gap: 0.5rem;
  flex-wrap: wrap;
}

.theme-toggle-btn {
  background-color: var(--bg-card);
  color: var(--text-main);
  border: 1px solid var(--border-color);
  padding: 0.4rem 0.85rem;
  border-radius: 9999px;
  font-size: 0.8rem;
  font-weight: 600;
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  gap: 0.4rem;
  transition: all 0.2s ease;
  user-select: none;
}

.theme-toggle-btn:hover {
  border-color: var(--accent-blue);
  color: var(--accent-blue);
}

/* --- REGRAS DE TIPOGRAFIA ASIÁTICA & FURIGANA (RUBY) --- */
ruby {
  ruby-position: over;
  font-size: 1.05em;
  line-height: 2.0;
  display: inline-line-height;
}

rt {
  font-size: 0.6em;
  color: var(--text-muted);
  font-weight: 500;
  font-family: 'Noto Sans JP', sans-serif;
  line-height: 1.1;
  user-select: none;
  text-align: center;
  transition: opacity 0.15s ease;
}

/* RECURSO DE RECUPEAÇÃO ATIVA: OCULTAR FURIGANA PARA AUTOAVALIAÇÃO */
body.hide-furigana rt {
  opacity: 0;
}

body.hide-furigana ruby:hover rt {
  opacity: 1; /* Revela o furigana ao passar o mouse ou tocar no dispositivo móvel */
}

.ja-text {
  font-family: 'Noto Sans JP', sans-serif;
  letter-spacing: 0.02em;
}

/* --- CABEÇALHO & CARDS DE HEADER --- */
.header-card {
  background: var(--bg-card);
  border: 1px solid var(--border-color);
  border-left: 5px solid var(--accent-blue);
  border-radius: 0.75rem;
  padding: 1.75rem;
  margin-bottom: 2rem;
  position: relative;
}

.header-top-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1rem;
  flex-wrap: wrap;
  gap: 0.75rem;
}

.header-card h1 {
  font-size: 1.85rem;
  color: var(--text-main);
  margin-bottom: 0.75rem;
}

.meta-badges {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
}

.badge {
  font-size: 0.75rem;
  font-weight: 600;
  padding: 0.25rem 0.65rem;
  border-radius: 9999px;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.badge-blue { background: var(--accent-blue-bg); color: var(--accent-blue); border: 1px solid var(--accent-blue); }
.badge-purple { background: var(--accent-purple-bg); color: var(--accent-purple); border: 1px solid var(--accent-purple); }
.badge-yellow { background: var(--accent-yellow-bg); color: var(--accent-yellow); border: 1px solid var(--accent-yellow); }
.badge-green { background: var(--accent-green-bg); color: var(--accent-green); border: 1px solid var(--accent-green); }

/* Badges Especiais de Grupos de Verbos (Aula 19+) */
.badge-g1 { background: rgba(74,222,128,0.15); color: #4ade80; border: 1px solid #4ade80; }
.badge-g2 { background: rgba(56,189,248,0.15); color: #38bdf8; border: 1px solid #38bdf8; }
.badge-g3 { background: rgba(192,132,252,0.15); color: #c084fc; border: 1px solid #c084fc; }

.header-objective {
  font-size: 0.95rem;
  color: var(--text-muted);
  border-top: 1px solid var(--border-color);
  padding-top: 0.75rem;
  margin-top: 0.75rem;
}

/* --- ESTRUTURA DE SEÇÕES E TÍTULOS --- */
section {
  margin-bottom: 2.5rem;
}

h2.section-title {
  font-size: 1.4rem;
  color: var(--accent-blue);
  border-bottom: 2px solid var(--border-color);
  padding-bottom: 0.5rem;
  margin-bottom: 1.25rem;
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

h3.subsection-title {
  font-size: 1.15rem;
  color: var(--accent-purple);
  margin: 1.25rem 0 0.75rem 0;
}

/* --- SEÇÃO 1: CARDS DE KANJI (SOLUÇÃO ANTIVAZAMENTO) --- */
.kanji-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: 1.25rem;
  margin-bottom: 1.5rem;
}

.kanji-card {
  background-color: var(--bg-card);
  border: 1px solid var(--border-color);
  border-radius: 0.75rem;
  padding: 1.25rem;
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.kanji-big-box {
  background-color: var(--accent-yellow-bg);
  border: 2px solid var(--accent-yellow);
  border-radius: 0.75rem;
  min-height: 105px;
  padding: 1.5rem 1rem 0.75rem 1rem;
  display: flex;
  align-items: center;
  justify-content: center;
  box-sizing: border-box;
  overflow: visible;
}

.kanji-glyph {
  font-family: 'Noto Sans JP', sans-serif;
  font-size: 3rem;
  font-weight: 700;
  color: var(--accent-yellow);
  line-height: 1.4;
}

.kanji-details {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  font-size: 0.9rem;
}

.reading-tag {
  display: inline-block;
  font-size: 0.75rem;
  font-weight: 700;
  padding: 0.15rem 0.4rem;
  border-radius: 0.25rem;
  margin-right: 0.4rem;
}

.tag-radical { background: var(--accent-yellow-bg); color: var(--accent-yellow); }

.kanji-words {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
  margin: 0.25rem 0;
}

.kanji-word-chip {
  background-color: var(--bg-card-subtle);
  border: 1px solid var(--border-color);
  border-radius: 9999px;
  padding: 0.3rem 0.75rem;
  font-size: 0.95rem;
}

.kanji-mnemonic {
  background-color: var(--bg-card-subtle);
  border-left: 3px solid var(--accent-yellow);
  padding: 0.65rem 0.85rem;
  border-radius: 0.25rem;
  font-size: 0.85rem;
  color: var(--text-muted);
}

/* --- SEÇÃO 2: TABELAS RESPONSIVAS DE VOCABULÁRIO --- */
.table-wrapper {
  width: 100%;
  overflow-x: auto;
  -webkit-overflow-scrolling: touch;
  margin: 1.25rem 0;
  border-radius: 0.5rem;
  border: 1px solid var(--border-color);
}

table {
  width: 100%;
  border-collapse: collapse;
  white-space: normal;
  font-size: 0.95rem;
}

th {
  background-color: var(--bg-card);
  color: var(--accent-blue);
  font-weight: 600;
  text-align: left;
  padding: 0.85rem 1rem;
  border-bottom: 1px solid var(--border-color);
}

td {
  padding: 0.85rem 1rem;
  border-bottom: 1px solid var(--border-color);
  background-color: var(--bg-card-subtle);
  color: var(--text-main);
  word-break: break-word;
  word-wrap: break-word;
  white-space: normal;
}

tr:last-child td {
  border-bottom: none;
}

tr:nth-child(even) td {
  background-color: var(--bg-card);
}

/* --- SEÇÃO 3: BLOCS GRAMATICAIS E FÓRMULAS --- */
.grammar-block {
  background-color: var(--bg-card);
  border: 1px solid var(--border-color);
  border-radius: 0.75rem;
  padding: 1.5rem;
  margin-bottom: 1.5rem;
}

.formula-box {
  background-color: var(--accent-purple-bg);
  border: 1px dashed var(--accent-purple);
  color: var(--accent-purple);
  padding: 0.85rem 1.25rem;
  border-radius: 0.5rem;
  font-family: 'Inter', monospace;
  font-weight: 600;
  font-size: 1rem;
  margin: 0.85rem 0;
}

.mental-model {
  background-color: var(--bg-card-subtle);
  border-left: 4px solid var(--accent-blue);
  padding: 1rem;
  border-radius: 0.25rem 0.5rem 0.5rem 0.25rem;
  margin-bottom: 1.25rem;
  font-size: 0.95rem;
}

/* EXEMPLOS EM 4 CAMADAS OBRIGATÓRIAS */
.example-card {
  background-color: var(--bg-card-subtle);
  border: 1px solid var(--border-color);
  border-radius: 0.5rem;
  padding: 1.15rem;
  margin-bottom: 1rem;
}

.layer-1-ja {
  font-size: 1.25rem;
  font-weight: 500;
  color: var(--text-main);
  margin-bottom: 0.4rem;
}

.layer-3-pt {
  font-size: 0.95rem;
  color: var(--accent-green);
  font-weight: 500;
  margin-bottom: 0.6rem;
}

.layer-4-breakdown {
  font-size: 0.82rem;
  color: var(--text-muted);
  background-color: var(--bg-main);
  padding: 0.5rem 0.75rem;
  border-radius: 0.35rem;
  border: 1px solid var(--border-color);
  font-family: monospace;
}

/* --- SEÇÃO 3.5: MINI-DIÁLOGO (CHAT BUBBLES) --- */
.dialogue-container {
  display: flex;
  flex-direction: column;
  gap: 1rem;
  margin: 1.25rem 0;
}

.chat-bubble {
  max-width: 85%;
  padding: 1rem 1.25rem;
  border-radius: 1rem;
  position: relative;
}

.chat-left {
  align-self: flex-start;
  background-color: var(--bg-card);
  border: 1px solid var(--border-color);
  border-bottom-left-radius: 0.2rem;
}

.chat-right {
  align-self: flex-end;
  background-color: var(--bg-card-subtle);
  border: 1px solid var(--accent-blue);
  border-bottom-right-radius: 0.2rem;
}

.chat-speaker {
  font-size: 0.75rem;
  font-weight: 700;
  text-transform: uppercase;
  margin-bottom: 0.35rem;
}

.speaker-a { color: var(--accent-yellow); }
.speaker-b { color: var(--accent-blue); }

/* --- CALLOUTS DIDÁTICOS VARIADOS --- */
.callout-box {
  border-radius: 0.5rem;
  padding: 1.15rem;
  margin-bottom: 1.25rem;
  font-size: 0.92rem;
}

.callout-note {
  background-color: var(--accent-blue-bg);
  border: 1px solid rgba(56, 189, 248, 0.3);
  border-left: 5px solid var(--accent-blue);
}

.callout-tip {
  background-color: var(--accent-green-bg);
  border: 1px solid rgba(74, 222, 128, 0.3);
  border-left: 5px solid var(--accent-green);
}

.callout-warning {
  background-color: var(--accent-yellow-bg);
  border: 1px solid rgba(250, 204, 21, 0.3);
  border-left: 5px solid var(--accent-yellow);
}

.callout-pitfall {
  background-color: var(--accent-red-bg);
  border: 1px solid var(--accent-red);
  border-left: 5px solid var(--accent-red);
}

.pitfall-title {
  color: var(--accent-red);
  font-weight: 700;
  font-size: 1rem;
  display: flex;
  align-items: center;
  gap: 0.5rem;
  margin-bottom: 0.75rem;
}

.pitfall-item {
  margin-bottom: 0.5rem;
}

/* --- SEÇÃO 5: EXERCÍCIOS E GABARITO COLAPSÁVEL --- */
.exercise-card {
  background-color: var(--bg-card);
  border: 1px solid var(--border-color);
  border-radius: 0.75rem;
  padding: 1.25rem;
  margin-bottom: 1rem;
}

.exercise-number {
  color: var(--accent-blue);
  font-weight: 700;
  margin-right: 0.4rem;
}

details.gabarito-box {
  background-color: var(--bg-card-subtle);
  border: 1px solid var(--accent-green);
  border-radius: 0.5rem;
  padding: 0.75rem 1.25rem;
  margin-top: 1.5rem;
}

details.gabarito-box summary {
  color: var(--accent-green);
  font-weight: 700;
  cursor: pointer;
  outline: none;
  font-size: 1rem;
  user-select: none;
}

details.gabarito-box summary:hover {
  text-decoration: underline;
}

.gabarito-content {
  margin-top: 1rem;
  border-top: 1px dashed var(--border-color);
  padding-top: 1rem;
  font-size: 0.92rem;
}

/* --- COMPONENTES DA AULA DE CONSOLIDAÇÃO (TEMPLATE B) --- */
.recall-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0.75rem 1rem;
  border-bottom: 1px solid var(--border-color);
}

.autodiagnostico-table td {
  text-align: center;
}

/* --- OTIMIZAÇÃO RIGOROSA PARA IMPRESSÃO EM PAPEL (@media print) --- */
@media print {
  body {
    background-color: #ffffff !important;
    color: #000000 !important;
    max-width: 100% !important;
    padding: 0 !important;
  }

  .control-btn-group, .theme-toggle-btn {
    display: none !important; /* Oculta botões interativos no papel */
  }

  .header-card, .kanji-card, .grammar-block, .exercise-card, .example-card, .callout-box, .callout-pitfall, .table-wrapper {
    background-color: #ffffff !important;
    border: 1px solid #cbd5e1 !important;
    box-shadow: none !important;
    page-break-inside: avoid;
  }

  .header-card {
    border-left: 5px solid #0284c7 !important;
  }

  .kanji-big-box {
    background-color: #f8fafc !important;
    border: 2px solid #0f172a !important;
  }

  .kanji-glyph {
    color: #0f172a !important;
  }

  .table-wrapper {
    overflow: visible !important;
  }

  table {
    width: 100% !important;
    table-layout: fixed;
    white-space: normal !important;
  }

  th {
    background-color: #f1f5f9 !important;
    color: #0f172a !important;
    padding: 0.4rem 0.5rem !important;
    font-size: 0.82rem !important;
    word-wrap: break-word;
    word-break: break-word;
    white-space: normal !important;
  }

  td {
    background-color: #ffffff !important;
    color: #0f172a !important;
    padding: 0.4rem 0.5rem !important;
    font-size: 0.82rem !important;
    word-wrap: break-word;
    word-break: break-word;
    white-space: normal !important;
  }

  rt {
    color: #334155 !important;
    font-weight: 600 !important;
    opacity: 1 !important; /* Garante que Furigana sempre imprime */
  }

  details.gabarito-box {
    border: 1px solid #16a34a !important;
    page-break-inside: avoid;
  }

  details.gabarito-box summary ~ * {
    display: block !important;
  }
}
```

---

## 🏗️ 3. ESQUELETOS HTML5 CANÔNICOS

### 3.1 TEMPLATE A: AULA DE CONTEÚDO (📘 Aulas 1-4, 6-8, 10-12, 14-17, 19-21, 23-25, 27-29, 31)

```html
<!DOCTYPE html>
<html lang="pt-BR" data-theme="amoled">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Aula X: [Título da Aula] — JLPT N5</title>
  <style>
    /* INSIRA AQUI O CONTEÚDO INTEGRAL DO CSS MASTER (SEÇÃO 2.1) */
  </style>
</head>
<body>

  <!-- CABEÇALHO DA AULA COM BOTÕES DE CONTROLE -->
  <header class="header-card">
    <div class="header-top-row">
      <div class="meta-badges">
        <span class="badge badge-blue">Nível JLPT N5</span>
        <span class="badge badge-purple">Fase X: [Nome da Fase]</span>
        <span class="badge badge-yellow">Registro: [Polido / Casual]</span>
        <span class="badge badge-green">~60 Minutos</span>
      </div>
      
      <!-- Grupo de Botões de Controle Interativo -->
      <div class="control-btn-group">
        <button class="theme-toggle-btn" onclick="toggleFurigana()" id="furiganaBtn">
          👁️ Furigana: VISÍVEL
        </button>
        <button class="theme-toggle-btn" onclick="toggleTheme()" id="themeBtn">
          🌙 AMOLED Black
        </button>
      </div>
    </div>

    <h1>AULA X: [TÍTULO DA AULA EM PORTUGUÊS]</h1>
    <div class="header-objective">
      <strong>🎯 Objetivo Prático:</strong> [Descrever exatamente o que o aluno comunicará/entenderá ao fim da aula].
    </div>
    <div class="header-objective" style="border-top: none; padding-top: 0.25rem; font-size: 0.85rem;">
      <strong>✍️ Kanji da Aula (âncoras de reconhecimento):</strong> [Kanji 1], [Kanji 2], [Kanji 3]. *(Estude forma + significado com o radical; a leitura é aprendida nas palavras. Escrita à mão é opcional — o JLPT N5 não testa escrita. Todos os demais kanjis apresentados são exclusivamente para reconhecimento de leitura e trazem Furigana).*
    </div>
  </header>

  <!-- SEÇÃO 0: REVISÃO DA AULA ANTERIOR (Omitida na Aula 1) -->
  <section id="sec-0">
    <h2 class="section-title">0. 🔄 REVISÃO DA AULA ANTERIOR</h2>
    <div class="grammar-block">
      <p style="margin-bottom: 0.75rem;">Recapitulando os pontos fundamentais da aula anterior:</p>
      <div class="example-card">
        <strong>P1: [Pergunta de revisão sobre gramática/vocab anterior]</strong><br>
        <span style="color: var(--accent-green);">💡 Resposta: [Resposta comentada e direta]</span>
      </div>
    </div>
  </section>

  <!-- SEÇÃO 1: KANJI DA AULA (ÂNCORAS DE RECONHECIMENTO) -->
  <section id="sec-1">
    <h2 class="section-title">1. 🔤 KANJI DA AULA — ÂNCORAS DE RECONHECIMENTO</h2>
    <p style="margin-bottom: 1rem; color: var(--text-muted);">⚠️ Estes kanji <strong>não</strong> se estudam decorando leituras (onyomi/kunyomi) — isso é baixo rendimento e o JLPT N5 não testa escrita. Estude a <strong>forma</strong> + o <strong>significado</strong>, usando o radical como gancho de memória. A <strong>leitura</strong> é aprendida exclusivamente nas palavras da aula e do Anki.</p>
    <div class="kanji-grid">
      <div class="kanji-card">
        <div class="kanji-big-box">
          <ruby class="kanji-glyph">[Kanji]<rt>[Leitura na palavra-chave]</rt></ruby>
        </div>
        <div class="kanji-details">
          <div><strong>Significado:</strong> [Significado PT-BR]</div>
          <div><span class="reading-tag tag-radical">RADICAL</span> [Radical] — [1 linha: por que o radical ajuda a lembrar o significado]</div>
          <div><strong>Leitura em palavras (é assim que se aprende a ler):</strong></div>
          <div class="kanji-words">
            <span class="kanji-word-chip ja-text"><ruby>[Palavra 1]<rt>[Leitura]</rt></ruby></span>
            <span class="kanji-word-chip ja-text"><ruby>[Palavra 2]<rt>[Leitura]</rt></ruby></span>
            <span class="kanji-word-chip ja-text"><ruby>[Palavra 3]<rt>[Leitura]</rt></ruby></span>
          </div>
          <div style="font-size: 0.8rem; color: var(--text-dim);">✍️ Opcional (só se quiser escrever à mão): [Nº] traços. Ordem dos traços não é cobrada no JLPT N5.</div>
        </div>
        <div class="kanji-mnemonic">
          💡 <strong>Mnemônica Visual:</strong> [Explicação de associação mental fácil].
        </div>
      </div>
    </div>
  </section>

  <!-- SEÇÃO 2: VOCABULÁRIO FOCO (TABELAS SEMÂNTICAS ENXUTAS) -->
  <section id="sec-2">
    <h2 class="section-title">2. 📖 VOCABULÁRIO FOCO DA AULA</h2>
    <h3 class="subsection-title">Tema: [Ex: Família e Relações]</h3>
    <div class="table-wrapper">
      <table>
        <thead>
          <tr>
            <th>Palavra &amp; Leitura (Kanji + Furigana)</th>
            <th>Significado &amp; Classe (PT-BR)</th>
            <th>Combinação Comum (Collocation)</th>
          </tr>
        </thead>
        <tbody>
          <tr>
            <td class="ja-text"><ruby>私<rt>わたし</rt></ruby></td>
            <td>Eu <span style="color: var(--text-muted); font-size: 0.85em;">(Substantivo / Neutro)</span></td>
            <td class="ja-text"><ruby>私<rt>わたし</rt></ruby>は [Nome] です</td>
          </tr>
          <tr>
            <!-- Palavra 100% kana: SEM <ruby> (regra 4.2 item 0) -->
            <td class="ja-text">あなた</td>
            <td>Você <span style="color: var(--text-muted); font-size: 0.85em;">(Pronome)</span></td>
            <td class="ja-text">あなたは [Nome] ですか</td>
          </tr>
        </tbody>
      </table>
    </div>
  </section>

  <!-- SEÇÃO 2.5: VOCABULÁRIO ANKI -->
  <section id="sec-2-5">
    <h2 class="section-title">2.5 📋 VOCABULÁRIO ANKI — REVISÃO SEMANAL</h2>
    <div class="table-wrapper">
      <table>
        <thead>
          <tr>
            <th>Palavra &amp; Leitura (Kanji + Furigana)</th>
            <th>Tradução PT-BR</th>
            <th>Classe</th>
          </tr>
        </thead>
        <tbody>
          <tr>
            <td class="ja-text"><ruby>外国人<rt>がいこくじん</rt></ruby></td>
            <td>Estrangeiro</td>
            <td>Substantivo</td>
          </tr>
        </tbody>
      </table>
    </div>
  </section>

  <!-- SEÇÃO 3: ESTRUTURAS GRAMATICAIS -->
  <section id="sec-3">
    <h2 class="section-title">3. 🧩 ESTRUTURAS GRAMATICAIS & REGRAS</h2>
    <div class="grammar-block">
      <h3 class="subsection-title" style="margin-top: 0;">3.1 [Nome do Ponto Gramatical]</h3>
      
      <div class="formula-box">
        [Slot A: Substantivo] + は + [Slot B: Substantivo] + です
      </div>

      <div class="mental-model">
        <strong>🧠 Modelo Mental (Native Feeling):</strong><br>
        [Explicação intuitiva da perspectiva do falante nativo].
      </div>

      <!-- Exemplo 100% anotado (TODO kanji com ruby — política "sempre furigana"): layer-2-kana SEMPRE omitida (regra 4.3) -->
      <div class="example-card">
        <div class="layer-1-ja ja-text"><ruby>私<rt>わたし</rt></ruby>は<ruby>学生<rt>がくせい</rt></ruby>です。</div>
        <div class="layer-3-pt">"Eu sou estudante."</div>
        <div class="layer-4-breakdown">
          [私] (Eu) + [は] (Topico) + [学生] (Estudante) + [です] (Copula ser/estar)
        </div>
      </div>

      <!-- Todo exemplo segue o mesmo padrão: kanji sempre com ruby, sem layer-2-kana -->
      <div class="example-card">
        <div class="layer-1-ja ja-text"><ruby>一つ<rt>ひとつ</rt></ruby>です。</div>
        <div class="layer-3-pt">"É um só."</div>
        <div class="layer-4-breakdown">
          [一つ] (Um item) + [です] (Cópula ser/estar)
        </div>
      </div>
    </div>
  </section>

  <!-- SEÇÃO 3.5: MINI-DIÁLOGO EM CONTEXTO -->
  <section id="sec-3-5">
    <h2 class="section-title">3.5 💬 MINI-DIÁLOGO EM CONTEXTO</h2>
    <div class="grammar-block">
      <div class="dialogue-container">
        <div class="chat-bubble chat-left">
          <div class="chat-speaker speaker-a">Pessoa A</div>
          <div class="layer-1-ja ja-text"><ruby>初めまして<rt>はじめまして</rt></ruby>。</div>
          <div class="layer-3-pt">"Prazer em conhecê-lo."</div>
          <div class="layer-4-breakdown">[初めまして] (Prazer)</div>
        </div>
      </div>
    </div>
  </section>

  <!-- SEÇÃO 4: ARMADILHAS & ERROS COMUNS -->
  <section id="sec-4">
    <h2 class="section-title">4. ⚠️ ARMADILHAS & ERROS COMUNS</h2>
    <div class="callout-pitfall">
      <div class="pitfall-title">⚠️ Erro Clássico de Falantes de Português</div>
      <div class="pitfall-item">❌ <strong>Errado:</strong> <span class="ja-text">私 です 学生。</span></div>
      <div class="pitfall-item">💡 <strong>Por que é errado:</strong> O japonês segue a ordem SOV.</div>
      <div class="pitfall-item">✅ <strong>Correto:</strong> <span class="ja-text"><ruby>私<rt>わたし</rt></ruby>は<ruby>学生<rt>がくせい</rt></ruby>です。</span></div>
    </div>
  </section>

  <!-- SEÇÃO 5: FIXAÇÃO & AUTOAVALIAÇÃO -->
  <section id="sec-5">
    <h2 class="section-title">5. 🎯 FIXAÇÃO & AUTOAVALIAÇÃO</h2>
    <div class="exercise-card">
      <p><strong>Exercícios da Aula Atual</strong></p>
      <ol style="margin-left: 1.25rem; margin-top: 0.5rem; display: flex; flex-direction: column; gap: 0.75rem;">
        <li><span class="exercise-number">1. [Reconhecimento]</span> Identifique a função da partícula は na frase "...".</li>
      </ol>
    </div>

    <details class="gabarito-box">
      <summary>🔍 Clique aqui para ver o Gabarito Comentado</summary>
      <div class="gabarito-content">
        <p><strong>1. Resposta:</strong> [Explicação didática da resposta].</p>
      </div>
    </details>
  </section>

  <!-- SCRIPT INLINE DE CONTROLES (TEMA + FURIGANA) -->
  <script>
    function toggleTheme() {
      const html = document.documentElement;
      const btn = document.getElementById('themeBtn');
      if (html.getAttribute('data-theme') === 'light') {
        html.setAttribute('data-theme', 'amoled');
        btn.innerHTML = '🌙 AMOLED Black';
      } else {
        html.setAttribute('data-theme', 'light');
        btn.innerHTML = '☀️ Light / Print';
      }
    }

    function toggleFurigana() {
      const body = document.body;
      const btn = document.getElementById('furiganaBtn');
      body.classList.toggle('hide-furigana');
      if (body.classList.contains('hide-furigana')) {
        btn.innerHTML = '🙈 Furigana: OCULTO';
      } else {
        btn.innerHTML = '👁️ Furigana: VISÍVEL';
      }
    }
  </script>

</body>
</html>
```

---

### 3.2 TEMPLATE B: AULA DE CONSOLIDAÇÃO (🔄 Aulas 5, 9, 13, 18, 22, 26, 30, 32)

As Aulas de Consolidação **não ensinam conteúdo novo**. Elas exercitam ativamente o conteúdo acumulado dos blocos anteriores através da estrutura canônica abaixo:

```html
<!DOCTYPE html>
<html lang="pt-BR" data-theme="amoled">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Aula X: Consolidação (Aulas A a B) — JLPT N5</title>
  <style>
    /* INSIRA AQUI O CONTEÚDO INTEGRAL DO CSS MASTER (SEÇÃO 2.1) */
  </style>
</head>
<body>

  <header class="header-card">
    <div class="header-top-row">
      <div class="meta-badges">
        <span class="badge badge-purple">Nível JLPT N5</span>
        <span class="badge badge-yellow">🔄 Consolidação</span>
        <span class="badge badge-green">~45 Minutos</span>
      </div>
      <div class="control-btn-group">
        <button class="theme-toggle-btn" onclick="toggleFurigana()" id="furiganaBtn">👁️ Furigana: VISÍVEL</button>
        <button class="theme-toggle-btn" onclick="toggleTheme()" id="themeBtn">🌙 AMOLED Black</button>
      </div>
    </div>
    <h1>🔄 AULA X: CONSOLIDAÇÃO — Aulas A a B</h1>
    <div class="header-objective">
      <strong>🎯 Escopo de Revisão:</strong> Revisão ativa cumulativa de todo o conteúdo gramatical, vocabulário e kanjis cobertos nas Aulas A a B.
    </div>
  </header>

  <!-- SEÇÃO 1: RECALL RÁPIDO (MEMÓRIA ATIVA) -->
  <section id="sec-1">
    <h2 class="section-title">1. 🧠 RECALL RÁPIDO (15 MIN)</h2>
    <div class="grammar-block">
      <p style="margin-bottom: 1rem;">Tente responder mentalmente ou em papel ANTES de abrir a resposta.</p>
      
      <h3 class="subsection-title">A. Kanji ➔ Significado</h3>
      <div class="table-wrapper">
        <table>
          <thead>
            <tr><th>Kanji &amp; Leitura</th><th>Sua Resposta</th><th>Resposta Correta</th></tr>
          </thead>
          <tbody>
            <tr>
              <td class="ja-text" style="font-size: 1.5rem;"><ruby>一<rt>いち</rt></ruby></td>
              <td>_________</td>
              <td><details><summary>Revelar</summary>Um (いち / ひと)</details></td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </section>

  <!-- SEÇÃO 2: EXERCÍCIOS INTERLEAVED -->
  <section id="sec-2">
    <h2 class="section-title">2. 🔀 EXERCÍCIOS INTERLEAVED (15 MIN)</h2>
    <div class="exercise-card">
      <p><span class="badge badge-blue">Origem: Aula X + Aula Y</span></p>
      <p style="margin-top: 0.5rem;">1. <strong>[Tradução Guiada]</strong> Traduza para o japonês aplicando o vocabulário da Aula X e a gramática da Aula Y.</p>
    </div>
  </section>

  <!-- SEÇÃO 3: DIÁLOGO DE PRODUÇÃO -->
  <section id="sec-3">
    <h2 class="section-title">3. 💬 DIÁLOGO DE PRODUÇÃO (10 MIN)</h2>
    <div class="grammar-block">
      <p style="margin-bottom: 1rem;"><strong>Contexto:</strong> Diálogo longo em 4 camadas integrando o vocabulário acumulado.</p>
      <!-- Chat bubbles estilo 4 camadas -->
    </div>
  </section>

  <!-- SEÇÃO 4: AUTODIAGNÓSTICO -->
  <section id="sec-4">
    <h2 class="section-title">4. 📊 AUTODIAGNÓSTICO (5 MIN)</h2>
    <div class="table-wrapper">
      <table class="autodiagnostico-table">
        <thead>
          <tr><th>Item de Conteúdo</th><th>Status (✅ Seguro / ⚠️ Revisar / ❌ Esqueci)</th></tr>
        </thead>
        <tbody>
          <tr>
            <td>Gramática: Particle は vs が</td>
            <td>[ &nbsp; ] ✅ &nbsp;&nbsp;&nbsp; [ &nbsp; ] ⚠️ &nbsp;&nbsp;&nbsp; [ &nbsp; ] ❌</td>
          </tr>
        </tbody>
      </table>
    </div>
  </section>

  <script>
    function toggleTheme() {
      const html = document.documentElement;
      const btn = document.getElementById('themeBtn');
      if (html.getAttribute('data-theme') === 'light') {
        html.setAttribute('data-theme', 'amoled');
        btn.innerHTML = '🌙 AMOLED Black';
      } else {
        html.setAttribute('data-theme', 'light');
        btn.innerHTML = '☀️ Light / Print';
      }
    }
    function toggleFurigana() {
      const body = document.body;
      const btn = document.getElementById('furiganaBtn');
      body.classList.toggle('hide-furigana');
      if (body.classList.contains('hide-furigana')) {
        btn.innerHTML = '🙈 Furigana: OCULTO';
      } else {
        btn.innerHTML = '👁️ Furigana: VISÍVEL';
      }
    }
  </script>

</body>
</html>
```

---

## 📜 4. DIRETRIZES DE PREENCHIMENTO DIDÁTICO E CONTRATO DE CONTEÚDO

Toda IA responsável pela geração dos arquivos das aulas **DEVE** obedecer rigorosamente às seguintes diretrizes didáticas:

### 4.1 Proibição Absoluta de Resumos ou Omissões de Conteúdo
- É **estritamente proibido** omitir itens da ementa (`JLPTN5.md`), resumir tabelas com reticências `...` ou pular exercícios.
- Se a ementa atribui 15 palavras de vocabulário Foco e 10 palavras de vocabulário Anki para a Aula X, **todas as 25 palavras DEVEM ser explicitamente apresentadas em código HTML completo**.

### 4.2 Política de Furigana/Ruby (Sempre Furigana)

Todo kanji em TODA ocorrência recebe `<ruby>` com a leitura completa da palavra. Não há níveis de renderização: a lista de 80 kanji de `Content/N5_Kanji.md` deixa de definir furigana e passa a ser apenas a **prioridade de foco no Anki** (a coluna `Aula (intro)` indica quando cada kanji entra na rotação de cards).

0. **Kana Puro — NUNCA `<ruby>`:** Se a palavra **não contém NENHUM kanji** (hiragana/katakana puro: `あなた`, `はい`, `ええ`, `どうも`, `どうぞ`, `じゃあ`, `さあ`, partículas `は`/`です`/`か`/`を`/`に`...), escrever em **texto limpo, SEM `<ruby>`**. Ruby existe apenas para anotar a leitura de kanji. `<ruby>じゃあ<rt>じゃあ</rt></ruby>` é PROIBIDO.
1. **Todo kanji, sempre com `<ruby>`:** qualquer palavra que contenha kanji recebe `<ruby>` em **TODA ocorrência**, sem exceção por nível ou por repetição na aula. O furigana fica visível por padrão; o auto-teste é opcional, feito pelo botão "👁️ Furigana" (CSS `hide-furigana`) quando o aluno quiser. O recall ativo de leitura acontece no Anki (frente = kanji sem furigana / verso = leitura + tradução), não no HTML.
2. **Ruby sobre a Palavra Inteira (Jamais Kanji a Kanji):**
   - A anotação deve cobrir a palavra inteira: ex: `<ruby>今日<rt>きょう</rt></ruby>`, `<ruby>大人<rt>おとな</rt></ruby>`.
   - **Proibido** dividir kanji por kanji (`<ruby>今<rt>きょ</rt>日<rt>う</rt></ruby>`), pois isso destrói leituras irregulares (jukujikun).
3. **Proibido ensinar leituras isoladas:** Onyomi/kunyomi e contagem de traços **NUNCA** são apresentados como conteúdo de estudo nem cobrados em exercícios. A leitura do kanji é aprendida exclusivamente pelas palavras (`Leitura (Kana)` de `Content/N5_Vocabulary.md`). O radical aparece apenas como **gancho mnemônico** forma→significado. As colunas `Onyomi`/`Kunyomi` de `Content/N5_Kanji.md` são apenas dados de referência para o gerador, **nunca** conteúdo para o aluno. *(Única exceção de exibição: o card da Seção 1 do Template A pode mostrar a leitura do glifo no contexto da palavra-chave — é âncora de apresentação, não conteúdo de estudo; não quebra a regra do ruby por palavra inteira da Seção 4.2 item 2.)*
4. **Kanji em Callouts e Dicas do Anki:** NENHUM kanji pode aparecer sem `<ruby>` em nenhuma parte do documento HTML, inclusive dentro de callouts, avisos ou caixas de dica do Anki. Ao instruir o aluno a criar cards no Anki, use a palavra com `<ruby>` normalmente (ex: `<ruby>医者<rt>いしゃ</rt></ruby>`) ou descreva genericamente (*"mantendo a palavra em kanji na frente"*). Jamais escreva palavras em kanji puro sem `<ruby>` no texto corrido dos callouts.

### 4.3 Padrão de Camadas para Exemplos (3 Camadas com Layer-2 Sempre Omitida)
Todo exemplo de frase em japonês no documento deve apresentar as camadas especificadas no CSS. Como a `layer-1-ja` é sempre 100% anotada por `<ruby>` (§4.2), a antiga camada `layer-2-kana` (leitura integral) é **sempre redundante e DEVE ser omitida** em exemplos e diálogos:
1. `layer-1-ja`: Texto original em Japonês com Furigana `<ruby>` conforme a §4.2 (todo kanji anotado).
2. `layer-3-pt`: Tradução idiomática e natural em Português (PT-BR).
3. `layer-4-breakdown`: Decomposição sintática elemento por elemento entre colchetes (isenta de ruby).

### 4.4 Salvação Local e Upload para o Google Drive
Em conformidade com a Regra 13 de `JLPTN5.md`:
1. Salvar o arquivo gerado temporariamente como HTML.
2. Executar o script Node.js para envio ao Google Drive:
   ```bash
   node "/Users/bmanica/Documents/GitHub/Bruno/Google Workspace/Drive/scripts/upload_to_gdrive.js" "<caminho_do_arquivo_html_temp>" "N5_LX.html"
   ```
3. Retornar no chat apenas uma mensagem sucinta de confirmação do salvamento e upload.

### 4.5 Arquitetura de Tabelas Inteligentes (3 Colunas) & Otimização para Impressão
- Como toda palavra com Kanji já carrega o Furigana `<ruby>` sobreposto, a coluna isolada de "Leitura (Kana)" é redundante.
- As tabelas de vocabulário adotam a **Arquitetura de 3 Colunas Inteligentes**:
  1. `Palavra & Leitura (Kanji + Furigana)`
  2. `Significado & Classe (PT-BR)`
  3. `Combinação Comum (Collocation)`
- Essa estrutura, somada ao CSS de `@media print` (`table-layout: fixed`, `white-space: normal`, `word-break: break-word`), garante fluidez perfeita no celular e evita cortes na impressão em papel A4.

### 4.6 Checklist de Validação Automática (Antes do Upload)

O script `upload_to_gdrive.js` executa esta validação mecanicamente e **BLOQUEIA** o upload se qualquer checagem de 1 a 4 falhar (a 5 é aviso não bloqueante). O gerador DEVE conferir o mesmo antes de salvar o arquivo:

1. **Sem ruby sobre kana puro** (bloqueante): todo `<ruby>` deve ter base contendo ≥1 kanji. `あなた`, `はい`, `ええ`, `どうも`, `どうぞ`, `じゃあ`, `さあ` e partículas ficam **sem** `<ruby>`.
2. **Todo kanji com ruby** (política "sempre furigana"): não deve existir kanji solto fora das exceções (layer-4 breakdown, exemplo kunyomi do card com leitura em parênteses, listas meta). O script **bloqueia** qualquer kanji sem ruby — inclusive em textos explicativos, callouts e dicas do Anki. O gerador aplica ruby em **TODO** kanji, sem exceção.
3. **Nenhuma `layer-2-kana`** (bloqueante): como a `layer-1-ja` é sempre 100% anotada por ruby, a camada `layer-2-kana` **não deve existir** em exemplos ou diálogos.
4. **Ruby sobre a palavra inteira** (bloqueante): nenhum `<ruby>` dividido kanji a kanji; leituras irregulares (`今日` = きょう, `大人` = おとな) preservadas.
5. **Aviso não bloqueante esperado:** o script pode emitir avisos de "ruby repetido" para kanji dos 80 já introduzidos — **ignorar**; a política atual é ruby em toda ocorrência.
