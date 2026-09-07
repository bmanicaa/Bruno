/**
 * build_epub.js — Converte a aula HTML gerada num EPUB 3 otimizado para
 * e-reader de tinta eletrônica (Kindle Paperwhite), preservando o furigana.
 *
 * POR QUE EPUB (e não MOBI/AZW3/PDF):
 *   - O Send to Kindle (e-mail @kindle.com, app desktop ou web) aceita EPUB e
 *     converte no servidor para KFX. A Amazon aposentou o MOBI como formato de
 *     envio; AZW3 só entra por USB e não é gerável sem ferramenta proprietária.
 *   - EPUB 3 é XHTML: `<ruby>/<rt>` são NATIVOS. O furigana sobrevive à
 *     conversão e aparece sobre o kanji, que é exatamente o recurso que a versão
 *     HTML já entrega no navegador (Regra 11 do JLPTN5.md).
 *   - PDF em tela de 6" exige zoom e pan — inutilizável para estudo.
 *   - EPUB é um ZIP de XHTML: dá para gerar com `zlib` do próprio Node, sem
 *     nenhuma dependência externa, como todo o resto de `scripts/`.
 *
 * O QUE A CONVERSÃO ADAPTA (a aula HTML foi desenhada para navegador):
 *   1. Remove `<script>` e os botões de tema/furigana — o Kindle não roda JS.
 *   2. Achata as variáveis CSS (`var(--accent-blue)`) em cores literais: o
 *      renderizador do Kindle não implementa custom properties, e um `var()`
 *      não resolvido apaga a declaração inteira.
 *   3. Troca a paleta AMOLED por uma paleta de alto contraste para e-ink.
 *   4. Quebra o documento em capítulos (um XHTML por `<section>`), o que dá
 *      sumário navegável e virada de página sã num arquivo de 6".
 *   5. Converte as tabelas de 3 colunas em blocos empilhados — uma tabela de 3
 *      colunas numa tela de 6" fica ilegível (`--tabelas tabela` desativa).
 *   6. Marca o texto japonês com `lang="ja"` e dá entrelinha folgada ao ruby,
 *      senão o furigana é cortado pela linha de cima.
 *   7. Adiciona `<rp>` como degradação elegante em leitor sem suporte a ruby.
 *
 * O EPUB gerado passa pelo MESMO validador dos demais artefatos
 * (`scripts/validate_artifact.js`): se a conversão comer um furigana, a
 * geração falha em vez de entregar um livro silenciosamente degradado.
 *
 * Uso:
 *   node scripts/build_epub.js <arquivo.html> [-o saida.epub]
 *   node scripts/build_epub.js N5_L4.html --upload            # sobe ao Drive
 *   node scripts/build_epub.js N5_L4.html --titulo "..." --autor "..."
 *   node scripts/build_epub.js N5_P3_Reading.html --tabelas tabela
 *
 * Flags:
 *   -o, --saida <arq>   caminho do .epub (padrão: mesmo nome do HTML)
 *   --titulo <txt>      título do livro (padrão: <title> do HTML)
 *   --autor <txt>       autor/coleção (padrão: "Curso JLPT N5")
 *   --idioma <tag>      dc:language principal (padrão: pt-BR — ver nota abaixo)
 *   --aula N            nº da aula para o Vocabulary Gate (padrão: do nome)
 *   --mode M            lesson|reading (padrão: inferido do nome)
 *   --tabelas <modo>    blocos (padrão) | tabela
 *   --upload            envia o .epub ao Google Drive após gerar
 *   --nome-drive <n>    nome do arquivo no Drive (padrão: basename do .epub)
 *
 * NOTA SOBRE `--idioma`: o padrão é `pt-BR` porque a aula é escrita em
 * português; o japonês é marcado item a item com `lang="ja"`, que é a forma
 * semanticamente correta e a que orienta a escolha de fonte. Se num Kindle
 * específico o furigana não aparecer, regere com `--idioma ja` — algumas
 * versões de firmware só ligam o motor de ruby em livro declarado como japonês.
 */

const fs = require('fs');
const path = require('path');
const zlib = require('zlib');
const crypto = require('crypto');

const { validateArtifact, detectMode, detectLesson } = require('./validate_artifact.js');

// ─────────────────────────────────────────────────────────────
// Paleta e-ink: substitui as custom properties do CSS master.
// Tons escuros e saturados — legíveis como cinza em tinta eletrônica
// (Paperwhite) e ainda coloridos num Colorsoft ou no app.
// ─────────────────────────────────────────────────────────────
const PALETA_EINK = {
    'bg-main': '#ffffff',
    'bg-card': '#ffffff',
    'bg-card-subtle': '#f2f2f2',
    'border-color': '#8a8a8a',
    'border-light': '#5a5a5a',
    'text-main': '#000000',
    'text-muted': '#3d3d3d',
    'text-dim': '#4f4f4f',
    'accent-blue': '#00407a',
    'accent-blue-bg': '#eef2f6',
    'accent-green': '#0b5227',
    'accent-green-bg': '#eef4ef',
    'accent-yellow': '#6b3d00',
    'accent-yellow-bg': '#f6f2ea',
    'accent-red': '#7d0000',
    'accent-purple': '#3f1a6b',
    'accent-red-bg': '#f7eeee',
    'accent-purple-bg': '#f1eef7',
};

const VAZIOS = new Set(['area', 'base', 'br', 'col', 'embed', 'hr', 'img',
    'input', 'link', 'meta', 'param', 'source', 'track', 'wbr']);

const BOOLEANOS = /\s(hidden|checked|disabled|selected|readonly|multiple|autofocus|controls|loop|muted|async|defer|novalidate|required)(?=[\s>])/gi;

