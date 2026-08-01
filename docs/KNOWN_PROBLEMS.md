# Bekannte Probleme

Stand: 1. August 2026

## Offen

### KP-001 – Storage-Scan überschreitet das Zeitlimit

- **Priorität:** niedrig
- **Status:** technisch behoben; nach Neustart im Dauerbetrieb beobachten
- **Frühere Beobachtung:** Ein realer Scan endete nach 35,236 Sekunden als `TIMEOUT`; 27 von 94 Dateiverweisen waren abgeschlossen.
- **Messung vom 1. August 2026:** Der schreibgeschützte Ist-Scan erfasste 105 physische Dateien und dauerte mit altem Budget 1,084 Sekunden. Ein Benchmark mit 64 MiB JSONL-Budget verarbeitete rund 68 MB in 2,135 Sekunden, deutlich unter dem 30-Sekunden-Limit.
- **Umsetzung:** Alle relevanten Phasen werden getrennt gemessen; der JSONL-Index meldet Bytes, Prozent, vollständige Dateien und geschätzte Restläufe. Das Standardbudget beträgt jetzt 64 MiB statt 256 KiB.
- **Restbeobachtung:** Bei weiter stark wachsendem Bestand Laufzeiten und Timeoutstatus kontrollieren. Keine Retention oder Löschung als Schnelllösung verwenden.
- **Neustartprüfung:** Nach dem kontrollierten Neustart dauerte ein Produktionsscan 2,416 Sekunden, bearbeitete 106/106 Dateien und erhöhte den JSONL-Fortschritt auf 9,20 %; kein Timeout trat auf.
- **Unabhängige Datenwarnung:** `stock_patterns.json` und dessen Backup `stock_patterns.before_json_repair_20260710_224237.json` enthalten vorhandene JSON-Syntaxfehler und halten den Gesamtstatus auf `DEGRADED`; sie wurden nicht verändert.

### KP-002 – WebSocket-Fallback und Reconnect sind unvollständig

- **Priorität:** hoch
- **Status:** offen
- **Beobachtung:** `close` startet ungeprüft ein neues Polling-Intervall, `error` setzt nur den Textstatus, Nachrichten werden ohne lokalen JSON-/Render-Fehlerpfad verarbeitet und ein Reconnect fehlt.
- **Auswirkung:** Die Oberfläche kann „Polling“ anzeigen, ohne zuverlässig weiterzuladen, oder mehrere Polling-Timer erzeugen.
- **Nächster Fix:** genau einen Polling-Timer verwalten, `error` und `close` idempotent behandeln, begrenzten Backoff-Reconnect ergänzen und mit Webtests absichern.

### KP-003 – Synchroner EventBus kann Publisher blockieren

- **Priorität:** mittel
- **Status:** offen
- **Beobachtung:** Handler werden synchron im veröffentlichenden Thread ausgeführt.
- **Auswirkung:** Langsame Datei-, Statistik- oder Netzwerkhandler verzögern Produzenten und nachfolgende Handler.
- **Hinweis:** Eine Entkopplung ist eine Architekturänderung und benötigt eigene Freigabe und Reihenfolgeverträge.

### KP-004 – Brain und Decision Core besitzen kein unabhängiges Freigabe-Gate

- **Priorität:** mittel
- **Status:** offen
- **Beobachtung:** Brain persistiert und reicht weiter; Decision Core normalisiert deterministisch.
- **Auswirkung:** Modulnamen können eine fachliche Prüfung suggerieren, die nicht implementiert ist.
- **Sicherheitsregel:** Daraus niemals automatische oder reale Orders ableiten.

### KP-005 – Telegram umgeht die finale Entscheidungskette

- **Priorität:** mittel
- **Status:** offen
- **Beobachtung:** Telegram abonniert Crypto-/Stock-Analysen und simulierte Crypto-Trade-Updates direkt.
- **Auswirkung:** Eine Nachricht kann vor oder unabhängig von `DECISION_CREATED`/`SIGNAL_CREATED` entstehen.
- **Sicherheitsregel:** Telegram deaktiviert beziehungsweise im Dry-Run lassen, bis ein explizites Gate entworfen und freigegeben ist.

### KP-006 – Keine zentrale Retention-Policy

