# Decision-Gate-Vertrag

Stand: 8. August 2026

Vertragsname: `pandorickki.decision-gate`, Version `1`

## Zweck und Sicherheitsgrenze

Version 1 ist eine ausführbare, rein beobachtende und fail-closed Referenz für eine spätere fachliche Freigabekette. Sie liegt in `decision_gate_contract.py`, ist noch nicht an den EventBus angeschlossen und verändert weder bestehende Decisions und Signals noch Tracker, Telegram oder History.

Ein Ergebnis `QUALIFIED` bedeutet ausschließlich, dass ein Kandidat die ausdrücklich übergebene Testpolicy erfüllt. Es bedeutet keine Meldungs-, Trade- oder Orderfreigabe. Jedes Version-1-Ergebnis setzt deshalb unveränderlich:

- `mode=OBSERVER`
- `release_status=OBSERVER_ONLY`
- `ready_for_telegram=false`
- `order_execution_allowed=false`

## Nachgewiesener Ist-Zustand

- `BrainAdapter` projiziert Analyseereignisse auf den kompakten Marktvertrag. Der vollständige Featureblock und damit `features.metadata.data_quality` werden absichtlich nicht weitergereicht.
- `DecisionSignalAdapter` erzeugt derzeit aus jedem Brain-Ereignis unmittelbar `DECISION_CREATED` und `SIGNAL_CREATED`; dabei setzt er `ready_for_telegram=true`, ohne eine unabhängige Qualitäts-, Risiko- oder Confidence-Prüfung.
- `TelegramAdapter` abonniert weiterhin Analyse- und simulierte Tradeereignisse direkt. Er liegt nicht hinter dem Decision Core, bleibt aber sicher deaktiviert und im Dry-Run.
- Der aktuelle Stock-Einzelsnapshot ist technisch valide, aber nur `WARN/UNVERIFIED/WARMING`; der Live-Crypto-Pfad wurde mit `PASS/VERIFIED/READY` verifiziert.

Diese drei Laufzeitpfade werden durch Version 1 bewusst noch nicht geändert.

## Eingang

`evaluate_decision_gate(candidate, policy=...)` erwartet eine normalisierte Mapping-Sicht mit:

- `market_type`, `symbol`, `direction`
- `probability`, `confidence`
- positivem `price` oder `current_price`
- nicht leerer, strukturierter `facts`-Sicht
- `risk` mit zur Richtung passendem Stop und mindestens einem Take-Profit-Ziel
- keinem `feature_error`
- Feature-Qualität entweder als bisheriges `features.metadata.data_quality` oder als künftige kompakte `feature_quality`-Projektion
- optionaler `source_event_id` für die spätere Zuordnung

`project_feature_quality()` übernimmt nur die für das Gate erforderlichen Zähler sowie Order- und Warmupstatus. Verletzungsdetails, Warnlisten und der vollständige Featureblock werden nicht kopiert.

## Explizite Policy

Wahrscheinlichkeits- und Confidence-Schwellen besitzen absichtlich keine Defaults. Jeder Aufrufer muss `DecisionGatePolicy(minimum_probability=..., minimum_confidence=...)` ausdrücklich konfigurieren und später dokumentieren. So wird keine unbestätigte Produktentscheidung im Code versteckt.

Die sichere Version-1-Grundeinstellung verlangt:

- Richtung `LONG` oder `SHORT`
- Markt `crypto` oder `stock`
- Qualitätsstatus `PASS`
- Reihenfolge `VERIFIED`
- Warmup `READY`
- Fakten vorhanden
- vollständigen, richtungskonsistenten Risikoplan
- identische Probability und Confidence, sofern die explizite Toleranz nicht erhöht wird

Commodity wird mangels heutiger Feature-Qualitätsanbindung fail-closed blockiert. `WAIT`, `HOLD`, fehlende oder unbekannte Richtungen sind nicht freigabefähig.

## Zustände und Reason Codes

Das Gate liefert nur `QUALIFIED` oder `BLOCKED`. Mehrere Ablehnungsgründe bleiben gleichzeitig sichtbar und erscheinen deterministisch in `reason_codes`.

| Bereich | Reason Codes |
|---|---|
| Identität | `DG_MARKET_NOT_ALLOWED`, `DG_SYMBOL_MISSING`, `DG_DIRECTION_NOT_ELIGIBLE` |
| Preis | `DG_PRICE_INVALID` |
| Wahrscheinlichkeit | `DG_PROBABILITY_INVALID`, `DG_PROBABILITY_BELOW_THRESHOLD` |
| Confidence | `DG_CONFIDENCE_INVALID`, `DG_CONFIDENCE_BELOW_THRESHOLD`, `DG_CONFIDENCE_CONFLICT` |
| Fakten/Features | `DG_FACTS_MISSING`, `DG_FEATURE_ERROR` |
| Datenqualität | `DG_QUALITY_MISSING`, `DG_QUALITY_SCHEMA_UNSUPPORTED`, `DG_QUALITY_STATUS_NOT_ALLOWED`, `DG_ORDER_NOT_VERIFIED`, `DG_WARMUP_NOT_READY` |
| Risiko | `DG_RISK_MISSING`, `DG_RISK_DIRECTION_CONFLICT`, `DG_STOP_LOSS_INVALID`, `DG_TAKE_PROFIT_INVALID` |
| Erfolg | `DG_QUALIFIED` |

## Geplante Integrationsreihenfolge

1. Die kompakte `feature_quality`-Projektion an der Analyse-/Brain-Grenze mit Kompatibilitätstests weiterreichen.
2. Einen separaten Observer abonnieren, der Kandidaten ausschließlich bewertet und versionierte Gate-Ergebnisse in einen eigenen begrenzten Auditpfad schreibt.
3. Gate-Ergebnisse über mehrere Livezyklen auswerten; Schwellen bleiben explizite Konfiguration und benötigen fachliche Freigabe.
4. Erst nach separater Freigabe den heutigen automatischen Signalpfad hinter ein bestandenes Gate verschieben.
5. Telegram später ausschließlich an ein finales freigegebenes Ereignis koppeln; bis dahin deaktiviert/Dry-Run.

Keine Stufe dieser Reihenfolge erlaubt reale Orderausführung.

## Tests

```powershell
.\.venv\Scripts\python.exe -m unittest tests.test_decision_gate_contract -v
```

Die Tests decken den qualifizierten Observerfall, fehlende Qualität, den Stock-Fallback, HOLD/WAIT, Fakten-, Feature-, Confidence- und Risikokonflikte sowie die unveränderliche Telegram-/Order-Sperre ab.
