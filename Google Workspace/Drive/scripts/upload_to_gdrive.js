const fs = require('fs');
const path = require('path');

// --- VALIDAÇÃO AUTOMÁTICA DE RUBY (Regra 11 do JLPTN5.md / §4.6 do Filters/HTML.md) ---
// Determinística e bloqueante: um arquivo HTML reprovado NÃO é enviado ao Drive.

const KANJI_RE = /[\u3400-\u9fff\uf900-\ufaff]/; // Ideogramas CJK (kanji)

function extractLessonNumber(fileName) {
    const m = fileName.match(/N5_L(\d+)\.html/i);
    return m ? parseInt(m[1], 10) : null;
}

// Lê Content/N5_Kanji.md e monta o mapa kanji -> aula de introdução.
function loadFormalKanji() {
    const kanjiPath = path.join(__dirname, '../../../Japones/Content/N5_Kanji.md');
    if (!fs.existsSync(kanjiPath)) return null;
    const lines = fs.readFileSync(kanjiPath, 'utf8').split('\n');
    const map = new Map();
    for (const line of lines) {
        const m = line.match(/^\|\s*\d+\s*\|\s*([\u3400-\u9fff])\s*\|\s*(\d+)\s*\|/);
        if (m) map.set(m[1], parseInt(m[2], 10));
    }
    return map.size ? map : null;
}

function validateLessonHtml(html, lessonNum, formalKanji) {
    const errors = [];
    const warnings = [];

    // Isola o <body> (remove <head>, <style> e <script>)
    const clean = (html.includes('</head>') ? html.split('</head>')[1] : html)
        .replace(/<style>[\s\S]*?<\/style>/g, ' ')
        .replace(/<script>[\s\S]*?<\/script>/g, ' ');

    // CHECK 1 — Nenhum <ruby> sobre palavra sem kanji (kana puro).
    const rubyRe = /<ruby[^>]*>([\s\S]*?)<\/ruby>/g;
    let m;
    while ((m = rubyRe.exec(clean)) !== null) {
        const inner = m[1];
        const rtIdx = inner.indexOf('<rt>');
        const base = (rtIdx >= 0 ? inner.slice(0, rtIdx) : inner).replace(/<[^>]+>/g, '');
        if (![...base].some(ch => KANJI_RE.test(ch))) {
            errors.push(`CHECK1 [ruby sobre kana puro]: <ruby>${base}</ruby> não pode existir.`);
        }
    }

    // Regiões isentas: layer-4 breakdown (a frase anotada está logo acima).
    const exemptRegions = [];
    const breakdownRe = /<div class="layer-4-breakdown">[\s\S]*?<\/div>/g;
    let bm;
    while ((bm = breakdownRe.exec(clean)) !== null) {
        exemptRegions.push([bm.index, bm.index + bm[0].length]);
    }
    const inExempt = (pos) => exemptRegions.some(([a, b]) => pos >= a && pos < b);

    // Regiões cobertas por <ruby> (a base contém o kanji anotado).
    const rubyRegions = [];
    const rubyAllRe = /<ruby[^>]*>[\s\S]*?<\/ruby>/g;
    let rm;
    while ((rm = rubyAllRe.exec(clean)) !== null) rubyRegions.push([rm.index, rm.index + rm[0].length]);
    const inRuby = (pos) => rubyRegions.some(([a, b]) => pos >= a && pos < b);

    // CHECK 2 — Todo kanji Nível 2 (reconhecimento) precisa de ruby em TODA ocorrência.
    if (formalKanji && lessonNum) {
        const isLevel2 = (ch) => {
            if (!formalKanji.has(ch)) return true;
            return formalKanji.get(ch) > lessonNum;
        };
        for (let i = 0; i < clean.length; i++) {
            const ch = clean[i];
            if (!KANJI_RE.test(ch)) continue;
            if (inRuby(i) || inExempt(i)) continue;
            if (isLevel2(ch)) {
                const ctx = clean.slice(Math.max(0, i - 15), i + 16).replace(/<[^>]+>/g, '').replace(/\s+/g, ' ').trim();
                errors.push(`CHECK2 [kanji Nível 2 sem ruby]: "${ch}" em ...${ctx}...`);
            }
        }
    } else if (formalKanji) {
        warnings.push('CHECK2 não executado: número da aula não identificado no nome do arquivo (use N5_LX.html).');
    } else {
        warnings.push('CHECK2 não executado: Content/N5_Kanji.md não encontrado.');
    }

    // CHECK 3 — Layer-2-kana condicional (presente ⟺ layer-1 tem kanji sem ruby).
    const layer1Re = /<div class="layer-1-ja ja-text">([\s\S]*?)<\/div>/g;
    let lm;
    while ((lm = layer1Re.exec(clean)) !== null) {
        const l1Clean = lm[1].replace(/<ruby[^>]*>[\s\S]*?<\/ruby>/g, '').replace(/<[^>]+>/g, '');
        const bare = [...l1Clean].some(ch => KANJI_RE.test(ch));
        const after = clean.slice(lm.index + lm[0].length, lm.index + lm[0].length + 200);
        const hasL2 = /^\s*<div class="layer-2-kana">/.test(after);
        const snippet = lm[1].replace(/<[^>]+>/g, '').replace(/\s+/g, ' ').trim();
        if (hasL2 && !bare) {
            errors.push(`CHECK3 [layer-2 redundante]: frase 100% anotada por ruby não deve ter layer-2-kana — "${snippet}".`);
        }
        if (!hasL2 && bare) {
            errors.push(`CHECK3 [layer-2 ausente]: frase com kanji sem ruby (buraco de leitura) exige layer-2-kana — "${snippet}".`);
        }
    }

    // CHECK 4 (aviso) — Nível 1 não pode repetir <ruby> para a mesma palavra no arquivo.
    if (formalKanji && lessonNum) {
        const seen = new Map();
        rubyRe.lastIndex = 0;
        while ((m = rubyRe.exec(clean)) !== null) {
            const inner = m[1];
            const rtIdx = inner.indexOf('<rt>');
            const base = (rtIdx >= 0 ? inner.slice(0, rtIdx) : inner).replace(/<[^>]+>/g, '');
            const baseKanji = [...base].filter(ch => KANJI_RE.test(ch));
            const allLevel1 = baseKanji.length > 0 && baseKanji.every(ch => formalKanji.has(ch) && formalKanji.get(ch) <= lessonNum);
            if (!allLevel1) continue;
            if (seen.has(base)) {
                warnings.push(`CHECK4 [Nível 1 ruby repetido]: "${base}" já apareceu com ruby neste arquivo (1ª ocorrência apenas).`);
            } else {
                seen.set(base, true);
            }
        }
    }

    return { errors, warnings };
}

