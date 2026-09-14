/**
 * optimize_kanji.js — Reatribui os 80 kanji às 24 aulas de conteúdo de modo a
 * MAXIMIZAR a viabilidade pedagógica da seção "Chaves de Leitura".
 *
 * PROBLEMA: a Regra 7 manda ensinar cada kanji com "2-3 palavras do vocabulário
 * cumulativo" mostrando a decomposição. Isso só funciona se, na aula em que o
 * kanji estreia, já existirem palavras que o contenham. Na atribuição original,
 * 10 kanji tinham ZERO palavras disponíveis (bridging forçado) e 31 tinham só uma.
 *
 * SOLUÇÃO: atribuição ótima (algoritmo húngaro / min-cost perfect matching),
 * não heurística. Um greedy testado antes chegava a um resultado PIOR que o
 * original, porque empurrava kanji maduros para cedo e deixava as aulas finais
 * sem candidatos bons.
 *
 * FUNÇÃO OBJETIVO (lexicográfica, codificada nos pesos):
 *   1º  evitar q=0  ....... +1000  (bridging forçado é o defeito grave)
 *   2º  alcançar q>=2 ..... +1000  (o que a spec pede)
 *   3º  a palavra estar no vocabulário NOVO da própria aula ... +400
 *       (o caso mais forte: a aula ensina a palavra e o kanji junto)
 *   4º  riqueza total ..... +q
 * onde q = nº de palavras no inventário cumulativo até a aula que contêm o kanji.
 *
 * TETO ESTRUTURAL: 円 não aparecia em nenhuma das 644 palavras e 20 kanji
 * aparecem em exatamente uma em toda a lista. Para esses, nenhuma atribuição
 * alcança 2 palavras — o gargalo é o vocabulário, não a ordem das aulas.
 *
 * Uso: node scripts/optimize_kanji.js [--apply]
 */

const fs = require('fs');
const path = require('path');

const CONTENT_LESSONS = [1, 2, 3, 4, 6, 7, 8, 10, 11, 12, 14, 15, 16, 17, 19, 20, 21, 23, 24, 25, 27, 28, 29, 31];

