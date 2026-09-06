/**
 * audit_curriculum.js — Auditoria estrutural do currículo. Pré-voo obrigatório.
 *
 * Existe porque todo defeito estrutural encontrado até hoje (kanji órfãos,
 * caminhos quebrados, comandos sem rota, specs contraditórias, colunas de tabela
 * desatualizadas) foi achado por inspeção manual. Inspeção manual não escala e
 * não se repete. Cada checagem abaixo é um defeito real que já aconteceu.
 *
 * Uso:
 *   node scripts/audit_curriculum.js          # relatório completo
 *   node scripts/audit_curriculum.js --quiet  # só falhas (para CI / pré-voo)
 *
 * Saída: exit 0 se tudo passa, 1 se há FALHA. Avisos não derrubam o exit code.
 */

const fs = require('fs');
const path = require('path');

const ROOT = path.join(__dirname, '..');
const R = (p) => fs.readFileSync(path.join(ROOT, p), 'utf8');
const CONTENT_LESSONS = [1, 2, 3, 4, 6, 7, 8, 10, 11, 12, 14, 15, 16, 17, 19, 20, 21, 23, 24, 25, 27, 28, 29, 31];

const falhas = [];
const avisos = [];
const oks = [];
const fail = (t, d) => falhas.push({ t, d });
const warn = (t, d) => avisos.push({ t, d });
const ok = (t, d) => oks.push({ t, d });

// ── dados ────────────────────────────────────────────────────
function carregar() {
    const jlpt = R('JLPTN5.md');
    const yaml = jlpt.split('```yaml')[1] || '';
    const kanji = [];
    for (const l of R('Content/N5_Kanji.md').split(/\r?\n/)) {
        const m = l.match(/^\|\s*(\d+)\s*\|\s*(\S)\s*\|\s*(\d+)\s*\|/);
        if (m) kanji.push({ n: +m[1], ch: m[2], aula: +m[3] });
    }
    const words = [];
    let a = 0;
    for (const l of R('Content/N5_Vocabulary.md').split(/\r?\n/)) {
        const h = l.match(/^## Aula (\d+)/);
        if (h) { a = +h[1]; continue; }
        const m = l.match(/^\|\s*\d+\s*\|\s*(\S+)\s*\|/);
        if (m && a) words.push({ w: m[1], aula: a });
    }
    const gram = [];
    for (const l of R('Content/N5_Grammar.md').split(/\r?\n/)) {
        const m = l.match(/^\|\s*(\d+)\s*\|/);
        if (m) gram.push(+m[1]);
    }
    return { jlpt, yaml, kanji, words, gram };
}

// ── checagens ────────────────────────────────────────────────
function checarCobertura({ yaml, kanji, gram }) {
    const g = [], k = [];
    for (const l of yaml.split(/\r?\n/)) {
        const mg = l.match(/^\s+grammar:\s*\[([^\]]*)\]/);
        if (mg) g.push(...mg[1].split(',').map(Number));
        const mk = l.match(/^\s+kanji:\s*\[([^\]]*)\]/);
        if (mk) k.push(...mk[1].split(',').map(Number));
    }
    const dup = (a) => [...new Set(a.filter((x, i) => a.indexOf(x) !== i))];
    const falta = (a, tot) => tot.filter((x) => !a.includes(x));
    const gTot = gram.length ? gram : [...Array(84).keys()].map((i) => i + 1);
    const kTot = kanji.map((x) => x.n);
    if (falta(g, gTot).length || dup(g).length) fail('cobertura de gramática', `faltando ${falta(g, gTot)} · duplicados ${dup(g)}`);
    else ok('cobertura de gramática', `${g.length} referências, cada uma exatamente 1×`);
    if (falta(k, kTot).length || dup(k).length) fail('cobertura de kanji', `faltando ${falta(k, kTot)} · duplicados ${dup(k)}`);
    else ok('cobertura de kanji', `${k.length} referências, cada uma exatamente 1×`);

    // YAML × coluna "Aula (intro)" de N5_Kanji.md
    const assign = {};
    let cur = null;
    for (const l of yaml.split(/\r?\n/)) {
        const m = l.match(/^  (\d+):/); if (m) { cur = +m[1]; continue; }
        const mk = l.match(/^\s+kanji:\s*\[([^\]]*)\]/);
        if (mk && cur) mk[1].split(',').forEach((x) => (assign[+x] = cur));
    }
    const bad = kanji.filter((x) => assign[x.n] !== x.aula);
    if (bad.length) fail('sincronia YAML × N5_Kanji.md', bad.map((b) => `${b.ch}: md=A${b.aula} yaml=A${assign[b.n]}`).join(' · '));
    else ok('sincronia YAML × N5_Kanji.md', '80/80 consistentes');
}

