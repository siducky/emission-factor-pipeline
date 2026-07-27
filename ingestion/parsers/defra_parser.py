import io
import logging
import os
from datetime import datetime

import pandas as pd
import requests

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


def parse_file() -> dict[str, bytes]:
    """Download DEFRA GHG conversion factors for the previous calendar year.

    Returns a single-entry dict mapping year string → CSV bytes.
    """
    base_url = _get_defra_url()
    year = datetime.now().year - 1
    df = _download_year(year, base_url)
    return {str(year): df.to_csv(index=False).encode("utf-8")}


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    result = parse_file()
    for year_key, csv_bytes in result.items():
        print(f"--- {year_key} ---")
        print(csv_bytes.decode("utf-8"))
