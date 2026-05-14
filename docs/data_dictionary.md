# Data Dictionary

## `actual_clean.csv`

| Column | Description |
|---|---|
| `date` | Daily transaction or operating date |
| `units_sold` | Actual candles sold |
| `unit_cost` | Cost per candle for the day |
| `revenue` | Daily revenue |
| `total_cost` | Daily total cost |
| `profit` | Daily revenue minus daily total cost |
| `month` | Calendar month |
| `day_of_week` | Day name |
| `gross_margin` | Profit divided by revenue |
| `cost_phase` | Pre- or post-cost optimization period |
| `is_weekend` | True for Saturday or Sunday |
| `is_festival_window` | True for days around the modeled Diwali windows |

## `monthly_kpis.csv`

| Column | Description |
|---|---|
| `month` | Calendar month |
| `days` | Number of days in the month covered by data |
| `units` | Monthly actual units sold |
| `revenue` | Monthly actual revenue |
| `total_cost` | Monthly actual cost |
| `profit` | Monthly actual profit |
| `avg_daily_units` | Average units sold per day |
| `avg_daily_revenue` | Average daily revenue |
| `gross_margin` | Monthly profit divided by monthly revenue |
| `revenue_growth_pct` | Month-over-month revenue growth |

## `model_comparison.csv`

| Column | Description |
|---|---|
| `model` | Basic or Advanced |
| `forecast_units` | Total forecasted units |
| `forecast_revenue` | Total forecasted revenue |
| `forecast_profit` | Total forecasted profit |
| `unit_mae` | Mean absolute unit forecast error |
| `unit_rmse` | Root mean squared unit forecast error |
| `revenue_mape` | Mean absolute percentage revenue error |
| `revenue_bias_pct` | Total forecast revenue bias vs actual |

## `advanced_stress_test_forecast.csv`

| Column | Description |
|---|---|
| `volatility_factor` | Random demand volatility multiplier |
| `units_after_volatility` | Forecast units after volatility adjustment |
| `delay_flag` | 1 when a procurement or delivery disruption is simulated |
| `stress_units` | Units after delay impact |
| `stress_revenue_pre_delay` | Revenue before delivery disruption adjustment |
| `stress_revenue` | Revenue after delivery disruption adjustment |
| `stress_profit` | Profit after volatility and delivery adjustment |
| `lost_units_from_delay` | Units lost because of simulated delay |
| `revenue_at_risk_from_delay` | Revenue lost from delay impact |
