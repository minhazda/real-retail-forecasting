"""Build the committed processed artifact: cleaned daily top-50 demand panel.

Also prints the cleaning report (measured numbers used in docs/DATA_DECISIONS.md).
"""

from __future__ import annotations

from pathlib import Path

from real_retail.data.aggregate import daily_panel
from real_retail.data.clean import clean_transactions, cleaning_report
from real_retail.data.download import RAW_DIR, RDA_NAME, download_raw
from real_retail.data.load import load_raw

OUT = Path("data/processed/daily_top50.parquet")


def main() -> None:
    raw_path = RAW_DIR / RDA_NAME
    if not raw_path.exists():
        raw_path = download_raw()
    raw = load_raw(raw_path)

    rep = cleaning_report(raw)
    print("=== cleaning report (measured) ===")
    for k, v in rep.__dict__.items():
        print(f"{k:24s} {v:,}")
    print(f"missing_customer_pct      {rep.missing_customer_kept / rep.clean_rows:.2%}")

    clean = clean_transactions(raw)
    panel = daily_panel(clean, n=50)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    panel.to_parquet(OUT, index=False)
    print(f"\nwrote {OUT}  rows={len(panel):,}  products={panel['StockCode'].nunique()}  "
          f"dates={panel['date'].min().date()}..{panel['date'].max().date()}")


if __name__ == "__main__":
    main()
