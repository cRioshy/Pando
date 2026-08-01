# Vertrag für kompakte Event-Payloads

Stand: 1. August 2026  
Vertragsname: `pandorickki.compact-market-event`  
Version: `1`

## Zweck und aktueller Status

Dieser Vertrag ist das getestete Ziel für die spätere Verkleinerung der Brain-, Decision-, Signal- und NeuroBrain-Ereignisse. Er ist noch **nicht** in den laufenden Produktionspfad geschaltet. Bestehende Events und History-Dateien bleiben unverändert. Erst ein eigener Folgeschritt darf Producer und Consumer kontrolliert migrieren.

Die ausführbare Referenz liegt in `event_payload_contract.py`. `compact_market_payload()` akzeptiert sowohl den heutigen EventBus-Umschlag als auch eine flache Payload, erzeugt Schema-Metadaten und kopiert nur ausdrücklich zugelassene Felder.

## Tatsächliche Produzenten

| Producer | Topic | Heutiger Inhalt |
|---|---|---|
| `CryptoAdapter` | `CRYPTO_ANALYSIS_FINISHED` | normalisierte Markt-, Preis-, Fakten-, Indikator-, Risiko- und Featurefelder plus vollständiges `raw_result` |
| `StockAdapter` | `STOCK_ANALYSIS_FINISHED` | normalisierte Markt-, Preis-, Fakten-, Indikator-, Risiko- und Featurefelder plus vollständiges `raw_result` |
| `CommodityAdapter` | `COMMODITY_ANALYSIS_FINISHED` | normalisierte Quote; `raw_result` ist derzeit leer |
| `BrainAdapter` | `BRAIN_DECISION_RECEIVED` | ausgewählte Felder, übernimmt aber weiterhin `raw_result` und persistiert die vollständige eingehende Analyse |
| `DecisionSignalAdapter` | `DECISION_CREATED`, `SIGNAL_CREATED` | kopiert aktuell `indicators`, `risk` und `raw_result` weiter |

## Verifizierter Feldverbrauch

| Consumer | Tatsächlich benötigte Felder | Besonderheit |
|---|---|---|
| Brain | Markt, Symbol, Richtung, Wahrscheinlichkeit, Preis, Indikatoren, Risiko, Quellzeit und Event-ID | persistiert derzeit zusätzlich die komplette Eingangspayload |
| Decision Core | Brain-Felder plus Confidence und IDs | reicht `raw_result` derzeit unverändert weiter, wertet es aber nicht fachlich aus |
| Crypto Trade Tracker | Markt, Symbol, Richtung, Preis, ATR, Risiko, IDs | liest für Swing-Low/-High noch Kerzen aus `raw_result.market_data.candles` |
| Outcome Tracker | Markt, Symbol, Richtung, Preis, Risikoziele, Decision-/Signal-IDs und Zeitstempel | benötigt kein vollständiges Raw Result |
| Control Center | kompakte Anzeige-, Preis-, Status- und Tradefelder | projiziert bereits auf eine kleine Sicht |
| Telegram | Markt, Symbol, Richtung, Wahrscheinlichkeit, Preis und optionale Tradefelder | bleibt deaktiviert beziehungsweise Dry-Run |
| Learning Graph | Symbol, Richtung, Indikatornamen und Ergebnislabel | liest das Ergebnislabel noch aus `raw_result.result`, unterstützt aber bereits `public_result` |
| NeuroBrain | Topic, Quelle, IDs, Markt, Symbol, Richtung, Wahrscheinlichkeit und Zeitstempel | erzeugt bereits eine kleine Kopfsicht, speichert daneben aber noch die komplette Event-Payload |

## Version 1

Pflichtfelder jeder Projektion:

- `schema_name`
- `schema_version`
- `market_type`
- `symbol`

Die gemeinsame Feldmenge enthält bei Verfügbarkeit Event-/Decision-/Signal-IDs, Markt- und Richtungsdaten, Preise und Preisstatus, Quell- und Empfangszeiten, kompakte `facts`, `indicators`, `risk`, `market_context`, `public_result` sowie simulierte Tradefelder. Nicht vorhandene optionale Felder werden nicht künstlich befüllt.

Verboten sind in jeder Verschachtelung:

- `raw_result`
- `features`
- `market_data_diagnostics`
- `candles`

`facts`, `indicators` und `risk` bleiben strukturierte, von ihren Producern begrenzte Sichten. Die Projektion entfernt daraus ebenfalls verbotene Bulk-Felder. Secrets oder fremde Rohantworten gehören grundsätzlich nicht in den Vertrag.

## Ersatz für heutige Raw-Abhängigkeiten

| Heutiger Zugriff | Kompakter Ersatz | Migration |
|---|---|---|
| `CryptoTradeTracker`: `raw_result.market_data.candles` | `market_context.recent_swing_low` und `market_context.recent_swing_high` | Tracker muss vor Entfernung von `raw_result` auf diese Felder umgestellt werden |
| `LearningGraphBuilder`: `raw_result.result` | `public_result` | vorhandener Fallback kann nach der Producer-Migration zum Primärfeld werden |

Die Referenzprojektion berechnet die beiden Swing-Werte ausschließlich für die Kompatibilitätsmigration aus den letzten 20 Legacy-Kerzen. Die Kerzen selbst werden nie in die kompakte Ausgabe übernommen.

## Migrations- und Kompatibilitätsregeln

1. Zuerst Consumer für `schema_name`/`schema_version` und die beiden Ersatzfelder vorbereiten.
2. Danach Brain- und Decision-/Signal-Producer auf die Projektion umstellen.
3. NeuroBrain darf nur die Projektion persistieren; seine vorhandene kompakte Kopfsicht und IDs bleiben erhalten.
4. Bestehende JSONL-History wird weder geändert noch gelöscht. Leser behalten einen Legacy-Pfad für alte Datensätze.
5. Unbekannte Schema-Hauptversionen werden nicht stillschweigend als kompatibel behandelt.
6. Keine reale Order- oder Telegram-Freigabe ist Bestandteil dieses Vertrags.

## Tests

```powershell
.\.venv\Scripts\python.exe -m unittest tests.test_event_payload_contract -v
```

Die Tests prüfen Schema und Pflichtfelder, den Ausschluss aller Bulk-Felder, die beiden Legacy-Ersatzprojektionen sowie die deklarierte Feldabdeckung der tatsächlich untersuchten Consumer.
