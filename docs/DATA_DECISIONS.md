# Data-cleaning decision log

This is a first-class artifact, not buried in code. Every rule below has an ID that
the cleaning code references (`src/real_retail/data/clean.py`). All numbers are
**measured** on the full 1,067,371-row table by `scripts/build_dataset.py`
(`cleaning_report`), not cited from elsewhere.

| Stage | Rows |
|---|---|
| Raw | 1,067,371 |
| After cleaning (DD-01,02,04,05,07) | **1,003,214** |

---

## DD-00 (lead finding) — Saturday is a structural closure, not missing data

Daily day-of-week means (Mon→Sun): `19,561 / 20,462 / 19,353 / 22,397 / 16,003 / 49 / 10,026`.
**Saturdays are systematically ~0**: all 105 Saturdays exist in the calendar but carry
essentially no transactions — the retailer does not process Saturday orders.

- **Decision:** keep Saturdays as explicit zero-demand days in the panel and expose
  `is_saturday` to the model; do **not** drop them or treat them as gaps.
- **Rationale:** the zero is real signal, not absence. Seasonal-naive(7) encodes it for
  free (last Saturday was also ~0), and the model must learn it too.
- **Rejected alternative:** dropping Saturdays / reindexing to business days only — that
  would hide the single most distinctive feature of this dataset and make the model look
  better than it is on the days that actually matter.

This finding leads `docs/REAL_VS_SYNTHETIC.md`.

---

## DD-01 — Cancellations (`C`-prefixed invoices)

- **Measured:** 19,494 rows (1.83%).
- **Decision:** exclude from the demand series; report the rate separately.
- **Rationale:** cancellations are reversals, not demand. Netting them in would corrupt
  the forecasting target.
- **Rejected alternative:** keep them as negative demand — conflates returns with sales
  and double-counts against DD-02.

## DD-02 — Negative `Quantity`

- **Measured:** 22,950 rows (2.15%). **19,493 of the 19,494 cancellations are negative-qty**;
  that leaves ~3,457 negative-qty rows that are *not* cancellations (manual adjustments,
  damages, write-offs on non-`C` invoices).
- **Decision:** drop all non-positive quantities from the demand target.
- **Rationale:** negative quantity is never demand. The verified overlap with DD-01 is why
  both rules exist — cancellations and negative-qty are *correlated but not identical*.
- **Rejected alternative:** assume negative-qty ≡ cancellations and apply only DD-01 — would
  silently leak ~3,457 adjustment rows into the target.

## DD-03 — Missing `CustomerID` (~kept~)

- **Measured:** 22.77% of raw rows; 226,637 rows with missing `CustomerID` are **kept** in
  the cleaned demand set (22.59% of clean rows).
- **Decision:** **keep** these rows for demand forecasting.
- **Rationale:** demand aggregates over product × time; `CustomerID` is irrelevant to the
  target. Dropping ~23% of data would discard real sales for no modelling benefit.
- **Rejected alternative:** drop rows with missing `CustomerID` (common in RFM tutorials) —
  correct for a *customer-level* task, wrong here. The choice is task-dependent, and saying
  so is the honest position.

## DD-04 — Non-product stock codes

- **Measured:** 6,093 rows (0.57%), **4.12% of positive revenue**, 62 distinct codes.
  Examples: `POST`, `DOT` (postage, £322k), `M` (manual), `C2`, `D` (discount), `S`
  (samples), `BANK CHARGES`, `ADJUST`, `AMAZONFEE` (−£260k), plus small `DCGS*`/`gift_*`.
- **Decision:** keep only codes matching `^\d{5}[A-Za-z]*$` (5 digits + optional letter
  suffix); exclude everything else from the product-demand series.
- **Rationale:** these are fees/adjustments/services, not sellable products; they would
  inject non-demand volume and revenue. The regex allowlist is auditable.
- **Rejected alternative:** a hand-maintained blocklist of known junk codes — brittle as new
  service codes appear; an allowlist of the canonical product-code shape is more robust.

## DD-05 — Zero / negative `Price`

- **Measured:** 6,207 rows with non-positive price (0.58%); negative prices ≈ 0.00%.
- **Decision:** drop non-positive-price rows from the demand target.
- **Rationale:** zero-price rows are free samples / adjustments, not paid demand.
- **Rejected alternative:** impute a price — invents revenue and demand that did not occur.

## DD-06 — Outliers (flag, do not clip)

- **Decision:** do **not** blanket-clip extreme quantities; keep them, and let the model see
  rolling/lag context. Outliers are surfaced, not silently removed.
- **Rationale:** large bulk/B2B orders are *real* demand. Clipping would fabricate a
  smoother series than reality.
- **Rejected alternative:** winsorise at a fixed percentile by default — would improve
  metrics cosmetically while hiding genuine demand spikes.

## DD-07 — Exact duplicate rows

- **Measured:** 33,663 exact duplicates removed (within the otherwise-kept rows).
- **Decision:** drop exact duplicates after the other filters.
- **Rationale:** identical (invoice, code, qty, price, timestamp) rows are data-entry
  artifacts that would inflate demand.
- **Rejected alternative:** keep them — biases high-volume timestamps upward.

---

### Note on the modelling universe

After cleaning, the panel is restricted to the **top-50 products by total quantity** at
**daily** grain (see the EDA: daily per-product demand is intermittent — top-50 median
29.8% zero-days — and weekly would strip the day-of-week signal that makes seasonal-naive(7)
a meaningful baseline). One of the 50 series is excluded from MASE because its in-sample
seasonal-naive scale is zero (undefined MASE), leaving **49 series** in the headline metrics.
