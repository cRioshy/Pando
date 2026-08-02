# Learning-Metrikvertrag

Stand: 2. August 2026

Dieser Vertrag beschreibt ausschließlich beobachtbare Auswertungs-, Outcome- und Projektionsmetriken. PandorickKi trainiert aktuell kein ML-Modell.

## Schema

- Name: `pandorickki.learning-metrics`
- Version: `1`
- Ausführbare Referenz: `learning_metrics_contract.py`
- Öffentliche Sichten: Learning Report, Trading-Statistik und Learning Graph

Bestehende API-Felder bleiben vorerst als Kompatibilitätsaliase erhalten. Neue Oberflächen müssen die expliziten Version-1-Felder und ihre Nenner verwenden.

## Verbindliche Begriffe

| Begriff | Bedeutung | Keine Bedeutung |
|---|---|---|
| Decision | Persistiertes finales `DECISION_CREATED` im betrachteten Datenfenster | keine unabhängige Risiko- oder KI-Freigabe |
| Outcome-fähige Decision | Finale LONG-/BUY-/SHORT-/SELL-Decision | HOLD, WAIT oder WATCHLIST |
| Zugeordnetes Outcome | Geschlossener simulierter Trade, der im Report per `decision_id` einer geladenen Decision zugeordnet wurde | ungeprüftes Learning-Event |
| Hit-Rate | `Wins / (Wins + Losses)` | nicht Wins geteilt durch alle geschlossenen Outcomes |
| Breakeven | Eigenständige geschlossene Ergebnisklasse | weder Win noch Loss; nicht im Hit-Rate-Nenner |
| Outcome-Abdeckung | Zugeordnete geschlossene Outcomes geteilt durch outcome-fähige Decisions desselben vergleichbaren Scopes | keine Erfolgsquote |
| Learning-Update | Gezählt ausgegebenes `AI_LEARNING_UPDATED`-Projektionsereignis | kein erfolgreicher Modellupdate und kein Training |
| Muster-Bucket | Sichtbarer, deduplizierter Graphknoten für eine beobachtete Kategorie | kein gelerntes Modellmuster |
| Projektion heute | Datensätze mit heutigem Datum innerhalb des geladenen Graph-Fensters | keine globale Tagesgesamtsumme |

## Pflichtfelder und Nenner

`build_learning_metrics()` liefert mindestens:

- `decisions.total`
- `decisions.outcome_eligible`
- `outcomes.matched`, `closed`, `wins`, `losses`, `breakeven`, `unknown`
- `outcomes.classified_for_hit_rate`
- `rates.hit_rate_percent`, `hit_rate_numerator`, `hit_rate_denominator`
- `rates.outcome_coverage_percent`, `outcome_coverage_numerator`, `outcome_coverage_denominator`
- `rates.outcome_coverage_scope_consistent`
- `learning.update_events`
- `learning.successful_model_updates = null`
- `learning.patterns_learned = null`
- `ml_training.active = false`
- `ml_training.model_updates = 0`

Eine Rate ohne belastbaren Nenner ist `null` und darf in der UI nicht als `0 %` erscheinen.

## Datenbereiche

Der Learning Report lädt höchstens die letzten 6.000 Decision- und Outcome-Ledgerzeilen und ordnet Outcomes per `decision_id` zu. Seine Outcome-Abdeckung gilt ausschließlich für dieses geladene Fenster.

Die persistente Trading-Statistik verwendet historisch gewachsene Aggregatzähler. Wenn geschlossene Outcomes und outcome-fähige Decisions nicht aus einem nachweislich identischen Rekonstruktionsscope stammen, ist `outcome_coverage_scope_consistent=false` und `outcome_coverage_percent=null`. Die Oberfläche zeigt dann `nicht vergleichbar`, statt eine Quote größer als 100 Prozent zu erfinden.

Legacy-Stock-Daten ohne `decision_id` bleiben als ausdrücklich markierter `legacy_order_fallback` lesbar. Für diesen Fallback wird keine exakte Outcome-Abdeckung behauptet.

## Kompatibilität

- `summary.learning_events_with_outcome` bleibt als Alias für zugeordnete Outcome-Datensätze erhalten.
- `learning_score` bleibt als Alias für `evaluation_score` erhalten; die UI nennt ihn Auswertungs-Score und weist auf fehlendes ML-Training hin.
- `trading.hit_rate` bleibt erhalten, verwendet aber Version 1 mit Wins-plus-Losses-Nenner.
- `successful_learnings` und `learned_patterns` liefern `null`, weil kein entsprechender Erfolgs- oder Trainingsnachweis existiert.
- `patterns_recognized` und `new_learnings_today` bleiben als Graph-Aliase; die UI verwendet `pattern_buckets` und `learning_projection_records_today`.

## Sicherheits- und Datenregeln

- Keine bestehende History oder Statistikdatei für diesen Vertrag umschreiben oder löschen.
- Keine reale Orderausführung aus diesen Metriken ableiten.
- Telegram bleibt deaktiviert beziehungsweise im Dry-Run.
- Ein späteres ML-Training benötigt einen neuen, ausdrücklich freigegebenen Modell-, Daten- und Evaluationsvertrag; Modulnamen oder Projektionszähler reichen dafür nicht aus.
