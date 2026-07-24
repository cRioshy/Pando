# Phase ControlCenter Switch

## Ziel

Das ControlCenter kann jetzt pro Start oder per ENV ein- und ausgeschaltet
werden.

## Geaenderte Dateien

- `config.py`
- `main.py`
- `orchestrator.py`
- `.env.example`
- `README.md`
- `tests/test_config.py`
- `tests/test_live_control_center.py`

## Neue Dateien

- `control_center.html`
- `open_control_center.bat`

## Schalter

ENV:

```text
PANDORICKKI_CONTROL_CENTER_ENABLED=1
PANDORICKKI_CONTROL_CENTER_ENABLED=0
```

CLI:

```powershell
python main.py --live --control-on
python main.py --live --control-off
```

## Verhalten

- Wenn ControlCenter an ist, wird der Adapter normal gestartet.
- Wenn ControlCenter aus ist, wird kein ControlCenter-Adapter erstellt.
- `--live --control-off` startet sicher ohne Live-Anzeige und meldet
  `Modus: live-control-off`.
- Crypto, Stock, Brain und Telegram laufen weiter.
- `control_center.html` bildet die verlinkte Dashboard-Optik nach und zeigt
  einen AN/AUS-Schalter mit passendem Startbefehl.

## Tests

Auszufuehren:

- `python -m unittest tests.test_config`
- `python -m unittest tests.test_live_control_center`
- `python -m unittest discover tests`
- `python -m compileall .`
- `python main.py --live --control-off --cycles 1 --interval 0.1`