// Entidades nomeadas do HTML que o XHTML não predefine (só amp/lt/gt/quot/apos
// são universais). Tudo o mais vira referência numérica.
const ENTIDADES = {
    nbsp: 160, iexcl: 161, cent: 162, pound: 163, curren: 164, yen: 165,
    sect: 167, copy: 169, laquo: 171, not: 172, shy: 173, reg: 174, deg: 176,
    plusmn: 177, sup2: 178, sup3: 179, micro: 181, para: 182, middot: 183,
    raquo: 187, frac14: 188, frac12: 189, frac34: 190, iquest: 191,
    Aacute: 193, Acirc: 194, Atilde: 195, Ccedil: 199, Eacute: 201, Ecirc: 202,
    Iacute: 205, Oacute: 211, Ocirc: 212, Otilde: 213, Uacute: 218, Uuml: 220,
    aacute: 225, acirc: 226, atilde: 227, auml: 228, ccedil: 231, eacute: 233,
    ecirc: 234, iacute: 237, ntilde: 241, oacute: 243, ocirc: 244, otilde: 245,
    ouml: 246, uacute: 250, ucirc: 251, uuml: 252, times: 215, divide: 247,
    ndash: 8211, mdash: 8212, lsquo: 8216, rsquo: 8217, sbquo: 8218,
    ldquo: 8220, rdquo: 8221, bdquo: 8222, dagger: 8224, bull: 8226,
    hellip: 8230, permil: 8240, prime: 8242, Prime: 8243, euro: 8364,
    trade: 8482, larr: 8592, uarr: 8593, rarr: 8594, darr: 8595, harr: 8596,
    infin: 8734, ne: 8800, le: 8804, ge: 8805, loz: 9674, spades: 9824,
    hearts: 9829, diams: 9830, ensp: 8194, emsp: 8195, thinsp: 8201,
};

// ─────────────────────────────────────────────────────────────
// ZIP mínimo (EPUB = OCF = ZIP). Sem dependências: zlib + CRC-32.
// Data fixa → build reprodutível: o mesmo HTML gera o mesmo .epub.
// ─────────────────────────────────────────────────────────────
const TABELA_CRC = (() => {
    const t = new Int32Array(256);
    for (let n = 0; n < 256; n++) {
        let c = n;
        for (let k = 0; k < 8; k++) c = c & 1 ? 0xedb88320 ^ (c >>> 1) : c >>> 1;
        t[n] = c;
    }
    return t;
})();

function crc32(buf) {
    let c = -1;
    for (let i = 0; i < buf.length; i++) c = TABELA_CRC[(c ^ buf[i]) & 0xff] ^ (c >>> 8);
    return (c ^ -1) >>> 0;
}

const DATA_ZIP = ((2020 - 1980) << 9) | (1 << 5) | 1; // 2020-01-01
const HORA_ZIP = 0;

/** entradas: [{ nome, dados: Buffer, comprimir: boolean }] */
function zipar(entradas) {
    const locais = [];
    const central = [];
    let offset = 0;

    for (const { nome, dados, comprimir } of entradas) {
        const nomeBuf = Buffer.from(nome, 'utf8');
        // A OCF exige o cabeçalho mais simples possível no `mimetype`.
        const flags = nome === 'mimetype' ? 0 : 0x0800;
        const bruto = Buffer.isBuffer(dados) ? dados : Buffer.from(dados, 'utf8');
        const corpo = comprimir ? zlib.deflateRawSync(bruto, { level: 9 }) : bruto;
        const metodo = comprimir ? 8 : 0;
        const crc = crc32(bruto);

        const cab = Buffer.alloc(30);
        cab.writeUInt32LE(0x04034b50, 0);
        cab.writeUInt16LE(20, 4);       // versão necessária
        cab.writeUInt16LE(flags, 6);    // bit 11 = nomes em UTF-8
        cab.writeUInt16LE(metodo, 8);
        cab.writeUInt16LE(HORA_ZIP, 10);
        cab.writeUInt16LE(DATA_ZIP, 12);
        cab.writeUInt32LE(crc, 14);
        cab.writeUInt32LE(corpo.length, 18);
        cab.writeUInt32LE(bruto.length, 22);
        cab.writeUInt16LE(nomeBuf.length, 26);
        cab.writeUInt16LE(0, 28);
        locais.push(cab, nomeBuf, corpo);

        const dir = Buffer.alloc(46);
        dir.writeUInt32LE(0x02014b50, 0);
        dir.writeUInt16LE(20, 4);       // versão do criador
        dir.writeUInt16LE(20, 6);       // versão necessária
        dir.writeUInt16LE(flags, 8);
        dir.writeUInt16LE(metodo, 10);
        dir.writeUInt16LE(HORA_ZIP, 12);
        dir.writeUInt16LE(DATA_ZIP, 14);
        dir.writeUInt32LE(crc, 16);
        dir.writeUInt32LE(corpo.length, 20);
        dir.writeUInt32LE(bruto.length, 24);
        dir.writeUInt16LE(nomeBuf.length, 28);
        dir.writeUInt32LE(0, 38);       // atributos externos
        dir.writeUInt32LE(offset, 42);
        central.push(dir, nomeBuf);

        offset += 30 + nomeBuf.length + corpo.length;
    }

    const dirBuf = Buffer.concat(central);
    const fim = Buffer.alloc(22);
    fim.writeUInt32LE(0x06054b50, 0);
    fim.writeUInt16LE(entradas.length, 8);
    fim.writeUInt16LE(entradas.length, 10);
    fim.writeUInt32LE(dirBuf.length, 12);
    fim.writeUInt32LE(offset, 16);

    return Buffer.concat([...locais, dirBuf, fim]);
}

// ─────────────────────────────────────────────────────────────
// Transformações HTML → XHTML de e-reader
// ─────────────────────────────────────────────────────────────

