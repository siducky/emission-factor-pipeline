import io
import logging
import os

import pandas as pd
import requests

logger = logging.getLogger(__name__)

NVE_URL = os.getenv("NVE_URL")
if not NVE_URL:
    raise ValueError("NVE URL is not defined")


def _find_column(columns: list, target: str) -> str | None:
    """Locate a column by case-insensitive, whitespace-stripped header match."""
    try:
        return next(c for c in columns if str(c).strip().lower() == target.lower())
    except StopIteration:
        return None


def parse_file(url=NVE_URL) -> bytes:
    """Parse NVE electricity grid emission factors and returns csv.

    Extracts the year and CO2 factor columns, casts to ``int`` and ``float`` respectively. 
    Adds a ``factor_type`` column:``Market-based`` for the *Varedeklarasjon* sheet, ``Location-based``
    for the *Klimadeklarasjon* sheet.
    """
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

        if not year_col or not co2_col:
            continue

        try:
            extracted = df[[year_col, co2_col]].copy()
        except KeyError:
            logger.warning(
                "Sheet '%s': columns '%s'/'%s' not present after lookup",
                sheet_name, year_col, co2_col,
            )
            continue

        extracted.columns = ["year", "co2_per_kWh"]
        extracted["year"] = extracted["year"].astype(int)
        extracted["co2_per_kWh"] = extracted["co2_per_kWh"].astype(float)
        extracted["factor_type"] = factor_type
        frames.append(extracted)
        logger.info(
            "Extracted %d rows from sheet '%s' (%s)",
            len(extracted), sheet_name, factor_type,
        )

    if not frames:
        raise ValueError(
            "No data extracted from any sheet — NVE parser produced zero rows"
        )

    combined = pd.concat(frames, ignore_index=True)
    logger.info("Combined result: %d rows, columns=%s",
                len(combined), list(combined.columns))
    return combined.to_csv(index=False).encode("utf-8")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    data = parse_file()
    print(data.decode("utf-8"))
