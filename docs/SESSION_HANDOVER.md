# Session-Handover

## Aktuelle Aufgabe: PR #23 mergen und PR #24 auf main umstellen

### Datum und Uhrzeit

14. August 2026, 10:51 Uhr, Europe/Berlin (`+02:00`)

### Ziel der Aufgabe

Nach ausdrücklicher Benutzerfreigabe den zuvor geprüften Stock-/Polling-/Verification-PR #23 kontrolliert nach `main` mergen. Anschließend den Market-Regime-PR #24 auf den neuen `main` umstellen, weiterhin als Draft belassen und Diff, Konfliktfreiheit, Tests und Sicherheitsgrenzen erneut prüfen. PR #24 nicht mergen.

### Durchgeführte Arbeiten

- Verpflichtende Übergabe- und Market-Regime-Vertragsdokumente erneut vollständig gelesen.
- GitHub-Authentifizierung, Remote, Working Tree, beide PR-Heads, Basis-SHAs, Merge-Status und Repository-Mergeverfahren unmittelbar vor dem Merge geprüft.
- PR #23 mit erwartetem Head `4f685522267b33277f1fa3da2444b132dd2cfbff` aus Draft genommen und per normalem Merge-Commit nach `main` gemergt; Branch nicht gelöscht.
- Merge-Commit `c751fe18e966dc6800d80925c8c7020093c85e8e` und vollständige Erreichbarkeit des PR-Heads aus `origin/main` verifiziert.
- PR #24 von `agent/integrate-decision-gate-observer` auf `main` umgestellt und ausdrücklich als Draft/offen/ungemergt belassen.
- Neuen `main` ohne Rebase oder Force-Push per normalem Merge-Commit `6f8d96f3035d1b9a57df66ce0a2a4fd02a2d4496` in `agent/market-regime-contract-v1` aufgenommen.
- PR-#24-Diff erneut geprüft: weiterhin exakt 29 Regime-/Adapter-/API-/UI-/Test-/Dokumentationspfade, konfliktfreie Merge-Simulation, keine Runtime-/History-/Ledgerpfade und keine Secret-Mustertreffer.
- Getesteten Branch einschließlich `main`-Merge und Zustandsdokumentation als Commit `7c7d4f8f0598f0dc943a86b9ab4be53baba979ca` auf `origin/agent/market-regime-contract-v1` veröffentlicht. Lokal und Remote waren anschließend `0/0` synchron; GitHub zeigte PR #24 weiterhin offen, Draft, ungemergt und gegen `main`.

### Veränderte Dateien

- `docs/CURRENT_SYSTEM_STATE.md`
- `docs/SESSION_HANDOVER.md`
- `docs/KNOWN_PROBLEMS.md`
- `docs/NEXT_STEPS.md`

### Neue Dateien

- Keine.

### Ausgeführte Befehle

- `gh auth status`, GitHub Pull-Request-/Repository-API, `gh pr ready`, `gh pr merge`, `gh pr edit`
- `git status`, `git fetch`, `git rev-parse`, `git merge-base`, `git rev-list`
- `git merge-tree --write-tree`, `git diff --check`, Scope- und Secret-Musterprüfung
- `git merge --no-edit origin/main`
- `.venv\Scripts\python.exe -m unittest discover -s tests -q`
- isolierter `unittest`-Lauf für `test_legacy_cache_without_metric_contract_is_rebuilt`
- `node --check web/static/control_center.js`
- `.venv\Scripts\python.exe -m py_compile ...` für Decision-/Stock-/Regime-/Orchestrator-/Web-Kernmodule

### Ausgeführte Tests und tatsächliche Testergebnisse

- Erster Gesamtlauf nach Retargeting: 317 fachliche Tests bestanden; ein Fehler ausschließlich beim Windows-`TemporaryDirectory`-Cleanup des Learning-Report-Tests mit bekanntem `WinError 145` (KP-019).
- Betroffener Test unmittelbar isoliert: 1/1 bestanden in 0,010 Sekunden.
- Unmittelbare vollständige Wiederholung: 318/318 bestanden in 42,246 Sekunden.
- JavaScript-Syntax und Python-Kompilierung: bestanden.
- PR-#24-Diffprüfung: sauber; 29 Pfade, 0 Runtime-/History-/Ledgerpfade, 0 Secret-Mustertreffer.
- Merge-Simulation PR #24 gegen neuen `main`: konfliktfrei.

### Bekannte Fehler

- KP-019 trat erneut sporadisch beim Windows-Temp-Cleanup auf; isolierter Test und vollständige Wiederholung waren grün. Kein Hinweis auf eine fachliche Stock-/Regime-/Merge-Regression.
- KP-027 bleibt für PR #24 teilweise offen: weiterhin keine GitHub-Checks und keine Reviews. PR #23 wurde nach dokumentierter lokaler Prüfung und ausdrücklicher Benutzerfreigabe gemergt.
- KP-026 bleibt offen: längere unabhängige Regime-Coverage und Schwellenvalidierung fehlen weiterhin.

### Getroffene Architekturentscheidungen

- Der geprüfte Stock-/Polling-/Verification-Stand ist nun Bestandteil von `main`.
- Market Regime v1 bleibt ein separater Draft-PR direkt gegen `main`, observer-only und ohne Decision-, Telegram- oder Orderkopplung.
- Historie wurde nicht umgeschrieben: kein Rebase, kein Force-Push und kein Branch-Löschen.

### Nicht abgeschlossene Punkte

- PR #24 bleibt Draft und ungemergt; GitHub-CI/Review fehlen weiterhin.
- Kein kontrollierter Produktionsneustart mit Market Regime v1 wurde ausgeführt, da der PR noch nicht gemergt ist.

### Exakter nächster sinnvoller Arbeitsschritt

Abschlussbericht vorlegen und PR #24 als Draft belassen. PR #24 nur nach einer neuen ausdrücklichen Freigabe aus Draft nehmen oder mergen; erst nach einem späteren Merge einen kontrollierten Produktionsneustart und observer-only Liveprüfung durchführen.

## Aktuelle Aufgabe: Draft-PR #23 und #24 fachlich prüfen

### Datum und Uhrzeit

13. August 2026, 12:01 Uhr, Europe/Berlin (`+02:00`)

### Ziel der Aufgabe

Den Stock-/Polling-/Verification-Draft-PR #23 und anschließend den darauf gestapelten Market-Regime-Draft-PR #24 hinsichtlich Scope, Branch-Basis, Konflikten, Checks, Secrets, Runtime-Daten, Tests und Sicherheitsgrenzen prüfen. Nichts mergen und keinen Produktcode verändern.

### Durchgeführte Arbeiten

- Verpflichtende Übergabe- und Market-Regime-Vertragsdokumente erneut vollständig gelesen und aktuellen lokalen Branch/Remote geprüft.
- GitHub-Metadaten, Commits, Dateien, Reviews, Checks und Merge-Status für PR #23 und #24 schreibgeschützt abgerufen.
- Beide Remote-Branches aktualisiert und getrennte Drei-Punkt-Diffs gegen ihre jeweilige Basis geprüft.
- PR #23 gegen `main` und PR #24 gegen `agent/integrate-decision-gate-observer` per `git merge-tree --write-tree` konfliktfrei simuliert.
- Beide Änderungsumfänge auf Runtime-/History-/Ledger-/Secret-Pfade und typische Secret-Muster geprüft.
- Sicherheitsrelevante Defaults und neue Observer-Payloads gegen Telegram-/Order-/Decision-Grenzen geprüft.
- Aktuelle gestapelte Gesamtsuite, JavaScript-Syntax und Python-Kompilierung erneut ausgeführt.

### Veränderte Dateien

- `docs/SESSION_HANDOVER.md`
- `docs/KNOWN_PROBLEMS.md`
- `docs/NEXT_STEPS.md`

### Neue Dateien

- Keine.

### Ausgeführte Befehle

- `git status`, `git branch --show-current`, `git rev-parse`, `git remote -v`, `git fetch`
- `gh pr view`, `gh pr checks`, GitHub Pull-Request-API
- `git diff --name-status`, `git diff --check`, Scope-/Secret-Musterprüfung
- `git merge-tree --write-tree` für beide PR-Stufen
- `.venv\Scripts\python.exe -m unittest discover -s tests -q`
- `node --check web/static/control_center.js`
- `.venv\Scripts\python.exe -m py_compile ...` für die neuen und geänderten Kernmodule

### Ausgeführte Tests und tatsächliche Testergebnisse

- Vollständige aktuelle Regression: 318/318 Tests bestanden in 40,963 Sekunden.
- JavaScript-Syntax: bestanden.
- Python-Kompilierung der Decision-/Stock-/Regime-/Orchestrator-/Web-Kernmodule: bestanden.
- PR #23: 48 geänderte Pfade, 0 Runtime-/History-/Ledgerpfade, 0 Secret-Mustertreffer, Diffprüfung sauber, Merge-Simulation konfliktfrei; GitHub `mergeable=true`, `mergeable_state=clean`.
- PR #24: 29 geänderte Pfade, 0 Runtime-/History-/Ledgerpfade, 0 Secret-Mustertreffer, Diffprüfung sauber, Merge-Simulation konfliktfrei; GitHub `mergeable=true`, `mergeable_state=clean`.
- GitHub meldet für beide Branches keine Checks und keine Reviews. Dies ist kein bestandener CI-Lauf, sondern eine fehlende CI-/Review-Abdeckung.

### Bekannte Fehler

- KP-027 neu dokumentiert: Für PR #23 und #24 sind keine GitHub-Checks eingerichtet beziehungsweise gemeldet und keine Reviews vorhanden.
- KP-026 bleibt offen: Der Regime-Classifier benötigt längere unabhängige Coverage und Schwellenvalidierung.
- Die bestehenden Stock-Verification-, `SPCX`- und historischen Storage-Grenzen bleiben unverändert.

### Getroffene Architekturentscheidungen

- Keine Architekturänderung vorgenommen.
- PR #24 bleibt gestapelt auf PR #23. PR #24 darf nicht vor PR #23 in `main` integriert werden.
- Observer-only-Grenzen bleiben erhalten: kein aktiver Decision-Einfluss, keine Telegram-Freigabe und keine Orderausführung.

### Nicht abgeschlossene Punkte

- Kein PR wurde gemergt oder aus dem Draft-Status genommen.
- Es existiert weiterhin keine unabhängige GitHub-CI- oder menschliche Review-Freigabe.
- Nach einem später ausdrücklich freigegebenen Merge von PR #23 muss PR #24 auf `main` umgestellt beziehungsweise gegen den neuen `main` neu geprüft werden.

### Exakter nächster sinnvoller Arbeitsschritt

PR #23 im Draft belassen, bis der Benutzer den Merge nach Kenntnis der fehlenden GitHub-CI-/Review-Abdeckung ausdrücklich freigibt. Erst PR #23 mergen; danach PR #24 auf `main` retargeten, Merge-Status und vollständige Tests erneut prüfen und PR #24 weiterhin separat als Draft behandeln.

## Aktuelle Aufgabe: Market Regime Contract v1 observer-only implementieren

### Datum und Uhrzeit

12. August 2026, 22:13 Uhr, Europe/Berlin (`+02:00`)

### Ziel der Aufgabe

Nach sauberem Abschluss von Phase 0 auf einem separaten Branch einen deterministischen, restart-sicheren Market-Regime-Observer mit unabhängigen Achsen für Trendrichtung, Volatilität und Trendphase implementieren. Bestehende Decisions, Shadow Decisions, Confidence, Outcomes, Telegram, Orders, Stimpy, Ren, `main` und das separate PANDO-Token-Projekt unverändert lassen.

### Durchgeführte Arbeiten

- Branch `agent/market-regime-contract-v1` vom gesicherten Phase-0-Head `4f685522267b33277f1fa3da2444b132dd2cfbff` erstellt.
- Versionierten Vertrag `pandorickki.market-regime-snapshot` v1 mit endlichen Scores von 0 bis 1 und strikt getrennten Achsen implementiert.
- Deterministische `feature_snapshot_id`, `regime_id` und einen SHA-256-`config_fingerprint` definiert. `source_event_id` dient nur der Rückverfolgung und nicht der kanonischen Identität.
- Feature-Quality-Vertrag fail-closed eingebunden: `OK`, confidence-begrenztes `DEGRADED` und vollständiges `UNKNOWN` bei `REJECTED`.
- Echte Crypto-`15m`-Kerzen und öffentliche Stock-`1d`-Kerzen intern angebunden. Der Stock-Legacy-Einzeilenfallback wird nicht verwendet; fehlende reale Timeframes werden explizit ausgewiesen.
- Begrenzte Drop-newest-Queue, Batch-Worker, append-only rotierendes JSONL-Ledger, Restart-Deduplizierung und vollständig drainierenden Shutdown umgesetzt.
- Ausschließlich kompakte `MARKET_REGIME_OBSERVED`-Ereignisse ergänzt; Rohkerzen, vollständige Features, `raw_result`, Secrets und lokale Pfade bleiben außerhalb öffentlicher Payloads.
- GET-only API mit Filterung, Zeitraum, Limits und Pagination sowie read-only Control-Center-Bereich ohne Tradebuttons oder Empfehlungen ergänzt.
- Coverage über sämtliche zulässigen Kategorien einschließlich Nullwerten, häufigste Kombinationen und Assetklassen implementiert.
- Kurzen isolierten Live-Smoke-Test mit öffentlichen BTCUSDT-`15m`- und AAPL-`1d`-Daten ausgeführt. Er verwendete ausschließlich temporären Speicher und veränderte weder den laufenden Dienst auf Port 8000 noch vorhandene Runtime-/History-Daten.
- AFTER-Backup per kontrolliertem Staging und PowerShell `Compress-Archive` erstellt und vollständig geprüft: `C:\Users\Admin\Desktop\PandorickBackUp_2026-08-12_22-16-19_AFTER.zip`, 1.512.476.762 Byte, 1.201 Einträge. `.git`, `docs`, `tests`, `AGENTS.md` und Regime-Quellen sind enthalten; .NET-Öffnung und vollständige Testextraktion waren erfolgreich, beide temporären Prüfverzeichnisse wurden anschließend sicher entfernt.
- Implementierungsstand als Commit `226931eb9ba0f4ddbf719b3dbd3675dcbd8a2fc1` mit Nachricht `Add observer-only market regime contract v1` gesichert und ausschließlich auf `origin/agent/market-regime-contract-v1` gepusht; lokal und Remote waren danach `0/0` synchron.
- Draft-PR #24 erstellt: `https://github.com/cRioshy/Pando/pull/24`. Er ist `OPEN`, `isDraft=true`, hat Head `agent/market-regime-contract-v1` und Basis `agent/integrate-decision-gate-observer`. `main` blieb auf `14e19bf0a4e79860732ff3b6bba4135a2504b909` unverändert; PR #23 blieb Draft und ungemergt.

### Veränderte Dateien

- `.env.example`
- `AGENTS.md`
- `README.md`
- `adapters/crypto_adapter.py`
- `adapters/stock_adapter.py`
- `config.py`
- `docs/ARCHITECTURE.md`
- `docs/CURRENT_SYSTEM_STATE.md`
- `docs/KNOWN_PROBLEMS.md`
- `docs/NEXT_STEPS.md`
- `docs/SESSION_HANDOVER.md`
- `orchestrator.py`
- `tests/test_config.py`
- `tests/test_crypto_adapter.py`
- `tests/test_stock_adapter.py`
- `tests/test_web_control_center.py`
- `web/api.py`
- `web/routes.py`
- `web/static/control_center.html`
- `web/static/control_center.js`

### Neue Dateien

- `market_regime_contract.py`
- `adapters/market_regime_observer_adapter.py`
- `scripts/market_regime_live_smoke.py`
- `tests/test_market_regime_contract.py`
- `tests/test_market_regime_observer_adapter.py`
- `docs/MARKET_REGIME_CONTRACT.md`
- `docs/DATA_MODEL.md`
- `docs/API.md`
- `docs/SECURITY_BOUNDARIES.md`

### Ausgeführte Befehle

- Pflichtdokument-, Struktur-, Import-, Diff-, Branch- und Remote-Prüfungen mit PowerShell, `rg` und Git
- gezielte `python -m unittest`-Läufe für Vertrag, Observer, Konfiguration, Crypto, Stocks und Web/API
- vollständige `python -m unittest discover -s tests -q`-Regression
- `node --check web/static/control_center.js`
- `git diff --check`
- `.venv\Scripts\python.exe scripts\market_regime_live_smoke.py` mit öffentlichem Netzwerkzugriff
- kontrollierte rekursive Staging-Kopie, `Compress-Archive`, .NET-`ZipFile.OpenRead` und `Expand-Archive` für das AFTER-Backup
- `git commit`, `git push --set-upstream`, `gh pr create --draft` und abschließende Branch-/PR-/Remote-Prüfungen

### Ausgeführte Tests und tatsächliche Testergebnisse

- Gezielte Abschluss-Suite: 55/55 bestanden in 9,195 Sekunden.
- Vollständige Regression: 318/318 bestanden in 43,245 Sekunden.
- JavaScript-Syntax: bestanden.
- Diff-Prüfung: keine Inhaltsfehler; nur erwartete LF/CRLF-Hinweise.
- Ein versuchter `pytest`-Aufruf wurde nicht ausgeführt, weil `pytest` nicht in der Projekt-`.venv` installiert ist. Es wurde nichts installiert; die dokumentierte `unittest`-Suite lief vollständig erfolgreich.
- Isolierter Live-Smoke-Test: 2 Eingaben, 2 persistierte Snapshots, 1 Batch, 0 Duplikate, 0 Drops, 0 Fehler, Queue-Tiefe 0 und Worker nach Shutdown beendet. Laufzeit 1,616 Sekunden, CPU-Zeit 0,484 Sekunden.
- BTCUSDT: `DOWN + MEDIUM + WEAKENING`, Quality `OK`, Timeframe `15m`, fehlend `1m/5m/1h/4h`.
- AAPL: `UNKNOWN + HIGH + UNKNOWN`, Quality `OK`, Timeframe `1d`, fehlend `1m/5m/15m/1h/4h`. `UNKNOWN` wurde sicher beibehalten und nicht künstlich ersetzt.
- Ereignisse: ausschließlich Start, zwei `MARKET_REGIME_OBSERVED` und Stop. Keine Decision-, Signal-, Shadow-, Trade-, Telegram- oder Orderereignisse. Temporäres Ledger nach erfolgreicher Prüfung entfernt.
- AFTER-Backup: 1.201 plausible Einträge und 1.512.476.762 Byte; `.git`, `docs`, `tests`, `AGENTS.md` und Quellcode vorhanden; Testextraktion bestanden.

### Bekannte Fehler

- KP-026 bleibt offen: Ein kurzer Zweimarkt-Smoke-Test validiert keine fachlichen Schwellen oder Marktphasen-Coverage.
- Die bestehende Stock-Verification-Laufunterbrechung, `SPCX`-Quote-Grenze und zwei beschädigten historischen Backup-JSONs bleiben unverändert dokumentiert.
- `pytest` ist nicht Teil der Projekt-`.venv`; die verbindliche Suite verwendet `unittest`.

### Getroffene Architekturentscheidungen

- Regime v1 bleibt vollständig observer-only und besitzt keine Kante zu Decision Core, Shadow Gate, Outcome-Entscheidung, Trade Tracker, Telegram oder Orders.
- Drei Regime-Achsen bleiben unabhängig; keine Kombination wird in LONG, SHORT, HOLD oder NO-TRADE übersetzt.
- Persistenz liegt hinter einer begrenzten Queue. Kanonische Identität basiert auf Marktdaten, Vertrag, Classifier und Konfiguration, nicht auf restart-abhängigen Event-IDs.
- API und UI zeigen ausschließlich kompakte, read-only Projektionen. Coverage führt alle Vertragsklassen explizit, auch wenn ihr Zähler null ist.

### Nicht abgeschlossene Punkte

- Reale mehrwöchige Coverage und Outcome-Auswertung sind bewusst nicht gestartet.
- Keine automatische Regime-Regel, Schwellenoptimierung oder Stimpy-Verbindung implementiert.

### Exakter nächster sinnvoller Arbeitsschritt

Draft-PR #24 fachlich prüfen und ausdrücklich nicht mergen, solange der gestapelte Phase-0-PR #23 nicht geprüft ist. Danach nur mit separater Freigabe eine längere observer-only Regime-Coverage starten; keinen Fit, keine Decision-Regel und keine Telegram-/Orderkopplung aktivieren.

## Aktuelle Aufgabe: Phase 0 – bestehenden Stock-/Polling-/Verification-Stand sichern

### Datum und Uhrzeit

12. August 2026, 21:42 Uhr, Europe/Berlin (`+02:00`)

### Ziel der Aufgabe

Den bereits lokal vorhandenen Stock-/Polling-/Verification-Stand vollständig prüfen, testen und als eigenen Stand auf `agent/integrate-decision-gate-observer` für Draft-PR #23 sichern. Noch keinen Market-Regime-Code beginnen; `main`, Decision Core, Shadow Gate, Telegram, Orders, Stimpy, Ren und das separate PANDO-Token-Projekt unverändert lassen.

### Durchgeführte Arbeiten

- Pflicht- und Stock-Vertragsdokumente gelesen und den vollständigen lokalen Diff geprüft.
- Alle 14 betroffenen Pfade eindeutig Stock-Pipeline, Polling/Timeout, Stock-Verification oder der dazugehörigen Kalibrierungs-/Übergabedokumentation zugeordnet.
- Secret-Musterprüfung ohne Treffer und `git diff --check` ohne Inhaltsfehler ausgeführt.
- Runtime-Preflight mit der projektlokalen Python-3.12.13-Umgebung bestanden.
- Einen in der erweiterten Testsuite sichtbaren Timing-Flake behoben: Ein einmal festgestellter Stock-Timeout bleibt nun bis zum Abschluss des nicht überlappenden Hintergrundjobs explizit markiert. Dadurch bleibt die Folgemeldung deterministisch und der tatsächliche Hintergrundjob unverändert geschützt.
- Bestehendes geprüftes BEFORE-Backup bestätigt: `C:\Users\Admin\Desktop\PandorickBackUp_2026-08-12_21-01-42_BEFORE.zip`, 1.510.376.788 Byte, 1.017 Einträge, `.git`, `docs`, `tests` und Quellcode enthalten; vollständige Testextraktion erfolgreich.
- GitHub-Authentifizierung für `cRioshy` außerhalb der Sandbox erfolgreich bestätigt. Der lokale Remote bleibt ausschließlich `https://github.com/cRioshy/Pando.git`.
- Benutzer bestätigte ausdrücklich, dass `cRioshy/Pando` das korrekte PandorickKi-Repository ist und sich die PANDO-Sperre nur auf das separate Token-Projekt bezieht.
- Produkt- und Vertragsstand als Commit `95d5d54eee01a5499e28812b41bed4c603b1c8c7` auf `agent/integrate-decision-gate-observer` gepusht. Draft-PR #23 zeigt exakt diesen Head, bleibt `OPEN`, `isDraft=true`, ungemergt und gegen `main` gerichtet. Lokal und Remote waren danach `0/0` synchron.

