"""The time-ordered split must never leak future into train."""

from __future__ import annotations

import pandas as pd

from real_retail.evaluate.split import time_split


def test_no_leakage(panel_sample: pd.DataFrame) -> None:
    train, test = time_split(panel_sample, test_days=7)
    assert train["date"].max() < test["date"].min()


def test_test_window_length(panel_sample: pd.DataFrame) -> None:
    _, test = time_split(panel_sample, test_days=7)
    # 7 held-out days across both products in the panel.
    assert test["date"].nunique() == 7
