import os
import asyncio
import io
import json
import re
from pathlib import Path
from dotenv import load_dotenv
from telegram import (
    Update, BotCommand, InlineKeyboardButton, InlineKeyboardMarkup
)
from telegram.constants import ChatAction, ParseMode
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler, CallbackQueryHandler,
    filters, ContextTypes
)

from agent import OpenCodeAgent, PROJECT_ROOT
from scheduler import scheduler

ENV_FILE = Path(__file__).resolve().parent / ".env"
FAVORITES_FILE = Path(__file__).resolve().parent / "favorites.json"
load_dotenv(dotenv_path=ENV_FILE)

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
OPENCODE_URL = os.getenv("OPENCODE_URL", "http://127.0.0.1:4096").strip()
ALLOWED_USER_ID_STR = os.getenv("ALLOWED_USER_ID", "").strip()

ALLOWED_USER_ID = int(ALLOWED_USER_ID_STR) if ALLOWED_USER_ID_STR.isdigit() else None

agent = OpenCodeAgent(base_url=OPENCODE_URL)
active_telegram_app = None

def load_favorites() -> dict:
    if FAVORITES_FILE.exists():
        try:
            with open(FAVORITES_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {}

def save_allowed_user(user_id: int):
    global ALLOWED_USER_ID
    ALLOWED_USER_ID = user_id
    try:
        lines = []
        if ENV_FILE.exists():
            with open(ENV_FILE, "r", encoding="utf-8") as f:
                lines = f.readlines()
        
        updated = False
        new_lines = []
        for line in lines:
            if line.startswith("ALLOWED_USER_ID="):
                new_lines.append(f"ALLOWED_USER_ID={user_id}\n")
                updated = True
            else:
                new_lines.append(line)
        if not updated:
            new_lines.append(f"ALLOWED_USER_ID={user_id}\n")
            
        with open(ENV_FILE, "w", encoding="utf-8") as f:
            f.writelines(new_lines)
    except Exception as e:
        print(f"[Auth] Erro ao salvar ALLOWED_USER_ID no .env: {e}")

async def send_split_message(update: Update, context: ContextTypes.DEFAULT_TYPE, text: str, chat_id: int):
    """Envia mensagens longas divididas em blocos de até 4000 caracteres."""
    max_len = 4000
    chunks = [text[i:i+max_len] for i in range(0, len(text), max_len)]
    for chunk in chunks:
        try:
            await context.bot.send_message(
                chat_id=chat_id,
                text=chunk,
                parse_mode=ParseMode.MARKDOWN
            )
        except Exception:
            await context.bot.send_message(
                chat_id=chat_id,
                text=chunk
            )

async def check_authorization(update: Update) -> bool:
    user = update.effective_user
    if not user:
        return False
        
    global ALLOWED_USER_ID
    if ALLOWED_USER_ID is None:
        save_allowed_user(user.id)
        return True
        
    if user.id != ALLOWED_USER_ID:
        if update.message:
            await update.message.reply_text("⛔ Acesso negado. Este bot é privado.")
        elif update.callback_query:
            await update.callback_query.answer("⛔ Acesso negado.", show_alert=True)
        return False
    return True

def get_main_models_keyboard(current_model: str = "") -> InlineKeyboardMarkup:
    """Menu principal de modelos com os mais usados no OpenCode e categorias."""
    keyboard = [
        [
            InlineKeyboardButton("⚡ DeepSeek V4 Flash", callback_data="setmod_deepseek/deepseek-v4-flash"),
            InlineKeyboardButton("👑 DeepSeek V4 Pro", callback_data="setmod_deepseek/deepseek-v4-pro")
        ],
        [
            InlineKeyboardButton("🤖 Nemotron 3 Ultra 550B", callback_data="setmod_nvidia/nvidia/nemotron-3-ultra-550b-a55b"),
            InlineKeyboardButton("⚡ DeepSeek V4 (Nvidia)", callback_data="setmod_nvidia/deepseek-ai/deepseek-v4-flash")
        ],
        [
            InlineKeyboardButton("🧠 DeepSeek Reasoner", callback_data="setmod_deepseek/deepseek-reasoner"),
            InlineKeyboardButton("💻 Qwen 3 Coder 480B", callback_data="setmod_nvidia/qwen/qwen3-coder-480b-a35b-instruct")
        ],
        [
            InlineKeyboardButton("💎 Gemma 4 31B (Google)", callback_data="setmod_google/gemma-4-31b-it")
        ],
        [
            InlineKeyboardButton("🟣 DeepSeek", callback_data="favcat_DeepSeek"),
            InlineKeyboardButton("🟢 Nvidia", callback_data="favcat_Nvidia"),
            InlineKeyboardButton("🔵 Google", callback_data="favcat_Google")
        ],
        [
            InlineKeyboardButton("📋 Ver Todos os 60+ Modelos do OpenCode", callback_data="menu_all_models")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_category_models_keyboard(category_name: str, chat_id: int) -> InlineKeyboardMarkup:
    """Gera botões com os modelos favoritos da categoria selecionada."""
    favs = load_favorites()
    keyboard = []
    
    current_info = agent.user_models.get(chat_id)
    current_mid = f"{current_info['providerID']}/{current_info['modelID']}" if current_info else "deepseek/deepseek-v4-flash"

    items = favs.get(category_name, [])

    row = []
    for item in items:
        mid = item["id"]
        is_active = (mid == current_mid)
        label = f"✅ {item['label']}" if is_active else item["label"]
        row.append(InlineKeyboardButton(label, callback_data=f"setmod_{mid}"))
        if len(row) == 2:
            keyboard.append(row)
            row = []
    if row:
        keyboard.append(row)

    keyboard.append([InlineKeyboardButton("🔙 Voltar aos Modelos Principais", callback_data="menu_model_main")])
    return InlineKeyboardMarkup(keyboard)

def get_agent_mode_keyboard() -> InlineKeyboardMarkup:
    """Gera botões interativos para alternar o modo do agente."""
    keyboard = [
        [
            InlineKeyboardButton("🔨 Modo Build (Execução Total)", callback_data="setagent_build")
        ],
        [
            InlineKeyboardButton("📋 Modo Plan (Planejamento Seguro)", callback_data="setagent_plan")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_workspace_keyboard(chat_id: int) -> InlineKeyboardMarkup:
    """Gera botões para alternar pastas e navegar pelo projeto."""
    subdirs = agent.list_subdirectories(chat_id)
    
    keyboard = []
    
    # Atalhos rápidos padrão
    keyboard.append([
        InlineKeyboardButton("📁 Pasta Telegram", callback_data="setdir_Telegram"),
        InlineKeyboardButton("📁 Pasta Project", callback_data="setdir_project")
    ])

    # Botões para subpastas do diretório atual
    if subdirs:
        row = []
        for d in subdirs[:6]:
            row.append(InlineKeyboardButton(f"📁 {d}", callback_data=f"setdir_{d}"))
            if len(row) == 2:
                keyboard.append(row)
                row = []
        if row:
            keyboard.append(row)

    # Botão para subir pasta
    keyboard.append([
        InlineKeyboardButton("⬆️ Subir Pasta (..)", callback_data="setdir_.."),
        InlineKeyboardButton("🔄 Recarregar /dir", callback_data="menu_dir_refresh")
    ])
    return InlineKeyboardMarkup(keyboard)

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_authorization(update):
        return

    current_dir = agent.get_current_directory(update.effective_chat.id)
    msg = (
        "🚀 **Assistente OpenCode Conectado!**\n\n"
        "⚡ **Motor:** `OpenCode Engine`\n"
        f"📂 **Pasta Atual:** `{current_dir}`\n"
        f"👤 **Usuário Autorizado:** `{update.effective_user.id}`\n\n"
        "**Painel de Controle:**\n"
        "• `/dir` ou `/cd` - Escolher e navegar nas pastas de trabalho\n"
        "• `/cron` - Agendar tarefas automáticas (ex: `/cron 10s envie oi`)\n"
        "• `/model` - Escolher modelos favoritos (DeepSeek, Google, Nvidia)\n"
        "• `/agent` - Alternar modo do agente (`build` ou `plan`)\n"
        "• `/stats` - Ver consumo de tokens e custo da sessão\n"
        "• `/diff` - Ver status e alterações no Git\n"
        "• `/sessions` - Listar e alternar sessões\n"
        "• `/clear` - Iniciar nova sessão limpa\n\n"
        "👇 **Acesse os menus rápidos abaixo:**"
    )
    keyboard = [
        [
            InlineKeyboardButton("📂 Trocar Pasta (Workspace)", callback_data="menu_dir"),
            InlineKeyboardButton("🤖 Escolher Modelo", callback_data="menu_model_main")
        ],
        [
            InlineKeyboardButton("⏰ Tarefas Agendadas (Crons)", callback_data="menu_crons"),
            InlineKeyboardButton("🛠️ Modo Agente", callback_data="menu_agent")
        ],
        [
            InlineKeyboardButton("📊 Ver Estatísticas", callback_data="menu_stats"),
            InlineKeyboardButton("🧹 Limpar Sessão", callback_data="menu_clear")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(msg, parse_mode=ParseMode.MARKDOWN, reply_markup=reply_markup)

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_authorization(update):
        return

    msg = (
        "📖 **Guia Completo de Comandos do OpenCode:**\n\n"
        "⏰ **Tarefas Periódicas e Crons:**\n"
        "• `/cron <intervalo> <tarefa>` — Agenda uma tarefa periódica autônoma!\n"
        "  Exemplos:\n"
        "  - `/cron 10s me mande um oi`\n"
        "  - `/cron 5m verifique se ha novos arquivos`\n"
        "  - `/cron */10 * * * * faca resumo do projeto`\n"
        "• `/cron list` — Lista todos os agendamentos ativos.\n"
        "• `/cron stop all` ou `/cron stop <id>` — Cancela os agendamentos.\n\n"
        "📂 **Pastas e Workspaces:**\n"
        "• `/dir` ou `/cd` — Menu com botões para escolher em qual pasta quer trabalhar.\n"
        "• `/dir <caminho>` ou `/cd <caminho>` — Troca de pasta diretamente (ex: `/cd Telegram`, `/cd ..`).\n\n"
        "🤖 **Modelos e Favoritos:**\n"
        "• `/model` — Menu interativo para escolher seus modelos favoritos.\n"
        "• `/models [filtro]` — Lista todos os modelos disponíveis no OpenCode.\n\n"
        "⚙️ **Controle de Sessão e Agente:**\n"
        "• `/agent` — Alterna entre modo completo (`build`) e planejamento (`plan`).\n"
        "• `/clear` — Inicia uma nova sessão limpa no OpenCode.\n"
        "• `/stats` — Mostra tokens e custo estimado em dólar.\n"
        "• `/diff` — Mostra o status e diffs do Git no projeto."
    )
    await update.message.reply_text(msg, parse_mode=ParseMode.MARKDOWN)

async def dir_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_authorization(update):
        return

    chat_id = update.effective_chat.id
    if context.args:
        target_dir = " ".join(context.args).strip()
        success, reply_msg = agent.set_directory(chat_id, target_dir)
        await update.message.reply_text(reply_msg, parse_mode=ParseMode.MARKDOWN)
        return

    current = agent.get_current_directory(chat_id)
    reply_markup = get_workspace_keyboard(chat_id)
    await update.message.reply_text(
        f"📂 **Pasta de Trabalho Atual:**\n`{current}`\n\n"
        "👇 **Escolha uma pasta abaixo para trabalhar ou use `/cd <nome>`:**",
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=reply_markup
    )

async def model_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_authorization(update):
        return

    chat_id = update.effective_chat.id
    if context.args:
        target_model = " ".join(context.args).strip()
        success, reply_msg = agent.set_model(chat_id, target_model)
        await update.message.reply_text(reply_msg, parse_mode=ParseMode.MARKDOWN)
        return

    info = agent.get_current_model_info(chat_id)
    reply_markup = get_main_models_keyboard()
    await update.message.reply_text(
        f"{info}\n\n👇 **Seus Modelos Favoritos do OpenCode (Clique para ativar):**",
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=reply_markup
    )

async def models_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_authorization(update):
        return

    filter_term = " ".join(context.args).strip().lower() if context.args else ""
    all_models = agent.get_available_models()

    if filter_term:
        filtered = [m for m in all_models if filter_term in m.lower()]
    else:
        filtered = all_models

    if not filtered:
        await update.message.reply_text(f"Nenhum modelo encontrado com o filtro '{filter_term}'.", parse_mode=ParseMode.MARKDOWN)
        return

    by_provider = {}
    for m in filtered:
        prov = m.split("/")[0] if "/" in m else "outros"
        by_provider.setdefault(prov, []).append(m)

    lines = ["📋 **Modelos Disponíveis no OpenCode:**\n"]
    for prov, mlist in by_provider.items():
        lines.append(f"🔹 **{prov.upper()}:**")
        for model in mlist[:12]:
            lines.append(f"  • `{model}`")
        if len(mlist) > 12:
            lines.append(f"  _... e mais {len(mlist) - 12} modelos._")
        lines.append("")

    lines.append("💡 Use `/model` para abrir o menu interativo com botões clicáveis!")
    await send_split_message(update, context, "\n".join(lines), update.effective_chat.id)

async def agent_mode_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_authorization(update):
        return

    chat_id = update.effective_chat.id
    if context.args:
        target_mode = context.args[0].lower()
        success, reply_msg = agent.set_agent_mode(chat_id, target_mode)
        await update.message.reply_text(reply_msg, parse_mode=ParseMode.MARKDOWN)
        return

    current_agent = agent.user_agents.get(chat_id, "build")
    msg = (
        f"🛠️ **Modo do Agente Atual:** `{current_agent}`\n\n"
        "👇 **Escolha o modo de operação desejado:**"
    )
    reply_markup = get_agent_mode_keyboard()
    await update.message.reply_text(msg, parse_mode=ParseMode.MARKDOWN, reply_markup=reply_markup)

async def callback_query_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Trata todos os cliques nos botões interativos do Telegram."""
    query = update.callback_query
    if not await check_authorization(update):
        return

    await query.answer()
    data = query.data
    chat_id = update.effective_chat.id

    if data in ["menu_dir", "menu_dir_refresh"]:
        current = agent.get_current_directory(chat_id)
        await query.edit_message_text(
            f"📂 **Pasta de Trabalho Atual:**\n`{current}`\n\n"
            "👇 **Escolha uma pasta abaixo para trabalhar ou use `/cd <nome>`:**",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=get_workspace_keyboard(chat_id)
        )
    elif data.startswith("setdir_"):
        target_folder = data.replace("setdir_", "")
        success, reply_msg = agent.set_directory(chat_id, target_folder)
        await query.edit_message_text(
            f"{reply_msg}\n\n👇 **Navegar para outra pasta:**",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=get_workspace_keyboard(chat_id)
        )
    elif data == "menu_model_main":
        info = agent.get_current_model_info(chat_id)
        await query.edit_message_text(
            f"{info}\n\n👇 **Seus Modelos Favoritos do OpenCode (Clique para ativar):**",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=get_main_models_keyboard()
        )
    elif data.startswith("favcat_"):
        cat_name = data.replace("favcat_", "")
        title_map = {
            "DeepSeek": "🟣 **Modelos Favoritos - DeepSeek**",
            "Google": "🔵 **Modelos Favoritos - Google**",
            "Nvidia": "🟢 **Modelos Favoritos - Nvidia / Qwen / Llama**",
            "Gratuitos": "🆓 **Modelos Gratuitos (OpenCode Free)**"
        }
        title = title_map.get(cat_name, f"**Modelos Favoritos ({cat_name})**")
        await query.edit_message_text(
            f"{title}\n\n👇 **Clique no modelo desejado para ativar:**",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=get_category_models_keyboard(cat_name, chat_id)
        )
    elif data.startswith("setmod_"):
        model_name = data.replace("setmod_", "")
        success, reply_msg = agent.set_model(chat_id, model_name)
        info = agent.get_current_model_info(chat_id)
        await query.edit_message_text(
            f"{reply_msg}\n\n{info}\n\nO OpenCode usará este modelo nas suas próximas mensagens.",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=get_main_models_keyboard()
        )
    elif data == "menu_agent":
        current_agent = agent.user_agents.get(chat_id, "build")
        await query.edit_message_text(
            f"🛠️ **Modo do Agente Atual:** `{current_agent}`\n\n👇 **Escolha o modo desejado:**",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=get_agent_mode_keyboard()
        )
    elif data.startswith("setagent_"):
        mode_name = data.replace("setagent_", "")
        success, reply_msg = agent.set_agent_mode(chat_id, mode_name)
        await query.edit_message_text(
            f"{reply_msg}\n\nModo de operação atualizado.",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=get_agent_mode_keyboard()
        )
    elif data == "menu_crons":
        jobs_text = scheduler.list_jobs(chat_id)
        await query.message.reply_text(jobs_text, parse_mode=ParseMode.MARKDOWN)
    elif data == "menu_stats":
        stats_text = agent.get_stats(chat_id)
        await query.message.reply_text(stats_text, parse_mode=ParseMode.MARKDOWN)
    elif data == "menu_clear":
        new_sid = agent.reset_session(chat_id)
        await query.message.reply_text(f"🧹 **Sessão limpa!**\nNova sessão OpenCode: `{new_sid}`", parse_mode=ParseMode.MARKDOWN)
    elif data == "menu_all_models":
        all_models = agent.get_available_models()
        lines = [f"• `{m}`" for m in all_models[:30]]
        await query.message.reply_text(
            "📋 **Modelos no OpenCode (Primeiros 30):**\n\n" + "\n".join(lines) + "\n\nPara ativar qualquer um, use `/model <nome>`.",
            parse_mode=ParseMode.MARKDOWN
        )

async def providers_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_authorization(update):
        return
    info = agent.get_providers_info()
    await update.message.reply_text(info, parse_mode=ParseMode.MARKDOWN)

async def git_diff_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_authorization(update):
        return
    diff_text = agent.get_git_diff(update.effective_chat.id)
    await send_split_message(update, context, diff_text, update.effective_chat.id)

async def export_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_authorization(update):
        return
    chat_id = update.effective_chat.id
    export_data = agent.export_session_markdown(chat_id)
    if not export_data:
        await update.message.reply_text("Nenhum dado de sessão disponível para exportação.", parse_mode=ParseMode.MARKDOWN)
        return

    file_bytes = io.BytesIO(export_data.encode("utf-8"))
    file_bytes.name = f"opencode_session_{chat_id}.json"
    await context.bot.send_document(
        chat_id=chat_id,
        document=file_bytes,
        caption="📄 Exportação da sessão atual do OpenCode."
    )

async def sessions_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_authorization(update):
        return

    chat_id = update.effective_chat.id
    args = context.args

    if args:
        target_sid = args[0].strip()
        agent.switch_session(chat_id, target_sid)
        await update.message.reply_text(f"✅ Sessão alternada para: `{target_sid}`", parse_mode=ParseMode.MARKDOWN)
        return

    session_list = agent.list_all_sessions()
    current_sid = agent.sessions.get(chat_id, "Nenhuma ativa")

    if not session_list:
        await update.message.reply_text(f"Nenhuma sessão anterior encontrada.\nSessão atual: `{current_sid}`", parse_mode=ParseMode.MARKDOWN)
        return

    lines = ["📂 **Sessões do OpenCode:**\n"]
    for s in session_list[:10]:
        sid = s.get("id", "sem-id")
        title = s.get("title", "Sem título")
        marker = "👉 " if sid == current_sid else "• "
        lines.append(f"{marker}`{sid}`: {title}")

    lines.append("\nPara trocar de sessão, envie: `/session <ID>`")
    await update.message.reply_text("\n".join(lines), parse_mode=ParseMode.MARKDOWN)

async def clear_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_authorization(update):
        return
    new_sid = agent.reset_session(update.effective_chat.id)
    await update.message.reply_text(f"🧹 **Sessão limpa!**\nNova sessão iniciada: `{new_sid}`", parse_mode=ParseMode.MARKDOWN)

async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_authorization(update):
        return
    stats_text = agent.get_stats(update.effective_chat.id)
    await update.message.reply_text(stats_text, parse_mode=ParseMode.MARKDOWN)

async def crons_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_authorization(update):
        return

    chat_id = update.effective_chat.id
    args = context.args

    if not args:
        jobs_text = scheduler.list_jobs(chat_id)
        await update.message.reply_text(jobs_text, parse_mode=ParseMode.MARKDOWN)
        return

    first_arg = args[0].lower()

    if first_arg in ["stop", "cancel", "delete", "remove", "parar"]:
        target = args[1] if len(args) > 1 else "all"
        msg = scheduler.cancel(target)
        await update.message.reply_text(msg, parse_mode=ParseMode.MARKDOWN)
        return

    if first_arg in ["list", "listar"]:
        jobs_text = scheduler.list_jobs(chat_id)
        await update.message.reply_text(jobs_text, parse_mode=ParseMode.MARKDOWN)
        return

    # Exemplo: /cron 10s mande um oi
    time_expr = args[0]
    instruction = " ".join(args[1:]).strip()

    if not instruction:
        await update.message.reply_text(
            "⚠️ Formato inválido.\n\nExemplo de uso:\n• `/cron 10s envie um oi`\n• `/cron 5m verifique o git status`\n• `/cron stop all`",
            parse_mode=ParseMode.MARKDOWN
        )
        return

    success, reply_msg = scheduler.schedule(time_expr, instruction, chat_id)
    await update.message.reply_text(reply_msg, parse_mode=ParseMode.MARKDOWN)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_authorization(update):
        return

    user_text = update.message.text.strip()
    chat_id = update.effective_chat.id
    user_lower = user_text.lower()

    # 1. Detecção de comando de parada de crons em linguagem natural
    if any(user_lower.startswith(w) for w in ["pare", "parar", "cancelar", "stop", "cancela", "chega", "para"]):
        if scheduler.jobs_metadata:
            msg = scheduler.cancel("all")
            await update.message.reply_text(f"🛑 {msg}", parse_mode=ParseMode.MARKDOWN)
            return

    # 2. Detecção de consulta de crons em linguagem natural
    if any(q in user_lower for q in ["quais crons", "quais tarefas", "listar crons", "ver crons", "crons rodando"]):
        jobs_text = scheduler.list_jobs(chat_id)
        await update.message.reply_text(jobs_text, parse_mode=ParseMode.MARKDOWN)
        return

    # 3. Detecção inteligente de agendamento em linguagem natural
    # Ex: "mande um oi a cada 10 segundos ate que eu diga para parar"
    match_cron_nl = re.search(
        r"(?:a cada|de|intervalo de)\s+(\d+)\s*(segundos?|minutos?|horas?|s|m|h)",
        user_lower
    )
    if match_cron_nl and ("mande" in user_lower or "envie" in user_lower or "notifique" in user_lower or "execute" in user_lower or "faca" in user_lower or "faça" in user_lower or "avise" in user_lower or "olhe" in user_lower):
        num = match_cron_nl.group(1)
        unit = match_cron_nl.group(2)
        unit_char = "s" if "seg" in unit or unit == "s" else ("m" if "min" in unit or unit == "m" else "h")
        time_expr = f"{num}{unit_char}"
        
        # Extrai a instrução limpando a expressão temporal
        cleaned_instruction = re.sub(r"(?:a cada|de|intervalo de)\s+\d+\s*(?:segundos?|minutos?|horas?|s|m|h)", "", user_text, flags=re.IGNORECASE)
        cleaned_instruction = re.sub(r"(?:ate que|até que|ate eu|até eu).*$", "", cleaned_instruction, flags=re.IGNORECASE).strip()
        if not cleaned_instruction:
            cleaned_instruction = "Enviar notificação de status periódica"

        success, sched_msg = scheduler.schedule(time_expr, cleaned_instruction, chat_id)
        if success:
            await update.message.reply_text(
                f"{sched_msg}\n\n💡 **Dica:** Para parar a qualquer momento, basta me enviar **'pare'** ou **/cron stop all**!",
                parse_mode=ParseMode.MARKDOWN
            )
            return

    # Processamento padrão via OpenCode (Assíncrono e concorrente)
    await context.bot.send_chat_action(chat_id=chat_id, action=ChatAction.TYPING)

    async def on_action_update(action_text: str):
        await context.bot.send_chat_action(chat_id=chat_id, action=ChatAction.TYPING)

    response_text = await agent.process_message(
        user_text=user_text,
        chat_id=chat_id,
        on_action=on_action_update
    )

    await send_split_message(update, context, response_text, chat_id)

async def on_cron_triggered(instruction: str, chat_id: int, job_id: str):
    """Callback disparado autonomamente em segundo plano pelo scheduler."""
    print(f"[Scheduler Disparado] Job '{job_id}' para chat {chat_id}: {instruction}")
    global active_telegram_app
    if not active_telegram_app:
        return

    instruction_lower = instruction.lower().strip()
    instruction_clean = re.sub(r"^(me\s+)?(envie|mande|fale|diga)\s+", "", instruction_lower).strip()
    
    # Se for uma saudação/mensagem simples e direta (ex: "mande um oi", "envie oi")
    if instruction_clean in ["um oi", "oi", "ola", "olá", "teste", "ping", "alerta"]:
        try:
            await active_telegram_app.bot.send_message(
                chat_id=chat_id,
                text="👋 **Oi!** (Notificação periódica ativa)",
                parse_mode=ParseMode.MARKDOWN
            )
        except Exception as e:
            print(f"[Scheduler] Erro ao enviar mensagem rápida: {e}")
        return

    # Para tarefas complexas que exigem inteligência, passa pelo OpenCode
    prompt = f"[NOTIFICAÇÃO AUTÔNOMA AGENDADA - JOB {job_id}]: Execute a instrução e envie o resumo: {instruction}"
    result = await agent.process_message(prompt, chat_id)
    
    chunks = [result[i:i+4000] for i in range(0, len(result), 4000)]
    for chunk in chunks:
        try:
            await active_telegram_app.bot.send_message(
                chat_id=chat_id,
                text=f"⏰ **[Alerta Agendado - `{job_id}`]**\n\n{chunk}",
                parse_mode=ParseMode.MARKDOWN
            )
        except Exception:
            await active_telegram_app.bot.send_message(
                chat_id=chat_id,
                text=f"⏰ [Alerta Agendado - {job_id}]\n\n{chunk}"
            )

async def on_post_init(application):
    """Registra a lista completa de comandos no menu '/' do Telegram."""
    global active_telegram_app
    active_telegram_app = application

    commands = [
        BotCommand("cron", "Agendar tarefas e mensagens autônomas"),
        BotCommand("dir", "Ver e alternar pasta de trabalho"),
        BotCommand("cd", "Navegar para uma pasta específica"),
        BotCommand("model", "Menu interativo de modelos favoritos"),
        BotCommand("models", "Listar todos os modelos do OpenCode"),
        BotCommand("agent", "Alternar modo (build / plan)"),
        BotCommand("stats", "Ver consumo de tokens e custo da sessão"),
        BotCommand("diff", "Ver status e alterações do Git"),
        BotCommand("sessions", "Listar ou trocar sessões"),
        BotCommand("clear", "Iniciar nova sessão limpa"),
        BotCommand("help", "Guia completo de ajuda e comandos"),
    ]
    try:
        await application.bot.set_my_commands(commands)
        print("[Bot] Menu completo de comandos '/' registrado no Telegram com sucesso!")
    except Exception as e:
        print(f"[Bot] Aviso ao registrar comandos no menu: {e}")

    scheduler.set_callback(on_cron_triggered)
    scheduler.start()

def main():
    if not TELEGRAM_BOT_TOKEN:
        print("[Bot] Erro: TELEGRAM_BOT_TOKEN não encontrado no arquivo .env!")
        return

    print("[Bot] Iniciando Bot do Telegram conectado ao OpenCode...")
    print(f"[Bot] Diretorio monitorado: {Path(__file__).resolve().parent.parent}")
    
    app = (
        ApplicationBuilder()
        .token(TELEGRAM_BOT_TOKEN)
        .concurrent_updates(True)
        .post_init(on_post_init)
        .build()
    )

    app.add_handler(CommandHandler("start", start_command, block=False))
    app.add_handler(CommandHandler("help", help_command, block=False))
    app.add_handler(CommandHandler("dir", dir_command, block=False))
    app.add_handler(CommandHandler("workspace", dir_command, block=False))
    app.add_handler(CommandHandler("cd", dir_command, block=False))
    app.add_handler(CommandHandler("model", model_command, block=False))
    app.add_handler(CommandHandler("models", models_command, block=False))
    app.add_handler(CommandHandler("agent", agent_mode_command, block=False))
    app.add_handler(CommandHandler("providers", providers_command, block=False))
    app.add_handler(CommandHandler("auth", providers_command, block=False))
    app.add_handler(CommandHandler("diff", git_diff_command, block=False))
    app.add_handler(CommandHandler("git", git_diff_command, block=False))
    app.add_handler(CommandHandler("export", export_command, block=False))
    app.add_handler(CommandHandler("session", sessions_command, block=False))
    app.add_handler(CommandHandler("sessions", sessions_command, block=False))
    app.add_handler(CommandHandler("clear", clear_command, block=False))
    app.add_handler(CommandHandler("reset", clear_command, block=False))
    app.add_handler(CommandHandler("new", clear_command, block=False))
    app.add_handler(CommandHandler("stats", stats_command, block=False))
    app.add_handler(CommandHandler("cost", stats_command, block=False))
    app.add_handler(CommandHandler("cron", crons_command, block=False))
    app.add_handler(CommandHandler("crons", crons_command, block=False))
    app.add_handler(CommandHandler("schedule", crons_command, block=False))
    app.add_handler(CallbackQueryHandler(callback_query_handler, block=False))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message, block=False))

    print("[Bot] Bot ativo via Long Polling Concorrente! Aguardando mensagens...")
    print("[Bot] Pressione Ctrl+C nesta janela para encerrar.")
    app.run_polling()

if __name__ == "__main__":
    main()
