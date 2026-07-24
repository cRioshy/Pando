# PandorickKi Learning Performance Report

Stand: 2026-07-19

## Ziel

Dieser Report misst nicht die Menge der Learning-Events, sondern ob gespeicherte Ergebnisdaten eine nachvollziehbare Qualitätsauswertung erlauben.

## Datenbasis

- Stock-Decisions: `stock_decisions.json`
- Stock-Learning-Events: `stock_logs.json`
- Plattform-Brain-Events: `brain_events.jsonl` und rotierte `brain_events/*.jsonl`
- Keine produktiven Lernparameter wurden verändert.
- Keine Daten wurden gelöscht oder zurückgesetzt.

## Aktuelle Auswertung

- Entscheidungen im Report: 37.460
- Outcome-Daten mit Win/Loss: 44.106
- Crypto-Decision-Records: 1.351
- Trefferquote aus eindeutigen Stock-Outcomes: 54,38 %
- Durchschnittliche Confidence: 55,61 %
- Durchschnittlicher simulierter Preis-Change: 0,026 %
- Learning-Updates pro Decision: 1,1774
- Learning Score: 78,57 / 100

## Lernfortschritt

Vergleich erste 1000 gegen letzte 1000 auswertbare Ereignisse:

- Trefferquote-Delta: -1,80 Prozentpunkte
- Confidence-Delta: +0,742 Prozentpunkte
- Bewertung: Stagnation, keine klare Qualitätssteigerung nachweisbar.

## Marktvergleich

| Markt | Entscheidungen | Trefferquote | Confidence | Profit-Simulation |
| --- | ---: | ---: | ---: | ---: |
| Stocks | 36.764 | 54,38 % | 55,52 % | 0,026 % |
| Crypto | 696 | Nicht genuegend Daten | 59,95 % | Nicht genuegend Daten |

## Top-Symbole

| Symbol | Trefferquote | Confidence | Entscheidungen | Profit |
| --- | ---: | ---: | ---: | ---: |
| TSLA | 54,77 % | 55,60 % | 7.355 | 0,0331 % |
| MSFT | 54,63 % | 55,47 % | 7.355 | 0,0103 % |
| NVDA | 54,58 % | 55,85 % | 7.355 | 0,0241 % |
| AAPL | 54,37 % | 55,57 % | 7.355 | 0,0452 % |
| SPCX | 53,55 % | 55,13 % | 7.344 | 0,0175 % |

## Einschränkungen

- Crypto-Events enthalten aktuell keine belastbaren abgeschlossenen Ergebnisdaten.
- Drawdown, Haltedauer, Slippage und Gebühren sind aus den vorhandenen Daten nicht zuverlässig rekonstruierbar.
- Decision-Anzahl und Outcome-Anzahl sind nicht deckungsgleich; Trefferquote wird aus Stock-Learning-Logs berechnet.
- Der Report bewertet vorhandene Daten, trainiert aber nichts.

## Gesamtbewertung

PandorickKi zeigt beim Stock-System echte lernende Rückkopplung, aber die messbare Qualitätssteigerung stagniert aktuell. Die Plattform braucht eindeutige `decision_id`-Verknüpfungen zwischen Decision, Outcome, Trade-Verlauf und späterer Neubewertung, bevor die Lernqualität vollständig belastbar bewertet werden kann.

