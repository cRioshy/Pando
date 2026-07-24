# Phase 4C - ControlCenterAdapter

## Ziel

Der neue PandorickKi-ControlCenterAdapter beobachtet den zentralen EventBus,
liest den SharedState aus und gibt pro Plattform-Zyklus eine kompakte
PowerShell-Statusanzeige aus.

## Betroffene Dateien

- `adapters/control_center_adapter.py` wurde neu erstellt.
- `orchestrator.py` verdrahtet den neuen Adapter statt des bisherigen
  ControlCenter-Platzhalters.
- `tests/test_control_center_adapter.py` wurde neu erstellt.

## Unverändert

- Der bestehende Crypto-Bot wurde nicht importiert und nicht geändert.
- Der bestehende Stock-Bot wurde nicht geändert.
- Das bestehende Assistant-Core-Projekt wurde nicht geändert.

## Verhalten

- Der Adapter zählt alle Plattform-Events.
- Er zeigt Servicezustände aus `SharedState`.
- Er gibt `STOCK_ANALYSIS_FINISHED` und `BRAIN_DECISION_RECEIVED` separat aus.
- Er veröffentlicht selbst `CONTROL_STATUS_UPDATED`.
- Er verwendet keine API-Schlüssel und keine externen Dienste.

## Risiko

- Gering: Der Adapter hängt nur am neuen EventBus und liest den neuen
  SharedState.
- Die PowerShell-Ausgabe ist bewusst kompakt, kann aber später erweitert oder
  konfigurierbar gemacht werden.

## Tests

- `python -m unittest tests.test_control_center_adapter`
- `python -m unittest discover tests`
- `python -m compileall .`
- `python main.py --once`