async function getAccessToken() {
    const keysPath = path.join(__dirname, '../../Keys/Google keys.json');
    const tokenPath = path.join(__dirname, '../../Keys/token.json');
    
    if (!fs.existsSync(keysPath) || !fs.existsSync(tokenPath)) {
        throw new Error('Chaves de API não encontradas em Keys/');
    }

    const keys = JSON.parse(fs.readFileSync(keysPath, 'utf8'));
    const token = JSON.parse(fs.readFileSync(tokenPath, 'utf8'));
    const { client_id, client_secret } = keys.installed || keys.web;
    const { refresh_token } = token;

    const response = await fetch('https://oauth2.googleapis.com/token', {
        method: 'POST',
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
        body: new URLSearchParams({ client_id, client_secret, refresh_token, grant_type: 'refresh_token' }),
    });
    const data = await response.json();
    if (!data.access_token) {
        throw new Error('Erro ao obter token: ' + JSON.stringify(data));
    }
    return data.access_token;
}

async function findOrCreateFolder(token, folderName, parentId = 'root') {
    // Check if folder exists
    const q = `name = '${folderName}' and '${parentId}' in parents and mimeType = 'application/vnd.google-apps.folder' and trashed = false`;
    const res = await fetch(`https://www.googleapis.com/drive/v3/files?q=${encodeURIComponent(q)}`, {
        headers: { Authorization: `Bearer ${token}` }
    });
    const data = await res.json();
    if (data.files && data.files.length > 0) {
        return data.files[0].id;
    }

    // Create folder
    const createRes = await fetch('https://www.googleapis.com/drive/v3/files', {
        method: 'POST',
        headers: {
            Authorization: `Bearer ${token}`,
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            name: folderName,
            mimeType: 'application/vnd.google-apps.folder',
            parents: [parentId]
        })
    });
    const createData = await createRes.json();
    if (createData.error) throw new Error(createData.error.message);
    return createData.id;
}

