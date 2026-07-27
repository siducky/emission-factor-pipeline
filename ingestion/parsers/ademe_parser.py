import logging
import os

import requests

logger = logging.getLogger(__name__)


def _get_ademe_url() -> str:
    url = os.getenv("ADEME_URL")
    if not url:
        raise ValueError("ADEME URL environment variable is not set")
    return url


def parse_file(url: str | None = None) -> dict[str, bytes]:
    """Download ADEME Base Carbone CSV and return as ``{"2016": csv_bytes}``.

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
    return {"2016": content}


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    result = parse_file()
    for year_key, csv_bytes in result.items():
        print(f"--- {year_key} ---")
        print(csv_bytes.decode("utf-8"))
