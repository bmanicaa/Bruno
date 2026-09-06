/**
 * build_anki.js — Converte os TSVs de vocabulário do formato legado (2 campos,
 * notetype "Básico") para o formato v2 (notetype "N5 Vocab"), que suporta:
 *
 *   - Campo `Leitura` em kana puro → habilita o TTS nativo do Anki
 *     ({{tts ja_JP:Leitura}}), sem arquivos de áudio e sem API externa.
 *   - Campo `Exemplo` → frase de contexto (obrigatório da Aula 4 em diante).
 *   - Tags hierárquicas (`aula::01`, `fase::1`, `tipo::vocab`) → tornam possível
 *     o estudo filtrado que o Template B promete ("revise os itens ⚠️/❌").
 *   - Um segundo cartão de PRODUÇÃO (PT → JP), direção que o deck legado
 *     nunca treinava.
 *
 * Uso:
 *   node scripts/build_anki.js            # converte todos os Anki/N5_L*_Anki.tsv
 *   node scripts/build_anki.js --check    # só relata, não escreve
 */

const fs = require('fs');
const path = require('path');
const { EXEMPLOS } = require('./exemplos_vocab.js');

const ANKI_DIR = path.join(__dirname, '../Anki');

function faseDaAula(n) {
    if (n <= 5) return 1;
    if (n <= 9) return 2;
    if (n <= 13) return 3;
    if (n <= 18) return 4;
    if (n <= 26) return 5;
    return 6;
}

/** Extrai a leitura em kana de uma entrada. */
function extrairLeitura(frente, verso) {
    // 1) Palavra com ruby: concatena as leituras <rt>, preservando o kana fora do ruby.
    if (/<ruby>/.test(frente)) {
        const kana = frente
            .replace(/<ruby>([\s\S]*?)<rt>([\s\S]*?)<\/rt><\/ruby>/g, '$2')
            .replace(/<[^>]+>/g, '')
            .trim();
        if (kana) return kana;
    }
    // 2) Kana puro na frente.
    if (/^[぀-ヿー]+$/.test(frente.trim())) return frente.trim();
    // 3) Fallback: prefixo kana do verso ("くに - país" / "ちち — Pai").
    const m = verso.match(/^([぀-ヿー\s/]+?)\s*[-—]\s*/);
    return m ? m[1].trim() : '';
}

/** Remove o prefixo de leitura do verso — agora ele vive no campo `Leitura`. */
function limparSignificado(verso) {
    return verso.replace(/^[぀-ヿー\s/]+\s*[-—]\s*/, '').trim();
}

function converter(arquivo, check) {
    const nome = path.basename(arquivo);
    const aula = parseInt(nome.match(/N5_L(\d+)/)[1], 10);
    const linhas = fs.readFileSync(arquivo, 'utf8').split('\n');
    const corpo = linhas.filter((l) => l.trim() && !l.startsWith('#'));

    const vistos = new Set();
    const saida = [];
    const dups = [];
    const semExemplo = [];

    for (const linha of corpo) {
        const [frente, verso = ''] = linha.split('\t');
        if (!frente) continue;
        // Deduplica pela PALAVRA-BASE (sem ruby): 四[し] e 四[よん] são o mesmo
        // item lexical, e o Anki não os detectaria como duplicata porque compara
        // o campo bruto, no qual as leituras diferem.
        const chave = frente.replace(/<rt>[\s\S]*?<\/rt>/g, '').replace(/<[^>]+>/g, '').trim();
        if (vistos.has(chave)) { dups.push(chave); continue; }
        vistos.add(chave);

        const leitura = extrairLeitura(frente, verso);
        const significado = limparSignificado(verso);
        const exemplo = EXEMPLOS[chave] || '';
        if (!exemplo) semExemplo.push(chave);
        const tags = `aula::${String(aula).padStart(2, '0')} fase::${faseDaAula(aula)} tipo::vocab`;
        // Palavra | Significado | Leitura | Exemplo | Tags
        saida.push([frente.trim(), significado, leitura, exemplo, tags].join('\t'));
    }

    const cabecalho = [
        '#separator:tab',
        '#html:true',
        '#notetype:N5 Vocab',
        `#deck:Japonês::N5::Vocabulário`,
        '#tags column:5',
        '#columns:Palavra\tSignificado\tLeitura\tExemplo\tTags',
    ].join('\n');

    const conteudo = cabecalho + '\n' + saida.join('\n') + '\n';
    console.log(
        `${nome}: ${saida.length} cards` +
        (dups.length ? `  ⚠️ ${dups.length} duplicata(s) removida(s): ${[...new Set(dups)].join(', ')}` : '')
    );
    if (semExemplo.length) {
        console.log(`   ⚠️ ${semExemplo.length} sem frase de exemplo (obrigatória da Aula 4 em diante — ver scripts/exemplos_vocab.js):`);
        console.log('      ' + semExemplo.join(', '));
    }
    const semLeitura = saida.filter((l) => !l.split('\t')[2]);
    if (semLeitura.length) {
        console.log(`   ⚠️ ${semLeitura.length} sem leitura (TTS não funcionará nesses):`);
        semLeitura.forEach((l) => console.log('      ' + l.split('\t')[0].replace(/<[^>]+>/g, '')));
    }
    if (!check) fs.writeFileSync(arquivo, conteudo, 'utf8');
    return saida.length;
}

function main() {
    const check = process.argv.includes('--check');
    const arquivos = fs
        .readdirSync(ANKI_DIR)
        .filter((f) => /^N5_L\d+_Anki\.tsv$/.test(f))
        .sort()
        .map((f) => path.join(ANKI_DIR, f));
    if (!arquivos.length) { console.error('nenhum TSV de vocabulário encontrado em Anki/'); process.exit(1); }
    let total = 0;
    for (const a of arquivos) total += converter(a, check);
    console.log(`\n${check ? '[--check] ' : ''}Total: ${total} cards de vocabulário em ${arquivos.length} arquivo(s).`);
}

if (require.main === module) main();
module.exports = { extrairLeitura, limparSignificado, faseDaAula };
