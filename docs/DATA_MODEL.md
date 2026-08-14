# Datenmodell

Stand: 12. August 2026

## MarketRegimeSnapshot v1

`MarketRegimeSnapshot` ist eine kompakte, append-only Observerprojektion. Die vollständige Semantik und Identitätsbildung steht in `docs/MARKET_REGIME_CONTRACT.md`.

```text
MarketRegimeSnapshot
├── regime_id / feature_snapshot_id / source_event_id
├── symbol / asset_type / timestamp
├── trend_direction / trend_confidence / trend_reasons
├── volatility_regime / volatility_score / volatility_reasons
├── trend_phase / phase_confidence / phase_reasons
├── data_quality_status / data_quality_score
├── timeframes_used / missing_timeframes
└── classifier_version / config_fingerprint / schema_version / created_at
```

Persistenz: `data/market_regime.jsonl` plus rotierte Archive. Rohkerzen, vollständige Feature-Reihen, `raw_result`, Secrets und lokale Fremdpfade sind ausgeschlossen. Bestehende Datenmodelle und History-Dateien werden nicht migriert oder umgeschrieben.
