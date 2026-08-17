# Stock Live-Shadow-Verification-Vertrag

Stand: 9. August 2026

Vertragsname: `pandorickki.stock-shadow-verification`, Version `1`

## Zweck und Grenze

Der Vertrag vergleicht ausschließlich Aktienfälle zwischen der bestehenden Legacy-Entscheidung und dem getrennten öffentlichen Stock-Shadow. Er ist append-only, observer-only und darf weder Feature-Berechnung, Brain, produktive Decision/Signals, bestehende Outcomes, Learning, Telegram noch Orders verändern. Crypto bleibt ausgeschlossen, bis eine wirklich unabhängige Crypto-Shadow-Entscheidung existiert.

## Identität und Idempotenz

Ein `verification_id` wird deterministisch aus Symbol, Legacy-Quellzeitpunkt, öffentlichem Quote-Zeitpunkt, jüngstem Kerzenzeitpunkt, Observer-Version und Konfigurationsfingerprint erzeugt. Mehrere technische `source_event_id`-Werte dürfen bei einem Neustart auf denselben fachlichen Fall zeigen, ohne einen neuen Fall zu zählen. Die spätere Plattform-`decision_id` wird additiv über die vorhandene `source_event_id` verknüpft.

## Persistenz

Das Ledger ist ausschließlich append-only. Einträge besitzen getrennte Recordtypen für Beobachtung, zusätzliche Source-ID, Decision-Verknüpfung, Tracker-Verknüpfung und Outcome-Abschluss. Bestehende Legacy-, Decision- und Outcome-History wird weder migriert noch umgeschrieben. Beim Start wird der Materialized View aus aktiver Datei und vorhandenen Archiven rekonstruiert.

Pro Ledger darf genau ein Verification-Writer aktiv sein. Vor dem Lesen und vor EventBus-Subscriptions wird ein exklusiver Prozess-/OS-Dateilock erworben und bis zum vollständigen Adapter-Stop gehalten. Ein Lockkonflikt ist fail-closed: keine Verification-Subscriptions und keine Ledger-Schreibvorgänge. Completion-Selektion, erneute Prüfung auf `PENDING`, append-only Schreiben und Apply auf den Materialized View erfolgen unter derselben Adapter-Sperre. Parallele oder doppelte Quoteereignisse dürfen deshalb nur eine neue Completion-Zeile je noch offenem Fall erzeugen. Vorhandene historische Duplikatzeilen werden nicht umgeschrieben und müssen bei read-only Auswertungen kanonisch nach `verification_id` behandelt werden.

## Betriebsmodi

- `NORMAL`: erzeugt neue Fälle aus `STOCK_SHADOW_OBSERVED` und verarbeitet bestehende Decision-, Tracker- und Quote-Verknüpfungen.
- `DRAIN`: abonniert keine neuen Beobachtungen und erzeugt keine neuen Fälle; bereits rekonstruierte Fälle dürfen weiterhin Decision-/Tracker-Links und fällige Outcomes erhalten.
- `STOPPED`: keine Verification-Subscriptions und keine Ledgeraktivität.
- unbekannte oder leere Werte: effektiver Zustand `STOPPED`, ungesund/fail-closed und ohne Subscriptions.

Der Modus ist Prozesskonfiguration und verändert keine vorhandenen Ledgerzeilen. Ein Neustart in `DRAIN` rekonstruiert den bisherigen Materialized View und führt ausschließlich bestehende Fälle weiter.

## Statusbegriffe

- Entscheidung: `LONG`, `SHORT`, `HOLD` oder `UNKNOWN`
- Stock-Vertrag: vorhandene Rohwerte `READY` oder `BLOCKED`
- Feature-Qualität: vorhandene Rohwerte `PASS`, `WARN`, `FAIL` oder `UNKNOWN`
- UI-Qualitätsprojektion: `OK`, `DEGRADED`, `REJECTED`
- Shadow-Eignungsprojektion: `PASS`, `BLOCK`, `HOLD`, `UNKNOWN`
- Outcome: `PENDING`, `WIN`, `LOSS`, `NEUTRAL`, `UNKNOWN`

`HOLD` ist eine Entscheidung, kein Gate-Ergebnis. Die Shadow-Eignungsprojektion aktiviert nicht den produktiven Decision Gate.

## Outcome-Vertrag Version 1

Version 1 verwendet ein festes Forward-Mark-to-Market-Fenster:

- Standardhorizont: 86.400 Sekunden
- neutrale Toleranz: 0,05 Prozent
- Entry: öffentlicher Kurs, der zum Beobachtungszeitpunkt gespeichert wurde
- Exit: erster valider öffentlicher Kurs nach Ablauf des Horizonts
- der Exit-Quote-Zeitstempel muss strikt nach dem ursprünglichen Quote-Zeitstempel liegen
- LONG bewertet den prozentualen Marktmove direkt, SHORT mit umgekehrtem Vorzeichen
- HOLD, fehlende Richtung oder fehlender Entry bleiben `UNKNOWN`
- noch nicht fällige oder nicht fortgeschrittene Quotes bleiben `PENDING`
- Stop-/Zielberührungen werden ausdrücklich nicht behauptet, weil diskrete Quotes keinen vollständigen Intraday-Pfad beweisen

Legacy- und Shadow-Ergebnis werden getrennt gespeichert. Der vorhandene simulierte Outcome Tracker darf zusätzlich read-only verknüpft werden, ersetzt aber nicht den gemeinsamen Forward-Mark-to-Market-Vergleich.

## Konfigurationsstabilität

Jeder Fall speichert Observer-Version und einen SHA-256-Fingerprint ausschließlich aus nicht geheimen Stock-, Shadow-, Risiko- und Outcome-Parametern. Während eines Vergleichslaufs werden diese Werte nicht automatisch angepasst.

## Öffentliche Projektion

API und Control Center erhalten nur kompakte Records und Aggregate. Rohkerzen, vollständige Legacy-Payloads, Tokens und Secrets sind ausgeschlossen. Detailansichten sind read-only. Kein Ergebnis erzeugt eine Meldung, ein Signal oder eine Order.

## Abgrenzung zur Kalibrierung

Das Verification-Ledger ist die einzige zulässige spätere Outcome-Quelle für `pandorickki.stock-shadow-calibration` Version 1. Die Verification selbst führt jedoch keinen Fit aus und erzeugt weder eine kalibrierte Probability noch Confidence. Wiederholte Zyklen derselben Tageskerze bleiben im Audit erhalten, müssen vor einer Offline-Kalibrierung aber nach dem Kalibrierungsvertrag kanonisch dedupliziert werden.

Der freigegebene siebentägige Beobachtungslauf startete am 10. August 2026 um 19:03:44 Uhr Europe/Berlin mit 24h-Horizont, 0,05-%-Neutralband und Fingerprint `3d23f923d6b9d9dc3019457afcb078591b5d8c8b4d1f4f4db55911724fa71747`. Abschluss und reine Auswertung sind für den 17. August 2026 nach 19:10 Uhr vorgesehen. Vor dem Start bereits vorhandene Kurzlauffälle bleiben unverändert und werden anhand ihrer Zeitstempel separat berichtet.
