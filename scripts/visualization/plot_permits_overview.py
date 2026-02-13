#!/usr/bin/env python3
"""Simple monthly volume plot from unified permits."""

import pandas as pd
import matplotlib.pyplot as plt

INPUT = "data/processed/permits_unified.parquet"
OUTPUT = "scripts/visualization/output/monthly_volume.png"
DATE_COL = "issued_date"


def parse_dates(s: pd.Series) -> pd.Series:
    s = s.astype("string").str.strip()
    d1 = pd.to_datetime(s, format="%m/%d/%Y", errors="coerce")
    d2 = pd.to_datetime(s, format="%Y-%m-%d", errors="coerce")
    d3 = pd.to_datetime(s, errors="coerce")
    return d1.fillna(d2).fillna(d3)


df = pd.read_parquet(INPUT, columns=[DATE_COL])
df[DATE_COL] = parse_dates(df[DATE_COL])
df = df.dropna(subset=[DATE_COL])

df["month"] = df[DATE_COL].dt.to_period("M").dt.to_timestamp()

max_date = df[DATE_COL].max()
max_month_start = max_date.to_period("M").to_timestamp()
max_month_end = max_month_start + pd.offsets.MonthEnd(0)
last_complete = max_month_start - pd.DateOffset(months=1) if max_date < max_month_end else max_month_start

df = df[df["month"] <= last_complete]

monthly = df.groupby("month").size().rename("permits").to_frame()
monthly["ma12"] = monthly["permits"].rolling(12, min_periods=12).mean()

plt.style.use("dark_background")
fig, ax = plt.subplots(figsize=(12, 5))
fig.patch.set_facecolor("#111111")
ax.set_facecolor("#111111")
ax.plot(monthly.index, monthly["permits"], color="white", alpha=0.25, label="Total permits issued")
ax.plot(monthly.index, monthly["ma12"], color="#7A00FF", linewidth=2.0, label="Total permits 12-mo rolling")
ax.set_title("Monthly Permit Volume")
ax.set_xlabel("Month")
ax.set_ylabel("Permit count")
ax.grid(color="gray", alpha=0.3)
# light year markers
year_starts = pd.date_range(monthly.index.min(), monthly.index.max(), freq="YS")
for d in year_starts:
    ax.axvline(d, color="gray", alpha=0.25, linewidth=0.6)
ax.legend()
plt.tight_layout()
plt.savefig(OUTPUT, dpi=150)
plt.close(fig)

print("saved:", OUTPUT)
