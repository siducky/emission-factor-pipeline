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
    """Download ADEME Base Carbone CSV, filter & validate every row, return as ``{"2016": csv_bytes}``.

    Rows with a null/blank emission factor are dropped (logged as warnings).
    Rows that fail ``AdemeRawRow`` validation raise an error.

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

    filtered = _filter_and_validate_csv(content)

    return {"2016": filtered}


def _filter_and_validate_csv(raw: bytes) -> bytes:
    """Parse CSV, drop rows with null/blank emission factors, validate the rest.

    Returns re-serialized CSV bytes containing only valid rows with a non-empty
    ``Facteur d'émission`` column.
    """
    decoded = raw.decode("utf-8-sig")
    reader = csv.DictReader(io.StringIO(decoded))

    fieldnames = reader.fieldnames
    if not fieldnames:
        raise ValueError("ADEME CSV has no columns")

    valid_rows: list[dict[str, str]] = []
    errors: list[str] = []
    skipped = 0
    row_count = 0

    for row_num, row in enumerate(reader, start=2):
        row_count += 1
        ef = row.get("Facteur d'émission", "")
        if not ef or not ef.strip():
            skipped += 1
            logger.warning(
                "Row %d: missing 'Facteur d'émission', skipping", row_num)
            continue
        try:
            AdemeRawRow.model_validate(row)
            valid_rows.append(row)
        except Exception as e:
            errors.append(f"Row {row_num}: {e}")

    if row_count == 0:
        raise ValueError("ADEME CSV is empty — no rows to parse")

    if errors:
        summary = "\n".join(errors[:20])
        remainder = len(errors) - 20
        if remainder > 0:
            summary += f"\n... and {remainder} more row(s) with errors"
        raise ValueError(
            f"ADEME CSV validation failed: {len(errors)} / {row_count} rows invalid.\n{summary}"
        )

    logger.info(
        "ADEME CSV processed: %d valid, %d skipped (null EF), %d total rows",
        len(valid_rows),
        skipped,
        row_count,
    )

    buf = io.StringIO()
    writer = csv.DictWriter(buf, fieldnames=fieldnames, extrasaction="ignore")
    writer.writeheader()
    writer.writerows(valid_rows)
    return buf.getvalue().encode("utf-8")


if __name__ == "__main__":
    from ingestion.logging_config import setup_logging

    setup_logging()
    result = parse_file()
