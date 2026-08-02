# Session-Handover

## Aktuelle Aufgabe: Control-Center-UI und Lebenszyklus härten

### Datum und Uhrzeit

2. August 2026, 13:26 Uhr, Europe/Berlin (`+02:00`)

### Ziel der Aufgabe

Die vereinbarte UI-Härtung vollständig umsetzen: WebSocket-Reconnect und genau einen stabilen Polling-Timer, danach zentrale `STALE`-Heartbeats, schnelle und echte Stop-/Restart-Reaktion sowie bessere Learning-Graph-Performance. Bestehende Runtime-, History-, Lern- und Konfigurationsdaten mussten unverändert bleiben; echte Trades und Telegram-Liveversand durften nicht aktiviert werden.

### Durchgeführte Arbeiten

- Pflichtdokumentation vollständig gelesen und den tatsächlichen Code in Webserver, Control State, Orchestrator, Control-Center-JavaScript und Tests abgeglichen.
- Browserstatusverwaltung um genau einen idempotenten Polling-Fallback und single-flight Statusabrufe ergänzt.
- WebSocket-Reconnect mit begrenztem exponentiellem Backoff, Verbindungsgeneration gegen alte Callbacks, `error`-/`close`-Fallback und lokalem JSON-/Render-Fehlerpfad umgesetzt.
- Zentrale Heartbeat-Altersberechnung in REST- und leichten WebSocket-Snapshots ergänzt. Bekannte Heartbeats werden nach standardmäßig 150 Sekunden als `STALE` klassifiziert; Schwelle über `PANDORICKKI_SERVICE_HEARTBEAT_STALE_SECONDS` konfigurierbar.
- Orchestrator-Warteabschnitt auf 100-ms-Kontrollpunkte umgestellt. Stop kann den langen Zyklus-Sleep verlassen; Restart konsumiert die Anfrage atomar, stoppt und startet dieselben Adapterinstanzen im Prozess und startet bei Bedarf die Terminal-Liveansicht wieder.
- Restart-Befehl erhält nach Ausführung `APPLIED` und `completed_at`.
- Steuerereignis von `SERVICE_STATUS_CHANGED` auf `CONTROL_COMMAND_APPLIED` korrigiert, damit kein Phantom-Service `web_control_center` entsteht.
- Learning Graph auf single-flight Laden, Skip in ausgeblendeten Tabs, `requestAnimationFrame`-Koaleszierung und Layout-Wiederverwendung bei unveränderter Knoten-/Kantenstruktur umgestellt.
- Gezielte und vollständige Regressionstests ergänzt und ausgeführt.
- PandorickKi mehrfach ausschließlich kontrolliert über die lokale Stop-API beendet und mit Live-Crypto, NeuroBrain-Queue, Telegram aus und Dry-Run über die projektlokale `.venv` wieder gestartet.
- Offene Browserseite über einen vollständigen Prozessneustart hinweg beobachtet: Sie fiel zurück und verband sich ohne manuelles Reload wieder per WebSocket.
- Echten In-Process-Restart über den sichtbaren Restart-Button ausgeführt und serverseitig bis `APPLIED` geprüft.
- Learning Graph live geöffnet und Browserfehler geprüft.
- Systemzustand, Architektur, bekannte Probleme und nächste Schritte auf den tatsächlich verifizierten Stand aktualisiert.
- Den vollständigen Stand als lokalen Commit auf `agent/harden-control-center-ui` gesichert.

### Veränderte Dateien

- `config.py`
- `main.py`
- `orchestrator.py`
- `web/api.py`
- `web/schemas.py`
- `web/static/control_center.js`
- `tests/test_parallel_orchestrator.py`
- `tests/test_web_control_center.py`
- `docs/CURRENT_SYSTEM_STATE.md`
- `docs/ARCHITECTURE.md`
- `docs/KNOWN_PROBLEMS.md`
- `docs/NEXT_STEPS.md`
- `docs/SESSION_HANDOVER.md`

### Neue Dateien

- Keine versionierten Dateien.
- Ignorierte, leere Laufzeitlogs unter `runtime_logs/ui_hardening_*.stdout.log` und `runtime_logs/ui_hardening_*.stderr.log` entstanden durch die kontrollierten Hintergrundstarts.

### Ausgeführte Befehle

- Vollständiges Lesen von `AGENTS.md` sowie `docs/CURRENT_SYSTEM_STATE.md`, `docs/SESSION_HANDOVER.md`, `docs/ARCHITECTURE.md`, `docs/KNOWN_PROBLEMS.md` und `docs/NEXT_STEPS.md`.
- Code- und Testinventur mit `rg`, `Get-Content`, `git status`, `git diff`, `git diff --check` und `node --check`.
- Gezielte `unittest`-Läufe für `tests.test_parallel_orchestrator` und `tests.test_web_control_center`.
- Zwei vollständige `unittest discover -s tests -p 'test_*.py'`-Abschlussläufe.
- Dreifache isolierte Wiederholung des einmalig zeitlich ausgefallenen WebSocket-Tests.
- Read-only HTTP-Prüfungen auf `/api/status`, `/api/health` und `/api/config/public`.
- Kontrollierte POSTs auf `/api/control/stop` und ein sichtbarer POST über den Restart-Button.
- Verdeckte `Start-Process`-Starts mit `.venv\Scripts\python.exe main.py --headless --web`; Telegram dabei explizit deaktiviert und Dry-Run aktiv.
- Browser-DOM-, Graph- und Konsolenprüfung im lokalen Control Center.
- Dateiänderungen ausschließlich über `apply_patch`.

### Ausgeführte Tests

- 15 gezielte Web-/Orchestrator-Regressionstests.
- Vollständige Python-Testsuite.
- JavaScript-Syntaxprüfung für `web/static/control_center.js`.
- `git diff --check`.
- Live-Reconnect über vollständigen Prozessneustart.
- Live-In-Process-Restart über den Restart-Button.
- Live-Graphdarstellung und Browserkonsole.
- Live-API- und Sicherheitskonfiguration.

### Tatsächliche Testergebnisse

- Gezielte Tests: 15/15 bestanden.
- Finaler vollständiger Lauf: 243/243 Tests in 43,586 Sekunden bestanden.
- JavaScript-Syntax und `git diff --check`: bestanden.
- In einem früheren vollständigen Lauf wartete der vorhandene WebSocket-Test einmal vergeblich auf seinen zweiten Frame. Derselbe Test bestand davor gezielt, danach dreimal isoliert und im finalen vollständigen Lauf; kein reproduzierbarer Produktfehler.
- In-Process-Restart: `ACCEPTED` um 11:19:26.839 UTC, `APPLIED` um 11:19:26.943 UTC, rund 104 ms; WebSocket blieb verbunden und Services kehrten auf OK zurück.
- Vollständiger kontrollierter Stop: Port 8000 nach 2,326 Sekunden frei. Der frühere bis zu 60 Sekunden lange Sleep-Block trat nicht mehr auf.
- Reconnect: Bereits geöffnete Seite wechselte nach vollständigem Prozessneustart ohne Reload wieder auf `WebSocket`.
- Final live: Plattform `OK`, exakt zehn Services, kein Phantom-Service, Heartbeat-Alter im WebSocket-Snapshot, Telegram `enabled=false` und `dry_run=true`.
- Graph: 76 Knoten und 179 Kanten sichtbar; keine Browserfehler.
- Finale Runtime-stderr-Datei: 0 Byte.

### Bekannte Fehler

- Ein bereits laufender Adapterzyklus wird aus Sicherheitsgründen nicht hart abgebrochen. Stop/Restart unterbrechen den Warteabschnitt; aktive externe Analysearbeit kann die vollständige Prozessbeendigung weiterhin bis zum Zyklusende verzögern.
- Services ohne jemals beobachteten Heartbeat können nicht als `STALE` bewertet werden und behalten ihren sonstigen Status.
- `KP-003`, `KP-004`, `KP-005`, `KP-006`, `KP-007`, `KP-009` und `KP-017` bleiben laut `docs/KNOWN_PROBLEMS.md` offen.
- Bekannte `datetime.utcnow()`-Deprecation-Warnungen stammen weiterhin aus dem externen Legacy-Crypto-Projekt.

### Getroffene Architekturentscheidungen

- Polling ist ausschließlich ein singletonartiger WebSocket-Fallback, kein parallel laufender zweiter Livekanal.
- Reconnect verwendet begrenzten Backoff; alte Socket-Callbacks dürfen den neuen Verbindungszustand nicht überschreiben.
- `STALE` ist eine zentrale API-Projektion und nicht nur Browserkosmetik. Fehler- und Stopzustände haben Vorrang.
- Restart ist ein echter In-Process-Adapterrestart; der Webserver bleibt erreichbar. Bereits laufende Adapterzyklen werden nicht aggressiv abgebrochen.
- Steuerbefehle sind keine Servicezustände.
- Graph-Layout wird durch Strukturänderungen invalidiert; reine Liveupdates und Interaktionen verwenden vorhandene Positionen und Frame-Koaleszierung.
- Keine Runtime-, History-, Lern-, Token- oder Konfigurationsdatei wurde gelöscht oder umgeschrieben. Keine reale Orderausführung und kein Telegram-Liveversand wurden aktiviert.

### Nicht abgeschlossene Punkte

- Der Arbeitsstand ist lokal auf `agent/harden-control-center-ui` committed. Ein GitHub-Push und Draft-PR wurden in dieser Aufgabe noch nicht ausgeführt.
- Feature-Datenqualitätsvertrag, Decision Gate und Telegram-Kette wurden bewusst noch nicht begonnen.

### Exakter nächster sinnvoller Arbeitsschritt

Den lokalen UI-Härtungscommit – nur mit bestehender Veröffentlichungsfreigabe – als gestapelten Draft-PR gegen `agent/unify-learning-metrics` pushen. Erst anschließend in einem eigenen kleinen Arbeitsschritt die tatsächlichen Feature-Eingänge und Consumer inventarisieren und einen versionierten Datenqualitätsvertrag für Sortierung, Duplikate, OHLC-Konsistenz, Non-Finite-Werte und Warmup entwerfen; noch kein Decision Gate und keinen Telegram-Livepfad implementieren.

## Aktuelle Aufgabe: Learning-Metriken vereinheitlichen

### Datum und Uhrzeit

2. August 2026, 12:33 Uhr, Europe/Berlin (`+02:00`)

### Ziel der Aufgabe

Learning-, Outcome-, Hit-Rate-, Pattern- und Trainingsmetriken fachlich vereinheitlichen. Begriffe und Nenner offenlegen, eine belastbare Outcome-Abdeckung bereitstellen, Projektionen klar von echtem ML-Training trennen, bestehende API-Leser kompatibel halten und den Stand testgetrieben sowie live prüfen. Keine bestehenden History-, Statistik- oder Lerndaten verändern und weder echte Trades noch Telegram-Versand aktivieren.

### Durchgeführte Arbeiten

- Pflichtdokumentation, tatsächliche Repository-Struktur, Decision-/Outcome-Ledger, Learning Report, persistente Statistikrekonstruktion, Learning Graph und Control-Center-Renderer geprüft.
- Den ausführbaren Vertrag `pandorickki.learning-metrics` Version 1 eingeführt. Hit-Rate ist einheitlich `wins / (wins + losses)`; Breakeven und Unknown sind ausgeschlossen und separat sichtbar. Jede Rate liefert Zähler und Nenner.
- Outcome-Abdeckung als geschlossene, per `decision_id` zugeordnete Outcomes geteilt durch outcome-fähige LONG-/SHORT-Decisions desselben Scopes definiert.
- Learning Report auf exakte ID-Zuordnung umgestellt. Ein alter Report-Cache ohne Vertrag wird beim normalen Lesen verworfen und neu aufgebaut; die Datei wird nicht aktiv gelöscht.
- Persistente Trading-Statistik auf denselben Hit-Rate-Nenner umgestellt. Bei historisch inkompatiblen Zählerständen wird keine Quote erfunden, sondern `null` mit `outcome_coverage_scope_consistent=false` geliefert.
- `AI_LEARNING_UPDATED` als Projektionsereignis ausgewiesen. `successful_learnings` und `learned_patterns` werden nicht mehr aus Eventzählern erfunden; ML-Status ist `active=false`, Modellupdates sind null beziehungsweise 0 gemäß Vertrag.
- Learning Graph trennt Muster-Buckets, heutige Projektionen im geladenen Fenster und kumulative Learning-Update-Events.
- Control Center in „Outcome-Auswertung“ umbenannt und um Brüche, Outcome-Abdeckung, `nicht vergleichbar` sowie sichtbaren Hinweis „Kein ML-Training aktiv“ ergänzt.
- Neue Vertragsdokumentation erstellt und `AGENTS.md`, Systemzustand sowie Architekturregeln erweitert.
- Kontrollierten Live-Neustart durchgeführt. Zwei zunächst unvollständige Startkonfigurationen wurden anhand der öffentlichen API erkannt und jeweils geordnet beendet: zuerst fehlte `PANDORICKKI_LIVE_CRYPTO=1`, danach war der falsche NeuroBrain-Schalter gesetzt. Der finale Start verwendet die tatsächlichen Namen und sichere Werte.
- Browseroberfläche nach dem finalen Code neu geladen und die konkreten Outcome-/Trading-/Graphwerte sowie Browserkonsole geprüft.
- Implementierung als Commit `e09c18761270de1d877b318c13781f103aa0f72e` auf `agent/unify-learning-metrics` gepusht. Draft-PR #16 gegen `agent/queue-neurobrain-receiver` erstellt und als offen, Draft sowie ungemergt verifiziert.

### Veränderte Dateien

- `AGENTS.md`
- `docs/ARCHITECTURE.md`
- `docs/CURRENT_SYSTEM_STATE.md`
- `docs/KNOWN_PROBLEMS.md`
- `docs/NEXT_STEPS.md`
- `docs/SESSION_HANDOVER.md`
- `learning_graph/graph_builder.py`
- `learning_graph/graph_models.py`
- `learning_graph/graph_sanitizer.py`
- `learning_graph/graph_service.py`
- `tests/test_learning_graph_phase3.py`
- `tests/test_learning_report_service.py`
- `tests/test_statistics_and_storage.py`
- `tests/test_web_control_center.py`
- `web/learning_report_service.py`
- `web/statistics_service.py`
- `web/static/control_center.html`
- `web/static/control_center.js`

### Neue Dateien

- `learning_metrics_contract.py`
- `tests/test_learning_metrics_contract.py`
- `docs/LEARNING_METRICS_CONTRACT.md`
- Ignorierte Laufzeitlogs `runtime_logs/web_learning_metrics_2026-08-02_12-28-59_stdout.log` und `runtime_logs/web_learning_metrics_2026-08-02_12-28-59_stderr.log`; beide waren bei Abschluss 0 Byte.

### Ausgeführte Befehle

- Vollständiges Lesen von `AGENTS.md` und den fünf vorgeschriebenen Übergabedokumenten; danach Code-, Routen-, Ledger-, Statistik-, Graph-, UI- und Testinventur mit `rg`, `Get-Content` und `git`.
- Gezielte Unittests vor und nach Implementierung, `py_compile`, `git diff --check` und vollständige Test-Discovery.
- Read-only Python-Auswertung der vorhandenen Decision-, Outcome-, Statistik- und Graphdaten.
- HTTP-Prüfungen auf `/api/status`, `/api/config/public`, `/api/statistics`, `/api/learning-report` und `/api/v1/learning-graph/stats`.
- Drei kontrollierte POSTs auf `/api/control/stop`; alle Prozesse beendeten sich regulär nach dem laufenden Zyklusintervall, ohne harten Prozessabbruch.
- `\.venv\Scripts\python.exe scripts\runtime_preflight.py`.
- Verdeckte `Start-Process`-Starts über die projektlokale `.venv`; final mit Live-Crypto, NeuroBrain-Queue, Telegram aus und Dry-Run.
- Lokales Control Center im In-App-Browser neu geladen, gezielte DOM-Werte und Browserkonsole gelesen.

### Ausgeführte Tests

- 7 gezielte Learning-Report-/Vertragstests nach der Cache-Schemaergänzung.
- Syntaxprüfung der sieben geänderten Python-Produktionsmodule.
- `git diff --check`.
- Vollständige `unittest`-Suite.
- Runtime-Preflight.
- Kontrollierter Stop/Start und zwei vollständige Livezyklen.
- Live-API-, Crypto-, Stock-, NeuroBrain-, Telegram-, Report-, Statistik- und Graphprüfung.
- Sichtprüfung der relevanten UI-Felder und Browserkonsole.

### Tatsächliche Testergebnisse

- Gezielte Tests: 7/7 bestanden.
- Vollständige Suite: 239/239 Tests in 51,814 Sekunden bestanden.
- `py_compile`, `git diff --check` und Runtime-Preflight: bestanden; Python 3.12.13 aus der projektlokalen `.venv`.
- Finaler Livebetrieb: Plattform und alle zehn Services `OK`, Session-`error_count=0`; Crypto und Stock jeweils zwei vollständige Zyklen, Crypto drei Ergebnisse pro Zyklus und aktuelle Preise für BTCUSDT, ETHUSDT und XRPUSDT.
- NeuroBrain: Worker aktiv, Queue-Tiefe 0, Drops 0, fehlgeschlagene Events 0.
- Telegram: `enabled=false`, `dry_run=true`, `messages_sent=0`.
- Learning Report: Cache `fresh`, Schema Version 1, live zuletzt Hit-Rate 16,67 % (`14/84`) und Outcome-Abdeckung 19,37 % (`165/852`), kein ML-Training.
- Historische Trading-Aggregate: Hit-Rate 48,21 % (`2135/4429`); Outcome-Abdeckung korrekt `null`, weil der persistente Decision-/Outcome-Scope nicht konsistent ist.
- Learning Graph: 42 Muster-Buckets, 728 heutige Projektionsdatensätze im geladenen Fenster, 36.231 kumulative Learning-Update-Events, `ml_training_active=false`, `model_updates=0`.
- Browser: Outcome-Hit-Rate und -Abdeckung mit Bruch, ML-Training „Nein“, Trading-Abdeckung „nicht vergleichbar“, Muster-Buckets/Projektionen korrekt benannt; 0 Warnungen und 0 Fehler in der Browserkonsole.
- Finale Runtime-stdout/-stderr: jeweils 0 Byte.

### Bekannte Fehler

- Neu dokumentiert als `KP-017`: Historische persistente Decision- und Outcome-Gesamtzähler stammen nicht garantiert aus demselben Rekonstruktionsscope. Version 1 verhindert eine falsche Abdeckungsquote; der ID-basierte Learning Report bleibt die verlässliche Sicht.
- `KP-002`: WebSocket-Reconnect und idempotentes Polling fehlen weiterhin.
- `KP-008`: Stale-Heartbeats werden weiterhin nicht klassifiziert.
- `KP-013`: Ein akzeptierter Stop benötigt weiterhin bis zum Ende des maximal 60 Sekunden langen Zyklus-Sleeps.
- `KP-003`: Andere synchrone EventBus-Consumer können weiterhin blockieren; NeuroBrain selbst ist bereits entkoppelt.

### Getroffene Architekturentscheidungen

- Ein zentraler, additiver Version-1-Vertrag ist die einzige Definition der öffentlichen Learning-/Outcome-Raten.
- Hit-Rate schließt Breakeven und Unknown aus; deren Zähler bleiben sichtbar.
- Outcome-Abdeckung wird nur bei nachgewiesen gleichem Scope berechnet. `null` ist fachlich korrekter als eine scheinpräzise Quote.
- Projektionsereignisse und Graph-Buckets belegen kein ML-Training. Alte Feldnamen bleiben nur als rückwärtskompatible Aliase bestehen.
- Bestehende History und persistente Statistiken werden nicht still migriert, zurückgesetzt oder umgeschrieben.

### Nicht abgeschlossene Punkte

- UI-Härtung aus Schritt 10 bleibt vollständig offen.
- Für KP-017 existiert noch kein gemeinsamer Rekonstruktionscursor oder Migrationsvertrag.

### Exakter nächster sinnvoller Arbeitsschritt

In einem eigenen kleinen Branch zuerst WebSocket-Reconnect und genau einen idempotenten Polling-Timer testgetrieben umsetzen; dabei Stop-/Restart-Wartezeit, STALE-Heartbeats und Graph-Performance weiterhin getrennt behandeln.

## Aktuelle Aufgabe: NeuroBrain über begrenzte FIFO-Queue entkoppeln

### Datum und Uhrzeit

2. August 2026, 11:53 Uhr, Europe/Berlin (`+02:00`)

### Ziel der Aufgabe

