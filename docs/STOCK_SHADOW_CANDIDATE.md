# Stock-Shadow-Kandidat

Stand: 9. August 2026

## Zweck und Grenze

`pandorickki.stock-shadow-candidate` Version 1 ist eine ausschließlich beobachtende Aktienprojektion. Sie wird vollständig aus öffentlichen Yahoo-Tageskerzen und dem separat geladenen öffentlichen Kurs berechnet. Sie ersetzt, verändert oder bestätigt die aktive Legacy-Aktienentscheidung nicht.

Der Kandidat wird nicht auf den EventBus publiziert und nicht in Brain-, Decision-, Signal- oder NeuroBrain-History persistiert. Der getrennte Vertrag `pandorickki.stock-shadow-risk` darf für LONG/SHORT einen observer-only Risikoplan aus derselben öffentlichen Datensicht ergänzen. `ready_for_telegram=false` und `order_execution_allowed=false` bleiben unveränderlich; weder Kandidat noch Plan können eine Meldung oder Order freigeben.

## Eingangsvertrag

- mindestens 200 vollständig zeitgestempelte, valide OHLCV-Tageskerzen
- Qualitätsstatus `PASS`, Reihenfolge `VERIFIED`, Warmup `READY`
- positiver öffentlicher aktueller Kurs
- explizite öffentliche Kerzen- und Preisquelle
- explizite LONG-/SHORT-Schwellen; derzeit 60 beziehungsweise 40 im Bullish Score

Ungültige oder zu kurze Reihen liefern einen kompakten `BLOCKED`-Datensatz ohne Richtung und Probability.

## Version-1-Berechnung

Der Bullish Score startet bei 50 und addiert transparente, versionierte Beiträge:

| Beobachtung | bullisch | bärisch |
|---|---:|---:|
| Kurs gegenüber SMA20 | +8 | -8 |
| SMA20 gegenüber SMA50 | +8 | -8 |
| SMA50 gegenüber SMA200 | +10 | -10 |
| 20-Tage-Rendite | +8 | -8 |
| RSI14 ab 55 / bis 45 | +6 | -6 |

Exakte Gleichstände der Trendwerte und RSI14 zwischen 45 und 55 sind neutral und tragen 0 bei.

Ab Bullish Score 60 entsteht `LONG`, bis 40 `SHORT`, dazwischen `HOLD`. `probability` ist die Stärke in Richtung des Kandidaten. Sie ist ausdrücklich als `UNVALIDATED_HEURISTIC_SCORE` gekennzeichnet: keine statistisch kalibrierte Eintrittswahrscheinlichkeit, keine Confidence und keine Handelsfreigabe.

Die kompakte Projektion enthält SMA20/50/200, 20-Tage-Rendite, RSI14, ATR14, Volumenverhältnis, Qualitätsprojektion und Score-Komponenten, aber keine Kerzenliste.

## Vergleich mit Legacy

`StockAdapter` hält zwei Sichten ausdrücklich getrennt:

- `legacy`: bestehende Placeholder-Richtung und -Probability aus dem externen Aktienprojekt
- `public_shadow`: Richtung und unkalibrierter Score aus ausschließlich öffentlichen PandorickKi-Daten

`direction_matches` ist nur eine Beobachtung. `affects_active_decision` ist immer `false`. Der Stock-Datenvertrag bewertet den öffentlichen Shadow einschließlich des getrennten Risikoplans fail-closed. Auch ein dortiges `READY` ist nur Datenreife und bleibt für Decision Gate, Telegram und Orders ohne Wirkung.

## Nicht enthalten

- der Risikoplan ist ein eigener observer-only Vertrag und keine aktive Freigabe
- keine unabhängige Confidence
- keine EventBus-Publikation oder History-Persistenz
- keine Umschaltung des aktiven Feature-/Decision-/Signalpfads
- keine Telegram- oder Orderfreigabe

## Kalibrierungsgrenze

Der separate Vertrag `pandorickki.stock-shadow-calibration` Version 1 in `docs/STOCK_SHADOW_CALIBRATION_CONTRACT.md` definiert eine mögliche spätere Offline-Prüfung gegen unabhängige abgeschlossene Verification-Outcomes. Er ändert die heutige Scoreformel nicht. Solange dessen Mindestabdeckung und chronologische Validierung nicht erfüllt sind, bleibt `probability_kind=UNVALIDATED_HEURISTIC_SCORE`; es gibt keine kalibrierte Probability und keine unabhängige Confidence.
