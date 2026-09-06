const fs = require('fs');
const path = require('path');

// --- VALIDAÇÃO AUTOMÁTICA DE ARTEFATOS (Regra 11 do JLPTN5.md / §4.6 do HTML_Lesson.md) ---
// A lógica vive numa FONTE ÚNICA DE VERDADE, em Japones/scripts/validate_artifact.js,
// para que o mesmo validador sirva HTML (aula/reading), Markdown (Teste/Lacunas/Ditado)
// e TSV do Anki. Determinística e bloqueante: artefato reprovado NÃO sobe ao Drive.
const {
    validateArtifact,
    detectMode,
    detectLesson,
} = require('../../../Japones/scripts/validate_artifact.js');

const { getAccessToken } = require('./auth');

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
    // VALIDAÇÃO AUTOMÁTICA (Regra 11) — bloqueia upload de artefato reprovado.
    // O modo é inferido do nome do arquivo: N5_L{n}.html = aula (furigana universal),
    // N5_P{n}_Reading.html = reading (furigana gradual). Nunca mais silenciosamente
    // pulada: se o modo/aula não puder ser inferido, isso é dito em voz alta.
    {
        const mode = detectMode(fileName);
        const lesson = detectLesson(fileName);
        if (!lesson) {
            console.log(`⚠️ Aula não identificada em "${fileName}" — o Vocabulary Gate (CHECK5) não será executado.`);
        }
        const { errors, warnings } = validateArtifact(fileContent, { mode, lesson });
        console.log(`▶ Validando "${fileName}" [mode=${mode}${lesson ? `, aula=${lesson}` : ''}]`);
        if (warnings.length) {
            console.log('⚠️ AVISOS (não bloqueantes):\n' + warnings.map(w => '  - ' + w).join('\n'));
        }
        if (errors.length) {
            console.error('❌ VALIDAÇÃO REPROVADA — upload bloqueado:\n' + errors.map(e => '  - ' + e).join('\n'));
            throw new Error('Artefato reprovado na validação (Regra 11 / HTML_Lesson.md §4.6). Corrija e tente novamente.');
        }
        console.log('✓ Validação aprovada (Regra 11).');
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

module.exports = { uploadLesson, validateArtifact, detectMode, detectLesson };
