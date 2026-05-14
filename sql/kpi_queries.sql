-- Serene Scents KPI query examples.
-- Assumes a table named serene_scents_actuals with columns:
-- date, units_sold, unit_cost, revenue, total_cost, profit

-- 1. Executive KPI summary
SELECT
    COUNT(*) AS operating_days,
    SUM(units_sold) AS total_units_sold,
    SUM(revenue) AS total_revenue,
    SUM(profit) AS total_profit,
    SUM(profit) / NULLIF(SUM(revenue), 0) AS gross_margin,
    AVG(units_sold) AS avg_daily_units,
    MAX(units_sold) AS peak_daily_units
FROM serene_scents_actuals;

-- 2. Monthly revenue, profit, and margin
SELECT
    DATE_TRUNC('month', date) AS month,
    SUM(units_sold) AS units,
    SUM(revenue) AS revenue,
    SUM(total_cost) AS total_cost,
    SUM(profit) AS profit,
    SUM(profit) / NULLIF(SUM(revenue), 0) AS gross_margin
FROM serene_scents_actuals
GROUP BY 1
ORDER BY 1;

-- 3. Pre- and post-cost optimization margin
SELECT
    CASE
        WHEN date < DATE '2025-10-01' THEN 'Pre cost optimization'
        ELSE 'Post cost optimization'
    END AS cost_phase,
    SUM(units_sold) AS units,
    SUM(revenue) AS revenue,
    SUM(profit) AS profit,
    AVG(unit_cost) AS avg_unit_cost,
    SUM(profit) / NULLIF(SUM(revenue), 0) AS gross_margin
FROM serene_scents_actuals
GROUP BY 1
ORDER BY 1;

-- 4. Weekend vs weekday demand
SELECT
    CASE
        WHEN EXTRACT(DOW FROM date) IN (0, 6) THEN 'Weekend'
        ELSE 'Weekday'
    END AS day_type,
    AVG(units_sold) AS avg_daily_units,
    AVG(revenue) AS avg_daily_revenue,
    SUM(revenue) AS total_revenue
FROM serene_scents_actuals
GROUP BY 1;

-- 5. Festival-window demand
SELECT
    CASE
        WHEN date BETWEEN DATE '2025-10-17' AND DATE '2025-10-23'
          OR date BETWEEN DATE '2025-10-29' AND DATE '2025-11-04'
        THEN 'Festival window'
        ELSE 'Non-festival window'
    END AS demand_period,
    COUNT(*) AS days,
    AVG(units_sold) AS avg_daily_units,
    AVG(revenue) AS avg_daily_revenue,
    SUM(revenue) AS total_revenue,
    SUM(profit) AS total_profit
FROM serene_scents_actuals
GROUP BY 1;

-- 6. Forecast model comparison.
-- Assumes a table named serene_scents_forecast_comparison with actual and forecast columns.
SELECT
    SUM(revenue) AS actual_revenue,
    SUM(basic_revenue) AS basic_revenue,
    SUM(advanced_revenue) AS advanced_revenue,
    (SUM(basic_revenue) - SUM(revenue)) / NULLIF(SUM(revenue), 0) AS basic_revenue_bias_pct,
    (SUM(advanced_revenue) - SUM(revenue)) / NULLIF(SUM(revenue), 0) AS advanced_revenue_bias_pct,
    AVG(ABS(basic_units - units_sold)) AS basic_unit_mae,
    AVG(ABS(advanced_units - units_sold)) AS advanced_unit_mae
FROM serene_scents_forecast_comparison;
