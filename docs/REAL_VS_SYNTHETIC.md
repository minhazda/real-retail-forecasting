# Real data vs my synthetic generator

This repo is the real-data counterpart to
[`synthetic-retail-mlops-pipeline`](https://github.com/minhazda/synthetic-retail-mlops-pipeline).
That project proved the engineering on data I controlled; this one tests whether the same
discipline survives real, messy UK retail data. Below is where the real data **matched** the
assumptions baked into my synthetic generator and where it **broke** them — every claim is
backed by a measured number from this dataset.

## Lead finding — the 6-day trading week breaks the "7-day demand" assumption

My synthetic generator emits demand for **every calendar day** with a smooth weekly
seasonality. The real retailer **does not trade on Saturdays**: day-of-week means are
`Mon 19,561 … Fri 16,003, Sat 49, Sun 10,026`. In the 56-day holdout, the top-50 products
had a **mean Saturday demand of exactly 0.0**.

**What this taught me:** a generator that assumes 7 active days per week produces a series
that no amount of modelling on real data will match, because ~1/7 of the synthetic signal
lives on a day that is structurally empty in reality. The fix is to model the *trading
calendar* as a first-class input (here: an `is_saturday` flag + explicit zero days), not to
assume uniform weekly activity. Both seasonal-naive(7) and LightGBM nail the Saturday zero
(MAE 0.0); the model's entire **+26.3%** edge comes from non-Saturday trading days.

## Where the real data matched my synthetic assumptions

- **Strong weekly seasonality exists** — assumed, and confirmed: daily autocorr(lag-7) = 0.45,
  day-of-week CV = 0.51. Seasonal-naive(7) is a genuinely strong baseline, as the synthetic
  design anticipated.
- **A positive, right-skewed demand distribution** — broadly as modelled.

## Where the real data broke them

| Synthetic assumption | Real data | Evidence |
|---|---|---|
| Demand every calendar day | **Saturday is a structural closure** | Sat mean ≈ 0 vs ~20k weekday |
| Clean transactions only | 1.83% cancellations, 2.15% negative-qty | DD-01/DD-02 |
| Every sale has a customer id | **22.77% missing `CustomerID`** | DD-03 |
| Only sellable products | 4.12% of revenue in non-product codes (`POST`, `AMAZONFEE`, …) | DD-04 |
| No duplicate records | **33,663 exact duplicates** | DD-07 |
| Smooth per-product series | **Intermittent**: top-50 median 29.8% zero-days daily | EDA |
| Stationary-ish demand | **Strong pre-Christmas ramp** | holdout MASE 1.69 > 1 for the baseline |

The last row is subtle and important: because the Oct–Dec holdout sits on a rising
pre-Christmas trend, even the seasonal-naive baseline has **MASE 1.69 > 1** — the test period
is genuinely harder than in-sample. My synthetic generator's near-stationary demand never
created this regime, so it never stress-tested a model against a trending holdout. The
LightGBM model (MASE 1.41) closes part of that gap by using lag/rolling features, but does
not fully tame the ramp — an honest result, not a polished one.

## What I would change in the synthetic generator

1. Add a configurable **trading calendar** (closed days) instead of 7-day uniform demand.
2. Inject **data-quality noise** — cancellations, negative quantities, missing ids, duplicate
   rows, and service/adjustment line items — so downstream cleaning is exercised.
3. Make demand **non-stationary** (seasonal ramps), so models are tested on trending holdouts
   where the naive baseline's MASE exceeds 1.
4. Make per-product series **intermittent**, not smooth, to reflect real sparsity.
