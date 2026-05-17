# Guia de Organização do Google Drive (Automação)

Este repositório contém as chaves de acesso e o mapa estrutural da conta do Google Drive vinculada (`b.manicag@gmail.com`). O objetivo é permitir que a Inteligência Artificial gerencie, organize e consulte o Drive de forma autônoma e com altíssima eficiência de tokens.

## 🗺️ Mapa do Drive (Fonte da Verdade)

Para evitar chamadas lentas de API e estourar o limite de contexto consultando milhares de arquivos, mantemos o estado do Drive armazenado localmente nestes arquivos:

1. **`drive_index.txt`**: É o índice principal. Contém todos os arquivos de propriedade do usuário. Formato: `ID | Caminho Completo | Tamanho | Data`. É perfeito para usar comandos `grep` para achar arquivos rapidamente.
2. **`folders_summary.txt`**: Um resumo de cada pasta existente, com a contagem de arquivos e o peso total (tamanho ocupado) daquela pasta. Útil para identificar quais pastas estão mais pesadas.
3. **`duplicates_report.txt`**: Um relatório de arquivos potencialmente duplicados (mesmo nome e mesmo tamanho exato de bytes).

*(Atenção IA: Se o usuário pedir para listar arquivos, procure **sempre** nesses arquivos de texto primeiro. Não chame a API a menos que precise mover ou deletar algo.)*

## 🛠️ Como Atualizar o Mapa

Sempre que a IA realizar uma alteração no Drive (mover, deletar, renomear), ou se o usuário relatar que deletou algo pela interface web, **atualize o mapa** rodando o script a partir da raiz do projeto:

```bash
node Drive/scripts/refresh_drive.js
```

*(Ou navegue até a pasta `Drive` e execute `node scripts/refresh_drive.js`).*

Este script vai bater na API do Google Drive usando as credenciais em `Keys/`, mapear a árvore de diretórios, calcular os tamanhos das pastas e reconstruir os 3 arquivos de texto na pasta `Drive/`.

## 🔐 Credenciais

* As credenciais estão na pasta `Keys/`.
* `token.json` contém o token de acesso (OAuth2) do usuário.
* Para executar os scripts, basta importar as credenciais, obter um novo `access_token` usando o `refresh_token`, e enviar a requisição via `fetch` para `https://www.googleapis.com/drive/v3/`.

## 🧹 Boas Práticas de Organização

* **Não use o Mermaid para árvores complexas**: Para 100+ arquivos, o Mermaid consome muitos tokens e falha na renderização. Use listas em Markdown ou a saída plana do `drive_index.txt`.
* **Cuidado com `[FORA_DO_ESCOPO]`**: Se um arquivo aparecer neste diretório no mapa, significa que o arquivo pertence ao usuário, mas está dentro de uma pasta cujo dono é outra pessoa, ou a pasta pai foi deletada, deixando o arquivo "órfão".
