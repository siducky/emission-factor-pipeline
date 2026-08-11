# Active Context: Emission Factor Pipeline

## Current focus
RDS Gold serving layer wired + committed. `marts.dim_emission_factors` live on RDS (1,960 rows). Next: get CI end-to-end (secrets + RDS reachability).

## Current state (from git)
- Branch: `create-rds`; HEAD `a527ad0 add rds gold layer` (RDS work committed).
- Transformation pipeline: staging views -> intermediate views -> `dim_emission_factors` table in DuckDB (`dev.duckdb`).
- `transformation/load_gold_to_rds.py`: loads DuckDB `dim_emission_factors` -> Postgres `marts.dim_emission_factors`; full refresh in one transaction (DELETE + INSERT), PK `ef_id`; asserts duckdb==postgres row count. Env: `DB_HOST/DB_PORT(5432)/DB_NAME/DB_USER/DB_PASSWORD`, `DUCKDB_PATH` (default `transformation/normalise_emission_factors/dev.duckdb`).
- Code review applied to loader (2026-08-11): explicit `_COLUMNS` list in INSERT (no more `SELECT *` positional drift), `_quote_conninfo` escapes backslashes before quotes (libpq `\\`), `_redact()` scrubs DB password from ATTACH/load error logs, `_verify` guards `fetchone()` None. Verified: py_compile + unit asserts (quote/redact/15-column alignment) pass.
- `profiles.yml` reverted: `dev` + `prod` targets are DuckDB again (the postgres `prod` target was a dead end - staging reads S3 parquet via DuckDB external tables, Postgres cannot).
- `dbt-postgres` removed from `pyproject.toml` (loader needs no dbt adapter).
- `.github/workflows/etl_pipeline.yml` rebuilt into a valid workflow: dbt build (dev target) -> `load_gold_to_rds.py` with `secrets.DB_*`.
- `dev.duckdb` untracked + gitignored (`*.duckdb`).
- Verified against real RDS: 1,960 rows / 1,960 unique `ef_id`; `valid_to='infinity'` (ADEME) maps correctly; first-5 rows match DuckDB exactly; re-run idempotent (still 1,960).
- `imt_defra_cleaned.sql` WTT/Motorbike naming tweaks committed in `a527ad0` (no longer uncommitted WIP).
- Cleanup (2026-08-11): stray `q` (psql `\d` dump) + `,` (0-byte) artifacts removed from repo + gitignored.

## Last decisions
- Gold export target: **DuckDB table -> RDS via DuckDB `postgres` extension ATTACH** (chosen over COPY-to-file; a dbt-postgres profile run is impossible end-to-end because staging reads S3 parquet via `httpfs`).
- Serving model: **single snapshot table** `marts.dim_emission_factors` + `is_current` flag (no SCD over time). Defer SCD until serving needs history.
- Test: loader ran directly against the real RDS using existing `DB_*` env vars (no local Postgres install; no `.env.example` changes).

## Flagged (not yet fixed)
- **CI -> RDS reachability (OPEN):** GitHub `ubuntu-latest` runner may not reach a private-VPC RDS; needs security-group allow / public access / bastion for GitHub egress.
- **`DB_*` secrets (OPEN):** workflow reads `secrets.DB_*` from GitHub Actions secrets. Local `.env` alone does NOT reach CI - must add `DB_HOST/DB_PORT/DB_NAME/DB_USER/DB_PASSWORD` to repo secrets (plus `AWS_*` already referenced).

## Next actions (proposed)
- Add `DB_*` (and `AWS_*`) to GitHub repo secrets.
- Confirm RDS reachable from GitHub runner (public access or security-group allow); trigger workflow_dispatch to verify end-to-end.
- Optional: full `dbt build` on a clean checkout (idempotency confirmation after DEFRA tweaks).

## Open questions
- (resolved) Gold export target - DuckDB-attach loader.
- (resolved) Serving EC model - single snapshot table; revisit SCD if downstream needs history.
- CI reachability of RDS (VPC/security-group) - unconfirmed.