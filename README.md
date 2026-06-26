# real-retail-forecasting

[![CI](https://github.com/minhazda/real-retail-forecasting/actions/workflows/ci.yml/badge.svg)](https://github.com/minhazda/real-retail-forecasting/actions/workflows/ci.yml)

Daily product-level **demand forecasting on real UK online-retail transactions**
([UCI Online Retail II](https://archive.ics.uci.edu/dataset/502/online+retail+ii), CC BY 4.0) —
built to the same typed / tested / CI engineering bar as my synthetic pipeline.

## Portfolio thesis

This repo is the **real-data counterpart** to
[**synthetic-retail-mlops-pipeline**](https://github.com/minhazda/synthetic-retail-mlops-pipeline).

> The synthetic pipeline proved the engineering on data I controlled.
> **This repo proves that discipline survives contact with real, messy UK retail data** —
> and documents exactly where the real data broke the assumptions baked into my synthetic
> generator (see [`docs/REAL_VS_SYNTHETIC.md`](docs/REAL_VS_SYNTHETIC.md)).

The two repos are meant to be read as a pair: engineering rigor *and* honest handling of
real-world mess.

## Headline result

Time-ordered 56-day holdout (2011-10-15 → 2011-12-09), 49 top products, 2,744 test points.
**Every number comes from a real run** (`make eval`) — see [`docs/RESULTS.md`](docs/RESULTS.md).

| Metric | Seasonal-naive(7) | LightGBM | |
|---|---|---|---|
| Pooled MAE | 79.03 | **58.26** | **+26.3%** |
| Mean MASE | 1.69 | **1.41** | |
| Series beaten | — | **47 / 49 (96%)** | |

**The Saturday story (the headline real-data finding):** the retailer doesn't trade on
Saturdays — daily demand means run `~20k` Mon–Fri but **`~0` on Saturday**. Both methods nail
the structural Saturday zero (MAE `0.0`); the model's entire **+26.3%** edge therefore comes
from real trading days. The holdout sits on the pre-Christmas ramp, so even the baseline has
**MASE 1.69 > 1** — a genuinely hard, non-stationary test window, not a soft one.

## What makes this a "real data" project

Measured on the full 1,067,371-row table (not cited estimates) — full log in
[`docs/DATA_DECISIONS.md`](docs/DATA_DECISIONS.md):

- **22.77%** missing `CustomerID` (kept — irrelevant to demand; DD-03)
- **1.83%** cancellations + **2.15%** negative quantities (dropped; DD-01/02)
- **4.12% of revenue** in non-product codes — `POST`, `AMAZONFEE`, `BANK CHARGES`… (DD-04)
- **33,663** exact duplicate rows (DD-07)
- **Intermittent** per-product demand (top-50 median 29.8% zero-days) + the Saturday closure

Each cleaning decision is logged with its **rationale and the alternative I rejected**, and
the cleaning code references the decision IDs.

## Quickstart

```bash
python -m venv .venv && . .venv/Scripts/activate   # or source .venv/bin/activate
pip install -e ".[dev]"

make data        # download raw -> data/raw/ (gitignored)
make clean-data  # cleaned daily top-50 panel -> data/processed/ (committed)
make eval        # train baseline + LightGBM, write docs/RESULTS.md
make all         # ruff + mypy + pytest
```

The committed `data/processed/daily_top50.parquet` lets you run `make eval` without the
download. Raw data is fetched on demand and gitignored.

## Project layout

```
src/real_retail/
  data/      download, load (asserts integrity), clean (DD-rules), aggregate
  features/  leakage-safe calendar + lag/rolling builders
  models/    seasonal-naive(7) baseline, global LightGBM
  evaluate/  time-ordered split, MAE / MASE
scripts/     download_data, build_dataset, eda, run_eval
docs/        DATA_DECISIONS.md, REAL_VS_SYNTHETIC.md, RESULTS.md
tests/       cleaning rules, no-leakage split, MASE math, baseline behaviour
```

## Data provenance (airtight)

Canonical source: **UCI dataset 502**, DOI [10.24432/C5CG6D](https://doi.org/10.24432/C5CG6D),
**CC BY 4.0**. UCI's direct server is throttled to ~15 KB/s with no range support, so the
loader fetches a CC BY 4.0 redistribution of the *same* table and **asserts it is byte-
identical in content** (exactly 1,067,371 rows + canonical schema) on every load. Full
detail in [`ATTRIBUTION.md`](ATTRIBUTION.md).

## Why serving (FastAPI / Docker) is scoped out

Deliberately. Model serving, containerisation, and the deployment surface are already
demonstrated in
[synthetic-retail-mlops-pipeline](https://github.com/minhazda/synthetic-retail-mlops-pipeline).
This repo's job is the part that pipeline *can't* show: surviving real, messy data with a
documented, defensible cleaning and evaluation process. Keeping the scope tight is the point.

## License

Code: MIT. Data: CC BY 4.0 (UCI), see `ATTRIBUTION.md`.
