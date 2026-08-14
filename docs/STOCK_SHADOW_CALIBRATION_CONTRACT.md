# Stock-Shadow-Score- und Confidence-Kalibrierungsvertrag

Stand: 10. August 2026

Vertragsname: `pandorickki.stock-shadow-calibration`, Version `1`

## Status und Zweck

Version 1 ist zunächst ausschließlich ein fachlicher Dokumentations- und Reviewvertrag. Es existiert noch kein Kalibrierungsmodul, kein trainiertes Modell und keine Laufzeitkopplung.

Die in diesem Vertrag genannten Mindestabdeckungen und Sicherheitsgrenzen wurden am 10. August 2026 vom Benutzer ausdrücklich bestätigt. Diese Bestätigung ist keine Freigabe für einen Verification-Lauf, Fit, Gate-Umschaltung, Telegram oder Orders.

Der Vertrag legt fest, unter welchen Bedingungen der heutige transparente `UNVALIDATED_HEURISTIC_SCORE` später gegen unabhängige Stock-Outcomes geprüft werden darf. Er verhindert insbesondere, dass der aktuelle Shadow-Score, wiederholte Zyklen derselben Tageskerze oder die aus `probability` kopierte Brain-`confidence` als kalibrierte Wahrscheinlichkeit ausgegeben werden.

Der Vertrag darf niemals:

- die aktive Legacy-Decision, den Decision Core oder den Decision-Gate-Observer verändern;
- `ready_for_telegram=true` oder `order_execution_allowed=true` setzen;
- Telegram aktivieren oder eine Order erzeugen;
- Crypto einbeziehen, solange dort keine unabhängige Shadow-Decision existiert;
- bestehende Runtime-, History-, Learning- oder Verification-Daten umschreiben;
- aus einem kurzen Lauf eine Aussage wie „Shadow ist besser“ ableiten.

## Verbindliche Begriffe

| Begriff | Bedeutung |
|---|---|
| `bullish_score` | Transparenter Rohwert von 0 bis 100 aus den fünf heutigen technischen Komponenten. |
| `directional_score` | Für LONG der `bullish_score`, für SHORT `100 - bullish_score`; nur für LONG/SHORT definiert. |
| `heuristic_probability` | Heutiges Feld `shadow.probability`; bleibt bis zu einer erfolgreichen Kalibrierung ein Score und keine Wahrscheinlichkeit. |
| `calibrated_probability` | Geschätzte Wahrscheinlichkeit, dass der feste richtungsbezogene 24h-Outcome `WIN` wird. Darf nur aus einem gültigen, zeitlich getrennt validierten Artefakt stammen. |
| `calibration_confidence` | Evidenzqualität der Kalibrierung, getrennt von Score und Probability. Sie beschreibt Stichprobenumfang und Unsicherheit, nicht Marktrichtung. |
| `independent_case` | Höchstens ein kanonischer Fall je Symbol, jüngstem Kerzenzeitstempel, Outcome-Policy, Observer-Version und Konfigurationsfingerprint. |

`calibration_confidence` darf nicht aus `calibrated_probability` kopiert werden. Sie wird als `INSUFFICIENT`, `LOW`, `MEDIUM` oder `HIGH` plus Stichprobenumfang und Unsicherheitsintervall dargestellt. Eine numerische Gate-Confidence ist nicht Bestandteil von Version 1.

## Zulässige Datenquelle

Zulässig sind ausschließlich unveränderte Datensätze aus dem append-only Stock-Shadow-Verification-Ledger:

- ein gültiger `VERIFICATION_CREATED`-Fall;
- ein zugehöriger `OUTCOME_COMPLETED`-Datensatz;
- `asset_type=stock` und `mode=OBSERVER_ONLY`;
- Shadow-Richtung LONG oder SHORT;
- positiver Entry- und Exitpreis;
- feste Outcome-Policy `FORWARD_MARK_TO_MARKET` mit identischem Horizont und Neutralband;
- strikt späterer öffentlicher Quote-Zeitstempel;
- unterstützte Schema-, Observer- und Konfigurationsversion;
- keine Telegram-, Order- oder Active-Decision-Wirkung.

HOLD, `PENDING`, `UNKNOWN`, unvollständige Quotes und `SPCX` ohne belegbare öffentliche Quelle bleiben in Abdeckungszählern sichtbar, dürfen aber keine Richtungswahrscheinlichkeit fitten.

## Zielvariable

Für einen LONG-/SHORT-Fall gilt:

- `1`, wenn der bestehende 24h-Outcome `WIN` ist;
- `0`, wenn er `LOSS` oder `NEUTRAL` ist;
- nicht fit-fähig bei `PENDING` oder `UNKNOWN`.

