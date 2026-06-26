"""MASE/MAE math is the headline metric — pin it to known values."""

from __future__ import annotations

import numpy as np

from real_retail.evaluate.metrics import improvement_pct, mae, mase, seasonal_naive_scale


def test_mae_zero_on_perfect() -> None:
    assert mae([1, 2, 3], [1, 2, 3]) == 0.0


def test_seasonal_naive_scale() -> None:
    # y[7:] - y[:-7] = [8,9] - [1,2] = [7,7] -> mean 7.0
    y = np.arange(1, 10, dtype=float)
    assert seasonal_naive_scale(y, season=7) == 7.0


def test_mase_matches_definition() -> None:
    y_train = np.arange(1, 10, dtype=float)  # scale = 7.0
    y_true = np.array([10.0, 10.0])
    y_pred = np.array([3.0, 17.0])  # MAE = 7.0
    assert mase(y_true, y_pred, y_train, season=7) == 1.0


def test_improvement_pct() -> None:
    assert improvement_pct(100.0, 75.0) == 25.0
