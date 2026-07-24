# Phase 10.2 - Brain Event Rotation

Stand: 2026-07-14

## Ziel

Phase 10.2 fuehrt eine zentrale Reader-/Writer-Schicht fuer Brain-Events ein. Neue Brain-Events werden nicht mehr in die grosse Legacy-Datei `data/brain_events.jsonl` geschrieben, sondern append-only in eine rotierende Tagesstruktur.

Tradinglogik, Decision Core, Brain-Bewertung, Learning-Algorithmen, Crypto Engine, Stock Engine, Telegram und Signalberechnung wurden nicht fachlich veraendert.

## Neue Struktur

```text
data/
  brain_events.jsonl              # Legacy-Datei, bleibt unveraendert
  brain_events/
    manifest.json
    YYYY-MM-DD/
      events_0001.jsonl
      events_0002.jsonl
      index.json
```

## Neue Dateien

- `brain_event_store.py`
- `tests/test_brain_event_store.py`
- `PHASE_10_2_BRAIN_EVENT_ROTATION_REPORT.md`

## Geaenderte Dateien

- `adapters/brain_adapter.py`
- `config.py`
- `orchestrator.py`
- `learning_graph/graph_repository.py`
- `learning_graph/graph_service.py`
- `web/api.py`
- `web/statistics_service.py`
- `tests/test_brain_adapter.py`
- `tests/test_integration_full.py`
- `tests/test_orchestrator_stock.py`

## Backup

Vor der Aenderung wurde ein Backup der betroffenen Code-Dateien erstellt:

```text
backups/phase10_2_before_20260714_212317
```

## Writer

Der neue `BrainEventWriter` schreibt:

- pro Kalendertag in einen eigenen Ordner
- append-only JSONL
- Rotation standardmaessig bei 200 MB
- Tageswarnung ab ca. 1,5 GB
- atomische `index.json`- und `manifest.json`-Updates ueber Temp-Datei plus `os.replace`
- thread-sicher ueber Lock
- mit Flush und periodischem fsync

Neue Events bekommen eine technische `event_id`, falls keine stabile Event-ID vorhanden ist. Diese ID dient nur zur Deduplizierung und veraendert keine Tradinglogik.

## Reader

Der neue `BrainEventReader` liest kompatibel aus:

- alter `data/brain_events.jsonl`
- neuer rotierter Struktur `data/brain_events/`
- beiden Quellen gemeinsam

Dubletten werden ueber `event_id`, `source_event_id` oder eine deterministische Hash-ID aus sicheren Feldern entfernt.

Unvollstaendige letzte JSONL-Zeilen werden beim Lesen uebersprungen und als Warnung im Reader vermerkt.

## Integration

- `BrainAdapter` schreibt neue Events ueber `BrainEventWriter`.
- `Orchestrator` uebergibt Rotationspfad und Grenzwerte aus der Config.
- `LearningGraphService` und `GraphRepository` lesen Brain-Events ueber `BrainEventReader`.
- `AnalysisStatisticsService` kann Brain-Events ueber den zentralen Reader rekonstruieren.
- `StorageStatisticsService` erkennt die neue rotierte Brain-Event-Struktur als eigenen Speicherbereich.
- `StorageStatisticsService` ueberspringt beim Start die vollstaendige Zeilenzahlung einer riesigen Legacy-`brain_events.jsonl` und zeigt stattdessen Metadaten mit `record_count_status=skipped_large_jsonl`. Das verhindert, dass der Webserver vor dem Port-Bind minutenlang blockiert.

## Konfiguration

Neue Konfigurationswerte:

- `brain_events_dir`
- `brain_event_rotation_bytes`
- `brain_event_day_warning_bytes`

Neue Environment-Variablen:

- `PANDORICKKI_BRAIN_EVENTS_DIR`
- `PANDORICKKI_BRAIN_EVENT_ROTATION_BYTES`
- `PANDORICKKI_BRAIN_EVENT_DAY_WARNING_BYTES`

## Tests

Ausgefuehrt:

```text
python -m py_compile brain_event_store.py adapters/brain_adapter.py config.py orchestrator.py learning_graph/graph_repository.py learning_graph/graph_service.py web/api.py web/statistics_service.py
python -m unittest tests.test_brain_event_store tests.test_brain_adapter
python -m unittest tests.test_statistics_and_storage
python -m unittest tests.test_integration_full tests.test_orchestrator_stock
python -m unittest tests.test_live_control_center.LiveControlCenterTest.test_live_and_headless_cli_modes_start tests.test_live_control_center.LiveControlCenterTest.test_live_cli_control_off_falls_back_to_headless
python -m unittest discover
```

Ergebnis:

```text
Ran 97 tests in 37.487s
OK
```

## Nicht umgesetzt in Phase 10.2

Bewusst noch nicht umgesetzt:

- kein inkrementeller Learning-Graph-Cache
- keine API-Umstellung auf Cache
- keine SQL-Migration
- keine automatische Komprimierung
- keine automatische Loeschung alter Daten

Diese Punkte gehoeren zu Phase 10.3 oder spaeter.

## Ergebnis

Phase 10.2 ist in der Projektkopie abgeschlossen. Die Legacy-Datei bleibt erhalten, neue Events laufen ueber die neue rotierende Struktur, und alle vorhandenen Tests sind erfolgreich.
