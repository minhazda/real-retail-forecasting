"""End-to-end evaluation: seasonal-naive(7) vs LightGBM on a time-ordered holdout.

Headline metric = % MAE improvement over the named baseline, per-series and
aggregated. Also reports how each method handles the structural Saturday closure.
All numbers come from this real run; results are written to docs/RESULTS.md.
"""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from real_retail.evaluate.metrics import (
    improvement_pct,
    mae,
    per_series_table,
    seasonal_naive_scale,
)
from real_retail.evaluate.split import TEST_DAYS_DEFAULT, time_split
from real_retail.features.build import build_features, feature_columns
from real_retail.models.baseline import seasonal_naive
from real_retail.models.lgbm import train_predict

PANEL = Path("data/processed/daily_top50.parquet")
RESULTS_MD = Path("docs/RESULTS.md")
METRICS_JSON = Path("reports/metrics.json")


def main() -> None:
    panel = pd.read_parquet(PANEL)
    panel["date"] = pd.to_datetime(panel["date"])

    # Baseline over the full panel (uses actual y[t-7]); attach to rows.
    panel = panel.sort_values(["StockCode", "date"]).reset_index(drop=True)
    panel["pred_baseline"] = seasonal_naive(panel).to_numpy()

    feats = build_features(panel)
    feature_cols = [c for c in feature_columns(feats) if c != "pred_baseline"]

    train, test = time_split(feats, TEST_DAYS_DEFAULT)
    test = test.dropna(subset=["pred_baseline"]).copy()

    # LightGBM (handles NaN lags natively); predictions clipped at 0.
    test["pred_model"] = train_predict(train, test, feature_cols)
    test = test.rename(columns={"quantity": "y_true"})

    # Per-series MASE scale from the in-sample (train) target.
    scales = {
        code: seasonal_naive_scale(g["quantity"].to_numpy())
        for code, g in train.groupby("StockCode", observed=True)
    }
    test["scale"] = test["StockCode"].map(scales).astype(float)
    test = test[test["scale"] > 0].copy()

    # ---- aggregated (pooled across all test points) ----
    mae_b = mae(test["y_true"], test["pred_baseline"])
    mae_m = mae(test["y_true"], test["pred_model"])
    agg_imp = improvement_pct(mae_b, mae_m)

    # ---- per-series ----
    ps = per_series_table(test).sort_values("improvement_pct", ascending=False)
    win_rate = float((ps["improvement_pct"] > 0).mean())

    # ---- Saturday closure handling ----
    sat = test[test["date"].dt.dayofweek == 5]
    nonsat = test[test["date"].dt.dayofweek != 5]
    sat_stats = {
        "saturday_actual_mean": float(sat["y_true"].mean()),
        "saturday_pred_baseline_mean": float(sat["pred_baseline"].mean()),
        "saturday_pred_model_mean": float(sat["pred_model"].mean()),
        "saturday_mae_baseline": mae(sat["y_true"], sat["pred_baseline"]),
        "saturday_mae_model": mae(sat["y_true"], sat["pred_model"]),
        "nonsat_mae_baseline": mae(nonsat["y_true"], nonsat["pred_baseline"]),
        "nonsat_mae_model": mae(nonsat["y_true"], nonsat["pred_model"]),
    }

    metrics = {
        "test_days": TEST_DAYS_DEFAULT,
        "test_start": str(test["date"].min().date()),
        "test_end": str(test["date"].max().date()),
        "n_series": int(test["StockCode"].nunique()),
        "n_test_points": int(len(test)),
        "pooled_mae_baseline": mae_b,
        "pooled_mae_model": mae_m,
        "pooled_improvement_pct": agg_imp,
        "median_series_improvement_pct": float(ps["improvement_pct"].median()),
        "series_win_rate": win_rate,
        "mean_mase_baseline": float(ps["mase_baseline"].mean()),
        "mean_mase_model": float(ps["mase_model"].mean()),
        **sat_stats,
    }

    _write_outputs(metrics, ps)
    print(json.dumps(metrics, indent=2))


def _write_outputs(metrics: dict, ps: pd.DataFrame) -> None:
    METRICS_JSON.parent.mkdir(parents=True, exist_ok=True)
    METRICS_JSON.write_text(json.dumps(metrics, indent=2), encoding="utf-8")

    m = metrics
    cols = ["StockCode", "mae_baseline", "mae_model", "improvement_pct"]
    top = _md_table(ps.head(5)[cols])
    worst = _md_table(ps.tail(3)[cols])
    lines = [
        "# Results",
        "",
        "_All numbers produced by `make eval` (`scripts/run_eval.py`) on a real run._",
        "",
        f"- Holdout: last **{m['test_days']} days** "
        f"({m['test_start']} → {m['test_end']}), time-ordered, no leakage.",
        f"- Series: **{m['n_series']}** top products, **{m['n_test_points']:,}** test points.",
        "",
        "## Headline — LightGBM vs seasonal-naive(7)",
        "",
        "| Metric | Seasonal-naive(7) | LightGBM |",
        "|---|---|---|",
        f"| Pooled MAE | {m['pooled_mae_baseline']:.3f} | {m['pooled_mae_model']:.3f} |",
        f"| Mean MASE | {m['mean_mase_baseline']:.3f} | {m['mean_mase_model']:.3f} |",
        "",
        f"**Pooled MAE improvement vs baseline: {m['pooled_improvement_pct']:+.1f}%**  ",
        f"Median per-series improvement: {m['median_series_improvement_pct']:+.1f}%  ",
        f"Series where model beats baseline: {m['series_win_rate']:.0%}",
        "",
        "## Saturday closure (the headline real-data effect)",
        "",
        "| | Actual | Seasonal-naive | LightGBM |",
        "|---|---|---|---|",
        f"| Mean Saturday units | {m['saturday_actual_mean']:.2f} | "
        f"{m['saturday_pred_baseline_mean']:.2f} | {m['saturday_pred_model_mean']:.2f} |",
        f"| Saturday MAE | — | {m['saturday_mae_baseline']:.3f} | "
        f"{m['saturday_mae_model']:.3f} |",
        f"| Non-Saturday MAE | — | {m['nonsat_mae_baseline']:.3f} | "
        f"{m['nonsat_mae_model']:.3f} |",
        "",
        "## Best / worst series (by MAE improvement)",
        "",
        top,
        "",
        worst,
        "",
    ]
    RESULTS_MD.parent.mkdir(parents=True, exist_ok=True)
    RESULTS_MD.write_text("\n".join(lines), encoding="utf-8")


def _md_table(df: pd.DataFrame) -> str:
    """Render a small DataFrame as a GitHub markdown table (no extra deps)."""
    header = "| " + " | ".join(df.columns) + " |"
    sep = "| " + " | ".join("---" for _ in df.columns) + " |"
    rows = [
        "| " + " | ".join(
            f"{v:.3f}" if isinstance(v, float) else str(v) for v in row
        ) + " |"
        for row in df.itertuples(index=False)
    ]
    return "\n".join([header, sep, *rows])


if __name__ == "__main__":
    main()