/** `var(--accent-blue)` → `#00407a`. Sem isso o Kindle descarta a declaração. */
function achatarVariaveis(html) {
    return html.replace(/var\(\s*--([a-z0-9-]+)\s*(?:,\s*([^()]*?)\s*)?\)/gi, (todo, token, fallback) => {
        if (PALETA_EINK[token]) return PALETA_EINK[token];
        if (fallback) return fallback;
        return 'inherit';
    });
}

/** Remove tudo que depende de JS ou de tela: scripts, botões, comentários. */
function removerInterativos(html) {
    return html
        .replace(/<script[\s\S]*?<\/script>/gi, '')
        .replace(/<noscript[\s\S]*?<\/noscript>/gi, '')
        .replace(/<!--[\s\S]*?-->/g, '')
        // O <button> sai ANTES do contêiner: apagar o contêiner primeiro deixaria
        // um </div> órfão se ele tivesse qualquer filho aninhado.
        .replace(/<button[\s\S]*?<\/button>/gi, '')
        .replace(/\son[a-z]+\s*=\s*"[^"]*"/gi, '')
        .replace(/\son[a-z]+\s*=\s*'[^']*'/gi, '')
        // Restos vazios: o grupo de botões e o <div> que às vezes o embrulha.
        .replace(/<div class="control-btn-group"[^>]*>\s*<\/div>/gi, '')
        .replace(/<div>\s*<\/div>/g, '');
}

/** Entidade → caractere. Usado onde o texto vira dado (título, rótulo do sumário). */
function decodificarEntidades(texto) {
    return texto.replace(/&(#x[0-9a-fA-F]+|#\d+|[a-zA-Z][a-zA-Z0-9]*);/g, (todo, corpo) => {
        if (corpo[0] === '#') {
            const cod = corpo[1] === 'x' || corpo[1] === 'X'
                ? parseInt(corpo.slice(2), 16)
                : parseInt(corpo.slice(1), 10);
            return Number.isFinite(cod) ? String.fromCodePoint(cod) : todo;
        }
        const basicas = { amp: 38, lt: 60, gt: 62, quot: 34, apos: 39 };
        const cod = basicas[corpo] !== undefined ? basicas[corpo] : ENTIDADES[corpo];
        return cod !== undefined ? String.fromCodePoint(cod) : todo;
    });
}

/** Texto legível de um trecho de HTML: sem tags, sem furigana, sem entidades. */
function textoPuro(html) {
    return decodificarEntidades(
        html
            .replace(/<rt>[\s\S]*?<\/rt>/gi, '')
            .replace(/<[^>]+>/g, '')
    ).replace(/\s+/g, ' ').trim();
}

/**
 * Tabela de 3 colunas numa tela de 6" quebra em colunas de 2 caracteres.
 * Cada `<tr>` vira um bloco empilhado com o cabeçalho como rótulo.
 * Tabela sem `<thead>` ou com parsing duvidoso é deixada intacta.
 */
function tabelasParaBlocos(html) {
    return html.replace(/<table\b[^>]*>([\s\S]*?)<\/table>/gi, (original, corpo) => {
        if (/<table\b/i.test(corpo)) return original; // tabela aninhada: não mexe
        const rotulos = [...corpo.matchAll(/<th\b[^>]*>([\s\S]*?)<\/th>/gi)].map((m) => textoPuro(m[1]));
        const linhas = [...corpo.matchAll(/<tr\b[^>]*>([\s\S]*?)<\/tr>/gi)]
            .map((m) => [...m[1].matchAll(/<td\b[^>]*>([\s\S]*?)<\/td>/gi)].map((c) => c[1]))
            .filter((celulas) => celulas.length);
        if (!rotulos.length || !linhas.length) return original;

        const blocos = linhas.map((celulas) => {
            const campos = celulas.map((valor, i) => {
                // `textoPuro` devolve o rótulo já decodificado; ele volta para
                // dentro do HTML, então precisa ser reescapado.
                const rotulo = rotulos[i] ? `<span class="registro-rotulo">${esc(rotulos[i])}</span>` : '';
                const classe = i === 0 ? 'registro-campo registro-chave' : 'registro-campo';
                return `<div class="${classe}">${rotulo}<span class="registro-valor">${valor.trim()}</span></div>`;
            }).join('\n        ');
            return `      <div class="registro">\n        ${campos}\n      </div>`;
        }).join('\n');
        return `<div class="registro-lista">\n${blocos}\n    </div>`;
    });
}

/**
 * Marca o japonês com `lang="ja"`: orienta a escolha de fonte CJK do leitor e
 * evita que o motor de hifenização portuguesa encoste no texto vertical do ruby.
 */
function marcarIdiomaJapones(html) {
    const COM_JAPONES = /\b(ja-text|layer-1-ja|kanji-glyph|kanji-big-box)\b/;
    return html
        .replace(/<ruby(\s[^>]*)?>/gi, (todo, attrs) =>
            /lang=/i.test(attrs || '') ? todo : `<ruby${attrs || ''} lang="ja" xml:lang="ja">`)
        .replace(/<([a-z][a-z0-9]*)((?:\s[^>]*)?class="([^"]*)"(?:[^>]*)?)>/gi, (todo, tag, attrs, classes) => {
            if (!COM_JAPONES.test(classes) || /lang=/i.test(attrs)) return todo;
            return `<${tag}${attrs} lang="ja" xml:lang="ja">`;
        });
}

/**
 * `<rp>` = degradação elegante: leitor sem suporte a ruby imprime
 * 私(わたし) em vez de 私わたし. Leitor com suporte ignora os `<rp>`.
 */
function rubyComParenteses(html) {
    return html.replace(/<rt>([\s\S]*?)<\/rt>/gi, '<rp>(</rp><rt>$1</rt><rp>)</rp>');
}

