# Active Context: Emission Factor Pipeline

## Current focus
Initialising the memory bank. Active work is the dbt transformation layer on branch `transformation_imt`.

## Current state (from git)
- Branch: `transformation_imt`, clean working tree.
- Recent commits: `staging models` (d644d71) -> `add intermediate models` (25db322).
- dbt models present: staging (stg_ademe/stg_defra/stg_nve + schema) and intermediate (imt_*_cleaned, imt_all_sources). Marts `table` layer referenced in dbt_project.yml.

## Last decisions
- Transformation uses DuckDB + dbt-core (chosen over only-Lambda); S3 read via `httpfs`/`parquet` extensions.
- Per-source staging -> intermediate -> marts (medallion) graph.
- Validated via Pydantic at ingestion edge; dbt tests enforce uniqueness + temporal validity (`valid_from_before_valid_to_*`, `unique_stg_*_id`).

## Flagged (not yet fixed)
- **Import mismatch:** `ingestion/lambda_handler.py` imports `from parsers import ...` while pyproject install finds `ingestion*`. On `python -m ingestion.lambda_handler` this works; standalone in a packaged env it may ImportError. Confirm before next deploy.
- **Empty `memory-bank/`** now seeded. Next session: continue marts + Gold output.

## Next actions (proposed)
- Verify/bundle `parsers` imports with `ingestion.parsers` package path.
- Build marts models (Gold) over `imt_all_sources`; wire RDS load.
- Run `dbt test` on new models; confirm idempotency re-run.

## Open questions
- Gold export target: DuckDB table -> COPY, or direct to RDS Postgres?
- Confirm EC at serving: single snapshot table or SCD over time?