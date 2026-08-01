# Vertrag für kompakte Event-Payloads

Stand: 1. August 2026

Vertragsname: `pandorickki.compact-market-event`

Version: `1`

## Zweck und aktueller Status

Dieser Vertrag ist das getestete Ziel für die schrittweise Verkleinerung der Brain-, Decision-, Signal- und NeuroBrain-Ereignisse. Brain sowie Decision-/Signal-Events und ihre neuen Ledgerdatensätze verwenden Version 1 inzwischen aktiv. NeuroBrain-Persistenz ist noch nicht umgestellt. Bestehende Events und History-Dateien bleiben unverändert.

Die ausführbare Referenz liegt in `event_payload_contract.py`. `compact_market_payload()` akzeptiert sowohl den heutigen EventBus-Umschlag als auch eine flache Payload, erzeugt Schema-Metadaten und kopiert nur ausdrücklich zugelassene Felder.

## Tatsächliche Produzenten

| Producer | Topic | Heutiger Inhalt |
|---|---|---|
| `CryptoAdapter` | `CRYPTO_ANALYSIS_FINISHED` | normalisierte Markt-, Preis-, Fakten-, Indikator-, Risiko- und Featurefelder plus vollständiges `raw_result` |
| `StockAdapter` | `STOCK_ANALYSIS_FINISHED` | normalisierte Markt-, Preis-, Fakten-, Indikator-, Risiko- und Featurefelder plus vollständiges `raw_result` |
| `CommodityAdapter` | `COMMODITY_ANALYSIS_FINISHED` | normalisierte Quote; `raw_result` ist derzeit leer |
| `BrainAdapter` | `BRAIN_DECISION_RECEIVED` | persistiert und publiziert für neue Analysen ausschließlich die kompakte Version-1-Projektion |
| `DecisionSignalAdapter` | `DECISION_CREATED`, `SIGNAL_CREATED` | persistiert und publiziert beide Stufen als kompakte Version-1-Projektion mit erhaltenen IDs |

## Verifizierter Feldverbrauch

| Consumer | Tatsächlich benötigte Felder | Besonderheit |
|---|---|---|
| Brain | Markt, Symbol, Richtung, Wahrscheinlichkeit, Preis, Indikatoren, Risiko, Quellzeit und Event-ID | projiziert einmal an der Eingangsgrenze und verwendet dieselbe kompakte Sicht für History und Folgeevent |
| Decision Core | Brain-Felder plus Confidence und IDs | ergänzt deterministische Decision-/Signal-IDs und Stufenfelder, ohne `raw_result` neu weiterzureichen |
| Crypto Trade Tracker | Markt, Symbol, Richtung, Preis, ATR, Risiko, IDs | bevorzugt `market_context.recent_swing_low/high`; alte Payloads verwenden weiterhin Kerzen als Legacy-Fallback |
| Outcome Tracker | Markt, Symbol, Richtung, Preis, Risikoziele, Decision-/Signal-IDs und Zeitstempel | benötigt kein vollständiges Raw Result |
| Control Center | kompakte Anzeige-, Preis-, Status- und Tradefelder | projiziert bereits auf eine kleine Sicht |
| Telegram | Markt, Symbol, Richtung, Wahrscheinlichkeit, Preis und optionale Tradefelder | bleibt deaktiviert beziehungsweise Dry-Run |
| Learning Graph | Symbol, Richtung, Indikatornamen und Ergebnislabel | bevorzugt `public_result`; alte Payloads verwenden weiterhin `raw_result.result` als Legacy-Fallback |
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
| `CryptoTradeTracker`: `raw_result.market_data.candles` | `market_context.recent_swing_low` und `market_context.recent_swing_high` | seit 1. August 2026 Primärfelder; Rohkerzen nur noch Legacy-Fallback |
| `LearningGraphBuilder`: `raw_result.result` | `public_result` | seit 1. August 2026 Primärfeld; Raw Result nur noch Legacy-Fallback |

Die Referenzprojektion berechnet die beiden Swing-Werte ausschließlich für die Kompatibilitätsmigration aus den letzten 20 Legacy-Kerzen. Die Kerzen selbst werden nie in die kompakte Ausgabe übernommen.

## Migrations- und Kompatibilitätsregeln

1. Consumer für `schema_name`/`schema_version` und die beiden Ersatzfelder vorbereiten. Die Ersatzfeld-Priorität für Tracker und Graph ist umgesetzt; die Schemaannahme erfolgt erst beim Producer-Wechsel.
2. Brain auf die Projektion umstellen. Dieser Schritt ist für neue Brain-Datensätze und Folgeevents umgesetzt.
3. Decision-/Signal-Producer auf die Projektion umstellen. Dieser Schritt ist für neue Events und Ledgerdatensätze umgesetzt.
4. NeuroBrain darf nur die Projektion persistieren; seine vorhandene kompakte Kopfsicht und IDs bleiben erhalten.
5. Bestehende JSONL-History wird weder geändert noch gelöscht. Leser behalten einen Legacy-Pfad für alte Datensätze.
6. Unbekannte Schema-Hauptversionen werden nicht stillschweigend als kompatibel behandelt.
7. Keine reale Order- oder Telegram-Freigabe ist Bestandteil dieses Vertrags.

## Tests

```powershell
.\.venv\Scripts\python.exe -m unittest tests.test_event_payload_contract -v
```

Die Tests prüfen Schema und Pflichtfelder, den Ausschluss aller Bulk-Felder, die beiden Legacy-Ersatzprojektionen sowie die deklarierte Feldabdeckung der tatsächlich untersuchten Consumer.