Damit bedeutet `calibrated_probability` ausdrücklich `P(richtungsbezogener 24h-Move oberhalb des Neutralbands)`. Sie behauptet weder eine Stop-/Zielberührung noch einen realen Tradegewinn.

Der richtungsbezogene Prozent-Return wird zusätzlich deskriptiv ausgewiesen, aber nicht als Wahrscheinlichkeit bezeichnet.

## Unabhängigkeit und Deduplizierung

Mehrere Minutenzyklen mit derselben letzten Tageskerze sind keine unabhängigen Trainingsfälle. Vor jeder Kalibrierung wird deshalb deterministisch nach folgendem Schlüssel gruppiert:

```text
symbol
+ latest_candle_timestamp
+ outcome horizon
+ neutral band
+ observer version
+ config fingerprint
```

Je Gruppe ist nur der zeitlich erste vollständig beobachtbare Fall kalibrierungsfähig. Alle weiteren Fälle bleiben als Wiederholungen auditierbar und werden als `correlated_repetitions_excluded` gezählt.

Kein Datensatz darf gleichzeitig in Fit und Validierung liegen. Die Trennung erfolgt chronologisch nach `analysis_timestamp`; zufälliges Mischen über denselben Markttag oder dieselbe Kerze ist verboten.

## Datenstatus und Mindestabdeckung

Version 1 kennt folgende Zustände:

- `INSUFFICIENT_DATA`: Mindestabdeckung nicht erreicht;
- `RESEARCH_ONLY`: Fit möglich, aber unabhängige Validierung oder Stabilität unzureichend;
- `VALIDATED_OBSERVER`: vorab definierte Daten- und Gütegrenzen erfüllt, weiterhin ohne Freigabewirkung;
- `REJECTED`: Artefakt verletzt Vertrag, verschlechtert den Referenzwert oder ist instabil.

Für einen ersten `RESEARCH_ONLY`-Fit werden mindestens verlangt:

- 400 unabhängige abgeschlossene LONG-/SHORT-Fälle insgesamt;
- mindestens 100 Fälle je Richtung;
- mindestens 30 unterschiedliche US-Handelstage;
- mindestens vier unterstützte Symbole;
- mindestens 40 Fälle in jedem tatsächlich ausgewerteten Score-Bucket.

Für `VALIDATED_OBSERVER` muss zusätzlich die zeitlich spätere Holdout-Menge mindestens 20 Prozent der Fälle, 80 Fälle insgesamt und 20 Fälle je Richtung enthalten.

Diese Grenzen sind Forschungs- und Reviewgrenzen, keine Handelsfreigabe. Eine spätere Änderung erfordert eine neue Vertragsversion; sie darf nicht rückwirkend passend zu beobachteten Ergebnissen abgesenkt werden.

## Kalibrierungsverfahren

Die erste spätere Implementierung muss mindestens drei Kandidaten getrennt vergleichen:

1. unveränderter directional Score als Referenz;
2. feste empirische Score-Buckets mit sichtbaren Zählern und Wilson-Intervallen;
3. monotone Isotonic-Kalibrierung, ausschließlich auf dem chronologisch früheren Fit-Segment.

Ein komplexeres Verfahren ist ohne neuen Review nicht zulässig. Es findet kein Online-Lernen und kein automatisches Nachtrainieren im laufenden PandorickKi-Prozess statt.

Das gewählte Artefakt wird nur dann `VALIDATED_OBSERVER`, wenn es auf dem unangetasteten Holdout:

- den Brier Score gegenüber der Rohscore-Referenz nicht verschlechtert;
- eine Expected Calibration Error von höchstens 0,08 erreicht;
- je Richtung eine Expected Calibration Error von höchstens 0,12 erreicht;
- Coverage, Neutral-, UNKNOWN- und Ausschlussquoten vollständig ausweist;
- keine wesentliche Verschlechterung eines einzelnen unterstützten Symbols verbirgt.

Log Loss, Brier Score, ECE, Reliability-Tabelle, mittlerer richtungsbezogener Return und Konfidenzintervalle müssen gemeinsam berichtet werden. Eine einzelne Hit-Rate genügt nicht.

## Artefaktvertrag

Ein späteres Artefakt muss unveränderlich und versioniert mindestens enthalten:

- `schema_name` und `schema_version`;
- `calibration_id`;
- Erstellungszeit und Daten-Cutoff;
- Score-, Verification-, Outcome- und Policy-Versionen;
- Konfigurations- und Dataset-Fingerprint;
- Fit-/Holdout-Zeiträume und Fallzahlen;
- Zähler für LONG, SHORT, HOLD, PENDING, UNKNOWN und ausgeschlossene Wiederholungen;
- Verfahren und feste Parameter;
- Reliability-Buckets mit Zähler, Rohscore, beobachteter Erfolgsrate und Unsicherheitsintervall;
- Gesamt-, Richtungs- und Symbolmetriken;
- Status und deterministische Reason Codes;
- `affects_active_decision=false`;
- `ready_for_telegram=false`;
- `order_execution_allowed=false`.

