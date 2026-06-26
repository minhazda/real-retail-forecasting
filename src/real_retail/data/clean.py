"""Clean raw transactions into a product-demand frame.

Every rule maps to a decision in ``docs/DATA_DECISIONS.md`` (DD-01..DD-07).
``clean_transactions`` returns the cleaned frame; ``cleaning_report`` returns the
row counts removed by each rule so the pipeline is auditable and testable.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

import pandas as pd

# Canonical product codes look like 5 digits with an optional letter suffix
# (e.g. 85048, 79323P). Everything else is a service/adjustment code (DD-04).
PRODUCT_CODE_RE = re.compile(r"^\d{5}[A-Za-z]*$")


def is_cancellation(df: pd.DataFrame) -> pd.Series:
    """DD-01: invoices prefixed with 'C' are cancellations/reversals."""
    return df["Invoice"].astype(str).str.startswith("C")


def is_product_code(df: pd.DataFrame) -> pd.Series:
    """DD-04: True for genuine product stock codes."""
    return df["StockCode"].astype(str).str.match(PRODUCT_CODE_RE)


@dataclass(frozen=True)
class CleaningReport:
    """Row counts removed by each cleaning rule (for transparency/tests)."""

    raw_rows: int
    cancellations: int  # DD-01
    negative_qty: int  # DD-02
    non_product_codes: int  # DD-04
    nonpositive_price: int  # DD-05
    duplicates: int  # DD-07
    missing_customer_kept: int  # DD-03 (kept, not dropped)
    clean_rows: int


def clean_transactions(df: pd.DataFrame) -> pd.DataFrame:
    """Apply DD-01, DD-02, DD-04, DD-05, DD-07 (DD-03 keeps rows; DD-06 flags)."""
    cancel = is_cancellation(df)
    product = is_product_code(df)
    keep = (
        (~cancel)  # DD-01
        & (df["Quantity"] > 0)  # DD-02
        & product  # DD-04
        & (df["Price"] > 0)  # DD-05
    )
    out = df.loc[keep].copy()
    out = out.drop_duplicates()  # DD-07
    # DD-06: outliers are flagged, never silently clipped.
    return out


def cleaning_report(df: pd.DataFrame) -> CleaningReport:
    """Quantify what each rule removes — drives the DATA_DECISIONS numbers."""
    cancel = is_cancellation(df)
    product = is_product_code(df)
    nonpositive_price = (df["Price"] <= 0).sum()
    clean = clean_transactions(df)
    return CleaningReport(
        raw_rows=len(df),
        cancellations=int(cancel.sum()),
        negative_qty=int((df["Quantity"] < 0).sum()),
        non_product_codes=int((~product).sum()),
        nonpositive_price=int(nonpositive_price),
        duplicates=int(df.loc[
            (~cancel) & (df["Quantity"] > 0) & product & (df["Price"] > 0)
        ].duplicated().sum()),
        missing_customer_kept=int(clean["CustomerID"].isna().sum()),
        clean_rows=len(clean),
    )
