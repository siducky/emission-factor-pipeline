# Project Brief: Emission Factor Pipeline

## Mission
Build a reliable, idempotent ETL pipeline that ingests greenhouse-gas (GHG) **emission factors (EFs)** from multiple public sources and delivers a normalised, queryable dataset for downstream carbon accounting.

## Problem
Emission factors come from heterogeneous sources (different schemas, units, languages, time validity, geographic scope). Consumers need one consistent, validated, trustworthy view — with correct temporal and geographic constraints — not per-source raw files.

## Goals (what "done" means)
- Ingest EFs from ADEME, DEFRA, NVE into an S3 Bronze layer.
- Normalise all sources to a single schema via dbt on DuckDB (Silver/Gold).
- Serve the normalised dataset to Amazon RDS PostgreSQL.
- Fully idempotent end-to-end (safe to re-run, no duplicates).
- Every EF carries `valid_from` / `valid_to`; always checked before use.
- Every location maps to ISO 3166-1/2; fallback order Sub-national -> National -> Global.

## Non-goals (deferred/out-of-scope)
- No UI/dashboard in scope.
- No per-EF provider API beyond the three current sources.
- No realtime/low-latency serving requirement (batch only).

## Source of truth
`.clinerules/project_rules.md` holds the authoritative stack and engineering rules. This memory bank is the working record layered on top.