function load() {
    const kjPath = path.join(__dirname, '../Content/N5_Kanji.md');
    const vocPath = path.join(__dirname, '../Content/N5_Vocabulary.md');
    const kanji = [];
    for (const l of fs.readFileSync(kjPath, 'utf8').split('\n')) {
        const m = l.match(/^\|\s*(\d+)\s*\|\s*(\S)\s*\|\s*(\d+)\s*\|/);
        if (m) kanji.push({ n: +m[1], ch: m[2], aulaOrig: +m[3] });
    }
    const words = [];
    let a = 0;
    for (const l of fs.readFileSync(vocPath, 'utf8').split('\n')) {
        const h = l.match(/^## Aula (\d+)/);
        if (h) { a = +h[1]; continue; }
        const m = l.match(/^\|\s*\d+\s*\|\s*(\S+)\s*\|/);
        if (m && a) words.push({ w: m[1], aula: a });
    }
    return { kanji, words, kjPath };
}

/** Algoritmo húngaro O(n^3) — matching perfeito de custo mínimo. */
function hungarian(cost) {
    const n = cost.length, m = cost[0].length;
    const INF = Infinity;
    const u = new Array(n + 1).fill(0), v = new Array(m + 1).fill(0);
    const p = new Array(m + 1).fill(0), way = new Array(m + 1).fill(0);
    for (let i = 1; i <= n; i++) {
        p[0] = i;
        let j0 = 0;
        const minv = new Array(m + 1).fill(INF);
        const used = new Array(m + 1).fill(false);
        do {
            used[j0] = true;
            const i0 = p[j0];
            let delta = INF, j1 = 0;
            for (let j = 1; j <= m; j++) {
                if (used[j]) continue;
                const cur = cost[i0 - 1][j - 1] - u[i0] - v[j];
                if (cur < minv[j]) { minv[j] = cur; way[j] = j0; }
                if (minv[j] < delta) { delta = minv[j]; j1 = j; }
            }
            for (let j = 0; j <= m; j++) {
                if (used[j]) { u[p[j]] += delta; v[j] -= delta; }
                else minv[j] -= delta;
            }
            j0 = j1;
        } while (p[j0] !== 0);
        do { const j1 = way[j0]; p[j0] = p[j1]; j0 = j1; } while (j0);
    }
    const assign = new Array(n).fill(-1);
    for (let j = 1; j <= m; j++) if (p[j] > 0) assign[p[j] - 1] = j - 1;
    return assign;
}

function main() {
    const apply = process.argv.includes('--apply');
    const { kanji, words, kjPath } = load();

    // Cotas por aula: preserva o tamanho original de cada aula (3 ou 4 kanji).
    const quota = {};
    CONTENT_LESSONS.forEach((L) => (quota[L] = 0));
    kanji.forEach((k) => quota[k.aulaOrig]++);

    // Expande as aulas em "vagas": 80 vagas para 80 kanji.
    const slots = [];
    for (const L of CONTENT_LESSONS) for (let i = 0; i < quota[L]; i++) slots.push(L);

    const qual = (ch, L) => words.filter((w) => w.aula <= L && w.w.includes(ch)).length;
    const own = (ch, L) => words.filter((w) => w.aula === L && w.w.includes(ch)).length;

    const score = (ch, L) => {
        const q = qual(ch, L);
        return (q >= 1 ? 1000 : 0) + (q >= 2 ? 1000 : 0) + (own(ch, L) >= 1 ? 400 : 0) + Math.min(q, 6);
    };

    const cost = kanji.map((k) => slots.map((L) => -score(k.ch, L)));
    const assign = hungarian(cost);
    kanji.forEach((k, i) => (k.aulaNova = slots[assign[i]]));

    // Relatório
    const bucket = (arr, f) => arr.reduce((acc, k) => { const q = f(k); acc[q === 0 ? 0 : q === 1 ? 1 : 2]++; return acc; }, [0, 0, 0]);
    const antes = bucket(kanji, (k) => qual(k.ch, k.aulaOrig));
    const depois = bucket(kanji, (k) => qual(k.ch, k.aulaNova));
    const ownAntes = kanji.filter((k) => own(k.ch, k.aulaOrig) >= 1).length;
    const ownDepois = kanji.filter((k) => own(k.ch, k.aulaNova) >= 1).length;

    console.log('                        ANTES → DEPOIS');
    console.log(`  0 palavras (bridging):  ${antes[0]}  →  ${depois[0]}`);
    console.log(`  1 palavra:             ${antes[1]}  →  ${depois[1]}`);
    console.log(`  2+ palavras (spec):    ${antes[2]}  →  ${depois[2]}`);
    console.log(`  kanji na própria aula: ${ownAntes}  →  ${ownDepois}`);
    const movidos = kanji.filter((k) => k.aulaNova !== k.aulaOrig);
    console.log(`\n  kanji reposicionados: ${movidos.length}/80`);
    const dist = CONTENT_LESSONS.map((L) => `${L}:${kanji.filter((k) => k.aulaNova === L).length}`);
    console.log('  kanji por aula: ' + dist.join(' '));
    const zeros = kanji.filter((k) => qual(k.ch, k.aulaNova) === 0);
    if (zeros.length) console.log('\n  ainda com 0 palavras: ' + zeros.map((k) => `${k.ch}(A${k.aulaNova})`).join(' '));

    if (!apply) { console.log('\n[dry-run] use --apply para gravar em Content/N5_Kanji.md'); return; }

    // Grava a coluna "Aula (intro)".
    // ATENÇÃO: os arquivos de Content/ usam CRLF. Um `(.*)$` cru NUNCA casa aí,
    // porque `.` não consome o \r e `$` (sem flag m) exige o fim absoluto da
    // string — a leitura funciona (regex sem âncora final) mas a escrita falha
    // em silêncio. Por isso normalizamos as quebras e restauramos no fim.
    const raw = fs.readFileSync(kjPath, 'utf8');
    const eol = raw.includes('\r\n') ? '\r\n' : '\n';
    const byN = new Map(kanji.map((k) => [k.n, k.aulaNova]));
    let alteradas = 0;
    const out = raw.split(/\r?\n/).map((l) => {
        const m = l.match(/^\|\s*(\d+)\s*\|\s*(\S)\s*\|\s*(\d+)\s*\|(.*)$/);
        if (!m || !byN.has(+m[1])) return l;
        if (+m[3] !== byN.get(+m[1])) alteradas++;
        return `| ${m[1]} | ${m[2]} | ${byN.get(+m[1])} |${m[4]}`;
    }).join(eol);
    if (!alteradas) { console.error('\n✗ ABORTADO: nenhuma linha casou o padrão da tabela.'); process.exit(1); }
    fs.writeFileSync(kjPath, out, 'utf8');
    console.log(`\n✓ ${alteradas} linhas alteradas.`);
    console.log('\n✓ Content/N5_Kanji.md atualizado.');
    fs.writeFileSync(path.join(__dirname, '../.kanji_assignment.json'),
        JSON.stringify(kanji.map(({ n, ch, aulaOrig, aulaNova }) => ({ n, ch, aulaOrig, aulaNova })), null, 2), 'utf8');
    console.log('✓ .kanji_assignment.json gravado (insumo para atualizar o YAML).');
}

if (require.main === module) main();
module.exports = { CONTENT_LESSONS };
