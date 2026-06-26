"""Forecast error metrics: MAE and MASE (seasonal-naive scaled)."""

from __future__ import annotations

import numpy as np
import pandas as pd
from numpy.typing import ArrayLike


def mae(y_true: ArrayLike, y_pred: ArrayLike) -> float:
    return float(np.mean(np.abs(np.asarray(y_true) - np.asarray(y_pred))))


def seasonal_naive_scale(y_train: ArrayLike, season: int = 7) -> float:
    """In-sample MAE of the seasonal-naive forecast — the MASE denominator."""
    y = np.asarray(y_train, dtype=float)
    if len(y) <= season:
        return float("nan")
    diffs = np.abs(y[season:] - y[:-season])
    scale = float(np.mean(diffs))
    return scale


def mase(
    y_true: ArrayLike,
    y_pred: ArrayLike,
    y_train: ArrayLike,
    season: int = 7,
) -> float:
    """Mean Absolute Scaled Error vs the in-sample seasonal-naive baseline."""
    scale = seasonal_naive_scale(y_train, season)
    if not np.isfinite(scale) or scale == 0:
        return float("nan")
    return mae(y_true, y_pred) / scale


def improvement_pct(mae_baseline: float, mae_model: float) -> float:
    """% reduction in MAE of the model vs the named baseline (positive = better)."""
    if mae_baseline == 0:
        return float("nan")
    return (mae_baseline - mae_model) / mae_baseline * 100.0


def per_series_table(
    test: pd.DataFrame,
    season: int = 7,
) -> pd.DataFrame:
    """Per-StockCode MAE/MASE for baseline + model from a scored test frame.

    ``test`` must have columns: StockCode, y_true, pred_baseline, pred_model,
    and ``scale`` (in-sample seasonal-naive MAE for that series).
    """
    rows = []
    for code, g in test.groupby("StockCode", observed=True):
        scale = float(g["scale"].iloc[0])
        mae_b = mae(g["y_true"], g["pred_baseline"])
        mae_m = mae(g["y_true"], g["pred_model"])
        rows.append(
            {
                "StockCode": code,
                "mae_baseline": mae_b,
                "mae_model": mae_m,
                "mase_baseline": mae_b / scale if scale else float("nan"),
                "mase_model": mae_m / scale if scale else float("nan"),
                "improvement_pct": improvement_pct(mae_b, mae_m),
            }
        )
    return pd.DataFrame(rows)
