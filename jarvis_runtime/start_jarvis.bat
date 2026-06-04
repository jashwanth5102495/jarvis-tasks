
@echo off
cd /d "%~dp0.."
echo [Jarvis] Starting AI Runtime Manager...
python -m jarvis_runtime.runtime_manager
pause
