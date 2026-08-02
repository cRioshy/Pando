# Nächste Schritte

Stand: 2. August 2026

## Verbindliche Reihenfolge

1. **Funktionierenden Crypto-Stand sichern und veröffentlichen.**
   - **Erledigt am 1. August 2026.**
   - BEFORE-Backup, Scope-/Secret-Prüfung, Preflight, 10 Crypto-Tests, 200 Gesamttests und zwei Livezyklen erfolgreich.
   - Commit `b0379c3` auf `agent/add-market-feature-engine` gepusht.
   - Draft-PR #3 gegen `main` erstellt; ausdrücklich nicht mergen.

2. **Storage-Worker-Shutdown deterministisch machen.**
   - **Erledigt am 1. August 2026.**
   - Regressionstest reproduzierte die verfrühte Rückkehr und `WinError 145` vor dem Fix.
   - Nach `close()` werden neue Scans abgelehnt und laufende Worker beziehungsweise synchrone Refreshes vollständig abgewartet.
   - 201/201 Gesamttests bestanden; keine Runtime-Daten gelöscht.
   - Commit `610b4a9` veröffentlicht; gestapelter Draft-PR #4 gegen `agent/add-market-feature-engine` erstellt und nicht gemergt.

3. **Storage-Anzeige korrigieren.**
   - **Erledigt am 1. August 2026.**
   - Überlappende logische Ziele bleiben getrennt sichtbar, physische Dateien werden aber nur einmal gescannt und summiert.
   - API und UI unterscheiden physisch eindeutige Werte, logische Kategorieverweise und Überlappungen.
   - Alte Caches werden bis zum nächsten vollständigen Scan als nicht physisch verifiziert markiert.
   - Commit `a15770b` veröffentlicht; gestapelter Draft-PR #5 gegen `agent/fix-storage-worker-shutdown` erstellt und nicht gemergt.

4. **Storage-Scanner instrumentieren und reparieren.**
   - **Erledigt am 1. August 2026.**
   - Phasenlaufzeiten, kumulativer JSONL-Fortschritt, Restbytes sowie geschätzte Restläufe/-zeit werden pro Scan erfasst und im Control Center angezeigt.
   - Zwei schreibgeschützte Realmessungen ergaben 1,084 Sekunden mit altem Budget und 2,135 Sekunden bei 64 MiB; das Standardbudget wurde deshalb von 256 KiB auf 64 MiB erhöht.
   - Der reale JSONL-Index lag bei 5,69 %; mit dem neuen Budget waren bei der Messung ungefähr 82 weitere Minutenläufe erforderlich.
   - 39/39 gezielte und 204/204 vollständige Tests bestanden; keine History-Datei wurde gelöscht oder verändert.
   - Commit `cc6e92d` veröffentlicht; gestapelter Draft-PR #6 gegen `agent/fix-storage-physical-totals` erstellt und nicht gemergt.

5. **Dauerhaftes begrenztes Service-Fehlerjournal ergänzen.**
   - **Erledigt am 1. August 2026.**
   - Kompakte versionierte Fehlerprojektion mit Erst-/Letztbeobachtung und Fehleranzahl umgesetzt.
   - Secret-Filter und Ausschluss vollständiger Payloads beziehungsweise externer Antwortinhalte getestet.
   - Aktives Journal auf 5 MiB, Archive auf vier und Zusammenfassung auf 500 Fingerprints begrenzt.
   - Commit `8a0a78d` veröffentlicht; gestapelter Draft-PR #7 gegen `agent/instrument-storage-scanner` erstellt und nicht gemergt.

6. **Vertrag für kompakte Event-Payloads definieren.**
   - **Erledigt und veröffentlicht am 1. August 2026.**
   - Tatsächliche Producer und Feldleser in Brain, Decision Core, Trackern, Learning, Control Center, Telegram und NeuroBrain geprüft.
   - Vertrag `pandorickki.compact-market-event` Version 1, ausführbare Projektion, Validator und Kompatibilitätstests ergänzt.
   - Zwei echte Legacy-Abhängigkeiten ausdrücklich erfasst: Crypto-Swings aus Kerzen und Learning-Ergebnis aus `raw_result`.
   - Produktionspayloads und bestehende History bewusst noch nicht verändert.
   - Commit `311dd38` veröffentlicht; gestapelter Draft-PR #9 gegen `agent/fix-outcome-timestamp-normalization` erstellt und nicht gemergt.

