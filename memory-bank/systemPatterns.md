# System Patterns: Emission Factor Pipeline

## Architecture — layered ETL
```
[Source APIs] -> [Lambda ingestion] -> S3 bronze/
   -> [dbt + DuckDB] staging views -> intermediate views -> marts tables
   -> [RDS Postgres] gold serving
```
Medallion layering: Bronze (raw S3) -> Silver (staging/intermediate) -> Gold (marts).

## Orchestration
GitHub Actions (`.github/workflows/etl_pipeline.yml`) triggers ingestion and configures AWS creds. Ingestion is a Lambda function registered as a parser registry.

## Code structure
- `ingestion/lambda_handler.py` — entry point + parser registry `{ademe, nve, defra}`. Reads `S3_BUCKET` env; writes `bronze/<source>/<year>/factors.csv`.
- `ingestion/parsers/<source>_parser.py` — fetch + filter + validate per source; returns `{"<year>": csv_bytes}`.
- `ingestion/parsers/models.py` — Pydantic row models: `AdemeRawRow`, `DefraRawRow`, `NveRawRow`.
- `transformation/normalise_emission_factors/` — dbt project `profile: transform`.
  - **staging** (`stg_ademe|stg_defra|stg_nve`, `sources.yml`, `stg_schema.yml`) — materialized `view`; read closest raw seed/source.
  - **intermediate** (`imt_ademe_cleaned|imt_defra_cleaned|imt_nve_cleaned`, `imt_all_sources`) — `view`; cleaning + union across sources.
  - **marts** — `table` (Gold).
  - Seeds: `ademe_translations`, `defra_category_mapping`, `defra_overrides`, `defra_sub_category_mapping`.
  - Deps: `dbt_utils` (vendored in `dbt_packages/`).

## Key patterns / invariants
- **Idempotency** — re-runnable; no duplicate rows on repeat.
- **EEP** — validate-then-write; bad rows raise before S3 write.
- **Temporal** — every EF has `valid_from`/`valid_to`; tested (`valid_from_before_valid_to_*`).
- **Geo** — all locations map to ISO 3166-1/2; fallback Sub-national -> National -> Global.
- **Type-checking** — critical fields cross-validated in Pydantic `field_validator`s (non-empty, non-negative, year bounds).

## Current dbt model graph (branch `transformation_imt`)
```
stg_ademe ---> imt_ademe_cleaned ---+
stg_defra ---> imt_defra_cleaned ---+--> imt_all_sources --> marts
stg_nve   ---> imt_nve_cleaned   ---+
```
Latest commits: `staging models` (d644d71), `add intermediate models` (25db322).