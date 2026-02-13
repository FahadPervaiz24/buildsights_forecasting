import pandas as pd
import numpy as np

# =========================
# 12-Month Rolling Avg Baseline (Per District)
# - Uses last COMPLETE month only (drops in-progress month automatically)
# - Holdout = last 12 COMPLETE months
# =========================

df = pd.read_parquet("data/processed/monthly_permits_by_district_modeling.parquet")

# Expected columns: BoroCD, month, permit_count
df = df.rename(columns={"permit_count": "permits"})

# Ensure month is datetime
df["month"] = pd.to_datetime(df["month"])

# Determine last complete month from dataset
max_date = df["month"].max()
max_month_start = max_date.to_period("M").to_timestamp()
max_month_end = max_month_start + pd.offsets.MonthEnd(0)
last_complete_month = max_month_start - pd.DateOffset(months=1) if max_date < max_month_end else max_month_start

df = df[df["month"] <= last_complete_month].copy()

def metrics(d: pd.DataFrame):
    y = d["y_true"].to_numpy(float)
    p = d["pred"].to_numpy(float)
    mae = np.mean(np.abs(y - p))
    smape = np.mean(2 * np.abs(p - y) / (np.abs(p) + np.abs(y) + 1e-8))
    return mae, smape

rows = []

for boro, g in df.groupby("BoroCD"):
    g = g.sort_values("month").copy()
    g["roll12"] = g["permits"].rolling(window=12, min_periods=12).mean()
    g["pred"] = g["roll12"].shift(1)
    eval_df = g.dropna(subset=["pred"]).copy()
    eval_df["y_true"] = eval_df["permits"]
    if eval_df.empty:
        continue

    holdout_start = last_complete_month - pd.DateOffset(months=11)
    train_eval = eval_df[eval_df["month"] < holdout_start]
    val_eval = eval_df[eval_df["month"] >= holdout_start]

    mae_all, smape_all = metrics(eval_df)
    mae_tr, smape_tr = metrics(train_eval) if len(train_eval) else (np.nan, np.nan)
    mae_va, smape_va = metrics(val_eval) if len(val_eval) else (np.nan, np.nan)

    rows.append({
        "BoroCD": boro,
        "mae_all": mae_all,
        "smape_all": smape_all,
        "mae_train": mae_tr,
        "smape_train": smape_tr,
        "mae_val": mae_va,
        "smape_val": smape_va,
        "n_train": len(train_eval),
        "n_val": len(val_eval),
        "n_eval": len(eval_df),
    })

if not rows:
    print("No districts had enough history for a 12-month rolling baseline.")
    print("Last complete month:", last_complete_month)
else:
    results = pd.DataFrame(rows).sort_values("BoroCD")
    avg_mae = results["mae_val"].mean()
    avg_smape = results["smape_val"].mean()
    print("Last complete month:", last_complete_month)
    print("Districts evaluated:", len(results))
    print(f"Avg VAL MAE: {avg_mae:.4f}")
    print(f"Avg VAL sMAPE: {avg_smape:.4f}")
    print()
    print(results)
