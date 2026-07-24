# Phase Statistics And Storage Report

## Neue Dateien

- `web/statistics_service.py`
- `tests/test_statistics_and_storage.py`
- `PHASE_STATISTICS_AND_STORAGE_REPORT.md`

## Geaenderte Dateien

- `config.py`
  - neues Setting `storage_scan_interval_seconds`
  - ENV: `PANDORICKKI_STORAGE_SCAN_INTERVAL`
- `web/api.py`
  - persistente Analysezaehler
  - gecachter Storage-Scanner
  - WebSocket-Event `STATISTICS_UPDATED`
- `web/routes.py`
  - neue Statistik-API-Endpunkte
  - sicherer manueller Storage-Refresh
- `web/websocket_manager.py`
  - robustes Handling sauber getrennter Browser-Verbindungen
- `web/static/control_center.html`
  - Bereiche `Statistik` und `Datenspeicher`
- `web/static/control_center.css`
  - Layout fuer Statistik-Kacheln und Storage-Details
- `web/static/control_center.js`
  - Live-Rendering fuer Analyse- und Datenspeicherstatistik
- `tests/test_web_control_center.py`
  - WebSocket-Test auf neues `STATISTICS_UPDATED`-Frame angepasst
- `README.md`
  - Statistik-Hinweis ergaenzt

Bestehende Analyse- und Adapterlogik wurde nicht veraendert.

## Gezaehlte Events

- `CRYPTO_ANALYSIS_FINISHED`
  - `crypto_analyses +1`
  - `total_analyses +1`
  - Richtung LONG/SHORT/HOLD wird normalisiert gezaehlt
- `STOCK_ANALYSIS_FINISHED`
  - `stock_analyses +1`
  - `total_analyses +1`
  - Richtung LONG/SHORT/HOLD wird normalisiert gezaehlt
- `BRAIN_DECISION_RECEIVED`
  - `brain_evaluations +1`
- `DECISION_CREATED`
  - `decisions_created +1`
- `SIGNAL_CREATED`
  - `signals_created +1`
- `AI_LEARNING_UPDATED`
  - `learning_updates +1`
- `SYSTEM_ERROR` und Service-Fehler
  - `error_count +1`
- `TELEGRAM_MESSAGE_SENT`
  - `telegram_messages_sent +1`

Doppelte Events werden ueber `event_id` und eine Signatur aus Topic, Source, Symbol, Timeframe und Source-Timestamp erkannt. Doppelte Events erhoehen nur `duplicate_events_ignored`.

## Persistente Speicherform

Analysezaehler werden gespeichert in:

```text
storage/statistics/system_statistics.json
```

Gespeichert werden:

- alle Counter
- bekannte `event_id`s
- bekannte Event-Signaturen
- Rekonstruktionsstatus
- letzter Aktualisierungszeitpunkt

## Untersuchte Ordner

Tatsaechlich vorhandene Ziele werden gescannt. Nicht vorhandene Pfade werden nicht erfunden.

Bei diesem Lauf gefunden:

- `platform_data`
- `statistics`
- `stock_data`
- `stock_legacy_data`
- `brain_events`
- `shared_state`

Nicht vorhanden oder nicht auswertbar in diesem Projektlauf:

- `storage/market_history`
- `storage/calculations`
- `storage/decisions`
- `storage/signals`
- `storage/logs`
- `crypto_data`

## Unterstuetzte Dateitypen

- JSONL
  - gueltige nichtleere JSON-Zeilen
- CSV
  - Datenzeilen ohne Kopfzeile
- JSON
  - Listenlaenge
  - bekannte Listenfelder wie `decisions`, `signals`, `history`, `records`, `events`, `logs`, `data`, `items`, `memory`, `memories`
- SQLite
  - sichere `SELECT COUNT(*)`-Abfragen auf User-Tabellen im Read-only-Modus
- Log/TXT
  - Zeilenanzahl als `log_lines`

