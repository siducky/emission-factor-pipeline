import csv
import io
import logging
import os

import requests

from ingestion.parsers.models import AdemeRawRow

logger = logging.getLogger(__name__)


def _get_ademe_url() -> str:
    url = os.getenv("ADEME_URL")
    if not url:
        raise ValueError("ADEME URL environment variable is not set")
    return url


def parse_file(url: str | None = None) -> dict[str, bytes]:
    """Download ADEME Base Carbone CSV, validate every row, return as ``{"2016": csv_bytes}``.

    Parameters
    ----------
    url : str, optional
        URL to ADEME API.
    """
    if url is None:
        url = _get_ademe_url()
    logger.info("Downloading ADEME data from %s", url)
    with requests.get(url, timeout=30) as response:
        response.raise_for_status()
        content = response.content
    logger.info("Downloaded %d bytes", len(content))

    _validate_csv(content)

    return {"2016": content}


def _validate_csv(raw: bytes) -> None:
    """Parse CSV bytes and validate every row against ``AdemeRawRow``."""
    decoded = raw.decode("utf-8-sig")
    reader = csv.DictReader(io.StringIO(decoded))

    errors: list[str] = []
    row_count = 0
    for row_num, row in enumerate(reader, start=2):
        row_count += 1
        ef = row.get("Facteur d'émission", "")
        if not ef or not ef.strip():
            continue
        try:
            AdemeRawRow.model_validate(row)
        except Exception as e:
            errors.append(f"Row {row_num}: {e}")

    if row_count == 0:
        raise ValueError("ADEME CSV is empty — no rows to validate")

    if errors:
        summary = "\n".join(errors[:20])
        remainder = len(errors) - 20
        if remainder > 0:
            summary += f"\n... and {remainder} more row(s) with errors"
        raise ValueError(
            f"ADEME CSV validation failed: {len(errors)} / {row_count} rows invalid.\n{summary}"
        )

    logger.info("ADEME CSV validated: %d rows OK", row_count)


if __name__ == "__main__":
    from ingestion.logging_config import setup_logging
    setup_logging()
    result = parse_file()
