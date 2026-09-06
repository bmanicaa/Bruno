/**
 * validate_artifact.js — Validador canônico de artefatos do curso de japonês.
 *
 * FONTE ÚNICA DE VERDADE para a Regra 11 de JLPTN5.md e a §4.6 de
 * Filters/HTML/HTML_Lesson.md. Todo artefato gerado (aula HTML, Reading HTML,
 * Teste/Lacunas/Ditado em Markdown, TSV do Anki) DEVE passar por aqui.
 *
 * Uso via CLI:
 *   node scripts/validate_artifact.js <arquivo> [--aula N] [--mode M]
 *
 * Uso via require (upload_to_gdrive.js):
 *   const { validateArtifact, detectMode } = require('.../validate_artifact');
 *
 * Modos (inferidos do nome do arquivo quando não informados):
 *   lesson   — N5_L{n}.html          → furigana UNIVERSAL
 *   reading  — N5_P{n}_Reading.html  → furigana GRADUAL (só 1ª ocorrência)
 *   markdown — N5_P{n}*.md           → furigana UNIVERSAL
 *   anki     — N5_L{n}_Anki.tsv      → furigana UNIVERSAL na frente do card
 */

const fs = require('fs');
const path = require('path');

const KANJI = /[㐀-鿿豈-﫿]/;
const KANJI_G = /[㐀-鿿豈-﫿]/g;
const KANA_ONLY = /^[぀-ヿー\s]+$/;

// ─────────────────────────────────────────────────────────────
// Inferência de modo e número da aula a partir do nome do arquivo
// ─────────────────────────────────────────────────────────────
function detectMode(fileName) {
    const f = path.basename(fileName);
    if (/_Reading\.html$/i.test(f)) return 'reading';
    if (/^N5_L\d+\.html$/i.test(f)) return 'lesson';
    if (/\.html$/i.test(f)) return 'lesson';
    if (/\.tsv$/i.test(f)) return 'anki';
    if (/\.md$/i.test(f)) return 'markdown';
    return 'lesson';
}

function detectLesson(fileName) {
    const f = path.basename(fileName);
    const m = f.match(/N5_(?:L|P)(\d+)/i);
    return m ? parseInt(m[1], 10) : null;
}