### Veränderte Dateien

- `AGENTS.md`
- `adapters/stock_adapter.py`
- `adapters/stock_shadow_verification_adapter.py`
- `docs/ARCHITECTURE.md`
- `docs/CURRENT_SYSTEM_STATE.md`
- `docs/KNOWN_PROBLEMS.md`
- `docs/NEXT_STEPS.md`
- `docs/SESSION_HANDOVER.md`
- `docs/STOCK_SHADOW_CANDIDATE.md`
- `docs/STOCK_SHADOW_VERIFICATION_CONTRACT.md`
- `orchestrator.py`
- `tests/test_stock_adapter.py`
- `tests/test_stock_shadow_verification_adapter.py`

### Neue Dateien

- `docs/STOCK_SHADOW_CALIBRATION_CONTRACT.md`

### Ausgeführte Befehle

- `git status`, Branch-/HEAD-/Remote-/Ahead-Behind-Prüfung und vollständige pfadweise Diff-Prüfung
- `git diff --check` und redigierte Secret-Musterprüfung
- `gh --version` und `gh auth status`
- `.venv\Scripts\python.exe scripts\runtime_preflight.py`
- gezielte `unittest`-Läufe für Stock-Adapter, Verification, Stock-Verträge und Orchestrator
- vollständige `unittest discover`-Regression

### Ausgeführte Tests und tatsächliche Testergebnisse

- Kernregression Stock-Adapter/Verification-Adapter: 12/12 bestanden in 1,815 Sekunden.
- Erweiterte Stock-/Verification-/Orchestrator-Suite: beim ersten Lauf 49/50 bestanden; der Timeout-Folgetest zeigte den beschriebenen Timing-Flake.
- Nach expliziter Timeout-Statuskorrektur: erweiterte Suite 50/50 bestanden in 5,791 Sekunden.
- Vollständige Regression: 299/299 bestanden in 49,457 Sekunden.
- Runtime-Preflight: bestanden, Python 3.12.13.
- Secret-Musterprüfung: 0 Treffer. `git diff --check`: keine Inhaltsfehler; nur erwartete LF/CRLF-Hinweise.

### Bekannte Fehler

- Der laufende siebentägige Verification-Betrieb enthält die bereits dokumentierte PC-Unterbrechung und korrelierte Wiederholungen; kein Fit oder automatische Kalibrierung zulässig.
- `SPCX` bleibt ohne belegbaren öffentlichen Quote-Zeitstempel blockiert.
- PR #23 bleibt absichtlich Draft und ungemergt.

### Getroffene Architekturentscheidungen

- Die Phase-0-Änderungen bleiben ein eigener Stock-/Polling-/Verification-Stand; keine Regime-v1-Arbeit wird in diesen Commit gemischt.
- Ein erkannter Stock-Timeout wird als expliziter Zustand geführt, bis genau der eine zulässige Hintergrundjob beendet und übernommen wurde.
- Decision Core, Shadow Gate, Outcome-Entscheidungen, Telegram und Orders bleiben unverändert.

### Nicht abgeschlossene Punkte

- Market Regime Contract v1 ist noch nicht begonnen.
- Der siebentägige Verification-Lauf wird weiterhin nur observer-only fortgeführt und später separat ausgewertet.

### Exakter nächster sinnvoller Arbeitsschritt

Den neuen Branch `agent/market-regime-contract-v1` vom gesicherten Phase-0-Head erstellen. Erst dort den observer-only Market-Regime-Vertrag implementieren; keine Verbindung zu Decision Core, Shadow Gate, Telegram oder Orders herstellen.

## Aktuelle Aufgabe: Stock-/Polling-Freeze beheben und Livebetrieb wiederherstellen

### Datum und Uhrzeit

12. August 2026, 20:21 Uhr, Europe/Berlin (`+02:00`)

### Ziel der Aufgabe

Den nach dem PC-Neustart reproduzierten Stock-Hotloop beheben, damit Web-Polling, Crypto und der Gesamtzyklus weiterlaufen. Bestehende Runtime-/History-/Lerndaten erhalten; Stock-Verification stock-only/observer-only, Telegram aus/Dry-Run und Orders gesperrt lassen.

### Durchgeführte Arbeiten

- Pflicht-, Architektur-, Problem-, Next-Steps- sowie alle relevanten Event-/Feature-/Gate-/Stock-/Shadow-/Verification-/Kalibrierungsverträge gelesen und gegen Code und Runtime geprüft.
- Festhängenden Prozess zuerst kontrolliert gestoppt; Port 8000 freigegeben.
- Regressionstest ergänzt: langsame Stock-Normalisierung muss vom Plattformzyklus entkoppelt sein.
- Gesamte blockierende Stockpipeline in genau einen nicht überlappenden Hintergrundlauf verschoben; der Produktions-Orchestrator wartet nicht darauf und übernimmt Ergebnisse im Folgetakt.
- Zweiten realen Engpass diagnostiziert: `StockShadowVerificationAdapter._handle_stock_price()` schrieb tausende fällige 24h-Outcomes synchron in einem Event.
- Outcome-Aufarbeitung chronologisch auf höchstens acht Fälle je Symbol/Quote begrenzt. Offene Fälle bleiben append-only `PENDING` und werden restart-safe weitergeführt.
- Mehrere kontrollierte Liveprüfungen ausgeführt. Zwei durch blockierte Stopverarbeitung versehentlich parallele Instanzen wurden anhand PID/Startzeit exakt identifiziert und beendet; keine Dateien gelöscht.
- Final genau eine Instanz mit dem unveränderten Verification-Fingerprint und sicheren Telegram-/Orderwerten gestartet.

### Veränderte Dateien

- `adapters/stock_adapter.py`
- `adapters/stock_shadow_verification_adapter.py`
- `orchestrator.py`
- `tests/test_stock_adapter.py`
- `tests/test_stock_shadow_verification_adapter.py`
- `docs/CURRENT_SYSTEM_STATE.md`
- `docs/ARCHITECTURE.md`
- `docs/KNOWN_PROBLEMS.md`
- `docs/NEXT_STEPS.md`
- `docs/SESSION_HANDOVER.md`

Bereits vorhandene fremde/lokale Dokumentationsänderungen wurden erhalten und nicht zurückgesetzt.

### Neue Dateien

- Keine versionierten Produktdateien außer dem bereits vorhandenen unversionierten Kalibrierungsvertrag. Nur ignorierte Runtime-Logs und freigegebene append-only Verification-Daten entstanden.

### Ausgeführte Befehle

- Read-only API-, Prozess-, Thread-, Port-, Ledger-, Storage- und Git-Prüfungen.
- Kontrollierte Stop-API; bei zwei eindeutig festhängenden Altinstanzen nach exakter PID-/Startzeitprüfung gezieltes Prozessende.
- Runtime-Preflight mit projektlokaler Python-3.12.13-Umgebung.
- Wiederholte sichere Einzelstarts mit explizit gesetzten 7-Tage-, Gate-Observer-, Telegram-aus- und Dry-Run-Werten.
- Gezielte und vollständige `unittest`-Läufe sowie `git diff --check`.

### Ausgeführte Tests und tatsächliche Ergebnisse

- Neuer Normalisierungs-Regressionstest schlug vor dem ersten Fix reproduzierbar fehl und bestand danach.
- Neuer Batch-/Restart-Test beweist: Batchgröße 1 schließt genau einen Fall, lässt zwei `PENDING`, rekonstruiert nach Neustart und schließt im nächsten Quoteevent genau den zweiten.
- Abschließende gezielte Suite: 20/20 bestanden in 5,048 Sekunden.
- Abschließende Gesamtsuite: 299/299 bestanden in 43,725 Sekunden.
- Finale Liveprüfung: genau ein Port-8000-Listener; drei Stock- und drei Cryptozyklen; `stock=OK`, `crypto=OK`, keine STALE-Dienste, `error_count=0`, Runtime-Stderr 0 Byte.
- Verification aktiv; Summary zuletzt 6.760 Fälle, 4.461 `COMPLETED`, 943 `PENDING`. `ready_for_telegram=false`, `order_execution_allowed=false`.
- Telegram `enabled=false`, `dry_run=true`, `messages_sent=0`.

### Bekannte Fehler

- Die reale PC-Unterbrechung und die während Diagnose/Neustarts entstandenen Coverage-Lücken bleiben sichtbar.
- `SPCX` bleibt ohne belegbaren öffentlichen Quote-Zeitstempel blockiert.
- Die Verification-Daten enthalten stark korrelierte Wiederholungen; keine Kalibrierung zulässig.
- Historischer `PENDING`-Rückstand wird bewusst begrenzt nachgearbeitet und darf den EventBus nicht erneut blockieren.

### Getroffene Architekturentscheidungen

- Nur der Produktions-Orchestrator setzt `StockAdapter(nonblocking_cycle=True)`; direkte Adapterverwendung behält den bisherigen wartenden Vertrag.
- Nie mehr als ein Legacy-Stocklauf gleichzeitig. Ergebnisse werden in einem Folgetakt publiziert.
- Verification-Outcomes werden nach Fälligkeit sortiert und in kleinen, festen Batches verarbeitet. Keine History-Umschreibung, keine automatische Optimierung.
- Gate, aktiver Decision-Pfad, Telegram und Orders bleiben unverändert.

### Nicht abgeschlossene Punkte

- Lauf bis zum geplanten Abschluss beobachten; keinen Fit starten.
- Lokale Code- und Dokumentationsänderungen sind noch nicht commitet oder gepusht.
- Abschlussautomation für den 17. August ist weiterhin nicht als aktive Automation bestätigt.

### Exakter nächster sinnvoller Arbeitsschritt

PandorickKi unverändert laufen lassen. Beim nächsten Statuscheck mindestens Stock-/Crypto-Zyklen, STALE, Sitzungsfehler, Verification-`PENDING`/`COMPLETED`, einen einzelnen Listener sowie Telegram-/Orderflags read-only prüfen. Am 17. August kontrolliert stoppen und nur deskriptiv nach UTC-Cutoff und kanonischer Unabhängigkeit auswerten; keinen Fit oder automatische Kalibrierung starten.

## Aktuelle Aufgabe: PandorickKi nach PC-Ausfall wieder starten

### Datum und Uhrzeit

12. August 2026, 12:51 Uhr, Europe/Berlin (`+02:00`)

### Ziel der Aufgabe

Den durch einen PC-Ausfall beendeten PandorickKi-Prozess sicher mit dem bereits freigegebenen siebentägigen Stock-Verification-Profil fortsetzen, ohne bestehende Daten, Code, persistente Konfiguration, Gate, Telegram oder Orders zu verändern.

### Durchgeführte Arbeiten

- AGENTS-, Pflichtübergabe- und Stock-Verification-/Kalibrierungsverträge vor der Ausführung gelesen und ihre Existenz/Hashes geprüft.
- Port 8000 und `/api/health` als nicht erreichbar bestätigt; keinen bestehenden Prozess vorgefunden.
- Letzten Ledger-Zeitstempel `2026-08-11T22:44:09.901899+00:00` ermittelt; bestehende append-only Daten nicht verändert.
- Runtime-Preflight aus der projektlokalen Python-3.12.13-Umgebung ausgeführt.
- PandorickKi verborgen mit denselben 7-Tage-Parametern neu gestartet: Verification an, 24h-Horizont, 0,05-%-Neutralband, Shadow 60/40, Decision-Gate-Observer 60/60/0, Telegram aus/Dry-Run.
- Health, Services, Summary, Fingerprint, Sicherheitsflags und Runtime-Stderr read-only geprüft.

### Veränderte Dateien

- `docs/CURRENT_SYSTEM_STATE.md`
- `docs/SESSION_HANDOVER.md`
- `docs/NEXT_STEPS.md`

Bereits vorhandene lokale Dokumentationsänderungen wurden erhalten. Kein Programmcode und keine persistente Konfigurationsdatei wurden verändert.

### Neue Dateien

- Nur ignorierte Runtime-Logdateien des Wiederanlaufs; keine neue versionierte Projektdatei.

### Ausgeführte Befehle

- vollständige Pflichtdatei-Lektüre/Hashprüfung, Port- und Health-Prüfung
- read-only letzte Ledgerzeit ermittelt
- `.venv\\Scripts\\python.exe scripts/runtime_preflight.py`
- verborgener `Start-Process` mit expliziten sicheren 7-Tage-Umgebungswerten
- wiederholte GET-Abfragen von `/api/health`, `/api/status`, `/api/config/public` und `/api/shadow-verification/summary`

### Ausgeführte Tests und tatsächliche Testergebnisse

- Runtime-Preflight: bestanden.
- Neustart: Health `OK`, Web aktiv, Verification-Service `OK` und `enabled=true`.
- Fingerprint unverändert: `3d23f923d6b9d9dc3019457afcb078591b5d8c8b4d1f4f4db55911724fa71747`.
- Beim ersten Snapshot 6.737 Fälle gesamt: 1.104 `COMPLETED`, 4.280 `PENDING`, 1.353 `UNKNOWN`; neuer Fallzeitstempel `2026-08-12T10:51:30.239422+00:00`.
- Telegram `enabled=false`, `dry_run=true`; `ready_for_telegram=false`, `order_execution_allowed=false`.
- Runtime-Stderr nach Neustart: 0 Byte.
- Der erste Stock-Zyklus blieb bei der letzten Prüfung länger als drei Minuten `RUNNING`; API, Verification und die übrigen Services blieben erreichbar. Noch kein bestätigter Fehler.

### Bekannte Fehler

- Ungefähr zwölf Stunden und sieben Minuten Erfassungslücke durch den PC-Ausfall; keine Datenkorruption festgestellt.
- Erster öffentlicher Stock-Zyklus nach Wiederanlauf noch nicht als `OK` abgeschlossen. Nur bei Fortbestand diagnostizieren; keinen harten Prozessabbruch vornehmen.
- `SPCX` bleibt als bekannte öffentliche Datenlücke separat blockiert.

### Getroffene Architekturentscheidungen

- Keine Architekturänderung. Der bestehende append-only/restart-safe Verification-Adapter setzt denselben Lauf mit demselben Fingerprint fort.
- Die reale PC-Unterbrechung wird bei der Abschlussauswertung als Coverage-Lücke ausgewiesen und nicht künstlich aufgefüllt.

### Nicht abgeschlossene Punkte

- Regulären Abschluss des ersten Stock-Zyklus nach dem Neustart bestätigen.
- Die zuvor vorbereitete Abschlussautomation für den 17. August ist weiterhin nicht als aktive Automation gespeichert und muss separat bestätigt beziehungsweise erneut vorbereitet werden.
- Sieben-Tage-Lauf bis zum geplanten Abschluss weiter beobachten; kein Fit oder automatische Kalibrierung.
- Lokale Dokumentationsänderungen bleiben uncommitted und ungepusht.

### Exakter nächster sinnvoller Arbeitsschritt

Stock-Service und Ledger erneut read-only prüfen. Wenn der Zyklus regulär auf `OK` wechselt, PandorickKi unverändert weiterlaufen lassen. Falls `RUNNING` fortbesteht, nur die öffentlichen Provider-/Timeoutpfade diagnostizieren. Danach den kontrollierten Abschluss am 17. August erneut als einmalige Automation vorbereiten und bestätigen lassen.

## Aktuelle Aufgabe: siebentägigen Stock-Verification-Lauf starten

### Datum und Uhrzeit

10. August 2026, 19:03 Uhr, Europe/Berlin (`+02:00`)

### Ziel der Aufgabe

Den ausdrücklich freigegebenen siebentägigen Stock-only Verification-Lauf kontrolliert mit unverändertem Fingerprint starten, Sicherheitsgrenzen verifizieren und einen kontrollierten Abschluss nach mindestens sieben Tagen vorbereiten. Kein Fit, keine Kalibrierung, keine Gate-, Telegram- oder Orderänderung.

### Durchgeführte Arbeiten

- Laufenden normalen Dienst und öffentliche Konfiguration read-only geprüft: 60-Sekunden-Zyklus, Verification aus, Telegram aus/Dry-Run.
- Laufenden Prozess ausschließlich über `POST /api/control/stop` geordnet beendet und Port 8000 vollständig freigegeben.
- Runtime-Preflight mit projektlokaler Python-3.12.13-Umgebung bestanden.
- PandorickKi verborgen mit öffentlichen Live-Marktdaten, Stock-Datenobserver, Decision-Gate-Observer 60/60/0 und Stock-Verification aktiviert neu gestartet.
- Verification-Policy explizit auf 86.400 Sekunden und 0,05 Prozent gesetzt; Stock-/Risk-Parameter unverändert gelassen.
- Health, zwölf Services, öffentliche Konfiguration, Verification-Summary, Sicherheitsflags, Ledger und Runtime-Stderr geprüft.
- Einmalige Abschlussautomation für 17. August 2026, 19:10 Uhr Europe/Berlin vorbereitet; App-Bestätigung steht beim Schreiben dieses Eintrags noch aus.

### Veränderte Dateien

- `docs/CURRENT_SYSTEM_STATE.md`
- `docs/SESSION_HANDOVER.md`
- `docs/KNOWN_PROBLEMS.md`
- `docs/NEXT_STEPS.md`
- `docs/STOCK_SHADOW_VERIFICATION_CONTRACT.md`
- `docs/STOCK_SHADOW_CALIBRATION_CONTRACT.md`

Bereits vorhandene lokale Dokumentationsänderungen wurden erhalten. Kein Programmcode und keine persistente Konfigurationsdatei wurden verändert.

### Neue Dateien

- Keine versionierten Projektdateien. Nur ignorierte Runtime-Logdateien und append-only Verification-Ledgerdaten entstanden im freigegebenen Betrieb.

### Ausgeführte Befehle

- read-only GET auf `/api/status`, `/api/config/public`, `/api/health` und `/api/shadow-verification/summary`
- kontrolliertes `POST /api/control/stop` und Portfreigabeprüfung
- `.venv\\Scripts\\python.exe scripts/runtime_preflight.py`
- verborgener Start von `.venv\\Scripts\\python.exe main.py --headless --web` mit expliziten sicheren Umgebungswerten
- read-only PowerShell-Auswertung des Verification-Ledgers und der Runtime-Logs
- Vorbereitung einer einmaligen lokalen Abschlussautomation

### Ausgeführte Tests und tatsächliche Testergebnisse

- Runtime-Preflight: bestanden.
- Kontrollierter Stop: akzeptiert, Port vollständig freigegeben.
- Neustart: Health `OK`, Web/WebSocket/Statistik aktiv.
- Nach zwei vollständigen 60-Sekunden-Zyklen: alle zwölf Services `OK`, zehn neue `VERIFICATION_CREATED`, zehn neue `LEGACY_DECISION_LINKED`, ein Fingerprint.
- Zwölf neue `OUTCOME_COMPLETED`-Ledgerzeilen vervollständigten erwartungsgemäß die am 9. August angelegten, nun mehr als 24 Stunden alten Kurzlauffälle; sie gehören nicht zur neuen Laufkohorte.
- Fingerprint: `3d23f923d6b9d9dc3019457afcb078591b5d8c8b4d1f4f4db55911724fa71747`.
- Runtime-Stderr: 0 Byte.
- Verification `enabled=true`; `ready_for_telegram=false`, `order_execution_allowed=false`, `affects_active_decision=false`.

### Bekannte Fehler

- Keine neue Runtime-Störung beim Start.
- `SPCX` bleibt ohne belegbaren öffentlichen Quote-Zeitstempel `UNKNOWN`/blockiert.
- Kurzlauf- und Sieben-Tage-Laufdaten teilen denselben Fingerprint; Abschlussauswertung muss deshalb zusätzlich den UTC-Start-Cutoff `2026-08-10T17:03:44Z` verwenden.

### Getroffene Architekturentscheidungen

- Keine Architekturänderung. Der vorhandene optionale Verification-Adapter wurde für den freigegebenen Zeitraum aktiviert.
- Der Prozess schreibt ausschließlich append-only und bleibt stock-only/observer-only.
- Die Abschlussauswertung trennt Kohorten zeitlich und dedupliziert erst für die Kalibrierungsbewertung nach dem bestätigten Vertrag.

### Nicht abgeschlossene Punkte

- Lauf muss bis mindestens 17. August 2026, 19:10 Uhr Europe/Berlin weiterlaufen.
- Abschlussautomation muss noch in der App bestätigt werden.
- Kein Fit und keine Kalibrierung erlaubt oder begonnen.
- Lokale Dokumentationsänderungen bleiben uncommitted und ungepusht.

### Exakter nächster sinnvoller Arbeitsschritt

Die eingeblendete Abschlussautomation bestätigen. PandorickKi anschließend unverändert laufen lassen. Am 17. August vor dem kontrollierten Stop Abschlusswerte erfassen, danach Portfreigabe prüfen und ausschließlich Fälle ab `2026-08-10T17:03:44Z` sowie kanonisch unabhängige Outcomes deskriptiv auswerten; keinen Fit starten.

## Aktuelle Aufgabe: unabhängigen Stock-Shadow-Kalibrierungsvertrag entwerfen

### Datum und Uhrzeit

10. August 2026, 18:48 Uhr, Europe/Berlin (`+02:00`)

### Ziel der Aufgabe

Auf Basis des tatsächlichen Stock-Shadow-Scores, des vorhandenen 24h-Verification-Outcomes und der heutigen US-Marktphasenmessung einen unabhängigen Confidence-/Score-Kalibrierungsvertrag entwerfen und reviewen. Nur Dokumentation ändern; keinen Programmcode, Prozess, Gate-, Telegram-, Order- oder Verification-Betrieb verändern.

### Durchgeführte Arbeiten

- Pflicht-, Event-, Feature-, Gate-, Stock-Data-, Shadow-Candidate-, Shadow-Risk- und Verification-Verträge vollständig gelesen und gegen die tatsächlichen Producer/Consumer geprüft.
- Tatsächliche Scoreformel mit fünf Komponenten, `UNVALIDATED_HEURISTIC_SCORE`, Brain-Confidence-Kopie, Verification-ID und 24h-Outcome nachvollzogen.
- Vertrag `pandorickki.stock-shadow-calibration` Version 1 als reine Dokumentations- und Reviewgrenze erstellt.
- Rohscore, directional Score, kalibrierte Erfolgswahrscheinlichkeit und unabhängige Evidenz-Confidence eindeutig getrennt.
- Kanonische Deduplizierung wiederholter Tageskerzen, chronologische Fit-/Holdout-Trennung, Mindestabdeckung, Metriken, Artefaktfelder und Reason Codes festgelegt.
- Heutige Marktphasenmessung reviewt: trotz 20 berechneter Shadows null abgeschlossene unabhängige 24h-Verification-Outcomes; Status verbindlich `INSUFFICIENT_DATA`.
- Benutzer bestätigte am 10. August 2026 die vorgeschlagenen Mindestabdeckungen und Sicherheitsgrenzen ausdrücklich; keine Laufzeitfreigabe daraus abgeleitet.
- AGENTS-, Systemzustands-, Architektur-, Problem- und Next-Steps-Dokumentation entsprechend nachgeführt.
- Laufenden Dienst, Konfiguration, Runtime-/History-/Learning-Daten und sämtliche produktiven Pfade unangetastet gelassen.