7. **Brain- und NeuroBrain-Payloads verkleinern.**
   - **Consumer-Vorbereitung am 1. August 2026 abgeschlossen und veröffentlicht.**
   - Crypto Trade Tracker bevorzugt `market_context.recent_swing_low/high`, Learning Graph bevorzugt `public_result`; alte Raw-Payloads bleiben lesbar.
   - Vier neue Regressionstests und 221/221 Gesamttests bestanden.
   - Commit `1550d07` veröffentlicht; gestapelter Draft-PR #10 gegen `agent/define-compact-event-payload-contract` erstellt und nicht gemergt.
   - **Brain-Migration am 1. August 2026 implementiert und veröffentlicht.**
   - Neue Brain-History und `BRAIN_DECISION_RECEIVED` verwenden ausschließlich Version 1 mit erhaltener Quell-ID.
   - 28/28 gezielte und 222/222 vollständige Tests bestanden.
   - Commit `5b59fa2` veröffentlicht; gestapelter Draft-PR #11 gegen `agent/prepare-compact-payload-consumers` erstellt und nicht gemergt.
   - **Decision-/Signal-Migration am 1. August 2026 implementiert und veröffentlicht.**
   - Neue Decision-/Signal-Events und beide Ledger verwenden Version 1 ohne `raw_result`; alle IDs bleiben erhalten.
   - 32/32 gezielte und 223/223 vollständige Tests bestanden.
   - Commit `ed89a01` veröffentlicht; gestapelter Draft-PR #12 gegen `agent/compact-brain-payloads` erstellt und nicht gemergt.
   - **NeuroBrain-Persistenz am 1. August 2026 implementiert und veröffentlicht.**
   - Neue Inboxzeilen behalten ihre Kopfsicht und enthalten als Detailpayload nur Version 1; alte Inboxzeilen bleiben unverändert.
   - 18/18 gezielte und 224/224 vollständige Tests bestanden.
   - Commit `5d32bc7` veröffentlicht; gestapelter Draft-PR #13 gegen `agent/compact-decision-signal-payloads` erstellt und nicht gemergt.
   - **Liveverifikation am 1. August 2026 abgeschlossen:** drei saubere Produktionszyklen, alle zehn Services `OK`, echte Crypto-Preise, vollständige ID-Kette und keine Bulk-Felder in den geprüften neuen Zeilen.
   - **Schemaabgrenzung `KP-016` am 2. August 2026 behoben und live verifiziert:** Observer-Vertrag für Learning/Aggregate, Markt-Typ-Ergänzung für einzelwertige Preisupdates; 231/231 Tests und 152/152 neue Livezeilen ohne Verstoß.
   - Commit `e94c988` veröffentlicht; gestapelter Draft-PR #14 gegen `agent/compact-neurobrain-payloads` erstellt und nicht gemergt.
   - Bestehende History unverändert lesbar lassen.

8. **NeuroBrain gezielt entkoppeln.**
   - **Erledigt und am 2. August 2026 live verifiziert.**
   - **Vorgelagerte Schreibkonflikte am 2. August 2026 behoben und live verifiziert:** eindeutige Temp-Dateien, Pfadsperre, begrenzter Windows-Retry und geordnete Zustandssnapshots für NeuroBrain-Status und aktive Crypto-Trades.
   - 13/13 gezielte und 226/226 vollständige Tests bestanden; zwei Produktionszyklen ohne neue Ziel-Fingerprints oder Temp-Reste.
   - Commit `ed2a83e` auf dem bestehenden Branch veröffentlicht und Draft-PR #13 aktualisiert; nicht gemergt.
   - **Voraussetzung `KP-016` erledigt:** Markt- und Observer-Topics sind eindeutig getrennt und getestet.
   - FIFO-Queue mit Kapazität 2048, sichtbarem Drop-newest, Batchgröße 64, 250-ms-Flush, atomarem Status und vollständigem Shutdown-Drain umgesetzt.
   - 20/20 gezielte und 235/235 vollständige Tests; live 231 Zeilen in 48 Batches, null Drops/Fehler und sauberer Worker-Shutdown.
   - Ausschließlich NeuroBrain entkoppelt; der vollständige EventBus blieb unverändert.

9. **Learning-Metriken vereinheitlichen.**
   - Begriffe, Nenner und Outcome-Abdeckung offenlegen.
   - Hit-Rate und Trading-Statistik voneinander abgrenzen und fehlendes ML-Training klar kennzeichnen.

