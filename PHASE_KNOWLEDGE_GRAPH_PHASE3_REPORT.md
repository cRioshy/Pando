# Phase Knowledge Graph 3 Report

## Ziel

Phase 3 erweitert das Pandorick Control Center um eine echte interaktive Knowledge-Graph-Oberflaeche auf Basis der neuen read-only Graph-API.

Die Tradinglogik, Brainlogik, Learninglogik, Crypto Engine, Stock Engine, Adapter und bestehende Learning-Graph-API wurden nicht veraendert.

## Neue Dateien

- `web/static/knowledge_graph.js`
- `web/static/knowledge_graph.css`
- `tests/test_knowledge_graph_ui_phase3.py`

## Geaenderte Dateien

- `web/static/control_center.html`

## Funktionen

- eigene Knowledge-Graph-Ansicht im Control Center
- Force-Directed-Layout im Browser
- Cluster-Zentren fuer System, Infrastruktur, Brain, Crypto, Stocks, Indikatoren, Patterns, Decisions, Warnings und Errors
- Zoom per Mausrad
- Pan per Ziehen der Flaeche
- Knoten per Ziehen manuell verschiebbar
- Klick auf Knoten zeigt Details
- Doppelklick zentriert/fokussiert Knoten
- direkte Nachbarn werden hervorgehoben
- andere Knoten werden abgedunkelt
- Suche ueber `/api/v1/graph/search`
- Filter nach Typ
- Filter nach Cluster
- Option "Nur Nachbarn"
- Button "Alles einpassen"
- Button "Graph zuruecksetzen"
- Vollbildmodus
- automatische Aktualisierung alle 20 Sekunden

## Verwendete API

- `GET /api/v1/graph/overview`
- `GET /api/v1/graph/search?q=...`
- `GET /api/v1/graph/node/{node_id}`

## Live-Pruefung

- `/api/health`: `OK`
- `/knowledge_graph.js`: HTTP 200
- `/api/v1/graph/overview`: `56` Knoten, `159` Kanten, Version `4`

## Testergebnisse

- `python -m unittest tests.test_knowledge_graph_phase2 tests.test_knowledge_graph_ui_phase3`: OK, 14 Tests
- `python -m unittest discover`: OK, 114 Tests

## Bekannte Einschraenkungen

- Cytoscape.js wurde noch nicht lokal vendored eingebaut. Die aktuelle Phase nutzt eine eigene modulare SVG-Force-Ansicht, damit keine externe Netzwerkabhaengigkeit entsteht.
- Fuer sehr grosse Graphen sollte spaeter Cytoscape.js oder Sigma.js lokal gebundelt und der Renderer auf Canvas/WebGL migriert werden.
- Serverseitig gespeicherte Positionen sind noch nicht aktiv; Positionen bleiben im Browser zwischen Auto-Refreshs stabil, solange die Seite offen ist.