### Veränderte Dateien

- `AGENTS.md`
- `docs/CURRENT_SYSTEM_STATE.md`
- `docs/ARCHITECTURE.md`
- `docs/KNOWN_PROBLEMS.md`
- `docs/NEXT_STEPS.md`
- `docs/SESSION_HANDOVER.md`
- `docs/STOCK_SHADOW_CANDIDATE.md`
- `docs/STOCK_SHADOW_VERIFICATION_CONTRACT.md`

Die vier bereits durch die automatische Marktphasenanalyse lokal geänderten Pflichtdokumente wurden erhalten und nur additiv ergänzt.

### Neue Dateien

- `docs/STOCK_SHADOW_CALIBRATION_CONTRACT.md`

### Ausgeführte Befehle

- vollständige `Get-Content`-Lektüre aller Pflicht- und relevanten Vertragsdokumente
- `rg`-/`Get-Content`-Prüfung von Shadow-Score, Verification-Outcome, Brain-Confidence, Gate und Tests
- `git status --short` zur Scopekontrolle
- abschließende Markdown-, Referenz- und `git diff --check`-Prüfung
- abschließende read-only Abfrage von `/api/health` und `/api/shadow-verification/summary`

### Ausgeführte Tests und tatsächliche Testergebnisse

- Kein Programmcode geändert; daher keine Softwaretests ausgeführt.
- Dokumentations- und Referenzprüfung: bestanden.
- `git diff --check`: keine Inhaltsfehler; ausschließlich erwartete Windows-LF/CRLF-Hinweise.
- Kein Neustart und kein zusätzlicher Livezyklus ausgeführt. Abschließende read-only Runtime-Prüfung: Health `OK`, Web aktiv, Verification `enabled=false`, `ready_for_telegram=false`, `order_execution_allowed=false`.

### Bekannte Fehler

- Neu dokumentiert als KP-024: Stock-Shadow-Score ist unkalibriert; aktuelle unabhängige abgeschlossene Outcome-Stichprobe ist null.
- KP-021 bleibt bestehen: Brain-Confidence ist weiterhin nur eine Kopie von Probability.
- KP-023 bleibt bestehen: Outcomes sind 24h-Forward-Mark-to-Market und kein Stop-/Zielpfad-Backtest.

### Getroffene Architekturentscheidungen

- Kalibrierung ist eine spätere offline ausgeführte, versionierte und append-only Observer-Auswertung, keine Laufzeitkomponente.
- Mehrere Zyklen derselben Tageskerze zählen höchstens einmal je Symbol/Policy/Version/Fingerprint.
- `calibrated_probability` misst ausschließlich den richtungsbezogenen 24h-WIN oberhalb des Neutralbands.
- Evidenz-Confidence bleibt kategorial mit Stichprobenumfang/Unsicherheit und wird nicht aus Probability kopiert oder an das heutige Gate übergeben.
- Auch ein später `VALIDATED_OBSERVER` genanntes Artefakt setzt keine Telegram- oder Orderfreigabe.

### Nicht abgeschlossene Punkte

- Keine Kalibrierungsimplementierung und kein Fit erstellt.
- Vertragsgrenzen von 400 unabhängigen Fällen, 100 je Richtung, 30 Handelstagen, vier Symbolen und 40 Fällen je Bucket sind bestätigt.
- Siebentägiger Verification-Lauf weiterhin nicht gestartet.
- Dokumentationsänderungen aus Marktphasenanalyse und diesem Vertrag sind lokal, uncommitted und nicht gepusht.

### Exakter nächster sinnvoller Arbeitsschritt

Den Vertrag und insbesondere die vorgeschlagenen Mindestabdeckungen reviewen. Erst nach ausdrücklicher Bestätigung den ungefähr siebentägigen Stock-Verification-Lauf mit stabilem Konfigurationsfingerprint separat freigeben; danach nur Datenqualität, unabhängige Fälle und Outcome-Abdeckung auswerten und bei unzureichender Stichprobe weiterhin nichts fitten.

## Aktuelle Aufgabe: US-Marktphase observer-only auswerten

### Datum und Uhrzeit

10. August 2026, 18:13 Uhr, Europe/Berlin (`+02:00`)

### Ziel der Aufgabe

Den laufenden lokalen Dienst während der geöffneten US-Marktphase über mindestens fünf vollständige Stockzyklen ausschließlich lesend auf Health, Freshness, Shadow-/Risikoplan-/Datenverteilung und Sicherheitsgrenzen prüfen. Keine Prozesse, Runtime-Daten, Konfiguration, Gate-, Telegram- oder Orderfunktion verändern.

### Durchgeführte Arbeiten

- `AGENTS.md`, alle fünf Pflichtdokumente sowie Event-, Feature-, Gate- und sämtliche Stock-Verträge vollständig gelesen.
- Erreichbarkeit von `http://127.0.0.1:8000` vor jeder Runtime-Arbeit bestätigt; keinen Prozess gestartet, gestoppt oder neu konfiguriert.
- Baseline bei Stockzyklus 1204/6.020 publizierten Ergebnissen aufgenommen und die vollständigen Abschlüsse 1205 bis 1209 anhand von jeweils fünf zusätzlichen publizierten Stock-Ergebnissen erfasst.
- Pro Abschluss Plattform-/Service-Health, Sitzungsfehler, STALE, Stock-Zähler, Quote-Zeitstempel/Freshness, Telegram, NeuroBrain, Fehlerjournal und Gate read-only erfasst.
- Aktive Stock-Projektion und aktuelle kompakte Brain-/Decision-/Gate-Beispiele auf Observerfelder und Sicherheitsflags geprüft.

### Veränderte Dateien

- `docs/CURRENT_SYSTEM_STATE.md`
- `docs/SESSION_HANDOVER.md`
- `docs/KNOWN_PROBLEMS.md`
- `docs/NEXT_STEPS.md`

### Neue Dateien

- Keine.

### Ausgeführte Befehle

- Vollständige `Get-Content`-Lektüre der Pflicht- und Vertragsdokumente.
- `rg`-/`Get-Content`-Prüfung der relevanten Stock-, API-, Orchestrator- und Vertragscodepfade.
- Wiederholte read-only GET-Abrufe von `/api/health`, `/api/status`, `/api/events` und `/api/config/public`.
- Read-only Stichproben aus neuen Brain-, Decision- und Decision-Gate-Ledgerzeilen.
- `git status --short` und abschließende Dokumentationsprüfung.

### Ausgeführte Tests und tatsächliche Testergebnisse

- Keine Softwaretests, weil kein Programmcode geändert wurde.
- Messfenster: 18:05:44 bis 18:11:32 Uhr Europe/Berlin; fünf vollständige Stockzyklen, 25 publizierte Ergebnisse/Audits.
- Health: Plattform und Stock durchgehend gesund; 0 Sitzungsfehler, 0 STALE. Punktuelle 10 `OK` + 1 `RUNNING` entsprachen einem normal laufenden parallelen Adapterzyklus, nicht einem Fehler.
- Shadows: 20 berechnet = 10 LONG, 5 SHORT, 5 HOLD; weitere 5 `SPCX` ohne berechenbaren Shadow.
- Risiko: 15 berechnete Pläne, 10 Blocks = 5 HOLD plus 5 `SPCX`.
- Stock-Daten: 15 `READY`, 10 `BLOCKED`. Je Zyklus waren drei LONG/SHORT-Fälle bereit; HOLD und `SPCX` blockierten fail-closed.
- Quotes: AAPL/MSFT/NVDA/TSLA in allen 20 Beobachtungen `ok` von `yahoo_finance_chart`, Alter 8,737 bis 19,505 Sekunden. Erster beobachteter Bereich 16:06:24 bis 16:06:27 UTC, letzter 16:11:13 bis 16:11:22 UTC. `SPCX` fünfmal ohne Preis/Zeitstempel.
- Verfügbare letzte SPCX-Datengründe: `SD_DIRECTION_NOT_ELIGIBLE`, `SD_CANDLES_MISSING`, `SD_PRICE_INVALID`, `SD_PRICE_SOURCE_NOT_ALLOWED`, `SD_PRICE_TIMESTAMP_INVALID`, `SD_RISK_MISSING`; letzter Risikogrund `SSR_SHADOW_NOT_CALCULATED`. HOLD blockiert vertraglich mit ungeeigneter Richtung beziehungsweise fehlendem Risikoplan.
- NeuroBrain: Queue 0, Drops/fehlgeschlagene Events/Status-/Benachrichtigungsfehler jeweils 0. Fehlerjournal unverändert 191 Ereignisse, 10 Fingerprints, 0 Schreibfehler.
- Sicherheit: aktive Stock-Sicht ohne `stock_shadow*`, `stock_data_audit` oder `stock_candle*`; Telegram durchgehend aus/Dry-Run/0 Sendungen; Verification deaktiviert und Telegram-/Orderflags false.

### Bekannte Fehler

- Keine neue Runtime-Störung.
- `SPCX` besitzt weiterhin keinen belegbaren öffentlichen Ticker und bleibt korrekt blockiert.
- Der Shadow-Score bleibt unkalibriert; Confidence ist weiterhin nicht unabhängig.

### Getroffene Architekturentscheidungen

- Keine. Die Messung war ausschließlich observer-only und read-only.

### Nicht abgeschlossene Punkte

- Keine Confidence-/Score-Kalibrierung, Gate-Umschaltung, Telegram-Kopplung, Orderfunktion oder siebentägige Verification begonnen.

### Exakter nächster sinnvoller Arbeitsschritt

Auf Basis dieser Marktphasenverteilung einen separaten fachlichen Vertrag für unabhängige Confidence beziehungsweise ehrliche Score-Kalibrierung entwerfen und zunächst nur reviewen; `SPCX` weiter blockieren und Gate, Telegram, Orders sowie siebentägige Verification unverändert lassen.

## Aktuelle Aufgabe: Stock-Verification veröffentlichen und PR als Draft sichern

### Datum und Uhrzeit

9. August 2026, 19:25 Uhr, Europe/Berlin (`+02:00`)

### Ziel der Aufgabe

Den vollständig geprüften lokalen Stock-Live-Shadow-Verification-Stand auf dem bestehenden Arbeitsbranch veröffentlichen, Draft-PR #23 aktualisieren und `main` unverändert lassen.

### Durchgeführte Arbeiten

- Arbeitsbaum, Branch, Remote, ignorierte Runtime-Dateien und Veröffentlichungsscope geprüft.
- Vollständige Tests, Syntax-, Diff-, Secret- und Runtime-Health-Prüfung erneut ausgeführt.
- Ausschließlich die vorgesehenen 24 Code-, Test-, Konfigurations- und Dokumentationsdateien explizit gestaged.
- Implementierungscommit `53f1c8fe650889aff2d867f7f9dc75ac9799184a` erstellt und auf `origin/agent/integrate-decision-gate-observer` gepusht.
- PR #23 wieder auf Draft gesetzt und Titel/Beschreibung auf Stock-Pipeline plus Shadow-Verification aktualisiert.
- `main` weder ausgecheckt noch verändert oder gemergt.

### Veränderte Dateien

- In diesem Abschluss ausschließlich `docs/SESSION_HANDOVER.md` und `docs/NEXT_STEPS.md`; der vorherige Commit enthält die bereits dort vollständig aufgelisteten 24 Implementierungsdateien.

### Neue Dateien

- Keine zusätzlichen Dateien in diesem Abschluss.

### Ausgeführte Befehle

- `gh --version`, `gh auth status`, `git status -sb`, `git remote -v`, `git diff --name-status`, `git diff --stat`, `git diff --check`
- `.venv\\Scripts\\python.exe -m unittest discover -s tests -q`
- `python -m py_compile ...`, `node --check web/static/control_center.js`
- Secret-Scan über alle geänderten und nicht ignorierten neuen Dateien
- explizites `git add`, `git diff --cached --check`, `git commit`, `git push -u origin agent/integrate-decision-gate-observer`
- `gh pr ready 23 --undo`, `gh pr edit 23 ...`, `gh pr view 23 ...`

### Ausgeführte Tests und tatsächliche Testergebnisse

- Vollständige Suite: 297/297 Tests in 55,246 Sekunden bestanden.
- Python- und JavaScript-Syntax: bestanden.
- Arbeitsbaum- und Staging-Diffprüfung: keine Inhaltsfehler; nur erwartete Windows-LF/CRLF-Hinweise.
- Secret-Scan: null Treffer.
- Laufender PandorickKi-Dienst nach der Prüfung weiterhin Health `OK`.
- GitHub: PR #23 `OPEN`, `isDraft=true`, `CLEAN` und `MERGEABLE` gegen `main`.

### Bekannte Fehler

- Keine neuen Fehler bei Veröffentlichung oder PR-Aktualisierung.
- Bereits dokumentierte KP-019-Cleanupfluktuation und Stock-Datengrenzen bleiben unverändert.

### Getroffene Architekturentscheidungen

- Keine zusätzliche Architekturänderung durch die Veröffentlichung.
- Verification bleibt standardmäßig deaktiviert, stock-only und observer-only.

### Nicht abgeschlossene Punkte

- Draft-PR #23 ist absichtlich nicht gemergt.
- Siebentägiger Verification-Lauf wurde weiterhin nicht gestartet.
- Zwölf Kurzlauffälle bleiben bis zu einem ausreichend späten öffentlichen Quote `PENDING`.

### Exakter nächster sinnvoller Arbeitsschritt

Draft-PR #23 in Ruhe prüfen. Nicht mergen und den siebentägigen Lauf nicht automatisch starten. Erst nach eigener ausdrücklicher Laufzeitfreigabe Verification mit unverändertem Konfigurationsfingerprint aktivieren und nach ungefähr sieben Tagen wieder stoppen und auswerten.

## Aktuelle Aufgabe: Control Center nach kontrolliertem Stop wieder starten

### Datum und Uhrzeit

9. August 2026, 18:23 Uhr, Europe/Berlin (`+02:00`)

### Ziel der Aufgabe

PandorickKi nach dem vereinbarten Ende des kurzen Stock-Verification-Laufs wieder im normalen Dauerbetrieb unter `http://127.0.0.1:8000/` bereitstellen, ohne den siebentägigen Verification-Lauf oder Telegram-/Orderfreigaben zu aktivieren.

### Durchgeführte Arbeiten

- Pflichtdokumentation und tatsächlichen Webstarter geprüft.
- Bestätigt, dass Port 8000 vor dem Start nicht belegt war.
- PandorickKi verborgen im Hintergrund mit Live-Crypto, Live-Stocks, NeuroBrain und observer-only Decision Gate gestartet.
- `PANDORICKKI_STOCK_SHADOW_VERIFICATION_ENABLED=0`, Telegram deaktiviert und Dry-Run ausdrücklich gesetzt.
- Health-, Status- und Verification-Summary-API read-only geprüft.

### Veränderte Dateien

- `docs/SESSION_HANDOVER.md`
- `docs/NEXT_STEPS.md`

### Neue Dateien

- Zwei ignorierte leere Runtime-Logdateien unter `runtime_logs/` für Standardausgabe und Standardfehler des Hintergrundprozesses.

### Ausgeführte Befehle

- Pflichtdokumente und `start_pandorick_web.bat` mit PowerShell gelesen.
- Port 8000 mit `Get-NetTCPConnection` geprüft.
- Projektlokales `.venv\\Scripts\\python.exe main.py --headless --web` über verborgenen `Start-Process` gestartet.
- `GET /api/health`, `GET /api/status` und `GET /api/shadow-verification/summary?days=7&limit=1` aufgerufen.

### Ausgeführte Tests und tatsächliche Testergebnisse

- Kein Code geändert; daher keine neue Code-Testsuite erforderlich.
- Runtime-Health: `OK`; `web_running`, `websocket_active` und `statistics_active` sind `true`.
- Alle elf normalen Services melden `OK`.
- Stock-Verification meldet `enabled=false`, Stock-only/observer-only und null Fälle dieses normalen Starts.
- `ready_for_telegram=false` und `order_execution_allowed=false`.
- Unmittelbare Veröffentlichungskontrolle des gesamten lokalen Verification-Stands: 297/297 Tests in 55,246 Sekunden bestanden; Python-/JavaScript-Syntax und `git diff --check` bestanden, Secret-Scan ohne Treffer, Runtime anschließend weiterhin `OK`.

### Bekannte Fehler

- Keine neuen Fehler beim Neustart festgestellt.
- Die bereits dokumentierten bekannten Probleme bleiben unverändert.

### Getroffene Architekturentscheidungen

- Keine Architekturänderung.
- Normaler Dauerbetrieb bleibt vom separat freizugebenden siebentägigen Verification-Lauf getrennt.

### Nicht abgeschlossene Punkte

- Lokale Stock-Verification-Änderungen sind weiterhin nicht committed oder gepusht.
- Der siebentägige Verification-Lauf wurde weiterhin nicht gestartet.

### Exakter nächster sinnvoller Arbeitsschritt

Control Center im bereits geöffneten Browser neu laden. Danach entweder PandorickKi normal weiterlaufen lassen oder nach separater Freigabe den Implementierungsstand committen und Draft-PR #23 aktualisieren; den siebentägigen Lauf weiterhin nicht ohne eigene ausdrückliche Freigabe starten.

## Aktuelle Aufgabe: Stock-only Live-Shadow-Verification implementieren

### Datum und Uhrzeit

9. August 2026, 17:45 Uhr, Europe/Berlin (`+02:00`)

### Ziel der Aufgabe

Eine ausschließlich beobachtende Stock-Live-Shadow-Verification mit zuerst definiertem Verification-/Outcome-Vertrag, append-only/restart-safe/idempotenter Persistenz, read-only API/UI und kurzem kontrolliertem Lauf implementieren. Crypto, produktive Decisions, bestehende Outcomes, Learning, Telegram, Orders und `main` unverändert lassen; keinen siebentägigen Lauf starten.

### Durchgeführte Arbeiten

- Pflicht-, Event-, Learning-, Feature-, Gate- und alle Stock-Verträge vollständig gelesen und gegen Codepfade geprüft.
- Vor Änderungen den tatsächlichen Legacy-, Shadow-, ID-, Outcome-, Storage- und Control-Center-Fluss dokumentiert.
- Vertrag `pandorickki.stock-shadow-verification` Version 1 erstellt.
- Deterministische `verification_id` aus Symbol, Quell-/Quote-/Kerzenzeit, Observer-Version und secret-freiem Konfigurationsfingerprint umgesetzt.
- Getrennte Legacy-/Shadow-Ergebnisse mit festem 24h-Forward-Mark-to-Market und 0,05-%-Neutralband implementiert; strikt späterer Quote-Zeitstempel erforderlich.
- `StockAdapter` um separates kompaktes `STOCK_SHADOW_OBSERVED` mit gemeinsamer `source_event_id` ergänzt; aktiver `STOCK_ANALYSIS_FINISHED`-Payload bleibt frei von Shadow-/Auditfeldern.
- Optionalen `StockShadowVerificationAdapter` mit append-only Recordtypen, Ledger-Rotation, Archivlimit, Restart-Rekonstruktion, Source-Alias-, Decision-, Tracker- und Outcome-Verknüpfung ergänzt.
- Crypto-Events werden ausdrücklich ignoriert; unbekannte/HOLD-Daten bleiben `UNKNOWN`.
- Read-only Summary `GET /api/shadow-verification/summary?days=7`, Detailroute und Control-Center-Bereich ergänzt.
- Normalen Starter bewusst nicht aktiviert; `.env.example` dokumentiert sichere deaktivierte Standards.
- Laufenden Altprozess kontrolliert über die Websteuerung gestoppt.
- Neuen Stand mit genau drei Livezyklen und temporär aktivierter Verification ausgeführt; Prozess stoppte danach selbst.
- Ledger anschließend read-only auf Einträge, Eindeutigkeit, Stock-Scope, Sicherheitsflags und verbotene Bulkfelder geprüft.
- Draft-PR #23 blieb Draft; kein Commit, Push, Merge oder `main`-Eingriff in dieser Aufgabe.

### Veränderte Dateien

- `.env.example`
- `AGENTS.md`
- `adapters/stock_adapter.py`
- `config.py`
- `orchestrator.py`
- `docs/ARCHITECTURE.md`
- `docs/CURRENT_SYSTEM_STATE.md`
- `docs/EVENT_PAYLOAD_CONTRACT.md`
- `docs/KNOWN_PROBLEMS.md`
- `docs/NEXT_STEPS.md`
- `docs/SESSION_HANDOVER.md`
- `tests/test_config.py`
- `tests/test_stock_adapter.py`
- `tests/test_web_control_center.py`
- `web/api.py`
- `web/routes.py`
- `web/static/control_center.css`
- `web/static/control_center.html`
- `web/static/control_center.js`

### Neue Dateien

- `stock_shadow_verification_contract.py`
- `adapters/stock_shadow_verification_adapter.py`
- `docs/STOCK_SHADOW_VERIFICATION_CONTRACT.md`
- `tests/test_stock_shadow_verification_contract.py`
- `tests/test_stock_shadow_verification_adapter.py`

### Ausgeführte Befehle

- vollständige `Get-Content`-/`rg`-Prüfung der Pflichtdokumente, Verträge und relevanten Codepfade
- `git status -sb`, `git branch --show-current`, `git remote -v`, `git diff --stat`, `git diff --check`
- `python -m py_compile ...`
- `node --check web/static/control_center.js`
- gezielte und vollständige `python -m unittest`-Läufe
- kontrollierter `POST /api/control/stop` mit Portfreigabeprüfung
- temporär konfigurierter `python main.py --headless --web --cycles 3 --interval 1`
- read-only PowerShell-Auswertung von `data/stock_shadow_verification.jsonl`

### Ausgeführte Tests und tatsächliche Ergebnisse

- Gezielte Suite: 34/34 bestanden.
- Vollständige Suite: abschließender Lauf 297/297 bestanden in 42,693 Sekunden. Ein dazwischenliegender Lauf traf einmalig den bereits dokumentierten KP-019-Windows-Fehler (`WinError 145`) beim `TemporaryDirectory`-Cleanup des Learning-Report-Tests; der betroffene Test bestand anschließend isoliert mit 1/1 und die unmittelbar folgende vollständige Suite mit 297/297. Ein früherer vollständiger Lauf hatte ebenfalls 297/297 bestanden.
- Python-Syntaxprüfung: bestanden.
- JavaScript `node --check`: bestanden.
- `git diff --check`: keine Inhaltsfehler, nur erwartete Windows-LF/CRLF-Hinweise.
- Kontrollierter Lauf: Exit 0, Health `OK`; zwölf Dienste einschließlich Verification `OK`.
- Ledger: 30 append-only Einträge, davon 15 `VERIFICATION_CREATED` und 15 `LEGACY_DECISION_LINKED`; 15 eindeutige Stockfälle, ein Konfigurationsfingerprint.
- Verteilung: Qualität 9 `DEGRADED`, 6 `REJECTED`; Legacy 13 HOLD/2 LONG; Shadow 6 LONG/3 SHORT/3 HOLD/3 unbekannt; Gate 9 BLOCK/3 HOLD/3 UNKNOWN; Vergleich 9 `LEGACY_HOLD_SHADOW_ACTION`, 3 MATCH, 3 UNCOMPARABLE.
- Outcome: 12 PENDING; drei `SPCX`-Fälle wegen fehlender öffentlicher Daten UNKNOWN. Aufgrund 24h-Horizont erwartungsgemäß noch keine abgeschlossenen Forward-Outcomes.
- Keine `candles`-Liste und kein `raw_result` im Ledger; alle Telegram-, Order- und Active-Decision-Flags false.
- Port 8000 nach dem Lauf geschlossen; kein Dauer- oder 7-Tage-Prozess aktiv.