- **Priorität:** mittel
- **Status:** offen
- **Beobachtung:** Einzelne Ledger rotieren, der Gesamtbestand wächst weiter.
- **Auswirkung:** Längere Backups, größere Scans und steigender Speicherverbrauch.
- **Sicherheitsregel:** Keine vorhandenen History- oder Lerndaten ohne ausdrückliche Aufbewahrungsentscheidung löschen.

### KP-007 – Feature-Eingänge werden nicht strikt validiert

- **Priorität:** mittel
- **Status:** offen
- **Beobachtung:** Keine verbindliche Sortierungs-, Duplikat-, OHLC-Konsistenz-, Non-Finite- oder Mindestkerzenprüfung.
- **Auswirkung:** Ungültige Eingangsdaten können Zwischenrechnungen und Warmup-Werte beeinflussen.

### KP-008 – Heartbeats werden nicht als veraltet klassifiziert

- **Priorität:** niedrig
- **Status:** offen
- **Beobachtung:** Zeitstempel werden angezeigt, aber es existiert keine zentrale `STALE`-Schwelle.

### KP-009 – Portabilität durch lokale Windows-Pfade eingeschränkt

- **Priorität:** niedrig
- **Status:** offen
- **Beobachtung:** Standard- und Batchpfade verweisen teilweise auf lokale externe Projekte.
- **Auswirkung:** Ein neuer Rechner benötigt explizite Pfadkonfiguration.

### KP-013 – Web-Stop reagiert erst nach dem Zyklusintervall

- **Priorität:** niedrig
- **Status:** offen; kontrollierter Shutdown funktioniert, reagiert aber verzögert
- **Beobachtung:** Der am 1. August 2026 gesendete `/api/control/stop`-Befehl wurde sofort akzeptiert, der Prozess beendete sich jedoch erst nach dem laufenden, nicht unterbrechbaren `asyncio.sleep(cycle_interval)` von bis zu 60 Sekunden.
- **Auswirkung:** Die Oberfläche zeigt einen akzeptierten Stop, während Port und Prozess noch bis zum nächsten Schleifendurchlauf aktiv bleiben.
- **Nächster Fix:** Im späteren UI-/Lebenszyklus-Schritt das Intervall über ein Abbruchereignis unterbrechbar machen und Stop-/Restart-Bedeutung eindeutig testen; bis dahin nicht voreilig hart beenden.

### KP-015 – Vollständige Raw Results vergrößern Event-Ledger

- **Priorität:** hoch
- **Status:** für Markt-Payloads implementiert, getestet und am 1. August 2026 live verifiziert
- **Beobachtung:** Brain und Decision Core persistieren und publizieren neue Stufen kompakt. NeuroBrain speichert neben seiner Kopfsicht nur noch die Version-1-Projektion.
- **Auswirkung:** Wiederholte Rohdaten und Kerzen vergrößern Brain-/Decision-/Signal-/NeuroBrain-Ledger und verlängern Storage-Scans.
- **Verifizierte Altpfade:** `CryptoTradeTracker` kann Swing-Werte weiterhin aus `raw_result.market_data.candles` lesen; `LearningGraphBuilder` kann das Ergebnis weiterhin aus `raw_result.result` lesen. Beide Pfade sind jetzt ausschließlich Fallback hinter den kompakten Feldern.
- **Vorbereitung:** `docs/EVENT_PAYLOAD_CONTRACT.md` und `event_payload_contract.py` definieren Version 1. Tracker und Graph bevorzugen die kompakten Ersatzfelder; vier Regressionstests sichern Priorität und Legacy-Kompatibilität.
- **Liveergebnis:** Drei saubere Produktionszyklen bestätigten kompakte Brain-, Decision-, Signal- und marktbezogene NeuroBrain-Zeilen ohne verbotene Bulk-Felder sowie eine vollständige ID-Kette. Bestehende History wurde nicht umgeschrieben oder gelöscht.

### KP-016 – NeuroBrain verwendet das Markt-Schema für nicht marktbezogene Topics