Beschaedigte Dateien stoppen den Scan nicht. Der betroffene Eintrag erhaelt `WARN` und eine Fehlermeldung.

## Scan-Intervall

Standard:

```text
60 Sekunden
```

Konfigurierbar ueber:

```powershell
$env:PANDORICKKI_STORAGE_SCAN_INTERVAL="60"
```

Der periodische Scan laeuft ueber `asyncio.to_thread(...)` und blockiert den EventLoop nicht. Browser-Refreshes lesen nur den Cache.

## API-Endpunkte

- `GET /api/statistics`
- `GET /api/statistics/analyses`
- `GET /api/statistics/storage`
- `GET /api/statistics/storage/{folder_name}`
- `POST /api/statistics/storage/refresh`

Die API gibt nur Metadaten aus: Anzahl, Groesse, Zeitstempel, Status und relative Pfadnamen. Keine Dateiinhalte und keine Secrets.

## WebSocket-Event

```text
STATISTICS_UPDATED
```

Payload enthaelt:

- aktuelle Analysezaehler
- Entscheidungszaehler
- Signalzaehler
- Fehleranzahl
- Gesamtzahl gespeicherter Datensaetze
- Gesamtgroesse
- Zeitpunkt der Aktualisierung

## Testergebnisse

Ausgefuehrt:

```powershell
C:\Users\Admin\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe -m unittest tests.test_statistics_and_storage
C:\Users\Admin\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe -m unittest tests.test_web_control_center
C:\Users\Admin\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe -m unittest discover
```

Ergebnis:

```text
tests.test_statistics_and_storage: 9 Tests OK
tests.test_web_control_center: 7 Tests OK
unittest discover: 48 Tests OK
```

## Rekonstruierte Werte

Stand des Abschlusslaufs:

```text
Vorhandene Analysen rekonstruiert: 555
Crypto-Analysen erkannt: 210
Stock-Analysen erkannt: 345
Brain-Auswertungen erkannt: 555
LONG: 59
SHORT: 0
HOLD/WAIT: 496
```

## Datenspeicher

Stand des Abschlusslaufs:

```text
Dateien gesamt: 20
Datensaetze gesamt: 10037
Speicherplatz gesamt: 79.58 MB
```

Ordner:

```text
platform_data       693 Datensaetze    10.81 MB   OK
statistics          nicht eindeutig    78.40 KB   OK
stock_data          8451 Datensaetze   57.41 MB   OK
stock_legacy_data   306 Datensaetze    847.04 KB  OK
brain_events        587 Datensaetze    10.46 MB   OK
shared_state        nicht eindeutig    1.54 KB    OK
```

Nicht zuverlaessig als Datensatzmenge ausgewertet:

- `statistics`
- `shared_state`

Grund: JSON-Objekte ohne eindeutig zaehlbares Listenfeld werden nicht geraten.

## Bekannte Einschraenkungen

- Rekonstruktion zaehlt nur vorhandene historische Daten, die klare Markt- und Richtungsfelder enthalten.
- JSON-Dateien ueber 10 MB werden nicht vollstaendig in den RAM geladen; ihre `record_count` bleibt bei unklarer Struktur `null`.
- Service-spezifische Restart-Buttons bleiben sichere Control-Events und starten keine fremden Prozesse neu.
- Keine oeffentliche Freigabe, keine Web-App-Deployment-Funktion und keine mobilen Push-Statistiken.

## Abschluss

- Vorhandene Analysen rekonstruiert: `555`
- Crypto-Analysen erkannt: `210`
- Stock-Analysen erkannt: `345`
- Datensaetze insgesamt gefunden: `10037`
- Speicherplatz belegt: `79.58 MB`
- Nicht zuverlaessig ausgewertet: `statistics`, `shared_state`
- Browseranzeige aktualisiert live: Ja, ueber WebSocket `STATISTICS_UPDATED`
- Alle Tests erfolgreich: Ja, `48 Tests OK`