### Bekannte Fehler

- Zwei historische beschädigte Stock-Backup-JSONs bleiben unverändert.
- `SPCX` besitzt weiterhin keinen belegbaren öffentlichen Ticker und bleibt UNKNOWN/REJECTED.
- Version-1-Outcome ist absichtlich Forward-Mark-to-Market und kein Stop-/Zielpfad-Backtest.
- KP-019 trat in einem dazwischenliegenden Gesamtlauf einmalig als `WinError 145` beim `TemporaryDirectory`-Cleanup des Learning-Report-Tests auf; der isolierte Test und die unmittelbare vollständige Wiederholung bestanden. Nur bei erneuter Reproduktion weiter instrumentieren.

### Getroffene Architekturentscheidungen

- Stock-only; keine vorgetäuschte Crypto-Shadow-Auswertung.
- Eigenes append-only Verification-Ledger statt Umschreiben von Legacy-, Decision- oder Outcome-History.
- Gemeinsame `source_event_id` als primäre technische Verbindung; deterministische fachliche Fall-ID für Restart-Idempotenz.
- Bestehende `decision_id` und Tracker-Outcomes nur read-only additiv verknüpfen.
- Legacy und Shadow getrennt bewerten; fehlende Daten nie als Erfolg zählen.
- Diskrete Quotes erlauben nur Forward-Mark-to-Market, keine Behauptung über Stop-/Zielberührungen.
- API/UI verwenden bestehende REST-, WebSocket-, Polling- und Reconnect-Architektur und übertragen keine Rohkerzen.
- Feature ist standardmäßig deaktiviert; Aktivierung nur für ausdrücklich freigegebene Läufe.

### Nicht abgeschlossene Punkte

- Änderungen sind noch nicht committed oder gepusht; Draft-PR #23 enthält diesen neuen lokalen Stand noch nicht.
- Siebentägiger Live-Shadow-Lauf wurde nicht gestartet.
- 12 Kurzlauffälle bleiben bis zu einem strikt späteren Quote nach Ablauf des 24h-Horizonts PENDING.
- Keine Confidence-Kalibrierung, Gate-Umschaltung, Telegram-Kopplung oder Orderfunktion.

### Exakter nächster sinnvoller Arbeitsschritt

Den vorliegenden Implementierungs- und Kurzlaufbericht prüfen. Nach separater Freigabe zuerst den vollständigen Diff-/Secret-Scope erneut prüfen, den Stand auf demselben Arbeitsbranch committen und Draft-PR #23 aktualisieren. Den ungefähr siebentägigen Verification-Lauf erst nach einer weiteren ausdrücklichen Laufzeitfreigabe mit unverändertem Konfigurationsfingerprint aktivieren.

## Aktuelle Aufgabe: Observer-only Stock-Pipeline veröffentlichen

### Datum und Uhrzeit

9. August 2026, 17:01 Uhr, Europe/Berlin (`+02:00`)

### Ziel der Aufgabe

Den bereits implementierten und geprüften öffentlichen Stock-Daten-, Vertrags-, Shadow- und Risikostand kontrolliert auf dem bestehenden Arbeitsbranch veröffentlichen und als Draft-PR gegen `main` bereitstellen. Keine Änderung oder Zusammenführung von `main`.

### Durchgeführte Arbeiten

- GitHub-Anmeldung für `cRioshy` außerhalb der eingeschränkten Netzwerkumgebung erfolgreich verifiziert.
- Den Veröffentlichungsscope auf 24 bereits geprüfte Code-, Test- und Dokumentationsdateien begrenzt.
- `.env`, Tokens, Runtime-, History-, Lern- und Marktdaten vom Commit ausgeschlossen.
- Vollständige Testsuite und Diff-Prüfung erneut erfolgreich ausgeführt.
- Commit `4258111ebe51175e06d4ece363bf9c5b7c23f28a` erstellt und auf `origin/agent/integrate-decision-gate-observer` gepusht.
- Draft-PR #23 gegen `main` erstellt: `https://github.com/cRioshy/Pando/pull/23`.
- PR-Zustand anschließend als `OPEN`, `isDraft=true`, Basis `main` und Head `agent/integrate-decision-gate-observer` verifiziert.
- Kein Merge durchgeführt; `main` blieb unverändert.

### Veränderte Dateien

- Die 24 Dateien des Commit `4258111ebe51175e06d4ece363bf9c5b7c23f28a`
- `docs/SESSION_HANDOVER.md`
- `docs/NEXT_STEPS.md`

### Neue Dateien

- Keine zusätzlichen Programmdateien während der Veröffentlichung; die elf neuen Stock-Vertrags-, Service-, Dokumentations- und Testdateien sind Bestandteil von Commit `4258111ebe51175e06d4ece363bf9c5b7c23f28a`.

### Ausgeführte Befehle

- `gh auth status`
- `python -m unittest discover -s tests -q`
- `git status -sb`
- `git diff --check`
- explizites `git add -- <24 freigegebene Dateien>`
- `git diff --cached --name-status`, `--stat` und `--check`
- `git commit -m "Add observer-only public stock pipeline"`
- `git push -u origin agent/integrate-decision-gate-observer`
- `gh pr list`, `gh pr create --draft`, `gh pr view 23`

### Ausgeführte Tests und tatsächliche Ergebnisse

- Vollständige Testsuite: 289/289 bestanden in 46,276 Sekunden.
- `git diff --check`: keine Inhaltsfehler; ausschließlich erwartete LF/CRLF-Hinweise unter Windows.
- Vorherige Scope-/Secret-Prüfung: sauber; keine Secrets oder Laufzeitdaten im Commit.
- Push erfolgreich; Remote-Tracking eingerichtet.
- Draft-PR #23 erfolgreich als offen und Draft verifiziert.

### Bekannte Fehler

- Keine neue Code- oder Runtime-Störung festgestellt.
- Die bekannten zwei beschädigten historischen Stock-Backup-JSONs bleiben unverändert bestehen.
- Die aussagekräftige Quote-Freshness-Auswertung benötigt weiterhin die geöffnete US-Marktphase.

### Getroffene Architekturentscheidungen

- Keine neue Architekturänderung während der Veröffentlichung.
- Öffentliche Stock-Pipeline, Shadow-Kandidat und Risikoplan bleiben reine Observer; aktiver Legacy-Decision-/Signalpfad, Telegram und Orders bleiben unberührt.
- Veröffentlichung erfolgte ausschließlich auf dem Arbeitsbranch und als Draft-PR; keine automatische Zusammenführung.

### Nicht abgeschlossene Punkte

- Draft-PR #23 ist offen, Draft und nicht gemergt.
- Einmalige read-only US-Marktphasenmessung am 10. August 2026 ab 15:40 Uhr Europe/Berlin steht aus.
- Unabhängige Confidence beziehungsweise belastbare Score-Kalibrierung steht erst nach dieser Messung an.
- Keine Gate-, Telegram- oder Orderkopplung.

### Exakter nächster sinnvoller Arbeitsschritt

Draft-PR #23 unverändert als Draft belassen und am 10. August 2026 ab 15:40 Uhr Europe/Berlin die bereits aktive read-only Automation mindestens fünf vollständige Stockzyklen messen lassen. Danach Freshness, Shadow-Verteilung, Risikopläne und Reason Codes auswerten, bevor eine unabhängige Confidence oder Score-Kalibrierung geplant wird.

## Aktuelle Aufgabe: US-Marktphasenprüfung terminieren

### Datum und Uhrzeit

9. August 2026, 14:48 Uhr, Europe/Berlin (`+02:00`)

### Ziel der Aufgabe

Die nächste aussagekräftige observer-only Laufzeitanalyse während einer geöffneten US-Marktphase vorbereiten, ohne aktuellen Code, Runtime, Gate, Telegram oder Orders zu verändern.

### Durchgeführte Arbeiten

- Pflichtdokumentation und aktuellen Livezustand erneut geprüft.
- Einmalige lokale Codex-Automation für Montag, 10. August 2026, 15:40 Uhr Europe/Berlin vorbereitet.
- Auftrag auf mindestens fünf vollständige Stockzyklen, Quote-Freshness, Shadow-Verteilung, Risikopläne, Datenstatus/Reason Codes und Sicherheitsgrenzen begrenzt.
- Festgelegt, dass die Automation bei nicht erreichbarem Dienst nichts startet oder verändert, sondern nur den Blocker berichtet.
- Code-, Prozess-, Gate-, Telegram- und Orderänderungen ausdrücklich ausgeschlossen.
- Die Automationskarte wurde in der App zur Benutzerbestätigung angezeigt.

### Veränderte Dateien

- `docs/SESSION_HANDOVER.md`
- `docs/NEXT_STEPS.md`

### Neue Dateien

- keine

### Ausgeführte Befehle

- vollständige Lektüre der fünf Pflichtdokumente
- `git status --short`
- read-only Abruf von `http://127.0.0.1:8000/api/status`
- lokale Projektliste der Codex-App abgerufen
- einmalige zeitgebundene Automation als Bestätigungskarte vorbereitet

### Ausgeführte Tests und tatsächliche Ergebnisse

- Keine neuen Codetests erforderlich, da kein Programmcode verändert wurde.
- Aktueller Runtime-Preflight: `running=true`, Plattform `OK`, Fehler 0, STALE 0.
- Bei der Planung: 6 Stockzyklen, 24 Shadows, 18 Risikopläne, 30 sichere Daten-Blocks; Telegram aus/Dry-Run mit 0 Sendungen.
- Automationskarte erfolgreich gerendert; Aktivierung steht bis zur Benutzerbestätigung aus.

### Bekannte Fehler

- Keine neue Runtime-Störung festgestellt.
- Die aussagekräftige Freshness-Prüfung ist erst während der geöffneten US-Marktphase möglich.

### Getroffene Architekturentscheidungen

- Keine Architekturänderung.
- Die spätere Prüfung ist reine Beobachtung und darf keine Prozesse selbst starten.
- Nur verpflichtende Zustands-/Übergabedokumente dürfen nach der späteren Analyse aktualisiert werden; Programmcode bleibt unverändert.

### Nicht abgeschlossene Punkte

- Benutzer muss die angezeigte Automationskarte bestätigen.
- Marktphasenprüfung und Messbericht stehen noch aus.
- Keine Gate-, Telegram- oder Orderkopplung.

### Exakter nächster sinnvoller Arbeitsschritt

Automationskarte bestätigen. Am 10. August 2026 ab 15:40 Uhr Europe/Berlin mindestens fünf Stockzyklen observer-only erfassen und anschließend die tatsächlichen Freshness-, Shadow-, Risiko- und Daten-Audit-Ergebnisse berichten.

## Aktuelle Aufgabe: Observer-only Stock-Shadow-Risikoplan integrieren

### Datum und Uhrzeit

9. August 2026, 14:42 Uhr, Europe/Berlin (`+02:00`)

### Ziel der Aufgabe

Für LONG-/SHORT-Stock-Shadows einen normalisierten Risikoplan ausschließlich aus derselben öffentlichen Kerzen-/Kurs-Sicht ableiten. Keine Änderung am aktiven Legacy-Feature-/Decision-/Signalpfad, keine Gate-Umschaltung, keine Telegram-Freigabe und keine Orders.

### Durchgeführte Arbeiten

- Pflicht-, Stock-, Shadow-, Feature-, Event- und Gate-Dokumentation vollständig gelesen und gegen den aktuellen Code geprüft.
- Den tatsächlichen Legacy-Risikoplan untersucht: Entry am Kurs, ATR mit 0,5-%-Mindestdistanz, Stop bei 1R, Ziele bei 1R/2R/3R.
- `pandorickki.stock-shadow-risk` Version 1 als reinen, fail-closed Observervertrag implementiert.
- Explizite Policy für ATR-Multiplikator, Mindestdistanz, drei Zielmultiplikatoren und Rundungsstellen ergänzt.
- Entry aus öffentlichem Kurs und ATR14 aus exakt derselben validierten öffentlichen Shadow-Datensicht verwendet.
- LONG-/SHORT-Level richtungssicher normalisiert; HOLD, unberechneter Shadow, ungültiger ATR/Entry sowie unmögliche Level blockieren.
- Risikoplan in den internen Stock-Daten-Audit eingespeist, ohne den aktiven Pfad umzuschalten.
- Telemetrie für berechnete/blockierte Risikopläne und letzten Status ergänzt.
- Sicherheitsgrenze gehärtet: Audit, Shadow, Vergleich, Risiko und Providerfelder werden vor `STOCK_ANALYSIS_FINISHED` entfernt. Sie gelangen nicht auf den EventBus und nicht in Brain, Decision, NeuroBrain, Telegram oder History.
- Konfiguration, `.env.example` und Web-Starter mit expliziten Standardwerten ergänzt.
- Dokumentation und dauerhafte Arbeitsregeln aktualisiert.
- PandorickKi geordnet gestoppt, finalen Code mit unveränderten Sicherheitswerten neu gestartet und zwei Produktionszyklen geprüft.
- Externes Legacy-Stockprojekt nicht verändert.

### Veränderte Dateien

- `.env.example`
- `AGENTS.md`
- `adapters/stock_adapter.py`
- `config.py`
- `docs/ARCHITECTURE.md`
- `docs/CURRENT_SYSTEM_STATE.md`
- `docs/KNOWN_PROBLEMS.md`
- `docs/NEXT_STEPS.md`
- `docs/SESSION_HANDOVER.md`
- `docs/STOCK_DATA_CONTRACT.md`
- `docs/STOCK_SHADOW_CANDIDATE.md`
- `orchestrator.py`
- `start_pandorick_web.bat`
- `tests/test_config.py`
- `tests/test_stock_adapter.py`

### Neue Dateien

- `stock_shadow_risk.py`
- `tests/test_stock_shadow_risk.py`
- `docs/STOCK_SHADOW_RISK.md`

### Ausgeführte Befehle

- vollständige `Get-Content`-Lektüre aller Pflicht- und Zusatzverträge
- `git status --short`, `git branch --show-current`
- `rg`-Suche nach ATR-, Stop-, Ziel-, CRV- und Consumerpfaden
- `./.venv/Scripts/python.exe -m unittest tests.test_stock_shadow_risk tests.test_stock_shadow_candidate tests.test_stock_adapter tests.test_config tests.test_stock_data_contract tests.test_stock_candle_service -v`
- gezielte Suite nach Eventgrenzen-Härtung erneut mit `-q`
- `./.venv/Scripts/python.exe -m py_compile stock_shadow_risk.py stock_shadow_candidate.py adapters/stock_adapter.py config.py orchestrator.py`
- `./.venv/Scripts/python.exe -m unittest discover -s tests -q`
- `git diff --check`
- `POST http://127.0.0.1:8000/api/control/stop`
- versteckter Start mit `./.venv/Scripts/python.exe main.py --headless --web` und expliziten sicheren Observer-/Telegramwerten
- wiederholte read-only Abrufe von `/api/status` und Prüfung der veröffentlichten Stock-Sicht

### Ausgeführte Tests und tatsächliche Ergebnisse

- Gezielte Suite: 37/37 bestanden; finale Wiederholung 1,416 Sekunden.
- Gesamtsuite: 289/289 bestanden in 47,395 Sekunden.
- Python-Kompilationsprüfung: bestanden.
- `git diff --check`: keine Whitespacefehler; nur erwartete LF/CRLF-Hinweise.
- Zwei Livezyklen: Plattform gesund, Services gesund beziehungsweise während Momentaufnahme aktiv laufend; Sitzungsfehler 0, STALE 0.
- Stock: 10 Audits, 8 erfolgreiche öffentliche Historien, 2 erwartete `SPCX`-Blocks.
- Shadow: 8 Kandidaten, 4 LONG, 2 SHORT, 2 HOLD.
- Risiko: 6 gültige LONG-/SHORT-Pläne, 4 sichere Blocks aus 2 HOLD plus 2 `SPCX`.
- Daten-Audit: 0 `READY`, 10 `BLOCKED`; am Sonntag sind öffentliche Yahoo-Quotetimestamps vom Freitag und damit nach der 900-Sekunden-Policy korrekt stale. HOLD und `SPCX` blockieren zusätzlich.
- In der über `/api/status` sichtbaren aktiven Stock-Publikation kam kein `stock_shadow`, `stock_data_audit` oder `stock_candle_source` vor.
- NeuroBrain: Queue 0, Drops 0, Fehler 0.
- Fehlerjournal: gesund, Schreibfehler 0.
- Telegram: `enabled=false`, `dry_run=true`, `messages_sent=0`.

### Bekannte Fehler

- KP-021 bleibt offen: Brain-Confidence dupliziert Probability; der Shadow-Risikoplan erzeugt bewusst keine Confidence.
- KP-022 bleibt für eine aktive Gate-Kette offen: Öffentliche Stockdaten und Risiko sind observer-only und nicht mit dem Decision Gate gekoppelt.
- `SPCX` besitzt weiterhin keinen belegten öffentlichen Ticker und bleibt blockiert.
- Die 900-Sekunden-Quote-Freshness blockiert Stock-Daten-Audits außerhalb einer frischen Marktphase erwartungsgemäß.
- Zwei historische Stock-Backup-JSONs bleiben beschädigt und unverändert.

### Getroffene Architekturentscheidungen

- Version 1 übernimmt das nachgewiesene Legacy-Grundprinzip, bezieht aber keinen Wert aus dem Legacy-Snapshot.
- Risikodistanz ist `max(ATR14 × 1,0; 0,5 % Entry)`; Ziele liegen bei 1R/2R/3R; Rundung erfolgt auf vier Dezimalstellen.
- Der Stock-Datenvertrag darf den Plan intern als Datenreife prüfen. Ein `READY` wäre keine Decision-, Telegram- oder Orderfreigabe.
- Observerfelder werden vor jeder aktiven Stock-Eventpublikation explizit entfernt.
- Keine Positionsgröße, reale Ausführung, Gate-Kopplung oder Telegram-Kopplung wurde ergänzt.

### Nicht abgeschlossene Punkte

- Noch keine Beobachtung während einer geöffneten US-Marktphase mit frischen Kurszeitstempeln.
- Noch keine unabhängige Confidence und keine statistische Kalibrierung des Heuristikscores.
- Keine aktive Stock-Gate-, Signal-, Telegram- oder Orderkopplung.
- Der gesamte gestapelte Provider-/Stock-Vertrags-/Shadow-/Risikostand ist lokal, uncommitted und noch nicht veröffentlicht.

### Exakter nächster sinnvoller Arbeitsschritt

Während einer geöffneten US-Marktphase den unveränderten observer-only Stand über mehrere Zyklen auswerten: Reason-Code-Verteilung, Shadow-Richtungen, Risikodistanzen, 1R/2R/3R-Level und `stock_data READY/BLOCKED`. Danach eine unabhängige Confidence oder ehrliche Score-Kalibrierung als separaten Vertrag planen. Bis dahin keine Gate-Umschaltung, keine Telegram-Kopplung und keine Orders.

## Aktuelle Aufgabe: Öffentlichen Stock-Shadow-Kandidaten observer-only integrieren

### Datum und Uhrzeit

9. August 2026, 12:16 Uhr, Europe/Berlin (`+02:00`)

### Ziel der Aufgabe

Einen vollständig vom aktiven Legacy-Aktienpfad getrennten Shadow-Kandidaten aus öffentlichen Tageskerzen und öffentlichem Kurs erstellen. Fakten, Direction und Probability müssen kompakt und vergleichbar auditiert werden, ohne Feature-/Decision-/Signalpfad, Decision Gate, Telegram oder Orders zu verändern.

### Durchgeführte Arbeiten

- Pflicht- und Vertragsdokumentation sowie tatsächlichen Adapter-, Config- und Orchestratorcode erneut geprüft.
- `pandorickki.stock-shadow-candidate` Version 1 als pure observer-only Berechnung implementiert.
- Explizite Policy mit mindestens 200 Kerzen sowie LONG-/SHORT-Bullish-Score-Schwellen ergänzt.
- Öffentliche Kerzen strikt über den bestehenden Feature-Datenqualitätsvertrag normalisiert und fail-closed geprüft.
- Transparente Version-1-Komponenten für Kurs/SMA20, SMA20/SMA50, SMA50/SMA200, 20-Tage-Rendite und RSI14 ergänzt; SMA-, RSI-, ATR- und Volumenwerte kompakt projiziert.
- Score ausdrücklich als `UNVALIDATED_HEURISTIC_SCORE`, nicht als kalibrierte Wahrscheinlichkeit oder Confidence gekennzeichnet.
- Shadow-Kandidat ohne Rohkerzen, Risikoplan, Eventpublikation oder Persistenz in den getrennten Stock-Auditpfad integriert.
- Legacy- und Shadow-Sicht mit Quellen, Direction, Probability und `direction_matches` vergleichbar gemacht; `affects_active_decision` ist fest `false`.
- Service-Telemetrie für Kandidatenzahl sowie LONG/SHORT/HOLD und letzte Shadow-Sicht ergänzt.
- Web-Starter behält alle Sicherheitswerte bei und setzt die Observer-Schwellen ausdrücklich auf 60/40.
- Dokumentation und dauerhafte Arbeitsregeln aktualisiert.
- PandorickKi geordnet über die Control-API gestoppt, als versteckter Prozess mit Live-Crypto/-Aktien, Stock-Observer und Decision-Gate-Observer neu gestartet.
- Zwei vollständige Produktionszyklen kontrolliert, die Neutralitätskante korrigiert und den final getesteten Stand erneut geordnet geladen und über einen weiteren vollständigen Zyklus geprüft; externes Legacy-Projekt nicht verändert.

### Veränderte Dateien

- `.env.example`
- `AGENTS.md`
- `adapters/stock_adapter.py`
- `config.py`
- `docs/ARCHITECTURE.md`
- `docs/CURRENT_SYSTEM_STATE.md`
- `docs/KNOWN_PROBLEMS.md`
- `docs/NEXT_STEPS.md`
- `docs/SESSION_HANDOVER.md`
- `orchestrator.py`
- `start_pandorick_web.bat`
- `tests/test_config.py`
- `tests/test_stock_adapter.py`

### Neue Dateien

