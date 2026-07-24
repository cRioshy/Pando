# Phase Knowledge Graph 2 Report

## Ziel

Phase 2 erstellt die Backend-Grundlage fuer einen echten interaktiven Knowledge Graph, ohne Tradinglogik, Brainlogik, Learninglogik, Adapter oder bestehende Control-Center-Funktionen zu veraendern.

## Neue Dateien

- `learning_graph/knowledge_graph_models.py`
- `learning_graph/knowledge_graph_builder.py`
- `learning_graph/knowledge_graph_service.py`
- `tests/test_knowledge_graph_phase2.py`

## Geaenderte Dateien

- `web/api.py`
- `web/routes.py`

## Neue Read-only API-Endpunkte

- `GET /api/v1/graph/overview`
- `GET /api/v1/graph/cluster/{cluster_id}`
- `GET /api/v1/graph/node/{node_id}`
- `GET /api/v1/graph/search?q=...`
- `GET /api/v1/graph/changes?since_version=...`

## Datenquellen

Die neue Graph-Schicht verwendet weiterhin nur vorhandene Pandorick-Daten ueber die bestehende `GraphRepository`:

- Brain Events
- rotierte Brain Events
- Stock History
- Stock Decisions
- Crypto Trade Memory

Es wurden keine Demo-Daten erzeugt.

## Sicherheitsgrenze

Die API gibt nur browser-sichere Felder aus. Secrets, absolute Benutzerpfade, Raw-Result-Daten, Berechnungsdetails und Tokens werden nicht in das neue Knowledge-Graph-Modell uebernommen.

## Live-Pruefung

Nach Neustart antwortete:

- `/api/health`: `OK`
- `/api/v1/graph/overview`: `56` Knoten, `159` Kanten
- `/api/v1/graph/search?q=BTC`: `2` Treffer
- `/api/v1/graph/cluster/crypto`: `4` Knoten
- `/api/v1/graph/node/{node_id}`: Node-Details mit direkten Nachbarn

## Testergebnisse

- `python -m unittest tests.test_knowledge_graph_phase2`: OK, 7 Tests
- `python -m unittest discover`: OK, 107 Tests

## Bekannte Einschraenkungen

- Das Browser-Frontend nutzt noch die alte SVG-Learning-Graph-Ansicht.
- Cytoscape.js oder eine andere Graph-Bibliothek wurde in Phase 2 noch nicht eingebaut.
- Stabile Graph-Positionen und Cluster-Performance sind fuer spaetere Phasen vorgesehen.
- `/api/v1/graph/changes` liefert aktuell einen versionierten Snapshot und ist fuer echte Delta-Updates vorbereitet.
