"""Time-ordered holdout split (no shuffling, no leakage)."""

from __future__ import annotations

import pandas as pd

TEST_DAYS_DEFAULT = 56  # 8 weeks


def split_cutoff(df: pd.DataFrame, test_days: int = TEST_DAYS_DEFAULT) -> pd.Timestamp:
    """First date of the test window (last ``test_days`` days are held out)."""
    last = df["date"].max()
    return last - pd.Timedelta(days=test_days - 1)


def time_split(
    df: pd.DataFrame, test_days: int = TEST_DAYS_DEFAULT
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Return (train, test); test is strictly the final ``test_days`` days."""
    cutoff = split_cutoff(df, test_days)
    train = df[df["date"] < cutoff].copy()
    test = df[df["date"] >= cutoff].copy()
    # Leakage guard: every train date precedes every test date.
    assert train["date"].max() < test["date"].min(), "train/test overlap"
    return train, test
