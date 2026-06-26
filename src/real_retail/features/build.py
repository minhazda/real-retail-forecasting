"""Leakage-safe calendar + lag features for the daily demand panel."""

from __future__ import annotations

import pandas as pd

LAGS = (1, 7, 14, 28)
ROLL_WINDOWS = (7, 28)
MAX_LAG = max(max(LAGS), max(ROLL_WINDOWS))


def build_features(panel: pd.DataFrame) -> pd.DataFrame:
    """Add calendar + lag/rolling features.

    All temporal features use only past values (``groupby.shift``), so a row at
    date ``t`` never sees ``quantity`` at ``t`` or later. ``is_saturday`` makes
    the structural Saturday closure explicit to the model.
    """
    df = panel.sort_values(["StockCode", "date"]).copy()
    d = df["date"].dt

    # Calendar
    df["dayofweek"] = d.dayofweek.astype("int16")
    df["is_saturday"] = (d.dayofweek == 5).astype("int8")
    df["weekofyear"] = d.isocalendar().week.astype("int16").to_numpy()
    df["month"] = d.month.astype("int16")
    df["is_december"] = (d.month == 12).astype("int8")

    g = df.groupby("StockCode", observed=True)["quantity"]
    for lag in LAGS:
        df[f"lag_{lag}"] = g.shift(lag)
    for win in ROLL_WINDOWS:
        # shift(1) first so the window is strictly past data.
        df[f"roll_mean_{win}"] = g.shift(1).rolling(win).mean().to_numpy()

    df["StockCode"] = df["StockCode"].astype("category")
    return df


def feature_columns(df: pd.DataFrame) -> list[str]:
    """Model input columns (everything except keys/target)."""
    exclude = {"date", "quantity"}
    return [c for c in df.columns if c not in exclude]
