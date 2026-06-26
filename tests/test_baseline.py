"""Seasonal-naive(7) must equal y[t-7] and encode the Saturday zero."""

from __future__ import annotations

import pandas as pd

from real_retail.models.baseline import seasonal_naive


def test_seasonal_naive_is_lag_7(panel_sample: pd.DataFrame) -> None:
    df = panel_sample.sort_values(["StockCode", "date"]).reset_index(drop=True)
    pred = seasonal_naive(df)
    one = df[df["StockCode"] == "10001"].reset_index(drop=True)
    p = pred[df["StockCode"] == "10001"].reset_index(drop=True)
    # day 7 prediction equals day 0 actual.
    assert p.iloc[7] == one["quantity"].iloc[0]


def test_seasonal_naive_predicts_saturday_zero(panel_sample: pd.DataFrame) -> None:
    df = panel_sample.sort_values(["StockCode", "date"]).reset_index(drop=True)
    df["pred"] = seasonal_naive(df).to_numpy()
    sat = df[(df["date"].dt.dayofweek == 5) & df["pred"].notna()]
    # previous Saturday was 0, so the seasonal-naive Saturday forecast is 0.
    assert (sat["pred"] == 0).all()