/** HTML solto → XHTML bem-formado. */
function paraXhtml(html) {
    let s = html;
    // 1) entidades nomeadas → numéricas (o XHTML só predefine as cinco do XML)
    s = s.replace(/&([a-zA-Z][a-zA-Z0-9]*);/g, (todo, nome) => {
        if (['amp', 'lt', 'gt', 'quot', 'apos'].includes(nome)) return todo;
        if (ENTIDADES[nome] !== undefined) return `&#${ENTIDADES[nome]};`;
        return `&amp;${nome};`; // desconhecida: vira texto literal, nunca XML inválido
    });
    // 2) `&` solto → `&amp;`
    s = s.replace(/&(?!(?:amp|lt|gt|quot|apos|#\d+|#x[0-9a-fA-F]+);)/g, '&amp;');
    // 3) atributos booleanos ganham valor
    s = s.replace(BOOLEANOS, (todo, attr) => ` ${attr.toLowerCase()}="${attr.toLowerCase()}"`);
    // 4) elementos vazios se auto-fecham
    s = s.replace(/<([a-z][a-z0-9]*)\b([^>]*?)\s*\/?>/gi, (todo, tag, attrs) => {
        if (!VAZIOS.has(tag.toLowerCase())) return todo;
        return `<${tag.toLowerCase()}${attrs.replace(/\/$/, '')} />`;
    });
    return s;
}

/**
 * Checagem de boa-formação sem dependência: pilha de tags + atributos com aspas.
 * Um XHTML malformado só falharia no aparelho, depois do upload — aqui falha na
 * geração.
 */
function verificarXml(xml, rotulo) {
    const erros = [];
    const limpo = xml
        .replace(/<\?[\s\S]*?\?>/g, '')
        .replace(/<!DOCTYPE[^>]*>/gi, '')
        .replace(/<!--[\s\S]*?-->/g, '');
    const pilha = [];
    const re = /<(\/?)([a-zA-Z][a-zA-Z0-9:._-]*)((?:"[^"]*"|'[^']*'|[^>"'])*?)(\/?)>/g;
    let m;
    let ultimo = 0;
    while ((m = re.exec(limpo)) !== null) {
        if (limpo.slice(ultimo, m.index).includes('<')) {
            erros.push(`"<" solto perto de …${limpo.slice(m.index - 40, m.index + 20).replace(/\s+/g, ' ')}…`);
        }
        ultimo = m.index + m[0].length;
        const [, fecha, tag, attrs, auto] = m;
        if (/=(?!\s*["'])/.test(attrs)) erros.push(`atributo sem aspas em <${tag}>`);
        if (auto) continue;
        if (fecha) {
            const aberto = pilha.pop();
            if (aberto !== tag) erros.push(`</${tag}> fecha <${aberto || 'nada'}>`);
        } else {
            pilha.push(tag);
        }
    }
    if (pilha.length) erros.push(`tags não fechadas: ${pilha.join(', ')}`);
    if (erros.length) {
        throw new Error(`XML malformado em ${rotulo}:\n  - ${erros.slice(0, 8).join('\n  - ')}`);
    }
}

/**
 * Quebra o `<body>` nos seus elementos de topo — cada `<section>` vira um
 * capítulo. Texto solto entre elementos gruda no capítulo anterior.
 */
function dividirCapitulos(body) {
    const partes = [];
    const re = /<(\/?)([a-zA-Z][a-zA-Z0-9]*)\b((?:"[^"]*"|'[^']*'|[^>"'])*?)(\/?)>/g;
    let profundidade = 0;
    let inicio = null;
    let fimAnterior = 0;
    let m;
    while ((m = re.exec(body)) !== null) {
        const [, fecha, tag, , auto] = m;
        const vazio = auto === '/' || VAZIOS.has(tag.toLowerCase());
        if (vazio) continue;
        if (!fecha) {
            if (profundidade === 0) {
                const solto = body.slice(fimAnterior, m.index).trim();
                if (solto && partes.length) partes[partes.length - 1].html += `\n${solto}`;
                inicio = m.index;
            }
            profundidade++;
        } else {
            profundidade = Math.max(0, profundidade - 1);
            if (profundidade === 0 && inicio !== null) {
                partes.push({ tag: tag.toLowerCase(), html: body.slice(inicio, m.index + m[0].length) });
                inicio = null;
                fimAnterior = m.index + m[0].length;
            }
        }
    }
    const resto = body.slice(fimAnterior).trim();
    if (resto && partes.length) partes[partes.length - 1].html += `\n${resto}`;
    return partes;
}

// Seções sem heading próprio (o corpo do Reading, por exemplo) ainda precisam
// de um rótulo no sumário — "Seção 2" não ajuda ninguém a navegar.
const TITULOS_POR_CLASSE = [
    [/\bstory-card\b/, '📖 Texto'],
    [/\bquestions-card\b/, '❓ Compreensão'],
    [/\bheader-card\b/, 'Abertura'],
];

/** Título do capítulo: o primeiro h1/h2/h3; senão, a classe do bloco. */
function tituloDoCapitulo(html, indice) {
    const m = html.match(/<h([123])\b[^>]*>([\s\S]*?)<\/h\1>/i);
    const bruto = m ? textoPuro(m[2]) : '';
    if (bruto) return bruto;
    const abertura = (html.match(/^<[^>]*>/) || [''])[0];
    for (const [padrao, titulo] of TITULOS_POR_CLASSE) if (padrao.test(abertura)) return titulo;
    return `Seção ${indice}`;
}

// ─────────────────────────────────────────────────────────────
// CSS de tinta eletrônica (achatado — o Kindle não tem custom properties,
// flexbox confiável, box-shadow nem media queries)
// ─────────────────────────────────────────────────────────────
function folhaDeEstilo() {
    const p = PALETA_EINK;
    return `@charset "utf-8";

/* Aula JLPT N5 — folha de estilo para tinta eletrônica.
   Gerada por scripts/build_epub.js. Sem custom properties, sem flexbox,
   sem box-shadow: nada disso é confiável no renderizador do Kindle. */

body {
  margin: 0 0.35em;
  padding: 0;
  color: ${p['text-main']};
  background-color: ${p['bg-main']};
  line-height: 1.5;
  text-align: left;
  widows: 2;
  orphans: 2;
}

/* --- FURIGANA ---------------------------------------------------------
   O ruby precisa de entrelinha folgada: sem isso o <rt> encosta na linha
   de cima e o aparelho corta a leitura. */
ruby { ruby-position: over; -webkit-ruby-position: before; }
rt {
  font-size: 50%;
  ruby-align: center;
  text-align: center;
  color: ${p['text-muted']};
}
:lang(ja), .ja-text, .layer-1-ja { line-height: 2.2; }

/* --- CABEÇALHO --------------------------------------------------------- */
h1 { font-size: 1.45em; line-height: 1.3; margin: 0 0 0.5em 0; page-break-after: avoid; }
h2 { font-size: 1.2em; line-height: 1.3; margin: 0 0 0.5em 0; page-break-after: avoid; }
h3 { font-size: 1.05em; line-height: 1.3; margin: 1em 0 0.4em 0; page-break-after: avoid; }
p { margin: 0 0 0.7em 0; }

.header-card {
  border: 1px solid ${p['border-color']};
  border-radius: 6px;
  padding: 0.8em;
  margin-bottom: 1.2em;
}
.header-top-row { margin-bottom: 0.5em; }
.meta-badges { margin-bottom: 0.4em; }
.badge {
  display: inline-block;
  border: 1px solid ${p['border-color']};
  border-radius: 10px;
  padding: 0.05em 0.5em;
  margin: 0 0.3em 0.3em 0;
  font-size: 0.75em;
}
.badge-blue, .badge-g1 { color: ${p['accent-blue']}; border-color: ${p['accent-blue']}; }
.badge-green, .badge-g2 { color: ${p['accent-green']}; border-color: ${p['accent-green']}; }
.badge-yellow, .badge-g3 { color: ${p['accent-yellow']}; border-color: ${p['accent-yellow']}; }
.badge-purple { color: ${p['accent-purple']}; border-color: ${p['accent-purple']}; }
.header-objective {
  border-top: 1px solid ${p['border-color']};
  padding-top: 0.5em;
  margin-top: 0.5em;
  font-size: 0.92em;
}

.section-title {
  border-bottom: 2px solid ${p['text-main']};
  padding-bottom: 0.2em;
  margin-bottom: 0.7em;
}
.subsection-title { color: ${p['accent-blue']}; }

/* --- CHAVES DE LEITURA (KANJI) ----------------------------------------- */
.kanji-card {
  border: 1px solid ${p['border-color']};
  border-radius: 6px;
  padding: 0.8em;
  margin-bottom: 0.9em;
  page-break-inside: avoid;
}
.kanji-big-box {
  text-align: center;
  border-bottom: 1px solid ${p['border-color']};
  padding-bottom: 0.4em;
  margin-bottom: 0.5em;
}
.kanji-glyph { font-size: 2.6em; line-height: 1.9; }
.kanji-details { font-size: 0.95em; }
.kanji-details > div { margin-bottom: 0.35em; }
.kanji-composition { margin: 0.3em 0 0 0.6em; }
.kanji-composition-item { margin-bottom: 0.3em; line-height: 2.0; }
.composition-arrow { color: ${p['text-dim']}; }
.composition-result { font-weight: bold; }
.lesson-tag, .reading-tag, .tag-radical, .chip-translation {
  display: inline-block;
  border: 1px solid ${p['border-color']};
  border-radius: 4px;
  padding: 0 0.35em;
  font-size: 0.72em;
  color: ${p['text-muted']};
}
.kanji-mnemonic, .kanji-future-note {
  border-left: 3px solid ${p['accent-yellow']};
  background-color: ${p['bg-card-subtle']};
  padding: 0.4em 0.6em;
  margin-top: 0.5em;
  font-size: 0.9em;
}

/* --- VOCABULÁRIO: tabelas e blocos ------------------------------------- */
table {
  width: 100%;
  border-collapse: collapse;
  margin-bottom: 1em;
  font-size: 0.9em;
  table-layout: fixed;
  word-wrap: break-word;
}
th, td {
  border: 1px solid ${p['border-color']};
  padding: 0.3em 0.4em;
  text-align: left;
  vertical-align: top;
}
th { background-color: ${p['bg-card-subtle']}; font-size: 0.85em; }

.registro-lista { margin-bottom: 1em; }
.registro {
  border: 1px solid ${p['border-color']};
  border-radius: 5px;
  padding: 0.5em 0.6em;
  margin-bottom: 0.6em;
  page-break-inside: avoid;
}
.registro-campo { margin-bottom: 0.25em; font-size: 0.92em; }
.registro-chave { font-size: 1.25em; line-height: 2.2; border-bottom: 1px dotted ${p['border-color']}; padding-bottom: 0.3em; margin-bottom: 0.45em; }
.registro-rotulo {
  display: block;
  font-size: 0.68em;
  text-transform: uppercase;
  letter-spacing: 0.04em;
  color: ${p['text-dim']};
}
.registro-valor { display: block; }

/* --- GRAMÁTICA E EXEMPLOS ---------------------------------------------- */
.grammar-block { margin-bottom: 1.2em; }
.formula-box {
  border: 1px dashed ${p['accent-blue']};
  background-color: ${p['accent-blue-bg']};
  border-radius: 5px;
  padding: 0.5em 0.6em;
  margin: 0.5em 0;
  text-align: center;
  font-weight: bold;
  line-height: 2.0;
}
.mental-model {
  border-left: 3px solid ${p['accent-purple']};
  background-color: ${p['bg-card-subtle']};
  padding: 0.5em 0.7em;
  margin: 0.6em 0;
  font-size: 0.93em;
}
.example-card, .exercise-card, .recall-row {
  border: 1px solid ${p['border-color']};
  border-radius: 5px;
  padding: 0.55em 0.7em;
  margin-bottom: 0.7em;
  page-break-inside: avoid;
}
.layer-1-ja { font-size: 1.1em; line-height: 2.2; margin-bottom: 0.3em; }
.layer-3-pt { color: ${p['text-muted']}; font-style: italic; margin-bottom: 0.25em; }
.layer-4-breakdown {
  font-size: 0.82em;
  color: ${p['text-dim']};
  border-top: 1px dotted ${p['border-color']};
  padding-top: 0.25em;
}
.exercise-number { font-weight: bold; color: ${p['accent-blue']}; }

/* --- DIÁLOGO ----------------------------------------------------------- */
.dialogue-container { margin: 0.6em 0; }
.chat-bubble {
  border: 1px solid ${p['border-color']};
  border-radius: 8px;
  padding: 0.5em 0.7em;
  margin-bottom: 0.6em;
  page-break-inside: avoid;
}
.chat-left { border-left: 4px solid ${p['accent-blue']}; margin-right: 8%; }
.chat-right { border-right: 4px solid ${p['accent-green']}; margin-left: 8%; }
.chat-speaker { font-size: 0.75em; text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 0.25em; }
.speaker-a { color: ${p['accent-blue']}; }
.speaker-b { color: ${p['accent-green']}; }

/* --- CALLOUTS ---------------------------------------------------------- */
.callout-box, .callout-note, .callout-tip, .callout-warning, .callout-pitfall, .gabarito-box {
  border: 1px solid ${p['border-color']};
  border-left-width: 4px;
  border-radius: 5px;
  padding: 0.6em 0.7em;
  margin: 0.7em 0;
  page-break-inside: avoid;
}
.callout-note { border-left-color: ${p['accent-blue']}; background-color: ${p['accent-blue-bg']}; }
.callout-tip { border-left-color: ${p['accent-green']}; background-color: ${p['accent-green-bg']}; }
.callout-warning { border-left-color: ${p['accent-yellow']}; background-color: ${p['accent-yellow-bg']}; }
.callout-pitfall { border-left-color: ${p['accent-red']}; background-color: ${p['accent-red-bg']}; }
.pitfall-title { font-weight: bold; color: ${p['accent-red']}; margin-bottom: 0.3em; }
.pitfall-item { margin-bottom: 0.25em; }
.gabarito-box { border-left-color: ${p['accent-green']}; background-color: ${p['bg-card-subtle']}; }
.gabarito-content { font-size: 0.93em; }

/* --- READING ----------------------------------------------------------- */
.story-card {
  border: 1px solid ${p['border-color']};
  border-radius: 6px;
  padding: 0.8em;
  margin-bottom: 1.2em;
}
.story-card p { line-height: 2.3; margin-bottom: 1em; }
.questions-card { margin-bottom: 1em; }
.questions-list li { margin-bottom: 0.6em; }

/* --- CAPA -------------------------------------------------------------- */
.capa { text-align: center; margin-top: 22%; }
.capa-titulo { font-size: 1.8em; line-height: 1.25; margin-bottom: 0.6em; }
.capa-sub { font-size: 1em; color: ${p['text-muted']}; margin-bottom: 0.3em; }
.capa-regua { border: 0; border-top: 2px solid ${p['text-main']}; width: 40%; margin: 1.2em auto; }
`;
}

// ─────────────────────────────────────────────────────────────
// Montagem do pacote EPUB 3
// ─────────────────────────────────────────────────────────────
const esc = (s) => String(s)
    .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;').replace(/'/g, '&apos;');

function documentoXhtml({ titulo, idioma, corpo, classeBody }) {
    return `<?xml version="1.0" encoding="utf-8"?>
<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml" xmlns:epub="http://www.idpf.org/2007/ops" lang="${idioma}" xml:lang="${idioma}">
<head>
  <meta charset="utf-8" />
  <title>${esc(titulo)}</title>
  <link rel="stylesheet" type="text/css" href="style.css" />
</head>
<body${classeBody ? ` class="${classeBody}"` : ''}>
${corpo}
</body>
</html>
`;
}

/** UUID estável: regerar a mesma aula atualiza o livro em vez de duplicá-lo. */
function identificador(semente) {
    const h = crypto.createHash('sha1').update(`jlptn5-epub:${semente}`).digest('hex');
    return `urn:uuid:${h.slice(0, 8)}-${h.slice(8, 12)}-5${h.slice(13, 16)}-a${h.slice(17, 20)}-${h.slice(20, 32)}`;
}

function montarOpf({ titulo, autor, idioma, uuid, modificado, capitulos }) {
    const itens = capitulos
        .map((c) => `    <item id="${c.id}" href="${c.arquivo}" media-type="application/xhtml+xml" />`)
        .join('\n');
    const spine = capitulos.map((c) => `    <itemref idref="${c.id}" />`).join('\n');
    return `<?xml version="1.0" encoding="utf-8"?>
<package xmlns="http://www.idpf.org/2007/opf" version="3.0" unique-identifier="pub-id" xml:lang="${idioma}">
  <metadata xmlns:dc="http://purl.org/dc/elements/1.1/">
    <dc:identifier id="pub-id">${esc(uuid)}</dc:identifier>
    <dc:title>${esc(titulo)}</dc:title>
    <dc:creator>${esc(autor)}</dc:creator>
    <dc:language>${esc(idioma)}</dc:language>
    <dc:language>ja</dc:language>
    <dc:publisher>${esc(autor)}</dc:publisher>
    <meta property="dcterms:modified">${modificado}</meta>
    <meta property="rendition:layout">reflowable</meta>
  </metadata>
  <manifest>
    <item id="nav" href="nav.xhtml" media-type="application/xhtml+xml" properties="nav" />
    <item id="ncx" href="toc.ncx" media-type="application/x-dtbncx+xml" />
    <item id="css" href="style.css" media-type="text/css" />
${itens}
  </manifest>
  <spine toc="ncx">
${spine}
  </spine>
</package>
`;
}

function montarNav({ titulo, idioma, capitulos }) {
    const itens = capitulos
        .map((c) => `      <li><a href="${c.arquivo}">${esc(c.titulo)}</a></li>`)
        .join('\n');
    return `<?xml version="1.0" encoding="utf-8"?>
<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml" xmlns:epub="http://www.idpf.org/2007/ops" lang="${idioma}" xml:lang="${idioma}">
<head>
  <meta charset="utf-8" />
  <title>Sumário</title>
  <link rel="stylesheet" type="text/css" href="style.css" />
</head>
<body>
  <nav epub:type="toc" id="toc">
    <h1>Sumário</h1>
    <ol>
${itens}
    </ol>
  </nav>
  <nav epub:type="landmarks" hidden="hidden">
    <ol>
      <li><a epub:type="cover" href="${capitulos[0].arquivo}">Capa</a></li>
      <li><a epub:type="bodymatter" href="${(capitulos[1] || capitulos[0]).arquivo}">${esc(titulo)}</a></li>
    </ol>
  </nav>
</body>
</html>
`;
}

/** NCX: formalmente legado no EPUB 3, mas é o sumário que o Kindle usa. */
function montarNcx({ titulo, uuid, capitulos }) {
    const pontos = capitulos.map((c, i) => `    <navPoint id="np-${i + 1}" playOrder="${i + 1}">
      <navLabel><text>${esc(c.titulo)}</text></navLabel>
      <content src="${c.arquivo}" />
    </navPoint>`).join('\n');
    return `<?xml version="1.0" encoding="utf-8"?>
<ncx xmlns="http://www.daisy.org/z3986/2005/ncx/" version="2005-1">
  <head>
    <meta name="dtb:uid" content="${esc(uuid)}" />
    <meta name="dtb:depth" content="1" />
    <meta name="dtb:totalPageCount" content="0" />
    <meta name="dtb:maxPageNumber" content="0" />
  </head>
  <docTitle><text>${esc(titulo)}</text></docTitle>
  <navMap>
${pontos}
  </navMap>
</ncx>
`;
}

const CONTAINER_XML = `<?xml version="1.0" encoding="utf-8"?>
<container version="1.0" xmlns="urn:oasis:names:tc:opendocument:xmlns:container">
  <rootfiles>
    <rootfile full-path="OEBPS/content.opf" media-type="application/oebps-package+xml" />
  </rootfiles>
</container>
`;

// ─────────────────────────────────────────────────────────────
// Pipeline
// ─────────────────────────────────────────────────────────────
function construirEpub(htmlOrigem, opcoes = {}) {
    const modo = opcoes.mode || 'lesson';
    const aula = opcoes.lesson || null;
    const idioma = opcoes.idioma || 'pt-BR';
    const autor = opcoes.autor || 'Curso JLPT N5';
    const modificado = opcoes.modificado || new Date().toISOString().replace(/\.\d+Z$/, 'Z');

    const tituloHtml = (htmlOrigem.match(/<title>([\s\S]*?)<\/title>/i) || [, ''])[1].trim();
    const titulo = opcoes.titulo || textoPuro(tituloHtml) || 'Aula JLPT N5';

    const mBody = htmlOrigem.match(/<body[^>]*>([\s\S]*)<\/body>/i);
    if (!mBody) throw new Error('HTML de origem sem <body> — não é uma aula/reading gerada pelo curso.');

    let corpo = removerInterativos(mBody[1]);
    corpo = achatarVariaveis(corpo);
    if (opcoes.tabelas !== 'tabela') corpo = tabelasParaBlocos(corpo);
    corpo = marcarIdiomaJapones(corpo);

    // A validação de furigana roda ANTES dos <rp>: eles entrariam na base do
    // <ruby> e virariam falso positivo no Vocabulary Gate.
    const { errors, warnings } = validateArtifact(corpo, { mode: modo, lesson: aula });
    // Sai antes de montar o pacote: um erro de XML mais adiante mascararia a
    // causa real, que é o furigana perdido.
    if (errors.length) return { buffer: null, titulo, capitulos: [], errors, warnings, modo, aula };

    const partes = dividirCapitulos(corpo);
    if (!partes.length) throw new Error('Nenhum elemento de topo encontrado no <body>.');

    const capitulos = [{
        id: 'capa',
        arquivo: 'capa.xhtml',
        titulo: 'Capa',
        xhtml: documentoXhtml({
            titulo,
            idioma,
            classeBody: 'capa-body',
            corpo: `  <div class="capa">
    <div class="capa-titulo">${esc(titulo)}</div>
    <hr class="capa-regua" />
    <div class="capa-sub">${esc(autor)}</div>
    <div class="capa-sub">Furigana embutido · leitura em tinta eletrônica</div>
  </div>`,
        }),
    }];

    partes.forEach((parte, i) => {
        const n = String(i + 1).padStart(2, '0');
        const tituloCap = tituloDoCapitulo(parte.html, i + 1);
        const conteudo = paraXhtml(rubyComParenteses(parte.html));
        const xhtml = documentoXhtml({ titulo: tituloCap, idioma, corpo: conteudo });
        verificarXml(xhtml, `cap${n}.xhtml`);
        capitulos.push({ id: `cap${n}`, arquivo: `cap${n}.xhtml`, titulo: tituloCap, xhtml });
    });

    verificarXml(capitulos[0].xhtml, 'capa.xhtml');

    const uuid = identificador(opcoes.semente || titulo);
    const arquivos = [
        { nome: 'mimetype', dados: 'application/epub+zip', comprimir: false },
        { nome: 'META-INF/container.xml', dados: CONTAINER_XML, comprimir: true },
        { nome: 'OEBPS/content.opf', dados: montarOpf({ titulo, autor, idioma, uuid, modificado, capitulos }), comprimir: true },
        { nome: 'OEBPS/nav.xhtml', dados: montarNav({ titulo, idioma, capitulos }), comprimir: true },
        { nome: 'OEBPS/toc.ncx', dados: montarNcx({ titulo, uuid, capitulos }), comprimir: true },
        { nome: 'OEBPS/style.css', dados: folhaDeEstilo(), comprimir: true },
        ...capitulos.map((c) => ({ nome: `OEBPS/${c.arquivo}`, dados: c.xhtml, comprimir: true })),
    ];

    for (const a of arquivos) {
        if (a.nome.endsWith('.xml') || a.nome.endsWith('.opf') || a.nome.endsWith('.ncx')) {
            verificarXml(a.dados, a.nome);
        }
    }

    return { buffer: zipar(arquivos), titulo, capitulos, errors, warnings, modo, aula };
}

// ─────────────────────────────────────────────────────────────
// CLI
// ─────────────────────────────────────────────────────────────
async function main(argv) {
    const args = argv.slice(2);
    const flag = (nome, curto) => {
        const i = args.findIndex((a) => a === `--${nome}` || (curto && a === curto));
        return i >= 0 ? args[i + 1] : null;
    };
    const tem = (nome) => args.includes(`--${nome}`);
    // `--upload` não recebe valor: sem esta lista, `--upload aula.html` engoliria
    // o arquivo de entrada como se fosse o argumento da flag.
    const BOOLEANAS = new Set(['--upload']);
    const valores = new Set();
    args.forEach((a, i) => {
        if (BOOLEANAS.has(a)) return;
        if ((a.startsWith('--') || a === '-o') && args[i + 1] && !args[i + 1].startsWith('--')) valores.add(i + 1);
    });
    const posicionais = args.filter((a, i) => !a.startsWith('-') && !valores.has(i));

    const entrada = posicionais[0];
    if (!entrada) {
        console.error('uso: node scripts/build_epub.js <arquivo.html> [-o saida.epub] [--titulo T] ' +
            '[--autor A] [--idioma pt-BR|ja] [--aula N] [--mode lesson|reading] ' +
            '[--tabelas blocos|tabela] [--upload] [--nome-drive N]');
        process.exit(2);
    }
    if (!fs.existsSync(entrada)) {
        console.error(`✗ não encontrado: ${entrada}`);
        process.exit(2);
    }

    const saida = flag('saida', '-o') || entrada.replace(/\.html?$/i, '') + '.epub';
    const modo = flag('mode') || detectMode(entrada);
    const aula = flag('aula') ? parseInt(flag('aula'), 10) : detectLesson(entrada);
    const tabelas = flag('tabelas') || 'blocos';
    if (!['blocos', 'tabela'].includes(tabelas)) {
        console.error(`✗ --tabelas aceita "blocos" ou "tabela" (recebido: ${tabelas})`);
        process.exit(2);
    }

    const html = fs.readFileSync(entrada, 'utf8');
    const mtime = fs.statSync(entrada).mtime.toISOString().replace(/\.\d+Z$/, 'Z');

    let resultado;
    try {
        resultado = construirEpub(html, {
            mode: modo,
            lesson: aula,
            titulo: flag('titulo'),
            autor: flag('autor'),
            idioma: flag('idioma'),
            tabelas,
            modificado: mtime,
            semente: path.basename(entrada),
        });
    } catch (e) {
        console.error(`❌ falha ao converter ${path.basename(entrada)}: ${e.message}`);
        process.exit(1);
    }

    const rotulo = `${path.basename(entrada)} [mode=${modo}${aula ? `, aula=${aula}` : ''}]`;
    if (resultado.warnings.length) {
        console.log(`⚠️  ${rotulo} — ${resultado.warnings.length} aviso(s) de furigana:`);
        resultado.warnings.forEach((w) => console.log('   - ' + w));
    }
    if (resultado.errors.length) {
        console.error(`❌ ${rotulo} — ${resultado.errors.length} ERRO(S) BLOQUEANTE(S) — EPUB não gerado:`);
        resultado.errors.forEach((e) => console.error('   - ' + e));
        console.error('   O EPUB herda o furigana do HTML: corrija o HTML e regere os dois.');
        process.exit(1);
    }

    fs.writeFileSync(saida, resultado.buffer);
    const kb = (resultado.buffer.length / 1024).toFixed(1);
    console.log(`✅ ${path.basename(saida)} — ${resultado.capitulos.length} capítulos, ${kb} KB, furigana validado.`);
    console.log(`   Título: ${resultado.titulo}`);
    console.log('   Envie ao Kindle pelo Send to Kindle (e-mail @kindle.com, app ou web) — ' +
        'a Amazon converte o EPUB para KFX preservando o ruby.');

    if (tem('upload')) {
        const nomeDrive = flag('nome-drive') || path.basename(saida);
        const { uploadLesson } = require('../../Google Workspace/Drive/scripts/upload_to_gdrive.js');
        await uploadLesson(nomeDrive, fs.readFileSync(saida));
    }
}

if (require.main === module) {
    main(process.argv).catch((e) => {
        console.error('Erro:', e.message);
        process.exit(1);
    });
}

module.exports = {
    construirEpub, zipar, paraXhtml, tabelasParaBlocos, dividirCapitulos,
    verificarXml, textoPuro, decodificarEntidades, removerInterativos,
    achatarVariaveis, marcarIdiomaJapones,
};
