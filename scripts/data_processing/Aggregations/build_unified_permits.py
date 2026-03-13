#!/usr/bin/env python3
"""Build a canonical permits table from historical + DOB NOW raw parquet files."""

import argparse
from pathlib import Path

import pandas as pd


CANONICAL_COLUMNS = [
    "source_system",
    "permit_id",
    "issued_date",
    "filing_date",
    "expiration_date",
    "permit_status",
    "job_type",
    "work_type",
    "borough",
    "bin",
    "block",
    "lot",
    "zip_code",
    "latitude",
    "longitude",
    "community_board",
    "council_district",
    "census_tract",
    "nta",
    "estimated_job_cost",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build unified permits parquet.")
    parser.add_argument(
        "--historical-input",
        default="data/raw/dob_historical.parquet",
        help="Historical permits input parquet",
    )
    parser.add_argument(
        "--dob-now-input",
        default="data/raw/dob_now.parquet",
        help="DOB NOW permits input parquet",
    )
    parser.add_argument(
        "--output",
        default="data/processed/permits_unified.parquet",
        help="Output unified parquet path",
    )
    return parser.parse_args()


def parse_mixed_dates(series: pd.Series) -> pd.Series:
    """Parse mixed dates from both API systems."""
    s = series.astype("string").str.strip()
    parsed_us = pd.to_datetime(s, format="%m/%d/%Y", errors="coerce")
    parsed_iso = pd.to_datetime(s, format="%Y-%m-%d", errors="coerce")
    parsed_generic = pd.to_datetime(s, errors="coerce")
    return parsed_us.fillna(parsed_iso).fillna(parsed_generic)


def to_numeric(series: pd.Series) -> pd.Series:
    return pd.to_numeric(series, errors="coerce")


def build_historical(df: pd.DataFrame) -> pd.DataFrame:
    out = pd.DataFrame(
        {
            "source_system": "dob_historical",
            "permit_id": df["permit_si_no"],
            "issued_date": parse_mixed_dates(df["issuance_date"]),
            "filing_date": parse_mixed_dates(df["filing_date"]),
            "expiration_date": parse_mixed_dates(df["expiration_date"]),
            "permit_status": df["permit_status"],
            "job_type": df["job_type"],
            "work_type": df["work_type"],
            "borough": df["borough"],
            "bin": df["bin__"],
            "block": df["block"],
            "lot": df["lot"],
            "zip_code": df["zip_code"],
            "latitude": to_numeric(df["gis_latitude"]),
            "longitude": to_numeric(df["gis_longitude"]),
            "community_board": df["community_board"],
            "council_district": to_numeric(df["gis_council_district"]),
            "census_tract": df["gis_census_tract"],
            "nta": df["gis_nta_name"],
            "estimated_job_cost": pd.NA,
        }
    )
    return out[CANONICAL_COLUMNS]


def build_dob_now(df: pd.DataFrame) -> pd.DataFrame:
    out = pd.DataFrame(
        {
            "source_system": "dob_now",
            "permit_id": df["job_filing_number"],
            "issued_date": parse_mixed_dates(df["issued_date"]),
            "filing_date": pd.NaT,
            "expiration_date": parse_mixed_dates(df["expired_date"]),
            "permit_status": df["permit_status"],
            "job_type": pd.NA,
            "work_type": df["work_type"],
            "borough": df["borough"],
            "bin": df["bin"],
            "block": df["block"],
            "lot": df["lot"],
            "zip_code": df["zip_code"],
            "latitude": to_numeric(df["latitude"]),
            "longitude": to_numeric(df["longitude"]),
            "community_board": df["community_board"],
            "council_district": to_numeric(df["council_district"]),
            "census_tract": df["census_tract"],
            "nta": df["nta"],
            "estimated_job_cost": to_numeric(df["estimated_job_costs"]),
        }
    )
    return out[CANONICAL_COLUMNS]


def main() -> None:
    args = parse_args()

    hist_cols = [
        "permit_si_no",
        "issuance_date",
        "filing_date",
        "expiration_date",
        "permit_status",
        "job_type",
        "work_type",
        "borough",
        "bin__",
        "block",
        "lot",
        "zip_code",
        "gis_latitude",
        "gis_longitude",
        "community_board",
        "gis_council_district",
        "gis_census_tract",
        "gis_nta_name",
    ]
    now_cols = [
        "job_filing_number",
        "issued_date",
        "expired_date",
        "permit_status",
        "work_type",
        "borough",
        "bin",
        "block",
        "lot",
        "zip_code",
        "latitude",
        "longitude",
        "community_board",
        "council_district",
        "census_tract",
        "nta",
        "estimated_job_costs",
    ]

    hist_raw = pd.read_parquet(args.historical_input, columns=hist_cols)
    now_raw = pd.read_parquet(args.dob_now_input, columns=now_cols)

    hist = build_historical(hist_raw)
    now = build_dob_now(now_raw)
    permits = pd.concat([hist, now], ignore_index=True)

    # Requested quick overlap diagnostic (do NOT dedupe yet)
    permits["lat_r"] = permits["latitude"].round(5)
    permits["lon_r"] = permits["longitude"].round(5)
    permits["issue_day"] = permits["issued_date"].dt.floor("D")

    overlap = permits[
        (permits["issued_date"] >= "2016-01-01") & (permits["issued_date"] <= "2019-12-31")
    ]
    collisions = (
        overlap.groupby(["lat_r", "lon_r", "issue_day"])
        .agg(n=("source_system", "size"), n_sources=("source_system", "nunique"))
        .reset_index()
    )
    cross_system = collisions[collisions["n_sources"] > 1]
    print("cross-system collisions:", len(cross_system))

    permits = permits[CANONICAL_COLUMNS]
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    permits.to_parquet(output_path, index=False)

    print(f"wrote unified permits: {output_path}")
    print(f"rows: {len(permits):,}")
    print("rows by source:")
    print(permits["source_system"].value_counts(dropna=False))


if __name__ == "__main__":
    main()
