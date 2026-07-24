# Phase 5 - Learning Graph UI

## Ziel

Phase 5 macht den Pandorick Learning Graph im bestehenden Web-ControlCenter sichtbar.

Die bestehende Analyse-, Adapter-, Signal-, Telegram-, Brain- und Trade-Logik wurde nicht veraendert.

## Geaenderte Dateien

- `web/static/control_center.html`
  - Neuer Bereich `Learning Graph` im Dashboard.
  - Anzeige fuer Knoten, Verbindungen, Analysen, Muster, Learnings, Maerkte, Status und Update-Zeit.
  - Knoten-, Kanten- und Detailspalten.
  - Button `Graph aktualisieren`.

- `web/static/control_center.js`
  - Holt Graph-Daten ueber `GET /api/v1/learning-graph`.
  - Holt Knotendetails ueber `GET /api/v1/learning-graph/node/{node_id}`.
  - Aktualisiert den Graph automatisch alle 5 Sekunden.
  - Zeigt keine internen Dateien und keine Rohdaten an.

- `web/static/control_center.css`
  - Layout und Darstellung fuer Graph-Statistiken, Knoten, Kanten und Details.
  - Responsives Verhalten fuer kleine Bildschirme.

## Neue Dateien

- `tests/test_learning_graph_ui_phase5.py`
  - Prueft, dass der Learning-Graph-Bereich in der HTML-Seite existiert.
  - Prueft, dass das JavaScript nur die oeffentlichen API-Endpunkte nutzt.
  - Prueft, dass keine internen Brain-Dateien oder geheimen Felder direkt im Frontend abgefragt werden.

## Backup

Vor den Aenderungen wurde ein Backup erstellt:

- `backups/phase_learning_graph_before_phase5`

Die Desktop-Kopie wurde ebenfalls mit einem Backup aktualisiert:

- `C:/Users/Admin/Desktop/PandorickKi/backups/phase_learning_graph_before_phase5_desktop`

## Aktualisierung

Die Workspace-Version wurde getestet.

Die Desktop-Version unter `C:/Users/Admin/Desktop/PandorickKi` wurde mit den Phase-4- und Phase-5-Dateien aktualisiert.

Der bereits laufende Server auf `http://127.0.0.1:8000` hatte vor dem Neustart noch alten Code im Speicher und lieferte fuer `/api/v1/learning-graph` einen 404. Nach einem Neustart des Desktop-Servers werden die neuen Routen und die neue UI geladen.

## Tests

Gezielte Tests:

```text
python -m unittest tests.test_learning_graph_phase3 tests.test_learning_graph_api_phase4 tests.test_learning_graph_ui_phase5 tests.test_web_control_center
Ran 22 tests
OK
```

Gesamttests:

```text
python -m unittest discover -s tests
Ran 72 tests
OK
```

Hinweis: Die volle Test-Suite zeigt bestehende `DeprecationWarning`-Meldungen aus dem alten Crypto-Projekt wegen `datetime.utcnow()`. Das ist kein neuer Fehler aus Phase 5.

## Start

Empfohlener Start nach Neustart des alten Servers:

```text
python main.py --headless --web
```

Danach:

```text
http://127.0.0.1:8000/
```

## Bekannte Einschraenkungen

- Der Graph ist in Phase 5 als Listen-/Detailansicht umgesetzt, noch nicht als Canvas- oder Netzwerkvisualisierung.
- Die automatische Aktualisierung laeuft alle 5 Sekunden.
- Der aktuell laufende Port-8000-Prozess muss neu gestartet werden, damit der alte Code aus dem Speicher verschwindet.