async function uploadLesson(fileName, fileContent, convertToDoc = null) {
    // VALIDAÇÃO AUTOMÁTICA (Regra 11) — bloqueia upload de HTML reprovado.
    if (fileName.toLowerCase().endsWith('.html')) {
        const lessonNum = extractLessonNumber(fileName);
        const formalKanji = loadFormalKanji();
        const { errors, warnings } = validateLessonHtml(fileContent, lessonNum, formalKanji);
        if (warnings.length) {
            console.log('⚠️ AVISOS (não bloqueantes):\n' + warnings.map(w => '  - ' + w).join('\n'));
        }
        if (errors.length) {
            console.error('❌ VALIDAÇÃO DE RUBY REPROVADA — upload bloqueado:\n' + errors.map(e => '  - ' + e).join('\n'));
            throw new Error('Aula reprovada na validação de ruby (Regra 11 / Filters/HTML.md §4.6). Corrija o HTML e tente novamente.');
        }
        console.log('✓ Validação de ruby aprovada (Regra 11).');
    }

    const token = await getAccessToken();
    const isHtml = fileName.toLowerCase().endsWith('.html');

    if (convertToDoc === null) {
        convertToDoc = !isHtml;
    }

    // 1. Get or create 'Aulas' folder in root
    const aulasFolderId = await findOrCreateFolder(token, 'Aulas', 'root');
    
    // 2. Get or create 'Japones' folder inside 'aulas'
    const japonesFolderId = await findOrCreateFolder(token, 'Japones', aulasFolderId);

    // 3. Check if file already exists in Japones folder
    const checkQ = `name = '${fileName}' and '${japonesFolderId}' in parents and trashed = false`;
    const checkRes = await fetch(`https://www.googleapis.com/drive/v3/files?q=${encodeURIComponent(checkQ)}`, {
        headers: { Authorization: `Bearer ${token}` }
    });
    const checkData = await checkRes.json();
    const existingFileId = (checkData.files && checkData.files.length > 0) ? checkData.files[0].id : null;

    // 4. Metadata
    const metadata = {
        name: fileName,
        parents: existingFileId ? undefined : [japonesFolderId]
    };
    if (convertToDoc) {
        metadata.mimeType = 'application/vnd.google-apps.document';
    }

    const boundary = '-------314159265358979323846';
    const delimiter = "\r\n--" + boundary + "\r\n";
    const close_delim = "\r\n--" + boundary + "--";

    const fileBuffer = Buffer.from(fileContent, 'utf8');
    const uploadContentType = isHtml ? 'text/html; charset=UTF-8' : 'text/markdown; charset=UTF-8';

    const bodyHeader = 
        delimiter +
        'Content-Type: application/json; charset=UTF-8\r\n\r\n' +
        JSON.stringify(metadata) +
        delimiter +
        `Content-Type: ${uploadContentType}\r\n\r\n`;

    const payload = Buffer.concat([
        Buffer.from(bodyHeader, 'utf8'),
        fileBuffer,
        Buffer.from(close_delim, 'utf8')
    ]);

    let url = 'https://www.googleapis.com/upload/drive/v3/files?uploadType=multipart';
    let method = 'POST';
    if (existingFileId) {
        url = `https://www.googleapis.com/upload/drive/v3/files/${existingFileId}?uploadType=multipart`;
        method = 'PATCH';
    }

    const res = await fetch(url, {
        method: method,
        headers: {
            Authorization: `Bearer ${token}`,
            'Content-Type': `multipart/related; boundary=${boundary}`
        },
        body: payload
    });

    const result = await res.json();
    if (result.error) throw new Error(result.error.message);
    
    console.log(`✓ Aula enviada com sucesso para o Google Drive! ID: ${result.id}`);
    return result;
}

// CLI Execution if called directly
if (require.main === module) {
    const args = process.argv.slice(2);
    const filePath = args[0];
    const fileName = args[1] || (filePath ? path.basename(filePath) : null);
    
    if (!filePath) {
        console.log('Uso: node upload_to_gdrive.js <caminho_do_arquivo_local> [nome_no_drive]');
        process.exit(1);
    }
    
    const content = fs.readFileSync(filePath, 'utf8');
    uploadLesson(fileName, content)
        .then(() => console.log('Upload concluído!'))
        .catch(err => console.error('Erro no upload:', err));
}

module.exports = { uploadLesson, validateLessonHtml, extractLessonNumber, loadFormalKanji };
