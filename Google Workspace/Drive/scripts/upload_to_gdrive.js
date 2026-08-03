const fs = require('fs');
const path = require('path');

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

module.exports = { uploadLesson };
