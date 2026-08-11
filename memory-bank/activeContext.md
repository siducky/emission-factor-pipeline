# Active Context: Emission Factor Pipeline

## Current focus
RDS Gold serving layer wired: DuckDB Gold -> RDS Postgres via `transformation/load_gold_to_rds.py` (DuckDB `postgres` extension ATTACH). `marts.dim_emission_factors` live on RDS (1,960 rows).

## Current state (from git)
- Branch: `create-rds` (dirty - RDS work uncommitted).
- Transformation pipeline unchanged: staging views -> intermediate views -> `dim_emission_factors` table in DuckDB (`dev.duckdb`).
- NEW `transformation/load_gold_to_rds.py`: loads DuckDB `dim_emission_factors` -> Postgres `marts.dim_emission_factors`; full refresh in one transaction (DELETE + INSERT), PK `ef_id`; asserts duckdb==postgres row count. Env: `DB_HOST/DB_PORT(5432)/DB_NAME/DB_USER/DB_PASSWORD`, `DUCKDB_PATH` (default `transformation/normalise_emission_factors/dev.duckdb`).
- Code review applied to loader (2026-08-11): explicit `_COLUMNS` list in INSERT (no more `SELECT *` positional drift), `_quote_conninfo` escapes backslashes before quotes (libpq `\\`), `_redact()` scrubs DB password from ATTACH/load error logs, `_verify` guards `fetchone()` None. Verified: py_compile + unit asserts (quote/redact/15-column alignment) pass.
- `profiles.yml` reverted: `dev` + `prod` targets are DuckDB again (the postgres `prod` target was a dead end - staging reads S3 parquet via DuckDB external tables, Postgres cannot).
- `dbt-postgres` removed from `pyproject.toml` (loader needs no dbt adapter).
- `.github/workflows/etl_pipeline.yml` rebuilt into a valid workflow: dbt build (dev target) -> `load_gold_to_rds.py` with `secrets.DB_*`. (Previously an invalid 5-line fragment.)
- `dev.duckdb` untracked + gitignored (`*.duckdb`).
- Verified against real RDS: 1,960 rows / 1,960 unique `ef_id`; `valid_to='infinity'` (ADEME) maps correctly; first-5 rows match DuckDB exactly; re-run idempotent (still 1,960).

## Last decisions
- Gold export target: **DuckDB table -> RDS via DuckDB `postgres` extension ATTACH** (chosen over COPY-to-file; a dbt-postgres profile run is impossible end-to-end because staging reads S3 parquet via `httpfs`).
- Serving model: **single snapshot table** `marts.dim_emission_factors` + `is_current` flag (no SCD over time). Defer SCD until serving needs history.
- Test: loader ran directly against the real RDS using existing `DB_*` env vars (no local Postgres install; no `.env.example` changes).

## Flagged (not yet fixed)
- CI runner -> RDS reachability unconfirmed (RDS may be in a private VPC; may need security-group allow / bastion for GitHub `ubuntu-latest` egress).
- `imt_defra_cleaned.sql` has uncommitted WIP naming tweaks (Motorbike / WTT-*) - unrelated to RDS; re-run `dbt build` + reload before trusting row content downstream.

## Next actions (proposed)
- Optional: full `dbt build` on a clean checkout (idempotency confirmation).
- Commit RDS work; add `DB_*` to repo secrets for CI.

## Open questions
- (resolved) Gold export target - DuckDB-attach loader.
- (resolved) Serving EC model - single snapshot table; revisit SCD if downstream needs history.
- CI reachability of RDS (VPC/security-group) - unconfirmed.