- `stock_shadow_candidate.py`
- `tests/test_stock_shadow_candidate.py`
- `docs/STOCK_SHADOW_CANDIDATE.md`

Die bereits im selben uncommitteten Arbeitsstand vorhandenen neuen Provider-/Stock-Vertragsdateien bleiben ebenfalls erhalten und wurden nicht zurückgesetzt.

### Ausgeführte Befehle

- `git status --short`
- gezielte `rg`-/`Get-Content`-Prüfungen der Adapter-, Config-, Orchestrator-, Vertrags-, Test- und Dokumentationspfade
- zunächst `python -m pytest ...` (nicht ausführbar: globales `python` fehlt)
- `./.venv/Scripts/python.exe -m pytest ...` (nicht ausführbar: `pytest` ist in der Projekt-venv nicht installiert)
- `./.venv/Scripts/python.exe -m unittest tests.test_stock_shadow_candidate tests.test_stock_adapter tests.test_config tests.test_stock_data_contract tests.test_stock_candle_service -q`
- `./.venv/Scripts/python.exe -m unittest discover -s tests -q`
- `git diff --stat`
- `git diff --check`
- `POST http://127.0.0.1:8000/api/control/stop`
- versteckter Neustart mit `./.venv/Scripts/python.exe main.py --headless --web` und den bestehenden sicheren Runtimevariablen
- wiederholte read-only Abrufe von `/api/health` und `/api/status`

### Ausgeführte Tests und tatsächliche Ergebnisse

- Finale gezielte Suite nach Neutralitätskorrektur: 31/31 bestanden in 1,428 Sekunden.
- Finale Gesamtsuite: 283/283 bestanden in 42,497 Sekunden.
- `git diff --check`: keine Whitespacefehler; nur erwartete LF/CRLF-Hinweise.
- Kontrollierter Neustart: Port wurde geordnet freigegeben; kein harter Prozessabbruch.
- Nach zwei Produktionszyklen: Plattform `OK`, alle 11 Services gesund, Sitzungsfehler 0, STALE-Services 0.
- Stock: 10 Audits, 0 `READY`, 10 `BLOCKED`; 8 erfolgreiche öffentliche Historien, 2 erwartete `SPCX`-Blocks.
- Shadow: 8 berechnete Kandidaten, davon 4 LONG, 2 SHORT, 2 HOLD; letzter Score 90,0. Diese Zahlen sind Diagnose, keine Freigabe.
- NeuroBrain: Queue 0, Drops 0, Fehler 0, Worker aktiv.
- Telegram: `enabled=false`, `dry_run=true`, `messages_sent=0`.
- Finaler Reload nach Neutralitätskorrektur: ein weiterer vollständiger Crypto-/Stock-Zyklus, Plattform und 11/11 Services `OK`, Fehler 0, STALE 0, vier Shadow-Kandidaten, fünf Stock-Audits weiterhin `BLOCKED`, Telegram-Sendungen 0.
- Bekannte externe Crypto-Legacy-`datetime.utcnow()`-DeprecationWarnings blieben ohne Testfehler.

### Bekannte Fehler

- KP-022 bleibt teilweise offen: Der öffentliche Shadow ist vorhanden, aber ein normalisierter Risikoplan aus derselben öffentlichen Datensicht fehlt absichtlich. Deshalb bleiben alle Stock-Kandidaten sicher blockiert.
- KP-021 bleibt offen: Brain-Confidence dupliziert Probability; der Shadow erzeugt bewusst keine angeblich unabhängige Confidence.
- `SPCX` besitzt weiterhin keinen belegten öffentlichen Ticker und wird vor einem Provideraufruf blockiert.
- Zwei historische Stock-Backup-JSONs bleiben beschädigt; sie wurden nicht verändert.

### Getroffene Architekturentscheidungen

- Shadow und aktive Legacy-Decision bleiben getrennte Datenobjekte; Übereinstimmung ist nur Beobachtung.
- Öffentliche Rohkerzen bleiben im In-Memory-Providerpfad und gelangen weder auf den EventBus noch in History.
- Der Version-1-Score ist transparent und versioniert, aber ausdrücklich nicht kalibriert.
- Kein Risikoplan wird geraten oder aus Legacy-Daten übernommen.
- Decision Gate, aktiver Signalpfad, Telegram und Orders bleiben unverändert.

### Nicht abgeschlossene Punkte

- Noch kein normalisierter observer-only Stock-Risikoplan aus öffentlichen Daten.
- Noch keine fachlich unabhängige Confidence oder statistische Kalibrierung des Shadow-Scores.
- Keine Gate-Umschaltung und keine Telegram-Kopplung.
- Der gesamte gestapelte Provider-/Vertrags-/Shadow-Arbeitsstand ist lokal, uncommitted und noch nicht veröffentlicht.

### Exakter nächster sinnvoller Arbeitsschritt

Vor einer Umsetzung gemeinsam die observer-only ATR-Risikoregeln festlegen: Entry aus öffentlichem aktuellem Kurs, Stop-/Zielabstände, Mindest-Chance-Risiko-Verhältnis und Rundungsregeln. Danach einen versionierten Risikoplan ausschließlich aus derselben öffentlichen Shadow-Datensicht implementieren, fail-closed testen und nur in den getrennten Audit einspeisen. Aktiven Feature-/Decision-/Signalpfad, Decision Gate, Telegram und Orders nicht umschalten.

## Aktuelle Aufgabe: Öffentlichen Stock-Tageskerzenprovider read-only integrieren

### Datum und Uhrzeit

9. August 2026, 11:51 Uhr, Europe/Berlin (`+02:00`)

### Ziel der Aufgabe

Einen öffentlichen read-only Tageskerzenprovider innerhalb von PandorickKi ergänzen, mindestens 200 zeitgestempelte Kerzen gegen den Stock-Datenvertrag prüfen und die Ergebnisse zunächst ausschließlich als getrennten Audit sichtbar machen. Keine Rohkerzen persistieren, keine Placeholder-Decision fachlich aufwerten und Decision Core, Gate-Freigabe, Telegram sowie Orders unverändert lassen.

### Durchgeführte Arbeiten

- `StockCandleService` mit öffentlichen Yahoo-Chartdaten, query1/query2-Fallback, Tickerprüfung, sicherer Diagnostik und begrenztem 15-Minuten-In-Memory-Cache implementiert.
- Provider liefert normalisierte Tages-OHLCV-Zeilen einschließlich Provider-Zeitstempel; keine private API, kein Token und kein Schreibzugriff.
- Stock-Audit optional und standardmäßig deaktiviert konfigurierbar gemacht; Web-Starter aktiviert ihn ausdrücklich mit 260 Kerzen und dem dokumentierten 200-Kerzen-Vertrag.
- `StockAdapter` ruft den Provider nur im Observermodus auf und bewertet die Historie getrennt mit `pandorickki.stock-data`.
- Ehrliche Quellklassifikation `MIXED_PLACEHOLDER_DECISION` gesetzt, weil Richtung und Probability weiterhin aus dem Legacy-Placeholder-Snapshot stammen.
- Auditkerzen weder an die bestehende Feature Engine des aktiven Pfads noch an EventBus, Brain, Decision oder NeuroBrain weitergegeben.
- Nur kompakte kumulative Audit-/Providerzähler und letzte Reason Codes in die Service-Telemetrie aufgenommen.
- Externes Legacy-Stockprojekt nicht verändert.
- Kontrollierten Stop und drei sichere Starts während der schrittweisen Liveprüfung durchgeführt; der finale Prozess läuft mit dem vollständigen Telemetriestand.

### Veränderte Dateien

- `.env.example`
- `adapters/stock_adapter.py`
- `config.py`
- `orchestrator.py`
- `start_pandorick_web.bat`
- `tests/test_config.py`
- `tests/test_stock_adapter.py`
- `docs/CURRENT_SYSTEM_STATE.md`
- `docs/SESSION_HANDOVER.md`
- `docs/ARCHITECTURE.md`
- `docs/KNOWN_PROBLEMS.md`
- `docs/NEXT_STEPS.md`
- `docs/STOCK_DATA_CONTRACT.md`

### Neue Dateien

- `adapters/stock_candle_service.py`
- `tests/test_stock_candle_service.py`

### Ausgeführte Befehle

- Pflicht-, Stock-, Feature-, Event- und Decision-Gate-Dokumentation gelesen und mit Repository, Config, Orchestrator, Adapter und Legacy-Code abgeglichen.
- Gezielte Unit-Tests für Provider, Vertrag, Adapter, Konfiguration, Eventvertrag und Decision Gate.
- Öffentlichen AAPL-Provider einmal isoliert mit expliziter Netzwerkfreigabe read-only aufgerufen.
- Vollständige Unit-Test-Suite ausgeführt.
- Plattform jeweils über `/api/control/stop` kontrolliert beendet, mit Telegram aus/Dry-Run und read-only Marktquellen versteckt neu gestartet und über `/api/health` sowie `/api/status` geprüft.
- Python-Compile-, Diff-, Secret- und Git-Statusprüfung.

### Ausgeführte Tests

- `./.venv/Scripts/python.exe -m unittest tests.test_stock_candle_service tests.test_stock_data_contract tests.test_stock_adapter tests.test_config -v`
- `./.venv/Scripts/python.exe -m unittest tests.test_stock_candle_service tests.test_stock_data_contract tests.test_stock_adapter tests.test_config tests.test_event_payload_contract tests.test_decision_gate_contract -q`
- `./.venv/Scripts/python.exe -m unittest discover -s tests -q`
- Isolierter öffentlicher AAPL-Test mit 260 Tageskerzen und strikter `FeatureDataQualityPolicy`.
- Liveprüfung eines vollständigen Plattformzyklus.

### Tatsächliche Testergebnisse

- Erste gezielte Suite: 26/26 bestanden.
- Erweiterte gezielte Suite: 44/44 bestanden.
- Finale Gesamtsuite: 278/278 bestanden in 49,163 Sekunden.
- AAPL real: 260 empfangen, 260 akzeptiert, 0 entfernt, 0 Duplikate, 260 Zeitstempel, `PASS/VERIFIED/READY`.
- Live: Plattform und 11/11 Services `OK`, null STALE-Services und null Sitzungsfehler.
- Stock-Zyklus: 5 Ergebnisse, 5 Audits, 4 erfolgreiche Kerzenhistorien, 1 erwarteter Providerblock für `SPCX`, 0 `READY`, 5 `BLOCKED`.
- Abschließender Dauercheck nach vier Zyklen: 20 Audits, 16 erfolgreiche Historien, 4 erwartete `SPCX`-Blocks, weiterhin 0 `READY`, 20 `BLOCKED`, null Sitzungsfehler und null STALE-Services.
- Letzter SPCX-Audit: `SD_SOURCE_NOT_LIVE`, `SD_CANDLES_MISSING`, ungültiger/fehlender Preis und Zeitstempel sowie `SD_RISK_MISSING`.
- Telegram: `enabled=false`, `dry_run=true`, `messages_sent=0`.

### Bekannte Fehler

- KP-022 bleibt offen: Öffentliche Kerzen sind vorhanden, aber aktive Richtung/Probability stammen weiter aus Placeholder-Daten und der normalisierte Risikoplan fehlt.
- `SPCX`/`SPACEX` besitzt keinen unterstützten öffentlichen Börsenticker und bleibt absichtlich blockiert.
- Der erste isolierte Provideraufruf in der eingeschränkten Sandbox scheiterte erwartungsgemäß mit `WinError 10013`; der freigegebene read-only Netzwerkaufruf bestand. Es entstand daraus kein Plattform-Journaleintrag.
- Externe Crypto-Legacymodule erzeugen weiterhin `datetime.utcnow()`-DeprecationWarnings in Tests; keine Regression.

### Getroffene Architekturentscheidungen

- Öffentliche Kerzen und Placeholder-Decision werden nicht zu einer scheinbar echten Decision vermischt.
- Die Tageskerzen verbleiben flüchtig im Provider-/Auditpfad und werden weder persistiert noch publiziert.
- query1/query2 sind read-only Fallbacks desselben Providers; Cache-Key ist Symbol plus Limit, Cache-TTL standardmäßig 900 Sekunden.
- Observer ist in sicheren Defaults aus und nur im bestätigten Web-Starter aktiv.
- Auditstatus `READY` bleibt reine Datenbewertung und kann Telegram oder Orders nicht freigeben.

### Nicht abgeschlossene Punkte

- Noch kein vollständig öffentlicher PandorickKi-Shadow-Kandidat für Richtung/Probability/Fakten.
- Noch kein normalisierter Stock-Risikoplan aus derselben validierten Datensicht.
- Keine Weitergabe des Stock-Auditstatus an das Decision Gate.
- Keine Änderung am aktiven Feature-/Decision-/Signalpfad, Telegram oder Orders.
- Gesamter aktuelle Arbeitsbaum einschließlich des zuvor definierten Stock-Vertrags ist lokal und noch nicht committed oder veröffentlicht.

### Exakter nächster sinnvoller Arbeitsschritt

Einen getrennten, observer-only Stock-Shadow-Kandidaten aus den öffentlichen Tageskerzen und dem öffentlichen Preis definieren. Seine Fakten, Direction und Probability müssen klar von der Legacy-Placeholder-Decision getrennt und vergleichbar auditiert werden. Erst danach einen normalisierten Risikoplan aus genau derselben öffentlichen Datensicht ableiten; keine Gate-Umschaltung.

## Aktuelle Aufgabe: Stock-Datenvertrag Version 1 definieren

### Datum und Uhrzeit

9. August 2026, 11:31 Uhr, Europe/Berlin (`+02:00`)

### Ziel der Aufgabe

Den tatsächlichen Stock-Datenfluss analysieren und einen belastbaren, fail-closed Datenvertrag für zeitgestempelte Kerzenhistorie, aktuellen Livepreis und normalisierten Richtungs-Risikoplan definieren. Noch keine Runtime-Integration, keine Gate-Umschaltung, keine Telegram-Kopplung und keine Orderausführung.

### Durchgeführte Arbeiten

- Pflichtdokumentation sowie Event-, Feature-Qualitäts- und Decision-Gate-Verträge gelesen und gegen den aktuellen Code geprüft.
- `StockAdapter`, `StockPriceService` und die relevanten externen Legacy-Module für Decision, Snapshot, Risiko und SQLite-Persistenz untersucht.
- Nachgewiesen, dass der Legacy-Lauf zwar einen ATR-basierten `StockRiskPlan` erzeugt, ihn aber nicht an das zurückgegebene `Decision`-Objekt hängt.
- Nachgewiesen, dass PandorickKi ohne History auf genau eine nicht zeitgestempelte Faktenkerze zurückfällt und die qualitative Legacy-Risikoampel keinen Stop-/Take-Profit-Plan ersetzt.
- Ausführbare Referenz `pandorickki.stock-data` Version 1 mit expliziter Policy, deterministischen Reason Codes, strikter Feature-Qualität, Quote-Alterung und Richtungs-Risikoprüfung erstellt.
- Vertrag absichtlich nicht an Adapter, EventBus, Decision Core oder Gate angeschlossen.
- Dauerhafte Arbeitsregel, Systemzustand, Architektur, bekanntes Problem KP-022 und nächste Schritte aktualisiert.

### Veränderte Dateien

- `AGENTS.md`
- `docs/CURRENT_SYSTEM_STATE.md`
- `docs/SESSION_HANDOVER.md`
- `docs/ARCHITECTURE.md`
- `docs/KNOWN_PROBLEMS.md`
- `docs/NEXT_STEPS.md`

### Neue Dateien

- `stock_data_contract.py`
- `tests/test_stock_data_contract.py`
- `docs/STOCK_DATA_CONTRACT.md`

### Ausgeführte Befehle

- `Get-Content`, `rg`, `git status`, `git branch --show-current` und `git log` für Pflichtdokumentation, Repository- und Codeabgleich.
- Gezielte Unit-Test-Suite für Stock-Vertrag, Stock-Adapter, Preisservice, Feature-Qualität, Feature Engine und Decision Gate.
- Vollständige Unit-Test-Erkennung über `python -m unittest discover -s tests -v` und nach der Kerzenalter-Prüfung erneut mit `-q`.
- Syntax-/Diff-/Statusprüfung mit Python-Compile, `git diff --check` und `git status --short`.

### Ausgeführte Tests

- `./.venv/Scripts/python.exe -m unittest tests.test_stock_data_contract -v`
- `./.venv/Scripts/python.exe -m unittest tests.test_stock_data_contract tests.test_stock_adapter tests.test_stock_price_service tests.test_feature_data_quality_contract tests.test_feature_engine tests.test_decision_gate_contract -v`
- `./.venv/Scripts/python.exe -m unittest discover -s tests -v`
- `./.venv/Scripts/python.exe -m unittest discover -s tests -q`

### Tatsächliche Testergebnisse

- Stock-Vertrag: 6/6 bestanden.
- Gezielte Regressionen: 37/37 bestanden.
- Finale Gesamtsuite: 271/271 bestanden in 43,734 Sekunden.
- Der vollständige Referenzfall liefert `READY`, aber unverändert `ready_for_telegram=false` und `order_execution_allowed=false`.
- Der heutige Einzelsnapshot, Placeholder-Daten, fehlende Preise/Risiken, veraltete Quotes und richtungswidrige Risikopläne werden fail-closed blockiert.
- Die Gesamtsuite zeigte weiterhin vorhandene `datetime.utcnow()`-DeprecationWarnings im externen Crypto-Legacyprojekt; sie verursachten keinen Testfehler und wurden nicht verändert.

### Bekannte Fehler

- KP-022 bleibt als Runtime-Lücke offen: Der neue Vertrag ist noch nicht an den StockAdapter angeschlossen.
- `SPCX`/`SPACEX` besitzt weiterhin keinen unterstützten öffentlichen Börsenticker und wird ohne Livepreis blockiert.
- KP-021 bleibt offen: Confidence dupliziert Probability.
- KP-004/KP-005 bleiben offen: Der aktive Signalpfad ist nicht gate-gefiltert; Telegram bleibt deshalb deaktiviert/Dry-Run.

### Getroffene Architekturentscheidungen

- Der Vertrag ist eine eigenständige Referenz vor einer späteren Adapterintegration.
- Kerzen bleiben intern an der Adapter-/Feature-Grenze und gelangen nicht in kompakte Event-, Brain-, Decision- oder NeuroBrain-Payloads.
- Pflichtgrenzen für Kerzenzahl, Warmup und Quote-Alter werden nicht versteckt, sondern müssen ausdrücklich per Policy gesetzt werden.
- Die qualitative Legacy-Risikoampel und ein preisbezogener Stop-/Take-Profit-Plan bleiben fachlich getrennt.
- Das externe Legacy-Projekt wurde nicht verändert.

### Nicht abgeschlossene Punkte

- Noch kein öffentlicher read-only Tageskerzenprovider in PandorickKi.
- Noch keine Runtime-Projektion des normalisierten Stock-Risikoplans.
- Noch kein Liveaudit des neuen Stock-Datenvertrags.
- Keine Gate-, Decision-, Signal-, Telegram- oder Orderänderung.
- Änderungen sind lokal, uncommitted und noch nicht veröffentlicht.

### Exakter nächster sinnvoller Arbeitsschritt

Einen read-only öffentlichen Tageskerzenprovider innerhalb von PandorickKi entwerfen und mit Provider-Fallback, Tickerprüfung, Zeitstempeln und mindestens 200 Kerzen testen. Ihn zunächst nur im StockAdapter gegen `pandorickki.stock-data` auditieren; keine Rohkerzen persistieren und den aktiven Decision-/Signalpfad nicht umschalten.

## Aktuelle Aufgabe: Erste erweiterte Decision-Gate-Liveauswertung

### Datum und Uhrzeit

9. August 2026, 10:44 Uhr, Europe/Berlin (`+02:00`)

### Ziel der Aufgabe

Den weiterlaufenden 60/60/0-Decision-Gate-Observer vollständig read-only auswerten: Markt-, Symbol-, Richtungs-, Probability-, Qualitäts- und Reason-Code-Verteilung, qualifizierte Fälle, Schema-/Policytreue, Duplikate, unsichere Freigaben und aktuelle Systemgesundheit. Keine Gate-Regel, keinen Adapter, keinen Signalpfad und keine Runtime-History verändern.

### Durchgeführte Arbeiten

- Auditfenster vom ersten korrekten Netzwerkstart bis `2026-08-09T08:40:38Z` eingefroren und sämtliche 272 Datensätze eingelesen.
- Eindeutigkeit, Gate-/Policy-Schema, Observer-/Releasezustand und Telegram-/Orderflags geprüft.
- Verteilung nach Markt, Symbol, Richtung, Probability, Preis, Datenqualität und Reason Codes berechnet.
- Zwei technisch qualifizierte ETHUSDT-LONG-Fälle einzeln geprüft; beide blieben ohne Telegram- oder Orderfreigabe.
- Tatsächlichen Stock- und Brain-Code gegen die Auditbefunde geprüft.
- Bestätigt, dass Stock keinen normalisierten `risk`-Block erzeugt und Brain `confidence` direkt gleich `probability` setzt.
- Einen eingefrorenen Bericht erstellt und Systemzustand, bekannte Probleme und nächste Schritte aktualisiert.

### Veränderte Dateien

- `docs/CURRENT_SYSTEM_STATE.md`
- `docs/SESSION_HANDOVER.md`
- `docs/KNOWN_PROBLEMS.md`
- `docs/NEXT_STEPS.md`

### Neue Dateien

- `docs/DECISION_GATE_AUDIT_REPORT.md`

### Ausgeführte Befehle

- Pflicht- und Gate-Dokumentation sowie Branch/Commit/Status erneut geprüft.
- Read-only PowerShell-Auswertungen von `data/decision_gate_audit.jsonl`, `data/service_errors.jsonl` und `/api/status`.
- Codeprüfung mit `rg` und `Get-Content` in `adapters/stock_adapter.py`, `decision_gate_contract.py`, `event_payload_contract.py` und dem Brain-Pfad.
- Eingefrorenen Snapshot mit expliziter Start-/Endzeit erneut gezählt.
- `git diff --check`, Status- und Scopeprüfung.

### Ausgeführte Tests

- Keine Softwaretests, weil ausschließlich Runtime-Daten gelesen und technische Dokumentation ergänzt wurde.
- Reproduzierbare Snapshot-Verifikation für Anzahl, Marktaufteilung, Quell-ID-Eindeutigkeit, Qualification und Sicherheitsflags.
- Live-Health-/Service-/Telegramprüfung.

### Tatsächliche Testergebnisse

