# Phase Desktop Deployment

## Ziel

PandorickKi wird als eigenes Projekt fuer den Desktop vorbereitet und danach
nach `C:\Users\Admin\Desktop\PandorickKi` kopiert.

## Neue Dateien

- `README.md`
- `.env.example`
- `start_once.bat`
- `start_live.bat`
- `start_headless.bat`
- `PHASE_DESKTOP_DEPLOYMENT_REPORT.md`

## Deployment-Regeln

- Bestehende Crypto-, Stock- und Brain-Projekte werden nicht veraendert.
- `__pycache__` wird nicht als Quellbestandteil benoetigt.
- Runtime-Daten unter `data/` bleiben lokal erzeugte Betriebsdaten.
- Desktop-Ziel benoetigt Schreibfreigabe, weil es ausserhalb des Workspace liegt.
- Default-Pfade fuer Crypto und Stock zeigen weiterhin auf die bestehenden
  getrennten Quellprojekte. Sie koennen per ENV ueberschrieben werden.

## Startbefehle

- `python main.py --once`
- `python main.py --live`
- `python main.py --headless`
- `start_once.bat`
- `start_live.bat`
- `start_headless.bat`

## Tests

- Quelle: `python -m unittest discover tests` -> OK, 29 Tests
- Quelle: `python -m compileall .` -> OK
- Desktop: `python -m compileall .` -> OK
- Desktop: `python main.py --once` -> OK

## Desktop-Ergebnis

Zielordner:

```text
C:\Users\Admin\Desktop\PandorickKi
```

Der Desktop-Start meldet:

```text
Health: OK
Services: crypto=OK, brain=OK, stock=OK, telegram=OK, control_center=OK
```
