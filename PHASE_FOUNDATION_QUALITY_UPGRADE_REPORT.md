# Phase Foundation Quality Upgrade Report

## Ziel

PandorickKi wurde stabiler gemacht, ohne Tradinglogik, Brainlogik oder Analysegewichtungen zu verändern.

## Geänderte Bereiche

- JSONL-Ledger-Rotation fuer grosse append-only Dateien
- Decision/Signal/Outcome-Speicherung mit rotierender JSONL-Schreibschicht
- Learning-Report liest aktive und archivierte Ledger-Dateien
- Commodity-Provider-Aussetzer werden als Datenwarnung statt harter Service-Fehler behandelt
- Commodity-Preisservice nutzt Query1 und Query2 Yahoo-Chart-Endpunkte als kostenlosen Fallback
- Web-/Statistiktests erweitert

## Neue Datei

- `jsonl_ledger.py`

## Geänderte Dateien

- `config.py`
- `.env.example`
- `orchestrator.py`
- `adapters/decision_signal_adapter.py`
- `adapters/outcome_tracker.py`
- `adapters/commodity_adapter.py`
- `adapters/commodity_price_service.py`
- `adapters/control_center_adapter.py`
- `web/learning_report_service.py`
- `web/statistics_service.py`
- `tests/test_config.py`
- `tests/test_commodity_adapter.py`
- `tests/test_commodity_price_service.py`
- `tests/test_statistics_and_storage.py`
- `tests/test_decision_signal_adapter.py`
- `tests/test_learning_report_service.py`

## Rotation

Neue Einstellung:

`PANDORICKKI_JSONL_LEDGER_ROTATION_BYTES`

Standard:

`134217728` Bytes, also 128 MB.

Betroffene aktive Ledger:

- `data/platform_decisions.jsonl`
- `data/platform_signals.jsonl`
- `data/trade_outcomes.jsonl`

Archivziel:

- `data/archive/platform_decisions/`
- `data/archive/platform_signals/`
- `data/archive/trade_outcomes/`

Beim naechsten Schreibvorgang wird eine zu grosse aktive Datei atomisch in das Archiv verschoben und eine neue aktive Datei begonnen.

## Datenqualitaet

Normale Commodity-Provider-Probleme wie Timeout oder kein Preis werden jetzt als `COMMODITY_DATA_WARNING` gemeldet.

Harte Service-Fehler bleiben fuer echte Exceptions erhalten.

## Outcome-Kopplung

Die bestehende `decision_id`-Kopplung bleibt aktiv:

- finale Entscheidung erzeugt `decision_id`
- Signal traegt dieselbe `decision_id`
- simulierte Trades und geschlossene Outcomes werden ueber `decision_id` verbunden
- Learning-Report bevorzugt `decision_id_trade_outcomes`

## Tests

Ausgefuehrt:

`python -m unittest discover -s tests`

Ergebnis:

`171 tests OK`

## Bekannte Einschraenkungen

- Commodity-Fallback nutzt zwei Yahoo-Endpunkte, noch keine komplett unabhaengige zweite Datenquelle.
- Bestehende grosse Dateien werden erst beim naechsten Schreibvorgang rotiert.
- Alte Crypto-Module erzeugen weiterhin harmlose `datetime.utcnow()` DeprecationWarnings in Tests.
