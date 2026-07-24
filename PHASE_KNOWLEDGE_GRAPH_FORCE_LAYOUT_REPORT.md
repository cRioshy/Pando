# Knowledge Graph Force Layout Report

## Analyse

Der aktuelle Graph enthaelt live:

- 56 Knoten
- 159 Kanten
- Cluster: patterns 25, indicators 10, stocks 6, decisions 5, infrastructure 4, crypto 4, system 1, brain 1

Die wichtigsten Super-Knoten nach Verbindungsanzahl:

- brain:brain:pandorick_brain: 31
- stock:stocks:tsla: 20
- stock:stocks:msft: 20
- stock:stocks:nvda: 20
- stock:stocks:aapl: 20
- stock:stocks:spcx: 14
- crypto:crypto:ethusdt: 10
- crypto:crypto:btcusdt: 10

## Ursache

Ein Force-Layout war bereits aktiv, aber es war eine einfache selbstgeschriebene SVG-Force-Simulation.

Die Knoten fanden nicht sauber zu Clustern, weil:

- Super-Knoten wie Brain, Stock-Symbole, Decisions und Indicators viele Cluster gleichzeitig verbunden haben.
- Cross-Cluster-Kanten zu stark gezogen haben.
- Cluster-Zentren zu eng lagen.
- Knoten-Groessen fast alle durch hohe Counts an die Maximalgroesse liefen.
- Es gab keine Velocity-/Alpha-Daempfung wie bei einer typischen Force-Simulation.

## Vorher

- Arbeitsflaeche: 1800 x 1100
- einfache Pull-/Push-Kraefte
- Cross-Cluster-Linkdistanz: ca. 340
- Cluster-Schwerkraft: schwach
- Kanten zogen Super-Knoten zu stark zusammen
- Groessenberechnung stark von rohen Counts gepraegt

## Nachher

- Arbeitsflaeche: 2200 x 1350
- echte iterative Force-Simulation mit Velocity, Alpha und Daempfung
- Relation-spezifische Link-Distanzen
- schwache Cross-Cluster-Zugkraft
- staerkere Cluster-Schwerkraft
- groessere Cluster-Abstaende
- Knotengroesse aus Typ, Importance, Degree, gewichteten Kanten und logarithmischem Count
- Reset leert Positionen, manuelle Pins, Velocity und Layout-Signatur

## Geaenderte Dateien

- `web/static/knowledge_graph.js`
- `tests/test_knowledge_graph_ui_phase3.py`

## Tests

- `python -m unittest tests.test_knowledge_graph_ui_phase3`: OK, 8 Tests
- `python -m unittest discover`: OK, 114 Tests

## Hinweis

Die API und alle Trading-, Brain-, Learning-, Crypto-, Stock- und Adaptermodule blieben unveraendert.
