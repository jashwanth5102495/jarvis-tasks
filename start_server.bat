
@echo off
cd /d "%~dp0"
echo [JARVIS] Starting server...
python -m uvicorn jarvis_server.app:app --host 0.0.0.0 --port 5000
pause
