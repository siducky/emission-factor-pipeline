import io
import logging
import os
from datetime import datetime

import pandas as pd
import requests

from ingestion.parsers.models import DefraRawRow

logger = logging.getLogger(__name__)


def _get_defra_url() -> str:
    """Return DEFRA_URL from environment, or raise if missing."""
    url = os.getenv("DEFRA_URL")
    if not url:
        raise ValueError("DEFRA_URL environment variable is not set")
    return url


def _download_year(year: int, base_url: str) -> pd.DataFrame:
    """Download and parse a single year's DEFRA data."""
    url = f"{base_url}/ghg-conversion-factors-{year}-flat-format.xlsx"
    sheet_name = "Factors by Category"
    logger.info("Downloading DEFRA %d from %s (sheet='%s')",
                year, url, sheet_name)
    try:
        with requests.get(url, timeout=30) as response:
            response.raise_for_status()
            content = response.content
    except requests.RequestException as e:
        raise RuntimeError(
            f"Failed to download DEFRA {year} data from {url}") from e

    try:
        df = pd.read_excel(
            io.BytesIO(content),
            sheet_name=sheet_name,
            index_col=None, header=5)
    except Exception as e:
        raise RuntimeError(f"Failed to parse DEFRA {year} Excel sheet") from e
    df = df.dropna(how="all")
    df.columns = [str(c).strip() for c in df.columns]
    logger.info("Loaded DEFRA %d: %d rows, %d columns", year, *df.shape)
    return df


def _validate_df(df: pd.DataFrame, year: int) -> pd.DataFrame:
    """Validate every row of a DEFRA DataFrame against ``DefraRawRow``.

    Invalid rows are logged and dropped. The returned DataFrame contains
    only rows that passed validation. Never raises — caller gets the
    filtered result regardless.

    ponytail: filtering means data loss if nobody checks the log.
    Upgrade path: emit CloudWatch metric on invalid_count > threshold.
    """
    ghg_col = None
    for col in df.columns:
        if col.startswith("GHG Conversion Factor"):
            ghg_col = col
            break

    if not ghg_col:
        logger.error(
            "No 'GHG Conversion Factor' column in DEFRA %s. Columns: %s",
            year, list(df.columns))
        return df.iloc[:0]  # return empty DataFrame, don't break

    valid_rows: list[dict] = []
    invalid_count = 0
    row_count = 0

    for row_idx, row in df.iterrows():
        row_count += 1
        factor_val = row.get(ghg_col)
        if pd.isna(factor_val) or factor_val == "":
            continue

        record = {
            "ID": row.get("ID", ""),
            "Level 1": row.get("Level 1", ""),
            "Level 2": row.get("Level 2", ""),
            "Level 3": row.get("Level 3", ""),
            "Level 4": row.get("Level 4", ""),
            "Column Text": row.get("Column Text", ""),
            "GHG Conversion Factor": factor_val,
            "UOM": row.get("UOM", ""),
            "Scope": row.get("Scope", ""),
            "GHG/Unit": row.get("GHG/Unit", ""),
            "year": year
        }
        if pd.isna(record["Level 3"]) or record["Level 3"] == "":
            record["Level 3"] = record["Level 2"]
        try:
            DefraRawRow.model_validate(record)
            valid_rows.append(record)
        except Exception as e:
            invalid_count += 1
            if invalid_count <= 20:
                logger.warning("DEFRA %s row %s invalid: %s", year, row_idx, e)

    if invalid_count > 20:
        logger.warning(
            "DEFRA %s: %s more invalid rows (not shown)", year, invalid_count - 20)

    if row_count == 0:
        logger.warning(
            "DEFRA %s DataFrame is empty — no rows to validate", year)
        return pd.DataFrame()

    logger.info(
        "DEFRA %s validated: %d valid, %d invalid, %d skipped (no factor)",
        year, len(valid_rows), invalid_count, row_count - len(valid_rows) - invalid_count)
    return pd.DataFrame(valid_rows)


def parse_file() -> dict[str, bytes]:
    """Download DEFRA GHG conversion factors for the previous calendar year.

    Validates rows, drops invalid ones, returns CSV bytes of clean data.
    Pipeline never breaks from bad rows.
    """
    base_url = _get_defra_url()
    year = datetime.now().year - 1
    df = _download_year(year, base_url)
    df_clean = _validate_df(df, year)
    return {str(year): df_clean.to_csv(index=False).encode("utf-8")}


if __name__ == "__main__":
    from ingestion.logging_config import setup_logging
    setup_logging()
    result = parse_file()
