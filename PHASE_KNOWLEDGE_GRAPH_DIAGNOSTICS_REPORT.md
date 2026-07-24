# Phase Knowledge Graph Diagnostics Report

## Ziel

Der Knowledge Graph sollte nicht mehr wie ein Linienknauel erscheinen. Die Aenderung betrifft nur Projektion, Layout, Renderer-Diagnostik und Cache-Verhalten des Web-ControlCenters.

Tradinglogik, Brain, Learning, Crypto, Stock, Telegram und DecisionCore wurden nicht veraendert.

## Geaenderte Dateien

- `learning_graph/graph_projection_service.py`
- `learning_graph/knowledge_graph_service.py`
- `web/static/control_center.html`
- `web/static/knowledge_graph.css`
- `web/static/knowledge_graph.js`
- `web/static/knowledge_graph_bootstrap.js`
- `web/static/knowledge_graph_legacy.js`

## Backup

- `backups/knowledge_graph_before_diagnostics_20260721_192121`

## Ursache

Die alte Graph-Ansicht zeigte zu viele Detailknoten und Detailverbindungen gleichzeitig. Dadurch wirkten stark verbundene Knoten wie Zentren eines Faecher-Layouts. Zusaetzlich wurde der Knowledge-Graph-Cache bei vielen Live-Events komplett geloescht, wodurch der Browser wiederholt teure Graph-Neuaufbauten ausloesen konnte.

## Umsetzung

- Overview-Projektion auf kompakte Markt-/System-Cluster reduziert.
- Edges in der Overview aggregiert.
- Serverseitiges ForceAtlas2-aehnliches Layout mit 350 Iterationen eingebaut.
- Positionen normalisiert und auf eine feste Bounding Box begrenzt.
- Diagnosewerte fuer Renderer, Layout, Iterationen, Bounds, Overlaps und doppelte Positionen eingebaut.
- Sigma/WebGL-Renderer bleibt aktiv, wenn WebGL verfuegbar ist.
- SVG-Fallback bleibt erhalten, falls WebGL im Browser nicht verfuegbar ist.
- Knowledge-Graph-Cache wird bei Live-Events nicht mehr sofort geloescht, sondern als dirty markiert und kontrolliert neu aufgebaut.

## Vorher / Nachher

Vorher:

- Overview enthielt bis zu 50 Knoten.
- Viele direkte Detailverbindungen wurden gleichzeitig dargestellt.
- Fan-/Knauelwirkung durch allgemeine Knoten und eng liegende Positionen.
- Cache konnte bei Live-Events permanent invalidiert werden.

Nachher:

- Overview aktuell: 13 Knoten.
- Overview aktuell: 17 Kanten.
- Aggregierte Cluster statt zu vieler Detailknoten.
- ForceAtlas2-aehnliches Layout: 350 Iterationen.
- Erkannte Ueberlagerungen: 0.
- Doppelte Positionen: 0.
- Zweiter API-Aufruf nach Cache: ca. 0,45 Sekunden.

## API-Pruefung

`GET /api/health`

- HTTP 200
- Status: OK
- Webserver: aktiv
- WebSocket: aktiv
- Statistik: aktiv

`GET /api/v1/graph/overview`

- HTTP 200
- node_count: 13
- edge_count: 17
- layout_engine: `server_forceatlas2_style`
- forceatlas2_iterations: 350
- overlapping_nodes: 0
- duplicate_positions: 0

## Performance

- Erster Graph-Aufbau im laufenden System: ca. 8,5 Sekunden.
- Danach gecachter Graph-Aufruf: ca. 0,45 Sekunden.
- Cache-Rebuilds werden gedrosselt, damit Analyse-Events den Graph nicht permanent neu berechnen.

## Renderer-Hinweis

Der Codex In-App-Browser stellt in dieser Umgebung kein WebGL bereit. Dort wird deshalb der SVG-Fallback verwendet. In einem normalen Browser mit WebGL kann der Sigma-WebGL-Renderer genutzt werden.

## Tests

- Gezielte Graph-/UI-/API-Tests: 25 Tests OK.
- Voller Testlauf: 122 Tests OK.

## Bekannte Einschraenkungen

- Das Layout ist serverseitig ForceAtlas2-aehnlich berechnet. Es nutzt nicht den browserseitigen Graphology-ForceAtlas2-Worker.
- Der erste Graph-Aufbau kann bei laufendem Pandorick einige Sekunden dauern.
- Neue Analyse-Events erscheinen nicht bei jedem einzelnen Event sofort im Graph, sondern kontrolliert nach Cache-Rebuild. Das verhindert Browser- und API-Lastspitzen.