- Snapshot: 272 Datensätze, 272 eindeutige Quell-IDs, 102 Crypto, 170 Stock, 2 `QUALIFIED`, 270 `BLOCKED`, 0 unsichere Freigaben.
- Alle 272 Einträge Schema Version 1, Policy 60/60/0, `OBSERVER_ONLY`; keine Schema- oder Policyabweichung.
- Crypto: 102/102 `PASS/VERIFIED/READY`, 2 qualifizierte ETHUSDT-LONG-Fälle mit 62,90 und 60,90 Probability/Confidence.
- Stock: 170/170 `WARN/UNVERIFIED/WARMING`, 31 LONG-Fälle mit ungültigem/fehlendem Stop und Take-Profit, 34 SPCX-Fälle ohne positiven Preis.
- Häufigste Gründe: Probability/Confidence unter 60 und ungeeignete Richtung je 239; Stock-Qualität/Order/Warmup je 170.
- Plattform und alle elf Services weiterhin `OK`; Gate gesund, Telegram deaktiviert/Dry-Run und null gesendete Nachrichten; seit dem korrekten Netzwerkstart keine neuen Dienstfehler.
- Snapshot-Nachprüfung bestätigte exakt 272/2/102/170/272/0 für Gesamt, Qualified, Crypto, Stock, eindeutige IDs und unsichere Freigaben.

### Bekannte Fehler

- KP-021: Confidence ist derzeit keine unabhängige Messgröße, sondern entspricht Probability.
- KP-022: Stock kann den sicheren Gate-Vertrag wegen Einzelsnapshot, fehlendem Risikoplan und SPCX-Preisloch nicht erfüllen.
- KP-004 und KP-005 bleiben offen: Gate ist Observer, aktiver Decision-/Signalpfad ungefiltert; Telegram bleibt deshalb deaktiviert/Dry-Run.
- Der Zeitraum von knapp 39 Minuten ist noch keine belastbare Langzeit- oder Outcome-Bewertung.

### Getroffene Architekturentscheidungen

- Keine Architektur- oder Produktentscheidung geändert.
- 60/60/0 bleibt unverändert diagnostisch; Gate-Regeln werden nicht gelockert, um unvollständige Stock-Daten passieren zu lassen.
- Qualifizierte Observerergebnisse bleiben technische Kandidaten, keine Meldungs-, Trade- oder Orderfreigaben.
- Der Bericht verwendet ein festes Zeitfenster, damit weiterlaufende Append-only-Daten die dokumentierten Zahlen nicht nachträglich verändern.

### Nicht abgeschlossene Punkte

- Keine mehrstündige, tägliche oder mehrtägige Verteilung und keine Outcome-Zuordnung der qualifizierten Fälle.
- Noch kein eigener Stock-Datenvertrag für Kerzen, Preis und Risiko.
- Noch kein unabhängiger Confidence-Vertrag.
- Keine Umschaltung von Gate, Decision Core, Telegram oder Orders.
- Dokumentationsänderungen sind lokal und noch nicht veröffentlicht.

### Exakter nächster sinnvoller Arbeitsschritt

Observer unverändert weiterlaufen lassen und nach einem deutlich längeren Zeitfenster denselben eingefrorenen Snapshot einschließlich späterer simulierter Outcomes wiederholen. Parallel zunächst nur den Stock-Datenvertrag und einen ehrlichen unabhängigen Confidence-Begriff entwerfen; Implementierung erst nach separater Freigabe.

## Aktuelle Aufgabe: Decision-Gate-Observer diagnostisch mit 60/60 aktivieren

### Datum und Uhrzeit

9. August 2026, 10:06 Uhr, Europe/Berlin (`+02:00`)

### Ziel der Aufgabe

Nach ausdrücklicher Benutzerbestätigung `60/60 aktivieren` den bereits getesteten Decision-Gate-Audit-Observer dauerhaft im lokalen Web-Starter aktivieren, PandorickKi kontrolliert neu starten und mehrere Livezyklen ausschließlich beobachtend auswerten. Keine Umschaltung von Decision/Signal, Telegram oder Trackern und keine Orderfunktion aktivieren.

### Durchgeführte Arbeiten

- Pflichtdokumentation, Gate-, Event-Payload- und Feature-Qualitätsvertrag sowie aktuellen Branch/Commit und Starter geprüft.
- In `start_pandorick_web.bat` Observer=aktiv, Minimum Probability=60, Minimum Confidence=60 und Toleranz=0 ergänzt. Telegram bleibt dort ausdrücklich deaktiviert und Dry-Run.
- Runtime-Preflight, 35 gezielte Gate-/Payload-/Brain-/Decision-/Konfigurationstests und Diffprüfung bestanden.
- Alten, seit rund 11,5 Stunden laufenden Webprozess über `/api/control/stop` geordnet beendet; Port 8000 wurde ohne harten Prozessabbruch freigegeben.
- Zwei Starts innerhalb der eingeschränkten Codex-Sandbox wegen erwartbarem `WinError 10013` für öffentliche Provider jeweils kontrolliert beendet. Die sechs daraus entstandenen Fehlerjournalzeilen wurden nicht gelöscht oder verändert.
- PandorickKi anschließend mit ausdrücklicher Netzwerkfreigabe und identischen sicheren Werten versteckt gestartet.
- Vier vollständige Crypto-/Stock-Zyklen über API, Auditdatei, Fehlerjournal und Runtime-Logs verifiziert.

### Veränderte Dateien

- `start_pandorick_web.bat`
- `docs/CURRENT_SYSTEM_STATE.md`
- `docs/SESSION_HANDOVER.md`
- `docs/KNOWN_PROBLEMS.md`
- `docs/NEXT_STEPS.md`

### Neue Dateien

- Keine Projektdateien.
- Ignorierte Runtime-Logs `runtime_logs/decision_gate_60_60_*` und das vorgesehene Runtime-Audit `data/decision_gate_audit.jsonl` wurden erzeugt beziehungsweise fortgeschrieben.

### Ausgeführte Befehle

- Pflicht- und Vertragsdokumentation mit `Get-Content`, Code-/Konfigurationsprüfung mit `rg`, Git-Status-/Branch-/Remoteprüfung.
- `.\.venv\Scripts\python.exe scripts\runtime_preflight.py`.
- Gezielter Unittest-Lauf für Gate-Vertrag, Audit-Adapter, Konfiguration, Event-Payload, Brain und Decision.
- Read-only Abrufe von `/api/health` und `/api/status`.
- Kontrollierte POSTs auf `/api/control/stop` und Portfreigabeprüfung.
- Versteckter Prozessstart mit expliziten Live-Crypto-/Stock-, NeuroBrain-, Gate- und sicheren Telegramwerten; finaler Start mit freigegebenem Netzwerkzugriff.
- Read-only JSONL-Auswertung von Gate-Audit und Servicefehlerjournal.

### Ausgeführte Tests

- Runtime-Preflight.
- 35 gezielte Regressionstests.
- `git diff --check`.
- Kontrollierter Stop und Neustart.
- Vier vollständige Livezyklen.
- Service-, Crypto-, Stock-, Gate-, Audit-, Journal-, Telegram- und Logprüfung.

### Tatsächliche Testergebnisse

- Preflight bestanden mit Python 3.12.13 aus `.venv` und vorhandener Legacy-Crypto-Pipeline.
- 35/35 gezielte Tests in 0,467 Sekunden bestanden.
- Final: Plattform und 11/11 Services `OK`; Crypto vier Zyklen mit je drei Ergebnissen, Stock vier Zyklen mit je fünf Ergebnissen, Gate gesund.
- Seit dem korrekten Netzwerkstart null neue Dienstfehler; stdout/stderr jeweils 0 Byte.
- 32 neue eindeutige Gate-Audits: 12 Crypto, 20 Stock, 0 `QUALIFIED`, 32 `BLOCKED`, 0 ungültige Schemas, 0 doppelte Quell-IDs und 0 Telegram-/Orderfreigaben.
- Richtungen: 18 `HOLD`, 12 `WAIT`, 2 `LONG`. Zwei Kandidaten lagen bei Probability mindestens 60, blockierten aber weiter fail-closed wegen Richtung oder Stock-Preis-/Qualitäts-/Warmup-/Risikomängeln.
- Auditgröße nach Prüfung 60.764 Byte, keine Rotation erforderlich, keine Archive. Telegram `enabled=false`, `dry_run=true`, `messages_sent=0`.

### Bekannte Fehler

- KP-020: Sandbox-Prozesse können Binance/Bitget nicht erreichen; sechs dauerhafte, korrekte Journalzeilen aus den zwei beendeten Versuchen. Der freigegebene Netzwerkprozess ist nicht betroffen.
- KP-004 bleibt fachlich offen: Observer aktiv, aber der aktive Decision Core wird bewusst noch nicht durch das Gate gefiltert.
- Stock-Einzelsnapshots bleiben `WARN/UNVERIFIED/WARMING` und liefern dem Gate teilweise keinen positiven Preis beziehungsweise keinen vollständigen Risikoplan.
- Telegram liegt weiterhin vor der finalen Gate-Kette, bleibt deshalb deaktiviert/Dry-Run.

### Getroffene Architekturentscheidungen

- Die bestätigten 60/60/0-Werte gelten ausschließlich für Diagnose und Klassifikation, nicht als produktive Signal- oder Tradingfreigabe.
- Der Web-Starter aktiviert den Observer reproduzierbar; die zentrale Konfiguration bleibt sicher standardmäßig deaktiviert, falls andere Einstiegspunkte keine expliziten Werte setzen.
- Bestehender Decision-/Signalpfad bleibt parallel und unverändert. Gate-Ergebnisse sind Auditdaten, keine Steuerbefehle.
- Runtime-History, Fehlerjournal und Audit werden nicht gelöscht, bereinigt oder umgeschrieben.

### Nicht abgeschlossene Punkte

- Noch keine Langzeitauswertung der Gate-Verteilung; bislang vier Zyklen/32 Kandidaten.
- Noch keine Korrektur oder vertragliche Erweiterung der Stock-Preis-, Kerzen- und Risikodaten.
- Keine Gate-Umschaltung des Decision Core und keine Telegram-Kopplung.
- Lokale Starter-/Dokumentationsänderungen sind noch nicht veröffentlicht.

### Exakter nächster sinnvoller Arbeitsschritt

Den Observer zunächst weiterlaufen lassen und nach einem längeren Zeitraum die Reason-Code-Verteilung read-only auswerten. Danach vor jeder Freigabeumschaltung einen eigenen Stock-Datenvertrag für aktuellen Preis, zeitgestempelte Kerzenhistorie und vollständigen richtungskonsistenten Risikoplan entwerfen und testen. Decision-/Signalpfad sowie Telegram bis dahin unverändert lassen.

## Aktuelle Aufgabe: Kompakte Feature-Qualität und Decision-Gate-Audit-Observer integrieren

### Datum und Uhrzeit

8. August 2026, 22:52 Uhr, Europe/Berlin (`+02:00`)

### Ziel der Aufgabe

Den zuvor definierten Decision-Gate-Vertrag sicher an die bestehende Payloadkette anbinden: ausschließlich die kompakte Feature-Qualität bis Brain/Decision erhalten und einen separaten, standardmäßig deaktivierten Audit-Observer ergänzen. Den bestehenden Decision-/Signalpfad, Telegram, Tracker und jede Ordersemantik unverändert lassen.

### Durchgeführte Arbeiten

- Gemeinsame Projektion `project_feature_data_quality()` als einzige Grenze für Status, Zähler, Reihenfolge und Warmup eingeführt; vollständige Features, Warnungen und Verletzungsdetails bleiben ausgeschlossen.
- `compact_market_payload()` erhält `feature_quality`, sodass dieselbe begrenzte Sicht in Brain-History, `BRAIN_DECISION_RECEIVED`, Decision, Signal und deren Ledger gelangt.
- Neuen `DecisionGateAuditAdapter` ergänzt. Er abonniert nur `BRAIN_DECISION_RECEIVED`, bewertet mit dem Version-1-Vertrag, publiziert nur `DECISION_GATE_EVALUATED` und persistiert einen getrennten Auditdatensatz.
- Audit-Ledger auf 5 MiB Standardgröße und höchstens vier Archive begrenzt; Duplikatschutz, Health-Zähler, Heartbeat, Stop-Semantik und Fehlerereignis ergänzt.
- Observer standardmäßig deaktiviert. Aktivierung verlangt ausdrücklich gesetzte Probability- und Confidence-Schwellen; ohne diese bricht die Adapterkonstruktion fail-closed ab.
- Orchestrator-Reihenfolge bei Aktivierung: Brain → Gate-Observer → unveränderter Decision Core. Das Gate blockiert, ersetzt oder verändert kein Ereignis.
- `.env.example`, Systemzustand, Architektur, Verträge, bekannte Probleme und nächste Schritte aktualisiert.

### Veränderte Dateien

- `.env.example`
- `config.py`
- `decision_gate_contract.py`
- `event_payload_contract.py`
- `feature_data_quality_contract.py`
- `orchestrator.py`
- `tests/test_brain_adapter.py`
- `tests/test_config.py`
- `tests/test_decision_signal_adapter.py`
- `tests/test_event_payload_contract.py`
- `docs/CURRENT_SYSTEM_STATE.md`
- `docs/ARCHITECTURE.md`
- `docs/DECISION_GATE_CONTRACT.md`
- `docs/EVENT_PAYLOAD_CONTRACT.md`
- `docs/KNOWN_PROBLEMS.md`
- `docs/NEXT_STEPS.md`
- `docs/SESSION_HANDOVER.md`

### Neue Dateien

- `adapters/decision_gate_audit_adapter.py`
- `tests/test_decision_gate_audit_adapter.py`

### Ausgeführte Befehle

- Pflichtdokumente und die drei Verträge vollständig gelesen.
- Relevante Producer, Consumer, Konfiguration, Orchestrator und Tests mit `rg` und `Get-Content` geprüft.
- `git switch -c agent/integrate-decision-gate-observer`
- Gezielte Unittests über `.\.venv\Scripts\python.exe -m unittest ...`
- Gesamtsuite über `.\.venv\Scripts\python.exe -m unittest discover -s tests -p "test_*.py"`
- Isolierte Wiederholung des Learning-Cache-Tests.
- `git diff --check`, Status- und Diffprüfung.

### Ausgeführte Tests und tatsächliche Ergebnisse

- Gezielte Integrationssuite: **35/35 bestanden**.
- Erster Gesamtlauf: **265 Tests ausgeführt; 264 fachlich bestanden, 1 Cleanup-Fehler**. Fehler war `WinError 145` beim Entfernen eines temporären Verzeichnisses nach `test_legacy_cache_without_metric_contract_is_rebuilt`.
- Derselbe Learning-Cache-Test direkt isoliert: **1/1 bestanden**.
- Vollständige Wiederholung: **265/265 bestanden** in 43,517 Sekunden.

### Bekannte Fehler

- KP-019: sporadischer Windows-`TemporaryDirectory`-Cleanupfehler im ersten vollständigen Testlauf; isolierte und vollständige Wiederholung waren grün.
- Der aktive Decision Core besitzt weiterhin kein produktives Gate und erstellt aus jedem Brain-Ereignis Decision und Signal.
- Telegram liegt weiterhin nicht hinter einer final freigegebenen Entscheidungskette und muss deaktiviert/Dry-Run bleiben.

### Getroffene Architekturentscheidungen

- `feature_quality` ist die einzige erlaubte Qualitätsprojektion jenseits der Feature-Grenze; der vollständige `features`-Block bleibt verboten.
- Audit und aktiver Decision Core laufen parallel. Der Observer ist ausdrücklich kein Filter und besitzt keine Signal-, Telegram- oder Orderberechtigung.
- Keine versteckten Produktschwellen: beide Schwellen sind optional in der Konfiguration, aber zwingend für eine Aktivierung.
- Auditretention ist lokal begrenzt; vorhandene History- und Runtime-Daten werden nicht migriert, geändert oder gelöscht.

### Nicht abgeschlossene Punkte

- Noch kein Live-Neustart mit dem neuen Code und keine Observer-Liveauswertung.
- Noch keine fachlich bestätigten Probability-/Confidence-Schwellen.
- Keine Umschaltung des aktiven Decision-/Signal- oder Telegrampfads.
- Änderungen liegen vollständig geprüft auf `agent/integrate-decision-gate-observer`; sie werden als lokaler Aufgabencommit abgeschlossen und nicht veröffentlicht.

### Exakter nächster sinnvoller Arbeitsschritt

Den Benutzer ausdrücklich nach den diagnostischen Probability-/Confidence-Schwellen fragen; erst mit dieser Freigabe den Observer kontrolliert aktivieren und mehrere Livezyklen rein beobachtend auswerten.

## Aktuelle Aufgabe: Fail-closed Decision-Gate-Vertrag Version 1 definieren

### Datum und Uhrzeit

8. August 2026, 22:35 Uhr, Europe/Berlin (`+02:00`)

### Ziel der Aufgabe

Nach Merge und Liveverifikation des Feature-Datenqualitätsvertrags den nächsten freigegebenen Schritt klein und sicher beginnen: den tatsächlichen Brain-/Decision-/Tracker-/Telegram-Fluss prüfen und einen ausführbaren, rein beobachtenden und fail-closed Decision-Gate-Vertrag definieren. Noch keine aktive EventBus-Integration, keine Telegram-Kopplung, keine reale Orderausführung und keine Änderung bestehender Runtime- oder Historydaten.

### Durchgeführte Arbeiten

- Pflicht-, Event-Payload- und Feature-Datenqualitätsdokumentation sowie die tatsächlichen Producer und Consumer geprüft.
- Bestätigt, dass `DecisionSignalAdapter` heute jedes `BRAIN_DECISION_RECEIVED` unmittelbar in `DECISION_CREATED` und `SIGNAL_CREATED` überführt und dabei `ready_for_telegram=true` setzt, ohne Datenqualitäts-, Risiko- oder Confidence-Gate.
- Bestätigt, dass `TelegramAdapter` weiterhin Crypto-/Stock-Analysen und simulierte Trade-Updates direkt abonniert. Der laufende Dienst blieb sicher `enabled=false`, `dry_run=true`, `messages_sent=0`.
- Migrationslücke identifiziert: Der vollständige Featureblock wird an der kompakten Brain-Grenze korrekt entfernt; dadurch erreicht `features.metadata.data_quality` den Decision-Pfad heute noch nicht.
- Ausführbaren Vertrag `pandorickki.decision-gate` Version 1 erstellt. `DecisionGatePolicy` verlangt Probability- und Confidence-Schwellen ausdrücklich und besitzt dafür keine versteckten Defaults.
- Fail-closed Regeln für Markt, Symbol, LONG/SHORT, Preis, Probability, Confidence, Fakten, Featurefehler, Qualitätsschema/-status, verifizierte Reihenfolge, vollständigen Warmup und richtungskonsistenten Stop/Take-Profit definiert.
- Kompakte `feature_quality`-Projektion erstellt, die nur Gate-relevante Qualitätszähler sowie Order- und Warmupstatus übernimmt und keinen vollständigen Featureblock persistiert.
- Deterministische Reason Codes und nur zwei Bewertungszustände (`QUALIFIED`, `BLOCKED`) definiert. Version 1 setzt stets `mode=OBSERVER`, `release_status=OBSERVER_ONLY`, `ready_for_telegram=false` und `order_execution_allowed=false`.
- Dokumentation und verbindliche AGENTS-Leseregel aktualisiert. Das Modul ist bewusst nicht an EventBus, Decision Core, Tracker oder Telegram angeschlossen.

### Veränderte Dateien

- `AGENTS.md`
- `docs/ARCHITECTURE.md`
- `docs/CURRENT_SYSTEM_STATE.md`
- `docs/KNOWN_PROBLEMS.md`
- `docs/NEXT_STEPS.md`
- `docs/SESSION_HANDOVER.md`

### Neue Dateien

- `decision_gate_contract.py`
- `tests/test_decision_gate_contract.py`
- `docs/DECISION_GATE_CONTRACT.md`

### Ausgeführte Befehle

- Vollständige Lektüre der Pflicht- und relevanten Vertragsdokumentation.
- `rg`-/`Get-Content`-Bestandsaufnahme von Brain, Decision Core, Outcome Tracker, Crypto Trade Tracker, Telegram, Event-Payload-Vertrag sowie zugehörigen Tests.
- Read-only Abruf von `http://127.0.0.1:8000/api/status` zur Bestätigung des aktiven Ereignisflusses und der sicheren Telegram-Einstellungen.
- Neuer lokaler Branch `agent/define-decision-gate-contract` auf dem vorherigen lokalen Liveverifikations-Dokumentationscommit erstellt.
- Test-first Unittest-Lauf vor und nach Implementierung, Python-Syntaxprüfung, angrenzende Regressionen, vollständige Testsuite sowie `git diff --check`.

### Ausgeführte Tests

- Vor Implementierung: `python -m unittest tests.test_decision_gate_contract -v` erwartungsgemäß rot wegen fehlendem Vertragsmodul.
- Nach Implementierung: `.\.venv\Scripts\python.exe -m unittest tests.test_decision_gate_contract -v`.
- Syntaxprüfung der Gate-, Feature-Qualitäts-, Event-Payload-, Brain- und Decision-Module.
- 48 angrenzende Gate-/Qualitäts-/Payload-/Brain-/Decision-/Outcome-/Trade-Tracker-Tests.
- Vollständige Unittest-Discovery.
- `git diff --check`.

### Tatsächliche Testergebnisse

- Vorheriger Reproduktionslauf: 1 Importfehler, weil `decision_gate_contract.py` noch nicht existierte.
- Danach 10/10 Decision-Gate-Vertragstests bestanden.
- Abgedeckt sind qualifizierter Observerfall, fehlende Qualität, Stock `WARN/UNVERIFIED/WARMING`, WAIT/HOLD, fehlende Fakten, Featurefehler, Confidence-/Richtungskonflikte, ungültiger Stop/Take-Profit, kompakte Qualitätsprojektion sowie unveränderliche Telegram-/Order-Sperre.
- Python-Syntaxprüfung und nach der letzten Grenzfallkorrektur 49/49 angrenzende Regressionen in 0,815 Sekunden bestanden.
- Vollständige Suite nach der letzten Änderung: 261/261 Tests in 45,836 Sekunden bestanden; nur die bekannten externen `datetime.utcnow()`-DeprecationWarnings.
- `git diff --check` bestand; nur normale Windows-LF/CRLF-Hinweise.
- Der bestehende Pandorickki-Prozess wurde nicht neu gestartet und nicht verändert. Beim read-only Statusabruf liefen Plattform und alle zehn Services `OK`; Telegram war deaktiviert/Dry-Run und hatte null Nachrichten gesendet.

### Bekannte Fehler

- KP-004 bleibt in der aktiven Architektur offen: Der neue Vertrag ist getestet, aber noch nicht als Observer verdrahtet.
- KP-005 bleibt offen: Telegram abonniert weiterhin vor-gelagerte Analyse-/Tradeereignisse direkt, ist aber sicher deaktiviert/Dry-Run.
- Die kompakte Marktprojektion enthält noch keine `feature_quality`; ohne diese Projektion blockiert der Vertrag korrekt mit `DG_QUALITY_MISSING`.
- Der Stock-Einzelsnapshot blockiert unter der sicheren Version-1-Grundeinstellung korrekt wegen `WARN`, `UNVERIFIED` und `WARMING`.
- Die übrigen Einträge in `docs/KNOWN_PROBLEMS.md` bestehen unverändert.