- **Priorität:** hoch
- **Status:** offen; live reproduziert am 1. August 2026
- **Beobachtung:** Neue NeuroBrain-Inboxzeilen für `AI_LEARNING_UPDATED` sowie einzelne reine Market-Data-Topics tragen `pandorickki.compact-market-event` Version 1, obwohl `market_type` oder `symbol` fehlen. Im geprüften neuen Bereich waren 18 von 94 Zeilen nach `contract_errors()` formal ungültig; alle geprüften eigentlichen Markt-, Brain-, Decision- und Signalzeilen waren gültig.
- **Auswirkung:** Downstream-Leser dürfen sich bei jeder NeuroBrain-Zeile derzeit nicht allein aufgrund des Schemanamens auf die Pflichtfelder verlassen.
- **Abgrenzung:** Die Zeilen enthalten keine verbotenen Bulk-Felder, die zweistufige Event-/Quell-ID bleibt erhalten und der laufende Dienst bleibt gesund. Bestehende Inboxzeilen wurden nicht verändert.
- **Nächster Fix:** Vor der Queue-/Batch-Entkopplung Topicgruppen und Schemazuständigkeit festlegen. Nicht marktbezogene Ereignisse entweder mit einem eigenen kompakten Lifecycle-Schema persistieren oder nur dann als Markt-Schema kennzeichnen, wenn alle Pflichtfelder vorhanden sind; Regressionstests für beide Gruppen ergänzen.

## Behoben oder entschärft

### KP-R10 – Outcome Tracker mischte naive und UTC-Zeitstempel

- **Status:** behoben, getestet und live verifiziert am 1. August 2026
- `_duration_seconds()` versieht ausschließlich geparste Zeitstempel ohne `tzinfo` mit UTC. Bereits offset-bewusste Werte behalten ihren tatsächlichen Offset.
- Bestehende offene Trades, Outcomes und andere Historydateien werden weder umgeschrieben noch gelöscht.
- Der öffentliche Regressionstest reproduzierte vor dem Fix das reale `OUTCOME_TRACKER_ERROR`; nach dem Fix wird der Legacy-Trade geschlossen, es entsteht kein Fehlerereignis und Tracker-Health bleibt gesund.
- Reine naive, reine offset-bewusste, gemischte und unterschiedlich offset-bewusste Zeitpaare sind abgedeckt.
- 12/12 Outcome-Tracker-Tests und 212/212 Gesamttests bestanden.
- Nach kontrolliertem Neustart und vier vollständigen Crypto-Heartbeats blieb der bekannte Journalfingerprint unverändert bei 158 Vorkommen; letztes Auftreten weiterhin 17:13:29 UTC. Alle zehn Services meldeten `OK`.

### KP-R09 – Historische Service-Exceptions verschwanden aus der In-Memory-Historie

- **Status:** behoben und getestet am 1. August 2026
- Ein standardmäßig aktives `ServiceErrorJournal` persistiert kompakte versionierte Projektionen von `SYSTEM_ERROR`, `service.error` und allen Themen mit Suffix `_ERROR`.
- Das aktive JSONL rotiert bei 5 MiB und behält höchstens vier Archive. Die atomar geschriebene Zusammenfassung behält höchstens 500 Fehlerfingerprints samt Anzahl sowie erster und letzter Beobachtung.
- Schlüssel- und Textfilter entfernen Tokens, API-Keys, Authorization-, Cookie-, Passwort-, Secret- und Chat-ID-Werte. Rohe Payloads und externe Response-Inhalte werden nicht kopiert.
- Journal-Schreibfehler brechen den Event-Publisher nicht und werden über `service_error_journal` als fehlerhafter Health-Zustand sichtbar.
- Der begrenzte Bestand ist bewusst kein vollständiges Langzeitarchiv; bestehende andere History-Dateien bleiben unverändert.
- 17/17 gezielte und 210/210 vollständige Tests bestanden.
- Live verifiziert: drei wiederkehrende Outcome-Tracker-Fehler wurden als ein Fingerprint mit erster/letzter Beobachtung erfasst; Journal-Health blieb `OK` und `failed_writes=0`.

### KP-R08 – Scannerfortschritt war nicht messbar und praktisch zu langsam

- **Status:** behoben und am realen Bestand schreibgeschützt vermessen am 1. August 2026
- Phasenlaufzeiten für Zielermittlung, Pfadauflösung, Metadaten, Fingerprint, Dateiverarbeitung, Index- und Cachepersistenz sind im Scanstatus enthalten.
- Der kumulative JSONL-Fortschritt bleibt über Läufe erhalten und zeigt Bytes, Prozent, vollständige Dateien, Restläufe und Restzeit.
- Das 64-MiB-Standardbudget blieb im Realbenchmark mit 2,135 Sekunden weit unter dem 30-Sekunden-Limit.
- 39/39 gezielte und 204/204 vollständige Tests bestanden.

