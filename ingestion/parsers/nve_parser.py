import io
import logging
import os

import pandas as pd
import requests

from ingestion.parsers.models import NveRawRow

logger = logging.getLogger(__name__)


def _get_nve_url() -> str:
    url = os.getenv("NVE_URL")
    if not url:
        raise ValueError("NVE URL environment variable is not set")
    return url


def _find_column(columns: list[str], target: str) -> str | None:
    """Locate a column by case-insensitive, whitespace-stripped header match."""
    try:
        return next(c for c in columns if str(c).strip().lower() == target.lower())
    except StopIteration:
        return None


def _validate_df(df: pd.DataFrame) -> None:
    """Validate every row of an NVE DataFrame against ``NveRawRow``."""
    errors: list[str] = []
    row_count = 0
    for row_idx, row in df.iterrows():
        row_count += 1
        try:
            NveRawRow.model_validate(row.to_dict())
        except Exception as e:
            errors.append(f"Row {row_idx}: {e}")

    if row_count == 0:
        raise ValueError("NVE DataFrame is empty — no rows to validate")

    if errors:
        summary = "\n".join(errors[:20])
        remainder = len(errors) - 20
        if remainder > 0:
            summary += f"\n... and {remainder} more row(s) with errors"
        raise ValueError(
            f"NVE validation failed: {len(errors)} / {row_count} rows invalid.\n{summary}"
        )

    logger.info("NVE validated: %d rows OK", row_count)


def parse_file(url: str | None = None) -> dict[str, bytes]:
    """Parse NVE electricity grid emission factors and returns per-year CSV bytes.

    Extracts the year and CO2 factor columns, casts to ``int`` and ``float`` respectively. 
    Adds a ``factor_type`` column:``Market-based`` for the *Varedeklarasjon* sheet, ``Location-based``
    for the *Klimadeklarasjon* sheet.
    Splits the result by year and returns a dict mapping year string → CSV bytes.

    Parameters
    ----------
    url : str, optional
        URL to NVE Excel file. Falls back to ``NVE_URL`` env var.
    """
    if url is None:
        url = _get_nve_url()
    logger.info("Downloading NVE Electricity emission factors from %s", url)
    response = requests.get(url, timeout=30)
    response.raise_for_status()
    logger.info("Downloaded %d bytes", len(response.content))

    sheets = pd.read_excel(io.BytesIO(response.content),
                           sheet_name=None, index_col=None)
    logger.info("Found %d sheets: %s", len(sheets), list(sheets.keys()))

    frames: list[pd.DataFrame] = []
    for sheet_name, df in sheets.items():
        name_lower = str(sheet_name).lower()
        if "varedeklarasjon" in name_lower:
            factor_type = "Market-based emission factor for Norwegian electricity consumption"
        elif "klimadeklarasjon" in name_lower:
            factor_type = "Location-based emission factor for Norwegian electricity consumption"
        else:
            logger.debug("Skipping sheet '%s' (no match)", sheet_name)
            continue

        columns = list(df.columns)
        year_col = _find_column(columns, "År")
        co2_col = _find_column(columns, "CO2")

        if not year_col:
            logger.warning(
                "Sheet '%s': column 'År' not found in %s", sheet_name, columns)
        if not co2_col:
            logger.warning(
                "Sheet '%s': column 'CO2' not found in %s", sheet_name, columns)

        try:
            extracted = df[[year_col, co2_col]].copy()
        except KeyError:
            logger.warning(
                "Sheet '%s': columns '%s'/'%s' not present after lookup",
                sheet_name, year_col, co2_col,
            )
            continue

        extracted.columns = ["year", "co2_per_kWh"]
        extracted["factor_type"] = factor_type
        frames.append(extracted)
        logger.info(
            "Extracted %d rows from sheet '%s' (%s)",
            len(extracted), sheet_name, factor_type,
        )

    if not frames:
        raise ValueError(
            "No data extracted from any sheet — NVE parser produced zero rows"
        ) from None

    combined = pd.concat(frames, ignore_index=True)
    logger.info("Combined result: %d rows, columns=%s",
                len(combined), list(combined.columns))

    # Validate before splitting
    _validate_df(combined)

    # Split by year into per-year CSVs
    years = combined["year"].unique()
    result: dict[str, bytes] = {}
    for year_val in sorted(years):
        year_df = combined[combined["year"] == year_val]
        year_key = str(year_val)
        result[year_key] = year_df.to_csv(index=False).encode("utf-8")
        logger.info("Year %s: %d rows", year_key, len(year_df))

    return result


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    result = parse_file()
    for year_key, csv_bytes in result.items():
        print(f"--- {year_key} ---")
        print(csv_bytes.decode("utf-8"))
