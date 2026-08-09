# Progress: Emission Factor Pipeline

## What works
- **Ingestion:** Lambda handler with parser registry (ademe/nve/defra); writes `bronze/<source>/<year>/factors.csv` to S3. Pydantic validation models for all three sources.
- **Transformation (dbt + DuckDB):**
  - Staging: `stg_ademe`, `stg_defra`, `stg_nve` (views) + `sources.yml`, `stg_schema.yml` (uniqueness + temporal tests).
  - Intermediate: `imt_ademe_cleaned`, `imt_defra_cleaned`, `imt_nve_cleaned`, `imt_all_sources` (views).
  - Seeds for translations/mapping/overrides.
  - Dev db runs against local `dev.duckdb`.
  - **Marts (Gold):** `dim_emission_factors` (table) built + validated. 22/22 data tests pass (`marts_schema.yml`): `ef_id unique/not_null`, temporal `valid_from<=valid_to`, accepted values, `is_current`, `country_level`. `gCO2e_per_unit` bound is `>= 0` (DEFRA legitimately reports zero EFs, e.g. BEVs / landfill gas; only negatives rejected). Full `dbt build` green on 1st AND re-run (idempotent).
  - **`is_current` semantics changed (2026-08):** no longer `valid_from<=current_date<=valid_to`; now flags the LATEST published edition per `(source, factor_name)` via `ROW_NUMBER() OVER (PARTITION BY source, factor_name ORDER BY valid_from DESC, valid_to DESC) = 1`. "Usable now" still comes from `valid_from`/`valid_to`; `is_current` = most-recent-edition pointer. Verified: every `(source,factor_name)` group has exactly 1 current; NVE only 2024 flagged; ADEME all current (single static snapshot); `dbt build` green + idempotent (18/18).
  - **Deterministic keys:** replaced `uuid()` in all staging models with source-+identifier-+year hashes (idempotent, cross-source unique). mart `ef_id` = staging `id`. NVE: `factor_type+year`; DEFRA: source `ID`+year; ADEME: `__id`.

## In progress
- RDS Postgres load path (Gold export target undecided).

## Blocked / risks
- **ADEME translation fan-out — FIXED:** seed now keyed by `(federation, factor_name_fr)`; `imt_ademe_cleaned` joins on name + federation (NULL-federation = wildcard). Generic `Ballon→Ball` replaced by federation-specific `Rugby ball`. Mart `ROW_NUMBER` dedupe stopgap removed. Verified 1,960 rows / 1,960 unique `ef_id`; all 12 conflict names resolve to correct English names (1 row each). Guarded by new seed `unique(concat(factor_name_fr,'¦',federation))` test.
- **Import packaging risk — FIXED:** `lambda_handler.py` now `from ingestion.parsers import ...` (matches parser modules + pyproject `include=["ingestion*"]`). Verified `from ingestion.lambda_handler import lambda_handler` imports.
- Gold serving target (DuckDB COPY vs RDS) undecided.

## Environment / build state
- Python `>=3.11`, uv-managed. `dev.duckdb` present in repo root.
- Ruff config: 88 cols, select `E4,E7,E9,F,I`.
- dbt project compiles (target/ run artifacts present in `transformation/normalise_emission_factors/target/`).

## Done (recent commits)
- `add intermediate models` (25db322)
- `staging models` (d644d71)
- `add colored logging` (0d09c54)
- `add transformation` (0482cf7), `add source - ademe` (2cc320f), `dockerfile/default handler`, `.env`/temp-env fixes

## Memory-bank init
- `memory-bank/` seeded with 6 docs (brief, product, patterns, tech, active, progress) on branch `transformation_imt`. Verify field accuracy before heavy reliance.