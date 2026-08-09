# Tech Context: Emission Factor Pipeline

## Stack
- **Orchestration:** GitHub Actions `.github/workflows/etl_pipeline.yml`
- **Ingestion:** Python 3.11+ AWS Lambda -> S3 (Bronze). Runner entry: `ingestion/lambda_handler.py`.
- **Transformation:** dbt-core + DuckDB. Local db: `dev.duckdb`; prod: `normalise_emission_factors.duckdb`.
- **Serving:** Amazon RDS PostgreSQL (Gold).
- **Dev:** VS Code Dev Containers (`.devcontainer/`); `.aws` + `.ssh` bind-mounted.

## Languages / tooling
- Python `>=3.11` (`.python-version`, ruff target `py311`)
- Manager: `uv` (uv.lock)
- Lint: ruff, line-length 88, select `E4,E7,E9,F,I` (basic + isort)

## Key dependencies (pyproject)
- runtime: `boto3`, `dbt-core`, `dbt-duckdb`, `duckdb`, `numpy`, `openpyxl`, `pandas`, `pydantic`, `requests`
- dev: `pytest`, `ruff`
- dbt package: `dbt_utils` (vendored)

## Data sources
- **ADEME** Base Carbone (FR) — CSV, French columns, `CodeFede`, uncertainty %
- **DEFRA** GHG conversion factors (UK) — flat-format Excel, header row 5, Level 1-4 categories
- **NVE** electricity grid EFs (NO) — CO2/kWh by year + factor_type
- Locale seeds: `ademe_translations`, `defra_category_mapping`, `defra_overrides`, `defra_sub_category_mapping`

## Profiles
`transformation/normalise_emission_factors/profiles.yml` — profile `transform`; targets `dev` (dev.duckdb) and `prod`; DuckDB extensions `httpfs`, `parquet`; S3 creds from env `AWS_ACCESS_KEY_ID` / `AWS_SECRET_ACCESS_KEY`, region `eu-north-1`.

## Env vars
- `S3_BUCKET` (required by Lambda)
- `ADEME_URL` (set per source parser; raises if missing)
- `AWS_REGION` / `AWS_ACCESS_KEY_ID` / `AWS_SECRET_ACCESS_KEY`

## Dev session
- Branch: `transformation_imt`; working tree clean at init.
- Package name `emission-factor-pipeline`; setuptools finds `ingestion*` (but loader uses top-level `parsers` — potential mismatch, see progress.md).