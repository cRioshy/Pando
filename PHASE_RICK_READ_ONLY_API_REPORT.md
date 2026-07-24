# Phase Rick Read-only API Report

## Ziel

PandorickKi wurde fuer eine spaetere Rick-Anbindung vorbereitet. Die neue Schnittstelle ist read-only, versioniert und liefert ein einheitliches Antwortformat fuer Rick, ohne Tradinglogik, Brainlogik, Lernlogik oder Graph-Engine umzubauen.

## Backup

- Backup-Pfad: `backups/rick_api_prechange_20260722_174501`
- Git-Status: Kein Git-Repository in `PandorickKi`; ein Commit konnte deshalb nicht erstellt werden.
- Stable Graph wurde vor Aenderungen als Datei-Backup gesichert.

## Geaenderte Dateien

- `config.py`
- `web/api.py`
- `web/routes.py`
- `web/rick_api_service.py`
- `tests/test_rick_read_only_api.py`

## Read-only API Endpunkte

- `GET /api/v1/health`
- `GET /api/v1/system/status`
- `GET /api/v1/brain/status`
- `GET /api/v1/learning/summary`
- `GET /api/v1/graph/overview`
- `GET /api/v1/graph/cluster/{cluster_id}`
- `GET /api/v1/graph/node/{node_id}`
- `GET /api/v1/decisions/recent`
- `GET /api/v1/statistics`
- `GET /api/v1/warnings`

Die bestehende Control-Center-API bleibt unveraendert nutzbar.

## Antwortformat

Alle Rick-Endpunkte liefern:

```json
{
  "status": "ok",
  "generated_at": "2026-07-22T15:52:09.691690+00:00",
  "data_age_seconds": 3.36,
  "source": "pandoriki",
  "version": "v1",
  "data": {}
}
```

## Authentifizierung

- Token-Variable: `PANDORICKKI_RICK_API_TOKEN`
- Header: `Authorization: Bearer <token>`
- Alternative Header: `X-Rick-API-Token: <token>`
- Wenn kein Token gesetzt ist, sind lokale Tests von `127.0.0.1` erlaubt.
- Wenn ein Token gesetzt ist, werden falsche oder fehlende Tokens mit HTTP `401` abgelehnt.
- Zugriff wird in `data/rick_api_audit.jsonl` auditiert.
- Tokens werden nicht im Audit-Log und nicht in API-Antworten ausgegeben.

## Sicherheit

- Nur lokale Zugriffe sind erlaubt.
- Rick-API akzeptiert nur lesende GET-Methoden.
- POST/PUT/PATCH/DELETE fuer `/api/v1/*` werden abgelehnt.
- Keine Shell-Kommandos aus Browser/API-Eingaben.
- Keine echten Orders.
- Keine Secrets, Tokens, Passwoerter oder API-Keys in Antworten.
- Absolute Benutzerpfade werden in Rick-Antworten maskiert.
- Graph-Daten werden auf oeffentliche Felder reduziert.

## Live-Pruefung

Startbefehl:

```powershell
$env:PANDORICKKI_LIVE_CRYPTO='false'
$env:PANDORICKKI_CRYPTO_LIVE_PRICE_DISPLAY='true'
python main.py --live --web
```

Port:

```text
127.0.0.1:8000
```

Beispiel `/api/v1/health`:

```json
{
  "status": "ok",
  "source": "pandoriki",
  "version": "v1",
  "data": {
    "status": "OK",
    "web_running": true,
    "websocket_active": true,
    "statistics_active": true
  }
}
```

Beispiel `/api/v1/learning/summary`:

```json
{
  "status": "ok",
  "source": "pandoriki",
  "version": "v1",
  "data": {
    "crypto_analyses": 3772,
    "stock_analyses": 5620,
    "learning_graph_nodes": 13,
    "learning_graph_edges": 17,
    "proven_learning_status": "activity_detected"
  }
}
```

Beispiel Rick-Graph:

```json
{
  "status": "ok",
  "source": "pandoriki",
  "version": "v1",
  "data": {
    "node_count": 13,
    "edge_count": 17,
    "nodes": [],
    "edges": []
  }
}
```

## Tests

- Neue Rick-API Tests: erfolgreich
- Web-ControlCenter Tests: erfolgreich
- Knowledge-Graph Tests: erfolgreich
- Vollstaendige Suite: `132` Tests erfolgreich

## Bekannte Einschraenkungen

- Authentifizierung ist vorbereitet, aber ohne gesetztes `PANDORICKKI_RICK_API_TOKEN` im lokalen Ersttest offen fuer localhost.
- Rate-Limit ist architektonisch vorbereitet durch zentrale Route/Auth-Schicht, aber noch nicht aktiv begrenzend.
- Hit-Rate und Trading-Erfolg werden nicht behauptet, solange keine verifizierten Trade-Ergebnisse vorliegen.
- Rick selbst wird nicht veraendert; spaeter braucht Rick einen separaten Adapter.
