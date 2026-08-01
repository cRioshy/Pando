# Nächste Schritte

Stand: 1. August 2026

## Verbindliche Reihenfolge

1. **Funktionierenden Crypto-Stand sichern und veröffentlichen.**
   - BEFORE-Backup, Scope-/Secret-Prüfung, Preflight, 10 Crypto-Tests, 200 Gesamttests und zwei Livezyklen sind erfolgreich.
   - Den geprüften Stand auf `agent/add-market-feature-engine` committen und pushen.
   - Bestehenden Draft-PR gegen `main` prüfen; nicht mergen.

2. **Storage-Worker-Shutdown deterministisch machen.**
   - Reproduzierbaren Test für einen beim `close()` laufenden Schreibvorgang ergänzen.
   - Einen eindeutigen Shutdown-Vertrag festlegen: Nach `close()` darf kein Worker mehr schreiben.
   - Keine Runtime-Daten löschen; ausschließlich Thread-/Abbruch-Synchronisation ändern.

3. **Storage-Anzeige korrigieren.**
   - Überlappende logische Ziele erkennen und physische Dateien in der Gesamtsumme nur einmal zählen.
   - Logische Kategorien weiter getrennt anzeigen und logische sowie physische Summen klar benennen.

4. **Storage-Scanner instrumentieren und reparieren.**
   - Zeitmessungen für Dateiermittlung, Metadaten/Fingerprint, Dateityp-Auswertung und Cache-Schreiben ergänzen.
   - Inkrementelles Budget anhand realer Messwerte einstellen und Fortschritt über mehrere Läufe erhalten.
   - Keine History-Dateien löschen.

5. **Dauerhaftes begrenztes Service-Fehlerjournal ergänzen.**
   - Erste und letzte konkrete Exception auch nach längerer Laufzeit rekonstruierbar machen.
   - Provider, Stufe, Symbol und Fehlerart speichern, aber keine Secrets oder vollständigen externen Antwortinhalte.
   - Größenlimit und Rotation von Beginn an festlegen.

6. **Vertrag für kompakte Event-Payloads definieren.**
   - Benötigte Felder für Decision Core, Tracker, Learning und UI vollständig ermitteln.
   - Versionierte Projektion und Kompatibilitätstests festlegen; `raw_result` nicht ungeprüft entfernen.

7. **Brain- und NeuroBrain-Payloads verkleinern.**
   - Nur die definierte Projektion neu persistieren und IDs beziehungsweise Referenzen erhalten.
   - Bestehende History unverändert lesbar lassen.

8. **NeuroBrain gezielt entkoppeln.**
   - Begrenzte Queue, Überlaufregel, Batch-Schreiben, atomaren Status und sicheren Shutdown umsetzen.
   - Zunächst nur NeuroBrain entkoppeln, nicht ungeprüft den vollständigen EventBus ersetzen.

9. **Learning-Metriken vereinheitlichen.**
   - Begriffe, Nenner und Outcome-Abdeckung offenlegen.
   - Hit-Rate und Trading-Statistik voneinander abgrenzen und fehlendes ML-Training klar kennzeichnen.

10. **UI härten.**
    - Idempotentes Polling, WebSocket-Reconnect, `STALE`-Heartbeats und Graph-Performance bearbeiten.
    - Control-Buttons entweder an echte Lebenszyklusaktionen koppeln oder korrekt als UI-Zustand beschriften.

## Erst anschließend

- Feature-Datenqualitätsvertrag für Sortierung, Duplikate, OHLC-Konsistenz, Non-Finite-Werte und Warmup definieren.
- Fachlichen Decision-Gate-Vertrag mit Fakten-, Risiko-, Confidence- und Konfliktregeln entwerfen.
- Telegram ausschließlich an freigegebene finale Ereignisse anbinden und bis dahin deaktiviert beziehungsweise im Dry-Run lassen.
- Aufbewahrungs-/Archivkonzept und Portabilität der Legacy-Pfade separat planen, ohne bestehende History zu löschen.

## Zuletzt erledigt

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
