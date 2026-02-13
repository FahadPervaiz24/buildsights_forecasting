#!/usr/bin/env python3
"""SARIMA baseline per district (1-month targets, 12-month holdout)."""

import warnings
import pandas as pd
import numpy as np
from statsmodels.tsa.statespace.sarimax import SARIMAX


INPUT = "data/processed/monthly_permits_by_district_modeling.parquet"
SEASONAL_PERIODS = 12
HOLDOUT_MONTHS = 12


def smape(y_true, y_pred):
    y = np.asarray(y_true, dtype=float)
    p = np.asarray(y_pred, dtype=float)
    return np.mean(2 * np.abs(p - y) / (np.abs(p) + np.abs(y) + 1e-8))


def mae(y_true, y_pred):
    y = np.asarray(y_true, dtype=float)
    p = np.asarray(y_pred, dtype=float)
    return np.mean(np.abs(p - y))


def make_full_month_index(df):
    start = df["month"].min()
    end = df["month"].max()
    full_idx = pd.date_range(start, end, freq="MS")
    out = df.set_index("month").reindex(full_idx)
    try:
        out.index = out.index.set_freq("MS")
    except Exception:
        out.index.freq = "MS"
    out.index.name = "month"
    out["permits"] = out["permits"].fillna(0)
    return out.reset_index()


def choose_sarima_order(train_series):
    orders = [(0, 1, 1), (1, 1, 0), (1, 1, 1)]
    seas = [
        (0, 1, 1, SEASONAL_PERIODS),
        (1, 1, 0, SEASONAL_PERIODS),
        (1, 1, 1, SEASONAL_PERIODS),
    ]
    best = None
    best_aic = np.inf
    for o in orders:
        for s in seas:
            try:
                model = SARIMAX(
                    train_series,
                    order=o,
                    seasonal_order=s,
                    enforce_stationarity=False,
                    enforce_invertibility=False,
                )
                res = model.fit(disp=False)
                if res.aic < best_aic:
                    best_aic = res.aic
                    best = (o, s)
            except Exception:
                continue
    return best


def sarima_forecast(train, steps):
    order = choose_sarima_order(train)
    if order is None:
        return pd.Series([np.nan] * steps, index=pd.RangeIndex(steps))
    o, s = order
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        model = SARIMAX(
            train,
            order=o,
            seasonal_order=s,
            enforce_stationarity=False,
            enforce_invertibility=False,
        )
        res = model.fit(disp=False)
        return res.forecast(steps)


def main():
    warnings.filterwarnings(
        "ignore",
        message="No frequency information was provided, so inferred frequency MS will be used.",
        category=Warning,
    )

    df = pd.read_parquet(INPUT).rename(columns={"permit_count": "permits"})
    df["month"] = pd.to_datetime(df["month"])

    results = []

    for boro, g in df.groupby("BoroCD"):
        g = g.sort_values("month")
        g = make_full_month_index(g)

        last_complete = g["month"].max()
        holdout_start = last_complete - pd.DateOffset(months=HOLDOUT_MONTHS - 1)

        series = g.set_index("month")
        actual = series.loc[holdout_start:last_complete, "permits"]
        if len(actual) < HOLDOUT_MONTHS:
            continue

        train = series.loc[:(holdout_start - pd.DateOffset(months=1)), "permits"]
        if len(train) < SEASONAL_PERIODS * 2:
            continue

        pred = sarima_forecast(train, HOLDOUT_MONTHS)
        pred = pd.Series(pred.values, index=actual.index)

        results.append({
            "BoroCD": boro,
            "mae_sarima": mae(actual, pred),
            "smape_sarima": smape(actual, pred),
        })

    res = pd.DataFrame(results).sort_values("BoroCD")
    print("districts:", len(res))
    print("Avg MAE / sMAPE across districts:")
    print("SARIMA:", res["mae_sarima"].mean(), res["smape_sarima"].mean())
    print()
    print(res)


if __name__ == "__main__":
    main()
