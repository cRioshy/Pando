# Phase 4 Stock Adapter Analysis

## Scope

Analysiert wurde nur der bestehende Stock-Bot:

`C:/Users/Admin/Documents/Codex/2026-07-09/h/pandorick_stock_bot`

Es wurde kein bestehender Stock-Code geaendert.

## Startdatei

- `bot_stock.py`
- Diese Datei importiert `main` aus `main.py`.
- Durch `if __name__ == "__main__": main()` startet sie nur bei direkter Ausfuehrung.

Bewertung: sicher importierbar, solange nicht `bot_stock.main()` direkt aufgerufen wird.

## Zentrale Startfunktion

- `main.py::main()`
- `main.py::run_forever(config)`
- `main.py::run_once(config, sensor, cycle_number, next_sleep_seconds=None)`

Beste Adapter-Ziel-Funktion:

- `run_once(...)`

Grund:

- Sie fuehrt genau einen Analysezyklus aus.
- Sie gibt `list[Decision]` zurueck.
- Sie startet keine Endlosschleife.
- Sie nutzt vorhandene Logik fuer Analyse, Brain, Learning, History und Control-Ausgabe.

## Endlosschleifen

Existiert in:

- `main.py::run_forever(config)`

Verhalten:

- erstellt `PlaceholderStockDataProvider`
- erstellt `SensorEngine`
- ruft zyklisch `run_once(...)`
- wartet mit `time.sleep(config.loop_sleep_seconds)`

Adapter-Regel:

- `run_forever(...)` darf nicht direkt vom neuen Orchestrator verwendet werden.
- Der Adapter verwendet nur `run_once(...)`.

## Globale Variablen und Konfiguration

Globale Konfiguration:

- `config.py::PROJECT_ROOT`
- `config.py::DATA_DIR`
- `config.py::DATA_STOCK_DIR`
- `config.py::CONFIG`

Wichtige Werte:

- `CONFIG.symbols = ("AAPL", "MSFT", "NVDA", "TSLA", "SPCX")`
- `CONFIG.loop_sleep_seconds = 60`
- Datenpfade liegen unter `data_stock/`

Globale mutable Runtime-Listen wurden im Stock-Bot nicht wie im Crypto-Bot gefunden. Runtime-Zustand entsteht hauptsaechlich ueber Objekte:

- `PlaceholderStockDataProvider`
- `SensorEngine`
- `StockBrain`

## Geschriebene Dateien

Der Stock-Bot schreibt in:

- `data_stock/stock_history.json`
- `data_stock/stock_brain.json`
- `data_stock/stock_decisions.json`
- `data_stock/stock_logs.json`
- `data_stock/stock_precedence.json`
- `data_stock/stock_knowledge.json`
- `data_stock/stock_patterns.json`
- `data_stock/stock_weights.json` nur bei Initialisierung, falls nicht vorhanden
- `data_stock/backups/` wird angelegt

Alter Ordner:

- `data/`

Bewertung:

- `data/` ist Altbestand und wird fuer die Integration nicht bevorzugt.
- `data_stock/` ist aktive Stock-Datenquelle.

## API-Anbieter

Aktuell:

- Kein echter externer Stock-API-Anbieter.
- `PlaceholderStockDataProvider` erzeugt deterministische/evolvierende Testdaten.

Konfigurationsplatzhalter:

- `DataProviderConfig.provider_name = "placeholder"`
- `DataProviderConfig.api_key_env = "STOCK_DATA_API_KEY"`

Bewertung:

- Fuer Phase 4 kann ein kontrollierter echter Stock-Test ohne Zugangsdaten nur mit Placeholder-Daten laufen.
- Spaeterer echter API-Anbieter muss im Stock-Bot oder Adapter separat angebunden werden.

## Telegram

Datei:

- `telegram.py`

Funktionen:

- `format_decision_message(decision)`
- `send_message(message)`

Bewertung:

- Aktuell kein echter Versand.
- Keine hardcoded Telegram-Tokens.
- `send_message(...)` ist ein Platzhalter.
- Die neue Plattform sollte Telegram weiter zentral ueber einen eigenen TelegramAdapter versenden.

## Analyseergebnisse

`run_once(...)` liefert:

- `list[Decision]`

Jede `Decision` enthaelt:

- `symbol`
- `timestamp`
- `action`
- `final_probability`
- `state`
- `probability`
- `brain_adjustment`
- `risk`
- `reasoning`

Ueber `Decision.to_dict()` sind die Daten JSON-serialisierbar.

Wichtige normalisierbare Felder:

- `market_type`: fest `stock`
- `symbol`: `decision.symbol`
- `direction`: Mapping aus `decision.action`
- `probability`: `decision.final_probability`
- `facts`: `decision.state.facts`
- `indicators`: aus `decision.state.facts`
- `price`: `decision.state.facts["close_price"]`
- `source_timestamp`: `decision.timestamp`
- `raw_result`: `decision.to_dict()`

## Abhaengigkeiten

Stock-Bot nutzt derzeit nur Python-Standardbibliothek:

- `argparse`
- `dataclasses`
- `datetime`
- `json`
- `pathlib`
- `random`
- `typing`
- `zoneinfo`

Keine externen Pakete fuer den aktuellen Placeholder-Betrieb.

## Adapter-Risiken

1. Namenskonflikte: Stock-Bot hat generische Modulnamen wie `main`, `config`, `brain`, `market`.
2. Importpfad muss kontrolliert werden, damit nicht `PandorickKi/main.py` statt `pandorick_stock_bot/main.py` geladen wird.
3. `run_once(...)` druckt Control-Ausgabe in die Konsole.
4. `run_once(...)` schreibt echte JSON-Dateien in `data_stock/`.
5. Doppelte Analysen muessen im Adapter dedupliziert werden.
6. Der Adapter muss synchronen Stock-Code mit `asyncio.to_thread(...)` ausfuehren.
7. Der Adapter darf `run_forever(...)` nicht verwenden.

## Empfehlung fuer Schritt 2

Erstelle:

- `PandorickKi/adapters/stock_adapter.py`

Schnittstelle:

- `async start()`
- `async stop()`
- `async run_once()`
- `async health()`
- `async get_status()`

Technischer Ansatz:

- Stock-Pfad gezielt in `sys.path` einfuegen.
- `pandorick_stock_bot/main.py` kontrolliert per `importlib.util.spec_from_file_location(...)` laden.
- `PlaceholderStockDataProvider` und `SensorEngine` aus dem geladenen Stock-Modul verwenden.
- `run_once(...)` per `asyncio.to_thread(...)` ausfuehren.
- Ergebnisse in gemeinsames Stock-Format normalisieren.
- Events ueber vorhandenen `EventBus` publizieren.
