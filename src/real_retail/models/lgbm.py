"""A single global LightGBM regressor on lag/calendar features."""

from __future__ import annotations

import lightgbm as lgb
import numpy as np
import pandas as pd
from numpy.typing import NDArray


def _build_model() -> lgb.LGBMRegressor:
    """A single global regressor; objective=L1 optimises MAE directly."""
    return lgb.LGBMRegressor(
        objective="regression_l1",
        n_estimators=400,
        learning_rate=0.05,
        num_leaves=31,
        min_child_samples=50,
        subsample=0.8,
        colsample_bytree=0.8,
        random_state=42,
        verbose=-1,
    )


def train_predict(
    train: pd.DataFrame,
    test: pd.DataFrame,
    feature_cols: list[str],
    target: str = "quantity",
) -> NDArray[np.float64]:
    """Fit on train rows, return predictions for test rows (clipped at 0)."""
    cat = [c for c in ["StockCode"] if c in feature_cols]
    model = _build_model()
    model.fit(
        train[feature_cols],
        train[target],
        categorical_feature=cat or "auto",
    )
    preds = model.predict(test[feature_cols])
    return np.clip(preds, 0.0, None)
