import os
import subprocess
from pathlib import Path
from typing import Dict, Any, Optional

PROJECT_ROOT = Path(__file__).resolve().parent.parent

def resolve_path(relative_path: str) -> Path:
    target = (PROJECT_ROOT / relative_path).resolve()
    # Segurança básica para não escapar da pasta do projeto
    try:
        target.relative_to(PROJECT_ROOT)
    except ValueError:
        raise PermissionError(f"Acesso negado fora do diretório do projeto: {relative_path}")
    return target

def read_file(relative_path: str, start_line: Optional[int] = None, end_line: Optional[int] = None) -> str:
    """Lê o conteúdo de um arquivo do projeto."""
    try:
        path = resolve_path(relative_path)
        if not path.exists() or not path.is_file():
            return f"Erro: Arquivo '{relative_path}' não encontrado."
        
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            lines = f.readlines()
        
        if start_line is not None or end_line is not None:
            start = max(1, start_line or 1) - 1
            end = min(len(lines), end_line or len(lines))
            selected = lines[start:end]
            numbered = [f"{i + start + 1}: {line}" for i, line in enumerate(selected)]
            return "".join(numbered)
        
        return "".join(lines)
    except Exception as e:
        return f"Erro ao ler arquivo: {str(e)}"

def write_file(relative_path: str, content: str) -> str:
    """Cria ou sobrescreve um arquivo dentro do projeto."""
    try:
        path = resolve_path(relative_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        return f"Sucesso: Arquivo '{relative_path}' salvo com sucesso ({len(content)} caracteres)."
    except Exception as e:
        return f"Erro ao escrever arquivo: {str(e)}"

def edit_file(relative_path: str, target_content: str, replacement_content: str) -> str:
    """Substitui um trecho exato de texto dentro de um arquivo."""
    try:
        path = resolve_path(relative_path)
        if not path.exists() or not path.is_file():
            return f"Erro: Arquivo '{relative_path}' não encontrado."
        
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            text = f.read()
            
        if target_content not in text:
            return f"Erro: O trecho a ser substituído não foi encontrado no arquivo '{relative_path}'."
            
        new_text = text.replace(target_content, replacement_content, 1)
        with open(path, "w", encoding="utf-8") as f:
            f.write(new_text)
            
        return f"Sucesso: Arquivo '{relative_path}' modificado com sucesso."
    except Exception as e:
        return f"Erro ao editar arquivo: {str(e)}"

def list_directory(relative_path: str = "") -> str:
    """Lista pastas e arquivos de um diretório dentro do projeto."""
    try:
        path = resolve_path(relative_path)
        if not path.exists() or not path.is_dir():
            return f"Erro: Diretório '{relative_path}' não encontrado."
            
        items = []
        for item in sorted(path.iterdir()):
            prefix = "📁" if item.is_dir() else "📄"
            rel = item.relative_to(PROJECT_ROOT)
            items.append(f"{prefix} {rel}")
            
        if not items:
            return f"Diretório '{relative_path}' está vazio."
            
        return "\n".join(items)
    except Exception as e:
        return f"Erro ao listar diretório: {str(e)}"

def run_command(command: str) -> str:
    """Executa um comando no terminal (PowerShell) dentro da raiz do projeto."""
    try:
        result = subprocess.run(
            ["powershell", "-NoProfile", "-Command", command],
            cwd=str(PROJECT_ROOT),
            capture_output=True,
            text=True,
            timeout=120,
            encoding="utf-8",
            errors="replace"
        )
        output = result.stdout
        if result.stderr:
            output += f"\n[STDERR]\n{result.stderr}"
        if not output.strip():
            output = f"[Comando executado com código de saída {result.returncode} sem saída]"
        return output
    except subprocess.TimeoutExpired:
        return "Erro: O comando excedeu o tempo limite de execução (120s)."
    except Exception as e:
        return f"Erro ao executar comando: {str(e)}"

# Definição dos Schemas de Tools para a API OpenAI/DeepSeek
TOOLS_DEFINITIONS = [
    {
        "type": "function",
        "function": {
            "name": "read_file",
            "description": "Lê o conteúdo de um arquivo de código, relatório ou dado do projeto.",
            "parameters": {
                "type": "object",
                "properties": {
                    "relative_path": {
                        "type": "string",
                        "description": "Caminho relativo do arquivo (ex: 'reports/relatorio_preliminar.md' ou 'scripts/main.py')."
                    },
                    "start_line": {
                        "type": "integer",
                        "description": "Linha inicial opcional (1-indexada)."
                    },
                    "end_line": {
                        "type": "integer",
                        "description": "Linha final opcional (1-indexada)."
                    }
                },
                "required": ["relative_path"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "write_file",
            "description": "Cria ou substitui completamente um arquivo com novo conteúdo no projeto.",
            "parameters": {
                "type": "object",
                "properties": {
                    "relative_path": {
                        "type": "string",
                        "description": "Caminho relativo do arquivo a ser criado ou atualizado."
                    },
                    "content": {
                        "type": "string",
                        "description": "Conteúdo textual completo a ser gravado no arquivo."
                    }
                },
                "required": ["relative_path", "content"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "edit_file",
            "description": "Substitui um trecho específico de texto em um arquivo existente.",
            "parameters": {
                "type": "object",
                "properties": {
                    "relative_path": {
                        "type": "string",
                        "description": "Caminho relativo do arquivo."
                    },
                    "target_content": {
                        "type": "string",
                        "description": "Trecho exato de texto a ser substituído."
                    },
                    "replacement_content": {
                        "type": "string",
                        "description": "Novo trecho de texto que substituirá o original."
                    }
                },
                "required": ["relative_path", "target_content", "replacement_content"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "list_directory",
            "description": "Lista pastas e arquivos de um diretório relativo na pasta Project.",
            "parameters": {
                "type": "object",
                "properties": {
                    "relative_path": {
                        "type": "string",
                        "description": "Diretório a ser listado (vazio para a raiz do projeto)."
                    }
                },
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "run_command",
            "description": "Executa comandos de terminal (ex: scripts python, git, testes) dentro do diretório Project.",
            "parameters": {
                "type": "object",
                "properties": {
                    "command": {
                        "type": "string",
                        "description": "Comando PowerShell a executar (ex: 'python scripts/analise.py' ou 'git status')."
                    }
                },
                "required": ["command"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "schedule_cron",
            "description": "Agenda uma tarefa ou instrução para ser executada periodicamente via Cron.",
            "parameters": {
                "type": "object",
                "properties": {
                    "cron_expression": {
                        "type": "string",
                        "description": "Expressão cron padrão de 5 campos (minuto hora dia_mes mes dia_semana), ex: '0 9 * * *' para todo dia às 09h."
                    },
                    "instruction": {
                        "type": "string",
                        "description": "Instrução que o agente deve executar ao disparar o cron (ex: 'Gere o relatório semanal e me informe os resultados')."
                    },
                    "job_id": {
                        "type": "string",
                        "description": "Identificador único amigável para o job (ex: 'relatorio_diario')."
                    }
                },
                "required": ["cron_expression", "instruction"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "list_cron_jobs",
            "description": "Lista todas as tarefas agendadas (crons) ativas no momento.",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "cancel_cron_job",
            "description": "Cancela e remove uma tarefa agendada pelo seu job_id.",
            "parameters": {
                "type": "object",
                "properties": {
                    "job_id": {
                        "type": "string",
                        "description": "O ID do job a ser cancelado."
                    }
                },
                "required": ["job_id"]
            }
        }
    }
]
