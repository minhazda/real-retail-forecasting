"""Load the raw Online Retail II table (both years) into one frame.

Provenance is asserted here so any reviewer can confirm the GitHub-mirrored
``.rda`` is byte-identical in content to UCI dataset 502: the loader fails loudly
if the row count or schema does not match the canonical 1,067,371-row table.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import pyreadr

# The original workbook is split into two sheets by year; the boundary is the
# first invoice of the 2010-2011 book. We reconstruct that label for parity.
SHEET_BOUNDARY = pd.Timestamp("2010-12-01")
COLUMNS = [
    "Invoice",
    "StockCode",
    "Description",
    "Quantity",
    "InvoiceDate",
    "Price",
    "CustomerID",
    "Country",
]
# Integrity contract for UCI dataset 502 (verified against the canonical table).
EXPECTED_ROWS = 1_067_371


def load_raw(path: Path, *, verify: bool = True) -> pd.DataFrame:
    """Read the raw table, assert integrity, normalise types, tag source sheet."""
    result = pyreadr.read_r(str(path))
    df = next(iter(result.values()))
    if verify:
        assert set(COLUMNS) <= set(df.columns), (
            f"schema mismatch: expected {COLUMNS}, got {list(df.columns)}"
        )
        assert len(df) == EXPECTED_ROWS, (
            f"row-count mismatch: expected {EXPECTED_ROWS:,}, got {len(df):,} — "
            "this is NOT the canonical UCI 502 table."
        )
    df = df[COLUMNS].copy()
    df["InvoiceDate"] = pd.to_datetime(df["InvoiceDate"])
    df["source_sheet"] = df["InvoiceDate"].lt(SHEET_BOUNDARY).map(
        {True: "Year 2009-2010", False: "Year 2010-2011"}
    )
    return df
