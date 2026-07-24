# Phase 4 - Learning Graph API

## Ziel

Phase 4 stellt den Pandorick Learning Graph als reine, lokale Read-only-API bereit.

Es wurden keine Crypto-, Stock-, Brain-, Telegram-, Signal- oder Trade-Berechnungen veraendert.

## Geaenderte Dateien

- `web/api.py`
  - `LearningGraphService` an den bestehenden `WebControlServer` angebunden.
  - Read-only-Methoden fuer Graph, Nodes, Edges, Stats, Recent und Einzelknoten erstellt.
  - Cache-Invalidierung bei relevanten Lern-, Analyse-, Decision- und Signal-Events ergaenzt.

- `web/routes.py`
  - Neue lokale API-Routen fuer den Learning Graph registriert.
  - Einzelknotenroute mit sicherem URL-Decoding und 404 bei fehlendem Knoten ergaenzt.

## Neue Dateien

- `tests/test_learning_graph_api_phase4.py`
  - API-Tests fuer alle neuen Learning-Graph-Endpunkte.
  - Tests gegen interne Rohdaten, Secrets, Formeln und Windows-Benutzerpfade.
  - Tests fuer kaputte oder leere Brain-Event-Dateien.

## API-Endpunkte

- `GET /api/v1/learning-graph`
- `GET /api/v1/learning-graph/nodes`
- `GET /api/v1/learning-graph/edges`
- `GET /api/v1/learning-graph/stats`
- `GET /api/v1/learning-graph/recent`
- `GET /api/v1/learning-graph/node/{node_id}`

## Sicherheitsregeln

- Nur lokale API-Ausgabe ueber den bestehenden Webserver.
- Keine Shell-Kommandos.
- Keine Schreiboperationen.
- Keine direkten Browserzugriffe auf interne JSONL-Dateien.
- Keine Ausgabe von `raw_result`, `reasoning`, `calculation`, `weight`, Tokens oder absoluten Windows-Benutzerpfaden in der Graph-API.

## Tests

Gezielte Tests:

```text
python -m unittest tests.test_learning_graph_phase3 tests.test_learning_graph_api_phase4 tests.test_web_control_center
Ran 19 tests
OK
```

Gesamttests:

```text
python -m unittest discover -s tests
Ran 69 tests
OK
```

Hinweis: Die volle Test-Suite zeigt bestehende `DeprecationWarning`-Meldungen aus dem alten Crypto-Projekt wegen `datetime.utcnow()`. Das ist kein neuer Fehler aus Phase 4.

## Bekannte Einschraenkungen

- Noch keine Visualisierung im Browser.
- Noch kein Menuepunkt im ControlCenter.
- Noch keine Filter- oder Suchparameter in der API.
- Phase 4 ist bewusst nur Backend/API.
