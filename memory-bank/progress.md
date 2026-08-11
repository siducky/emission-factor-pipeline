# Progress: Emission Factor Pipeline

## What works
- **Ingestion:** Lambda handler with parser registry (ademe/nve/defra); writes `bronze/<source>/<year>/factors.csv` to S3. Pydantic validation models for all three sources.
- **Transformation (dbt + DuckDB):**
  - Staging: `stg_ademe`, `stg_defra`, `stg_nve` (views) + `sources.yml`, `stg_schema.yml` (uniqueness + temporal tests).
  - Intermediate: `imt_ademe_cleaned`, `imt_defra_cleaned`, `imt_nve_cleaned`, `imt_all_sources` (views).
  - Seeds for translations/mapping/overrides.
  - Dev db runs against local `dev.duckdb`.
  - **Marts (Gold):** `dim_emission_factors` (table) built + validated. `ef_id unique/not_null`, temporal `valid_from<=valid_to`, accepted values, `is_current`, `country_level`; `gCO2e_per_unit >= 0` (DEFRA legitimately has zero EFs, e.g. BEVs / landfill gas). `dbt build` green on 1st AND re-run (idempotent).
  - **`is_current` semantics (2026-08):** latest published edition per `(source, factor_name)` via `ROW_NUMBER() ... ORDER BY valid_from DESC, valid_to DESC = 1`. "Usable now" still from `valid_from`/`valid_to`.
  - **Deterministic keys:** md5 over source+identifier+year (idempotent, cross-source unique). mart `ef_id` = staging `id`.
- **Serving (RDS Gold) - NEW (2026-08):**
  - `transformation/load_gold_to_rds.py`: DuckDB `postgres` extension ATTACH -> `marts.dim_emission_factors` on RDS. Full-refresh in one transaction (DELETE + INSERT), PK `ef_id`, asserts source==target row count.
  - Verified on real RDS: 1,960 rows / 1,960 unique `ef_id`; `valid_to='infinity'` maps correctly; sample rows match DuckDB; re-run idempotent.
  - No driver/dependency added (duckdb already a dep; `postgres` ext fetched from `extensions.duckdb.org`, host that already served `httpfs`).

## In progress
- None - RDS Postgres load path wired.

## Blocked / risks
- **ADEME translation fan-out - FIXED:** seed keyed by `(federation, factor_name_fr)`; NULL-federation = wildcard; 1,960 rows / 1,960 unique `ef_id`; guarded by seed uniqueness test.
- **Import packaging risk - FIXED:** `lambda_handler.py` uses `from ingestion.parsers import ...`.
- **CI -> RDS reachability (OPEN):** GitHub `ubuntu-latest` runner may not reach a private-VPC RDS; needs security-group/VPC config.
- **`imt_defra_cleaned.sql` WIP (OPEN):** uncommitted Motorbike/WTT-* factor_name tweaks - re-run `dbt build` + reload before relying on row content.

## Environment / build state
- Python `>=3.11`, uv-managed. `dev.duckdb` in repo (now gitignored `*.duckdb`).
- `dbt-postgres` removed from `pyproject.toml` (unused - loader uses duckdb postgres ext).
- Ruff: 88 cols, select `E4,E7,E9,F,I`. Loader passes ruff + py_compile.
- Local devcontainer: `postgres` DuckDB extension installs+loads fine (network to `extensions.duckdb.org`); libpq present.

## Done (recent commits)
- `add marts model` (8e3b40e)
- `add intermediate models` (25db322), `staging models` (d644d71), `add transformation` (0482cf7), ingestion work (lambda/parsers/ademe)

## Memory-bank init
- `memory-bank/` seeded on branch `transformation_imt`. This session: RDS Gold load wired + verified (branch `create-rds`, uncommitted).
