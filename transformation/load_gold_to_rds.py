"""Push the Gold-layer `dim_emission_factors` table from DuckDB to RDS Postgres.

Serving step of the medallion pipeline:
  1. dbt materialises Gold into DuckDB (`dev.duckdb`) -- see dbt_project.yml.
  2. This script replicates that table into `marts.dim_emission_factors` on
     RDS Postgres, using the DuckDB `postgres` extension (ATTACH). No extra
     Python driver is required.

Idempotency: full refresh inside one DuckDB transaction (DELETE all rows, then
INSERT a copy of the DuckDB table). Re-running always lands on the same state.

Environment: DB_HOST, DB_PORT (default 5432), DB_NAME, DB_USER, DB_PASSWORD,
DUCKDB_PATH (default transformation/normalise_emission_factors/dev.duckdb).
"""

from __future__ import annotations

import logging
import os
from pathlib import Path

import duckdb

LOGGER = logging.getLogger("load_gold_to_rds")

DEFAULT_DUCKDB_PATH = Path("transformation") / \
    "normalise_emission_factors" / "dev.duckdb"
GOLD_TABLE = "dim_emission_factors"
TARGET_SCHEMA = "marts"
RDS_ALIAS = "rds"  # DuckDB catalog alias for the ATTACHed Postgres database

_COLUMNS = (
    "ef_id",
    "factor_name",
    "description",
    "gCO2e_per_unit",
    "unit",
    "source",
    "ghg_scope",
    "category",
    "sub_category",
    "country_code",
    "source_year",
    "valid_from",
    "valid_to",
    "is_current",
    "uncertainty_pct",
)

_DDL = """
CREATE TABLE IF NOT EXISTS {schema}.{table} (
    ef_id           VARCHAR(32) PRIMARY KEY,
    factor_name     VARCHAR     NOT NULL,
    description     VARCHAR,
    gCO2e_per_unit  DOUBLE PRECISION NOT NULL,
    unit            VARCHAR     NOT NULL,
    source          VARCHAR(16) NOT NULL,
    ghg_scope       VARCHAR     NOT NULL,
    category        VARCHAR,
    sub_category    VARCHAR,
    country_code    VARCHAR     NOT NULL,
    source_year     INTEGER     NOT NULL,
    valid_from      DATE        NOT NULL,
    valid_to        DATE        NOT NULL,
    is_current      BOOLEAN     NOT NULL,
    uncertainty_pct DOUBLE PRECISION
)
"""


def _require_env(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise SystemExit(
            f"[load_gold_to_rds] missing required env var: {name}")
    return value


def _quote_conninfo(value: str) -> str:
    """Quote a libpq key=value token so passwords with spaces/quotes survive."""
    if any(c in value for c in " '\""):
        # Escape backslashes first: libpq treats \\ as an escaped backslash,
        # so a trailing backslash would otherwise swallow the closing quote.
        return "'" + value.replace("\\", "\\\\").replace("'", "\\'") + "'"
    return value


def _redact(message: str, secret: str) -> str:
    """Replace the DB password in an error message before logging."""
    return message.replace(secret, "****")


def _connect_string() -> str:
    parts = {
        "host": _require_env("DB_HOST"),
        "port": os.getenv("DB_PORT") or "5432",
        "dbname": _require_env("DB_NAME"),
        "user": _require_env("DB_USER"),
        "password": _require_env("DB_PASSWORD"),
    }
    return " ".join(f"{key}={_quote_conninfo(value)}" for key, value in parts.items())


def _load(con: duckdb.DuckDBPyConnection) -> None:
    con.execute(f"CREATE SCHEMA IF NOT EXISTS {RDS_ALIAS}.{TARGET_SCHEMA}")
    con.execute(_DDL.format(
        schema=f"{RDS_ALIAS}.{TARGET_SCHEMA}", table=GOLD_TABLE))

    # ponytail: full-refresh is fine for a small snapshot dim. If the remote
    # writes split across Postgres transactions, a crash between DELETE and
    # INSERT leaves an empty table -- the re-run heals it. Upgrade path: stage
    # into a temp table + RENAME swap if serving ever needs zero-downtime.
    con.execute("BEGIN")
    try:
        con.execute(f"DELETE FROM {RDS_ALIAS}.{TARGET_SCHEMA}.{GOLD_TABLE}")
        columns = ", ".join(_COLUMNS)
        con.execute(
            f"INSERT INTO {RDS_ALIAS}.{TARGET_SCHEMA}.{GOLD_TABLE} ({columns}) "
            f"SELECT {columns} FROM {GOLD_TABLE}"
        )
    except Exception:
        try:
            con.execute("ROLLBACK")
        except Exception:
            pass  # keep the original error
        raise
    con.execute("COMMIT")


def _verify(con: duckdb.DuckDBPyConnection) -> int:
    src_row = con.execute(f"SELECT count(*) FROM {GOLD_TABLE}").fetchone()
    dst_row = con.execute(
        f"SELECT count(*) FROM {RDS_ALIAS}.{TARGET_SCHEMA}.{GOLD_TABLE}"
    ).fetchone()
    if src_row is None or dst_row is None:
        raise RuntimeError(
            "[load_gold_to_rds] verification failed: count query returned no row")
    src, dst = src_row[0], dst_row[0]
    if src != dst:
        raise RuntimeError(
            f"[load_gold_to_rds] verification failed: "
            f"duckdb={src} rows, postgres={dst} rows"
        )
    return dst


def main() -> None:
    logging.basicConfig(level=logging.INFO,
                        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
                        datefmt="%Y-%m-%d %H:%M:%S",
                        )
    duckdb_path = Path(os.getenv("DUCKDB_PATH", str(DEFAULT_DUCKDB_PATH)))
    if not duckdb_path.is_file():
        raise SystemExit(
            f"[load_gold_to_rds] DuckDB file not found: {duckdb_path}")

    con = duckdb.connect(str(duckdb_path))
    try:
        con.execute("INSTALL postgres")
        con.execute("LOAD postgres")
        try:
            con.execute(
                f"ATTACH '{_connect_string()}' AS {RDS_ALIAS} (TYPE postgres)")
            _load(con)
        except Exception as exc:
            # DuckDB ATTACH errors can echo the conninfo; scrub the password
            # before it lands in CI logs.
            LOGGER.error(
                "RDS load failed: %s",
                _redact(str(exc), _require_env("DB_PASSWORD")),
            )
            raise
        rows = _verify(con)
        LOGGER.info(
            "Loaded %s rows into %s.%s from %s",
            rows, TARGET_SCHEMA, GOLD_TABLE, duckdb_path,
        )
    finally:
        con.close()


if __name__ == "__main__":
    main()
