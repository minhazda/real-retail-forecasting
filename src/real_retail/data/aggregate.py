"""Aggregate cleaned transactions into a daily per-product demand panel."""

from __future__ import annotations

import pandas as pd

TOP_N_DEFAULT = 50


def top_products(clean: pd.DataFrame, n: int = TOP_N_DEFAULT) -> list[str]:
    """Top-N stock codes by total quantity sold."""
    totals = clean.groupby("StockCode")["Quantity"].sum()
    return totals.nlargest(n).index.astype(str).tolist()


def daily_panel(clean: pd.DataFrame, n: int = TOP_N_DEFAULT) -> pd.DataFrame:
    """Daily quantity per top-N product, as a complete panel.

    Missing product-days (including the structural Saturday closure) are filled
    with explicit zeros so the series is continuous and gaps are real signal.
    """
    codes = top_products(clean, n)
    sub = clean[clean["StockCode"].astype(str).isin(codes)].copy()
    sub["date"] = pd.to_datetime(sub["InvoiceDate"]).dt.normalize()
    grouped = (
        sub.groupby(["StockCode", "date"])["Quantity"].sum().rename("quantity")
    )

    full_dates = pd.date_range(sub["date"].min(), sub["date"].max(), freq="D")
    index = pd.MultiIndex.from_product(
        [codes, full_dates], names=["StockCode", "date"]
    )
    panel = (
        grouped.reindex(index, fill_value=0.0)
        .reset_index()
        .sort_values(["StockCode", "date"])
        .reset_index(drop=True)
    )
    panel["StockCode"] = panel["StockCode"].astype(str)
    return panel
