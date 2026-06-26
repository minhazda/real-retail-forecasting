"""Each cleaning rule (DD-01..DD-07) is load-bearing — test it directly."""

from __future__ import annotations

import pandas as pd

from real_retail.data.clean import clean_transactions, cleaning_report


def test_cancellations_dropped(raw_sample: pd.DataFrame) -> None:  # DD-01
    out = clean_transactions(raw_sample)
    assert not out["Invoice"].astype(str).str.startswith("C").any()


def test_negative_quantity_dropped(raw_sample: pd.DataFrame) -> None:  # DD-02
    out = clean_transactions(raw_sample)
    assert (out["Quantity"] > 0).all()


def test_missing_customer_id_kept(raw_sample: pd.DataFrame) -> None:  # DD-03
    out = clean_transactions(raw_sample)
    assert out["CustomerID"].isna().any(), "rows with missing CustomerID must be kept"


def test_non_product_code_dropped(raw_sample: pd.DataFrame) -> None:  # DD-04
    out = clean_transactions(raw_sample)
    assert "POST" not in set(out["StockCode"].astype(str))


def test_nonpositive_price_dropped(raw_sample: pd.DataFrame) -> None:  # DD-05
    out = clean_transactions(raw_sample)
    assert (out["Price"] > 0).all()


def test_exact_duplicates_dropped(raw_sample: pd.DataFrame) -> None:  # DD-07
    out = clean_transactions(raw_sample)
    assert not out.duplicated().any()


def test_cleaning_report_counts(raw_sample: pd.DataFrame) -> None:
    rep = cleaning_report(raw_sample)
    # 2 genuine product rows survive (one duplicate + four rule-violations removed).
    assert rep.clean_rows == 2
    assert rep.cancellations == 1
    assert rep.duplicates == 1
    assert rep.missing_customer_kept == 1