10. **UI härten.**
    - Idempotentes Polling, WebSocket-Reconnect, `STALE`-Heartbeats und Graph-Performance bearbeiten.
    - Control-Buttons entweder an echte Lebenszyklusaktionen koppeln oder korrekt als UI-Zustand beschriften.
    - Stop-/Restart-Wartezeit unterbrechbar machen; aktuell wird ein akzeptierter Stop erst nach dem bis zu 60 Sekunden langen Zyklus-Sleep wirksam.

## Erst anschließend

- Feature-Datenqualitätsvertrag für Sortierung, Duplikate, OHLC-Konsistenz, Non-Finite-Werte und Warmup definieren.
- Fachlichen Decision-Gate-Vertrag mit Fakten-, Risiko-, Confidence- und Konfliktregeln entwerfen.
- Telegram ausschließlich an freigegebene finale Ereignisse anbinden und bis dahin deaktiviert beziehungsweise im Dry-Run lassen.
- Aufbewahrungs-/Archivkonzept und Portabilität der Legacy-Pfade separat planen, ohne bestehende History zu löschen.

## Zuletzt erledigt

- NeuroBrain-Datei-I/O über begrenzte FIFO-Queue und einzelnen Batch-Worker vom Publisher entkoppelt; Drop-newest, Healthmetriken und vollständiger Flush-Shutdown getestet.
- 20/20 gezielte und 235/235 vollständige Tests; live 231 neue Zeilen in 48 Batches ohne Drops, FIFO-/Schema- oder Workerfehler. Dienst nach erfolgreichem Stop erneut sicher gestartet.
- NeuroBrain-Schemaabgrenzung behoben: kompakter Observer-Vertrag für Learning-/Aggregatereignisse, Markt-Typ-Inferenz für einzelwertige Crypto-/Commodity-Updates.
- 15/15 gezielte und 231/231 vollständige Tests bestanden; 152 neue Livezeilen ohne Schema-, Pflichtfeld- oder Bulk-Verstoß, alle Services `OK`, Telegram aus/Dry-Run.
- Commit `e94c988` auf `agent/fix-neurobrain-observer-schema` veröffentlicht; Draft-PR #14 bleibt offen, Draft und ungemergt.
- Wiederkehrende `WinError 5`-Konflikte bei NeuroBrain-Status und aktiven Crypto-Trades mit einem konfliktresistenten atomaren JSON-Schreibpfad behoben.
- Retry- und Parallelitätsregressionen, 13/13 gezielte sowie 226/226 vollständige Tests bestanden; zwei Livezyklen ohne neue Fehlerfingerprints oder Temp-Reste.
- Vollständigen gestapelten Payloadstand kontrolliert live gestartet und drei saubere Produktionszyklen verifiziert.
- Neue Brain-, Decision-, Signal- und marktbezogene NeuroBrain-Zeilen verwenden Version 1, enthalten keine Bulk-Felder und behalten die vollständige ID-Kette.
- Die zunächst als `KP-016` dokumentierte Live-Vertragslücke wurde am 2. August 2026 behoben; noch keine Queue-/Batch-Änderung begonnen.
- Neue NeuroBrain-Inboxzeilen auf Version 1 umgestellt; Kopfsicht, ID-Kette, Duplikatschutz und alte Inboxzeilen erhalten.
- 18/18 gezielte und 224/224 vollständige Tests bestanden; Commit `5d32bc7` und gestapelter Draft-PR #13 veröffentlicht.
- Neue Decision-/Signal-Events und beide Ledger auf Version 1 umgestellt; IDs und Legacy-Eingangskompatibilität erhalten.
- 32/32 gezielte und 223/223 vollständige Tests bestanden; Commit `ed89a01` und gestapelter Draft-PR #12 veröffentlicht.
- Neue Brain-History und `BRAIN_DECISION_RECEIVED` auf die kompakte Version-1-Projektion umgestellt; bestehende History unangetastet gelassen.
- 28/28 gezielte und 222/222 vollständige Tests bestanden; Commit `5b59fa2` und gestapelter Draft-PR #11 veröffentlicht.
- Crypto Trade Tracker und Learning Graph auf kompakte Ersatzfelder vorbereitet; Legacy-Raw-Payloads bleiben lesbar.
- 20/20 gezielte und 221/221 vollständige Tests bestanden; Commit `1550d07` und gestapelter Draft-PR #10 veröffentlicht.
- Kompakten Event-Payload-Vertrag Version 1 mit tatsächlicher Consumer-Matrix, Validator und fünf Kompatibilitätstests definiert; Produktionspayloads noch unverändert gelassen.
- 217/217 Gesamttests bestanden; Commit `311dd38` und gestapelter Draft-PR #9 veröffentlicht.
- Outcome-Zeitstempel-Fix kontrolliert live verifiziert: vier Crypto-Heartbeats, alle Services `OK`, bekannter Fehlerzähler unverändert bei 158, Telegram aus/Dry-Run.
- Commit `a2a139f` veröffentlicht und gestapelten Draft-PR #8 gegen den Fehlerjournal-Branch erstellt.
- Outcome-Tracker-Zeitnormalisierung rückwärtskompatibel umgesetzt: naive historische Werte gelten beim Lesen als UTC, vorhandene History bleibt unverändert.
- Regressionstest reproduzierte den Livefehler vor dem Fix; danach 12/12 Outcome-Tracker-Tests und 212/212 Gesamttests bestanden.
- Neuen Journalstand kontrolliert live gestartet: alle zehn Services `OK`, Journal gesund, Telegram aus/Dry-Run und 110/110 Storage-Dateien ohne Scannerfehler verarbeitet.
- Das Journal machte drei Wiederholungen eines zuvor flüchtigen Outcome-Tracker-Zeitstempelfehlers dauerhaft sichtbar; als `KP-014` dokumentiert, noch nicht behoben.
- Begrenztes, secret-gefiltertes Service-Fehlerjournal mit atomarer Erst-/Letzt-Zusammenfassung ergänzt.
- PandorickKi nach Scanner-Veröffentlichung kontrolliert neu gestartet und zwei Produktionszyklen verifiziert: alle Services `OK`, keine neuen Sessionfehler, Telegram aus/Dry-Run.
- Produktions-Storage-Scan mit 106/106 Dateien in 2,416 Sekunden und 9,20 % kumulativem JSONL-Fortschritt bestätigt; Control Center ohne Browser-Konsolenfehler geprüft.
- Storage-Scanner phasenweise instrumentiert und kumulativen JSONL-Indexfortschritt samt Restschätzung sichtbar gemacht.
- Standardbudget anhand schreibgeschützter Realmessungen auf 64 MiB pro Lauf eingestellt; 204/204 Gesamttests bestanden.
- Storage-Ziele pro physischem Pfad dedupliziert und Scanbudget nur einmal je Datei verbraucht.
- Physische und logische Summen samt Überlappungsanzahl in API und Control Center getrennt ausgewiesen.
- 44/44 gezielte und 203/203 vollständige Tests nach der Storage-Summenkorrektur bestanden.
- Storage-Worker-Shutdown mit deterministischem Race-Test und eindeutigem `close()`-Vertrag behoben.
- 27/27 Storage-, 36/36 Storage-/Web- und 201/201 Gesamttests nach dem Fix bestanden.
- Crypto-Reparaturstand mit verifiziertem BEFORE-Backup, 200/200 Tests und zwei erfolgreichen Livezyklen gesichert.
- Commit `b0379c3` veröffentlicht und Draft-PR #3 gegen `main` erstellt.
- Persistenter Storage-Cache und Dateiindex.
- Einzelner Hintergrundscanner mit Timeout, Sperre und Abbruch.
- Inkrementelle JSONL-Offsets und Schutz unvollständiger letzter Zeilen.
- Metadatenmodus für große Dateien und globales JSONL-Bytebudget.
- Asynchroner Storage-Refresh mit HTTP `202`.
- Scanstatus und Single-Flight-Storage-Lader im Control Center.
- Broadcast-Drosselung und Browser-Payload-Sanitizing.
- Begrenzung der Crypto-/Stock-Feature-Berechnung auf 500 Kerzen.
- Ergänzte Storage-, Timeout-, Parallelitäts- und UI-Tests.
- Dauerhafte lokale Übergaberegeln und Ist-Dokumentation angelegt.
- Öffentlichen Branch `agent/add-market-feature-engine` aktualisiert und Draft-PR #2 eröffnet.
- Crypto-Ausfall behoben: interner Binance/Bitget-Marktdatenclient, optionale Futures-Daten und korrekte ERROR-/DEGRADED-Projektion.
- Projektlokale `.venv`, reproduzierbares Setup und Runtime-Preflight eingeführt.
- 200/200 Tests sowie zwei aufeinanderfolgende Live-Produktionszyklen erfolgreich verifiziert.
