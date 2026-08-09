# Decision-Gate-Audit – erste erweiterte Liveauswertung

Stand: 9. August 2026, Snapshot bis 10:40:38 Europe/Berlin

## Umfang und Sicherheitsgrenze

Diese Auswertung ist ein eingefrorener read-only Snapshot des Auditfensters von `2026-08-09T08:01:54Z` bis `2026-08-09T08:40:38Z`. Der Observer lief mit Probability `60`, Confidence `60` und Toleranz `0`. Er blieb durchgehend `OBSERVER_ONLY`; bestehende Decisions, Signals, Tracker, Telegram und History wurden nicht verändert.

Der Zeitraum von knapp 39 Minuten ist eine erweiterte Funktions- und Datenflussprüfung, noch keine statistisch belastbare Langzeit- oder Performancebewertung. Der Observer sammelt nach dem Snapshot weiter.

## Ergebnisübersicht

| Kennzahl | Ergebnis |
|---|---:|
| Kandidaten | 272 |
| eindeutige Quell-IDs | 272 |
| Crypto | 102 |
| Stock | 170 |
| `QUALIFIED` | 2 |
| `BLOCKED` | 270 |
| unsichere Telegram-/Orderfreigaben | 0 |
| Schema-/Policyfehler | 0 |
| neue Dienstfehler seit korrektem Netzwerkstart | 0 |

Alle 272 Datensätze verwendeten `pandorickki.decision-gate` Version 1, `mode=OBSERVER`, `release_status=OBSERVER_ONLY` und die bestätigte Policy `60/60/0`.

## Crypto

- 102 Kandidaten: 34 je BTCUSDT, ETHUSDT und XRPUSDT.
- Sämtliche Crypto-Datensätze hatten positiven Preis sowie Qualität `PASS/VERIFIED/READY`.
- Probability: Minimum 38,45, Mittel 46,44, Maximum 62,90.
- 100 Kandidaten waren `WAIT`, lagen unter 60 und wurden korrekt blockiert.
- Zwei aufeinanderfolgende ETHUSDT-`LONG`-Kandidaten qualifizierten technisch:
  - 10:39:22 Europe/Berlin: Probability/Confidence 62,90, Preis 1.918,13.
  - 10:40:35 Europe/Berlin: Probability/Confidence 60,90, Preis 1.916,98.
- Beide Ergebnisse behielten `ready_for_telegram=false` und `order_execution_allowed=false`.

Bewertung: Der Crypto-Pfad liefert die vom Gate benötigte technische Qualität. Die 2 von 102 qualifizierten Fälle zeigen, dass das Gate nicht pauschal blockiert. Dieser kurze Zeitraum sagt noch nichts über Outcome-Qualität oder Profitabilität aus.

## Aktien

- 170 Kandidaten: 34 je AAPL, MSFT, NVDA, TSLA und SPCX.
- Alle 170 Stock-Kandidaten waren `WARN/UNVERIFIED/WARMING`, weil der heutige Feature-Fallback nur einen nicht zeitgestempelten Einzelsnapshot besitzt.
- 31 Stock-Kandidaten lagen bei Probability mindestens 60, dennoch qualifizierte keiner.
- 31 Stock-Kandidaten waren `LONG`; alle 31 scheiterten zusätzlich an Stop und Take-Profit.
- `StockAdapter._normalize_decision()` erzeugt derzeit keinen normalisierten `risk`-Block. Der Gate-Befund ist deshalb korrekt und kein Schwellenproblem.
- SPCX besaß in allen 34 Snapshot-Datensätzen keinen positiven Livepreis und erhielt zusätzlich `DG_PRICE_INVALID`.

Bewertung: Aktien sind unter dem sicheren Vertrag derzeit prinzipiell nicht qualifizierbar. Die Gate-Regeln dürfen deshalb nicht gelockert werden. Zuerst müssen echte zeitgestempelte Kerzen, ein verlässlicher aktueller Preis und ein vollständiger richtungskonsistenter Risikoplan vertraglich bereitgestellt werden.

## Häufigste Blockierungsgründe

| Reason Code | Anzahl |
|---|---:|
| `DG_PROBABILITY_BELOW_THRESHOLD` | 239 |
| `DG_CONFIDENCE_BELOW_THRESHOLD` | 239 |
| `DG_DIRECTION_NOT_ELIGIBLE` | 239 |
| `DG_QUALITY_STATUS_NOT_ALLOWED` | 170 |
| `DG_ORDER_NOT_VERIFIED` | 170 |
| `DG_WARMUP_NOT_READY` | 170 |
| `DG_PRICE_INVALID` | 34 |
| `DG_STOP_LOSS_INVALID` | 31 |
| `DG_TAKE_PROFIT_INVALID` | 31 |
| `DG_QUALIFIED` | 2 |

## Wichtige Vertragsgrenze bei Confidence

`BrainAdapter` setzt heute `confidence = probability`. Confidence ist damit noch keine unabhängige Messgröße. Die Toleranz 0 prüft zwar deterministisch, kann aber aktuell keinen echten Konflikt zwischen zwei getrennten Bewertungen erkennen. Vor einer produktiven Gate-Nutzung muss entweder eine unabhängig begründete Confidence erzeugt oder das Feld fachlich korrekt umbenannt beziehungsweise aus der Freigaberegel entfernt werden.

## Schlussfolgerung

Der Observer arbeitet technisch korrekt und fail-closed. Die bestätigte 60/60-Policy sollte unverändert weiter beobachtet werden. Eine Umschaltung des aktiven Decision-/Signalpfads wäre verfrüht, weil:

1. das Auditfenster noch zu kurz für Outcome- oder Stabilitätsaussagen ist;
2. Stock-Daten die Version-1-Qualitätsgrenze grundsätzlich nicht erfüllen;
3. Stock keinen Gate-Risikoplan liefert;
4. SPCX keinen verlässlichen aktuellen Preis liefert;
5. Confidence derzeit Probability dupliziert;
6. Gate-Audits noch nicht systematisch mit späteren Outcomes verknüpft ausgewertet wurden.

## Nächster sinnvoller Schritt

Observer mindestens über einen deutlich längeren Zeitraum weiterlaufen lassen und danach denselben Snapshot mit Zeitfenster, Reason-Code-Verteilung, qualifizierten Fällen und späteren simulierten Outcomes wiederholen. Parallel ausschließlich den Stock-Datenvertrag analysieren: zeitgestempelte Kerzenhistorie, aktueller Preis, normalisierter Risikoplan und unabhängige Confidence. Noch keine Gate-, Signal- oder Telegram-Umschaltung vornehmen.
