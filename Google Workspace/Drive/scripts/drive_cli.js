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
        throw new Error('Erro ao obter token de acesso: ' + JSON.stringify(data));
    }
    return data.access_token;
}

async function searchIndex(term) {
    const indexPath = path.join(__dirname, '../drive_index.txt');
    if (!fs.existsSync(indexPath)) {
        console.log('drive_index.txt não encontrado. Execute refresh_drive.js primeiro.');
        return;
    }
    const lines = fs.readFileSync(indexPath, 'utf8').split('\n');
    const termLower = term.toLowerCase();
    const results = lines.filter(l => !l.startsWith('#') && l.toLowerCase().includes(termLower));
    
    console.log(`--- Resultados para "${term}" (${results.length} encontrados) ---`);
    results.forEach(r => console.log(r));
}

async function downloadFile(fileId, destPath) {
    const token = await getAccessToken();
    const metaRes = await fetch(`https://www.googleapis.com/drive/v3/files/${fileId}?fields=id,name,mimeType`, {
        headers: { Authorization: `Bearer ${token}` }
    });
    const meta = await metaRes.json();
    if (meta.error) {
        throw new Error(meta.error.message);
    }

    const fileName = path.basename(meta.name);
    const isGoogleDoc = meta.mimeType.startsWith('application/vnd.google-apps.');
    let url = `https://www.googleapis.com/drive/v3/files/${fileId}?alt=media`;
    
    if (isGoogleDoc) {
        let exportMime = 'text/plain';
        if (meta.mimeType.includes('spreadsheet')) exportMime = 'text/csv';
        if (meta.mimeType.includes('document')) exportMime = 'text/markdown';
        url = `https://www.googleapis.com/drive/v3/files/${fileId}/export?mimeType=${encodeURIComponent(exportMime)}`;
    }

    const res = await fetch(url, { headers: { Authorization: `Bearer ${token}` } });
    if (!res.ok) throw new Error(`Falha no download: ${res.statusText}`);

    const buffer = Buffer.from(await res.arrayBuffer());
    const finalPath = destPath || path.join(process.cwd(), fileName);
    fs.writeFileSync(finalPath, buffer);
    console.log(`✓ Arquivo salvo em: ${finalPath}`);
}

async function uploadFile(localPath, folderId) {
    if (!fs.existsSync(localPath)) {
        throw new Error(`Arquivo não encontrado: ${localPath}`);
    }
    const token = await getAccessToken();
    const fileName = path.basename(localPath);
    const metadata = { name: fileName };
    if (folderId) metadata.parents = [folderId];

    const fileBuffer = fs.readFileSync(localPath);

    const form = new Blob([
        JSON.stringify(metadata) + '\n',
        fileBuffer
    ]);

    // Simple upload using Multipart API
    const boundary = '-------314159265358979323846';
    const delimiter = "\r\n--" + boundary + "\r\n";
    const close_delim = "\r\n--" + boundary + "--";

    const body = 
        delimiter +
        'Content-Type: application/json; charset=UTF-8\r\n\r\n' +
        JSON.stringify(metadata) +
        delimiter +
        'Content-Type: application/octet-stream\r\n\r\n';

    const payload = Buffer.concat([
        Buffer.from(body, 'utf8'),
        fileBuffer,
        Buffer.from(close_delim, 'utf8')
    ]);

    const res = await fetch('https://www.googleapis.com/upload/drive/v3/files?uploadType=multipart', {
        method: 'POST',
        headers: {
            Authorization: `Bearer ${token}`,
            'Content-Type': `multipart/related; boundary=${boundary}`
        },
        body: payload
    });

    const data = await res.json();
    if (data.error) throw new Error(data.error.message);
    console.log(`✓ Arquivo enviado com sucesso! ID: ${data.id}`);
}

async function main() {
    const args = process.argv.slice(2);
    const command = args[0];

    try {
        switch (command) {
            case 'search':
                await searchIndex(args[1] || '');
                break;
            case 'download':
                if (!args[1]) return console.log('Uso: node drive_cli.js download <fileID> [destPath]');
                await downloadFile(args[1], args[2]);
                break;
            case 'upload':
                if (!args[1]) return console.log('Uso: node drive_cli.js upload <localPath> [folderID]');
                await uploadFile(args[1], args[2]);
                break;
            default:
                console.log('Comandos disponíveis:');
                console.log('  node drive_cli.js search <termo>');
                console.log('  node drive_cli.js download <fileID> [destino]');
                console.log('  node drive_cli.js upload <arquivoLocal> [folderID]');
                break;
        }
    } catch (e) {
        console.error('ERRO:', e.message);
    }
}

main();
