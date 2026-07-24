# Phase Web ControlCenter Report

## Neue Dateien

- `web/__init__.py`
- `web/api.py`
- `web/routes.py`
- `web/schemas.py`
- `web/websocket_manager.py`
- `web/static/control_center.html`
- `web/static/control_center.css`
- `web/static/control_center.js`
- `tests/test_web_control_center.py`
- `start_pandorick_web.bat`

## Geaenderte Dateien

- `main.py`: neue Option `--web` sowie `--web-host` und `--web-port`
- `orchestrator.py`: optionale sichere Callbacks `should_pause` und `should_stop`
- `README.md`: Startbefehle fuer das lokale Web-ControlCenter

Die bestehenden Analyse- und Adapterlogiken wurden nicht veraendert.

## API-Endpunkte

- `GET /api/health`
- `GET /api/status`
- `GET /api/services`
- `GET /api/crypto`
- `GET /api/stocks`
- `GET /api/brain`
- `GET /api/signals`
- `GET /api/errors`
- `GET /api/events`
- `GET /api/config/public`

## Steuer-Endpunkte

- `POST /api/control/start`
- `POST /api/control/stop`
- `POST /api/control/restart`
- `POST /api/control/pause`
- `POST /api/control/resume`
- `POST /api/control/restart/crypto`
- `POST /api/control/restart/stocks`
- `POST /api/control/restart/brain`
- `POST /api/control/restart/telegram`

Die Steuerbefehle werden validiert, lokal geloggt und fuehren keine Shell-Kommandos oder echten Orders aus.

## WebSocket-Verbindung

- Route: `GET /ws/live`
- Aktiv: Ja
- Der Browser erhaelt einen initialen Snapshot und danach Live-Updates bei relevanten Events.

Uebertragene Events:

- `CRYPTO_ANALYSIS_FINISHED`
- `STOCK_ANALYSIS_FINISHED`
- `DECISION_CREATED`
- `SIGNAL_CREATED`
- `AI_LEARNING_UPDATED`
- `SERVICE_HEARTBEAT`
- `SERVICE_STATUS_CHANGED`
- `SYSTEM_ERROR`
- Service-Heartbeats und Fehler der bestehenden Adapter
- Telegram-Status- und Nachrichten-Events

## Startbefehle

```powershell
python main.py --live --web
python main.py --headless --web
python -m web.api
start_pandorick_web.bat
```

Standard-URL:

```text
http://127.0.0.1:8000
```

## Sicherheitsmassnahmen

- Standard-Bind nur auf `127.0.0.1`
- API und Steuerung akzeptieren nur lokale Zugriffe
- keine CORS-Freigabe fuer fremde Domains
- keine Secrets in `/api/config/public`
- Secret-aehnliche Felder werden aus Status-Snapshots entfernt
- keine Browser-Eingaben werden als Shell-Kommandos ausgefuehrt
- keine echten Trade-Orders
- Steuerbefehle werden in `data/web_control_commands.jsonl` protokolliert

## Testergebnisse

Ausgefuehrt:

```powershell
C:\Users\Admin\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe -m unittest tests.test_web_control_center
C:\Users\Admin\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe -m unittest discover
```

Ergebnis:

```text
tests.test_web_control_center: 7 Tests OK
unittest discover: 39 Tests OK
```

## Bekannte Einschraenkungen

- Der Webserver nutzt aktuell bewusst die Python-Standardbibliothek statt FastAPI, damit keine neue externe Abhaengigkeit erforderlich ist.
- `pause`, `resume` und `stop` wirken auf den PandorickKi-Orchestratorlauf.
- Service-spezifische Restarts werden als sichere Control-Events protokolliert.
- Es gibt noch keine oeffentliche Freigabe, keine Web-App-Deployment-Funktion und keine mobile App.