Artefakte werden append-only abgelegt. Ein neues Fit ersetzt oder verändert kein altes Artefakt. Rohkerzen, `raw_result`, Secrets und vollständige Fremdantworten sind verboten.

## Reason Codes

Mindestens folgende Reason Codes sind für eine spätere Referenzimplementierung reserviert:

| Bereich | Reason Codes |
|---|---|
| Eingang | `SC_SCHEMA_UNSUPPORTED`, `SC_CONFIG_MIXED`, `SC_POLICY_MIXED`, `SC_OUTCOME_INVALID` |
| Abdeckung | `SC_TOTAL_SAMPLE_LOW`, `SC_DIRECTION_SAMPLE_LOW`, `SC_TRADING_DAYS_LOW`, `SC_SYMBOL_COVERAGE_LOW`, `SC_BUCKET_SAMPLE_LOW` |
| Unabhängigkeit | `SC_CORRELATED_REPETITION_EXCLUDED`, `SC_TEMPORAL_LEAKAGE` |
| Validierung | `SC_HOLDOUT_LOW`, `SC_BRIER_NOT_IMPROVED`, `SC_ECE_TOO_HIGH`, `SC_DIRECTION_ECE_TOO_HIGH`, `SC_SYMBOL_INSTABILITY` |
| Ergebnis | `SC_INSUFFICIENT_DATA`, `SC_RESEARCH_ONLY`, `SC_VALIDATED_OBSERVER`, `SC_REJECTED` |

Mehrere Gründe dürfen gleichzeitig auftreten. Fehlende Daten werden niemals als neutraler Erfolg behandelt.

## Heutiger Reviewstand

Die US-Marktphasenmessung vom 10. August 2026 ist technisch wertvoll, aber nicht kalibrierungsfähig:

- fünf Zyklen und 25 Stock-Audits;
- 20 berechnete Shadows: 10 LONG, 5 SHORT, 5 HOLD;
- vier unterstützte Symbole mit wiederholten Tageskerzen;
- fünf `SPCX`-Fälle ohne gültigen öffentlichen Quote-Zeitstempel;
- Verification im normalen Betrieb deaktiviert;
- null abgeschlossene unabhängige 24h-Verification-Outcomes.

Der korrekte Vertragsstatus ist daher `INSUFFICIENT_DATA` mit mindestens `SC_TOTAL_SAMPLE_LOW`, `SC_DIRECTION_SAMPLE_LOW`, `SC_TRADING_DAYS_LOW`, `SC_BUCKET_SAMPLE_LOW` und `SC_HOLDOUT_LOW`. Es wird keine `calibrated_probability` und keine `calibration_confidence` erzeugt.

Auch ein siebentägiger Lauf ist voraussichtlich nur eine technische Machbarkeits- und Datenqualitätsprüfung, noch keine belastbare Kalibrierung.

## Sichere weitere Reihenfolge

1. Vertrag reviewen und Schwellen ausdrücklich bestätigen oder versioniert ändern.
2. Stock-Verification nur nach separater Freigabe mit unverändertem Konfigurationsfingerprint für ungefähr sieben Tage aktivieren.
3. Danach ausschließlich Datenqualität, Outcome-Abdeckung, Deduplizierung und Unabhängigkeit prüfen.
4. Bei weiterhin zu kleiner Stichprobe den observer-only Erfassungszeitraum verlängern; nichts fitten.
5. Erst nach Erreichen der Mindestabdeckung eine separate, offline ausgeführte Referenzimplementierung mit Tests planen.
6. Ein kalibriertes Observer-Artefakt niemals automatisch an Gate, Telegram oder Orders koppeln.

## Freigegebener Datenerfassungslauf

Der Benutzer hat den siebentägigen Stock-Verification-Lauf am 10. August 2026 separat freigegeben. Er startete um 19:03:44 Uhr Europe/Berlin mit Fingerprint `3d23f923d6b9d9dc3019457afcb078591b5d8c8b4d1f4f4db55911724fa71747`, 24h-Horizont und 0,05-%-Neutralband. Dieser Lauf ist ausschließlich eine technische Datenqualitäts-, Outcome-Abdeckungs- und Unabhängigkeitsprüfung. Er ist keine Fit- oder Kalibrierungsfreigabe. Abschlussdaten ab `2026-08-10T17:03:44Z` werden getrennt von den bereits vorhandenen Kurzlauffällen ausgewertet.
