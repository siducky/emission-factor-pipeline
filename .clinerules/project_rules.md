# Project Context: Emission Factor ETL Pipeline

## Tech Stack & Environment
- **Orchestration:** GitHub Actions (`.github/workflows/etl_pipeline.yml`)
- **Ingestion:** Python + AWS Lambda (`ingestion/lambda_handler.py`) -> AWS S3 (Bronze Layer)
- **Transformation:** dbt-core + DuckDB (`transformation/`)
- **Serving:** AWS RDS PostgreSQL (Gold Layer)
- **Development:** VS Code Dev Containers (`.devcontainer/`)

## Core Engineering Rules
1. **Idempotency:** All dbt models and Python scripts must be fully idempotent (safe to re-run without duplicating data).
2. **Temporal Constraints:** Every emission factor must include `valid_from` and `valid_to` fields. Never use an EF without checking its date validity.
3. **Geographical Constraints:** All locations must map to ISO 3166-1/2 codes. Fallbacks must follow: Sub-national -> National -> Global.
4. **Token Efficiency:** When modifying code, only read the specific files requested. Do not recursively scan large data directories.

# Coding Style
- Functions: snake_case
- Files: kebab-case
- Prefer const over let
