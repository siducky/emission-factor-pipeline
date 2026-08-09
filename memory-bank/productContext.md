# Product Context: Emission Factor Pipeline

## Why this exists
Raw EFs from ADEME (FR), DEFRA (UK), NVE (NO) each have their own format, units, language, year-banding and uncertainty. Anyone doing carbon accounting must normally hand-stitch these together. This pipeline automates that, producing a single clean, validated, versioned view.

## How it works for the user
1. **Ingest** — parsers pull each source and validate every row (Pydantic models) before anything is written.
2. **N.B. broken intermediate design** — see progress.md; the loader today imports `parsers` as a top-level package, while the install uses `ingestion.parsers`. (Flagging, not fixing here.)
3. **Normalise** — dbt maps every source onto the shared `stg_*` -> `imt_*` -> marts schema.
4. **Serve** — normalised data lands in DuckDB locally and RDS (Gold) in prod.

## User value
- One consistent schema across FR/UK/NO factors.
- Trust: rows that fail validation never enter the pipeline (EAFP-style, fail loud).
- Correctness: temporal + ISO-geo constraints enforced at every layer.
- Re-runnable: re-running a stage never duplicates data.

## Pain points being solved
- Manual schema reconciliation across providers.
- Inconsistent units / GHG reporting basis (CO2e vs CO2, per-kWh vs per-tonne).
- Stale or out-of-window factors accidentally being used.

## Reporting / connect to speed
- Not packaging a user product yet; focus is data correctness and pipeline hardening.