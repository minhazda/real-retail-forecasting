-- ============================================================================
-- demand_analysis.sql  —  Online Retail II demand analysis in pure SQL (DuckDB)
-- ============================================================================
--
-- WHY THIS FILE EXISTS
--   The Python pipeline derives the project's headline findings (the structural
--   Saturday closure, intermittent per-product demand, the pre-Christmas ramp).
--   This file reproduces those same findings directly in SQL, so the analysis is
--   verifiable in two independent stacks — and demonstrates window functions,
--   aggregation, date logic, and regex-based cleaning.
--
-- HOW TO RUN  (no download needed — queries the committed processed panel)
--   pip install duckdb            # or: brew install duckdb
--   duckdb -c ".read sql/demand_analysis.sql"
--   # or:  duckdb < sql/demand_analysis.sql
--
-- DATA
--   Section A runs against data/processed/daily_top50.parquet (committed):
--     StockCode (VARCHAR) · date (DATE) · quantity (DOUBLE)
--     A complete daily panel for the top-50 products with explicit zeros for
--     non-trading days (including the Saturday closure) — gaps are real signal.
--   Section B is an illustrative reference against the raw 8-column UCI table
--   (Invoice, StockCode, Description, Quantity, InvoiceDate, Price, CustomerID,
--   Country); it mirrors the DD-01..DD-07 rules in src/real_retail/data/clean.py.
-- ============================================================================


-- ====================  SECTION A — runnable on the parquet  ==================

CREATE OR REPLACE VIEW panel AS
SELECT
    CAST(StockCode AS VARCHAR) AS stock_code,
    CAST(date AS DATE)         AS d,
    CAST(quantity AS DOUBLE)   AS qty
FROM read_parquet('data/processed/daily_top50.parquet');


-- A0 · Panel shape — sanity check that the integrity contract held.
SELECT
    COUNT(*)                       AS rows,
    COUNT(DISTINCT stock_code)     AS products,
    MIN(d)                         AS first_day,
    MAX(d)                         AS last_day,
    COUNT(DISTINCT d)              AS calendar_days
FROM panel;


-- A1 · THE SATURDAY STORY (headline finding).
-- Mean daily demand collapses to ~0 on Saturdays: the retailer doesn't trade
-- Saturdays, so both the model and the baseline nail this structural zero and
-- the model's +26.3% MAE edge comes entirely from real trading days.
SELECT
    dayname(d)                          AS weekday,
    ROUND(AVG(qty), 2)                  AS avg_qty,
    ROUND(SUM(qty), 0)                  AS total_qty,
    ROUND(100.0 * AVG(CASE WHEN qty = 0 THEN 1 ELSE 0 END), 1) AS pct_zero_days
FROM panel
GROUP BY weekday, isodow(d)
ORDER BY isodow(d);


-- A2 · INTERMITTENT DEMAND — per-product zero-day rate, then the cross-product
-- median (the README reports a ~29.8% median zero-day rate for the top-50).
WITH per_product AS (
    SELECT
        stock_code,
        AVG(CASE WHEN qty = 0 THEN 1.0 ELSE 0.0 END) AS zero_rate
    FROM panel
    GROUP BY stock_code
)
SELECT
    ROUND(100.0 * MEDIAN(zero_rate), 1) AS median_pct_zero_days,
    ROUND(100.0 * MIN(zero_rate), 1)    AS min_pct_zero_days,
    ROUND(100.0 * MAX(zero_rate), 1)    AS max_pct_zero_days
FROM per_product;


