# Phase Knowledge Graph Engine Report

## Ziel

Die alte, selbst geschriebene Knowledge-Graph-Darstellung wurde durch eine professionelle Graph-Engine-Integration vorbereitet. Tradinglogik, Brain, Learning, Crypto, Stocks, Telegram und Decision Core wurden nicht veraendert.

## Backup

Backup der vorherigen Graph-Dateien:

`backups/knowledge_graph_before_engine_20260721_183125`

## Neue Dateien

- `learning_graph/graph_projection_service.py`
- `web/static/vendor/sigma.min.js`
- `web/static/vendor/graphology.umd.min.js`
- `web/static/knowledge_graph_legacy.js`
- `web/static/knowledge_graph_legacy.css`
- `web/static/knowledge_graph_bootstrap.js`
- `tests/test_graph_projection_service.py`

## Geaenderte Dateien

- `learning_graph/knowledge_graph_service.py`
- `web/api.py`
- `web/routes.py`
- `web/static/control_center.html`
- `web/static/knowledge_graph.js`
- `web/static/knowledge_graph.css`
- `web/static/knowledge_graph_legacy.js`
- `tests/test_knowledge_graph_phase2.py`
- `tests/test_knowledge_graph_ui_phase3.py`
- `tests/test_learning_graph_ui_phase7_2.py`
- `tests/test_learning_graph_ui_phase7_3.py`
- `package.json`
- `pnpm-lock.yaml`

## Engine

- Sigma.js und Graphology wurden lokal installiert und als statische Vendor-Dateien eingebunden.
- Die aktive Browser-Ansicht verwendet Sigma/Graphology, wenn WebGL im Browser verfuegbar ist.
- Fuer Browser ohne WebGL wurde ein automatischer Fallback auf die gesicherte SVG-Ansicht eingebaut.
- Die alte SVG-Datei bleibt als Fallback erhalten und wird nicht als primaere Engine verwendet.

## Projektionen

Neue Projektionen:

- `/api/v1/graph/overview`
- `/api/v1/graph/cluster/{cluster_id}`
- `/api/v1/graph/node/{node_id}`
- `/api/v1/graph/search?q=...`
- `/api/v1/graph/changes`
- `/api/v1/graph/full?min_edge_weight=...`

## Graph-Struktur

- Overview ist auf maximal 50 Knoten begrenzt.
- Full-Projektion ist auf maximal 500 Knoten begrenzt.
- Super-Knoten werden ueber starke Kanten begrenzt.
- Knoten bekommen oeffentliche Layout-Metadaten: `community`, `degree`, `size`, `label_visible`, `x`, `y`.
- Community-Erkennung erfolgt deterministisch ueber gewichtete Label-Propagation mit Daempfung zwischen unterschiedlichen Gruppen.
- Kanten lassen sich im Entwicklergraph ueber `min_edge_weight` filtern.

## UI

Neue Controls:

- Uebersicht
- Entwicklergraph
- Suchfeld
- Typfilter
- Clusterfilter
- Nur Nachbarn
- Kanten-Mindestgewicht
- Alles einpassen
- Graph zuruecksetzen
- Vollbild

## Live-Pruefung

API-Pruefung nach Neustart:

```json
{
  "status": "OK",
  "web_running": true,
  "websocket_active": true,
  "statistics_active": true
}
```

Knowledge-Graph-Overview:

```json
{
  "mode": "overview",
  "nodes": 50,
  "edges": 76,
  "version": 1,
  "sample": "PandorickKi"
}
```

## Tests

Ausgefuehrt:

```text
python -m unittest discover
```

Ergebnis:

```text
Ran 122 tests in 31.242s
OK
```

## Bekannte Einschraenkungen

- Der Codex In-App-Browser stellt in dieser Umgebung kein WebGL bereit. Deshalb wird dort automatisch der SVG-Fallback aktiviert.
- In einem normalen Browser mit WebGL-Unterstuetzung soll Sigma/WebGL als primaere Darstellung laufen.
- ForceAtlas2 ist als Dependency installiert, aber noch nicht als Browser-Bundle aktiv. Die aktuelle stabile Anordnung kommt serverseitig ueber Graph-Projektionen, Communities und Super-Knoten-Reduktion.
- Echte Edge-Bundling-Algorithmen wurden noch nicht eingebaut; aktuell werden Kanten transparent dargestellt, begrenzt und filterbar gemacht.

## Bestaetigung

- Keine Tradinglogik geaendert.
- Keine Brainlogik geaendert.
- Keine Crypto-/Stock-Analyse geaendert.
- Keine Telegramlogik geaendert.
- PandorickKi laeuft auf `http://127.0.0.1:8000/`.
