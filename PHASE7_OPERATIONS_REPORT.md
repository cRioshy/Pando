# Phase 7 - Zentrale Konfiguration und Betriebsreife

## Ziel

Phase 7 verschiebt harte Pfade und Laufzeitwerte in eine zentrale
Konfiguration. Dadurch kann PandorickKi im Dauerbetrieb sauber gesteuert werden,
ohne bestehende Crypto-, Stock- oder Brain-Projekte zu veraendern.

## Geaenderte Dateien

- `main.py`
- `orchestrator.py`
- `adapters/stock_adapter.py`

## Neue Dateien

- `config.py`
- `tests/test_config.py`
- `PHASE7_OPERATIONS_REPORT.md`

## ENV-Konfiguration

- `PANDORICKKI_CRYPTO_PATH`
- `PANDORICKKI_STOCK_PATH`
- `PANDORICKKI_DATA_DIR`
- `PANDORICKKI_SHARED_STATE_FILE`
- `PANDORICKKI_BRAIN_EVENTS_FILE`
- `PANDORICKKI_LIVE_CRYPTO`
- `PANDORICKKI_CRYPTO_SYMBOLS`
- `PANDORICKKI_CRYPTO_TIMEFRAME`
- `PANDORICKKI_CRYPTO_CANDLE_LIMIT`
- `PANDORICKKI_CYCLE_INTERVAL`
- `PANDORICKKI_CONTROL_REFRESH`
- `PANDORICKKI_ERROR_BACKOFF`
- `PANDORICKKI_STOP_TIMEOUT`
- `PANDORICKKI_TELEGRAM_ENABLED`

## Startbefehle

- `python main.py --once`
- `python main.py --live`
- `python main.py --headless`

CLI-Werte `--interval` und `--refresh` ueberschreiben ENV-Defaults fuer den
aktuellen Start.

## Sicherheit

- Live-Crypto bleibt standardmaessig aus.
- Telegram bleibt standardmaessig aus.
- Bestehende Projektdateien werden nicht geaendert.
- Stock-Imports sind isoliert, damit `PandorickKi/config.py` nicht mit dem
  bestehenden Stock-Bot-`config.py` kollidiert.

## Tests

- `python -m unittest tests.test_config` -> OK, 2 Tests
- `python -m unittest tests.test_stock_adapter` -> OK, 4 Tests
- `python -m unittest discover tests` -> OK, 26 Tests
- `python -m compileall .` -> OK
- `python main.py --once` -> OK
- `python main.py --live --cycles 1 --refresh 0.1 --interval 0.1` -> OK
- `python main.py --headless --cycles 1 --interval 0.1` -> OK

## Bekannte Einschraenkungen

- TelegramAdapter ist noch nicht verdrahtet.
- Adapter-Auto-Restart ist vorbereitet als Konfigurationswert, aber noch nicht
  als eigener Supervisor umgesetzt.
- Live-Crypto benoetigt weiterhin bewusst aktivierte ENV-Konfiguration und
  passende externe Abhaengigkeiten.
