# TODO — Code Review Findings (2026-08-11)

## Critical Issues

- [ ] **Fix hardcoded years in parsers**
  - `ademe_parser.py:41` hardcodes `{"2016": filtered}`
  - `defra_parser.py:126` computes year but no parameter override
  - Cannot backfill or test with fixture years
  - Change: accept `year` parameter in all parsers, fall back to source default

- [ ] **Move DEFRA business logic from SQL to seed table**
  - `imt_defra_cleaned.sql:38-60` has 22-line CASE with hardcoded sub_category strings
  - Hidden mapping, brittle to source schema changes
  - Change: create `defra_factor_name_mapping.csv` seed and join in SQL

- [ ] **Keep `uncertainty_pct` NULL instead of coercing to 0**
  - `dim_emission_factors.sql:22` uses `coalesce(uncertainty_pct, 0)`
  - Misleads consumers: can't distinguish "known zero" from "no data"
  - Change: remove coalesce, keep NULL for missing uncertainty

## Limitations

- [ ] **Add data freshness validation**
  - Pipeline has no check that source data is actually new
  - Could succeed indefinitely with stale data
  - Change: store last-known `Last-Modified` header per source; skip ingest if unchanged

- [ ] **Standardise error handling across parsers**
  - `defra_parser` drops invalid rows silently
  - `ademe_parser` and `nve_parser` raise ValueError on any invalid row
  - Inconsistent contract for downstream consumers
  - Change: document and align strictness per source

- [ ] **Add retry with backoff to HTTP calls**
  - Single `requests.get()` in each parser
  - Transient failures (502/503/timeout) fail entire ingestion
  - Change: use `tenacity` or `requests.adapters.HTTPAdapter` with retry strategy

- [ ] **Add parser unit tests**
  - No tests for `ademe_parser`, `defra_parser`, or `nve_parser`
  - Change: fixture CSV/Excel files + one smoke test per parser

## Design Concerns

- [ ] **Review `is_current` semantics for overlapping validity periods**
  - `dim_emission_factors.sql:33-36` picks latest edition per `(source, factor_name, unit)`
  - If two editions have overlapping `valid_from`/`valid_to`, `is_current=true` may select an expired factor
  - Change: document edge case; consider `is_current` = `valid_from <= today AND valid_to >= today`

- [ ] **Add schema evolution strategy**
  - Adding a Gold column requires changes in staging SQL, intermediate SQL, loader `_COLUMNS`, loader DDL, and `stg_schema.yml`
  - No versioned schema contract
  - Change: maintain `SCHEMA_CONTRACT.md` with column list, types, and nullability

- [ ] **Add CI pre-flight check for RDS reachability**
  - GitHub runner may be in egress-restricted environment
  - Workflow currently runs dbt build before failing on RDS ATTACH
  - Change: add `nc -z $DB_HOST 5432` step early in workflow with clear skip/fail message

- [ ] **NVE parser sheet-name validation**
  - `nve_parser.py:81-87` skips unknown sheets at debug level
  - Could silently produce zero rows if source renames sheets
  - Change: assert expected sheets exist after `pd.read_excel`

- [ ] **DuckDB postgres extension external dependency risk**
  - `load_gold_to_rds.py:159-160` installs from `extensions.duckdb.org`
  - No fallback if domain unreachable or extension breaks
  - Change: cache extension in repo or add COPY-to-file fallback path