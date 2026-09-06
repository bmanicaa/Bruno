const fs = require('fs');
const path = require('path');

async function getAccessToken() {
    const keysPath = path.join(__dirname, '../../Keys/Google keys.json');
    const tokenPath = path.join(__dirname, '../../Keys/token.json');

    let keys, token;
    try {
        const [keysData, tokenData] = await Promise.all([
            fs.promises.readFile(keysPath, 'utf8'),
            fs.promises.readFile(tokenPath, 'utf8')
        ]);
        keys = JSON.parse(keysData);
        token = JSON.parse(tokenData);
    } catch (error) {
        if (error.code === 'ENOENT') {
            throw new Error('Chaves de API não encontradas em Keys/');
        }
        throw error;
    }

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

module.exports = { getAccessToken };