function checarEnsinabilidadeKanji({ kanji, words }) {
    const qual = (ch, L) => words.filter((w) => w.aula <= L && w.w.includes(ch)).length;
    const zeros = kanji.filter((k) => qual(k.ch, k.aula) === 0);
    const uns = kanji.filter((k) => qual(k.ch, k.aula) === 1);
    if (zeros.length) fail('kanji sem palavra na aula de estreia',
        `${zeros.length} kanji forçam nota de bridging: ${zeros.map((k) => `${k.ch}(A${k.aula})`).join(' ')}`);
    else ok('kanji sem palavra na aula de estreia', 'nenhum — todo kanji estreia com pelo menos 1 palavra');
    // 1 palavra só é aceitável quando é o teto do próprio vocabulário
    const tetoUm = uns.filter((k) => words.filter((w) => w.w.includes(k.ch)).length <= 1);
    const evitavel = uns.filter((k) => !tetoUm.includes(k));
    if (evitavel.length) warn('kanji com 1 palavra evitável',
        `${evitavel.length} poderiam ter 2+ se movidos: ${evitavel.map((k) => `${k.ch}(A${k.aula})`).join(' ')} — rode scripts/optimize_kanji.js`);
    ok('kanji com 2+ palavras', `${kanji.length - zeros.length - uns.length}/${kanji.length} · ${tetoUm.length} limitados pelo teto do vocabulário`);
}

function checarTabela({ jlpt, kanji, words, yaml }) {
    const vcount = {}, kcount = {}, gcount = {};
    words.forEach((w) => (vcount[w.aula] = (vcount[w.aula] || 0) + 1));
    kanji.forEach((k) => (kcount[k.aula] = (kcount[k.aula] || 0) + 1));
    let cur = null;
    for (const l of yaml.split(/\r?\n/)) {
        const m = l.match(/^  (\d+):/); if (m) { cur = +m[1]; continue; }
        const mg = l.match(/^\s+grammar:\s*\[([^\]]*)\]/);
        if (mg && cur) gcount[cur] = mg[1].split(',').length;
    }
    let cg = 0, ck = 0, cv = 0; const erros = [];
    for (const line of jlpt.split(/\r?\n/)) {
        const m = line.match(/^\| (\d+) \| (📘|🔄) \|[^|]*\|[^|]*\| *([^|]*?) *\| *([^|]*?) *\| *([^|]*?) *\| *(\d+) *\| *(\d+) *\| *(\d+) *\|$/);
        if (!m) continue;
        const n = +m[1];
        cg += gcount[n] || 0; ck += kcount[n] || 0; cv += vcount[n] || 0;
        if (+m[6] !== cg || +m[7] !== ck || +m[8] !== cv)
            erros.push(`Aula ${n}: tabela diz ${m[6]}/${m[7]}/${m[8]}, dados dizem ${cg}/${ck}/${cv}`);
    }
    if (erros.length) fail('colunas cumulativas da tabela', erros.slice(0, 5).join(' · '));
    else ok('colunas cumulativas da tabela', `Cum.G/K/V conferem com Content/ (${cg}/${ck}/${cv})`);
}

function checarTaxonomia() {
    const voc = R('Content/N5_Vocabulary.md');
    const linha = voc.split(/\r?\n/).find((l) => l.includes('Taxonomia canônica permitida'));
    if (!linha) return warn('taxonomia de subtítulos', 'linha de taxonomia não encontrada');
    const permitidos = [...linha.matchAll(/`([^`]+)`/g)].map((m) => m[1]).filter((x) => x !== '###');
    const usados = [...new Set([...voc.matchAll(/^### (.+)$/gm)].map((m) => m[1].trim()))];
    const fora = usados.filter((u) => !permitidos.includes(u));
    if (fora.length) fail('taxonomia de subtítulos', `fora da taxonomia: ${fora.join(' · ')}`);
    else ok('taxonomia de subtítulos', `${usados.length} subtítulos, todos na taxonomia canônica`);
}

function checarCaminhos() {
    const arquivos = [];
    const walk = (d) => {
        for (const e of fs.readdirSync(path.join(ROOT, d), { withFileTypes: true })) {
            if (e.name === '.git' || e.name === 'node_modules') continue;
            const rel = path.join(d, e.name);
            if (e.isDirectory()) walk(rel);
            else if (/\.(md|js)$/.test(e.name)) arquivos.push(rel);
        }
    };
    walk('.');
    const padroes = [/Users\/bmanica/, /Bruno\\Google/, /Bruno\/Japones/];
    const quebrados = [];
    for (const f of arquivos) {
        const src = R(f);
        for (const p of padroes) if (p.test(src)) quebrados.push(`${f} (${p})`);
    }
    if (quebrados.length) fail('caminhos obsoletos', quebrados.join(' · '));
    else ok('caminhos obsoletos', `${arquivos.length} arquivos varridos, nenhum caminho morto`);

    // o script de upload precisa resolver o validador compartilhado
    const up = path.join(ROOT, '../Google Workspace/Drive/scripts/upload_to_gdrive.js');
    if (!fs.existsSync(up)) warn('upload_to_gdrive.js', 'não encontrado no caminho relativo esperado');
    else if (!R(path.relative(ROOT, up)).includes('validate_artifact')) fail('upload_to_gdrive.js', 'não importa o validador compartilhado');
    else ok('upload_to_gdrive.js', 'importa scripts/validate_artifact.js');
}

function checarComandos() {
    const rotas = R('Filters/Exercises.md') + R('JLPTN5.md');
    const decl = new Set();
    for (const f of fs.readdirSync(path.join(ROOT, 'Filters/Modalidades'))) {
        if (!f.endsWith('.md')) continue;
        for (const m of R(`Filters/Modalidades/${f}`).matchAll(/`"([^"]*Aula X)"`/g)) decl.add(m[1]);
    }
    // Um prefixo de nível ("Reading N4 Aula X") é a MESMA modalidade qualificada
    // por nível — o roteamento por nível já está descrito em Exercises.md. Só a
    // forma sem prefixo precisa constar nas rotas.
    const niveis = new Set();
    const semNivel = (c) => c.replace(/\s+N[2-5]\s+/, (m) => { niveis.add(m.trim()); return ' '; });
    const orfaos = [...decl].filter((c) => !rotas.includes(semNivel(c).replace(/ Aula X$/, '')));
    if (orfaos.length) fail('comandos sem rota', orfaos.join(' · '));
    else ok('comandos sem rota', `${decl.size} comandos declarados, todos roteados`);

    // Níveis citados cujo ementário ainda não existe: informativo, não é defeito.
    const ausentes = [...niveis].filter((n) => !fs.existsSync(path.join(ROOT, `JLPT${n}.md`)));
    if (ausentes.length) warn('níveis citados sem ementário',
        `${ausentes.join(', ')} aparecem em exemplos de comando, mas JLPT${ausentes[0]}.md ainda não existe — os comandos desses níveis são aspiracionais`);
}

