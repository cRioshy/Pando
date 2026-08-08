@echo off
setlocal
cd /d "%~dp0"

set "PANDORICKKI_BOOTSTRAP_PYTHON=C:\Users\Admin\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe"
if not exist "%PANDORICKKI_BOOTSTRAP_PYTHON%" set "PANDORICKKI_BOOTSTRAP_PYTHON=python"

if not exist ".venv\Scripts\python.exe" (
    echo Creating project-local Python environment in .venv ...
    "%PANDORICKKI_BOOTSTRAP_PYTHON%" -m venv ".venv"
    if errorlevel 1 (
        echo Failed to create .venv. No service was started.
        exit /b 1
    )
)

".venv\Scripts\python.exe" -c "from zoneinfo import ZoneInfo; ZoneInfo('America/New_York')" >nul 2>&1
if errorlevel 1 (
    echo Installing verified project runtime dependencies ...
    ".venv\Scripts\python.exe" -m pip install --disable-pip-version-check -r requirements.txt
    if errorlevel 1 (
        echo Failed to install runtime dependencies. No service was started.
        exit /b 1
    )
)

echo Project-local Python environment is ready.
exit /b 0
