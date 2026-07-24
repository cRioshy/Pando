# Phase 7.2 - Interactive Network View

## Ziel

Phase 7.2 fuegt dem bestehenden Learning Graph eine interaktive Netzwerkansicht hinzu.

Die bestehende Listenansicht bleibt erhalten.

## Geaenderte Dateien

- `web/static/control_center.html`
  - Umschalter `Liste` / `Graph`.
  - SVG-Netzwerkcontainer.
  - Buttons fuer `Alles einpassen` und `Ansicht zuruecksetzen`.
  - Legendenbereich.
  - Gemeinsames sicheres Detailpanel.

- `web/static/control_center.js`
  - Native SVG-Netzwerkdarstellung aus bereinigten API-Nodes und API-Edges.
  - Knoten anklicken.
  - Nachbarn hervorheben.
  - Nicht verbundene Knoten abdunkeln.
  - Zoom per Mausrad.
  - Verschieben der Ansicht per Drag.
  - Node-/Edge-Deduplizierung.
  - Sichtbares Standardlimit: 300 Knoten, 800 Kanten.

- `web/static/control_center.css`
  - Netzwerkflaeche mit dunklem Hintergrund.
  - Knotentyp-Farben.
  - Responsive Layout fuer Desktop und Mobile.

## Neue Dateien

- `tests/test_learning_graph_ui_phase7_2.py`

## Verwendete Graph-Technik

Phase 7.2 nutzt eine native SVG-Netzwerkansicht.

Grund: Cytoscape.js ist nicht lokal im Projekt vorhanden und es wurde keine externe Cloud-Abhaengigkeit eingebunden.

## Sicherheit

- Keine API-, Trading-, Brain-, Crypto- oder Stock-Logik geaendert.
- Keine Demo-Daten.
- Keine Rohdateien im Browser.
- Keine internen Formeln, Gewichtungen, Reasoning-Felder oder Tokens im Frontend.
- Die Netzwerkansicht nutzt ausschliesslich die bereits bereinigte API `/api/v1/learning-graph`.

## Tests

Gezielte Tests:

```text
Ran 17 tests
OK
```

Gesamttests:

```text
Ran 81 tests
OK
```

Hinweis: Bestehende `DeprecationWarning`-Meldungen aus dem alten Crypto-Projekt bleiben unveraendert und sind kein Fehler aus Phase 7.2.

## Bekannte Einschraenkungen

- Filter und Suche kommen erst in Phase 7.3.
- Live-Update-Feinschliff und Layout-Stabilisierung kommen in Phase 7.4.
- Export als PNG ist noch nicht eingebaut.
