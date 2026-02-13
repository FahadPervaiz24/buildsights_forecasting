#!/usr/bin/env python3
"""Fetch NYC DOB permit issuance data from Socrata and store raw rows in Parquet."""

import argparse
import json
import os
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
from urllib.parse import urlencode
from urllib.request import Request, urlopen

import pyarrow as pa
import pyarrow.parquet as pq


BASE_DOMAIN = "data.cityofnewyork.us"
DEFAULT_DATASET_ID = "ipu4-2q9a"  # DOB Permit Issuance
VIEW_URL_TEMPLATE = "https://data.cityofnewyork.us/api/views/{dataset_id}.json"
DATA_URL_TEMPLATE = "https://data.cityofnewyork.us/resource/{dataset_id}.json"
DATASET_REQUIRED_FIELDS = {
    # DOB Permit Issuance
    "ipu4-2q9a": ["permit_si_no", "gis_latitude", "gis_longitude", "issuance_date"],
    # DOB NOW: Build - Approved Permits
    "rbx6-tga4": ["job_filing_number", "issued_date", "latitude", "longitude", "bin"],
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Ingest raw NYC DOB permits from API to Parquet."
    )
    parser.add_argument(
        "--dataset-id",
        default=DEFAULT_DATASET_ID,
        help=f"Socrata dataset id (default: {DEFAULT_DATASET_ID})",
    )
    parser.add_argument(
        "--output",
        default=None,
        help="Output parquet file path",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=50000,
        help="Page size per API call (default: 50000)",
    )
    parser.add_argument(
        "--max-pages",
        type=int,
        default=None,
        help="Optional max number of pages (for testing)",
    )
    parser.add_argument(
        "--where",
        default=None,
        help="Optional SoQL where clause, example: \"issuance_date >= '2024-01-01T00:00:00'\"",
    )
    parser.add_argument(
        "--app-token-env",
        default="SOCRATA_APP_TOKEN",
        help="Env var containing Socrata app token (default: SOCRATA_APP_TOKEN)",
    )
    parser.add_argument(
        "--retries",
        type=int,
        default=5,
        help="Retries per request (default: 5)",
    )
    parser.add_argument(
        "--start-offset",
        type=int,
        default=0,
        help="Starting offset for resume runs (default: 0)",
    )
    return parser.parse_args()


def get_required_fields(dataset_id: str) -> List[str]:
    return DATASET_REQUIRED_FIELDS.get(dataset_id, [])


def http_get_json(
    url: str,
    *,
    params: Optional[Dict[str, str]] = None,
    app_token: Optional[str] = None,
    timeout: int = 120,
) -> List[Dict] | Dict:
    if params:
        url = f"{url}?{urlencode(params)}"

    req = Request(url)
    req.add_header("Accept", "application/json")
    if app_token:
        req.add_header("X-App-Token", app_token)

    with urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))


def get_dataset_columns(app_token: Optional[str], dataset_id: str, retries: int) -> List[str]:
    url = VIEW_URL_TEMPLATE.format(dataset_id=dataset_id)
    for attempt in range(1, retries + 1):
        try:
            payload = http_get_json(url, app_token=app_token, timeout=60)
            columns = [c["fieldName"] for c in payload.get("columns", []) if c.get("fieldName")]
            if not columns:
                raise RuntimeError("No columns discovered from dataset metadata.")
            return columns
        except Exception:
            if attempt == retries:
                raise
            time.sleep(min(2 * attempt, 10))
    raise RuntimeError("Failed to fetch dataset columns.")


def fetch_page(
    app_token: Optional[str],
    dataset_id: str,
    columns: List[str],
    limit: int,
    offset: int,
    where_clause: Optional[str],
    retries: int,
) -> List[Dict]:
    params = {
        "$limit": str(limit),
        "$offset": str(offset),
        "$order": ":id",
        "$select": ",".join(columns),
    }
    if where_clause:
        params["$where"] = where_clause

    url = DATA_URL_TEMPLATE.format(dataset_id=dataset_id)
    for attempt in range(1, retries + 1):
        try:
            return http_get_json(url, params=params, app_token=app_token, timeout=120)
        except Exception:
            if attempt == retries:
                raise
            time.sleep(min(2 * attempt, 10))
    return []


def normalize_rows(records: List[Dict], columns: List[str]) -> List[Dict]:
    normalized = []
    for record in records:
        normalized.append({column: record.get(column) for column in columns})
    return normalized


def ingest_to_parquet(args: argparse.Namespace) -> None:
    default_output = (
        f"data/raw/{args.dataset_id}_raw_api_{datetime.now().strftime('%Y%m%d_%H%M%S')}.parquet"
    )
    output_value = args.output or default_output
    required_fields = get_required_fields(args.dataset_id)

    output_path = Path(output_value)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    if output_path.exists() and args.start_offset == 0:
        output_path.unlink()
    if output_path.exists() and args.start_offset > 0:
        raise RuntimeError(
            "Output file already exists for resume mode. "
            "Use a different --output path for resumed ingest."
        )

    app_token = os.environ.get(args.app_token_env)
    columns = get_dataset_columns(app_token=app_token, dataset_id=args.dataset_id, retries=args.retries)
    for field in required_fields:
        if field not in columns:
            columns.append(field)

    print(f"dataset_id: {args.dataset_id}")
    print(f"columns discovered: {len(columns)}")
    if required_fields:
        print(f"required fields: {', '.join(required_fields)}")
    else:
        print("required fields: (none configured for this dataset id)")
    print(f"output: {output_path}")
    print(f"limit: {args.limit}")

    writer = None
    total_rows = 0
    offset = args.start_offset
    page_num = 0
    fixed_schema = pa.schema([(column, pa.string()) for column in columns])

    try:
        while True:
            page_num += 1
            if args.max_pages is not None and page_num > args.max_pages:
                break

            rows = fetch_page(
                app_token=app_token,
                dataset_id=args.dataset_id,
                columns=columns,
                limit=args.limit,
                offset=offset,
                where_clause=args.where,
                retries=args.retries,
            )
            if not rows:
                break

            batch_rows = normalize_rows(rows, columns)
            table = pa.Table.from_pylist(batch_rows, schema=fixed_schema)
            if writer is None:
                writer = pq.ParquetWriter(str(output_path), table.schema)
            writer.write_table(table)

            batch_size = len(batch_rows)
            total_rows += batch_size
            print(
                f"page {page_num}: fetched {batch_size:,} rows "
                f"(session total {total_rows:,}, offset {offset:,})"
            )

            if batch_size < args.limit:
                break
            offset += args.limit
    finally:
        if writer is not None:
            writer.close()

    if writer is None:
        raise RuntimeError("No rows fetched. Parquet file was not created.")

    print(f"done: wrote {total_rows:,} rows to {output_path}")


if __name__ == "__main__":
    ingest_to_parquet(parse_args())
