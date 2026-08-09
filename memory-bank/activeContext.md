# Active Context: Emission Factor Pipeline

## Current focus
Marts (Gold) layer built and validated (`dim_emission_factors` table). Staging keys made deterministic (idempotent).

## Current state (from git)
- Branch: `transformation_imt`, clean working tree.
- dbt models present: staging (stg_ademe/stg_defra/stg_nve) + intermediate (imt_*_cleaned, imt_all_sources) + marts (`dim_emission_factors`, table).
- `dim_emission_factors`: 1,960 rows, 1,960 unique `ef_id`, all 21 `marts_schema.yml` tests pass.
- Staging `uuid()` replaced with deterministic md5 keys (NVE factor_type+year, DEFRA ID+year, ADEME __id).
- **`is_current` (2026-08):** rewritten from `valid_from<=current_date<=valid_to` to latest-edition flag — `ROW_NUMBER() OVER (PARTITION BY source, factor_name ORDER BY valid_from DESC, valid_to DESC)=1`. No longer date-window based; = "most recent published edition". `dbt build` green + idempotent.

## Last decisions
- Transformation uses DuckDB + dbt-core (chosen over only-Lambda); S3 read via `httpfs`/`parquet` extensions.
- Per-source staging -> intermediate -> marts (medallion) graph.
- Validated via Pydantic at ingestion edge; dbt tests enforce uniqueness + temporal validity (`valid_from_before_valid_to_*`, `unique_stg_*_id`).
- `ademe_translations` seed keyed by `(federation, factor_name_fr)`; intermediate joins on both (NULL federation = any). Import for `lambda_handler` aligned to `ingestion.parsers`.

## Flagged (not yet fixed)
- None — previous ADEME fan-out and import-mismatch flags resolved this session (see resolve notes in `progress.md`). `dbt build` green (88/88) on first run and on re-run (idempotent).

## Next actions (proposed)
- Wire RDS Gold load (DuckDB `dim_emission_factors` -> Postgres).
- Run full `dbt build` on a clean checkout to confirm no stale-target influence on idempotency.

## Open questions
- Gold export target: DuckDB table -> COPY, or direct to RDS Postgres?
- Confirm EC at serving: single snapshot table or SCD over time?