Nur den langsamen NeuroBrain-Dateiconsumer vom synchronen EventBus-Publisher entkoppeln. Kapazität, Überlauf, Reihenfolge, Batch-Schreiben, Fehlerzustände und Shutdown eindeutig definieren, testgetrieben implementieren und live verifizieren. Den allgemeinen EventBus nicht umbauen und bestehende Inbox-/Historydaten nicht verändern.

### Durchgeführte Arbeiten

- Pflichtdokumentation, Payloadvertrag, NeuroBrain-Adapter, EventBus, RotatingJsonlLedger, Orchestrator-Lebenszyklus, Konfiguration und tatsächliche Subscriber geprüft.
- Vertrag festgelegt: FIFO, Standardkapazität 2048, Drop-newest bei Überlauf, Standardbatch 64, maximal 250 Millisekunden Flush-Wartezeit, ein nicht-daemonisierter Writer und vollständiger Drain vor Rückkehr von `stop()`.
- Regressionstests vor der Implementierung ergänzt. Sie scheiterten erwartungsgemäß wegen fehlender Queueparameter, Batch-API und Konfiguration; der idempotente Stoptest reproduzierte zusätzlich ein doppeltes Stop-Ereignis.
- NeuroBrain-Wildcard-Handler auf kompakte Projektion plus thread-sicheres `put_nowait` begrenzt. Datei-, `fsync`-, Status- und Receipt-Arbeiten in einen einzelnen Worker verschoben.
- Sichtbare Metriken für Queue-Tiefe/-Kapazität, Drops, fehlgeschlagene Events, Status-/Benachrichtigungsfehler, Batchanzahl/-größe und Workerzustand in Health, Heartbeat, Service-Details und Statusdatei ergänzt.
- Überlauf lehnt nur den neuesten Eintrag ab; bereits akzeptierte FIFO-Einträge werden nicht überschrieben. Abgelehnte IDs werden nicht als Duplikat reserviert.
- Worker gegen Ledger-, Status- und Receipt-Fehler isoliert. Statusfehler beenden die Queue-Abarbeitung nicht.
- `RotatingJsonlLedger.append_many()` ergänzt: geordnete Batchzeilen, Rotation zwischen Dateichunks und ein Flush/`fsync` je aktivem Chunk. `append()` verwendet denselben Pfad.
- Queueparameter über `PlatformConfig`, Umgebungsvariablen und Orchestrator verdrahtet.
- Gezielte Tests, vollständige Suite, Syntaxprüfung, Diffprüfung und Runtime-Preflight ausgeführt.
- Laufenden Dienst geordnet gestoppt, Queue-Version mit NeuroBrain und öffentlichen Live-Marktdaten sowie Telegram aus/Dry-Run gestartet und mehrere Zyklen geprüft.
- Ausschließlich 231 neu angehängte Inboxzeilen auf Eindeutigkeit, FIFO-Zeitfolge, Schema-/Pflichtfelder und Bulk-Ausschluss geprüft.
- Neuen Prozess erneut geordnet gestoppt: Status bestätigte `running=false`, `worker_running=false`, `queue_depth=0`; danach PandorickKi wieder mit identischer sicherer Konfiguration gestartet.
- Keine bestehende Inbox-, History-, Lern-, Token- oder Konfigurationsdatei gelöscht, geleert, migriert oder manuell umgeschrieben.
- Implementierung und Übergabestand als Commit `0fe5bd64d366695d6c9786c1a561dc513187b37b` auf `agent/queue-neurobrain-receiver` veröffentlicht. Gestapelten Draft-PR #15 gegen `agent/fix-neurobrain-observer-schema` erstellt, als offen und Draft verifiziert und nicht gemergt.

### Veränderte Dateien

- `adapters/neurobrain_receiver_adapter.py`
- `config.py`
- `jsonl_ledger.py`
- `orchestrator.py`
- `tests/test_config.py`
- `tests/test_neurobrain_receiver_adapter.py`
- `docs/CURRENT_SYSTEM_STATE.md`
- `docs/SESSION_HANDOVER.md`
- `docs/ARCHITECTURE.md`
- `docs/KNOWN_PROBLEMS.md`
- `docs/NEXT_STEPS.md`

### Neue Dateien

- `tests/test_jsonl_ledger.py`

### Ausgeführte Befehle

- Vollständiges Lesen von `AGENTS.md`, den fünf Übergabedateien und `docs/EVENT_PAYLOAD_CONTRACT.md`.
- Code-/Lifecycle-/Subscriberinventur mit `rg`, `Get-Content`, Git-Status und Git-Diff.
- Rote und grüne Läufe der NeuroBrain-/Ledger-/Konfigurationstests.
- `.\.venv\Scripts\python.exe -m unittest tests.test_neurobrain_receiver_adapter tests.test_jsonl_ledger tests.test_config tests.test_parallel_orchestrator -v`.
- `.\.venv\Scripts\python.exe -m py_compile ...`, `git diff --check` und `.\.venv\Scripts\python.exe -m unittest discover -s tests -v`.
- `.\.venv\Scripts\python.exe scripts\runtime_preflight.py`.
- Read-only Baselines und Auswertungen von `/api/status`, `data/neurobrain/inbox.jsonl`, `data/neurobrain/status.json` und `data/service_error_summary.json`.
- Zweimal kontrollierter Stop über `POST /api/control/stop`; versteckte Starts mit Queueparametern, Live-Crypto/Stock und Telegram deaktiviert/Dry-Run.
- Explizites Git-Staging, Commit `0fe5bd64d366695d6c9786c1a561dc513187b37b`, `git push -u origin agent/queue-neurobrain-receiver`, `gh pr create --draft` und abschließende PR-Prüfung mit `gh pr list`.

### Ausgeführte Tests

- Publisher-Latenz bei künstlich langsamem Ledger.
- FIFO-Reihenfolge und Batchobergrenze.
- Deterministischer Queue-Überlauf mit Drop-newest.
- Vollständiger Flush aller akzeptierten Einträge vor `stop()`-Rückkehr und keine Annahme danach.
- Idempotenter wiederholter Stop.
- Statusschreibfehler-Isolation ohne Workerabbruch.
- Batch-Ledger mit fünf geordneten Zeilen und genau einem `fsync`.
- Konfigurationsdefaults, Umgebungswerte und Orchestratorverdrahtung.
- 20 gezielte Tests, vollständige Suite, `py_compile`, Preflight und Diffprüfung.
- Livezyklen, 231 neue Inboxzeilen und echter Queue-Worker-Shutdown.

### Tatsächliche Testergebnisse

- Vor der Implementierung: vier erwartete Fehler wegen fehlender Queueparameter, `append_many()` und Konfigurationsfelder; separater Stoptest rot mit zwei statt einem Stop-Ereignis.
- Nach der Implementierung: 20/20 gezielte Tests bestanden in 1,493 Sekunden.
- Vollständige Suite: 235/235 Tests bestanden in 45,092 Sekunden.
- `py_compile`, `git diff --check` und Runtime-Preflight: bestanden.
- Live vor Shutdown: alle zehn Services und Fehlerjournal `OK`; Crypto 2 Zyklen/6 Ergebnisse, Stock 2 Zyklen/10 Ergebnisse; Telegram `enabled=false`, `dry_run=true`, `messages_sent=0`.
- NeuroBrain: 231 neue eindeutige Zeilen, 48 Batches, Queue-Tiefe 0, Drops 0, fehlgeschlagene Events 0, Statusfehler 0, Benachrichtigungsfehler 0, Worker aktiv.
- 231/231 neue Zeilen ohne FIFO-, Schema-, Pflichtfeld- oder Bulk-Verstoß.
- Fehlerjournal unverändert bei 180 Ereignissen und `failed_writes=0`.
- Live-Shutdown: `running=false`, `worker_running=false`, `queue_depth=0`, 231 Events vollständig persistiert. Anschließender Neustart erfolgreich; NeuroBrain wieder `OK`, Queue leer und Worker aktiv.

### Bekannte Fehler

- Der allgemeine EventBus bleibt synchron. NeuroBrain-I/O ist entkoppelt; andere langsame Subscriber können Publisher weiterhin blockieren (`KP-003`).
- Die bestehende In-Memory-Menge `_seen_event_ids` ist weiterhin nicht dauerhaft beziehungsweise größenbegrenzt; in einer einzelnen sehr langen Laufzeit kann sie wachsen.
- Die übrigen offenen Punkte aus `docs/KNOWN_PROBLEMS.md` bleiben bestehen.

### Getroffene Architekturentscheidungen

- Gezielt nur NeuroBrain entkoppelt; keine globale EventBus- oder Produceränderung.
- Drop-newest schützt Reihenfolge und Bestand aller bereits akzeptierten Ereignisse. Jeder Drop bleibt als Healthfehler sichtbar.
- Ein einzelner Writer garantiert FIFO ohne zusätzliche Sequenzkoordination. Batch-Schreiben reduziert `fsync`-Aufwand, ohne das append-only Ledgerformat zu ändern.
- Ein akzeptiertes Ereignis wird beim Stop nicht verworfen; der nicht-daemonisierte Thread wird ohne willkürlichen Timeout vollständig gejoint.
- Status- und Receipt-Probleme dürfen den Persistenzworker nicht beenden. Ledgerfehler bleiben als fehlgeschlagene Ereignisse sichtbar.

### Nicht abgeschlossene Punkte

- `_seen_event_ids`-Retention ist nicht Teil dieser Entkopplung und muss nur bei belegtem Langzeit-Speicherproblem separat geplant werden.

### Veröffentlichung

