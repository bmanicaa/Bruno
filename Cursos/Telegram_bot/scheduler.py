import re
import json
from pathlib import Path
from typing import Dict, Any, List, Optional, Callable, Tuple
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger

STORAGE_FILE = Path(__file__).resolve().parent / "crons.json"

class AgentScheduler:
    def __init__(self):
        self.scheduler = AsyncIOScheduler()
        self.jobs_metadata: Dict[str, Dict[str, Any]] = {}
        self.execution_callback: Optional[Callable] = None

    def set_callback(self, callback: Callable):
        """Define a função assíncrona chamada a cada disparo: callback(instruction, chat_id, job_id)."""
        self.execution_callback = callback

    def start(self):
        if not self.scheduler.running:
            try:
                self.scheduler.start()
                self._load_jobs()
                print("[Scheduler] Motor de agendamento (Crons & Intervalos) ativo!")
            except Exception as e:
                print(f"[Scheduler] Aviso ao iniciar agendador: {e}")

    def _load_jobs(self):
        if STORAGE_FILE.exists():
            try:
                with open(STORAGE_FILE, "r", encoding="utf-8") as f:
                    self.jobs_metadata = json.load(f)
                for job_id, data in list(self.jobs_metadata.items()):
                    self._add_job_to_engine(job_id, data["expression"], data["instruction"], data["chat_id"])
            except Exception as e:
                print(f"[Scheduler] Erro ao carregar crons salvos: {e}")

    def _save_jobs(self):
        try:
            with open(STORAGE_FILE, "w", encoding="utf-8") as f:
                json.dump(self.jobs_metadata, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"[Scheduler] Erro ao salvar crons: {e}")

    def _parse_trigger(self, expr: str):
        """Identifica se a expressão é um intervalo (ex: 10s, 5m, 1h) ou um cron clássico (ex: */5 * * * *)."""
        expr_clean = expr.strip().lower()
        
        # Padrões de intervalo (ex: 10s, 10 seg, 10 segundos, 5m, 5 min, 1h)
        match_sec = re.match(r"^(\d+)\s*(s|sec|seg|segundos?|seconds?)$", expr_clean)
        if match_sec:
            seconds = int(match_sec.group(1))
            return IntervalTrigger(seconds=max(5, seconds)), f"a cada {seconds} segundos"

        match_min = re.match(r"^(\d+)\s*(m|min|minutos?|minutes?)$", expr_clean)
        if match_min:
            minutes = int(match_min.group(1))
            return IntervalTrigger(minutes=minutes), f"a cada {minutes} minutos"

        match_hour = re.match(r"^(\d+)\s*(h|hrs?|horas?|hours?)$", expr_clean)
        if match_hour:
            hours = int(match_hour.group(1))
            return IntervalTrigger(hours=hours), f"a cada {hours} horas"

        # Se tiver apenas número puro (ex: "10"), assume segundos se <= 60 ou minutos
        if expr_clean.isdigit():
            num = int(expr_clean)
            return IntervalTrigger(seconds=num), f"a cada {num} segundos"

        # Caso contrário, tenta como expressão Cron clássica de 5 campos
        try:
            return CronTrigger.from_crontab(expr), f"cron ({expr})"
        except Exception as e:
            raise ValueError(f"Formato inválido. Use intervalos como '10s', '5m', '1h' ou crons como '*/5 * * * *'. Detalhe: {e}")

    def _add_job_to_engine(self, job_id: str, expression: str, instruction: str, chat_id: int):
        trigger, _ = self._parse_trigger(expression)
        
        async def job_wrapper():
            if self.execution_callback:
                try:
                    await self.execution_callback(instruction, chat_id, job_id)
                except Exception as e:
                    print(f"[Scheduler] Erro ao executar job '{job_id}': {e}")

        self.scheduler.add_job(
            job_wrapper,
            trigger=trigger,
            id=job_id,
            max_instances=5,
            misfire_grace_time=30,
            replace_existing=True
        )

    def schedule(self, expression: str, instruction: str, chat_id: int, job_id: Optional[str] = None) -> Tuple[bool, str]:
        """Agenda uma nova tarefa periódica ou cronológica."""
        try:
            trigger, readable = self._parse_trigger(expression)
            jid = job_id or f"cron_{len(self.jobs_metadata) + 1}"
            
            self._add_job_to_engine(jid, expression, instruction, chat_id)
            
            self.jobs_metadata[jid] = {
                "expression": expression,
                "readable": readable,
                "instruction": instruction,
                "chat_id": chat_id
            }
            self._save_jobs()
            return True, f"✅ Tarefa periódica agendada com sucesso!\n\n• **ID:** `{jid}`\n• **Frequência:** `{readable}`\n• **Instrução:** {instruction}"
        except Exception as e:
            return False, f"⚠️ Erro ao agendar tarefa: {str(e)}"

    def list_jobs(self, chat_id: Optional[int] = None) -> str:
        """Retorna a lista de tarefas agendadas."""
        if not self.jobs_metadata:
            return "📭 Nenhuma tarefa agendada ou cron ativo no momento."
            
        lines = ["📅 **Tarefas Agendadas Ativas:**\n"]
        for jid, data in self.jobs_metadata.items():
            if chat_id is None or data.get("chat_id") == chat_id:
                readable = data.get("readable", data.get("expression"))
                lines.append(f"• **ID:** `{jid}` | **Frequência:** `{readable}`\n  👉 **Instrução:** {data['instruction']}")
        
        lines.append("\nPara cancelar uma tarefa, use: `/cron stop <ID>` ou `/cron stop all`")
        return "\n".join(lines)

    def cancel(self, job_id: str) -> str:
        """Cancela uma tarefa específica ou todas."""
        if job_id.lower() in ["all", "todas", "tudo"]:
            count = len(self.jobs_metadata)
            for jid in list(self.jobs_metadata.keys()):
                try:
                    self.scheduler.remove_job(jid)
                except Exception:
                    pass
            self.jobs_metadata.clear()
            self._save_jobs()
            return f"✅ Todas as {count} tarefas agendadas foram canceladas com sucesso."

        if job_id in self.jobs_metadata:
            try:
                self.scheduler.remove_job(job_id)
            except Exception:
                pass
            del self.jobs_metadata[job_id]
            self._save_jobs()
            return f"✅ Tarefa `{job_id}` cancelada e removida com sucesso."
        return f"⚠️ Tarefa com ID `{job_id}` não encontrada."

from typing import Tuple
scheduler = AgentScheduler()
