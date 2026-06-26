"""Phase-1 EDA: measured data-quality + series-shape findings (no cleaning yet)."""

from __future__ import annotations

import re

import numpy as np
import pandas as pd

from real_retail.data.download import RAW_DIR, RDA_NAME
from real_retail.data.load import load_raw

PRODUCT_CODE_RE = re.compile(r"^\d{5}[A-Za-z]*$")  # canonical product codes


def main() -> None:
    df = load_raw(RAW_DIR / RDA_NAME)
    n = len(df)
    print("\n=== ONLINE RETAIL II — EDA (raw, concatenated) ===")
    print(f"rows={n:,}  cols={list(df.columns)}")
    print(f"date_range={df['InvoiceDate'].min()} -> {df['InvoiceDate'].max()}")

    # --- missing CustomerID ---
    miss_cust = df["CustomerID"].isna().mean()
    print(f"\nmissing_CustomerID_pct = {miss_cust:.2%}")

    # --- cancellations (C-prefixed invoices) ---
    inv = df["Invoice"].astype(str)
    is_cancel = inv.str.startswith("C")
    print(f"cancellation_rows_pct  = {is_cancel.mean():.2%}")
    print(f"negative_quantity_pct  = {(df['Quantity'] < 0).mean():.2%}")
    print(f"  overlap cancel&negqty = {(is_cancel & (df['Quantity'] < 0)).sum():,} "
          f"of {is_cancel.sum():,} cancel rows")
    print(f"zero_price_pct         = {(df['Price'] == 0).mean():.2%}")
    print(f"negative_price_pct     = {(df['Price'] < 0).mean():.2%}")

    # --- junk / non-product stock codes ---
    df["_code"] = df["StockCode"].astype(str)
    df["_revenue"] = df["Quantity"] * df["Price"]
    total_rev = df.loc[df["_revenue"] > 0, "_revenue"].sum()
    is_junk = ~df["_code"].str.match(PRODUCT_CODE_RE)
    junk = df[is_junk]
    junk_codes = (
        junk.groupby("_code")
        .agg(rows=("_code", "size"), revenue=("_revenue", "sum"))
        .sort_values("rows", ascending=False)
    )
    print(f"\nnon_product_code_rows_pct = {is_junk.mean():.2%}  "
          f"(distinct junk codes = {junk['_code'].nunique()})")
    print(f"junk_revenue_share = {junk.loc[junk['_revenue']>0,'_revenue'].sum()/total_rev:.2%} "
          f"of positive revenue")
    print("top non-product codes (rows | revenue):")
    for code, row in junk_codes.head(15).iterrows():
        print(f"   {code:<14} rows={int(row['rows']):>6}  revenue={row['revenue']:>12,.0f}")

    # --- duplicates ---
    dup = df.drop(columns=["source_sheet", "_code", "_revenue"]).duplicated().sum()
    print(f"\nexact_duplicate_rows = {dup:,} ({dup/n:.2%})")

    # --- build a cleaned-ish demand frame for series-shape analysis ---
    demand = df[
        (~is_cancel)
        & (df["Quantity"] > 0)
        & (df["Price"] > 0)
        & (~is_junk)
    ].copy()
    demand["date"] = demand["InvoiceDate"].dt.normalize()
    print(f"\nrows_after_basic_demand_filter = {len(demand):,} "
          f"({len(demand)/n:.1%} of raw)")
    print(f"distinct_products = {demand['StockCode'].nunique():,}")

    # --- intermittency at product-day and product-week grain ---
    for grain, freq in [("daily", "D"), ("weekly", "W")]:
        g = (
            demand.assign(period=demand["date"].dt.to_period("W" if freq == "W" else "D"))
            .groupby(["StockCode", "period"])["Quantity"].sum()
        )
        # top-50 products by total quantity
        top = demand.groupby("StockCode")["Quantity"].sum().nlargest(50).index
        gt = g[g.index.get_level_values(0).isin(top)]
        # reindex each top product across full span to expose zero periods
        span = pd.period_range(demand["date"].min(), demand["date"].max(),
                               freq="W" if freq == "W" else "D")
        zero_frac = []
        for sc in top:
            s = gt.loc[sc].reindex(span, fill_value=0)
            zero_frac.append((s == 0).mean())
        print(f"intermittency_{grain}_top50: mean_zero_period_pct = "
              f"{np.mean(zero_frac):.1%}  median = {np.median(zero_frac):.1%}")

    # --- weekly seasonality strength on total daily demand ---
    daily_total = demand.groupby("date")["Quantity"].sum().asfreq("D", fill_value=0)
    lag7 = daily_total.autocorr(lag=7)
    lag1 = daily_total.autocorr(lag=1)
    dow = daily_total.groupby(daily_total.index.dayofweek).mean()
    dow_cv = dow.std() / dow.mean()
    print(f"\nweekly_seasonality: autocorr_lag7 = {lag7:.3f}  autocorr_lag1 = {lag1:.3f}")
    print(f"day_of_week_profile_CV = {dow_cv:.3f}  (0=flat week, higher=stronger weekly pattern)")
    print("dow_mean (Mon..Sun):", [f"{v:,.0f}" for v in dow.values])
    # Saturdays present?
    print(f"days_with_data = {daily_total.shape[0]}  "
          f"weekday_counts(0..6) = {np.bincount(daily_total.index.dayofweek)}")


if __name__ == "__main__":
    main()
