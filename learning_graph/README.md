# Pandorick Learning Graph

The Pandorick Learning Graph is a separate, read-only public graph layer for the PandorickKi platform.

It is designed for a beta-member view that shows public activity:

- active markets
- public indicator categories
- repeated setup clusters
- learning updates
- documented decisions
- public result states
- system components

It must not expose trading formulas, internal weights, raw Brain memory, API responses, file paths, tokens, or debug data.

## Public Node Types

- `MARKET`
- `INDICATOR`
- `PATTERN`
- `LEARNING`
- `DECISION`
- `RESULT`
- `DATA_SOURCE`
- `SYSTEM`

## Public Relationship Types

- `ANALYZED_BY`
- `USES_PUBLIC_FACTOR`
- `OBSERVED_PATTERN`
- `CREATED_LEARNING`
- `CREATED_DECISION`
- `HAS_RESULT`
- `CONNECTED_TO_SOURCE`
- `RELATED_MARKET`
- `UPDATED_BY`

## Data Flow

```text
existing internal data
-> graph_repository.py
-> graph_builder.py
-> graph_sanitizer.py
-> graph_service.py
-> API in later phase
-> browser in later phase
```

## Security Boundary

`graph_sanitizer.py` is mandatory for every browser-facing payload.

Allowed node fields are whitelisted in `graph_config.py`.
All unknown fields are removed.

## Current Phase

Phase 3 adds only the backend ground structure, models, sanitizer, repository, builder, service and tests.

API and frontend integration are intentionally not part of this phase.