function checarContradicoes() {
    const alvos = ['JLPTN5.md', 'Filters/Exercises.md', 'Filters/Modalidades/Lesson.md',
        'Filters/Modalidades/Teste.md', 'Filters/Modalidades/Lacunas.md',
        'Filters/Modalidades/Reading.md', 'Filters/HTML/HTML_Lesson.md'];
    const achados = [];
    for (const f of alvos) {
        if (!fs.existsSync(path.join(ROOT, f))) continue;
        const src = R(f);
        if (/4[- ][Cc]amadas|4[- ]LAYER|4 layers/.test(src)) achados.push(`${f}: fala em 4 camadas (o padrão é 3)`);
        if (/AS 5 SEÇÕES DO TESTE/.test(src)) achados.push(`${f}: fala em 5 seções do Teste (são 6)`);
    }
    if (achados.length) fail('contradições entre specs', achados.join(' · '));
    else ok('contradições entre specs', 'camadas e seções consistentes em todos os arquivos');
}

function checarProgress() {
    if (!fs.existsSync(path.join(ROOT, 'Progress.md'))) return fail('Progress.md', 'ausente — o sistema perde a memória entre sessões');
    const consumidores = ['Filters/Modalidades/Teste.md', 'Filters/Modalidades/Lacunas.md',
        'Filters/Modalidades/Ditado.md', 'Filters/Modalidades/Reading.md', 'Filters/Modalidades/Lesson.md'];
    const semRef = consumidores.filter((f) => fs.existsSync(path.join(ROOT, f)) && !R(f).includes('Progress.md'));
    if (semRef.length) fail('modalidades que ignoram Progress.md', semRef.join(' · '));
    else ok('Progress.md', `presente e referenciado por ${consumidores.length} modalidades`);
}

// ── execução ─────────────────────────────────────────────────
function main() {
    const quiet = process.argv.includes('--quiet');
    const d = carregar();
    checarCobertura(d);
    checarEnsinabilidadeKanji(d);
    checarTabela(d);
    checarTaxonomia();
    checarCaminhos();
    checarComandos();
    checarContradicoes();
    checarProgress();

    if (!quiet) {
        console.log('\n\x1b[1mAUDITORIA DO CURRÍCULO\x1b[0m\n');
        oks.forEach((o) => console.log(`  \x1b[32m✓\x1b[0m ${o.t} — ${o.d}`));
    }
    if (avisos.length) {
        console.log('');
        avisos.forEach((a) => console.log(`  \x1b[33m⚠\x1b[0m ${a.t} — ${a.d}`));
    }
    if (falhas.length) {
        console.log('');
        falhas.forEach((f) => console.log(`  \x1b[31m✗\x1b[0m ${f.t} — ${f.d}`));
    }
    console.log(`\n  ${oks.length} ok · ${avisos.length} aviso(s) · ${falhas.length} falha(s)\n`);
    process.exit(falhas.length ? 1 : 0);
}

if (require.main === module) main();
module.exports = { carregar };
