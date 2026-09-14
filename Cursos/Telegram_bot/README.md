# 🤖 Guia Completo: Assistente OpenCode no Telegram

Este bot integra **todos os recursos e comandos do OpenCode** ao seu Telegram, permitindo alternar modelos de IA, inspecionar diffs do Git, gerenciar sessões, ver telemetria de custos e agendar rotinas.

---

## 📋 Lista Completa de Comandos Slash (`/`)

### 🤖 Modelos e Provedores
| Comando | Descrição | Exemplo de Uso |
| :--- | :--- | :--- |
| `/model` | Exibe o modelo ativo, provedor e modo atual | `/model` |
| `/model <nome>` | Troca o modelo de IA em tempo real | `/model deepseek/deepseek-reasoner` ou `/model gemini-2.5-pro` |
| `/models [filtro]` | Lista modelos disponíveis no OpenCode | `/models` ou `/models deepseek` ou `/models google` |
| `/providers` ou `/auth` | Lista provedores e credenciais ativas | `/providers` |

### 🛠️ Controle de Agente e Sessões
| Comando | Descrição | Exemplo de Uso |
| :--- | :--- | :--- |
| `/agent [build\|plan]` | Alterna modo (execução total vs planejamento) | `/agent plan` ou `/agent build` |
| `/clear` ou `/reset` | Inicia uma nova sessão limpa | `/clear` |
| `/sessions` | Lista as últimas sessões do OpenCode | `/sessions` |
| `/session <id>` | Retoma uma sessão anterior pelo ID | `/session ses_123456` |
| `/stats` ou `/cost` | Mostra tokens (Input/Output/Cache/Reasoning) e custo | `/stats` |
| `/export` | Exporta o log completo da sessão atual em arquivo | `/export` |

### 💻 Git, Código e Tarefas
| Comando | Descrição | Exemplo de Uso |
| :--- | :--- | :--- |
| `/diff` ou `/git` | Mostra status e resumo de alterações Git no projeto | `/diff` |
| `/crons` | Lista tarefas e rotinas agendadas | `/crons` |
| `/crons cancel <id>` | Cancela uma tarefa agendada | `/crons cancel job_1` |
| `/help` | Exibe o menu completo de ajuda | `/help` |