### KP-R07 – Storage-Gesamtsummen zählten überlappende Ziele mehrfach

- **Status:** behoben und getestet am 1. August 2026
- `platform_data` umfasst vorhandene Dateien unter `data/`, während Brain-Events, rotierte Brain-Dateien und Shared State zusätzlich als eigene logische Kategorien erscheinen können.
- Der Scanner dedupliziert jetzt jeden aufgelösten physischen Pfad, scannt ihn nur einmal und verwendet das Ergebnis in allen zutreffenden Kategorien wieder.
- `total_*` und `physical_total_*` liefern physisch eindeutige Werte; `logical_total_*` beschreibt bewusst die Summe der Kategorieverweise und `overlapping_file_references` macht Überschneidungen sichtbar.
- Alte Cachedateien werden bis zum nächsten vollständigen Scan als `LEGACY_CACHE` markiert und beanspruchen keine verifizierten physischen Werte.
- 44/44 gezielte Storage-/Web-/Rick-API-Tests sowie 203/203 Gesamttests bestanden.

### KP-R06 – Storage-Worker schrieb nach `close()` weiter

- **Status:** behoben und deterministisch getestet am 1. August 2026
- Ein Regressionstest blockiert einen laufenden Cache-/Index-Schreibvorgang und reproduzierte vor dem Fix sowohl die verfrühte Rückkehr von `close()` als auch `WinError 145` beim anschließenden Entfernen des Testverzeichnisses.
- `close()` setzt jetzt einen dauerhaften geschlossenen Zustand, signalisiert Abbruch und wartet vollständig auf den aktiven Worker sowie einen gegebenenfalls synchron laufenden Refresh.
- Neue Scans werden nach `close()` mit `CLOSED` abgelehnt; wiederholtes `close()` bleibt sicher.
- Nach dem Fix bestanden der isolierte Regressionstest, 27/27 Storage-Tests, 36/36 Storage-/Webtests und 201/201 Gesamttests.

### KP-R05 – Crypto-Analyse seit 27. Juli ohne Ergebnisse

- **Status:** behoben und live verifiziert am 31. Juli 2026
- Externes `market.py` mit nicht verfügbarer `requests`-Abhängigkeit wird vom PandorickKi-Livepfad nicht mehr importiert.
- Interner Standardbibliotheks-Client verwendet Binance-Kerzen mit Bitget-Fallback und Retry.
- Open Interest und Funding sind optional und verwerfen keine gültigen Kerzen mehr.
- Service-Health meldet null Ergebnisse bei Fehlern als `ERROR` statt `OK`.
- 200/200 Tests bestanden; ein Live-Diagnoselauf und zwei Produktionszyklen lieferten insgesamt neun erfolgreiche Symbolanalysen ohne neuen Crypto-Fehler.

### KP-R04 – Arbeitsstand war nicht auf GitHub veröffentlicht

- **Status:** behoben
- Commit `38e1ddf` wurde auf `origin/agent/add-market-feature-engine` veröffentlicht.
- PR #2 wurde am 26. Juli 2026 nach `main` gemergt.
- Der spätere Crypto-Reparaturstand wurde als Commit `b0379c3` auf denselben Arbeitsbranch gepusht und liegt separat in Draft-PR #3: `https://github.com/cRioshy/Pando/pull/3`.
- Draft-PR #3 bleibt ungemergt.

### KP-R01 – Leere Speicheranzeige während langer Scans

- **Status:** entschärft
- Persistenter Cache wird beim Start geladen; Scans laufen im Hintergrund und blockieren den HTTP-Request nicht mehr.

### KP-R02 – Parallele Storage-Abfragen aus der Oberfläche

- **Status:** behoben
- Die UI verwendet einen Single-Flight-Lader für den vollständigen Storage-Snapshot.

### KP-R03 – Unbegrenzte Feature-Payloads aus sehr langen Kerzenreihen

- **Status:** entschärft
- Crypto- und Stock-Adapter begrenzen die Feature-Berechnung auf die letzten 500 Kerzen.
