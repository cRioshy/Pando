@echo off
cd /d "%~dp0"
set "PANDORICKKI_PYTHON=C:\Users\Admin\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe"
if not exist "%PANDORICKKI_PYTHON%" set "PANDORICKKI_PYTHON=python"
set PANDORICKKI_NEUROBRAIN_RECEIVER_ENABLED=1
set PANDORICKKI_LIVE_CRYPTO=1
set PANDORICKKI_CRYPTO_LIVE_PRICE_DISPLAY=1
set PANDORICKKI_STOCK_TEST_MODE=0
set PANDORICKKI_STOCK_LIVE_PRICE_DISPLAY=1
start "" http://127.0.0.1:8000
"%PANDORICKKI_PYTHON%" main.py --headless --web
