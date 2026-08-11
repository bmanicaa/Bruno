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

module.exports = { getAccessToken };
