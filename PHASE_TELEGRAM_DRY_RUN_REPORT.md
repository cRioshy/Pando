# Phase TelegramAdapter Dry-Run

## Ziel

Telegram wird als eigener Adapter an die PandorickKi-Plattform angeschlossen.
Der Adapter verarbeitet nur fertige Analyse-Events und sendet standardmaessig
nicht live.

## Geaenderte Dateien

- `config.py`
- `orchestrator.py`
- `adapters/control_center_adapter.py`
- `tests/test_config.py`
- `tests/test_integration_full.py`

## Neue Dateien

- `adapters/telegram_adapter.py`
- `tests/test_telegram_adapter.py`
- `PHASE_TELEGRAM_DRY_RUN_REPORT.md`

## Events

- `TELEGRAM_SERVICE_STARTED`
- `TELEGRAM_SERVICE_STOPPED`
- `TELEGRAM_MESSAGE_READY`
- `TELEGRAM_DRY_RUN_RECORDED`
- `TELEGRAM_MESSAGE_SENT`
- `TELEGRAM_SERVICE_ERROR`
- `TELEGRAM_SERVICE_HEARTBEAT`

## ENV-Variablen

- `PANDORICKKI_TELEGRAM_ENABLED`
- `PANDORICKKI_TELEGRAM_DRY_RUN`
- `PANDORICKKI_TELEGRAM_BOT_TOKEN`
- `PANDORICKKI_TELEGRAM_CHAT_ID`
- `PANDORICKKI_TELEGRAM_LOG_FILE`

## Sicherheit

- Keine alten Crypto-Telegram-Tokens werden gelesen.
- Dry-Run ist Standard.
- Ohne Token/Chat-ID wird Live-Versand nicht ausgefuehrt.
- Telegram-Fehler beenden Crypto, Stock, Brain oder ControlCenter nicht.

## Tests

- `python -m unittest tests.test_telegram_adapter` -> OK, 3 Tests
- `python -m unittest tests.test_integration_full` -> OK, 1 Test
- `python -m unittest discover tests` -> OK, 29 Tests
- `python -m compileall .` -> OK
- `python main.py --once` -> OK
- `PANDORICKKI_TELEGRAM_ENABLED=1` plus Dry-Run-Start -> OK,
  8 Dry-Run-Nachrichten aufgezeichnet
