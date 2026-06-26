"""Shared fixtures: small in-memory frames so tests need no dataset download."""

from __future__ import annotations

import pandas as pd
import pytest


@pytest.fixture
def raw_sample() -> pd.DataFrame:
    """A tiny raw-like frame exercising every cleaning rule (DD-01..DD-07)."""
    base = dict(Description="x", InvoiceDate=pd.Timestamp("2010-01-04"), Country="UK")
    rows = [
        # keepable product rows (second has missing CustomerID -> DD-03 keep)
        dict(Invoice="489434", StockCode="85048", Quantity=12, Price=6.95, CustomerID=1.0),
        dict(Invoice="489435", StockCode="79323P", Quantity=5, Price=2.10, CustomerID=None),
        # DD-01 cancellation
        dict(Invoice="C489436", StockCode="85048", Quantity=-3, Price=6.95, CustomerID=1.0),
        # DD-02 negative qty, non-cancellation adjustment
        dict(Invoice="489437", StockCode="85048", Quantity=-2, Price=6.95, CustomerID=1.0),
        # DD-04 non-product code
        dict(Invoice="489438", StockCode="POST", Quantity=1, Price=18.0, CustomerID=1.0),
        # DD-05 zero price
        dict(Invoice="489439", StockCode="85048", Quantity=4, Price=0.0, CustomerID=1.0),
    ]
    df = pd.DataFrame([{**base, **r} for r in rows])
    # DD-07 exact duplicate of the first keepable row
    df = pd.concat([df, df.iloc[[0]]], ignore_index=True)
    return df


@pytest.fixture
def panel_sample() -> pd.DataFrame:
    """Two products over 21 daily dates; Saturdays forced to zero demand."""
    dates = pd.date_range("2010-01-01", periods=21, freq="D")
    frames = []
    for code, level in [("10001", 10.0), ("10002", 100.0)]:
        q = [0.0 if d.dayofweek == 5 else level + i for i, d in enumerate(dates)]
        frames.append(pd.DataFrame({"StockCode": code, "date": dates, "quantity": q}))
    return pd.concat(frames, ignore_index=True)