// ─────────────────────────────────────────────────────────────
// Inventário cumulativo de vocabulário (Regra 3.1 — Vocabulary Gate)
// ─────────────────────────────────────────────────────────────
function loadInventory(upToLesson) {
    const vocPath = path.join(__dirname, '../Content/N5_Vocabulary.md');
    if (!fs.existsSync(vocPath) || !upToLesson) return null;
    const inv = new Set();
    let aula = 0;
    for (const line of fs.readFileSync(vocPath, 'utf8').split('\n')) {
        const a = line.match(/^## Aula (\d+)/);
        if (a) { aula = parseInt(a[1], 10); continue; }
        if (aula > 0 && aula <= upToLesson) {
            const m = line.match(/^\|\s*\d+\s*\|\s*(\S+)\s*\|\s*(\S+)\s*\|/);
            if (m) inv.add(m[1]);
        }
    }
    return inv;
}

// ─────────────────────────────────────────────────────────────
// Normalização: isola conteúdo verificável
// ─────────────────────────────────────────────────────────────
function stripNonContent(src, mode) {
    let s = src;
    if (mode === 'lesson' || mode === 'reading') {
        if (s.includes('</head>')) s = s.split('</head>').slice(1).join('</head>');
        s = s.replace(/<style[\s\S]*?<\/style>/gi, ' ')
             .replace(/<script[\s\S]*?<\/script>/gi, ' ')
             .replace(/<!--[\s\S]*?-->/g, ' ');
        // layer-4-breakdown é explicitamente isenta de ruby (§4.3)
        s = s.replace(/<div class="layer-4-breakdown">[\s\S]*?<\/div>/gi, ' ');
    }
    if (mode === 'markdown') {
        // Metadados do cabeçalho e blocos de código não são conteúdo didático
        s = s.replace(/```[\s\S]*?```/g, ' ');
    }
    return s;
}

// Um <ruby> nunca pode conter outro <ruby>: o corpo é "qualquer coisa que não
// abra uma nova tag ruby". Sem isso, um "<ruby>" solto em prosa (ex.: numa linha
// de metadados explicando a política) faria o match atravessar o arquivo inteiro.
const RUBY_RE = '<ruby[^>]*>((?:(?!<ruby)[\\s\\S])*?)<\\/ruby>';

function rubyRegions(text) {
    const out = [];
    const re = new RegExp(RUBY_RE, 'g');
    let m;
    while ((m = re.exec(text)) !== null) out.push([m.index, m.index + m[0].length]);
    return out;
}

function rubyBases(text) {
    const out = [];
    const re = new RegExp(RUBY_RE, 'g');
    let m;
    while ((m = re.exec(text)) !== null) {
        const inner = m[1];
        const rt = inner.indexOf('<rt>');
        const base = (rt >= 0 ? inner.slice(0, rt) : inner).replace(/<[^>]+>/g, '').trim();
        const reading = rt >= 0
            ? (inner.slice(rt).match(/<rt>([\s\S]*?)<\/rt>/) || [, ''])[1].replace(/<[^>]+>/g, '').trim()
            : '';
        out.push({ base, reading, index: m.index, raw: m[0] });
    }
    return out;
}

// ─────────────────────────────────────────────────────────────
// Validação principal
// ─────────────────────────────────────────────────────────────
function validateArtifact(content, opts = {}) {
    const mode = opts.mode || 'lesson';
    const lesson = opts.lesson || null;
    const errors = [];
    const warnings = [];

    const text = stripNonContent(content, mode);
    const bases = rubyBases(text);
    const regions = rubyRegions(text);
    const inRuby = (pos) => regions.some(([a, b]) => pos >= a && pos < b);
    const ctx = (i, n = 18) =>
        text.slice(Math.max(0, i - n), i + n).replace(/<[^>]+>/g, '').replace(/\s+/g, ' ').trim();

    // ── CHECK 1 (bloqueante, todos os modos) — ruby sobre kana puro
    for (const { base, raw } of bases) {
        if (!KANJI.test(base)) {
            errors.push(`CHECK1 [ruby sobre kana puro]: ${raw} — kana puro NUNCA recebe <ruby>.`);
        }
    }

    // ── CHECK 2 (bloqueante) — cobertura de furigana
    if (mode === 'reading') {
        // Furigana GRADUAL: 1ª ocorrência com ruby; ocorrências seguintes SEM ruby.
        const seen = new Set();
        for (const { base, raw, index } of bases) {
            if (!KANJI.test(base)) continue;
            if (seen.has(base)) {
                errors.push(
                    `CHECK2/reading [ruby repetido]: "${base}" já apareceu com furigana. ` +
                    `A modalidade Reading exige ruby APENAS na 1ª ocorrência (…${ctx(index)}…).`
                );
            }
            seen.add(base);
        }
        // Kanji solto antes da 1ª anotação = buraco de leitura
        // Títulos (<h1>/<h2>/<title>) são rótulos, não narrativa: isentos da checagem
        // de ORDEM (o corpo do texto anota a palavra na sua 1ª ocorrência real).
        const headingRegions = [];
        const headRe = new RegExp('<(h[12]|title)[^>]*>[\\s\\S]*?</\\1>', 'gi');
        let hm;
        while ((hm = headRe.exec(text)) !== null) headingRegions.push([hm.index, hm.index + hm[0].length]);
        const inHeading = (pos) => headingRegions.some(([a, b]) => pos >= a && pos < b);
        const firstRubyPos = new Map();
        for (const { base, index } of bases) {
            if (!firstRubyPos.has(base)) firstRubyPos.set(base, index);
        }
        let m;
        const wordRe = /[㐀-鿿豈-﫿]+/g;
        while ((m = wordRe.exec(text)) !== null) {
            if (inRuby(m.index) || inHeading(m.index)) continue;
            const w = m[0];
            const first = firstRubyPos.get(w);
            if (first === undefined) {
                warnings.push(`CHECK2/reading [nunca anotado]: "${w}" aparece sem furigana e nunca foi anotado antes (…${ctx(m.index)}…).`);
            } else if (m.index < first) {
                errors.push(`CHECK2/reading [ordem]: "${w}" aparece SEM furigana antes da sua 1ª anotação (…${ctx(m.index)}…).`);
            }
        }
    } else {
        // Furigana UNIVERSAL: todo kanji, em toda ocorrência, dentro de <ruby>.
        let m;
        KANJI_G.lastIndex = 0;
        while ((m = KANJI_G.exec(text)) !== null) {
            if (inRuby(m.index)) continue;
            errors.push(`CHECK2 [kanji sem ruby]: "${m[0]}" em …${ctx(m.index)}…`);
        }
    }

    // ── CHECK 3 (bloqueante, HTML de aula) — layer-2-kana não pode existir
    if (mode === 'lesson') {
        if (/layer-2-kana/.test(content)) {
            errors.push(
                'CHECK3 [layer-2-kana proibida]: a camada de leitura integral em kana é ' +
                'sempre redundante (layer-1 já é 100% anotada por ruby) e DEVE ser omitida (§4.3).'
            );
        }
    }

    // ── CHECK 4 (bloqueante, todos) — ruby sobre a palavra INTEIRA
    // 4a: <ruby> adjacentes = palavra fatiada kanji a kanji.
    // TAB e quebra de linha são FRONTEIRAS RÍGIDAS: separam colunas de um TSV ou
    // células/linhas de uma tabela, onde dois <ruby> vizinhos são palavras
    // distintas, não uma palavra fatiada. Só espaço comum ainda conta como
    // adjacência suspeita (texto japonês não usa espaço entre palavras).
    const adj = /<\/ruby>[ ]*<ruby/g;
    let a;
    while ((a = adj.exec(text)) !== null) {
        errors.push(
            `CHECK4a [ruby fatiado kanji a kanji]: …${ctx(a.index, 40)}… — ` +
            'a anotação deve cobrir a PALAVRA INTEIRA (ex.: <ruby>今日<rt>きょう</rt></ruby>), ' +
            'nunca um kanji por vez. Fatiar destrói leituras irregulares (jukujikun).'
        );
    }
    // 4b: kanji imediatamente colado a um <ruby>, fora dele
    for (const { raw, index } of bases) {
        const before = text[index - 1];
        const after = text[index + raw.length];
        if (before && KANJI.test(before)) {
            errors.push(`CHECK4b [ruby parcial]: kanji "${before}" colado ANTES de ${raw} — anote a palavra inteira.`);
        }
        if (after && KANJI.test(after)) {
            errors.push(`CHECK4b [ruby parcial]: kanji "${after}" colado DEPOIS de ${raw} — anote a palavra inteira.`);
        }
    }
    // 4c: prefixo honorífico / sufixo de tratamento partido para fora do ruby
    for (const { base, raw, index } of bases) {
        const before = text.slice(Math.max(0, index - 2), index);
        const after = text.slice(index + raw.length, index + raw.length + 3);
        const honPrefix = /[おご]$/.test(before);
        const honSuffix = /^(さん|ちゃん|くん|様)/.test(after);
        if (honPrefix && honSuffix) {
            errors.push(
                `CHECK4c [honorífico partido]: ${before.slice(-1)}${raw}${after.slice(0, 2)} — ` +
                `a palavra é お${base}さん (uma unidade lexical). Anote-a inteira: ` +
                `<ruby>お${base}さん<rt>…</rt></ruby>.`
            );
        }
    }

    // ── CHECK 5 (aviso) — Vocabulary Gate (Regra 3.1)
    const inv = loadInventory(lesson);
    if (inv) {
        const seen = new Set();
        for (const { base } of bases) {
            if (!KANJI.test(base) || seen.has(base)) continue;
            seen.add(base);
            if (!inv.has(base)) {
                warnings.push(
                    `CHECK5 [fora do inventário]: "${base}" não consta no vocabulário cumulativo ` +
                    `das Aulas 1–${lesson}. Se não for numeral/contador composto, é violação da Regra 3.1.`
                );
            }
        }
    } else if (lesson) {
        warnings.push('CHECK5 não executado: Content/N5_Vocabulary.md não encontrado.');
    }

    return { errors, warnings, mode, lesson };
}

// ─────────────────────────────────────────────────────────────
// CLI
// ─────────────────────────────────────────────────────────────
function main(argv) {
    const args = argv.slice(2);
    const getFlag = (name) => {
        const i = args.indexOf(`--${name}`);
        return i >= 0 ? args[i + 1] : null;
    };
    // O VALOR de uma flag não é um arquivo: sem isso, "--aula 3" fazia o "3"
    // ser tratado como caminho e o CLI reportava "não encontrado: 3".
    const flagValues = new Set();
    args.forEach((a, i) => { if (a.startsWith('--') && args[i + 1] && !args[i + 1].startsWith('--')) flagValues.add(i + 1); });
    const files = args.filter((x, i) => !x.startsWith('--') && !flagValues.has(i));
    if (!files.length) {
        console.error('uso: node scripts/validate_artifact.js <arquivo...> [--aula N] [--mode lesson|reading|markdown|anki]');
        process.exit(2);
    }
    let failed = 0;
    for (const f of files) {
        if (!fs.existsSync(f)) { console.error(`✗ não encontrado: ${f}`); failed++; continue; }
        const mode = getFlag('mode') || detectMode(f);
        const lesson = getFlag('aula') ? parseInt(getFlag('aula'), 10) : detectLesson(f);
        const { errors, warnings } = validateArtifact(fs.readFileSync(f, 'utf8'), { mode, lesson });
        const label = `${path.basename(f)} [mode=${mode}${lesson ? `, aula=${lesson}` : ''}]`;
        if (warnings.length) {
            console.log(`⚠️  ${label} — ${warnings.length} aviso(s):`);
            warnings.forEach((w) => console.log('   - ' + w));
        }
        if (errors.length) {
            failed++;
            console.error(`❌ ${label} — ${errors.length} ERRO(S) BLOQUEANTE(S):`);
            errors.forEach((e) => console.error('   - ' + e));
        } else {
            console.log(`✅ ${label} — validação aprovada.`);
        }
    }
    process.exit(failed ? 1 : 0);
}

if (require.main === module) main(process.argv);

module.exports = { validateArtifact, detectMode, detectLesson, loadInventory };
