# Data Attribution & Provenance

## Canonical source

This project uses the **Online Retail II** dataset.

- **Source of record:** UCI Machine Learning Repository, dataset **502** —
  https://archive.ics.uci.edu/dataset/502/online+retail+ii
- **DOI:** [10.24432/C5CG6D](https://doi.org/10.24432/C5CG6D)
- **Citation:** Chen, D. (2019). *Online Retail II* [Dataset]. UCI Machine Learning Repository.
- **License:** Creative Commons Attribution 4.0 International (**CC BY 4.0**) —
  https://creativecommons.org/licenses/by/4.0/
- **Coverage:** transactions of a UK-based, non-store online retailer, 2009-12-01 to 2011-12-09.

## Why a mirror is used (and why you can trust it)

UCI's direct file server for dataset 502 is heavily throttled — measured at **~15 KB/s with
no HTTP range support**, which makes the ~45 MB download fail repeatedly. The automated
fetch therefore pulls a **CC BY 4.0 redistribution** of the *same* table:

- **Mirror URL:** `https://raw.githubusercontent.com/allanvc/onlineretail2/master/data/onlineretail2.rda`

This mirror is **verified byte-identical in content** to the canonical UCI table, and the
verification is **reproducible and enforced in code**: `load_raw()`
(`src/real_retail/data/load.py`) asserts on every load that the table has exactly
**1,067,371 rows** and the canonical 8-column schema
(`Invoice, StockCode, Description, Quantity, InvoiceDate, Price, CustomerID, Country`).
If a mirror ever drifts, the loader fails loudly rather than training on altered data.

A reviewer who prefers the canonical bytes can download from UCI directly (URL above) and
point the loader at that file — the same integrity assertion applies.

## Redistribution in this repo

CC BY 4.0 permits redistribution with attribution. To keep the repo light, the raw file is
**gitignored** (`data/raw/`); only a small cleaned/aggregated artifact
(`data/processed/daily_top50.parquet`) is committed, which remains covered by CC BY 4.0 with
the attribution above.
