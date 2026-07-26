# Nächste Schritte

Stand: 26. Juli 2026

## Jetzt als Nächstes

1. **Storage-Worker-Shutdown deterministisch machen.**
   - Reproduzierbaren Test für einen beim `close()` laufenden Schreibvorgang ergänzen.
   - Einen eindeutigen Shutdown-Vertrag festlegen: Nach `close()` darf kein Worker mehr schreiben.
   - Keine Runtime-Daten löschen; ausschließlich Thread-/Abbruch-Synchronisation ändern.

2. **Storage-Timeout instrumentieren und Ursache bestimmen.**
   - Zeitmessungen für Dateiermittlung, Metadaten/Fingerprint, Dateityp-Auswertung und Cache-Schreiben ergänzen.
   - Reproduktion mit dem aktuellen Bestand ohne Datenlöschung.
   - Danach den kleinsten messbaren Engpass beheben und Storage-Tests erweitern.

3. **WebSocket-Client isoliert härten.**
   - Einen idempotenten Polling-Timer verwalten.
   - Polling bei `error` und `close` sicher starten.
   - Begrenzten Reconnect mit Backoff ergänzen.
   - JSON-Parsing und Rendern lokal absichern.

## Danach

4. Heartbeat-Stale-Schwelle und klare History-Bezeichnung statt irreführender Queue-Semantik ergänzen.
5. Feature-Eingangsvertrag für Sortierung, Duplikate, OHLC-Konsistenz, Non-Finite-Werte und Warmup definieren.
6. Aufbewahrungs- und Archivkonzept entwerfen, ohne bestehende History ungefragt zu löschen.
7. Portabilität der Legacy-Pfade und Vollständigkeit von `.env.example` verbessern.

## Nur nach gesonderter Architekturfreigabe

8. Fachlichen Decision-Gate-Vertrag mit Fakten-, Risiko-, Confidence- und Konfliktregeln entwerfen.
9. Telegram ausschließlich an freigegebene finale Ereignisse anbinden.
10. EventBus entkoppeln und Reihenfolge-, Backpressure- und Shutdown-Semantik festlegen.

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
