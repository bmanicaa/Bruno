@echo off
cd /d "%~dp0"
title Assistente OpenCode Telegram
set PYTHONUNBUFFERED=1
echo ======================================================
echo    INICIANDO ASSISTENTE DO PROJETO NO TELEGRAM
echo ======================================================
if exist "..\.venv\Scripts\python.exe" (
    "..\.venv\Scripts\python.exe" -u bot.py
) else if exist ".venv\Scripts\python.exe" (
    ".venv\Scripts\python.exe" -u bot.py
) else (
    python -u bot.py
)
pause
