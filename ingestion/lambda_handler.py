import logging
import os
import time

import boto3
from parsers import ademe_parser, defra_parser, nve_parser

logger = logging.getLogger(__name__)
s3_client = boto3.client("s3")
BUCKET_NAME = os.getenv("S3_BUCKET")
PARSERS = {"ademe": ademe_parser, "nve": nve_parser, "defra": defra_parser}

if not BUCKET_NAME:
    raise ValueError("S3_BUCKET environment variable is not set")


def lambda_handler(event, context):
    logger.info("Starting modular ingestion..")
    sources = event.get("sources", list(PARSERS.keys())
                        ) if event else list(PARSERS.keys())

    results = {}
    for source_name in sources:
        parser_module = PARSERS.get(source_name)
        if not parser_module:
            logger.error("Unknown source '%s', skipping", source_name)
            results[source_name] = {
                "status": "error", "reason": "unknown_source"}
            continue

        start = time.perf_counter()
        try:
            logger.info("Running parser for %s...", source_name)
            year_files = parser_module.parse_file()
            for year_key, csv_data in year_files.items():
                file_path = f"bronze/{source_name}/{year_key}/factors.csv"
                s3_client.put_object(
                    Bucket=BUCKET_NAME,
                    Key=file_path,
                    Body=csv_data,
                    ContentType="text/csv",
                )
            elapsed = time.perf_counter() - start
            logger.info(
                "Successfully ingested %s (%d files) in %.2fs",
                source_name,
                len(year_files),
                elapsed,
                extra={"source": source_name,
                       "duration_s": elapsed, "status": "ok"},
            )
            results[source_name] = {"status": "ok",
                                    "duration_s": round(elapsed, 2)}

        except Exception as e:
            elapsed = time.perf_counter() - start
            logger.error(
                "Failed to ingest %s after %.2fs: %s",
                source_name,
                elapsed,
                str(e),
                extra={"source": source_name,
                       "duration_s": elapsed, "status": "error"},
            )
            results[source_name] = {"status": "error", "reason": str(e)}

    all_ok = all(r["status"] == "ok" for r in results.values())
    status_code = 200 if all_ok else 500
    return {"statusCode": status_code, "body": results}


if __name__ == "__main__":
    from ingestion.logging_config import setup_logging
    setup_logging()
    lambda_handler({}, None)