### Getroffene Architekturentscheidungen

- Vertrag, Observer-Integration und spätere Freigabeumschaltung sind getrennte Arbeitsschritte.
- Probability- und Confidence-Schwellen müssen explizit konfiguriert und fachlich bestätigt werden; der Vertrag erfindet keinen produktiven Standardwert.
- Qualität wird später nur als kompakte Projektion weitergereicht. Vollständige Features, Kerzen und Raw Results bleiben aus Brain-/Decision-Payloads ausgeschlossen.
- Ein technisch qualifizierter Version-1-Kandidat ist noch keine Meldungs- oder Tradefreigabe.
- Commodity bleibt mangels heutiger Feature-Qualitätsanbindung fail-closed blockiert.

### Nicht abgeschlossene Punkte

- Die neue Implementierung, die Dokumentation und der vorherige Liveverifikations-Dokumentationscommit sind lokal und noch nicht in das öffentliche GitHub-Repository gepusht.
- `feature_quality` wird noch nicht durch den kompakten Marktvertrag und Brain weitergereicht.
- Es existiert noch kein EventBus-Subscriber, kein Gate-Audit-Ledger und keine Liveauswertung der Reason-Code-Verteilung.
- Der heutige Decision-/Signalpfad und Telegram wurden bewusst nicht umgestellt.

### Exakter nächster sinnvoller Arbeitsschritt

Den kompakten Event-Payload-Vertrag additiv um eine begrenzte `feature_quality`-Projektion erweitern, diese im Analyse-zu-Brain-Pfad erhalten und mit Consumer-/Bulk-Ausschluss-/Legacy-Tests absichern. Danach einen separaten, rein auditierenden Decision-Gate-Observer planen; bestehende Decisions, Signals, Tracker und Telegram noch nicht umschalten.

---

## Aktuelle Aufgabe: Feature-Datenqualitätsvertrag mergen und live verifizieren

### Datum und Uhrzeit

8. August 2026, 22:26 Uhr, Europe/Berlin (`+02:00`)

### Ziel der Aufgabe

Den vollständig geprüften Feature-Datenqualitätsvertrag aus PR #22 nach ausdrücklicher Freigabe nach `main` mergen, den lokalen Hauptstand synchronisieren, PandorickKi kontrolliert mit sicheren Laufzeitwerten neu starten und Crypto-/Stock-Qualitätsmetadaten sowie Control Center live prüfen. Keine echten Trades aktivieren, Telegram deaktiviert/Dry-Run lassen und keine History löschen oder umschreiben.

### Durchgeführte Arbeiten

- PR #22 über GitHub-App und CLI auf exakten Scope, Basis `main`, Head `3d2ab1b434a475ffa2434a8379e48d657a1d3626`, Mergeability und Dateiliste geprüft. 13 erwartete Code-, Test- und Dokumentationsdateien; keine Runtime-, History- oder Secret-Dateien.
- PR #22 nach ausdrücklicher Freigabe auf Ready gesetzt und per Head-geschütztem CLI-Fallback gemergt, weil die GitHub-App für Ready und Merge jeweils `403 Resource not accessible by integration` erhielt.
- Merge als GitHub-Commit `14e19bf0a4e79860732ff3b6bba4135a2504b909` verifiziert und lokalen `main` ausschließlich per Fast-Forward auf `origin/main` synchronisiert.
- Alten Webprozess über `POST /api/control/stop` kontrolliert beendet; Port 8000 war nach ungefähr 0,25 Sekunden ohne harten Prozessabbruch frei.
- Runtime-Preflight bestanden und PandorickKi verborgen aus `.venv` mit Live-Crypto, Live-Aktien, NeuroBrain aktiv, Telegram deaktiviert und Dry-Run aktiv gestartet. Neue stdout-/stderr-Logs mit Zeitstempel erzeugt; beide blieben leer.
- Vier vollständige Produktionszyklen per API geprüft: Crypto je drei Ergebnisse, Stock je fünf, Plattform und alle zehn Services `OK`, null Sitzungsfehler, null STALE-Services, NeuroBrain Queue/Drops null, Telegram null gesendete Nachrichten.
- Qualitätsmetadaten direkt an den Adaptern geprüft, weil Browser-/API-Payloads große Featureblöcke absichtlich entfernen. Crypto verwendete echte öffentliche Binance-Daten; Stock lief isoliert im temporären Testverzeichnis, damit keine zweite Instanz bestehende Aktien-History beschreibt.
- Bereits geöffnetes Control Center nach dem Prozesswechsel neu geladen und visuell geprüft: WebSocket verbunden, aktuelle BTC-/ETH-/XRP- und Aktienwerte, alle zehn Services `OK`, Telegram `false/true`, keine sichtbaren Fehler und keine Browser-Warnungen.
- Den bereits bestehenden, nicht veröffentlichten Handover-Commit `a9f5a95` unverändert auf seinem früheren Feature-Branch erhalten. Die neue Abschlussdokumentation liegt auf `agent/document-feature-quality-live-verification`.

### Veränderte Dateien

- `docs/CURRENT_SYSTEM_STATE.md`
- `docs/SESSION_HANDOVER.md`
- `docs/KNOWN_PROBLEMS.md`
- `docs/NEXT_STEPS.md`

### Neue Dateien

- Keine Projektdateien. Zwei neue normale Runtime-Logdateien wurden für den gestarteten Prozess angelegt und blieben leer; sie sind keine Commitdateien.

### Ausgeführte Befehle

- Pflichtdokumentation und GitHub-/Browser-Workflow vollständig gelesen.
- GitHub-App-Prüfung, `gh pr checks/view/ready/merge`, Mergeverifikation und Main-SHA-Prüfung.
- `git fetch origin`, Wechsel auf `main`, `git merge --ff-only origin/main` und neuer Dokumentationsbranch.
- Read-only API-Abfragen für Health, Status und Events; kontrollierter `POST /api/control/stop`; Runtime-Preflight; verborgener Start von `.venv\Scripts\python.exe main.py --headless --web` mit sicheren Umgebungswerten.
- Isolierter Adapter-Probelauf für Crypto und Stock sowie Browser-DOM-/Konsolenprüfung des lokalen Control Centers.

### Ausgeführte Tests

- Bereits vor Merge: 251/251 vollständige Tests und isolierter Binance-Realtest.
- Nach Merge: 30/30 gezielte Feature-, Crypto-, Stock- und Integrationsregressionen.
- Runtime-Preflight.
- Vier vollständige Produktionszyklen.
- Direkte Qualitätsmetadatenprüfung für BTCUSDT und fünf Stock-Symbole.
- Visuelle Control-Center- und Browserkonsolenprüfung.

### Tatsächliche Testergebnisse

- PR #22 gemergt; `origin/main` und lokaler Ausgangsstand auf `14e19bf`.
- 30/30 gezielte Tests in 2,404 Sekunden bestanden; nur bekannte externe `datetime.utcnow()`-DeprecationWarnings.
- Runtime-Preflight mit Python 3.12.13 bestanden.
- Crypto-Qualität: `PASS`, 240 Eingänge/240 akzeptiert, null entfernt, null Duplikate, null Verstöße, Reihenfolge `VERIFIED`, Warmup `READY`, kein Featurefehler.
- Stock-Qualität im sicheren isolierten Einzelsnapshot-Pfad: `WARN`, 1/1 akzeptiert, null Verstöße, Reihenfolge `UNVERIFIED`, Warmup `WARMING`, kein Featurefehler. Das entspricht dem dokumentierten rückwärtskompatiblen Fallback.
- Produktiv: Crypto vier Zyklen mit je drei Ergebnissen; Stock vier Zyklen mit je fünf Ergebnissen; zehn Services `OK`; `error_count=0`; keine STALE-Services; NeuroBrain Queue/Drops null; Telegram deaktiviert/Dry-Run und `messages_sent=0`.
- Browser: Control Center per WebSocket verbunden, System `OK`, aktuelle Marktdaten, keine sichtbaren Fehler und keine Console-Warnungen/-Fehler.

### Bekannte Fehler

- Keine neue Regression und kein neuer Sitzungsfehler festgestellt.
- KP-007 ist technisch behoben und live verifiziert.
- Der Stock-Einzelsnapshot besitzt weiterhin keinen Kerzenzeitstempel und keinen vollständigen Indikator-Warmup; dies ist jetzt sichtbar und muss vom Decision Gate fachlich behandelt werden.
- Bekannte externe `datetime.utcnow()`-DeprecationWarnings und die übrigen offenen Punkte in `docs/KNOWN_PROBLEMS.md` bleiben bestehen.

### Getroffene Architekturentscheidungen

- Der Datenqualitätsvertrag bleibt technische Eingangsgrenze; er ist kein Trading- oder Nachrichtenfreigabe-Gate.
- Browser und kompakte Events bleiben frei von großen Featureblöcken. Qualitätsdetails werden intern geprüft und sollen für ein späteres Gate nur als kompakte, ausdrücklich benötigte Projektion weitergereicht werden.
- Das kommende Decision Gate muss fail-closed arbeiten: unzureichende oder unverifizierte Daten dürfen nicht still als freigegebene Meldung gelten.
- Telegram bleibt bis hinter einer geprüften finalen Entscheidungskette deaktiviert/Dry-Run; reale Orderausführung bleibt ausgeschlossen.

### Nicht abgeschlossene Punkte

- Diese vier Abschlussdokumente sind lokal committed, aber noch nicht veröffentlicht.
- Der fachliche Decision-Gate-Vertrag ist noch nicht entworfen oder implementiert.
- Stock besitzt derzeit nur den rückwärtskompatiblen Einzelsnapshot für Features; eine echte zeitgestempelte Aktien-Kerzenhistorie ist eine spätere Datenquellenverbesserung, nicht Teil dieses Abschlusses.

### Exakter nächster sinnvoller Arbeitsschritt

Zuerst den Feld- und Zustandsvertrag für ein rein beobachtendes, fail-closed Decision Gate entwerfen: Eingangsereignis, benötigte Feature-/Qualitätsprojektion, zulässige Qualitäts- und Warmupzustände, Fakten-/Risiko-/Confidence-/Konfliktregeln, eindeutige Reason Codes und Ausgangsereignisse. Noch keine Telegram-Anbindung und keine reale Orderausführung implementieren.

---

## Aktuelle Aufgabe: Feature-Datenqualitätsvertrag Version 1 umsetzen

### Datum und Uhrzeit

8. August 2026, 21:22 Uhr, Europe/Berlin (`+02:00`)

### Ziel der Aufgabe

Den nächsten freigegebenen Entwicklungsschritt umsetzen: einen versionierten, rückwärtskompatiblen und getesteten Vertrag für Feature-Eingangsdaten mit Sortierung, Duplikaten, OHLC-Konsistenz, Non-Finite-Werten, Mindestkerzen und Warmup. Keine History verändern, kein Decision Gate vorziehen und Telegram sowie reale Trades unangetastet lassen.

### Durchgeführte Arbeiten

- Pflichtdokumentation, Event-Payload-Vertrag, Feature Engine, Crypto-/Stock-Adapter, Crypto-Marktdatenservice und sämtliche direkten Feature-Tests geprüft.
- Bestehende Kompatibilitätsgrenze identifiziert: Crypto besitzt Provider-Zeitstempel, verlor sie aber bei der Normalisierung; Stock kann bewusst auf einen zeitstempellosen Einzelfakten-Snapshot zurückfallen.
- Ausführbaren Vertrag `pandorickki.feature-data-quality` Version 1 in `feature_data_quality_contract.py` ergänzt.
- OHLCV-Aliase, endliche/positive Preise, OHLC-Konsistenz, nicht negatives Volumen und Zeitstempelaliase validiert. Ungültige Zeilen werden gezählt und nur bei weiterhin erreichter Mindestanzahl kontrolliert entfernt.
- Vollständig zeitgestempelte Reihen aufsteigend sortiert und doppelte Zeitstempel deterministisch per `keep_last` reduziert. Fehlende oder teilweise Zeitstempel bleiben in Providerreihenfolge und werden ausdrücklich `UNVERIFIED` markiert.
- Konfigurierbare Mindestkerzen, optionale Zeitstempelpflicht und expliziten Warmupstatus eingeführt. Standard: mindestens eine valide Kerze für den vorhandenen Stock-Fallback, vollständiger Warmup am größten aktiven Fenster, derzeit 200.
- Vertrag in `FeatureEngine.compute()` integriert und Qualitätsbericht unter `metadata.data_quality` ausgegeben. Nicht endliche optionale Kontextwerte werden entfernt.
- Crypto-Marktdatennormalisierung um den vorhandenen Binance-/Bitget-Zeitstempel ergänzt.
- Neue Regressionstests zuerst gegen den fehlenden Vertrag ausgeführt und danach grün gestellt.
- Architektur-, Systemzustands-, Problem-, Plan- und Vertragsdokumentation aktualisiert. `AGENTS.md` verlangt den Vertrag künftig vor Feature-/OHLCV-Änderungen.

### Veränderte Dateien

- `AGENTS.md`
- `adapters/crypto_market_data_service.py`
- `features/feature_engine.py`
- `tests/test_crypto_market_data_service.py`
- `tests/test_feature_engine.py`
- `docs/CURRENT_SYSTEM_STATE.md`
- `docs/SESSION_HANDOVER.md`
- `docs/ARCHITECTURE.md`
- `docs/KNOWN_PROBLEMS.md`
- `docs/NEXT_STEPS.md`

### Neue Dateien

- `feature_data_quality_contract.py`
- `tests/test_feature_data_quality_contract.py`
- `docs/FEATURE_DATA_QUALITY_CONTRACT.md`

### Ausgeführte Befehle

- Vollständiges Lesen der Pflicht- und relevanten Vertragsdateien sowie `rg`-/`Get-Content`-Prüfung der tatsächlichen Producer, Adapter, Consumer und Tests.
- Separaten Branch `agent/feature-data-quality-contract` direkt von aktualisiertem `main` erstellt; der unabhängige lokale PR-#21-Statusnachtrag blieb auf seinem eigenen Branch erhalten.
- Gezielte Unittest-Läufe vor und nach Implementierung.
- `py_compile`, `git diff --check`, Runtime-Preflight und vollständige Unittest-Discovery.
- Isolierter read-only Realtest mit `CryptoMarketDataService.fetch('BTCUSDT', '15m', 240)` und anschließender lokaler Feature-Berechnung.

### Ausgeführte Tests

- Vorheriger Reproduktionslauf: fehlendes Vertragsmodul, fehlende Qualitätsmetadaten und fehlender Crypto-Zeitstempel erwartungsgemäß rot.
- 14/14 erste gezielte Vertrags-/Feature-/Marktdaten-/Adaptertests.
- 30/30 erweiterte Feature-, Crypto-, Stock- und Vollintegrationstests.
- Python-Syntaxprüfung der drei geänderten Produktionsmodule.
- Runtime-Preflight.
- Vollständige Testsuite.
- Isolierte Prüfung mit 240 realen öffentlichen BTCUSDT-Kerzen.

### Tatsächliche Testergebnisse

- 14/14 erste gezielte Tests bestanden.
- 30/30 erweiterte gezielte Tests in 3,740 Sekunden bestanden; nur bekannte externe `datetime.utcnow()`-DeprecationWarnings.
- `py_compile` und `git diff --check` bestanden.
- Runtime-Preflight bestanden mit Python 3.12.13 aus `.venv` und verfügbarer Legacy-Crypto-Pipeline.
- Vollständige Suite: 251/251 Tests in 47,410 Sekunden bestanden.
- Realtest: Quelle Binance, 240 Eingangszeilen, 240 akzeptiert, 0 entfernt, 0 Duplikate, 0 Verstöße, Reihenfolge `VERIFIED`, Warmup `READY`, Gesamtstatus `PASS`.

### Bekannte Fehler

- Keine neue Regression festgestellt.
- KP-007 ist technisch implementiert und getestet, aber noch nicht gemergt und noch nicht durch einen vollständigen Plattformneustart verifiziert.
- Bekannte externe `datetime.utcnow()`-DeprecationWarnings bestehen unverändert.
- Die weiteren offenen Punkte aus `docs/KNOWN_PROBLEMS.md` bleiben bestehen.

### Getroffene Architekturentscheidungen

- Datenqualität ist eine eigene versionierte Eingangsgrenze vor der Feature-Berechnung, nicht Teil eines späteren fachlichen Decision Gates.
- `keep_last` ist die einzige Version-1-Duplikatstrategie, damit korrigierte spätere Providerzeilen deterministisch Vorrang haben.
- Ohne vollständige Zeitstempel wird keine Reihenfolge geraten. Rückwärtskompatible Verarbeitung bleibt möglich, aber sichtbar `UNVERIFIED`.
- Mindestanzahl und vollständiger Indikator-Warmup sind getrennte Begriffe. Einzelsnapshots bleiben kompatibel, behaupten aber keine volle Indikatorreife.
- Qualitätsmetadaten sind additiv. Bestehende Eventverträge, Decisions, History, Telegram und Ordergrenzen bleiben unverändert.

### Nicht abgeschlossene Punkte

- Implementierung und Dokumentation sind lokal als Commit `9470b47` (`Implement feature data quality contract`) gesichert.
- Der Push in das öffentliche Repository `cRioshy/Pando` wurde vom Sicherheitscheck gestoppt, weil für die öffentliche Veröffentlichung der 13 Code-, Test- und Dokumentationsdateien noch eine ausdrückliche Benutzerfreigabe erforderlich ist. Es wurde kein Umgehungsversuch unternommen.
- Vollständiger Plattformneustart mit dem neuen Branch steht noch aus; der isolierte öffentliche Crypto-Realtest ist bestanden.
- Das fachliche Decision Gate wurde bewusst noch nicht begonnen.

### Exakter nächster sinnvoller Arbeitsschritt

Nach ausdrücklicher Freigabe für die öffentliche Veröffentlichung Commit `9470b47` auf `agent/feature-data-quality-contract` zu `cRioshy/Pando` pushen und einen Draft-PR gegen `main` erstellen. Nach Merge Pandorickki kontrolliert neu starten und neue Crypto-/Stock-`metadata.data_quality` prüfen. Erst danach den fachlichen Decision-Gate-Vertrag entwerfen.

---

## Aktuelle Aufgabe: Post-Merge-Liveübergabe auf GitHub veröffentlichen

### Datum und Uhrzeit

8. August 2026, 17:10 Uhr, Europe/Berlin (`+02:00`)

### Ziel der Aufgabe

Nach erneuerter GitHub-Anmeldung und ausdrücklicher Freigabe für das öffentliche Repository ausschließlich den vorbereiteten Dokumentationsbranch veröffentlichen und einen Draft-Pull-Request gegen `main` erstellen. Nichts mergen und weder Produktcode noch Runtime-Daten verändern.

### Durchgeführte Arbeiten

- Pflichtdokumentation, Git-Branch, Remote, Commit und Dateiscope erneut geprüft.
- GitHub-Anmeldung außerhalb der lokalen Netzwerksperre als aktives Konto `cRioshy` bestätigt; Ziel als öffentliches Repository `cRioshy/Pando` mit Defaultbranch `main` verifiziert.
- Nach ausdrücklicher Benutzerfreigabe Branch `agent/document-post-merge-live-verification` mit Commit `2f50881a368e714236ac825139267bbfe8205de5` zu `origin` gepusht.
- GitHub-App versuchte bevorzugt, den PR anzulegen, erhielt aber `403 Resource not accessible by integration`. Danach gemäß Veröffentlichungsworkflow die authentifizierte GitHub-CLI als Fallback verwendet.
- Draft-PR #20 gegen `main` erstellt und anschließend als offen, Draft, mergebar und auf den richtigen Head geprüft.
- `main` blieb unverändert auf `381229a66c5ac8ed121297457fa4315155c55176`.

### Veränderte Dateien

- `docs/SESSION_HANDOVER.md`
- `docs/NEXT_STEPS.md`

### Neue Dateien

- Keine dauerhaften Dateien. Die temporäre PR-Beschreibungsdatei wurde nach erfolgreicher PR-Erstellung wieder entfernt.

### Ausgeführte Befehle

- Vollständiges Lesen der fünf Pflichtdokumente und des GitHub-Veröffentlichungsworkflows.
- `gh --version`, `gh auth status`, `gh repo view`, Git-Status-, Remote-, Branch-, Commit-, Scope- und Diffprüfungen.
- `git push -u origin agent/document-post-merge-live-verification`.
- Bevorzugter PR-Versuch über die GitHub-App; danach `gh pr create --draft` als dokumentierter Fallback.
- `gh pr view 20`, GitHub-Main-Head- und lokale/Remote-Refprüfungen.

### Ausgeführte Tests

- `git diff origin/main...HEAD --check` vor der Veröffentlichung.
- Branch-, Commit-, Dateiscope- und Remoteprüfung.
- GitHub-Authentifizierungs-, Repository-, Draft-, Basisbranch-, Headbranch-, Head-SHA-, Mergeability- und Main-Unverändert-Prüfung.
- Keine Softwaretests, weil ausschließlich bereits geprüfte Dokumentation veröffentlicht und kein Produktcode geändert wurde.

### Tatsächliche Testergebnisse

- GitHub-Anmeldung: aktiv als `cRioshy`, Git-Protokoll HTTPS, erforderlicher `repo`-Scope vorhanden.
- Repository: `cRioshy/Pando`, Sichtbarkeit `PUBLIC`, Defaultbranch `main`.
- Gepushter Branch: `agent/document-post-merge-live-verification`.
- Veröffentlichter Commit vor diesem Abschlussnachtrag: `2f50881a368e714236ac825139267bbfe8205de5`.
- Draft-PR #20: `OPEN`, `isDraft=true`, `MERGEABLE`, Basis `main`, Head `agent/document-post-merge-live-verification`.
- PR-URL: `https://github.com/cRioshy/Pando/pull/20`.
- `main` blieb auf `381229a66c5ac8ed121297457fa4315155c55176`; kein Merge wurde ausgeführt.

### Bekannte Fehler

- Die GitHub-App besitzt für die PR-Erstellung weiterhin nicht die erforderliche Berechtigung; die authentifizierte GitHub-CLI funktionierte als vorgesehener Fallback.
- Die offenen Produktprobleme aus `docs/KNOWN_PROBLEMS.md` bestehen unverändert.

### Getroffene Architekturentscheidungen

- Keine Produkt- oder Systemarchitektur geändert.
- Veröffentlichung enthält ausschließlich die vier bereits freigegebenen technischen Übergabedokumente sowie diesen verpflichtenden Dokumentationsnachtrag.
- PR #20 bleibt Draft. `main`, Telegram-Konfiguration und reale Orderausführung wurden nicht verändert.

### Nicht abgeschlossene Punkte

- Draft-PR #20 ist bewusst nicht gemergt.
- Der Feature-Datenqualitätsvertrag wurde noch nicht begonnen.

### Exakter nächster sinnvoller Arbeitsschritt