- Branch: `agent/queue-neurobrain-receiver`
- Implementierungscommit: `0fe5bd64d366695d6c9786c1a561dc513187b37b`
- Draft-PR: [#15 – Queue NeuroBrain persistence writes](https://github.com/cRioshy/Pando/pull/15)
- Basis: `agent/fix-neurobrain-observer-schema`
- Zustand: offen, Draft, nicht gemergt

### Exakter nächster sinnvoller Arbeitsschritt

Learning-Metriken vereinheitlichen: zuerst alle Produzenten und UI-Nenner für Decisions, Outcomes, Learnings, Patterns, Hit-Rate und Trading-Ergebnis inventarisieren. Danach einen gemeinsamen Begriff-/Nennervertrag festlegen, Outcome-Abdeckung sichtbar machen und klar kennzeichnen, dass aktuell kein ML-Modell trainiert wird. Noch keine Telegram- oder Decision-Gate-Änderung beginnen.

---

## Aktuelle Aufgabe: NeuroBrain-Markt- und Observer-Schemata eindeutig trennen

### Datum und Uhrzeit

2. August 2026, 11:25 Uhr, Europe/Berlin (`+02:00`)

### Ziel der Aufgabe

Die als `KP-016` dokumentierte Vertragslücke reproduzierbar schließen: Nicht marktbezogene Learning-/Aggregatereignisse dürfen nicht länger den Marktvertrag vortäuschen; einzelwertige Preisupdates müssen den Marktvertrag vollständig erfüllen. Bestehende Inbox-/Historyzeilen unverändert lassen, vollständig testen und kontrolliert live verifizieren.

### Durchgeführte Arbeiten

- Pflichtdokumentation, ausführbaren Payloadvertrag, tatsächlichen NeuroBrain-Consumer und die Produzenten aller betroffenen Topics geprüft.
- Tatsächliche Semantik abgegrenzt: `AI_LEARNING_UPDATED` ist ein Learning-Status; `STOCK_MARKET_DATA_UPDATED` ist ein Aggregat; Crypto-/Commodity-Market-Updates sind einzelne Symbolereignisse.
- Drei Adapterregressionen vor dem Fix ergänzt und die zwei falschen Schemanamen sowie den fehlenden Crypto-Markt-Typ reproduziert.
- `pandorickki.compact-observer-event` Version 1 samt Projektion und Validator ergänzt. Pflicht ist `event_type`; kleine Status-, Zähler-, Symbolsammlungs- und Learning-Felder bleiben erhalten; Bulk-Felder bleiben rekursiv verboten.
- NeuroBrain ordnet Learning und das Aktienaggregat explizit dem Observer-Vertrag zu. Einzelwertige Crypto-/Commodity-Updates bleiben Marktprojektionen und erhalten ihren Topic-eindeutigen Markt-Typ. Übrige Analysis-/Brain-/Decision-/Signal-/Trade-Topics bleiben unverändert Marktprojektionen.
- Gezielte und vollständige Tests, Syntaxprüfung und Diffprüfung ausgeführt.
- Vor dem Neustart die NeuroBrain-Dateigröße und den Fehlerjournalstand read-only erfasst. Den alten Prozess über `POST /api/control/stop` geordnet beendet und genau einen neuen Prozess mit NeuroBrain aktiv, Live-Crypto/Stock sowie Telegram deaktiviert/Dry-Run gestartet.
- Zwei vollständige Produktionszyklen abgewartet und ausschließlich 152 nach dem Neustart angehängte NeuroBrain-Zeilen geprüft.
- Vertrags-, System-, Architektur-, Problem- und Planungstexte aktualisiert. Bestehende Runtime-, History-, Lern-, Token- und Konfigurationsdateien wurden nicht gelöscht, geleert, migriert oder manuell umgeschrieben.
- Scope und Secret-Muster vor dem Staging geprüft, die zehn vorgesehenen Dateien gezielt gestaged und Commit `e94c98828b5ae0b91ab667775c4334729fe09f74` erstellt.
- Branch `agent/fix-neurobrain-observer-schema` nach `origin` gepusht und Draft-PR #14 gegen den direkten Vorgänger `agent/compact-neurobrain-payloads` eröffnet. Der PR ist offen, weiterhin Draft und nicht gemergt.

### Veränderte Dateien

- `adapters/neurobrain_receiver_adapter.py`
- `event_payload_contract.py`
- `tests/test_event_payload_contract.py`
- `tests/test_neurobrain_receiver_adapter.py`
- `docs/EVENT_PAYLOAD_CONTRACT.md`
- `docs/CURRENT_SYSTEM_STATE.md`
- `docs/ARCHITECTURE.md`
- `docs/KNOWN_PROBLEMS.md`
- `docs/NEXT_STEPS.md`
- `docs/SESSION_HANDOVER.md`

### Neue Dateien

- Keine.

### Ausgeführte Befehle

- Vollständiges Lesen von `AGENTS.md`, den fünf Übergabedateien und `docs/EVENT_PAYLOAD_CONTRACT.md`.
- Code-/Producer-/Topicinventur mit `rg`, `Get-Content`, Git-Status und Git-Diff.
- Roter und grüner Lauf von `.\.venv\Scripts\python.exe -m unittest tests.test_neurobrain_receiver_adapter -v`.
- `.\.venv\Scripts\python.exe -m unittest tests.test_event_payload_contract tests.test_neurobrain_receiver_adapter -v`.
- `.\.venv\Scripts\python.exe -m py_compile ...`, `git diff --check` und `.\.venv\Scripts\python.exe -m unittest discover -s tests -v`.
- Read-only Baseline-/Liveauswertung von `data/neurobrain/inbox.jsonl`, `data/service_error_summary.json` und `/api/status`.
- Kontrollierter Stop über `POST /api/control/stop`; versteckter Neustart mit sicheren Umgebungswerten und öffentlichen Live-Marktdaten.
- Bytegenaue Auswertung des neu angehängten Inboxbereichs mit Topic-/Schema-, Pflichtfeld- und rekursiver Bulk-Prüfung.
- `gh auth status`, explizites `git add`, Commit, `git push -u origin agent/fix-neurobrain-observer-schema` sowie `gh pr create --draft` und abschließendes `gh pr view`.

### Ausgeführte Tests

- Drei neue NeuroBrain-Adapterregressionen für Learning, Aktienaggregat und einzelwertiges Crypto-Update.
- Zwei Observer-Vertragstests für Projektion, rekursiven Bulk-Ausschluss und Pflichtfeldvalidierung.
- 15 gezielte Vertrags-/NeuroBrain-Tests.
- `py_compile` der vier geänderten Python-/Testdateien.
- Vollständige Unittest-Suite.
- Zwei vollständige Live-Produktionszyklen und Validierung aller nach Neustart angehängten NeuroBrain-Zeilen.

### Tatsächliche Testergebnisse

- Vor dem Fix: NeuroBrain-Suite erwartungsgemäß rot mit zwei falschen Markt-Schemanamen und fehlendem `market_type` beim Crypto-Update.
- Nach dem Fix: 15/15 gezielte Tests bestanden in 0,419 Sekunden.
- Vollständige Suite: 231/231 Tests bestanden in 43,563 Sekunden.
- `py_compile` und `git diff --check`: bestanden.
- Live: Crypto 2 Zyklen/6 Ergebnisse, Stock 2 Zyklen/10 Ergebnisse; alle zehn Services und das Fehlerjournal `OK`.
- 152 ausschließlich neue Inboxzeilen geprüft: 18 Observer-Zeilen und 134 Markt-Zeilen, null Schema-, Versions-, Pflichtfeld- oder Bulk-Verstöße.
- Observer-Beispiele: 16 Learning-Zeilen mit erhaltenen Status-/Zählerfeldern und zwei Aktienaggregate mit `count`/`symbols`. Crypto-Market-Updates trugen `market_type=crypto` und ein Symbol.
- Fehlerjournal unverändert bei 180 Ereignissen, `failed_writes=0`; Telegram `enabled=false`, `dry_run=true`, `messages_sent=0`.

### Bekannte Fehler

- `KP-016` ist behoben. Vorhandene alte Inboxzeilen behalten bewusst ihre historische Schemaform.
- NeuroBrain bleibt ein synchroner EventBus-Consumer; Queue, Batch, Überlaufregel und sicherer Queue-Shutdown fehlen weiterhin.
- Die übrigen offenen Punkte aus `docs/KNOWN_PROBLEMS.md` bleiben bestehen.

### Getroffene Architekturentscheidungen

- Schemazuständigkeit wird explizit aus der fachlichen Topicsemantik abgeleitet und nicht heuristisch aus zufällig vorhandenen Feldern.
- Learning-/Aggregatereignisse erhalten einen eigenen kleinen Observer-Vertrag statt künstlicher `market_type`-/`symbol`-Werte.
- Nur bei tatsächlich einzelwertigen Crypto-/Commodity-Preisupdates wird der Topic-eindeutige Markt-Typ ergänzt.
- Beide Verträge teilen den rekursiven Bulk-Ausschluss. Die NeuroBrain-Kopfsicht und append-only History bleiben kompatibel und unverändert.

### Nicht abgeschlossene Punkte

- Begrenzte NeuroBrain-Queue, Überlaufregel, Batch-Schreiben und Shutdown sind noch nicht implementiert.

### Veröffentlichung

- Branch: `agent/fix-neurobrain-observer-schema`
- Implementierungscommit: `e94c98828b5ae0b91ab667775c4334729fe09f74`
- Remote: `origin` → `https://github.com/cRioshy/Pando.git`
- Draft-PR: #14, `https://github.com/cRioshy/Pando/pull/14`
- Basis: `agent/compact-neurobrain-payloads`
- Status: `OPEN`, `isDraft=true`, nicht gemergt

### Exakter nächster sinnvoller Arbeitsschritt

Auf einem weiteren kleinen gestapelten Branch zuerst das gewünschte Queue-Verhalten vertraglich festlegen und mit Last-/Shutdown-Regressionen absichern: maximale Kapazität, Verhalten bei voller Queue, Reihenfolge, Batchgröße, Flush beim Stop und sichtbar gezählte Verluste. Danach ausschließlich den langsamen NeuroBrain-Consumer vom synchronen EventBus entkoppeln; den übrigen EventBus nicht umbauen.

---

## Aktuelle Aufgabe: Windows-Schreibkonflikte in NeuroBrain und Crypto Trade Tracker beheben

### Datum und Uhrzeit

2. August 2026, 10:41 Uhr, Europe/Berlin (`+02:00`)

### Ziel der Aufgabe

Die im Dauerbetrieb neu aufgetretenen `WinError 5` beim atomaren Ersetzen von `data/neurobrain/status.json` und `data/crypto_active_trades.json` reproduzierbar absichern, klein reparieren, vollständig testen und kontrolliert live verifizieren. Bestehende Runtime-/History-Dateien nicht löschen oder umschreiben; Telegram und reale Orderausführung nicht aktivieren.

### Durchgeführte Arbeiten

- Vorgeschriebene Übergabedokumentation und tatsächliche Schreibpfade erneut geprüft.
- Fehlerjournal read-only ausgewertet: NeuroBrain-Status-Fingerprint drei Vorkommen, Crypto-Trade-Tracker-Fingerprint drei Vorkommen; beide `os.replace()` von festen `*.tmp`-Pfaden betroffen.
- Weitere atomare JSON-Schreiber inventarisiert und die Änderung bewusst auf die zwei aktuell betroffenen Pfade begrenzt.
- Zwei Regressionstests zuerst angelegt und vor der Implementierung mit fehlendem `atomic_json` reproduzierbar rot ausgeführt.
- `atomic_json.py` ergänzt: JSON-Validierung, eindeutige Same-Directory-Temp-Datei, `fsync`, atomarer Replace, pro Zielpfad geteilte In-Process-Sperre, begrenzter Retry für transiente Windows-Permission-/Sharing-Fehler und Aufräumen ausschließlich der eigenen Temp-Datei.
- NeuroBrain-Status und aktive Crypto-Trades auf den Helfer umgestellt.
- Beide Adapter halten ihre eigene Zustandssperre jetzt bis zum erfolgreichen Dateireplace; dadurch können ältere Snapshots keine neueren Zustände nachträglich überschreiben.
- Gezielte Tests, `py_compile`, vollständige Suite, Diffprüfung und Runtime-Preflight ausgeführt.
- Fehlerjournal-Baseline erfasst, den alten Prozess über die lokale Stop-API geordnet beendet und PandorickKi mit normalem Netzwerkzugriff, Telegram deaktiviert/Dry-Run kontrolliert neu gestartet.
- Zwei vollständige Produktionszyklen sowie beide Zieldateien, Fehlerfingerprints und mögliche Temp-Reste live geprüft.
- Commit `ed2a83e` erstellt und auf `origin/agent/compact-neurobrain-payloads` veröffentlicht; der bestehende Draft-PR #13 wurde aktualisiert und bleibt ungemergt.
- Keine Runtime-, History-, Lern-, Token- oder Konfigurationsdatei gelöscht, geleert, migriert oder manuell verändert.

### Veränderte Dateien

- `adapters/crypto_trade_tracker.py`
- `adapters/neurobrain_receiver_adapter.py`
- `docs/CURRENT_SYSTEM_STATE.md`
- `docs/SESSION_HANDOVER.md`
- `docs/ARCHITECTURE.md`
- `docs/KNOWN_PROBLEMS.md`
- `docs/NEXT_STEPS.md`

### Neue Dateien

- `atomic_json.py`
- `tests/test_atomic_json.py`

### Ausgeführte Befehle

- Vollständiges Lesen von `AGENTS.md` und den fünf Übergabedateien.
- Code- und Schreibpfadinventur mit `rg` und `Get-Content`; Git-Status-/Diffprüfung.
- Read-only Auswertung von `data/service_error_summary.json` und der lokalen `/api/status`-Sicht.
- Roter und grüner Lauf von `.\.venv\Scripts\python.exe -m unittest tests.test_atomic_json -v` beziehungsweise der gezielten Modulsuite.
- `.\.venv\Scripts\python.exe -m py_compile atomic_json.py adapters\neurobrain_receiver_adapter.py adapters\crypto_trade_tracker.py tests\test_atomic_json.py`.
- `.\.venv\Scripts\python.exe -m unittest discover -s tests`.
- `.\.venv\Scripts\python.exe scripts\runtime_preflight.py`.
- Kontrollierter Stop über `POST /api/control/stop`, verdeckter Neustart mit Live-Crypto/Stock, NeuroBrain aktiv und Telegram aus/Dry-Run.
- Zwei Livezyklen über `/api/status`, anschließender Vergleich der Journalfingerprints und Suche nach eindeutigen Temp-Dateien.

### Ausgeführte Tests

- Zwei neue Atomic-JSON-Regressionstests vor und nach der Implementierung.
- 13 gezielte Atomic-/NeuroBrain-/Crypto-Trade-Tracker-Tests.
- `py_compile` der vier geänderten beziehungsweise neuen Python-Dateien.
- Vollständige Unittest-Suite.
- Runtime-Preflight.
- Zwei vollständige Produktionszyklen mit Live-Crypto und Live-Stock.
- Livevergleich von Servicezuständen, Fehlerjournal, Zieldatei-Zeitstempeln, Temp-Resten, Crypto-Preisen und Telegram-Status.

### Tatsächliche Testergebnisse

- Vor dem Fix: 2/2 neue Tests erwartungsgemäß rot mit `ModuleNotFoundError: atomic_json`.
- Nach dem Fix: Retrytest bestand nach zwei simulierten transienten `PermissionError`; Paralleltest bestand mit 24 Schreibvorgängen aus acht Threads und valider Enddatei ohne Temp-Reste.
- Gezielte Suite: 13/13 bestanden in 0,524 Sekunden.
- Vollständige Suite: 226/226 bestanden in 41,406 Sekunden.
- `py_compile`, Runtime-Preflight und `git diff --check`: bestanden.
- Live: zwei vollständige Zyklen; Plattform, Web und alle zehn Services `OK`. Crypto 6, Stock 10 publizierte Ergebnisse.
- Abschluss-Preise: BTCUSDT `63250.0`, ETHUSDT `1868.13`, XRPUSDT `1.0792`.
- Fehlerjournal: insgesamt unverändert 180. NeuroBrain-Fingerprint unverändert 3, letzter Zeitpunkt 1. August 22:13:29 UTC; Crypto-Trade-Tracker-Fingerprint unverändert 3, letzter Zeitpunkt 2. August 07:54:17 UTC.
- Keine eindeutigen oder alten `*.tmp`-Reste in den beiden betroffenen Datenverzeichnissen.
- Telegram: `enabled=false`, `dry_run=true`, `messages_sent=0`.
- Bekannte `datetime.utcnow()`-DeprecationWarnings stammen unverändert aus dem externen Legacy-Crypto-Projekt.

### Bekannte Fehler

- `KP-016` bleibt offen: Nicht marktbezogene NeuroBrain-Topics tragen noch das Markt-Schema, obwohl Pflichtfelder fehlen können.
- NeuroBrain bleibt synchroner EventBus-Consumer; Queue, Batch, Überlaufregel und sicherer Shutdown sind noch nicht implementiert.
- Andere bestehende atomare JSON-Schreiber verwenden weiterhin ihre bisherigen Temp-Strategien; ohne reproduzierbaren Fehler wurden sie in dieser kleinen Reparatur nicht pauschal verändert.
- Die übrigen offenen Punkte aus `docs/KNOWN_PROBLEMS.md` bleiben bestehen.

### Getroffene Architekturentscheidungen

- Ein kleiner gemeinsamer Atomic-JSON-Helfer kapselt künftig ausschließlich die bereits benötigte Konfliktbehandlung; keine globale Persistenzmigration ohne eigenen Testbefund.
- Einzigartige Temp-Dateien verhindern Schreiberkollisionen. Kurze begrenzte Retries behandeln nur transiente Windows-Sperren; endgültige Fehler bleiben sichtbar und werden nicht verschluckt.
- Adapterzustand und Dateisnapshot werden unter derselben Adapter-Sperre geordnet.
- Keine Änderung an Inbox-/Trade-History-Formaten, realer Orderausführung oder Telegram-Sicherheitsgrenze.

### Nicht abgeschlossene Punkte

- `KP-016` ist noch nicht implementiert behoben.
- NeuroBrain-Queue-/Batch-Entkopplung bleibt nach `KP-016` der nächste Architekturpunkt.
- Draft-PR #13 enthält den Fix, bleibt aber bewusst Draft und ungemergt.

### Exakter nächster sinnvoller Arbeitsschritt

`KP-016` in einem eigenen kleinen gestapelten Branch/PR testgetrieben beheben: Markt- und Lifecycle-/Learning-Topics eindeutig trennen, bestehende NeuroBrain-Inboxzeilen nicht umschreiben und anschließend gezielt sowie vollständig testen. Erst danach die Queue-/Batch-Entkopplung beginnen.

---

## Aktuelle Aufgabe: Gestapelten Payloadstand kontrolliert live verifizieren

### Datum und Uhrzeit

1. August 2026, 23:19 Uhr, Europe/Berlin (`+02:00`)

### Ziel der Aufgabe

Den vollständigen gestapelten Brain-/Decision-/Signal-/NeuroBrain-Payloadstand kontrolliert neu starten und mindestens zwei vollständige Produktionszyklen read-only auf Schema Version 1, ID-Kette, Bulk-Ausschluss, Servicezustand, Fehlerjournal und Telegram-Sicherheitszustand prüfen. Noch keine Queue-/Batch-Entkopplung implementieren.

### Durchgeführte Arbeiten

- Vorgeschriebene Übergabedokumentation, Payload-Vertrag, Startkonfiguration, Runtime-Preflight und tatsächliche Ledgerpfade geprüft.
- Vor dem Stop stabile Byte-Endstände der vier aktiven Persistenzgrenzen erfasst.
- Den alten Prozess über `POST /api/control/stop` geordnet beendet; keinen zweiten Prozess parallel gestartet und keinen Prozess hart abgebrochen.
- Runtime-Preflight mit der projektlokalen `.venv` ausgeführt und bestanden.
- Einen ersten Prüflauf innerhalb der eingeschränkten Ausführungsumgebung gestartet. Dessen fehlende Socket-Berechtigung verursachte reproduzierbar `WinError 10013` für Binance und Bitget; der Lauf wurde als nicht aussagekräftig für Crypto erkannt und geordnet beendet.
- PandorickKi anschließend mit freigegebenem Netzwerkzugriff, Live-Crypto, Live-Stock, NeuroBrain aktiv sowie Telegram deaktiviert/Dry-Run neu gestartet.
- Drei vollständige saubere Produktionszyklen beobachtet; ausschließlich neu angehängte Ledgerbereiche ab den gesicherten Byte-Offsets analysiert.
- Brain-, Decision-, Signal- und marktbezogene NeuroBrain-Payloads mit `contract_errors()` sowie rekursiv auf verbotene Bulk-Felder geprüft.
- Brain→Decision→Signal-ID-Kette und die Spiegelung der Decision-/Signal-Event-IDs in NeuroBrain vollständig abgeglichen.
- Eine bisher ungetestete Vertragslücke für nicht marktbezogene NeuroBrain-Topics als `KP-016` dokumentiert.
- Keine Quell-, Runtime-, History-, Lern-, Token- oder Konfigurationsdatei gelöscht, geleert oder umgeschrieben; die Anwendung hat während der Liveprüfung ausschließlich ihre normalen Laufzeitdaten angehängt.

### Veränderte Dateien

- `docs/CURRENT_SYSTEM_STATE.md`
- `docs/SESSION_HANDOVER.md`
- `docs/EVENT_PAYLOAD_CONTRACT.md`
- `docs/KNOWN_PROBLEMS.md`
- `docs/NEXT_STEPS.md`

### Neue Dateien

- Keine.

### Ausgeführte Befehle

- Vollständiges Lesen von `AGENTS.md`, den fünf Übergabedateien und `docs/EVENT_PAYLOAD_CONTRACT.md`.
- Code-/Konfigurationsinventur mit `rg` und `Get-Content`; Git-Status- und Branchprüfung.
- Read-only HTTP-Abfragen von `/api/health`, `/api/status`, `/api/crypto` und `/api/statistics/storage`.
- Read-only Erfassung von Ledger-Dateigrößen, Byte-Offsets, Endständen und Fehlerjournal-Zusammenfassung.
- Geordneter Stop über `POST /api/control/stop` mit wiederholter Erreichbarkeitsprüfung.
- `.\.venv\Scripts\python.exe scripts\runtime_preflight.py`.
- Verdeckter Start über `cmd.exe`, `setup_local_env.bat` und `.venv\Scripts\python.exe main.py --headless --web`; finaler Lauf mit freigegebenem Netzwerkzugriff.
- Read-only Python-/PowerShell-Prüfungen der ab Baseline angehängten JSONL-Bereiche mit `contract_errors()`, rekursivem Bulk-Feld-Scan und ID-Mengenvergleich.

### Ausgeführte Tests

- Runtime-Preflight.
- Kontrollierter Stop-/Start-Lifecycle ohne erzwungenen Prozessabbruch.
- Drei vollständige Live-Produktionszyklen des finalen Laufs.
- Vertragsprüfung neu angehängter Brain-, Decision-, Signal- und NeuroBrain-Datensätze.
- Rekursiver Ausschlusscheck für `raw_result`, `features`, `market_data_diagnostics` und `candles`.
- Ende-zu-Ende-Abgleich der ID-Kette und NeuroBrain-Spiegelung.
- Live-Health-, Preis-, Journal-, Storage- und Telegram-Prüfung.

### Tatsächliche Testergebnisse

- Preflight: bestanden mit Python 3.12.13.
- Finaler Lauf seit 23:15:40 Uhr: drei vollständige Zyklen; Plattform, Web und alle zehn Services `OK`.
- Crypto: 3/3 Ergebnisse je Zyklus, neun publizierte Ergebnisse, aktuelle Preise BTCUSDT `62772.0`, ETHUSDT `1841.07`, XRPUSDT `1.0588` beim Abschlussabruf.
- Stock: 5/5 Ergebnisse je Zyklus, 15 publizierte Ergebnisse.
- Ab neuer finaler Baseline zunächst 20 Brain-, 20 Decision-, 20 Signal- und 154 NeuroBrain-Zeilen geprüft; alle enthielten keine verbotenen Bulk-Felder.
- Brain, Decision und Signal: 0 Vertragsfehler. Sämtliche geprüften marktbezogenen NeuroBrain-Zeilen: 0 Vertragsfehler.
- ID-Abgleich: 0 Kettenfehler; keine geprüfte Decision- oder Signal-Event-ID fehlte in NeuroBrain.
- Offener Befund: In einem früheren Zwei-Zyklen-Ausschnitt waren 18 von 94 NeuroBrain-Zeilen für Lifecycle-/Learning- und reine Market-Data-Topics nach dem Marktvertrag ungültig, weil `market_type` oder `symbol` fehlten. Dieser Befund ist `KP-016`.
- Fehlerjournal im finalen Lauf: gesund, `failed_writes=0`, seit dem Start um 23:15:40 Uhr keine neuen Einträge. Die drei während des eingeschränkten Prüflaufs erzeugten Crypto-Fingerprints endeten spätestens um 21:12:20 UTC und wurden nicht gelöscht.
- Telegram: `enabled=false`, `dry_run=true`, `messages_sent=0`.
- Storage beim Abschlussabruf: `VERIFIED`, 115 physische Dateien, 7,95 GB; normaler Runtime-Zuwachs, keine Bereinigung.

### Bekannte Fehler

- `KP-016`: NeuroBrain kennzeichnet nicht marktbezogene Topics mit dem Markt-Schema Version 1, obwohl Pflichtfelder fehlen können.
- `KP-013`: Der Stop ist kooperativ, kann wegen laufendem Adapterzyklus plus nicht unterbrechbarem Intervallsleep mehrere Minuten benötigen; der erste Stop dieser Aufgabe dauerte rund acht Minuten, zeigte dabei aber fortlaufenden Fortschritt.
- Die übrigen offenen Punkte aus `docs/KNOWN_PROBLEMS.md` bleiben bestehen.

### Getroffene Architekturentscheidungen

- Die Liveverifikation ändert keine Architektur und startet die NeuroBrain-Queue noch nicht.
- Markt-Payload-Migration und nicht marktbezogener Lifecycle-Vertrag werden als getrennte Belange behandelt.
- Der Schemakonflikt muss vor der Queue-/Batch-Entkopplung behoben werden, damit asynchrones Persistieren keine formal uneindeutigen Zeilen vervielfacht.
- Telegram bleibt deaktiviert/Dry-Run; reale Orderausführung bleibt ausgeschlossen.

### Nicht abgeschlossene Punkte

- `KP-016` ist dokumentiert, aber noch nicht implementiert oder getestet behoben.
- NeuroBrain bleibt synchroner EventBus-Consumer; Queue, Überlaufregel, Batch-Schreiben und sicherer Shutdown sind noch nicht implementiert.
- Draft-PR #13 bleibt gegen `agent/compact-decision-signal-payloads` geöffnet, Draft und ungemergt.

### Exakter nächster sinnvoller Arbeitsschritt

Zuerst `KP-016` klein und testgetrieben beheben: tatsächliche NeuroBrain-Topicgruppen inventarisieren, Markt-Payloads nur bei vollständigen Pflichtfeldern als `pandorickki.compact-market-event` Version 1 kennzeichnen und für Lifecycle-/Learning-Ereignisse eine eindeutige kompakte Projektion beziehungsweise ein eigenes Schema festlegen. Bestehende Inboxzeilen nicht verändern. Danach gezielte Tests und vollständige Suite ausführen und erst nach erfolgreicher Liveprüfung mit der begrenzten NeuroBrain-Queue beginnen.

---

## Aktuelle Aufgabe: NeuroBrain-Inbox kompakt migrieren

### Datum und Uhrzeit

1. August 2026, 22:43 Uhr, Europe/Berlin (`+02:00`)

### Ziel der Aufgabe

Als letzte Payload-Persistenzgrenze ausschließlich neue NeuroBrain-Inboxzeilen auf `pandorickki.compact-market-event` Version 1 umstellen. Kopfsicht, tatsächlich gespiegelte Event-ID, vorgelagerte Quellreferenzen, Topicfilter und Duplikatschutz erhalten. Bestehende Inboxdateien nicht verändern; Queue-/Batch-Entkopplung noch nicht beginnen.

### Durchgeführte Arbeiten

- Vorgeschriebene Übergabedokumentation, Payload-Vertrag, tatsächlichen NeuroBrainReceiverAdapter und seine Lifecycle-/Duplikatlogik erneut geprüft.
- Gestapelten Branch `agent/compact-neurobrain-payloads` von `agent/compact-decision-signal-payloads` erstellt.
- Zwei neue Regressionstests zunächst vor dem Fix ausgeführt und die vollständige Payloadkopie durch fehlendes `schema_name` reproduziert.
- `_to_record()` projiziert die Event-Payload nun einmalig über `compact_market_payload()`.
- NeuroBrain-Kopfsicht wird aus der kompakten Projektion befüllt und behält die ID des tatsächlich gespiegelten Events separat als oberes `source_event_id`.
- Die Detailpayload bewahrt ihre vorgelagerte Quellreferenz sowie Decision-/Signal-IDs, Markt-, Symbol-, Richtungs- und Zeitfelder.
- Raw Results, Features, Kerzen, Diagnostik und interne Raw-Felder werden nicht in neue Inboxzeilen übernommen.
- Quell-Event bleibt beim Spiegeln unverändert; Größenregression verlangt weniger als ein Viertel des umfangreichen Testinputs.
- Vorhandene Legacy-Inboxzeile im Test bytegenau erhalten und kompakte neue Zeile dahinter angefügt.
- Duplikat-, unerwünschte Topic-, Lifecycle- und Orchestrator-Tests weiter bestanden.
- Architektur-, Systemzustands-, Vertrags-, Problem- und Planungsdokumentation aktualisiert.
- Commit `5d32bc7` auf `origin/agent/compact-neurobrain-payloads` veröffentlicht und gestapelten Draft-PR #13 gegen `agent/compact-decision-signal-payloads` erstellt.
- Keine bestehende Runtime-, NeuroBrain-Inbox-, Lern-, Token- oder Konfigurationsdatei verändert oder gelöscht.

### Veränderte Dateien

- `adapters/neurobrain_receiver_adapter.py`
- `tests/test_neurobrain_receiver_adapter.py`
- `docs/CURRENT_SYSTEM_STATE.md`
- `docs/SESSION_HANDOVER.md`
- `docs/ARCHITECTURE.md`
- `docs/EVENT_PAYLOAD_CONTRACT.md`
- `docs/KNOWN_PROBLEMS.md`
- `docs/NEXT_STEPS.md`

### Neue Dateien

- Keine.

### Ausgeführte Befehle

- Vollständiges Lesen von `AGENTS.md`, den fünf Übergabedateien und `docs/EVENT_PAYLOAD_CONTRACT.md`.
- Code-, Konfigurations- und Testinventur mit `rg` und `Get-Content`.
- `git switch -c agent/compact-neurobrain-payloads`.
- Zwei isolierte Regressionstests vor dem Fix, gezielte NeuroBrain-/Vertrags-/Decision-/Brain-Tests, vollständige Testsuite und `py_compile`.
- `git diff --check`, Scope- und Secret-Mustersuche.
- Explizites Staging, Commit, Push und Draft-PR-Erstellung über `gh`.

### Ausgeführte Tests

- Zwei neue isolierte NeuroBrain-Regressionstests vor dem Fix.
- `.\.venv\Scripts\python.exe -m unittest tests.test_neurobrain_receiver_adapter tests.test_event_payload_contract tests.test_decision_signal_adapter tests.test_brain_adapter -v`
- `.\.venv\Scripts\python.exe -m py_compile adapters\neurobrain_receiver_adapter.py tests\test_neurobrain_receiver_adapter.py`
- `.\.venv\Scripts\python.exe -m unittest discover -s tests`

### Tatsächliche Testergebnisse

- Vor dem Fix: beide Regressionstests erwartungsgemäß mit fehlendem `schema_name` gescheitert.
- Nach dem Fix: 18/18 gezielte NeuroBrain-/Vertrags-/Decision-/Brain-Tests bestanden in 0,464 Sekunden.
- Vollständige Suite: 224/224 bestanden in 50,007 Sekunden.
- `py_compile`, `git diff --check` und Secret-Prüfung: bestanden; keine Secret-Treffer.
- Größenprüfung: kompakte NeuroBrain-Detailpayload kleiner als 25 % der umfangreichen Eingangspayload.
- Legacy-Test: vorhandene erste Inboxzeile blieb bytegenau identisch; neue kompakte Zeile wurde angefügt.
- Bekannte `datetime.utcnow()`-DeprecationWarnings stammen aus dem externen Legacy-Crypto-Projekt.

### Bekannte Fehler

- `KP-015` ist implementiert und vollständig testgrün, aber der gesamte gestapelte Payloadstand wurde noch nicht kontrolliert live neu gestartet.
- NeuroBrain bleibt synchroner EventBus-Consumer ohne Queue oder Backpressure; dies ist der nächste Architekturpunkt, nicht Teil dieser Payload-Migration.
- Die übrigen offenen Punkte aus `docs/KNOWN_PROBLEMS.md` bleiben unverändert.

### Getroffene Architekturentscheidungen

- NeuroBrain behält zwei Referenzebenen: oberer Inbox-Kopf für das gespiegelte Event, kompakte Detailpayload für dessen vorgelagerte fachliche Referenzen.
- Das Quell-Event wird nicht mutiert; nur die persistierte Kopie wird projiziert.
- Bestehende Inboxzeilen werden nicht migriert, umgeschrieben oder gelöscht.
- Payload-Migration und asynchrone Queue-/Batch-Entkopplung bleiben getrennte Änderungen.
- Keine reale Orderausführung und keine Änderung der Telegram-Sicherheitsgrenze.

### Nicht abgeschlossene Punkte

- Draft-PR #13: `https://github.com/cRioshy/Pando/pull/13`, Basis `agent/compact-decision-signal-payloads`; Draft und ungemergt.
- Der aktuell laufende lokale Dienst wurde in diesem Schritt nicht neu gestartet; alle Payloadänderungen sind per Unit-/Integrationssuite verifiziert und werden erst nach kontrolliertem Neustart aktiv.
- Queue, Überlaufregel, Batch-Schreiben und sicherer Shutdown für NeuroBrain sind noch nicht implementiert.

### Exakter nächster sinnvoller Arbeitsschritt

Den vollständigen gestapelten Payloadstand kontrolliert neu starten. Vorher die aktuellen Zeilen-/Dateigrößen und letzten IDs der Brain-, Decision-, Signal- und NeuroBrain-Ledger read-only erfassen; danach mindestens zwei vollständige Produktionszyklen abwarten und ausschließlich neu angehängte Zeilen auf Schema Version 1, erhaltene ID-Ketten, fehlende Bulk-Felder, Service-Health, Journalfehler und Telegram-Sicherheitszustand prüfen. Erst nach erfolgreicher Liveverifikation mit der begrenzten NeuroBrain-Queue beginnen.

---

## Aktuelle Aufgabe: Decision-/Signal-Events und Ledger kompakt migrieren

### Datum und Uhrzeit

1. August 2026, 22:23 Uhr, Europe/Berlin (`+02:00`)

### Ziel der Aufgabe

Nach der Brain-Grenze ausschließlich den `DecisionSignalAdapter` auf `pandorickki.compact-market-event` Version 1 umstellen. Neue Decision-/Signal-Events und beide rotierenden Ledger sollen ohne `raw_result` auskommen, während Decision-, Signal-, Decision-Event- und Quell-IDs erhalten bleiben. Bestehende Ledger und NeuroBrain-Persistenz nicht verändern.

### Durchgeführte Arbeiten

- Vorgeschriebene Übergabedokumentation, Payload-Vertrag, tatsächlichen DecisionSignalAdapter und abhängige Consumer erneut geprüft.
- Gestapelten Branch `agent/compact-decision-signal-payloads` von `agent/compact-brain-payloads` erstellt.
- Neuen End-to-End-Regressionstest mit umfangreichem Legacy-Brain-Payload zunächst vor dem Fix ausgeführt; fehlende Vertragsversion reproduziert.
- `_decision_payload()` projiziert Eingänge nun zuerst auf Version 1 und ergänzt ausschließlich Decision-spezifische ID-, Zeit- und Begründungsfelder.
- `_signal_payload()` projiziert die Decision erneut auf Version 1 und ergänzt Signal-, Decision-Event-, Freigabe- und Zeitfelder.
- Decision-/Signal-Events und Ledger verwenden jeweils dieselbe kompakte Payload.
- Quell-, Decision-, Signal- und Decision-Event-IDs sowie Markt-, Preis-, Risiko- und Kontextfelder erhalten.
- Raw Results, Features, Kerzen und interne Raw-Felder werden nicht neu in Events oder Ledger übernommen.
- Legacy-Brain-Eingang mit Raw Result bleibt kompatibel: `public_result` und Swing-Kontext werden vor dem Ausschluss verdichtet.
- Größenregression ergänzt: Signal-Ledgerpayload muss beim umfangreichen Testinput kleiner als ein Viertel der Eingangspayload sein.
- Outcome Tracker, Crypto Trade Tracker und vollständigen Integrationsfluss erfolgreich geprüft.
- Architektur-, Systemzustands-, Vertrags-, Problem- und Planungsdokumentation aktualisiert.
- Commit `ed89a01` auf `origin/agent/compact-decision-signal-payloads` veröffentlicht und gestapelten Draft-PR #12 gegen `agent/compact-brain-payloads` erstellt.
- Keine bestehende Runtime-, Decision-/Signal-History-, Lern-, Token- oder Konfigurationsdatei verändert oder gelöscht.

### Veränderte Dateien

- `adapters/decision_signal_adapter.py`
- `tests/test_decision_signal_adapter.py`
- `docs/CURRENT_SYSTEM_STATE.md`
- `docs/SESSION_HANDOVER.md`
- `docs/ARCHITECTURE.md`
- `docs/EVENT_PAYLOAD_CONTRACT.md`
- `docs/KNOWN_PROBLEMS.md`
- `docs/NEXT_STEPS.md`

### Neue Dateien

- Keine.

### Ausgeführte Befehle

- Vollständiges Lesen von `AGENTS.md`, den fünf Übergabedateien und `docs/EVENT_PAYLOAD_CONTRACT.md`.
- Code- und Consumer-Inventur mit `rg` und `Get-Content`.
- `git switch -c agent/compact-decision-signal-payloads`.
- Isolierter Regressionstest vor dem Fix, gezielte Modul-/Consumer-/Integrationstests, vollständige Testsuite und `py_compile`.
- `git diff --check`, Scope- und Secret-Mustersuche.
- Explizites Staging, Commit, Push und Draft-PR-Erstellung über `gh`.

### Ausgeführte Tests

- Neuer isolierter Decision-/Signal-/Ledger-Regressionstest vor dem Fix.
- `.\.venv\Scripts\python.exe -m unittest tests.test_decision_signal_adapter tests.test_brain_adapter tests.test_outcome_tracker tests.test_crypto_trade_tracker tests.test_event_payload_contract tests.test_integration_full -v`
- `.\.venv\Scripts\python.exe -m py_compile adapters\decision_signal_adapter.py tests\test_decision_signal_adapter.py`
- `.\.venv\Scripts\python.exe -m unittest discover -s tests`

### Tatsächliche Testergebnisse

- Vor dem Fix: Regressionstest erwartungsgemäß mit fehlendem `schema_name` gescheitert.
- Nach dem Fix: 32/32 gezielte Decision-/Brain-/Outcome-/Tracker-/Integrations-/Vertragstests bestanden in 1,846 Sekunden.
- Vollständige Suite: 223/223 bestanden in 49,274 Sekunden.
- `py_compile`, `git diff --check` und Secret-Prüfung: bestanden; keine Secret-Treffer.
- Größenprüfung: kompakte Signal-Ledgerpayload kleiner als 25 % der umfangreichen Legacy-Eingangspayload.
- Bekannte `datetime.utcnow()`-DeprecationWarnings stammen aus dem externen Legacy-Crypto-Projekt.

### Bekannte Fehler

- `KP-015` bleibt nur für NeuroBrain offen: Es speichert neben seiner kompakten Kopfsicht weiterhin die vollständige empfangene Event-Payload.
- Brain und Decision Core sind für neue Events und Ledger kompakt; bestehende alte Historien enthalten erwartungsgemäß weiterhin Raw-Felder.
- Die übrigen offenen Punkte aus `docs/KNOWN_PROBLEMS.md` bleiben unverändert.

### Getroffene Architekturentscheidungen

- Jede Decision-/Signal-Stufe besitzt eine eigene Version-1-Projektion mit stufenspezifischen IDs.
- Events und Ledger verwenden exakt dieselbe Payload, damit keine zweite größere Persistenzsicht entsteht.
- Legacy-Eingänge werden vor dem Entfernen von Raw-Daten auf `public_result` und `market_context` verdichtet.
- Bestehende Ledger werden nicht migriert, umgeschrieben oder gelöscht.
- NeuroBrain bleibt ein separater Folgeschritt; keine reale Orderausführung und keine Änderung der Telegram-Sicherheitsgrenze.

### Nicht abgeschlossene Punkte

- Draft-PR #12: `https://github.com/cRioshy/Pando/pull/12`, Basis `agent/compact-brain-payloads`; Draft und ungemergt.
- Der aktuell laufende lokale Dienst wurde in diesem Schritt nicht neu gestartet; die Änderung ist per Unit-/Integrationssuite verifiziert und wird erst nach kontrolliertem Neustart aktiv.
- NeuroBrain-Persistenz ist die verbleibende kompakte Payload-Migration.

### Exakter nächster sinnvoller Arbeitsschritt

`NeuroBrainReceiverAdapter._project_event()` in einem eigenen Schritt so ändern, dass `payload` nur noch die Version-1-Projektion enthält, während Topic, Quelle, `source_event_id`, Decision-/Signal-IDs, Markt-, Symbol-, Richtungs- und Zeitkopfsicht erhalten bleiben. Bestehende Inboxdateien nicht verändern oder löschen. Mit Duplikat-, Größen-, Schema-, Restart- und Legacy-Eingangstests absichern; Queue-/Batch-Entkopplung erst danach separat beginnen.

---

## Aktuelle Aufgabe: Brain-History und Brain-Event kompakt migrieren

### Datum und Uhrzeit

1. August 2026, 22:02 Uhr, Europe/Berlin (`+02:00`)

### Ziel der Aufgabe

Als erste Producer-/Persistenzgrenze ausschließlich den `BrainAdapter` auf `pandorickki.compact-market-event` Version 1 umstellen. Neue Brain-History und `BRAIN_DECISION_RECEIVED` sollen dieselbe kompakte Projektion mit erhaltener Quell-ID verwenden. Bestehende History, Decision-/Signal-Persistenz und NeuroBrain bleiben in diesem Schritt unverändert.

### Durchgeführte Arbeiten

- Vorgeschriebene Übergabedokumentation, Payload-Vertrag, tatsächlichen BrainAdapter und alle relevanten Tests erneut geprüft.
- Gestapelten Branch `agent/compact-brain-payloads` von `agent/prepare-compact-payload-consumers` erstellt.
- Neuen Regressionstest mit 500 Kerzen, Trainingsfeatures, Diagnostik und internem Raw-Feld zunächst vor dem Fix ausgeführt; fehlende Vertragsversion reproduziert.
- Brain erzeugt nun direkt an der Eingangsgrenze einmalig `compact_market_payload()` und verwendet dieselbe Projektion für rotierte History sowie `BRAIN_DECISION_RECEIVED`.
- Eventtyp, kanonische Quell-Event-ID, Confidence und Brain-Empfangszeit explizit erhalten beziehungsweise ergänzt.
- Raw Results, Features, Marktdiagnostik, Kerzen und interne Raw-Felder werden nicht in neue Brain-Datensätze oder Folgeevents übernommen.
- Größenregression ergänzt: Die gespeicherte Projektion muss beim umfangreichen Testinput kleiner als ein Viertel der Eingangspayload sein.
- Bestehenden vollständigen Integrationsfluss bis Decision Core und Tracker erfolgreich geprüft.
- Architektur-, Systemzustands-, Vertrags-, Problem- und Planungsdokumentation auf die aktive Brain-Grenze aktualisiert.
- Commit `5b59fa2` auf `origin/agent/compact-brain-payloads` veröffentlicht und gestapelten Draft-PR #11 gegen `agent/prepare-compact-payload-consumers` erstellt.
- Keine bestehende Runtime-, Brain-History-, Lern-, Token- oder Konfigurationsdatei verändert oder gelöscht.

### Veränderte Dateien

- `adapters/brain_adapter.py`
- `tests/test_brain_adapter.py`
- `docs/CURRENT_SYSTEM_STATE.md`
- `docs/SESSION_HANDOVER.md`
- `docs/ARCHITECTURE.md`
- `docs/EVENT_PAYLOAD_CONTRACT.md`
- `docs/KNOWN_PROBLEMS.md`
- `docs/NEXT_STEPS.md`

### Neue Dateien

- Keine.

### Ausgeführte Befehle

- Vollständiges Lesen von `AGENTS.md`, den fünf Übergabedateien und `docs/EVENT_PAYLOAD_CONTRACT.md`.
- Code- und Testinventur mit `rg` und `Get-Content`.
- `git switch -c agent/compact-brain-payloads`.
- Isolierter Regressionstest vor dem Fix, gezielte Modul-/Integrationstests, vollständige Testsuite und `py_compile`.
- `git diff --check`, Scope- und Secret-Mustersuche.
- Explizites Staging, Commit, Push und Draft-PR-Erstellung über `gh`.

### Ausgeführte Tests

- Neuer isolierter kompakter Brain-Regressionstest vor dem Fix.
- `.\.venv\Scripts\python.exe -m unittest tests.test_brain_adapter tests.test_decision_signal_adapter tests.test_crypto_trade_tracker tests.test_event_payload_contract tests.test_learning_graph_phase3 tests.test_integration_full -v`
- `.\.venv\Scripts\python.exe -m py_compile adapters\brain_adapter.py tests\test_brain_adapter.py`
- `.\.venv\Scripts\python.exe -m unittest discover -s tests`

### Tatsächliche Testergebnisse

- Vor dem Fix: Regressionstest erwartungsgemäß mit fehlendem `schema_name` gescheitert.
- Nach dem Fix: 28/28 gezielte Brain-/Decision-/Tracker-/Graph-/Integrations-/Vertragstests bestanden in 1,258 Sekunden.
- Vollständige Suite: 222/222 bestanden in 52,209 Sekunden.
- `py_compile`, `git diff --check` und Secret-Prüfung: bestanden; keine Secret-Treffer.
- Größenprüfung: kompakte Brain-Persistenz kleiner als 25 % der umfangreichen Testpayload.
- Bekannte `datetime.utcnow()`-DeprecationWarnings stammen aus dem externen Legacy-Crypto-Projekt.

### Bekannte Fehler

- `KP-015` bleibt teilweise offen: Decision-/Signal-Payloads führen das Legacy-Feld `raw_result` noch weiter, bei kompaktem Brain-Input allerdings als `None`.
- NeuroBrain speichert neben seiner Kopfsicht weiterhin die vollständige empfangene Event-Payload.
- Die übrigen offenen Punkte aus `docs/KNOWN_PROBLEMS.md` bleiben unverändert.

### Getroffene Architekturentscheidungen

- Projektion genau einmal an der Brain-Eingangsgrenze und Wiederverwendung derselben Sicht für Persistenz und Folgeevent.
- `Event.event_id` ist die kanonische `source_event_id`, auch wenn der Event-Umschlag kein eigenes `event_id`-Feld enthält.
- Neue Brain-Persistenz ist ausschließlich Version 1; alte History bleibt unverändert und weiterhin lesbar.
- Decision Core und NeuroBrain werden in getrennten Folgeschritten migriert, damit Fehlergrenzen und Größenwirkung isoliert testbar bleiben.
- Keine reale Orderausführung und keine Änderung der Telegram-Sicherheitsgrenze.

### Nicht abgeschlossene Punkte

- Draft-PR #11: `https://github.com/cRioshy/Pando/pull/11`, Basis `agent/prepare-compact-payload-consumers`; Draft und ungemergt.
- Der aktuell laufende lokale Dienst wurde in diesem Schritt nicht neu gestartet; die Änderung ist per Unit-/Integrationssuite verifiziert und wird erst nach kontrolliertem Neustart aktiv.
- Decision-/Signal- und NeuroBrain-Persistenz sind noch nicht vollständig migriert.

### Exakter nächster sinnvoller Arbeitsschritt

`DecisionSignalAdapter` in einem eigenen kleinen Schritt auf die Version-1-Projektion umstellen: Decision- und Signal-IDs sowie Quellreferenzen erhalten, `raw_result` nicht mehr als Feld in neue Decision-/Signal-Ledger schreiben und Decision-/Signal-Events per Vertrags- und Größenregression prüfen. Bestehende Ledger nicht ändern oder löschen; NeuroBrain erst danach separat migrieren.

---

## Aktuelle Aufgabe: Consumer für kompakte Event-Payloads vorbereiten

### Datum und Uhrzeit

1. August 2026, 21:50 Uhr, Europe/Berlin (`+02:00`)

### Ziel der Aufgabe

Die zwei im Payload-Vertrag dokumentierten Raw-Abhängigkeiten rückwärtskompatibel auf kompakte Ersatzfelder vorbereiten. Crypto Trade Tracker und Learning Graph sollen neue Payloads bevorzugen, alte Events und History aber weiterhin lesen. Brain-, Decision-/Signal- und NeuroBrain-Producer beziehungsweise Persistenz noch nicht verkleinern.

### Durchgeführte Arbeiten

- Vorgeschriebene Übergabedokumentation, Payload-Vertrag, Branchstand und tatsächliche Consumer erneut geprüft.
- Gestapelten Branch `agent/prepare-compact-payload-consumers` von `agent/define-compact-event-payload-contract` erstellt.
- Zwei Regressionstests zunächst vor dem Fix ausgeführt und beide falschen Prioritäten reproduziert.
- `CryptoTradeTracker._swing_price()` so geändert, dass `market_context.recent_swing_low/high` bei gültigen Werten Vorrang hat.
- Bisherige Berechnung aus den letzten 20 Kerzen in `raw_result.market_data.candles` unverändert als Legacy-Fallback erhalten.
- `LearningGraphBuilder._public_result()` so geändert, dass `public_result` Vorrang vor `raw_result.result` hat.
- Bestehenden Raw-Ergebniszugriff als Legacy-Fallback erhalten.
- Je Consumer Prioritäts- und Legacy-Fallback-Test ergänzt.
- Architektur-, Systemzustands-, Vertrags-, Problem- und Planungsdokumentation aktualisiert.
- Commit `1550d07` auf `origin/agent/prepare-compact-payload-consumers` veröffentlicht und gestapelten Draft-PR #10 gegen `agent/define-compact-event-payload-contract` erstellt.
- Keine Runtime-, History-, Lern-, Token- oder Konfigurationsdatei verändert oder gelöscht.

### Veränderte Dateien

- `adapters/crypto_trade_tracker.py`
- `learning_graph/graph_builder.py`
- `tests/test_crypto_trade_tracker.py`
- `tests/test_learning_graph_phase3.py`
- `docs/CURRENT_SYSTEM_STATE.md`
- `docs/SESSION_HANDOVER.md`
- `docs/ARCHITECTURE.md`
- `docs/EVENT_PAYLOAD_CONTRACT.md`
- `docs/KNOWN_PROBLEMS.md`
- `docs/NEXT_STEPS.md`

### Neue Dateien

- Keine.

### Ausgeführte Befehle

- Vollständiges Lesen von `AGENTS.md`, den fünf Übergabedateien und `docs/EVENT_PAYLOAD_CONTRACT.md`.
- Code- und Testinventur mit `rg` und `Get-Content`.
- `git switch -c agent/prepare-compact-payload-consumers`.
- Gezielte Regressionstests vor und nach dem Fix, vollständige Testsuite und `py_compile`.
- `git diff --check`, Scope- und Secret-Mustersuche.
- Explizites Staging, Commit, Push und Draft-PR-Erstellung über `gh`.

### Ausgeführte Tests

- Zwei neue isolierte Prioritätstests vor dem Fix.
- `.\.venv\Scripts\python.exe -m unittest tests.test_crypto_trade_tracker tests.test_learning_graph_phase3 tests.test_event_payload_contract -v`
- `.\.venv\Scripts\python.exe -m py_compile adapters\crypto_trade_tracker.py learning_graph\graph_builder.py tests\test_crypto_trade_tracker.py tests\test_learning_graph_phase3.py`
- `.\.venv\Scripts\python.exe -m unittest discover -s tests`

### Tatsächliche Testergebnisse

- Vor dem Fix: 2/2 Prioritätstests erwartungsgemäß fehlgeschlagen. Tracker lieferte Raw-Swing `90.0` statt kompakt `98.5`; Graph lieferte Raw-Ergebnis `TP3_WIN` statt kompakt `DIRECT_STOP`.
- Nach dem Fix: 20/20 gezielte Tracker-/Graph-/Vertragstests bestanden in 0,142 Sekunden.
- Vollständige Suite: 221/221 bestanden in 48,558 Sekunden.
- `py_compile`, `git diff --check` und Secret-Prüfung: bestanden; keine Secret-Treffer.
- Bekannte `datetime.utcnow()`-DeprecationWarnings stammen aus dem externen Legacy-Crypto-Projekt.

### Bekannte Fehler

- `KP-015` bleibt offen: Brain, Decision Core und NeuroBrain transportieren beziehungsweise persistieren weiterhin vollständige Raw Results.
- Die beiden bisherigen Consumer-Blocker sind entschärft; Raw-Zugriffe existieren bewusst nur noch als Legacy-Fallback.
- Die übrigen offenen Punkte aus `docs/KNOWN_PROBLEMS.md` bleiben unverändert.

### Getroffene Architekturentscheidungen

- Kompakte Felder haben Vorrang; Raw-Felder bleiben während der Migration ausschließlich als Lesefallback.
- Ungültige oder fehlende kompakte Swing-Werte fallen weiterhin sicher auf den bisherigen Kerzenpfad zurück.
- Keine Historymigration und keine Änderung bestehender Producer in diesem Schritt.
- Keine reale Orderausführung und keine Änderung der Telegram-Sicherheitsgrenze.

### Nicht abgeschlossene Punkte

- Draft-PR #10: `https://github.com/cRioshy/Pando/pull/10`, Basis `agent/define-compact-event-payload-contract`; Draft und ungemergt.
- Brain-/Decision-/Signal-Producer und NeuroBrain-Persistenz verwenden die kompakte Projektion noch nicht.
- Bestehende History benötigt auch nach der Producer-Umstellung weiterhin die Legacy-Lesefallbacks.

### Exakter nächster sinnvoller Arbeitsschritt

Die Producer-/Persistenzmigration klein aufteilen: zuerst `BrainAdapter` so umstellen, dass neu geschriebene Brain-Datensätze und `BRAIN_DECISION_RECEIVED` ausschließlich die Version-1-Projektion mit erhaltenen IDs verwenden. `DecisionSignalAdapter` und NeuroBrain zunächst unverändert lassen, damit die Brain-Grenze isoliert mit Kompatibilitäts- und Größenregressionstests geprüft werden kann. Bestehende Brain-History nicht ändern oder löschen.

---

## Aktuelle Aufgabe: Kompakten Event-Payload-Vertrag Version 1 definieren

### Datum und Uhrzeit

1. August 2026, 21:15 Uhr, Europe/Berlin (`+02:00`)

### Ziel der Aufgabe

Vor der späteren Verkleinerung von Brain- und NeuroBrain-Ledgern den tatsächlichen Feldverbrauch aller relevanten Event-Consumer ermitteln und einen versionierten, getesteten kompakten Payload-Vertrag festlegen. Noch keine Produktionspayloads umstellen, keine History verändern, keine realen Trades oder Orderausführung aktivieren und Telegram deaktiviert beziehungsweise im Dry-Run lassen.

### Durchgeführte Arbeiten

- Vorgeschriebene Übergabedokumentation, Git-Stand und tatsächliche Producer-/Consumer-Codepfade geprüft.
- Gestapelten Branch `agent/define-compact-event-payload-contract` von `agent/fix-outcome-timestamp-normalization` erstellt.
- Producer in Crypto-, Stock-, Commodity-, Brain- und Decision-/Signal-Adaptern inventarisiert.
- Feldleser in Brain, Decision Core, Crypto Trade Tracker, Outcome Tracker, Control Center, Telegram, Learning Graph und NeuroBrain geprüft.
- Zwei verbliebene echte Raw-Abhängigkeiten identifiziert: Crypto-Swings aus `raw_result.market_data.candles` und Learning-Ergebnis aus `raw_result.result`.
- Vertrag `pandorickki.compact-market-event` Version 1 als ausführbare Referenzprojektion und Validator implementiert.
- Legacy-Kerzen werden im Migrationshelfer ausschließlich auf `recent_swing_low`/`recent_swing_high` verdichtet; `public_result` ersetzt das Legacy-Ergebnislabel.
- `raw_result`, `features`, `market_data_diagnostics` und `candles` in jeder Verschachtelung des Zielvertrags verboten.
- Fünf Vertragstests und vollständige Architektur-/Feldmatrix-Dokumentation ergänzt.
- Produktionsadapter bewusst nicht verdrahtet; laufendes Verhalten und vorhandene History bleiben unverändert.
- Commit `311dd38` auf `origin/agent/define-compact-event-payload-contract` veröffentlicht und gestapelten Draft-PR #9 gegen `agent/fix-outcome-timestamp-normalization` erstellt.

### Veränderte Dateien

- `AGENTS.md`
- `docs/CURRENT_SYSTEM_STATE.md`
- `docs/SESSION_HANDOVER.md`
- `docs/ARCHITECTURE.md`
- `docs/KNOWN_PROBLEMS.md`
- `docs/NEXT_STEPS.md`

### Neue Dateien

- `event_payload_contract.py`
- `tests/test_event_payload_contract.py`
- `docs/EVENT_PAYLOAD_CONTRACT.md`

### Ausgeführte Befehle

- Vollständiges Lesen der vorgeschriebenen Übergabedateien und gezielte Codeinventur mit `rg` und `Get-Content`.
- `git switch -c agent/define-compact-event-payload-contract`.
- Gezielte `unittest`-Läufe, vollständige Testsuite, `py_compile`, `git diff --check` und Secret-Mustersuche.
- Explizites Staging, Commit, `git push -u origin agent/define-compact-event-payload-contract`.
- `gh auth status` und `gh pr create --draft` für den gestapelten PR.

### Ausgeführte Tests

- `.\.venv\Scripts\python.exe -m unittest tests.test_event_payload_contract -v`
- `.\.venv\Scripts\python.exe -m unittest discover -s tests`
- `.\.venv\Scripts\python.exe -m py_compile event_payload_contract.py tests\test_event_payload_contract.py`
- `git diff --check`
- Secret-Mustersuche im neuen Code, den Tests und der Vertragsdokumentation.

### Tatsächliche Testergebnisse

- Vertragstests: 5/5 bestanden in 0,002 Sekunden.
- Vollständige Suite: 217/217 bestanden in 45,511 Sekunden.
- `py_compile`: bestanden.
- Secret-Mustersuche: keine Treffer.
- `git diff --check`: initial zwei Markdown-Zeilen mit absichtlichem Zeilenumbruch als Whitespace gemeldet; vor dem Abschluss entfernt und erneut geprüft.
- Bekannte `datetime.utcnow()`-DeprecationWarnings stammen aus dem externen Legacy-Crypto-Projekt.

### Bekannte Fehler

- `KP-015` bleibt offen: Die heutige Laufzeit transportiert und persistiert weiterhin vollständige Raw Results. Der neue Vertrag ist noch nicht produktiv aktiviert.
- Crypto Trade Tracker und Learning Graph müssen vor der Producer-Umschaltung auf ihre kompakten Ersatzfelder vorbereitet werden.
- Die übrigen offenen Punkte aus `docs/KNOWN_PROBLEMS.md` bleiben unverändert.

### Getroffene Architekturentscheidungen

- Ein gemeinsamer, explizit versionierter Vertrag statt stillschweigender Feldentfernung.
- Bulk-, Trainings- und Diagnostikfelder sind im kompakten Vertrag verboten; strukturierte Fakten, Indikatoren und Risiko bleiben als begrenzte Consumer-Sichten erhalten.
- Schema-Version 1 ist zunächst ein inaktives Migrationsziel. Producer werden erst nach Consumer-Kompatibilität umgestellt.
- Bestehende JSONL-History wird nicht migriert, umgeschrieben oder gelöscht; Leser benötigen weiterhin einen Legacy-Pfad.
- Telegram- und Orderfreigabe sind ausdrücklich nicht Bestandteil der Payload-Migration.

### Nicht abgeschlossene Punkte

- Draft-PR #9: `https://github.com/cRioshy/Pando/pull/9`, Basis `agent/fix-outcome-timestamp-normalization`; Draft und ungemergt.
- Crypto Trade Tracker liest die neuen Swing-Felder noch nicht direkt.
- Brain-, Decision-/Signal- und NeuroBrain-Persistenz verwendet die Projektion noch nicht.

### Exakter nächster sinnvoller Arbeitsschritt

In einem kleinen Consumer-Kompatibilitätsschritt zuerst `CryptoTradeTracker` so erweitern, dass er `market_context.recent_swing_low/high` bevorzugt und nur für alte Payloads auf Kerzen zurückfällt; `LearningGraphBuilder` soll `public_result` bevorzugen und `raw_result.result` nur noch als Legacy-Fallback lesen. Dazu gezielte Regressionstests schreiben. Noch keine Producer-Payloads verkleinern und bestehende History nicht verändern.

---

## Aktuelle Aufgabe: KP-014 – Outcome-Zeitstempel normalisieren

### Datum und Uhrzeit

1. August 2026, 20:53 Uhr, Europe/Berlin (`+02:00`)

### Ziel der Aufgabe

Den vom Service-Fehlerjournal live aufgedeckten Outcome-Tracker-Fehler klein und rückwärtskompatibel beheben. Historische ISO-Zeitstempel ohne Offset sollen beim Berechnen als UTC gelten, ohne bestehende offene Trades oder Historydateien umzuschreiben. Keine realen Trades, keine Orderausführung und kein Telegram-Liveversand.

### Durchgeführte Arbeiten

- Vorgeschriebene Übergabedokumentation sowie tatsächlichen Outcome-Tracker und seine Tests vollständig geprüft.
- Gestapelten Branch `agent/fix-outcome-timestamp-normalization` von `agent/add-service-error-journal` erstellt.
- Öffentlichen Regressionstest mit einem Legacy-Trade ohne UTC-Offset und einem neuen offset-bewussten Marktupdate ergänzt.
- Test vor dem Fix ausgeführt und exakt den Livefehler `can't subtract offset-naive and offset-aware datetimes` reproduziert.
- `_duration_seconds()` so geändert, dass nur geparste Zeitstempel ohne `tzinfo` als UTC interpretiert werden; vorhandene Offsetwerte bleiben unverändert.
- Tabellentest für naive, offset-bewusste, gemischte, unterschiedliche Offset-, ungültige und rückwärts laufende Zeitpaare ergänzt.
- Tracker-Health im öffentlichen Fehlerpfad geprüft: Nach dem Fix kein `OUTCOME_TRACKER_ERROR`, `healthy=true`, `last_error=null`.
- Commit `a2a139f` auf `origin/agent/fix-outcome-timestamp-normalization` veröffentlicht und gestapelten Draft-PR #8 gegen `agent/add-service-error-journal` erstellt.
- Laufenden Dienst kontrolliert gestoppt und mit dem Fix sowie unveränderten sicheren Laufzeitwerten neu gestartet.
- Vier vollständige Crypto-Heartbeats live geprüft; der bekannte Journalfingerprint blieb bei 158 und erzeugte kein neues Vorkommen.
- Keine Runtime-, History-, Lern-, Token- oder Konfigurationsdatei verändert oder gelöscht.

### Veränderte Dateien

- `adapters/outcome_tracker.py`
- `tests/test_outcome_tracker.py`
- `docs/CURRENT_SYSTEM_STATE.md`
- `docs/SESSION_HANDOVER.md`
- `docs/KNOWN_PROBLEMS.md`
- `docs/NEXT_STEPS.md`

### Neue Dateien

- Keine.

### Ausgeführte Befehle

- Vollständiges Lesen von `AGENTS.md` und den fünf vorgeschriebenen Übergabedokumenten.
- Git-, Branch-, Code- und Testinventur mit `git`, `rg` und `Get-Content`.
- `git switch -c agent/fix-outcome-timestamp-normalization`.
- Gezielte `unittest`-Läufe, `py_compile`, `git diff --check` und vollständige Testsuite.
- `gh auth status`, explizites Staging, Commit, Push und Draft-PR-Erstellung.
- POST `/api/control/stop`, Runtime-Preflight, versteckter Neustart und read-only API-/Journalprüfung.

### Ausgeführte Tests

- Neuer isolierter Legacy-Zeitstempel-Regressionstest vor dem Fix.
- `python -m unittest tests.test_outcome_tracker`
- `python -m py_compile adapters/outcome_tracker.py tests/test_outcome_tracker.py`
- `python -m unittest discover -s tests`

### Tatsächliche Testergebnisse

- Regressionstest vor dem Fix: erwartungsgemäß fehlgeschlagen; ein `OUTCOME_TRACKER_ERROR` mit dem live beobachteten TypeError wurde erzeugt.
- Outcome-Tracker-Modul nach dem Fix: 12/12 bestanden in 0,449 Sekunden.
- Vollständige Suite: 212/212 bestanden in 48,735 Sekunden.
- `py_compile` und `git diff --check`: bestanden; lediglich erwartete LF-/CRLF-Hinweise von Git.
- Bekannte `datetime.utcnow()`-DeprecationWarnings stammen aus dem externen Legacy-Crypto-Projekt und sind nicht Teil dieses Fixes.
- Live: vier Crypto-Heartbeats; Plattform und alle zehn Services `OK`; Journalfingerprint 158 vor und nach der Prüfung, `failed_writes=0`.
- Crypto: 3 Analysen; Stock: 5 Analysen. Telegram: `enabled=false`, `dry_run=true`, `messages_sent=0`.
- Storage: 114/114 Dateien in 2,275 Sekunden, `last_error=null`; `DEGRADED` beruht weiterhin auf bekannten Datenwarnungen.
- Listener PID 10664 auf `127.0.0.1:8000`; Runtime-stdout und -stderr blieben leer.

### Bekannte Fehler

- Der kontrollierte Neustart benötigte knapp über 180 Sekunden bis zur Listener-Erkennung; Prozess und Dienst liefen danach sauber. Startdauer weiter beobachten, aber nicht mit einem zweiten Parallelstart umgehen.
- Die übrigen offenen Punkte aus `docs/KNOWN_PROBLEMS.md` bleiben unverändert.

### Getroffene Architekturentscheidungen

- Keine Architekturänderung: ausschließlich Lesesemantik der Zeitdifferenzberechnung.
- Fehlender Offset bedeutet für historische PandorickKi-Werte UTC; bewusst vorhandene Offsets werden nicht vereinheitlicht oder verworfen.
- Persistierte Originalwerte bleiben unverändert. Es gibt keine Datenmigration.

### Nicht abgeschlossene Punkte

- Implementierung und erste Dokumentation sind als Commit `a2a139f` veröffentlicht.
- Draft-PR #8: `https://github.com/cRioshy/Pando/pull/8`, Basis `agent/add-service-error-journal`; Draft und ungemergt.
- Die abschließende Live-Dokumentation ist Bestandteil dieses Handovers.
- Kein Draft-PR darf gemergt werden.

### Exakter nächster sinnvoller Arbeitsschritt

Als nächsten eigenen Schritt den Feld-/Kompatibilitätsvertrag für kompakte Event-Payloads erstellen: tatsächliche Leser von `raw_result` und verschachtelten Payloads vollständig inventarisieren, benötigte Felder und Schemaversion festlegen und Kompatibilitätstests schreiben. Noch keine Payloads entfernen, bevor dieser Vertrag geprüft ist.

---

## Aktuelle Aufgabe: Begrenztes Service-Fehlerjournal implementieren

### Datum und Uhrzeit

1. August 2026, 16:31 Uhr, Europe/Berlin (`+02:00`)

### Ziel der Aufgabe

Nach der erfolgreichen Scanner-Veröffentlichung ein dauerhaftes, größenbegrenztes und secret-gefiltertes Fehlerjournal ergänzen. Erste und letzte konkrete Servicefehler sollen rekonstruierbar bleiben, ohne vollständige Event-Payloads, externe Antworten oder Zugangsdaten zu persistieren. Keine realen Trades, keine Orderausführung und kein Telegram-Liveversand.

### Durchgeführte Arbeiten

- Die vier Dokumentationsänderungen der kontrollierten Neustartprüfung als Commit `f3ed01c` auf `agent/instrument-storage-scanner` veröffentlicht und damit Draft-PR #6 aktualisiert.
- Neuen gestapelten Arbeitsbranch `agent/add-service-error-journal` von diesem Stand erstellt.
- Alle tatsächlich publizierten Fehler-Topics und verschachtelten Adapter-Payloads geprüft.
- `ServiceErrorJournal` als Wildcard-Subscriber implementiert; es akzeptiert `SYSTEM_ERROR`, `service.error` sowie Topics mit Suffix `_ERROR`.
- Eine kompakte Version-1-Projektion für Service, Stufe, Symbol, Provider, Fehlerart, Korrelation und maximal zehn Provider-Versuche implementiert; rohe Payloads werden nicht übernommen.
- Secret-Schutz für sensible Schlüsselnamen, Zuweisungen, Bearer-Werte und Query-Parameter ergänzt.
- Aktives JSONL auf 5 MiB, Archive auf vier und die atomare Erst-/Letzt-Zusammenfassung auf 500 Fingerprints begrenzt.
- Journal-Lifecycle in den Orchestrator integriert: Start vor den Adaptern, Shutdown nach den Adaptern, eigener Health-Eintrag und Journalisierung von Start-, Lauf- und Stopfehlern.
- Konfiguration, Beispielumgebung, Tests und Ist-Dokumentation aktualisiert.
- PandorickKi über den eingebauten Control-Endpunkt regulär gestoppt, mit den bisherigen sicheren Laufzeitwerten versteckt neu gestartet und mindestens zwei vollständige Produktionszyklen geprüft.
- Das Livejournal machte drei Wiederholungen eines Outcome-Tracker-Zeitstempelfehlers als einen dauerhaften Fingerprint sichtbar; als `KP-014` dokumentiert, aber in dieser Aufgabe nicht außerhalb des vereinbarten Journalumfangs verändert.
- Keine vorhandenen Runtime-, History-, Lern-, Token- oder Konfigurationsdaten gelöscht oder verändert.

### Veränderte Dateien

- `.env.example`
- `config.py`
- `jsonl_ledger.py`
- `orchestrator.py`
- `tests/test_config.py`
- `docs/CURRENT_SYSTEM_STATE.md`
- `docs/SESSION_HANDOVER.md`
- `docs/ARCHITECTURE.md`
- `docs/KNOWN_PROBLEMS.md`
- `docs/NEXT_STEPS.md`

### Neue Dateien

- `service_error_journal.py`
- `tests/test_service_error_journal.py`

### Ausgeführte Befehle

- Vorgeschriebene Übergabedokumente und betroffene Codepfade vollständig gelesen.
- `gh auth status`, `git fetch origin`, Branch-/Remote-/Status- und PR-Prüfungen.
- Expliziter Commit und Push der vorherigen Neustartdokumentation.
- `git switch -c agent/add-service-error-journal`.
- `python -m py_compile` für die geänderten Python-Module.
- Gezielte und vollständige `unittest`-Läufe.
- `git diff --check`, Scope-Prüfung und Secret-Mustersuche im Veröffentlichungsumfang.
- POST `/api/control/stop`, Runtime-Preflight, versteckter Neustart und read-only API-Prüfungen auf Health, Status, Storage und Journaldateien.

### Ausgeführte Tests

- `python -m unittest tests.test_service_error_journal`
- `python -m unittest tests.test_service_error_journal tests.test_config tests.test_parallel_orchestrator tests.test_orchestrator_stock`
- `python -m unittest discover -s tests`

### Tatsächliche Testergebnisse

- Neue Journaltests: 5/5 bestanden in 0,350 Sekunden.
- Gezielter Journal-/Config-/Orchestratorlauf: 17/17 bestanden in 5,567 Sekunden.
- Vollständige Suite: 210/210 bestanden in 43,191 Sekunden.
- `git diff --check`: keine Whitespace-Fehler; ausschließlich erwartete Git-Hinweise zur künftigen LF-/CRLF-Normalisierung.
- Secret-Mustersuche: keine echten Zugangsdaten im Veröffentlichungsumfang gefunden; vorkommende Secret-Texte sind ausschließlich Platzhalter, Filterregeln und Testwerte.
- Live nach mindestens zwei Zyklen: Plattform und alle zehn Services `OK`; Journal `OK`, 3 Ereignisse, 1 Fingerprint, 0 Schreibfehler.
- Crypto: 3 aktuelle Analysen; Stock: 5 Analysen. Telegram: `enabled=false`, `dry_run=true`, `messages_sent=0`.
- Storage: 110/110 Dateien in 2,865 Sekunden, 71,81 % kumulativer JSONL-Fortschritt, `last_error=null`; `DEGRADED` wegen der bekannten Datenwarnungen.
- Listener PID 6384 auf `127.0.0.1:8000`; Runtime-stdout und -stderr blieben leer.

### Bekannte Fehler

- Der synchrone EventBus bleibt ohne Backpressure (`KP-003`). Das Journal schreibt nur bei Fehlern und fängt eigene Fehler ab, kann den Publisher bei langsamem Datenträger aber kurz blockieren.
- `KP-014`: Der Outcome Tracker subtrahiert bei älteren offenen Trades offset-naive von neuen UTC-Zeitstempeln. Drei Livevorkommen wurden journalisiert; Zyklus-Health meldet trotzdem `OK`.
- WebSocket-Reconnect (`KP-002`), verzögerter Web-Stop (`KP-013`) und die übrigen offenen Punkte in `docs/KNOWN_PROBLEMS.md` bleiben bestehen.
- Die DeprecationWarnings zu `datetime.utcnow()` stammen weiterhin aus dem externen Legacy-Crypto-Projekt und wurden in dieser Aufgabe nicht verändert.

### Getroffene Architekturentscheidungen

- Keine vollständigen oder beliebigen Events persistieren; ausschließlich ein enger, versionierter Fehlervertrag.
- Secret-Filterung findet vor jedem Schreibvorgang statt. Provider-Antwortkörper und `raw_result` sind nicht Teil der Projektion.
- Der Journalbestand ist bewusst begrenzt. Nur diese neu eingeführten Journalarchive werden nach der konfigurierten Grenze entfernt; vorhandene Projekt-History bleibt unangetastet.
- Journalfehler dürfen Publisher niemals abbrechen und werden stattdessen als eigener Service-Health sichtbar.
- Der vorhandene synchrone EventBus wird in diesem Schritt nicht grundsätzlich umgebaut.

### Nicht abgeschlossene Punkte

- Commit `8a0a78d` wurde auf `origin/agent/add-service-error-journal` veröffentlicht.
- Gestapelter Draft-PR #7 gegen `agent/instrument-storage-scanner` wurde erstellt: `https://github.com/cRioshy/Pando/pull/7`.
- Die Liveprüfung ist abgeschlossen und in diesem Handover dokumentiert.
- Draft-PRs dürfen nicht gemergt werden.

### Exakter nächster sinnvoller Arbeitsschritt

`KP-014` als kleinen eigenen Fix bearbeiten: naive historische Zeitstempel in `_duration_seconds()` rückwärtskompatibel als UTC behandeln, gemischte Zeitstempelvarianten und Health-Projektion testen, vorhandene History unverändert lassen. Erst danach mit dem Feld-/Kompatibilitätsvertrag für kompakte Event-Payloads fortfahren.

---

## Aktuelle Aufgabe: PandorickKi kontrolliert neu starten und live prüfen

### Datum und Uhrzeit

1. August 2026, 15:38 Uhr, Europe/Berlin (`+02:00`)

### Ziel der Aufgabe

Den laufenden PandorickKi-Webdienst nach der Scanner-Veröffentlichung kontrolliert neu starten und anhand von Prozess, API, zwei Produktionszyklen, Storage-Scan und sichtbarem Control Center prüfen, ob das Gesamtsystem sauber läuft. Keine Codeänderung, keine realen Trades und kein Telegram-Liveversand.

### Durchgeführte Arbeiten

- Übergabedokumentation und tatsächliche Start-/Lebenszykluspfade vollständig geprüft.
- Vorherigen Webdienst eindeutig als `.venv`-Launcher PID 9708 und Listener-Kindprozess PID 16200 identifiziert.
- Vor dem Stop Gesamt-Health, Servicezustände, Crypto-/Stock-Ergebnisse und Telegram-Sicherheitszustand read-only geprüft; alle Kernservices meldeten `OK`.
- Eingebauten `/api/control/stop`-Befehl verwendet. Der Befehl wurde akzeptiert; der Prozess beendete sich nach dem laufenden Zyklusintervall ohne erzwungenen Prozessabbruch.
- Port 8000 und beide alten PIDs anschließend als beendet verifiziert.
- Projektlokalen Runtime-Preflight erfolgreich ausgeführt.
- Neuen Webdienst versteckt über die projektlokale `.venv` mit denselben sicheren Starterwerten gestartet: NeuroBrain an, Live-Crypto an, Stock-Livebetrieb, Telegram aus und Dry-Run.
- Neuen Dienst als `.venv`-Launcher PID 11884 und Listener-Kindprozess PID 9720 verifiziert.
- Zwei vollständige Crypto-/Stock-Produktionszyklen über die lokale API beobachtet.
- Produktions-Storage-Scans samt neuen Phasen-/Fortschrittsmetriken geprüft.
- Bereits geöffnetes lokales Control Center neu geladen und sichtbare System-, Service-, Crypto-, Stock-, Telegram- und Storage-Zustände geprüft.
- Browserkonsole auf Warnungen/Fehler geprüft; keine Einträge gefunden.

### Veränderte Dateien

- `docs/CURRENT_SYSTEM_STATE.md`
- `docs/SESSION_HANDOVER.md`
- `docs/KNOWN_PROBLEMS.md`
- `docs/NEXT_STEPS.md`

### Neue Dateien

- Keine versionierten Dateien.
- Ignorierte Laufzeitlogs: `runtime_logs/web_restart_2026-08-01_15-34-40_stdout.log` und `runtime_logs/web_restart_2026-08-01_15-34-40_stderr.log`; beide blieben während der Prüfung leer.

### Ausgeführte Befehle

- Vollständiges Lesen von `AGENTS.md` und den fünf vorgeschriebenen Übergabedokumenten.
- `git status -sb`, Prüfung von `start_pandorick_web.bat`, `main.py`, `orchestrator.py` und Control-Routen.
- `netstat -ano`, `Get-Process` und nach Freigabe `Get-CimInstance Win32_Process` zur eindeutigen Prozesszuordnung.
- Read-only `Invoke-RestMethod`-Abrufe auf `/api/health`, `/api/status` und `/api/statistics/storage`.
- `Invoke-RestMethod -Method Post` auf `/api/control/stop`.
- `\.venv\Scripts\python.exe scripts\runtime_preflight.py`.
- Versteckter `Start-Process` mit `main.py --headless --web` und expliziten sicheren Umgebungswerten.
- Browser-Neuladen, DOM-Prüfung und Konsolenlogprüfung des lokalen Control Centers.

### Ausgeführte Tests

- Runtime-Preflight.
- Kontrollierter Stop samt Prozess-/Portprüfung.
- Start- und Listenerprüfung des neuen Dienstes.
- Zwei vollständige Produktionszyklen über die lokale API.
- Health-, Service-, Crypto-, Stock-, Telegram-, WebSocket- und Storage-Prüfung.
- Sichtprüfung der gerenderten Control-Center-Daten und Browserkonsole.

### Tatsächliche Testergebnisse

- Preflight: `OK`, Python 3.12.13 aus der projektlokalen `.venv`.
- Alter Dienst: Stop um 13:32:33 UTC akzeptiert; reguläre Beendigung nach dem bis zu 60 Sekunden langen Zyklus-Sleep, kein erzwungener Stop nötig.
- Neuer Dienst: Launcher PID 11884, Listener PID 9720, Port `127.0.0.1:8000` aktiv.
- Nach zwei Zyklen: Plattform `OK`; `crypto`, `brain`, `decision_core`, `outcome_tracker`, `neurobrain_receiver`, `crypto_trade_tracker`, `stock`, `telegram` und `control_center` jeweils `OK`.
- Crypto: 2 Zyklen, je 3 Ergebnisse, `healthy=true`, `last_error=null`; aktuelle Preise für BTCUSDT, ETHUSDT und XRPUSDT.
- Stock: 2 Zyklen, je 5 Ergebnisse, Status `OK`.
- Neue Sitzung: `error_count=0`.
- Telegram: `enabled=false`, `dry_run=true`, `messages_sent=0`.
- WebSocket: ein aktiver Browserclient; Control Center zeigt Health `OK`, drei Cryptozeilen, fünf Stockzeilen und alle Services `OK`.
- Storage: `DEGRADED`, aber Scan technisch erfolgreich mit 106/106 Dateien, 2,416 Sekunden, `last_error=null`, `totals_status=VERIFIED`; JSONL-Fortschritt 9,20 %, 15/59 vollständig, ungefähr 84 Restläufe.
- Browserkonsole: 0 Warnungen und 0 Fehler.
- Laufzeit-stdout/-stderr: beide 0 Byte während der Prüfung.
- Abschlussprüfung nach fünf laufenden Zyklen: Plattform und Crypto weiterhin `OK`, `error_count=0`, Telegram weiterhin aus/Dry-Run und Listener PID 9720 aktiv.

### Bekannte Fehler

- Der Web-Stop prüft `stop_requested` erst nach dem nicht unterbrechbaren Zyklus-Sleep; die kontrollierte Beendigung kann deshalb bis zu ungefähr 60 Sekunden dauern (`KP-013`).
- Storage bleibt während der inkrementellen Nachindexierung sowie wegen der zwei bekannten beschädigten Stock-JSON-Dateien `DEGRADED`; es gab keinen Timeout oder Scannerfehler.
- Die übrigen offenen Punkte aus `docs/KNOWN_PROBLEMS.md` bleiben unverändert.

### Getroffene Architekturentscheidungen

- Keine Produktarchitektur oder kein Code wurde verändert.
- Für den Shutdown wurde zuerst ausschließlich der eingebaute Control-Endpunkt verwendet; nach dessen verzögerter, aber regulärer Beendigung war kein harter Prozessabbruch erforderlich.
- Der Neustart verwendet exakt die projektlokale `.venv` und die Sicherheitswerte des Webstarters; reale Orders bleiben unmöglich und Telegram bleibt aus/Dry-Run.

### Nicht abgeschlossene Punkte

- Die vier Dokumentationsänderungen sind lokal noch nicht committed oder gepusht.
- Der Dienst läuft weiter; Launcher PID 11884 und Listener PID 9720 gelten nur für diese konkrete Sitzung und müssen in einer späteren Aufgabe neu ermittelt werden.
- Das dauerhaft begrenzte Service-Fehlerjournal bleibt der nächste Implementierungsschritt.

### Exakter nächster sinnvoller Arbeitsschritt

Vor jeder Änderung Übergabe, Arbeitsbaum und laufenden Dienst erneut prüfen. Danach das rotierende, größenbegrenzte und secret-gefilterte Service-Fehlerjournal als eigene Aufgabe spezifizieren und implementieren. Keine vollständigen Provider-Antworten oder Tokens persistieren; Telegram deaktiviert beziehungsweise im Dry-Run lassen. Die verzögerte Stop-Semantik erst im später geplanten UI-/Lebenszyklus-Schritt ändern.

## Aktuelle Aufgabe: Storage-Scanner instrumentieren und reparieren

### Datum und Uhrzeit

1. August 2026, 13:20 Uhr, Europe/Berlin (`+02:00`)

### Ziel der Aufgabe

Den realen Storage-Scanner ohne Löschung oder Veränderung vorhandener History instrumentieren, seinen tatsächlichen Engpass messen, das inkrementelle Budget belastbar einstellen und den kumulativen Fortschritt im Control Center sichtbar machen. Keine Trading- oder Telegram-Kette verändern.

### Durchgeführte Arbeiten

- Die vorgeschriebene Übergabedokumentation, den tatsächlichen Scanner, seine Konfiguration, vorhandene Tests und UI-Verbraucher geprüft.
- Branch `agent/instrument-storage-scanner` auf Basis von `agent/fix-storage-physical-totals` erstellt.
- Zielermittlung, Pfadauflösung, Metadaten, Fingerprint, Dateiverarbeitung, Index- und Cachepersistenz einzeln instrumentiert.
- Rekursive Dateiermittlung mit kooperativen Abbruch-/Timeoutprüfungen versehen.
- Kumulativen JSONL-Fortschritt aus persistentem Index und aktuellem Dateibestand ergänzt: Dateien, Bytes, Prozent, Restbytes, geschätzte Restläufe und Restzeit.
- Control Center um JSONL-Fortschritt, Restschätzung und langsamste Scanphase erweitert.
- Zwei Realmessungen ausschließlich schreibgeschützt ausgeführt, indem Index- und Cachepersistenz im Diagnoseprozess deaktiviert wurden.
- Erst nach den Messungen das Standardbudget von 256 KiB auf 64 MiB pro Scan erhöht.
- Zwei vorhandene fehlerhafte Stock-JSON-Dateien identifiziert, aber weder repariert noch gelöscht.
- Übergabedokumentation an die tatsächliche Umsetzung und Messwerte angepasst.

### Veränderte Dateien

- `config.py`
- `web/statistics_service.py`
- `web/static/control_center.js`
- `web/static/control_center.html`
- `tests/test_statistics_and_storage.py`
- `tests/test_web_control_center.py`
- `docs/CURRENT_SYSTEM_STATE.md`
- `docs/SESSION_HANDOVER.md`
- `docs/ARCHITECTURE.md`
- `docs/KNOWN_PROBLEMS.md`
- `docs/NEXT_STEPS.md`

### Neue Dateien

- Keine.

### Ausgeführte Befehle

- `git status --short`
- `git diff --stat`
- `git branch --show-current`
- `rg`- und `Get-Content`-Prüfungen für Scanner, Konfiguration, Tests und Dokumentation.
- `\.venv\Scripts\python.exe -m unittest tests.test_statistics_and_storage tests.test_web_control_center`
- Schreibgeschützter Ist-Scan mit `StorageStatisticsService(PlatformConfig.from_env())`, wobei `_persist_index` und `_atomic_write_json` im Diagnoseprozess als No-op ersetzt waren.
- Derselbe schreibgeschützte Benchmark mit temporär im Prozess gesetztem 8-MiB-Budget.
- Derselbe schreibgeschützte Benchmark mit temporär im Prozess gesetztem 64-MiB-Budget.
- `git diff --check`
- `\.venv\Scripts\python.exe -m unittest discover -s tests`

### Ausgeführte Tests

- Neuer Regressionstest für Phasenmetriken und über zwei Läufe ansteigenden kumulativen JSONL-Fortschritt.
- Gezielte Storage-/Webtests.
- Vollständige Unittest-Suite.
- Drei schreibgeschützte Scanner-Messungen am realen Bestand: aktuelles Budget, 8 MiB und 64 MiB.

### Tatsächliche Testergebnisse

- Neuer isolierter Scanner-Test: 1/1 bestanden in 0,090 Sekunden.
- Gezielte Storage-/Webtests nach Abschluss: 39/39 bestanden in 10,349 Sekunden.
- Gesamtsuite: 204/204 bestanden in 51,063 Sekunden.
- Ist-Messung mit altem Budget: 105 physische Dateien, 58 JSONL-Dateien, rund 5,80 GB JSONL, 5,69 % indexiert, 1,084 Sekunden Gesamtdauer.
- 8-MiB-Benchmark: rund 9,25 MB untersucht, 0,667 Sekunden Gesamtdauer.
- 64-MiB-Benchmark: rund 67,97 MB untersucht, 2,135 Sekunden Gesamtdauer; Dateiverarbeitung war mit 1,878105 Sekunden die langsamste Phase.
- Aus rund 5,46 GB Restbestand ergaben sich beim neuen Budget ungefähr 82 weitere Scanläufe beziehungsweise 82 Minuten bei unverändertem Bestand und 60-Sekunden-Intervall.
- Keine Diagnose hat Index, Cache, History, Lern- oder Tradingdaten geschrieben.

### Bekannte Fehler

- `stock_patterns.json` enthält einen vorhandenen JSON-Syntaxfehler bei Zeile 249448; die Datei wurde nicht verändert.
- `stock_patterns.before_json_repair_20260710_224237.json` enthält einen vorhandenen JSON-Syntaxfehler bei Zeile 146372; die Datei wurde nicht verändert.
- Diese beiden Dateien halten den Storage-Gesamtstatus auf `DEGRADED`, obwohl der Scannerlauf technisch abgeschlossen wird.
- Der neue 64-MiB-Standard muss nach Neustart im Dauerbetrieb weiter beobachtet werden; der Realbenchmark blieb deutlich unter dem Timeout.
- Die übrigen offenen Punkte aus `docs/KNOWN_PROBLEMS.md`, insbesondere das fehlende Service-Fehlerjournal, bleiben bestehen.

### Getroffene Architekturentscheidungen

- Das bestehende persistente Offsetmodell bleibt erhalten; vorhandene History wird weder umgeschrieben noch neu formatiert.
- Fortschritt wird aus aktuellem physischem JSONL-Bestand und persistentem Index berechnet, nicht aus flüchtigen Dateizählern eines einzelnen Laufs.
- Restzeit ist ausdrücklich eine Schätzung aus Restbytes, konfiguriertem Bytebudget und Scanintervall; wachsende Dateien können sie verändern.
- Das globale Budget bleibt konfigurierbar über `PANDORICKKI_STORAGE_SCAN_BYTE_BUDGET`; nur der sichere Standard wurde auf Grundlage des Realbenchmarks erhöht.
- Scannerphasen werden beobachtbar gemacht, ohne neue Datenbank, neues Ledger oder zusätzliche Runtime-History einzuführen.

### Nicht abgeschlossene Punkte

- Der laufende Webprozess muss nach Veröffentlichung kontrolliert neu gestartet werden, bevor die neuen Metriken in dessen UI erscheinen; dieser Neustart gehört nicht zur aktuellen Codeaufgabe.
- Das dauerhafte, begrenzte Service-Fehlerjournal ist der nächste Implementierungsschritt.

### Veröffentlichung

- Implementierungs-/Dokumentationscommit: `cc6e92d` (`Instrument storage scanner progress`).
- Remote-Branch: `origin/agent/instrument-storage-scanner`.
- Gestapelter Draft-PR: #6, `https://github.com/cRioshy/Pando/pull/6`.
- PR-Basis: `agent/fix-storage-physical-totals`.
- Draft-PR #6 wurde nicht gemergt; die vorherigen Draft-PRs #3, #4 und #5 bleiben ebenfalls ungemergt.

### Exakter nächster sinnvoller Arbeitsschritt

Vor jeder neuen Änderung Branch-, PR- und Übergabestand erneut prüfen. Danach als eigene Aufgabe das rotierende, größenbegrenzte und secret-gefilterte Service-Fehlerjournal spezifizieren und implementieren. Keine vollständigen Provider-Antworten, Tokens oder unbegrenzten Logs persistieren; Telegram deaktiviert beziehungsweise im Dry-Run lassen.

## Aktuelle Aufgabe: Storage-Ziele und physische Gesamtwerte deduplizieren

### Datum und Uhrzeit

1. August 2026, 13:00 Uhr, Europe/Berlin (`+02:00`)

### Ziel der Aufgabe

Überlappende Storage-Ziele so korrigieren, dass logische Kategorien getrennt sichtbar bleiben, jede physische Datei aber nur einmal gescannt und in physischen Gesamtwerten nur einmal gezählt wird. Keine Runtime-, History- oder Lerndaten löschen oder inhaltlich verändern.

### Durchgeführte Arbeiten

- Übergabedokumentation, Branchbasis, Scanner-Datenmodell, Web-API, Rick-API und Control-Center-Verbraucher geprüft.
- Neuen Branch `agent/fix-storage-physical-totals` auf Basis des veröffentlichten Storage-Shutdown-Branches erstellt.
- Regressionstest mit `platform_data`, `brain_events` und `shared_state` ergänzt: vier logische Dateiverweise müssen zwei physischen Dateien entsprechen und `_scan_file()` darf nur zweimal laufen.
- `_scan()` um einen gemeinsamen Dateiergebnis-Cache je aufgelöstem physischen Pfad ergänzt.
- Logische Kategorien und deren relative Pfade bleiben erhalten; Fortschritt, Fehlerzähler und JSONL-Bytebudget zählen physische Dateien nur einmal.
- `total_*` auf physisch eindeutige Werte umgestellt und explizite Felder `physical_total_*`, `logical_total_*` sowie `overlapping_file_references` ergänzt.
- Vorhandene alte Cachedateien ohne neue Summenfelder werden als `LEGACY_CACHE` markiert; ihre bisherigen Werte werden nicht als physisch verifiziert behauptet.
- Statistik-API und Rick-API um die neuen Summenfelder erweitert.
- Control Center zeigt eine eigene Zusammenfassung für physisch eindeutige Werte, logische Kategorieverweise und Überlappungen; Cache-Buster aktualisiert.
- Gezielte und vollständige Tests erfolgreich ausgeführt.
- Änderung als Commit `a15770bf46749f3c7585edf58bed4753cdca591e` auf `origin/agent/fix-storage-physical-totals` veröffentlicht.
- Gestapelten Draft-PR #5 gegen `agent/fix-storage-worker-shutdown` erstellt: `https://github.com/cRioshy/Pando/pull/5`. PR #3 und PR #4 blieben unverändert und Draft.

### Veränderte Dateien

- `web/statistics_service.py`
- `web/api.py`
- `web/rick_api_service.py`
- `web/static/control_center.html`
- `web/static/control_center.js`
- `tests/test_statistics_and_storage.py`
- `tests/test_web_control_center.py`
- `docs/CURRENT_SYSTEM_STATE.md`
- `docs/SESSION_HANDOVER.md`
- `docs/ARCHITECTURE.md`
- `docs/KNOWN_PROBLEMS.md`
- `docs/NEXT_STEPS.md`

### Neue Dateien

- Keine.

### Ausgeführte Befehle

- `git status -sb`, relevante `rg`- und Codeprüfungen.
- `git switch -c agent/fix-storage-physical-totals`
- `\.venv\Scripts\python.exe -m unittest tests.test_statistics_and_storage.StatisticsAndStorageTest.test_overlapping_targets_keep_logical_categories_but_dedupe_physical_totals`
- `\.venv\Scripts\python.exe -m unittest tests.test_statistics_and_storage`
- `\.venv\Scripts\python.exe -m unittest tests.test_statistics_and_storage tests.test_web_control_center tests.test_rick_read_only_api`
- `\.venv\Scripts\python.exe -m unittest discover -s tests`
- `git commit -m "Deduplicate storage physical totals"`
- `git push -u origin agent/fix-storage-physical-totals`
- `gh pr create --repo cRioshy/Pando --base agent/fix-storage-worker-shutdown --head agent/fix-storage-physical-totals --draft ...`

### Ausgeführte Tests und tatsächliche Ergebnisse

- Neuer Überlappungstest vor dem Fix: erwartungsgemäß mit fehlenden getrennten Summenfeldern fehlgeschlagen.
- Neuer Überlappungstest nach dem Fix: 1/1 bestanden in 0,040 Sekunden; vier logische Referenzen, zwei physische Dateien, zwei tatsächliche `_scan_file()`-Aufrufe.
- Storage-Modul nach Backend-Fix: 28/28 bestanden in 3,289 Sekunden.
- Gezielter Storage-/Web-/Rick-API-Lauf einschließlich Legacy-Cache-Test: 44/44 bestanden in 12,489 Sekunden.
- Gesamtsuite: 203/203 bestanden in 36,854 Sekunden.
- Bekannte externe DeprecationWarnings für `datetime.utcnow()` blieben ohne Testauswirkung.

### Bekannte Fehler

- Der reale Storage-Scan kann das konfigurierte Zeitlimit weiterhin überschreiten (`KP-001`).
- Ein neuer vollständiger Produktionsscan wurde in dieser Aufgabe bewusst nicht erzwungen; deshalb werden keine neuen realen physischen Größenwerte erfunden oder dokumentiert.
- Weitere offene Probleme aus `docs/KNOWN_PROBLEMS.md` bleiben unverändert.

### Getroffene Architekturentscheidungen

- Logische Kategoriezugehörigkeit und physische Dateieindeutigkeit sind getrennte Konzepte.
- Der aufgelöste physische Pfad ist innerhalb eines Scans der Deduplizierungsschlüssel; Kategorieansichten verwenden Kopien desselben Scanergebnisses mit eigenem relativen Pfad.
- Bestehende `total_*`-Felder stehen nach einem verifizierten Scan für physisch eindeutige Werte; explizite physische und logische Felder verhindern Mehrdeutigkeit.
- Alte Caches werden nicht stillschweigend als neue Wahrheit umgedeutet.

### Nicht abgeschlossene Punkte

- Draft-PR #5 wurde ausdrücklich nicht gemergt.
- Scanner-Phasenmessung, realistisches inkrementelles Budget und Fortschrittsreparatur gehören bewusst erst zu Schritt 4.

### Exakter nächster sinnvoller Arbeitsschritt

Vor jeder weiteren Änderung Branch- und PR-Status erneut prüfen. Danach Laufzeiten für Dateiermittlung, Pfadauflösung, Metadaten/Fingerprint, Dateiartbehandlung sowie Cache-/Index-Schreiben instrumentieren und mit dem realen Bestand ohne Datenlöschung messen.

---

## Vorherige Aufgabe: Storage-Worker-Shutdown deterministisch reparieren

### Datum und Uhrzeit

1. August 2026, 12:48 Uhr, Europe/Berlin (`+02:00`)

### Ziel der Aufgabe

Die bestätigte Race in `StorageStatisticsService.close()` reproduzierbar machen und so beheben, dass nach Rückkehr von `close()` kein Hintergrundworker oder synchroner Refresh mehr Cache beziehungsweise Index schreiben kann. Keine Runtime-, History- oder Lerndaten löschen und keine Trading-/Telegram-Konfiguration verändern.

### Durchgeführte Arbeiten

- Übergabedokumentation, tatsächlichen Storage-Code, vorhandene Tests und Git-Stand geprüft.
- Neuen Branch `agent/fix-storage-worker-shutdown` vom veröffentlichten Crypto-Stand erstellt; Draft-PR #3 blieb unverändert.
- Deterministischen Regressionstest ergänzt, der `_atomic_write_json()` während eines Hintergrundscans blockiert und `close()` parallel aufruft.
- Vor dem Fix reproduziert, dass `close()` nach einer Sekunde zurückkehrte, obwohl der Worker weiterhin schreiben konnte; die Testbereinigung scheiterte zusätzlich mit dem bekannten `WinError 145`.
- Einen Lebenszyklus-Lock und dauerhaften `_closed`-Zustand ergänzt.
- `start_scan()` lehnt nach `close()` neue Scans mit Status `CLOSED` ab; `refresh()` startet nach dem Schließen keinen synchronen Scan mehr.
- `close()` signalisiert Abbruch, wartet vollständig auf den aktiven Worker und verwendet die Scan-Sperre als Barriere für gleichzeitig laufende synchrone Refreshes.
- Worker-Referenz wird nach vollständigem Ende bereinigt; wiederholtes `close()` ist sicher.
- Isolierten Regressionstest, Storage-Modul, Storage-/Webintegration und vollständige Testsuite erfolgreich ausgeführt.
- Fix als Commit `610b4a9cd7555f0cd8c5989256482799059547e2` auf `origin/agent/fix-storage-worker-shutdown` veröffentlicht.
- Gestapelten Draft-PR #4 gegen `agent/add-market-feature-engine` erstellt: `https://github.com/cRioshy/Pando/pull/4`. PR #3 gegen `main` blieb unverändert und Draft.

### Veränderte Dateien

- `web/statistics_service.py`
- `tests/test_statistics_and_storage.py`
- `docs/CURRENT_SYSTEM_STATE.md`
- `docs/SESSION_HANDOVER.md`
- `docs/ARCHITECTURE.md`
- `docs/KNOWN_PROBLEMS.md`
- `docs/NEXT_STEPS.md`

### Neue Dateien

- Keine.

### Ausgeführte Befehle

- `git status -sb`, `git log -3 --oneline` und relevante `rg`-/Codeprüfungen.
- `git switch -c agent/fix-storage-worker-shutdown`
- `\.venv\Scripts\python.exe -m unittest tests.test_statistics_and_storage.StatisticsAndStorageTest.test_close_waits_until_background_worker_can_no_longer_write`
- `\.venv\Scripts\python.exe -m unittest tests.test_statistics_and_storage`
- `\.venv\Scripts\python.exe -m unittest tests.test_statistics_and_storage tests.test_web_control_center`
- `\.venv\Scripts\python.exe -m unittest discover -s tests`
- `git commit -m "Fix storage worker shutdown"`
- `git push -u origin agent/fix-storage-worker-shutdown`
- `gh pr create --repo cRioshy/Pando --base agent/add-market-feature-engine --head agent/fix-storage-worker-shutdown --draft ...`

### Ausgeführte Tests und tatsächliche Ergebnisse

- Neuer Regressionstest vor dem Fix: erwartungsgemäß fehlgeschlagen; `close()` kehrte bei blockiertem Worker zu früh zurück, anschließend `WinError 145`.
- Neuer Regressionstest nach dem Fix: 1/1 bestanden in 1,245 Sekunden.
- Storage-/Statistikmodul: 27/27 bestanden in 3,220 Sekunden.
- Storage-/Webintegration: 36/36 bestanden in 9,402 Sekunden.
- Gesamtsuite: 201/201 bestanden in 37,859 Sekunden.
- Bekannte externe DeprecationWarnings für `datetime.utcnow()` blieben ohne Testauswirkung.

### Bekannte Fehler

- Storage-Scans überschreiten am realen Datenbestand weiterhin teilweise das konfigurierte Timeout (`KP-001`).
- Überlappende Storage-Ziele können physische Gesamtsummen weiterhin doppelt zählen; dies ist der nächste geplante Schritt.
- Weitere offene Probleme aus `docs/KNOWN_PROBLEMS.md` bleiben unverändert.

### Getroffene Architekturentscheidungen

- `close()` besitzt jetzt einen starken Abschlussvertrag und darf zugunsten korrekter Besitz-/Dateisemantik auf den kooperativ abbrechenden Scanner warten.
- Ein dauerhafter Closed-Zustand verhindert Neustarts desselben Serviceobjekts nach dem Shutdown.
- Es wurde keine globale EventBus- oder Storage-Datenarchitektur verändert.

### Nicht abgeschlossene Punkte

- Draft-PR #4 wurde ausdrücklich nicht gemergt.
- Storage-Anzeige und Scanner-Performance wurden bewusst noch nicht verändert.

### Exakter nächster sinnvoller Arbeitsschritt

Vor jeder weiteren Änderung Branch- und PR-Status erneut prüfen. Danach die überlappenden Storage-Ziele analysieren und physische Gesamtsummen deduplizieren, während logische Kategorien getrennt sichtbar bleiben. Keine Runtime- oder History-Dateien löschen.

---

## Vorherige Aufgabe: Funktionierenden Crypto-Stand sichern und veröffentlichen

### Datum und Uhrzeit

1. August 2026, 12:34 Uhr, Europe/Berlin (`+02:00`)

### Ziel der Aufgabe

Den am 31. Juli 2026 live reparierten Crypto-Stand vor allen weiteren Architekturarbeiten vollständig sichern, den Commitumfang auf Secrets und Runtime-Daten prüfen, Tests und Livebetrieb erneut verifizieren und ausschließlich den bestehenden Branch `agent/add-market-feature-engine` veröffentlichen. Kein Merge nach `main`, keine realen Trades und keine Telegram-Nachrichten.

### Durchgeführte Arbeiten

- Übergabedokumentation, Arbeitsbaum, Branch und Remote erneut geprüft.
- Alle 17 vorgesehenen Commitdateien inhaltlich abgegrenzt; keine Runtime-Verzeichnisse und keine erkannten Secrets im Commitumfang.
- Ersten PowerShell-Backupversuch wegen fehlendem `.git/HEAD` in der ZIP-Prüfung verworfen und eindeutig als `FAILED` markiert.
- Korrigiertes BEFORE-Backup über kontrolliertes Staging erstellt; im Staging das Windows-`Hidden`-Attribut von `.git` entfernt, damit `Compress-Archive` die Git-Metadaten einschließt.
- Gültiges Archiv `C:\Users\Admin\Desktop\PandorickBackUp_2026-08-01_12-20-18_BEFORE.zip` erstellt und mit .NET geöffnet, Pflichtinhalte geprüft sowie vollständig testextrahiert.
- Runtime-Preflight, gezielte Crypto-Tests und vollständige Testsuite erfolgreich ausgeführt.
- Zwei kontrollierte Produktionszyklen mit öffentlichen Marktdaten ausgeführt. Gesamt-Health und alle Services meldeten `OK`; Telegram blieb deaktiviert und im Dry-Run.
- GitHub-Anmeldung für `cRioshy` außerhalb der eingeschränkten Netzwerkumgebung erfolgreich verifiziert.
- Crypto-Reparatur als Commit `b0379c31fb5a157cbaa0c2e34eeb959afb7c5862` erstellt und auf `origin/agent/add-market-feature-engine` gepusht.
- Festgestellt, dass die früher dokumentierten PRs #1 und #2 bereits gemergt waren; für den neuen Stand deshalb Draft-PR #3 gegen `main` erstellt: `https://github.com/cRioshy/Pando/pull/3`.

### Veränderte Dateien

- `adapters/crypto_adapter.py`
- `orchestrator.py`
- `requirements.txt`
- `start_headless.bat`
- `start_live.bat`
- `start_once.bat`
- `start_pandorick_web.bat`
- `tests/test_crypto_adapter.py`
- `docs/CURRENT_SYSTEM_STATE.md`
- `docs/SESSION_HANDOVER.md`
- `docs/ARCHITECTURE.md`
- `docs/KNOWN_PROBLEMS.md`
- `docs/NEXT_STEPS.md`

### Neue Dateien

- `adapters/crypto_market_data_service.py`
- `tests/test_crypto_market_data_service.py`
- `setup_local_env.bat`
- `scripts/runtime_preflight.py`

### Ausgeführte Befehle

- `git status --short`, `git diff --check`, `git diff --stat` und inhaltliche Diffprüfung.
- Kontrollierte rekursive Staging-Kopie mit `robocopy`, anschließend `Compress-Archive`.
- ZIP-Prüfung mit `[System.IO.Compression.ZipFile]::OpenRead()` und vollständige Testextraktion mit `Expand-Archive`.
- `\.venv\Scripts\python.exe scripts\runtime_preflight.py`
- `\.venv\Scripts\python.exe -m unittest tests.test_crypto_market_data_service tests.test_crypto_adapter`
- `\.venv\Scripts\python.exe -m unittest discover -s tests`
- `\.venv\Scripts\python.exe main.py --headless --cycles 2 --interval 1`
- `gh auth status`
- `git fetch origin`
- Explizites `git add` der 17 geprüften Dateien.
- `git commit -m "Restore resilient crypto market data"`
- `git push -u origin agent/add-market-feature-engine`
- `gh pr list --repo cRioshy/Pando --head agent/add-market-feature-engine --state all ...`
- `gh pr create --repo cRioshy/Pando --base main --head agent/add-market-feature-engine --draft ...`

### Ausgeführte Tests und tatsächliche Ergebnisse

- Backup: 1.144.625.985 Bytes, 602 ZIP-Einträge, `.git`, `docs` und `tests` enthalten; vollständige Testextraktion `OK`.
- Secret-/Scope-Prüfung: 17 Commitkandidaten, 0 Runtime-Dateien, 0 Treffer der geprüften Secret-Muster, `git diff --check` ohne Fehler.
- Runtime-Preflight: `OK`, Python 3.12.13 aus der projektlokalen `.venv`.
- Gezielte Crypto-Tests: 10/10 bestanden in 0,446 Sekunden.
- Gesamttests: 200/200 bestanden in 40,828 Sekunden.
- Live-Verifikation: zwei Produktionszyklen, Health `OK`; `crypto`, `brain`, `decision_core`, `outcome_tracker`, `neurobrain_receiver`, `crypto_trade_tracker`, `stock`, `telegram` und `control_center` jeweils `OK`.
- Telegram-Schutz: `PANDORICKKI_TELEGRAM_ENABLED=0`, `PANDORICKKI_TELEGRAM_DRY_RUN=1`.
- Veröffentlichung: Commit `b0379c31fb5a157cbaa0c2e34eeb959afb7c5862` erfolgreich gepusht; Draft-PR #3 offen gegen `main`.

### Bekannte Fehler

- Die offenen Storage-, EventBus-, WebSocket-, Fehlerjournal-, Learning- und UI-Probleme aus `docs/KNOWN_PROBLEMS.md` bestehen unverändert.
- Die externe Legacy-Crypto-Pipeline erzeugt unter Python 3.12 DeprecationWarnings für `datetime.utcnow()`; dies beeinträchtigte die Tests und Livezyklen nicht.
- Ein versteckter Hintergrundstart blieb in der verwendeten Ausführungsumgebung nicht aktiv; die belastbare Live-Verifikation wurde deshalb als exakt begrenzter Vordergrundlauf durchgeführt. Das ist kein nachgewiesener PandorickKi-Codefehler.

### Getroffene Architekturentscheidungen

- Keine neue Architekturentscheidung in dieser Sicherungsaufgabe.
- Der interne Binance/Bitget-Marktdatenpfad und die projektlokale Runtime werden unverändert gesichert.
- Keine realen Orders, kein Merge nach `main`, Telegram weiterhin deaktiviert beziehungsweise Dry-Run.

### Nicht abgeschlossene Punkte

- Draft-PR #3 wurde ausdrücklich nicht gemergt.
- Der nächste Implementierungsschritt, Storage-Worker-Shutdown, wurde noch nicht begonnen.

### Exakter nächster sinnvoller Arbeitsschritt

Vor jeder Änderung den aktuellen Branch- und PR-Stand erneut prüfen. Danach den Storage-Worker-Shutdown mit einem deterministischen Regressionstest bearbeiten: Nach `StorageStatisticsService.close()` darf kein Worker mehr Cache oder Index schreiben.

---

## Vorherige Aufgabe: Crypto nach Dauerbetrieb wiederherstellen

### Datum und Uhrzeit

31. Juli 2026, 16:02 Uhr, Europe/Berlin (`+02:00`)

### Ziel der Aufgabe

Den seit dem 27. Juli ausgefallenen Crypto-Livepfad diagnostizieren, dauerhaft reparieren, vollständig testen und den laufenden PandorickKi-Dienst kontrolliert mit der Reparatur neu starten. Keine echten Trades oder Telegram-Nachrichten aktivieren.

### Durchgeführte Arbeiten

- Übergabedokumentation und tatsächlichen Code erneut geprüft.
- Laufzeit von knapp sechs Tagen, letzte Crypto-Zeitstempel, Fehlerverteilung und Serviceprojektion read-only analysiert.
- Binance Spot-Kerzen, Futures Open Interest und Funding einzeln erfolgreich geprüft.
- Reproduziert, dass der aktuelle verwaltete Python-Runtime das vom externen `market.py` verlangte Paket `requests` nicht enthält.
- `CryptoMarketDataService` als internen Standardbibliotheks-Client ergänzt: Binance-Kerzen, Bitget-Fallback, Retry, optionale Futures-Daten und sichere Diagnostik.
- CryptoAdapter vom externen `market.py` entkoppelt; externe Legacy-Analyse bleibt `persist=False` und schreibt keine Legacy-Brain-Daten.
- Zyklus-Health korrigiert: keine Ergebnisse plus Fehler ergeben `ERROR`, Teilerfolg `DEGRADED`, fehlerfreier Erfolg `OK`.
- `last_error_details` mit Stufe, Fehlertyp, Symbol und Provider-Versuchen in Adapter-Health und SharedState aufgenommen.
- Projektlokale `.venv`, `setup_local_env.bat` und Runtime-Preflight eingeführt; `tzdata 2026.3` lokal installiert.
- Alle Batch-Starter auf `.venv` und Preflight umgestellt. Webstart setzt Telegram ausdrücklich deaktiviert und Dry-Run.
- Alten Prozess PID 16028 nach exakter Pfad-/Portprüfung gestoppt. Wegen der bekannten Shutdown-Race erschien er nach 20 Sekunden noch vorhanden, war bei der unmittelbaren Folgeprüfung jedoch beendet; keine erzwungene zweite Beendigung nötig.
- Neue Version versteckt über den `.venv`-Launcher PID 8560 gestartet; der daraus gestartete Basisinterpreter PID 1884 besitzt den Listener auf Port 8000. Beide Prozesse stammen vom selben Startzeitpunkt und gehören zu derselben `.venv`-Ausführung.
- Zwei vollständige Produktionszyklen beobachtet: jeweils drei erfolgreiche Cryptoanalysen; Fehlerzähler unverändert.

### Veränderte Dateien

- `adapters/crypto_adapter.py`
- `orchestrator.py`
- `requirements.txt`
- `start_headless.bat`
- `start_live.bat`
- `start_once.bat`
- `start_pandorick_web.bat`
- `tests/test_crypto_adapter.py`
- `docs/CURRENT_SYSTEM_STATE.md`
- `docs/SESSION_HANDOVER.md`
- `docs/ARCHITECTURE.md`
- `docs/KNOWN_PROBLEMS.md`
- `docs/NEXT_STEPS.md`

### Neue Dateien

- `adapters/crypto_market_data_service.py`
- `tests/test_crypto_market_data_service.py`
- `setup_local_env.bat`
- `scripts/runtime_preflight.py`

Die lokale `.venv` und die neuen Laufzeitlogs sind absichtlich durch `.gitignore` ausgeschlossen.

### Ausgeführte Befehle

- Lokale API-Abfragen gegen `/api/v1/system/status`, `/api/services`, `/api/crypto`, `/api/events`, `/api/errors` und `/api/statistics`.
- Read-only HTTP-Prüfungen der öffentlichen Binance-Endpunkte.
- Nicht persistierender Live-Diagnoselauf des reparierten CryptoAdapters für BTCUSDT, ETHUSDT und XRPUSDT.
- `cmd /c setup_local_env.bat` und Installation aus `requirements.txt`.
- `.venv\Scripts\python.exe scripts\runtime_preflight.py`.
- Gezielte `py_compile`- und `unittest`-Läufe.
- Vollständiger `python -m unittest discover -s tests`-Lauf.
- Prozess-/Portprüfung, kontrolliertes `Stop-Process` für PID 16028 und versteckter `Start-Process` für PID 8560.
- Zwei Produktionszyklen über die lokale API überwacht und Fehlerzähler verglichen.
- `git status -sb`, `git diff --stat`, `git diff --check`.

### Ausgeführte Tests und tatsächliche Ergebnisse

- Gezielte Crypto-/Orchestrator-Tests: 16/16 bestanden in 6,499 Sekunden.
- Erster vollständiger Lauf in der neuen `.venv`: 200 Tests, drei Fehlschläge und vier Fehler wegen fehlendem `tzdata`; dies war ein echter Setupfehler und wurde nicht als grün gewertet.
- Nach Installation von `tzdata 2026.3`: betroffene Stock-/Integrationstests 11/11 bestanden in 7,196 Sekunden.
- Abschließende vollständige Suite: **200/200 bestanden in 61,863 Sekunden**.
- Nicht persistierender Live-Crypto-Test: 3/3 Symbole erfolgreich, Health `healthy=true`.
- Produktionsverifikation: Zyklen 1 und 2 jeweils `results=3`, `healthy=true`, `status=OK`; `published_results=6`.
- Crypto-Fehlerzähler vor/nach Zyklus 2: **12.024 → 12.024**, also kein neuer Fehler.
- Neue Analysezeiten in Zyklus 2: BTC 14:01:24 UTC, ETH 14:01:36 UTC, XRP 14:01:39 UTC.
- Telegram: `enabled=false`, `dry_run=true`, `messages_sent=0`.
- Neue stdout-/stderr-Logs waren zum Abschluss leer; kein Startfehler.

### Bekannte Fehler

- `KP-012`: Der erste historische Servicefehler kann weiterhin aus der begrenzten In-Memory-Historie verschwinden; aktuelle letzte Fehlerdetails sind nun sichtbar, aber noch nicht langfristig journalisiert.
- Storage-Worker-Shutdown-Race, Storage-Timeout und WebSocket-Fallback bleiben offen.
- Deprecation-Warnungen zu `datetime.utcnow()` stammen weiterhin aus dem externen Legacy-Crypto-Projekt.

### Getroffene Architekturentscheidungen

- Marktdatenbeschaffung gehört jetzt zur PandorickKi-Integrationsschicht und hängt nicht mehr von `requests`/`pandas` im externen `market.py` ab.
- Kerzen sind Pflichtdaten; Open Interest und Funding sind optionaler Kontext und dürfen gültige Analysen nicht stoppen.
- Binance ist primäre Candle-Quelle, Bitget read-only Fallback. Keine privaten APIs und keine Orderendpunkte.
- Externe Legacy-Analyse bleibt unverändert außerhalb des Repositories und wird mit `persist=False` verwendet.
- Startumgebung ist projektlokal und vorab prüfbar; Telegram-Sicherheitswerte werden im Webstarter explizit gesetzt.

### Nicht abgeschlossene Punkte

- Änderungen sind lokal getestet, aber noch nicht commitet oder auf GitHub gepusht.
- Langfristiges, größenbegrenztes Service-Fehlerjournal fehlt.
- Die bereits bekannten Storage- und WebSocket-Probleme bleiben offen.

### Exakter nächster sinnvoller Arbeitsschritt

Den vollständigen Diff einschließlich der neuen Dokumentation abschließend auf unbeabsichtigte lokale Daten und Secrets prüfen. Danach nach ausdrücklicher Benutzerfreigabe einen kleinen Commit auf dem bestehenden Feature-Branch erstellen und zu `cRioshy/Pando` pushen. Technisch anschließend `KP-011` (Storage-Worker-Shutdown-Race) mit einem deterministischen Regressionstest beheben.

---

## Letzte Aufgabe: Öffentliche Pando-Repo aktualisieren

### Datum und Uhrzeit

26. Juli 2026, 16:32 Uhr, Europe/Berlin (`+02:00`)

### Ziel der Aufgabe

Den geprüften lokalen Pandorick-Arbeitsstand im öffentlichen GitHub-Repository `cRioshy/Pando` veröffentlichen.

### Durchgeführte Arbeiten

- GitHub CLI unter `C:\Program Files\GitHub CLI\gh.exe` gefunden und Anmeldung als `cRioshy` bestätigt.
- Vollständigen Scope geprüft: 17 bekannte Projektdateien, keine Runtime-/History-Dateien.
- Secret-Mustersuche ausgeführt; markierte Treffer waren Konfigurationsfelder beziehungsweise Testwerte, keine veröffentlichten Zugangsdaten.
- Diff auf Whitespace geprüft und eine Markdown-Trailing-Whitespace-Stelle bereinigt.
- Commit `38e1ddf` erstellt und auf `origin/agent/add-market-feature-engine` gepusht.
- Neuen Draft-Pull-Request #2 gegen `main` eröffnet.

### Veränderte Dateien

- `docs/KNOWN_PROBLEMS.md` – Veröffentlichung als erledigt markiert.
- `docs/NEXT_STEPS.md` – GitHub-Veröffentlichung aus offenen Schritten entfernt.
- `docs/SESSION_HANDOVER.md` – Veröffentlichung dokumentiert.

### Neue Dateien

- Keine dauerhaften neuen Dateien in diesem Abschlusscommit.

### Ausgeführte Befehle

- `gh --version`, `gh auth status`
- `git status -sb`, `git diff --check`, `git diff --stat`, `git diff --name-only`
- Secret-Mustersuche über die 17 Veröffentlichungsdateien
- explizites `git add` der 17 Dateien
- `git commit -m "Stabilize storage statistics and add project handover"`
- `git push -u origin agent/add-market-feature-engine`
- `gh pr view`, `git fetch origin --prune`, Vergleich zu `origin/main`
- `gh pr create --draft --base main --head agent/add-market-feature-engine ...`

### Ausgeführte Tests

- In dieser Veröffentlichung keine neue vollständige Suite; verwendet wurden die unmittelbar zuvor dokumentierten Testergebnisse.
- `git diff --cached --check`: bestanden nach Bereinigung der Markdown-Leerzeichen.

### Tatsächliche Testergebnisse

- Commit: `38e1ddf` (`17 files changed, 1528 insertions, 48 deletions`).
- Push: erfolgreich, `d313794..38e1ddf` auf `origin/agent/add-market-feature-engine`.
- Draft-PR: `https://github.com/cRioshy/Pando/pull/2`.
- Bekannter Teststatus unverändert: jüngster vollständiger Lauf 195 Tests mit einem nicht-deterministischen Windows-Cleanup-Fehler; isolierte Wiederholung 1/1 bestanden.

### Bekannte Fehler

- Storage-Worker-Shutdown-Race, Storage-Timeout und WebSocket-Fallback bleiben offen laut `docs/KNOWN_PROBLEMS.md`.
- Branch liegt öffentlich vor, ist aber noch nicht nach `main` gemergt.

### Getroffene Architekturentscheidungen

- Keine neue Produktarchitektur.
- Veröffentlichung erfolgt über Feature-Branch und Draft-PR; `main` wird nicht direkt überschrieben.

### Nicht abgeschlossene Punkte

- Draft-PR #2 prüfen und anschließend bewusst mergen.
- Storage-Worker-Shutdown-Race bleibt der nächste technische Fix.

### Exakter nächster sinnvoller Arbeitsschritt

Draft-PR #2 prüfen. Technisch anschließend einen deterministischen Regressionstest für `StorageStatisticsService.close()` ergänzen und garantieren, dass nach `close()` kein Worker mehr schreibt.

---

## Letzte Aufgabe: GitHub-Aktualität prüfen

### Datum und Uhrzeit

26. Juli 2026, 16:06 Uhr, Europe/Berlin (`+02:00`)

### Ziel der Aufgabe

Feststellen, ob der aktuelle lokale Pando-Arbeitsstand vollständig auf GitHub vorhanden ist.

### Durchgeführte Arbeiten

- Vorgeschriebene Übergabedokumente gelesen.
- Repository und relevanten Git-Arbeitsbaum geprüft.
- Remote `origin` von `https://github.com/cRioshy/Pando.git` aktualisiert.
- Lokalen Branch mit seinem GitHub-Tracking-Branch verglichen.

### Veränderte Dateien

- `docs/SESSION_HANDOVER.md` – diese Statusprüfung ergänzt.

### Neue Dateien

- Keine.

### Ausgeführte Befehle

- `git status --short`, `git status -sb`, `git branch --show-current`, `git remote -v`, `git log -1 --oneline --decorate`
- `git fetch origin --prune`
- `git rev-list --left-right --count HEAD...origin/agent/add-market-feature-engine`
- `git branch -r` und Prüfung von `origin/HEAD`

### Ausgeführte Tests

- Keine Softwaretests; reine Git-Statusprüfung.

### Tatsächliche Testergebnisse

- Lokaler Commit `d313794` und `origin/agent/add-market-feature-engine` sind `0` Commits auseinander.
- Der Arbeitsbaum enthält weiterhin 11 veränderte und 6 unversionierte Projekt-/Dokumentationsdateien. Diese Inhalte sind nicht auf GitHub.
- Remote-Standardbranch ist `origin/main`.

### Bekannte Fehler

- `KP-010` bleibt offen: Der aktuelle Arbeitsbaum ist noch nicht versioniert und nicht gepusht.
- Weitere bekannte Fehler unverändert laut `docs/KNOWN_PROBLEMS.md`.

### Getroffene Architekturentscheidungen

- Keine.

### Nicht abgeschlossene Punkte

- Änderungen prüfen, committen und pushen.
- Vor einem Push muss der bekannte nicht-deterministische Testfehler bewusst bewertet werden.

### Exakter nächster sinnvoller Arbeitsschritt

Den vollständigen Diff auf Secrets, Runtime-Daten und unbeabsichtigte lokale Pfade prüfen. Danach nach ausdrücklicher Benutzerfreigabe einen nachvollziehbaren Commit auf `agent/add-market-feature-engine` erstellen und diesen Branch zu `origin` pushen.

---

## Datum und Uhrzeit

26. Juli 2026, 12:44 Uhr, Europe/Berlin (`+02:00`)

## Ziel der Aufgabe

Eine dauerhafte lokale Projektübergabe einrichten, damit ein neuer Codex-Chat den aktuellen Entwicklungsstand ohne Zugriff auf frühere Chats rekonstruieren kann. Die Dokumentation musste auf dem tatsächlich vorhandenen Code und der aktuellen Repository-Struktur beruhen.

## Durchgeführte Arbeiten

- Die vom Benutzer vorgegebene Lesereihenfolge geprüft. Zu Beginn fehlten `AGENTS.md`, `docs/SESSION_HANDOVER.md`, `docs/KNOWN_PROBLEMS.md` und `docs/NEXT_STEPS.md`.
- Die vorhandenen Dokumente `CURRENT_SYSTEM_STATE.md` und `ARCHITECTURE.md` vollständig gelesen und mit dem aktuellen Code abgeglichen.
- Repository-Struktur, Git-Arbeitsbaum, CLI-Einstieg, Orchestrator, Adapterreihenfolge, Event-Abonnements, Konfiguration, Speicherpfade, Web-API, Storage-Scanner und WebSocket-Client statisch geprüft.
- Die laufende lokale API read-only geprüft: Health `OK`, 7 Storage-Ordner, 93 gecachte Dateien, 4,26 GB, letzter Scan `TIMEOUT`, Live-Cryptopreise vorhanden.
- Verbindliche Arbeits-, Sicherheits- und Abschlussregeln in `AGENTS.md` angelegt.
- Systemzustand und Architektur vollständig auf den aktuellen Storage-Cache-/Worker-Stand gebracht; Mermaid-Diagramme aktualisiert.
- Bekannte Probleme priorisiert dokumentiert, einschließlich Storage-Timeout, WebSocket-Fallback und nicht-deterministischer Storage-Worker-Shutdown-Race.
- Nächste Schritte geordnet und den deterministischen Storage-Shutdown als ersten technischen Schritt festgelegt.
- Dokumentationsstruktur automatisiert geprüft.
- Vollständige Testsuite ausgeführt und den dabei neu erkannten Shutdown-Race ehrlich dokumentiert.
- Betroffenen Webtest isoliert wiederholt; der isolierte Lauf bestand.

## Veränderte Dateien

- `docs/CURRENT_SYSTEM_STATE.md` – veralteten Stand ersetzt, Storage-Architektur, Livezustand, Teststatus und Risiken aktualisiert.
- `docs/ARCHITECTURE.md` – Ist-Architektur und Mermaid-Diagramme aktualisiert.

Bereits vor dieser Dokumentationsaufgabe lokal verändert und bewusst erhalten:

- `.env.example`
- `adapters/crypto_adapter.py`
- `adapters/stock_adapter.py`
- `config.py`
- `tests/test_statistics_and_storage.py`
- `tests/test_web_control_center.py`
- `web/api.py`
- `web/routes.py`
- `web/static/control_center.html`
- `web/static/control_center.js`
- `web/statistics_service.py`

## Neue Dateien

- `AGENTS.md`
- `docs/SESSION_HANDOVER.md`
- `docs/KNOWN_PROBLEMS.md`
- `docs/NEXT_STEPS.md`

Hinweis: `docs/CURRENT_SYSTEM_STATE.md` und `docs/ARCHITECTURE.md` existierten lokal bereits, waren aber laut `git status` noch nicht versioniert.

## Ausgeführte Befehle und Prüfungen

Die folgenden Befehlsgruppen wurden read-only beziehungsweise testend ausgeführt:

- `Get-Content -Raw` für die sechs vorgegebenen Übergabedateien in der verlangten Reihenfolge.
- `git status --short` und `git diff --stat` mit dem gebündelten Git-Executable.
- `rg --files` zur tatsächlichen Repository-Inventur.
- `rg` auf Klassen, CLI-Argumente, Adapteraufbau, Event-Abonnements, Publikationen, Konfigurationsfelder, Storage-Worker, Web-Routen und WebSocket-Fallback.
- Ausschnittsweise `Get-Content`-Prüfung von `main.py`, `orchestrator.py`, `config.py`, `web/statistics_service.py` und `tests/test_web_control_center.py`.
- `Invoke-RestMethod` auf `/api/health`, `/api/status`, `/api/statistics/storage` und `/api/crypto`.
- PowerShell-Strukturprüfung auf vorhandene, nicht leere UTF-8-Dateien, alle Pflichtüberschriften und mindestens drei Mermaid-Blöcke.
- Vollständiger Unit-Testlauf und isolierter Wiederholungslauf des fehlgeschlagenen Tests.
- Dateiänderungen ausschließlich über `apply_patch`.

Es wurden keine Daten-, History-, Lern-, Token- oder Konfigurationsdateien gelöscht. Es wurden keine echten Trades, keine Orderausführung und kein Telegram-Liveversand aktiviert. Es wurde kein Commit und kein GitHub-Push ausgeführt.

## Ausgeführte Tests

### Dokumentationsstruktur

Geprüft wurden:

- Vorhandensein und nicht leerer UTF-8-Inhalt von `AGENTS.md`, `CURRENT_SYSTEM_STATE.md`, `ARCHITECTURE.md`, `KNOWN_PROBLEMS.md` und `NEXT_STEPS.md`.
- Alle vom Benutzer geforderten Abschnitte in `CURRENT_SYSTEM_STATE.md`.
- Mindestens drei Mermaid-Diagramme in `ARCHITECTURE.md`.

### Vollständige Python-Suite

```powershell
& 'C:\Users\Admin\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' -m unittest discover -s tests
```

### Isolierter Wiederholungstest

```powershell
& 'C:\Users\Admin\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' -m unittest tests.test_web_control_center.WebControlCenterTest.test_learning_report_endpoint_returns_json
```

## Tatsächliche Testergebnisse

- Dokumentationsstruktur: **bestanden**. Alle fünf vor der Übergabe angelegten/aktualisierten Grunddateien waren vorhanden, UTF-8-lesbar und nicht leer; alle Pflichtabschnitte und Mermaid-Blöcke wurden gefunden.
- Vollständige Python-Suite: **fehlgeschlagen mit 1 Fehler**. `Ran 195 tests in 243.332s`, Ergebnis `FAILED (errors=1)`.
- Fehler: `test_learning_report_endpoint_returns_json` scheiterte beim Aufräumen eines temporären Verzeichnisses mit `OSError: [WinError 145] Das Verzeichnis ist nicht leer: ...\storage\statistics`.
- Isolierter Wiederholungstest: **bestanden**, `Ran 1 test in 1.213s`, Ergebnis `OK`.
- Zusätzlich erschienen bekannte `DeprecationWarning`-Meldungen zu `datetime.utcnow()` aus dem externen Legacy-Crypto-Projekt.

Vor diesem Dokumentationslauf war dieselbe vollständige Suite in diesem Arbeitsstand einmal mit 195/195 erfolgreich. Der neue Lauf zeigt deshalb einen nicht-deterministischen Shutdown-/Dateischreib-Race und darf nicht als vollständig grün bezeichnet werden.

## Bekannte Fehler

Vollständig in `docs/KNOWN_PROBLEMS.md` beschrieben. Für die unmittelbare Weiterarbeit besonders wichtig:

1. `StorageStatisticsService.close()` wartet nur eine Sekunde; ein Worker kann danach noch Index-/Cachedateien schreiben und temporäre Verzeichnisse überleben.
2. Reale Storage-Scans überschreiten weiterhin teilweise das 30-Sekunden-Zeitlimit.
3. WebSocket-`error`/`close`, Polling-Timer, Reconnect und JSON-/Renderfehler sind nicht robust.
4. Der synchrone EventBus kann Publisher blockieren.
5. Brain/Decision Core besitzen kein unabhängiges fachliches Freigabe-Gate.
6. Telegram hängt nicht strikt hinter finalen Decisions.
7. Keine zentrale Retention-Policy; bestehende History darf trotzdem nicht ungefragt gelöscht werden.
8. Der gesamte aktuelle Arbeitsbaum ist noch nicht commitet beziehungsweise zu GitHub gepusht.

## Getroffene Architekturentscheidungen

- Die Übergabedokumentation beschreibt die aktuelle Implementierung, nicht gewünschte oder aus Modulnamen abgeleitete Fähigkeiten.
- Persistenter Storage-Cache und Dateiindex sind Teil der dokumentierten Ist-Architektur.
- `TIMEOUT`/Teilscan und der letzte gültige Cache werden als getrennte Zustände behandelt; ein Timeout bedeutet nicht automatisch Datenverlust.
- Der Storage-Worker-Shutdown muss garantieren, dass nach `close()` keine weiteren Schreibvorgänge stattfinden. Die konkrete Implementierung ist noch offen und wurde in dieser Dokumentationsaufgabe nicht verändert.
- Keine automatische Orderausführung und keine Aktivierung realer Trades.
- Runtime-Historien, Lern- und Konfigurationsdaten bleiben unangetastet.

## Nicht abgeschlossene Punkte

- Storage-Worker-Shutdown-Race ist dokumentiert, aber noch nicht behoben.
- Ursache des realen Storage-Timeouts ist noch nicht instrumentiert.
- WebSocket-Reconnect/Fallback ist noch nicht gehärtet.
- Arbeitsbaum ist nicht commitet und nicht gepusht.
- Vollständige Suite ist wegen des nicht-deterministischen Cleanup-Fehlers im jüngsten Lauf nicht grün.

## Exakter nächster sinnvoller Arbeitsschritt

Einen deterministischen Regressionstest erstellen, der `StorageStatisticsService.close()` während eines laufenden beziehungsweise verzögerten Cache-/Index-Schreibvorgangs aufruft. Danach den Shutdown-Vertrag so ändern, dass `close()` erst zurückkehrt, wenn der Worker garantiert beendet ist und keine weiteren Schreibvorgänge mehr stattfinden. Anschließend den isolierten Test, `tests.test_statistics_and_storage`, `tests.test_web_control_center` und zuletzt die vollständige 195-Test-Suite ausführen. Keine Runtime-Daten löschen und keine Trading-/Telegram-Einstellungen verändern.
