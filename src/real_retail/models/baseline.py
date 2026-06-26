"""Seasonal-naive(7) baseline — forecast = value from one week earlier.

Because Saturdays are structurally ~0, the previous Saturday's value is also ~0,
so seasonal-naive(7) encodes the Saturday closure for free.
"""

from __future__ import annotations

import pandas as pd

SEASON = 7


def seasonal_naive(panel: pd.DataFrame, season: int = SEASON) -> pd.Series:
    """Prediction y_hat[t] = quantity[t - season] per StockCode (NaN if unseen)."""
    df = panel.sort_values(["StockCode", "date"])
    return df.groupby("StockCode", observed=True)["quantity"].shift(season)
