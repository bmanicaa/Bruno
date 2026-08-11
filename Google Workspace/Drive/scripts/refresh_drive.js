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
    return data.access_token;
}

async function getRootId(accessToken) {
    const response = await fetch('https://www.googleapis.com/drive/v3/files/root?fields=id', {
        headers: { Authorization: `Bearer ${accessToken}` },
    });
    const data = await response.json();
    return data.id;
}

async function listOwnedFiles(accessToken) {
    let files = [];
    let pageToken = null;
    do {
        const url = new URL('https://www.googleapis.com/drive/v3/files');
        url.searchParams.append('pageSize', '1000');
        url.searchParams.append('fields', 'nextPageToken, files(id, name, mimeType, parents, size, modifiedTime)');
        url.searchParams.append('q', "'me' in owners and trashed = false");
        if (pageToken) url.searchParams.append('pageToken', pageToken);

        const response = await fetch(url, {
            headers: { Authorization: `Bearer ${accessToken}` },
        });
        const data = await response.json();
        if (data.files) files.push(...data.files);
        pageToken = data.nextPageToken;
    } while (pageToken);
    return files;
}

function formatSize(bytes) {
    if (!bytes || isNaN(bytes)) return '0 B';
    const s = ['B', 'KB', 'MB', 'GB', 'TB'];
    const e = Math.floor(Math.log(bytes) / Math.log(1024));
    return (bytes / Math.pow(1024, e)).toFixed(2) + ' ' + s[e];
}

async function main() {
    try {
        console.log('--- Iniciando Sincronização do Drive ---');
        const accessToken = await getAccessToken();
        const rootId = await getRootId(accessToken);
        const files = await listOwnedFiles(accessToken);
        
        const fileMap = {};
        files.forEach(f => fileMap[f.id] = f);

        // 1. Gerar drive_index.txt
        const pathCache = new Map();
        function getPath(file) {
            if (pathCache.has(file.id)) {
                return pathCache.get(file.id);
            }

            if (!file.parents || file.parents.length === 0 || file.parents[0] === rootId) {
                const p = '/' + file.name;
                pathCache.set(file.id, p);
                return p;
            }
            const parentId = file.parents[0];
            const parent = fileMap[parentId];
            
            if (!parent) {
                const p = '/[FORA_DO_ESCOPO]/' + file.name;
                pathCache.set(file.id, p);
                return p;
            }
            
            const p = getPath(parent) + '/' + file.name;
            pathCache.set(file.id, p);
            return p;
        }

        const indexLines = [];
        indexLines.push('# GOOGLE DRIVE INDEX - UPDATED ' + new Date().toISOString());
        indexLines.push('# FORMAT: ID | PATH | SIZE | MODIFIED');
        indexLines.push('');

        const folderStats = {};
        const duplicatesMap = {}; // key: name_size

        files.forEach(f => {
            const isFolder = f.mimeType === 'application/vnd.google-apps.folder';
            const fullPath = getPath(f);
            
            if (!isFolder) {
                const sizeNum = parseInt(f.size) || 0;
                const sizeStr = formatSize(sizeNum);
                const date = f.modifiedTime ? f.modifiedTime.split('T')[0] : 'N/A';
                indexLines.push(`${f.id} | ${fullPath} | ${sizeStr} | ${date}`);

                // Folder stats
                const parentPath = path.dirname(fullPath);
                if (!folderStats[parentPath]) {
                    folderStats[parentPath] = { count: 0, size: 0 };
                }
                folderStats[parentPath].count += 1;
                folderStats[parentPath].size += sizeNum;

                // Duplicates analysis
                if (sizeNum > 0) {
                    const dupKey = `${f.name}_${sizeNum}`;
                    if (!duplicatesMap[dupKey]) duplicatesMap[dupKey] = [];
                    duplicatesMap[dupKey].push(fullPath);
                }
            }
        });

        fs.writeFileSync(path.join(__dirname, '../drive_index.txt'), indexLines.join('\n'));
        console.log('✓ drive_index.txt atualizado.');

        // 2. Gerar folders_summary.txt
        const folderLines = [];
        folderLines.push('# FOLDERS SUMMARY');
        folderLines.push('# FORMAT: FOLDER PATH | FILE COUNT | TOTAL SIZE');
        folderLines.push('');
        
        Object.keys(folderStats).sort().forEach(folder => {
            const stats = folderStats[folder];
            folderLines.push(`${folder} | ${stats.count} files | ${formatSize(stats.size)}`);
        });
        
        fs.writeFileSync(path.join(__dirname, '../folders_summary.txt'), folderLines.join('\n'));
        console.log('✓ folders_summary.txt atualizado.');

        // 3. Gerar duplicates_report.txt
        const dupLines = [];
        dupLines.push('# POTENTIAL DUPLICATES REPORT');
        dupLines.push('# Items with same name and exact same byte size');
        dupLines.push('');
        
        let dupFound = false;
        Object.keys(duplicatesMap).forEach(key => {
            const paths = duplicatesMap[key];
            if (paths.length > 1) {
                dupFound = true;
                dupLines.push(`[DUPLICATE GROUP] Name_Size: ${key}`);
                paths.forEach(p => dupLines.push(`  - ${p}`));
                dupLines.push('');
            }
        });

        if (!dupFound) dupLines.push('Nenhuma duplicata óbvia encontrada.');
        fs.writeFileSync(path.join(__dirname, '../duplicates_report.txt'), dupLines.join('\n'));
        console.log('✓ duplicates_report.txt atualizado.');
        
        console.log('--- Sincronização Concluída ---');

    } catch (error) {
        console.error('ERRO:', error.message);
    }
}

main();
