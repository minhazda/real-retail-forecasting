# Results

_All numbers produced by `make eval` (`scripts/run_eval.py`) on a real run._

- Holdout: last **56 days** (2011-10-15 → 2011-12-09), time-ordered, no leakage.
- Series: **49** top products, **2,744** test points.

## Headline — LightGBM vs seasonal-naive(7)

| Metric | Seasonal-naive(7) | LightGBM |
|---|---|---|
| Pooled MAE | 79.028 | 58.259 |
| Mean MASE | 1.695 | 1.413 |

**Pooled MAE improvement vs baseline: +26.3%**  
Median per-series improvement: +29.6%  
Series where model beats baseline: 96%

## Saturday closure (the headline real-data effect)

| | Actual | Seasonal-naive | LightGBM |
|---|---|---|---|
| Mean Saturday units | 0.00 | 0.00 | 0.00 |
| Saturday MAE | — | 0.000 | 0.000 |
| Non-Saturday MAE | — | 92.199 | 67.969 |

## Best / worst series (by MAE improvement)

| StockCode | mae_baseline | mae_model | improvement_pct |
| --- | --- | --- | --- |
| 16014 | 131.107 | 66.435 | 49.328 |
| 84568 | 38.875 | 21.985 | 43.448 |
| 85099F | 49.125 | 28.253 | 42.487 |
| 21915 | 172.214 | 101.265 | 41.198 |
| 21232 | 61.214 | 36.264 | 40.760 |

| StockCode | mae_baseline | mae_model | improvement_pct |
| --- | --- | --- | --- |
| 20724 | 49.625 | 44.227 | 10.879 |
| 23084 | 399.589 | 406.987 | -1.851 |
| 22355 | 47.071 | 55.522 | -17.952 |
