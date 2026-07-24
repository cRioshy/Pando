# Phase Decision Outcome Link Report

Zeitpunkt: 2026-07-23

## Ziel

PandorickKi speichert finale Entscheidungen und Signale jetzt mit stabiler
`decision_id`, damit spaetere simulierte Outcomes eindeutig auf die
ausloesende Entscheidung zurueckgefuehrt werden koennen.

## Geaenderte Dateien

- `adapters/decision_signal_adapter.py`
- `adapters/outcome_tracker.py`
- `config.py`
- `orchestrator.py`
- `tests/test_decision_signal_adapter.py`
- `tests/test_outcome_tracker.py`

## Neue Datei

- `PHASE_DECISION_OUTCOME_LINK_REPORT.md`

## Neue persistente Dateien

- `data/platform_decisions.jsonl`
- `data/platform_signals.jsonl`

## Datenfluss

Der neue fachliche Datenfluss ist:

`BRAIN_DECISION_RECEIVED -> DECISION_CREATED -> SIGNAL_CREATED -> SIMULATED_TRADE_OPENED/UPDATED/CLOSED`

Die gleiche `decision_id` wird in finaler Decision und finalem Signal gespeichert.
Der Outcome-Tracker verknuepft zusaetzlich die passende `signal_id`, sobald das
Signal fuer eine offene simulierte Entscheidung eingeht.

## Sicherheit

- Keine Tradinglogik geaendert.
- Keine Brain-Gewichtung geaendert.
- Keine Analyseberechnung geaendert.
- Keine echten Orders aktiviert.
- Speicherung erfolgt append-only als JSONL.

## Validierung

Beispiel aus den Live-Dateien:

- Decision: `decision:6b36d1db-1358-563f-80e3-01a855e49c6c`
- Signal: `decision:6b36d1db-1358-563f-80e3-01a855e49c6c`
- Signal-ID: `signal:7fb6e4ac-899a-4054-9868-03fd8661cc47`

Damit ist die direkte Verbindung zwischen Decision und Signal nachweisbar.

## Tests

- `python -m unittest tests.test_decision_signal_adapter tests.test_outcome_tracker tests.test_crypto_trade_tracker`: OK
- `python -m unittest discover -s tests`: 144 Tests OK

## Laufpruefung

- `/api/health`: HTTP 200, Status OK
- Webserver: aktiv auf `http://127.0.0.1:8000`
- Ledger-Dateien werden live erweitert.

## Noch offen

Die naechste Ausbaustufe ist eine Statistik-Umstellung, die Trefferquote nicht
mehr aus rekonstruierten Learning-Logs berechnet, sondern aus eindeutig
geschlossenen Outcome-Datensaetzen je `decision_id`.
