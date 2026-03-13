#!/usr/bin/env python3
"""Build monthly permit counts by BoroCD with real year-month timestamps."""

import pandas as pd

INPUT = "data/processed/permits_unified_with_district.parquet"
OUTPUT_ALL = "data/processed/monthly_permits_by_district.parquet"
OUTPUT_MODEL = "data/processed/monthly_permits_by_district_modeling.parquet"

df = pd.read_parquet(INPUT)
df["issued_date"] = pd.to_datetime(df["issued_date"], errors="coerce")
df = df.dropna(subset=["issued_date", "BoroCD"])

# true year-month
df["month"] = df["issued_date"].dt.to_period("M").dt.to_timestamp()

monthly = (
    df.groupby(["BoroCD", "month"])["permit_id"]
      .count()
      .reset_index(name="permit_count")
      .sort_values(["BoroCD", "month"])
)

monthly.to_parquet(OUTPUT_ALL, index=False)

# filter low-volume districts
low_volume = (
    monthly.groupby("BoroCD")["permit_count"]
    .sum()
    .loc[lambda s: s < 5000]
    .index
)

monthly_model = monthly[~monthly["BoroCD"].isin(low_volume)].copy()
monthly_model.to_parquet(OUTPUT_MODEL, index=False)

print("all:", monthly.shape, "->", OUTPUT_ALL)
print("model:", monthly_model.shape, "->", OUTPUT_MODEL)
