# Progress: Emission Factor Pipeline

## What works
- **Ingestion:** Lambda handler with parser registry (ademe/nve/defra); writes `bronze/<source>/<year>/factors.csv` to S3. Pydantic validation models for all three sources.
- **Transformation (dbt + DuckDB):**
  - Staging: `stg_ademe`, `stg_defra`, `stg_nve` (views) + `sources.yml`, `stg_schema.yml` (uniqueness + temporal tests).
  - Intermediate: `imt_ademe_cleaned`, `imt_defra_cleaned`, `imt_nve_cleaned`, `imt_all_sources` (views).
  - Seeds for translations/mapping/overrides.
  - Dev db runs against local `dev.duckdb`.

## In progress
- Marts (Gold) tables over `imt_all_sources` — declared in `dbt_project.yml` (`marts: +materialized: table`) but not yet built.
- RDS Postgres load path.

## Blocked / risks
- **Import packaging risk:** `lambda_handler.py` imports top-level `parsers`; pyproject `[tool.setuptools.packages.find] include=["ingestion*"]`. Possible ImportError in packaged Lambda. Unconfirmed.
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