@echo off
cd /d "%~dp0"
set PANDORICKKI_NEUROBRAIN_RECEIVER_ENABLED=1
start "" http://127.0.0.1:8000
python main.py --headless --web
