import os
import subprocess
import time
import json
import requests
import asyncio
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SETTINGS_FILE = Path(__file__).resolve().parent / "user_settings.json"

class OpenCodeAgent:
    def __init__(self, base_url: str = "http://127.0.0.1:4096"):
        self.base_url = base_url.rstrip("/")
        self.sessions: Dict[int, str] = {} # chat_id -> session_id
        self.session_stats: Dict[int, Dict[str, Any]] = {} # chat_id -> last info
        self.user_models: Dict[int, Dict[str, str]] = {} # chat_id -> {"providerID": ..., "modelID": ...}
        self.user_agents: Dict[int, str] = {} # chat_id -> "build" | "plan"
        self.user_workspaces: Dict[int, str] = {} # chat_id -> absolute path
        self._cached_models: List[str] = []
        self._load_persisted_settings()
        self._ensure_server_running()

    def _load_persisted_settings(self):
        """Carrega configurações persistentes (modelo, modo e pasta de trabalho selecionados)."""
        if SETTINGS_FILE.exists():
            try:
                with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                models_data = data.get("models", {})
                for k, v in models_data.items():
                    self.user_models[int(k)] = v
                agents_data = data.get("agents", {})
                for k, v in agents_data.items():
                    self.user_agents[int(k)] = v
                workspaces_data = data.get("workspaces", {})
                for k, v in workspaces_data.items():
                    self.user_workspaces[int(k)] = v
                print(f"[OpenCodeAgent] Configurações carregadas do disco: {data}")
            except Exception as e:
                print(f"[OpenCodeAgent] Erro ao carregar user_settings.json: {e}")

    def _save_persisted_settings(self):
        """Salva as configurações do usuário no disco para persistirem entre reinicializações."""
        try:
            data = {
                "models": {str(k): v for k, v in self.user_models.items()},
                "agents": {str(k): v for k, v in self.user_agents.items()},
                "workspaces": {str(k): v for k, v in self.user_workspaces.items()}
            }
            with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"[OpenCodeAgent] Erro ao salvar user_settings.json: {e}")

    def _ensure_server_running(self):
        """Verifica se o servidor headless do OpenCode está ativo; se não, inicia em background."""
        try:
            r = requests.get(f"{self.base_url}/api/health", timeout=2)
            if r.status_code == 200 and r.json().get("healthy"):
                print("[OpenCode] Servidor OpenCode ja esta ativo e pronto na porta 4096.")
                return
        except Exception:
            pass

        print("[OpenCode] Iniciando servidor OpenCode em background...")
        try:
            subprocess.Popen(
                ["opencode.cmd", "serve", "--port", "4096"],
                cwd=str(PROJECT_ROOT),
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                shell=True
            )
            for _ in range(10):
                time.sleep(0.5)
                try:
                    r = requests.get(f"{self.base_url}/api/health", timeout=1)
                    if r.status_code == 200:
                        print("[OpenCode] Conectado ao servidor OpenCode com sucesso!")
                        return
                except Exception:
                    continue
        except Exception as e:
            print(f"⚠️ Erro ao iniciar opencode serve: {e}")

    def get_current_directory(self, chat_id: int) -> str:
        """Retorna o diretório de trabalho ativo do usuário (padrão: pasta Project)."""
        saved = self.user_workspaces.get(chat_id)
        if saved and Path(saved).exists() and Path(saved).is_dir():
            return saved
        # Se o caminho antigo salvo não existir mais (ex: repositório movido), reancora no novo PROJECT_ROOT
        return str(PROJECT_ROOT)

    def set_directory(self, chat_id: int, new_path: str) -> Tuple[bool, str]:
        """Altera a pasta de trabalho ativa e inicia uma nova sessão no OpenCode."""
        current = Path(self.get_current_directory(chat_id))
        new_path_clean = new_path.strip()

        # Resolução de caminho
        if new_path_clean == "..":
            target = current.parent
        elif new_path_clean in [".", "project", "raiz", "root"]:
            target = PROJECT_ROOT
        elif new_path_clean.lower() in ["telegram", "pasta telegram"]:
            target = PROJECT_ROOT / "Telegram"
        elif Path(new_path_clean).is_absolute():
            target = Path(new_path_clean)
        else:
            # Tenta relativo ao diretório atual primeiro, depois ao PROJECT_ROOT
            cand1 = (current / new_path_clean).resolve()
            cand2 = (PROJECT_ROOT / new_path_clean).resolve()
            target = cand1 if cand1.exists() else cand2

        if not target.exists() or not target.is_dir():
            return False, f"⚠️ O diretório `{new_path}` não foi encontrado ou não é uma pasta válida."

        # Salva o novo workspace
        self.user_workspaces[chat_id] = str(target.resolve())
        self._save_persisted_settings()

        # Reseta a sessão para criar uma nova no novo diretório
        new_sid = self.reset_session(chat_id)

        # Lista pastas filhas para conveniência
        subdirs = [p.name for p in target.iterdir() if p.is_dir() and not p.name.startswith(".")]

        subdirs_text = ""
        if subdirs:
            subdirs_text = f"\n📁 **Subpastas disponíveis:** " + ", ".join([f"`{d}`" for d in subdirs[:8]])

        return True, (
            f"📂 **Workspace Alterado com Sucesso!**\n\n"
            f"📍 **Novo Diretório:** `{target}`\n"
            f"🔄 **Nova Sessão:** `{new_sid}`"
            f"{subdirs_text}\n\n"
            "O OpenCode agora operará exclusivamente dentro deste contexto."
        )

    def list_subdirectories(self, chat_id: int) -> List[str]:
        """Retorna a lista de subpastas do diretório atual."""
        current = Path(self.get_current_directory(chat_id))
        try:
            return [p.name for p in current.iterdir() if p.is_dir() and not p.name.startswith(".")]
        except Exception:
            return []

    def get_or_create_session(self, chat_id: int) -> str:
        """Obtém o sessionID existente para o chat ou cria uma nova sessão ancorada na pasta atual."""
        if chat_id in self.sessions:
            return self.sessions[chat_id]

        active_dir = self.get_current_directory(chat_id)
        try:
            payload = {
                "title": f"Telegram Session - {Path(active_dir).name}",
                "directory": active_dir
            }
            r = requests.post(f"{self.base_url}/session", json=payload, timeout=10)
            if r.status_code == 200:
                data = r.json()
                session_id = data.get("id")
                self.sessions[chat_id] = session_id
                return session_id
        except Exception as e:
            print(f"[OpenCodeAgent] Erro ao criar sessão: {e}")

        return f"fallback_{chat_id}"

    def reset_session(self, chat_id: int) -> str:
        """Cria uma nova sessão limpa no OpenCode."""
        if chat_id in self.sessions:
            del self.sessions[chat_id]
        if chat_id in self.session_stats:
            del self.session_stats[chat_id]
        return self.get_or_create_session(chat_id)

    def switch_session(self, chat_id: int, session_id: str) -> bool:
        """Alterna para uma sessão existente."""
        self.sessions[chat_id] = session_id
        return True

    def list_all_sessions(self) -> List[Dict[str, Any]]:
        """Lista todas as sessões salvas no OpenCode."""
        try:
            r = requests.get(f"{self.base_url}/session", timeout=5)
            if r.status_code == 200:
                return r.json()
        except Exception as e:
            print(f"[OpenCodeAgent] Erro ao listar sessões: {e}")
        return []

    def get_available_models(self) -> List[str]:
        """Obtém a lista de todos os modelos disponíveis no OpenCode."""
        if self._cached_models:
            return self._cached_models
        try:
            result = subprocess.run(
                ["opencode.cmd", "models"],
                capture_output=True,
                text=True,
                timeout=10,
                shell=True
            )
            if result.returncode == 0:
                models = [m.strip() for m in result.stdout.strip().split("\n") if m.strip()]
                self._cached_models = models
                return models
        except Exception as e:
            print(f"[OpenCodeAgent] Erro ao buscar modelos: {e}")
        return [
            "deepseek/deepseek-v4-flash",
            "deepseek/deepseek-v4-pro",
            "deepseek/deepseek-chat",
            "deepseek/deepseek-reasoner",
            "google/gemma-4-31b-it",
            "google/gemini-2.5-pro",
            "google/gemini-3.7-flash"
        ]

    def set_model(self, chat_id: int, model_name: str) -> Tuple[bool, str]:
        """Define e PERSISTE o modelo ativo para o usuário."""
        available = self.get_available_models()
        model_name = model_name.strip().lower()

        matched = None
        for m in available:
            if m.lower() == model_name:
                matched = m
                break
        
        if not matched:
            for m in available:
                if model_name in m.lower():
                    matched = m
                    break

        if not matched:
            return False, f"Modelo '{model_name}' não encontrado. Use `/models` para ver a lista de modelos disponíveis."

        if "/" in matched:
            provider, model_id = matched.split("/", 1)
        else:
            provider, model_id = "deepseek", matched

        self.user_models[chat_id] = {
            "providerID": provider,
            "modelID": model_id
        }
        self._save_persisted_settings()
        return True, f"✅ Modelo alterado e salvo como padrão: `{matched}`"

    def get_current_model_info(self, chat_id: int) -> str:
        """Retorna informações do modelo atual configurado para o chat."""
        active = self.user_models.get(chat_id)
        if not active and self.user_models:
            active = list(self.user_models.values())[0]

        if active:
            model_str = f"{active['providerID']}/{active['modelID']}"
        else:
            model_str = "deepseek/deepseek-v4-flash (Padrão)"

        agent_mode = self.user_agents.get(chat_id, "build")
        current_dir = self.get_current_directory(chat_id)

        return (
            f"🤖 **Modelo Ativo Permanente:** `{model_str}`\n"
            f"🛠️ **Modo do Agente:** `{agent_mode}`\n"
            f"📂 **Pasta Atual (Workspace):** `{current_dir}`\n\n"
            "💡 O modelo e a pasta ficam **salvos permanentemente** no seu perfil."
        )

    def set_agent_mode(self, chat_id: int, mode: str) -> Tuple[bool, str]:
        """Define e PERSISTE o modo do agente (build, plan)."""
        mode = mode.strip().lower()
        if mode not in ["build", "plan"]:
            return False, "Modos disponíveis: `build` (execução completa) ou `plan` (somente planejamento)."
        self.user_agents[chat_id] = mode
        self._save_persisted_settings()
        return True, f"✅ Modo do agente alterado para: `{mode}`"

    def get_providers_info(self) -> str:
        """Lista provedores de IA configurados."""
        try:
            result = subprocess.run(
                ["opencode.cmd", "providers", "list"],
                capture_output=True,
                text=True,
                timeout=10,
                shell=True
            )
            if result.returncode == 0:
                return f"🔑 **Provedores e Credenciais no OpenCode:**\n```\n{result.stdout.strip()}\n```"
        except Exception as e:
            return f"Erro ao consultar provedores: {e}"
        return "Provedores ativos: DeepSeek, Google, Nvidia."

    def get_git_diff(self, chat_id: int) -> str:
        """Executa git status e diff no diretório ativo."""
        active_dir = self.get_current_directory(chat_id)
        try:
            status = subprocess.run(
                ["git", "status", "--short"],
                cwd=active_dir,
                capture_output=True,
                text=True,
                timeout=10
            ).stdout.strip()

            diff = subprocess.run(
                ["git", "diff", "--stat"],
                cwd=active_dir,
                capture_output=True,
                text=True,
                timeout=10
            ).stdout.strip()

            lines = [f"📊 **Status do Git em:** `{active_dir}`"]
            if status:
                lines.append(f"**Arquivos Modificados:**\n```\n{status}\n```")
            else:
                lines.append("✅ Nenhuma alteração pendente (working tree clean).")

            if diff:
                lines.append(f"**Resumo de Diffs:**\n```\n{diff}\n```")

            return "\n\n".join(lines)
        except Exception as e:
            return f"Erro ao verificar Git: {e}"

    def get_stats(self, chat_id: int) -> str:
        """Retorna telemetria detalhada da sessão atual."""
        stats = self.session_stats.get(chat_id)
        session_id = self.sessions.get(chat_id, "Nenhuma")
        active_dir = self.get_current_directory(chat_id)

        if not stats:
            return (
                f"📊 **Estatísticas da Sessão:**\n\n"
                f"• **ID da Sessão:** `{session_id}`\n"
                f"• **Pasta de Trabalho:** `{active_dir}`\n"
                f"• Nenhuma mensagem processada nesta sessão ainda."
            )

        tokens = stats.get("tokens", {})
        cost = stats.get("cost", 0.0)
        model = stats.get("modelID", "deepseek-chat")
        provider = stats.get("providerID", "deepseek")
        mode = stats.get("mode", "build")
        agent_type = stats.get("agent", "build")

        return (
            "📊 **Estatísticas da Sessão Atual (OpenCode):**\n\n"
            f"• **Pasta de Trabalho:** `{active_dir}`\n"
            f"• **Sessão:** `{session_id}`\n"
            f"• **Modelo:** `{provider}/{model}`\n"
            f"• **Modo / Agente:** `{mode}` / `{agent_type}`\n"
            f"• **Custo Acumulado:** `${cost:.6f} USD`\n\n"
            "🔢 **Consumo de Tokens:**\n"
            f"• **Total:** `{tokens.get('total', 0):,}`\n"
            f"• **Entrada (Input):** `{tokens.get('input', 0):,}`\n"
            f"• **Saída (Output):** `{tokens.get('output', 0):,}`\n"
            f"• **Raciocínio (Reasoning):** `{tokens.get('reasoning', 0):,}`\n"
            f"• **Cache Lido:** `{tokens.get('cache', {}).get('read', 0):,}`\n"
            f"• **Cache Gravado:** `{tokens.get('cache', {}).get('write', 0):,}`"
        )

    def export_session_markdown(self, chat_id: int) -> Optional[str]:
        """Exporta os dados da sessão como texto formatado."""
        session_id = self.sessions.get(chat_id)
        if not session_id:
            return None

        try:
            r = requests.get(f"{self.base_url}/session/{session_id}", timeout=10)
            if r.status_code == 200:
                data = r.json()
                return json.dumps(data, indent=2, ensure_ascii=False)
        except Exception:
            pass
        return None

    def _post_message_sync(self, url: str, payload: dict, chat_id: int) -> Tuple[bool, str]:
        """Executa a chamada HTTP síncrona dentro de uma thread separada para não bloquear o loop do Telegram."""
        try:
            r = requests.post(url, json=payload, timeout=180)
            if r.status_code != 200:
                return False, f"⚠️ Erro no OpenCode (Status {r.status_code}): {r.text[:400]}"

            data = r.json()
            if "info" in data:
                self.session_stats[chat_id] = data["info"]

            parts = data.get("parts", [])
            text_outputs = [part.get("text", "") for part in parts if part.get("type") == "text"]
            final_text = "\n\n".join(filter(None, text_outputs)).strip()
            return True, final_text or "✅ Tarefa processada pelo OpenCode com sucesso."

        except requests.Timeout:
            return False, "⏳ O OpenCode está demorando para responder (tempo limite excedido)."
        except Exception as e:
            return False, f"⚠️ Erro ao comunicar com o OpenCode: {str(e)}"

    async def process_message(self, user_text: str, chat_id: int, on_action: Optional[Any] = None) -> str:
        self._ensure_server_running()
        session_id = self.get_or_create_session(chat_id)
        active_dir = self.get_current_directory(chat_id)

        if on_action:
            await on_action(f"🔍 OpenCode processando em '{Path(active_dir).name}'...")

        # Força explicitamente a instrução de diretório ativo para o OpenCode
        contextualized_text = (
            f"[INSTRUÇÃO MANDATÓRIA DE DIRETÓRIO: O diretório de trabalho atual onde você DEVE operar é estritamente '{active_dir}'. "
            f"Qualquer criação de arquivo, leitura, comando de terminal ou referência a 'root' ou 'raiz' DEVE ser feita estritamente dentro desta pasta ({active_dir}). "
            f"Nunca crie arquivos fora desta pasta de trabalho].\n\n"
            f"{user_text}"
        )

        url = f"{self.base_url}/session/{session_id}/message"
        payload: Dict[str, Any] = {
            "parts": [
                {
                    "type": "text",
                    "text": contextualized_text
                }
            ]
        }

        # Injeta modelo persistido do usuário
        if chat_id in self.user_models:
            payload["model"] = self.user_models[chat_id]
        elif self.user_models:
            payload["model"] = list(self.user_models.values())[0]

        # Injeta modo de agente persistido
        if chat_id in self.user_agents:
            payload["agent"] = self.user_agents[chat_id]

        success, result_text = await asyncio.to_thread(self._post_message_sync, url, payload, chat_id)
        return result_text
