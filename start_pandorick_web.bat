@echo off
cd /d "%~dp0"
call setup_local_env.bat
if errorlevel 1 (
    pause
    exit /b 1
)
set "PANDORICKKI_PYTHON=%~dp0.venv\Scripts\python.exe"
"%PANDORICKKI_PYTHON%" scripts\runtime_preflight.py
if errorlevel 1 (
    pause
    exit /b 1
)
set PANDORICKKI_NEUROBRAIN_RECEIVER_ENABLED=1
set PANDORICKKI_LIVE_CRYPTO=1
set PANDORICKKI_CRYPTO_LIVE_PRICE_DISPLAY=1
set PANDORICKKI_STOCK_TEST_MODE=0
set PANDORICKKI_STOCK_LIVE_PRICE_DISPLAY=1
set PANDORICKKI_TELEGRAM_ENABLED=0
set PANDORICKKI_TELEGRAM_DRY_RUN=1
start "" http://127.0.0.1:8000
"%PANDORICKKI_PYTHON%" main.py --headless --web
