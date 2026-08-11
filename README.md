# Emission Factor Pipeline

Ingest, normalise and serve greenhouse-gas (GHG) **emission factors** from multiple public sources into one consistent, validated, queryable dataset.

Raw emission factors from [ADEME](https://www.bilans-ges.ademe.fr/) (France), [DEFRA](https://www.gov.uk/government/collections/government-conversion-factors-for-company-reporting) (UK) and [NVE](https://www.nve.no/) (Norway) each arrive in different schemas, units, languages and time validities. This pipeline stitches them together into a single normalised view — with correct temporal and geographic constraints — ready for downstream carbon accounting.

## Architecture

```
ADEME ─┐
DEFRA ─┼─> AWS Lambda (Python) ─> S3 bronze/ ─> dbt + DuckDB ─> marts.dim_emission_factors ─> RDS PostgreSQL (Gold)
NVE ───┘        (ingest + validate)   (raw)      (staging -> intermediate -> marts)
```

Medallion layering:

| Layer | Where | What |
|-------|-------|------|
| **Bronze** | S3 (`bronze/<source>/<year>/factors.csv`) | Raw, validated rows per source |
| **Silver** | DuckDB views | `stg_*` staging → `imt_*` intermediate cleaning + union |
| **Gold** | DuckDB table + RDS PostgreSQL | `marts.dim_emission_factors` — normalised, deduplicated, queryable |

## Quick Start

```bash
# 1. Install dependencies (Python >= 3.11, uv)
uv sync

# 2. Configure environment
cp .env.example .env
#   ... set S3_BUCKET, AWS_* credentials, DB_* vars

# 3. Transform bronze -> Gold (DuckDB)
cd transformation/normalise_emission_factors
dbt deps
dbt build --target dev

# 4. Load Gold into RDS PostgreSQL
cd ../..
python transformation/load_gold_to_rds.py
```

## Data Sources

| Source | Country | Format | Notes |
|--------|---------|--------|-------|
| [ADEME Base Carbone](https://www.bilans-ges.ademe.fr/) | FR | CSV | French column names, `CodeFede` categories, uncertainty % |
| [DEFRA GHG conversion factors](https://www.gov.uk/government/collections/government-conversion-factors-for-company-reporting) | UK | Excel (flat format) | Header on row 5, Level 1–4 categories, per-scope factors |
| [NVE electricity grid factors](https://www.nve.no/) | NO | Excel | CO₂/kWh by year + `factor_type` |

Locale seeds (`transformation/normalise_emission_factors/seeds/`) handle ADEME French→English translations, DEFRA category/sub-category mapping and overrides.

## Repository Structure

```
.
├── ingestion/
│   ├── lambda_handler.py          # AWS Lambda entry point + parser registry
│   ├── logging_config.py          # Logging setup for local runs
│   └── parsers/
│       ├── ademe_parser.py        # ADEME fetch + filter + validate
│       ├── defra_parser.py        # DEFRA fetch + filter + validate
│       ├── nve_parser.py          # NVE fetch + filter + validate
│       └── models.py              # Pydantic row validation models
├── transformation/
│   ├── load_gold_to_rds.py        # DuckDB -> RDS PostgreSQL Gold loader
│   └── normalise_emission_factors/  # dbt project (profile: transform)
│       ├── dbt_project.yml
│       ├── profiles.yml           # dev/prod DuckDB targets (httpfs + parquet)
│       ├── models/
│       │   ├── staging/           # stg_ademe, stg_defra, stg_nve (views)
│       │   ├── intermediate/      # imt_*_cleaned, imt_all_sources (views)
│       │   └── marts/             # dim_emission_factors (table, Gold)
│       └── seeds/                 # translations, mappings, overrides
├── .github/workflows/etl_pipeline.yml  # CI: dbt build + RDS load
├── memory-bank/                   # Development notes / project memory
├── .env.example
├── pyproject.toml                 # uv-managed, Python >= 3.11
└── LICENSE
```

## Prerequisites

- Python **>= 3.11** and [uv](https://docs.astral.sh/uv/)
- AWS account with an S3 bucket (Bronze layer) and credentials
- Amazon RDS PostgreSQL instance (Gold serving)
- GitHub repository secrets for CI (see [CI Pipeline](#ci-pipeline))

## Usage

### 1. Ingestion (Bronze → S3)

The ingestion step runs as an **AWS Lambda** function. It reads the `S3_BUCKET` environment variable, runs each registered parser, validates every row with Pydantic, and writes `bronze/<source>/<year>/factors.csv` to S3.

Run locally:

```bash
python -m ingestion.lambda_handler
```

Deploy `ingestion/lambda_handler.py` as a Lambda function with the `S3_BUCKET` env var set. The event payload can select sources:

```json
{ "sources": ["ademe", "defra", "nve"] }
```

### 2. Transformation (Silver → Gold, DuckDB)

```bash
cd transformation/normalise_emission_factors
dbt deps
dbt build --target dev
```

The dbt project (`profile: transform`) materialises:

- **Staging** (`stg_ademe`, `stg_defra`, `stg_nve`) — views reading raw bronze data from S3 via the DuckDB `httpfs` extension.
- **Intermediate** (`imt_ademe_cleaned`, `imt_defra_cleaned`, `imt_nve_cleaned`, `imt_all_sources`) — cleaning, translation and cross-source union.
- **Marts** (`dim_emission_factors`) — the Gold table with stable surrogate keys, temporal flags and ISO country codes.

### 3. Serving (Gold → RDS PostgreSQL)

```bash
python transformation/load_gold_to_rds.py
```

Loads `marts.dim_emission_factors` from DuckDB into RDS PostgreSQL using the DuckDB `postgres` extension (no extra Python driver). The load is a **full refresh inside one transaction** (DELETE + INSERT) and verifies the row count matches DuckDB before committing.

Required env vars: `DB_HOST`, `DB_NAME`, `DB_USER`, `DB_PASSWORD` (optional `DB_PORT`, default `5432`; optional `DUCKDB_PATH`, default `transformation/normalise_emission_factors/dev.duckdb`).

## CI Pipeline

[`.github/workflows/etl_pipeline.yml`](.github/workflows/etl_pipeline.yml) runs on push to `main` or manual `workflow_dispatch`:

1. Checkout + set up Python 3.11 and uv
2. Install dependencies (`uv pip install --system .`)
3. Configure AWS credentials (for dbt to read bronze from S3)
4. `dbt deps` + `dbt build --target dev`
5. `python transformation/load_gold_to_rds.py` with `DB_*` secrets

Ingestion runs as an independent AWS Lambda and is **not** part of this workflow.

Required GitHub secrets: `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `AWS_REGION`, `DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_USER`, `DB_PASSWORD`.

## Engineering Invariants

- **Idempotency** — every stage is safe to re-run; no duplicate rows. Gold keys are deterministic (md5 over source + identifier + year).
- **Temporal constraints** — every emission factor carries `valid_from` / `valid_to`; the `is_current` flag marks the latest published edition per `(source, factor_name, unit)`. Always check date validity before use.
- **Geographic constraints** — all locations map to ISO 3166-1/2 codes, with fallback order Sub-national → National → Global.
- **Validate-then-write** — Pydantic models reject invalid rows (non-empty fields, non-negative factors, year bounds) before anything reaches S3.

## Output Schema — `marts.dim_emission_factors`

| Column | Type | Notes |
|--------|------|-------|
| `ef_id` | `VARCHAR(32)` | Primary key, deterministic surrogate |
| `factor_name` | `VARCHAR` | Normalised factor name |
| `description` | `VARCHAR` | Optional description |
| `gCO2e_per_unit` | `DOUBLE PRECISION` | Emission factor in g CO₂e per unit |
| `unit` | `VARCHAR` | Unit of the factor |
| `source` | `VARCHAR(16)` | `ademe` / `defra` / `nve` |
| `ghg_scope` | `VARCHAR` | Reporting scope |
| `category` | `VARCHAR` | High-level category |
| `sub_category` | `VARCHAR` | Sub-category |
| `country_code` | `VARCHAR` | ISO 3166-1/2 code |
| `source_year` | `INTEGER` | Year of the source data |
| `valid_from` | `DATE` | Start of validity |
| `valid_to` | `DATE` | End of validity |
| `is_current` | `BOOLEAN` | Latest published edition flag |
| `uncertainty_pct` | `DOUBLE PRECISION` | Optional uncertainty (%) |

## Environment Variables

| Variable | Required | Purpose |
|----------|----------|---------|
| `S3_BUCKET` | Ingestion | Bronze S3 bucket name |
| `AWS_ACCESS_KEY_ID` / `AWS_SECRET_ACCESS_KEY` | dbt / CI | S3 read access for DuckDB `httpfs` |
| `AWS_REGION` | CI | AWS region (default `eu-north-1` in profiles) |
| `ADEME_URL` | ADEME parser | Base Carbone data URL |
| `DB_HOST` / `DB_NAME` / `DB_USER` / `DB_PASSWORD` | RDS load | RDS PostgreSQL connection |
| `DB_PORT` | RDS load (optional) | Default `5432` |
| `DUCKDB_PATH` | RDS load (optional) | Path to DuckDB file, default `transformation/normalise_emission_factors/dev.duckdb` |

## Known Limitations

- **Batch only** — no realtime/low-latency serving requirement.
- **Fixed sources** — ADEME, DEFRA and NVE only; no per-EF provider API beyond these.
- **No UI** — this is a data pipeline, not a dashboard.
- **CI → RDS reachability** — GitHub runners may need VPC/security-group configuration to reach a private RDS instance.

## License

See [LICENSE](LICENSE).