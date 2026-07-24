# Phase 7.3 - Graph View Polish

## Ziel

Phase 7.3 verbessert die bestehende Netzwerkansicht optisch und interaktiv.

Es wurden keine API-, Trading-, Brain-, Crypto-, Stock- oder Telegram-Module veraendert.

## Geaenderte Dateien

- `web/static/control_center.html`
  - Suchleiste fuer Learning-Graph-Knoten ergaenzt.

- `web/static/control_center.js`
  - Cluster-Layout fuer Crypto, Stocks, Indikatoren, Pattern, Learning, Entscheidungen, Ergebnisse und System.
  - Groessere Abstaende zwischen Clustern.
  - Kollisionsentschaerfung fuer Knoten.
  - Gekuerzte Labels und versetzte Labelpositionen.
  - Doppelklick zentriert einen Knoten.
  - Suche fokussiert passende Knoten.
  - Einzelne Knoten koennen gezogen werden.
  - Fenster-Resize passt die Ansicht automatisch ein.
  - Direkte Nachbarn werden hervorgehoben, nicht verbundene Elemente abgedunkelt.

- `web/static/control_center.css`
  - Suchfeld-Layout.
  - Transparentere Kanten.
  - Hover-Effekt fuer Knoten.
  - Sanfte Einblendanimation.
  - Hervorhebung direkter Verbindungen.

## Neue Dateien

- `tests/test_learning_graph_ui_phase7_3.py`

## Tests

Gezielte UI-Tests:

```text
Ran 15 tests
OK
```

Gesamttests:

```text
Ran 87 tests
OK
```

## Sicherheit

- Keine Demo-Daten.
- Keine Rohdaten aus internen Dateien.
- Keine internen Formeln, Gewichtungen, Reasoning-Felder, Tokens oder API-Keys im Frontend.
- Datenquelle bleibt die bereinigte API `/api/v1/learning-graph`.

## Bekannte Einschraenkungen

- Cytoscape.js ist weiterhin nicht eingebunden, weil keine lokale Bibliothek vorhanden ist.
- Export als PNG ist noch nicht umgesetzt.
- Weitere Filter kommen in Phase 7.4 beziehungsweise einer separaten Filterphase.

## Phase 7.3.2 - Force Layout

Phase 7.3.2 ersetzt die ringfoermige Netzwerk-Anordnung durch eine begrenzte native SVG-Force-Simulation ohne CDN und ohne Internetabhaengigkeit.

### Geaenderte Dateien

- `web/static/control_center.js`
  - Force-Directed-Layout mit Repulsion, Link-Anziehung, Cluster-Anziehung und weicher Zentrierung.
  - Cluster nach Crypto, Stocks, Brain, System, Indicators, Patterns, Learnings, Decisions, Results und Unconnected.
  - Bounding Box gegen Ausreisser.
  - Stabile Positionen zwischen Auto-Refreshs durch `layoutPositions`.
  - Neue Knoten starten nahe ihres Clusters.
  - Knotenradius je Typ begrenzt.
  - Labels standardmaessig nur fuer MARKET und SYSTEM, sonst bei Hover, Auswahl oder hoeherem Zoom.
  - Tooltips zeigen den vollstaendigen Knotennamen.
  - Zoom-Grenzen 0.25 bis 4.0.
  - Mausrad-Zoom bleibt am Mauspunkt.

- `web/static/control_center.css`
  - Linien deutlich transparenter.
  - Label-Hintergrund fuer lesbare Beschriftungen.
  - Dezente Cluster-Titel.
  - Hover- und Auswahlzustand ruhiger hervorgehoben.

- `tests/test_learning_graph_ui_phase7_3.py`
  - Tests fuer Force-Layout-Hooks, Cluster, Bounding Box, Labelregeln, Hover/Fokus und neue CSS-Regeln erweitert.

### Verwendeter Layout-Ansatz

Native JavaScript-Force-Simulation mit fester Iterationsgrenze. Die Simulation stoppt nach der Berechnung und laeuft nicht dauerhaft weiter, damit der Pandorick-Prozess nicht ausgebremst wird.

### Testergebnisse

Gezielte UI-Tests:

```text
Ran 17 tests
OK
```

Gesamttests:

```text
Ran 89 tests
OK
```

### Live-Pruefung

- `GET /` liefert HTTP 200.
- `GET /api/health` liefert `status: OK`.
- `GET /api/v1/learning-graph/stats` liefert echte Daten: 59 Knoten, 136 Verbindungen.
- Der laufende Server liefert die aktualisierten Dateien `control_center.js` und `control_center.css` aus.

### Nicht geaendert

- Keine Tradinglogik geaendert.
- Brain unveraendert.
- API unveraendert.
- Crypto-, Stock-, Telegram- und Adapterlogik unveraendert.
- `graph_sanitizer` unveraendert.

### Einschraenkung

Ein automatischer Browser-Screenshot konnte in dieser Sitzung nicht erstellt werden, weil keine ausfuehrbare In-App-Browser-Steuerung bereitgestellt wurde. Die Server- und Asset-Pruefung wurde per lokalem HTTP durchgefuehrt.
