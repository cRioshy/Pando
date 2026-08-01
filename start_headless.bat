@echo off
cd /d "%~dp0"
call setup_local_env.bat
if errorlevel 1 (
    pause
    exit /b 1
)
"%~dp0.venv\Scripts\python.exe" scripts\runtime_preflight.py
if errorlevel 1 (
    pause
    exit /b 1
)
"%~dp0.venv\Scripts\python.exe" main.py --headless
pause
