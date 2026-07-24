# Phase Live ControlCenter

## Geaenderte Dateien

- `adapters/control_center_adapter.py`
- `event_bus.py`
- `shared_state.py`
- `orchestrator.py`
- `main.py`
- `tests/test_control_center_adapter.py`

## Neue Dateien

- `tests/test_live_control_center.py`
- `PHASE_LIVE_CONTROL_CENTER_REPORT.md`

## Abonnierte Events

- `CRYPTO_MARKET_DATA_UPDATED`
- `STOCK_MARKET_DATA_UPDATED`
- `CRYPTO_ANALYSIS_FINISHED`
- `STOCK_ANALYSIS_FINISHED`
- `DECISION_CREATED`
- `SIGNAL_CREATED`
- `AI_LEARNING_UPDATED`
- `SERVICE_HEARTBEAT`
- `SERVICE_STATUS_CHANGED`
- `SYSTEM_ERROR`

Zusaetzlich beobachtet das ControlCenter vorhandene Adapter-Events wie
`BRAIN_DECISION_RECEIVED`, Service-Start/Stop/Error und spezifische Heartbeats.

## Aktualisierungsintervall

- Standard: `1.0` Sekunden
- Konfigurierbar mit `--refresh`
- Mindestintervall intern: `0.1` Sekunden
- Events werden sofort verarbeitet; nur die Terminal-Neuzeichnung ist
  intervallbasiert.

## Startbefehle

- `python main.py --once`
- `python main.py --live`
- `python main.py --headless`

Fuer kontrollierte Testlaeufe:

- `python main.py --live --cycles 1 --refresh 0.1`
- `python main.py --headless --cycles 1`

## Testergebnisse

- `python -m unittest tests.test_live_control_center` -> OK, 5 Tests
- `python -m unittest discover tests` -> OK, 24 Tests
- `python -m compileall .` -> OK
- `python main.py --once` -> OK
- `python main.py --live --cycles 1 --refresh 0.1 --interval 0.1` -> OK
- `python main.py --headless --cycles 1 --interval 0.1` -> OK

## Bekannte Einschraenkungen

- Die Live-Anzeige ist eine Terminalansicht, keine Weboberflaeche.
- Es wird keine externe Terminal-Bibliothek wie `rich` vorausgesetzt.
- Die EventBus-Queue-Groesse entspricht aktuell der In-Memory-Event-History.
- Live-Crypto bleibt standardmaessig im Testdatenmodus, bis Live-API-Zugriff
  bewusst aktiviert wird.