Draft-PR #20 prüfen und nur nach ausdrücklicher Freigabe nach `main` mergen. Danach den Feature-Engine-Datenfluss und alle Consumer read-only inventarisieren und zuerst einen versionierten Datenqualitätsvertrag für Sortierung, Duplikate, OHLC-Konsistenz, Non-Finite-Werte, Mindestkerzen und Warmup entwerfen.

---

## Aktuelle Aufgabe: Gemergten `main`-Stand kontrolliert neu starten und live prüfen

### Datum und Uhrzeit

8. August 2026, 16:54 Uhr, Europe/Berlin (`+02:00`)

### Ziel der Aufgabe

Den frisch konsolidierten und dokumentierten `main`-Stand kontrolliert neu starten und im realen lokalen Betrieb prüfen, ob Webdienst, Marktadapter, interne Services, NeuroBrain, Storage und Sicherheitskonfiguration sauber laufen. Keine Produktlogik ändern, keine echten Trades aktivieren und keine History löschen.

### Durchgeführte Arbeiten

- `main` als sauber und bytegleich mit `origin/main` auf `381229a66c5ac8ed121297457fa4315155c55176` bestätigt.
- Runtime-Preflight mit der projektlokalen Python-3.12.13-Umgebung ausgeführt und die laufende Instanz über Health-, Status- und Konfigurations-API geprüft.
- Den eingebauten Control-Center-Stop verwendet. Port 8000 wurde nach 15,041 Sekunden frei; PID 4648 endete anschließend selbstständig, ohne harten Prozessabbruch.
- Starterkonfiguration aus `start_pandorick_web.bat` geprüft und genau einen neuen versteckten Prozess über `.venv\Scripts\python.exe main.py --headless --web` gestartet. Telegram blieb deaktiviert und im Dry-Run; Live-Crypto und Live-Aktien blieben aktiviert.
- Sechs vollständige Crypto- und Stockzyklen über die lokalen APIs beobachtet. Livepreise, Servicezustände, Journal, NeuroBrain-Queue und Telegram-Zähler geprüft.
- Storage-Endpunkt gezielt ausgewertet: physische und logische Summen, Scanfortschritt und die zwei bekannten beschädigten Stock-Backup-JSONs geprüft.
- Server-stdout/stderr sowie den Git-Arbeitsbaum geprüft. Ein einmaliger lokaler `ConnectionResetError` aus der aggressiven Readiness-Abfrage wurde als niedrig priorisiertes KP-018 dokumentiert; danach keine Wiederholung.
- Die Browser-Steuerung gemäß Browser-Skill vorbereitet. Der Zugriff auf `http://127.0.0.1:8000/` wurde von der Browser-Sicherheitsrichtlinie blockiert und nicht umgangen; deshalb erfolgte die Sichtprüfung in dieser Aufgabe über die lokalen HTTP-APIs und Serverlogs.
- Die vier Übergabedokumente als lokalen Commit auf `agent/document-post-merge-live-verification` gesichert. Die geplante Veröffentlichung wurde vor dem Push gestoppt, weil `gh auth status` den gespeicherten Token als ungültig meldete.

### Veränderte Dateien

- `docs/CURRENT_SYSTEM_STATE.md`
- `docs/SESSION_HANDOVER.md`
- `docs/KNOWN_PROBLEMS.md`
- `docs/NEXT_STEPS.md`

### Neue Dateien

- Keine Projektdateien. Die Runtime erzeugte ausschließlich ignorierte Log- und Betriebsdaten im vorhandenen Runtime-Bereich.

### Ausgeführte Befehle

- Git-Status-, Branch-, Remote- und Commit-Prüfungen.
- `.venv\Scripts\python.exe scripts\runtime_preflight.py`.
- Lokale HTTP-Abfragen gegen `/api/health`, `/api/status`, `/api/control/stop` und `/api/statistics/storage`. Ein zusätzlicher Probeaufruf von `/api/config` lieferte erwartungsgemäß `404`; die öffentliche Telegram-Konfiguration wurde anschließend aus `telegram_status` des Statusendpunkts gelesen.
- Kontrollierter Start von `.venv\Scripts\python.exe main.py --headless --web` mit den geprüften Starter-Umgebungsvariablen und getrennten Runtime-Logs.
- Prozess-, Port-, Log-, Storage- und Arbeitsbaumprüfungen mit PowerShell, `netstat`, `rg` und Git.
- GitHub-Vorprüfung mit `gh --version`, `gh auth status`, Remote-, Branch- und Scopeprüfung. Kein Push und kein PR-Aufruf nach dem fehlgeschlagenen Authentifizierungscheck.

### Ausgeführte Tests

- Runtime-Preflight.
- Kontrollierter vollständiger Prozess-Stop und Neustart.
- Health-/WebSocket-/Statistik-Smoke-Test über `/api/health`.
- Live-Smoke-Test über sechs vollständige Crypto- und Stockzyklen.
- Service-, Preis-, NeuroBrain-, Fehlerjournal-, Telegram- und Storage-API-Prüfungen.
- Serverlog- und Git-Sauberkeitsprüfung.
- Keine erneute vollständige Unittest-Suite, da kein Produktcode geändert wurde und der identische Merge-Stand unmittelbar vor Integration bereits 243/243 Tests bestanden hatte.

### Tatsächliche Testergebnisse

- Runtime-Preflight bestanden: Python 3.12.13 aus `.venv`; Legacy-Crypto-Pfad verfügbar.
- Kontrollierter Stop erfolgreich; Portfreigabe nach 15,041 Sekunden, kein `Stop-Process` oder anderer harter Abbruch.
- Neue Instanz läuft seit 16:48:40 Uhr; API meldet `web_running=true`, `websocket_active=true` und `statistics_active=true`.
- Plattform und genau zehn Services `OK`; keine `STALE`-, `ERROR`- oder sonstigen Nicht-OK-Services; Sitzungsfehlerzähler null.
- Crypto und Stock jeweils sechs vollständige Zyklen; Crypto je Zyklus drei und Stock fünf Ergebnisse.
- Aktuelle Binance-Preise beobachtet: BTCUSDT etwa 65.156, ETHUSDT etwa 1.924,4 und XRPUSDT etwa 1,0449 USDT.
- NeuroBrain: Worker aktiv, Queue-Tiefe null, Drops null, fehlgeschlagene Events null und Status-Schreibfehler null.
- Fehlerjournal gesund: 183 historische Ereignisse, zehn Fingerprints, null fehlgeschlagene Schreibvorgänge und kein neuer Servicefehler dieser Sitzung.
- Telegram: `enabled=false`, `dry_run=true`, null versendete Nachrichten. Keine reale Orderausführung aktiviert.
- Storage: physisch 145 Dateien, 2.548.436 Datensätze und 10,52 GB; `totals_status=VERIFIED`, JSONL-Index 100 Prozent. Der Scan meldet 145 abgeschlossene Dateiverweise und zwei Warnungen in bekannten beschädigten historischen Stock-Backup-JSONs.
- Server-stdout blieb leer. Stderr enthielt genau einen `WinError 10054` aus einem lokalen Readiness-Client-Abbruch; sechs Marktzyklen erzeugten keinen weiteren Traceback.
- Git-Arbeitsbaum war vor der verpflichtenden Dokumentationsaktualisierung sauber.

### Bekannte Fehler

- KP-018: einmaliger lauter HTTP-Server-Traceback nach lokalem Client-Abbruch; ohne Service- oder Betriebswirkung und ohne Wiederholung.
- Die zwei bekannten beschädigten historischen Stock-Backup-JSONs halten den Storage-Scan auf `DEGRADED`, obwohl die physischen Gesamtwerte `VERIFIED` sind. Sie wurden nicht verändert.
- Die weiteren offenen Punkte aus `docs/KNOWN_PROBLEMS.md` bestehen unverändert.

### Getroffene Architekturentscheidungen

- Keine Architektur oder Produktlogik geändert.
- Für den Neustart ausschließlich der vorhandene Lifecycle und die dokumentierte Starterkonfiguration verwendet.
- Browser-Sicherheitsrichtlinie nicht umgangen; lokale API- und Logsignale dienen als verifizierte Betriebsgrundlage dieser Aufgabe.
- Telegram bleibt deaktiviert und im Dry-Run. Reale Trades und automatische Orderausführung bleiben ausgeschlossen.

### Nicht abgeschlossene Punkte

- Keine visuelle Browser- oder Browser-Konsolenprüfung in dieser Sitzung, weil die Browser-Steuerung die lokale URL blockierte. Die WebSocket-Aktivität wurde über den Health-Endpunkt bestätigt.
- Der lokale Dokumentationscommit ist noch nicht auf GitHub veröffentlicht. Der Benutzer muss `gh auth login -h github.com` ausführen und anschließend `gh auth status` erneut bestätigen; erst danach Branch pushen und einen Draft-PR gegen `main` erstellen.
- KP-018 wird nur bei erneuter Beobachtung technisch bearbeitet.
- Der Feature-Datenqualitätsvertrag ist noch nicht begonnen.

### Exakter nächster sinnvoller Arbeitsschritt

Zuerst nach erneuter GitHub-Anmeldung den lokalen Dokumentationscommit auf `origin/agent/document-post-merge-live-verification` pushen und einen Draft-PR gegen `main` erstellen. Danach den bestehenden Feature-Engine-Datenfluss und alle Consumer read-only inventarisieren und daraus einen versionierten Datenqualitätsvertrag für Sortierung, Duplikate, OHLC-Konsistenz, Non-Finite-Werte, Mindestkerzen und Warmup ableiten. Vor dieser Vertragsanalyse weder Decision Gate noch Telegram-Kette implementieren.

---

## Aktuelle Aufgabe: Konsolidierten Entwicklungsstand nach `main` mergen

### Datum und Uhrzeit

8. August 2026, 16:21 Uhr, Europe/Berlin (`+02:00`)

### Ziel der Aufgabe

Nach ausdrücklicher Benutzerfreigabe den validierten PR #18 aus dem Draft nehmen, ausschließlich diesen konsolidierten PR nach `main` mergen und die gestapelte PR-Kette #3 bis #17 anschließend als ersetzt schließen, ohne weitere Einzel-Merges auszuführen.

### Durchgeführte Arbeiten

- Lokalen Branch, Remote-Synchronität, Pflichtdokumentation und PR #18 erneut geprüft.
- PR #18 vor der Mutation als `CLEAN`, `MERGEABLE`, ohne Review-Sperre und ohne GitHub-Checks bestätigt.
- Nach zusätzlicher ausdrücklicher Bestätigung PR #18 aus dem Draft genommen und mit normalem Merge-Commit nach `main` gemergt.
- `origin/main` aktualisiert und bestätigt, dass der vollständige Integrations-Head `3853d4109ce924737631f575c74faff776f89062` Vorfahr des neuen Main-Heads ist.
- PR #4 bis #17 mit Hinweis auf den konsolidierten PR #18 geschlossen. Keiner dieser PRs erhielt einen eigenen Merge-Commit.
- PR #3 konnte nicht geschlossen werden, weil GitHub ihn durch die nun vollständige Commit-Erreichbarkeit automatisch als `MERGED` markiert hatte. Sein angezeigter Merge-Commit ist sein bereits enthaltener Head `599d29a`, nicht ein zusätzlicher Main-Merge.
- Abschließend PR #3 bis #18 und die Liste offener PRs geprüft: #18 gemergt, #4 bis #17 geschlossen, #3 automatisch als gemergt markiert, keine offenen PRs.
- Für diese verpflichtende Abschlussdokumentation Branch `agent/document-main-integration` direkt von aktuellem `origin/main` erstellt. Keine Produktlogik oder Architektur verändert.
- Vier Übergabedateien als Commit `db9d06a` veröffentlicht und Draft-PR #19 gegen `main` erstellt: `https://github.com/cRioshy/Pando/pull/19`.

### Veränderte Dateien

- `docs/CURRENT_SYSTEM_STATE.md`
- `docs/SESSION_HANDOVER.md`
- `docs/KNOWN_PROBLEMS.md`
- `docs/NEXT_STEPS.md`

### Neue Dateien

- Keine.

### Ausgeführte Befehle

- `gh pr view 18`, `gh pr checks 18`, `gh pr ready 18` und `gh pr merge 18 --merge`.
- `git fetch origin --prune`, `git rev-parse origin/main`, `git log -1 origin/main` und `git merge-base --is-ancestor`.
- `gh pr close` für PR #3 bis #17 mit Superseded-Hinweis; PR #3 lieferte den Hinweis, dass er bereits als gemergt gilt.
- Abschließende `gh pr view`-Prüfung für PR #3 bis #18 sowie `gh pr list --state open`.
- `git switch -c agent/document-main-integration origin/main`.
- Explizites Staging der vier Dokumente, Commit `db9d06a`, Push und `gh pr create --draft` für PR #19.

### Ausgeführte Tests

- Keine erneute Softwaretestsuite nach dem Merge; der gemergte Head ist bytegleich mit dem zuvor durch 243/243 Tests, Preflight, JavaScript-Syntax und Diffprüfung validierten Stand zuzüglich reiner Übergabedokumentation.
- Read-only Git-Ancestry-, Main-Head-, PR-Zustands- und Open-PR-Prüfungen.

### Tatsächliche Testergebnisse

- PR #18: `MERGED` am 8. August 2026 um 14:21:32 UTC.
- Main-Merge-Commit: `d219fcbf922b4fe94acc46e4c976d72c178dbae6`.
- Integrations-Head `3853d4109ce924737631f575c74faff776f89062` ist vollständig in `origin/main` enthalten.
- PR #4 bis #17: `CLOSED`, `mergedAt=null`.
- PR #3: GitHub-Status `MERGED` um 14:21:33 UTC durch Commit-Erreichbarkeit; kein zusätzlicher Merge-Commit auf `main`.
- Offene PRs nach Abschluss: 0.
- Danach ausschließlich Draft-PR #19 für die verpflichtende Abschlussdokumentation geöffnet.
- Vor dem Merge bereits bestanden: Runtime-Preflight, 243/243 Tests in 50,518 Sekunden, JavaScript-Syntax, Diff-, Merge-Simulations-, Runtime- und Secret-Prüfung.

### Bekannte Fehler

- Die offenen fachlichen und technischen Punkte aus `docs/KNOWN_PROBLEMS.md` bestehen unverändert.
- Die GitHub-Darstellung von PR #3 als `MERGED` ist eine Folge der konsolidierten Commit-Erreichbarkeit und kein separater Einzel-Merge.
- Bekannte externe `datetime.utcnow()`-DeprecationWarnings bleiben unverändert.

### Getroffene Architekturentscheidungen

- Keine Produktarchitektur geändert.
- Nur PR #18 wurde aktiv nach `main` gemergt. Die gestapelten Review-PRs wurden nicht einzeln gemergt.
- Der Merge erfolgte als nachvollziehbarer Merge-Commit; kein Force-Push, Rebase oder History-Umschreiben.
- Telegram und reale Orderausführung wurden nicht verändert oder aktiviert.

### Nicht abgeschlossene Punkte

- Die Abschlussdokumentation liegt in Draft-PR #19 und ist noch nicht nach `main` gemergt.
- Der Feature-Datenqualitätsvertrag wurde noch nicht begonnen.

### Exakter nächster sinnvoller Arbeitsschritt

Draft-PR #19 prüfen und nach ausdrücklicher Freigabe nach `main` mergen. Danach als nächsten technischen Schritt ausschließlich den Feature-Datenqualitätsvertrag für Sortierung, Duplikate, OHLC-Konsistenz, Non-Finite-Werte und Warmup entwerfen.

---

## Aktuelle Aufgabe: Validierten Entwicklungsstand als Integrations-Draft veröffentlichen

### Datum und Uhrzeit

8. August 2026, 12:33 Uhr, Europe/Berlin (`+02:00`)

### Ziel der Aufgabe

Den vollständig gestapelten und getesteten PandorickKi-Stand kontrolliert als einen neuen Integrationsbranch und zusammenfassenden Draft-Pull-Request gegen `main` veröffentlichen. Die vorhandenen Draft-PRs #3 bis #17 unverändert lassen, nichts mergen und keine Runtime-, History-, Lern-, Token- oder Konfigurationsdaten veröffentlichen oder verändern.

### Durchgeführte Arbeiten

- Pflichtdokumentation und tatsächlichen Git-/GitHub-Stand erneut geprüft; die Dokumente waren seit der unmittelbar vorherigen vollständigen Integrationsanalyse unverändert.
- `origin` aktualisiert und die zwei `main`-exklusiven Commits `1c632f0` und `2c43541` untersucht.
- Bestätigt, dass `origin/main` und die gemeinsame Merge-Basis `28341e2` denselben Tree `f09031790f3e3a2c509e74b81965ed82036d1d96` besitzen. Die zwei Merge-Commits enthalten damit keine `main`-exklusive Dateiänderung.
- Read-only Merge-Simulation ausgeführt: keine gemeinsam geänderten Konfliktpfade und keine Konfliktmarker.
- Runtime-Preflight, vollständige Testsuite, JavaScript-Syntax, Diff-, Scope- und Secret-Prüfung ausgeführt.
- Branch `agent/integrate-pandorickki-main` ohne Merge oder Rebase direkt auf dem geprüften Commit `85b640c8bf9e47d0cee67b84f1b623f1883a5981` erstellt und gepusht.
- Die GitHub-App konnte wegen `403 Resource not accessible by integration` keinen PR anlegen. Gemäß Veröffentlichungsworkflow auf die authentifizierte GitHub CLI zurückgefallen.
- Draft-PR #18 gegen `main` erstellt und anschließend als offen, Draft und mergebar verifiziert. Kein PR wurde gemergt oder geschlossen.

### Veränderte Dateien

- `docs/SESSION_HANDOVER.md`
- `docs/NEXT_STEPS.md`

### Neue Dateien

- Keine dauerhaften neuen Dateien. Die temporäre PR-Beschreibungsdatei wurde nach erfolgreicher Erstellung wieder entfernt.

### Ausgeführte Befehle

- Vollständiges Lesen beziehungsweise unveränderte Hash-/Git-Prüfung der fünf Pflichtdokumente sowie Prüfung von `AGENTS.md`.
- `git fetch origin --prune`, Branch-, Remote-, Commit-, Tree-, Merge-Basis- und Ahead/Behind-Vergleiche.
- Klassische read-only `git merge-tree`-Simulation, `git diff --check`, Diffstatistik und Ancestry-Prüfungen.
- `gh --version`, `gh auth status` und PR-Abfragen über GitHub-App beziehungsweise `gh`.
- `\.venv\Scripts\python.exe scripts\runtime_preflight.py`.
- `\.venv\Scripts\python.exe -m unittest discover -s tests -p 'test_*.py'`.
- `node --check web\static\control_center.js`.
- Prüfung aller 60 Diffdateien auf Runtime-Verzeichnisse und konkrete Secret-Tokenmuster.
- `git switch -c agent/integrate-pandorickki-main` und `git push -u origin agent/integrate-pandorickki-main`.
- `gh pr create --draft` und abschließendes `gh pr view 18`.

### Ausgeführte Tests

- Runtime-Preflight.
- Vollständige Python-Unittest-Suite.
- JavaScript-Syntaxprüfung.
- Git-Whitespace-/Patchprüfung.
- Read-only Merge-Konfliktsimulation.
- Veröffentlichungsumfang auf Runtime-Daten und Secret-Muster.
- GitHub-Draft-, Zielbranch-, Head- und Mergeability-Prüfung.

### Tatsächliche Testergebnisse

- Runtime-Preflight: bestanden mit Python 3.12.13 aus der projektlokalen `.venv`.
- Vollständige Suite: 243/243 Tests in 50,518 Sekunden bestanden.
- JavaScript-Syntax: bestanden.
- `git diff --check`: bestanden. Ein erster kombinierter Befehlslauf verwendete versehentlich `origin\main..HEAD` und endete nur wegen dieses ungültigen Refnamens; die korrekt wiederholte Prüfung bestand.
- Merge-Simulation: 0 gemeinsam geänderte Konfliktpfade, 0 Konfliktmarker.
- Umfang vor der Übergabedokumentation: 35 Commits, 60 Dateien, 6.716 Ergänzungen und 403 Löschungen gegenüber `main`; 0 Runtime-Dateien und 0 Treffer der geprüften Secret-Muster.
- Draft-PR #18: `OPEN`, `isDraft=true`, `MERGEABLE`, Basis `main`, Head `agent/integrate-pandorickki-main`, Head-SHA `85b640c8bf9e47d0cee67b84f1b623f1883a5981` vor diesem Abschlusscommit.

### Bekannte Fehler

- Die offenen fachlichen und technischen Punkte aus `docs/KNOWN_PROBLEMS.md` bleiben bestehen.
- Die bekannte externe `datetime.utcnow()`-DeprecationWarning trat erneut auf, beeinflusste die 243 bestandenen Tests aber nicht.
- Die GitHub-App besitzt für die PR-Erstellung nicht die nötige Berechtigung; die authentifizierte GitHub CLI funktionierte erfolgreich.

### Getroffene Architekturentscheidungen

- Keine Produktarchitektur geändert.
- Kein inhaltsloser Merge- oder Rebase-Commit nur zur Korrektur des Commitgraphen: `main` besitzt gegenüber der Merge-Basis keine eigene Dateidifferenz.
- Die bestehende gestapelte PR-Kette bleibt als Review-Historie erhalten. Für die spätere Integration nach `main` dient ausschließlich der neue konsolidierte Draft-PR #18.
- Telegram blieb unverändert; echte Trades und automatische Orderausführung wurden nicht aktiviert.

### Nicht abgeschlossene Punkte

- Draft-PR #18 ist bewusst noch nicht gemergt.
- PRs #3 bis #17 bleiben offen und Draft. Sie dürfen erst nach einer bewussten Integration von PR #18 als ersetzt geschlossen werden, nicht einzeln gemergt werden.
- Der Feature-Datenqualitätsvertrag wurde noch nicht begonnen.

### Exakter nächster sinnvoller Arbeitsschritt

Draft-PR #18 auf GitHub als Gesamtdiff prüfen und den nach diesem Handover-Push aktualisierten Head erneut als Draft/mergebar verifizieren. Erst nach ausdrücklicher Benutzerfreigabe PR #18 nach `main` mergen. Danach PRs #3 bis #17 als ersetzt schließen und erst anschließend den Feature-Datenqualitätsvertrag planen.

---

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
- Implementierungscommit `2f779e9dbc9068f188ce661dc3e4e86d184284ab` zu `origin/agent/harden-control-center-ui` gepusht.
- Draft-PR #17 gegen `agent/unify-learning-metrics` erstellt; ausdrücklich nicht gemergt.

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

- Feature-Datenqualitätsvertrag, Decision Gate und Telegram-Kette wurden bewusst noch nicht begonnen.

### Exakter nächster sinnvoller Arbeitsschritt

In einem eigenen kleinen Arbeitsschritt die tatsächlichen Feature-Eingänge und Consumer inventarisieren und einen versionierten Datenqualitätsvertrag für Sortierung, Duplikate, OHLC-Konsistenz, Non-Finite-Werte und Warmup entwerfen; noch kein Decision Gate und keinen Telegram-Livepfad implementieren.

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