-- A3 · TOP PRODUCTS by total quantity (the panel's demand leaders).
SELECT
    stock_code,
    ROUND(SUM(qty), 0)              AS total_qty,
    ROUND(AVG(qty), 2)             AS avg_daily_qty
FROM panel
GROUP BY stock_code
ORDER BY total_qty DESC
LIMIT 10;


-- A4 · DEMAND CONCENTRATION (Pareto) — cumulative share of the top products,
-- via a window over the product totals.
WITH totals AS (
    SELECT stock_code, SUM(qty) AS total_qty
    FROM panel GROUP BY stock_code
),
ranked AS (
    SELECT
        stock_code,
        total_qty,
        ROW_NUMBER() OVER (ORDER BY total_qty DESC)                       AS rnk,
        SUM(total_qty) OVER (ORDER BY total_qty DESC
                             ROWS UNBOUNDED PRECEDING)                    AS cum_qty,
        SUM(total_qty) OVER ()                                            AS grand_total
    FROM totals
)
SELECT
    rnk,
    stock_code,
    ROUND(total_qty, 0)                          AS total_qty,
    ROUND(100.0 * cum_qty / grand_total, 1)      AS cum_pct_of_demand
FROM ranked
WHERE rnk <= 10
ORDER BY rnk;


-- A5 · MONTHLY DEMAND TREND — the pre-Christmas ramp that makes the 56-day
-- holdout (Oct–Dec 2011) a genuinely non-stationary, hard test window.
SELECT
    date_trunc('month', d)         AS month,
    ROUND(SUM(qty), 0)             AS total_qty,
    ROUND(AVG(qty), 2)             AS avg_daily_qty
FROM panel
GROUP BY month
ORDER BY month;


-- A6 · 7-DAY ROLLING MEAN per product (the SQL analogue of the lag/rolling
-- features the model uses). Shown for the single highest-volume product.
WITH leader AS (
    SELECT stock_code
    FROM panel GROUP BY stock_code
    ORDER BY SUM(qty) DESC LIMIT 1
)
SELECT
    p.d,
    p.qty,
    ROUND(AVG(p.qty) OVER (
        PARTITION BY p.stock_code ORDER BY p.d
        ROWS BETWEEN 6 PRECEDING AND CURRENT ROW
    ), 2)                          AS qty_roll7
FROM panel p
JOIN leader USING (stock_code)
ORDER BY p.d
LIMIT 30;


-- A7 · DEMAND VOLATILITY — coefficient of variation per product (a proxy for
-- how hard each series is to forecast). High CV = spiky/intermittent.
SELECT
    stock_code,
    ROUND(AVG(qty), 2)                                     AS mean_qty,
    ROUND(STDDEV_SAMP(qty), 2)                             AS sd_qty,
    ROUND(STDDEV_SAMP(qty) / NULLIF(AVG(qty), 0), 2)       AS coef_var
FROM panel
GROUP BY stock_code
HAVING AVG(qty) > 0
ORDER BY coef_var DESC
LIMIT 10;


-- ============  SECTION B — illustrative reference on the RAW table  ==========
-- The raw source ships as an .rda (read via pyreadr), so these don't run
-- against the repo as-is; they document how the DD-01..DD-07 cleaning rules and
-- standard customer analytics look in SQL. Point a view at the raw table after
-- exporting it to parquet to execute them.
--
--   CREATE VIEW raw AS SELECT * FROM read_parquet('data/raw/online_retail_ii.parquet');
--
-- B1 · Cleaning funnel — replicates clean.py / docs/DATA_DECISIONS.md in SQL.
--   SELECT
--       COUNT(*)                                                          AS raw_rows,
--       SUM(CASE WHEN Invoice LIKE 'C%' THEN 1 ELSE 0 END)                AS cancellations,      -- DD-01
--       SUM(CASE WHEN Quantity <= 0 THEN 1 ELSE 0 END)                    AS nonpositive_qty,    -- DD-02
--       SUM(CASE WHEN NOT regexp_full_match(CAST(StockCode AS VARCHAR),
--                 '^\d{5}[A-Za-z]*$') THEN 1 ELSE 0 END)                  AS non_product_codes,  -- DD-04
--       SUM(CASE WHEN Price <= 0 THEN 1 ELSE 0 END)                       AS nonpositive_price,  -- DD-05
--       SUM(CASE WHEN CustomerID IS NULL THEN 1 ELSE 0 END)               AS missing_customer    -- DD-03 (kept)
--   FROM raw;
--
-- B2 · Revenue by country (post-clean).
--   SELECT Country,
--          ROUND(SUM(Quantity * Price), 0)        AS revenue,
--          COUNT(DISTINCT Invoice)                AS orders
--   FROM raw
--   WHERE Invoice NOT LIKE 'C%' AND Quantity > 0 AND Price > 0
--     AND regexp_full_match(CAST(StockCode AS VARCHAR), '^\d{5}[A-Za-z]*$')
--   GROUP BY Country
--   ORDER BY revenue DESC
--   LIMIT 15;
--
-- B3 · RFM customer segmentation (Recency / Frequency / Monetary, quintiles).
--   WITH tx AS (
--       SELECT CustomerID, Invoice, InvoiceDate, Quantity * Price AS revenue
--       FROM raw
--       WHERE Invoice NOT LIKE 'C%' AND Quantity > 0 AND Price > 0
--         AND regexp_full_match(CAST(StockCode AS VARCHAR), '^\d{5}[A-Za-z]*$')
--         AND CustomerID IS NOT NULL
--   ),
--   agg AS (
--       SELECT CustomerID,
--              date_diff('day', MAX(InvoiceDate), DATE '2011-12-10') AS recency_days,
--              COUNT(DISTINCT Invoice)                               AS frequency,
--              SUM(revenue)                                          AS monetary
--       FROM tx GROUP BY CustomerID
--   )
--   SELECT CustomerID, recency_days, frequency, ROUND(monetary, 2) AS monetary,
--          NTILE(5) OVER (ORDER BY recency_days DESC) AS r_score,   -- recent = high
--          NTILE(5) OVER (ORDER BY frequency)         AS f_score,
--          NTILE(5) OVER (ORDER BY monetary)          AS m_score
--   FROM agg
--   ORDER BY monetary DESC
--   LIMIT 20;
-- ============================================================================
