# Technical Documentation

## Data Sources

| Source | Role |
|---|---|
| `data/raw/serene_scents_actual_growth.csv` | Daily actual units, revenue, cost, and profit |
| `data/raw/serene_scents_advanced_forecast.csv` | Advanced forecast with seasonality and festival boost |
| `src/basic_forecasting_model_original.py` | Original phase 1 forecasting script |
| `src/advanced_forecasting_model_original.py` | Original phase 2 forecasting script |
| `src/business_analysis_original.py` | Original business intelligence and volatility/delay analysis script |
| `notebooks/SereneScents_original.ipynb` | Original exploratory notebook |

The business plan reference established the original unit cost of INR 129.70, selling price of INR 195, approximate break-even of 30 candles per 50-unit production batch, and the rationale for pricing at roughly 1.5x production cost.

## Pipeline

Run:

```bash
python src/serene_scents_pipeline.py
```

The pipeline performs:

1. Actual data cleaning and column standardization.
2. Basic forecast rebuild using geometric daily unit growth.
3. Advanced forecast ingestion and margin calculation.
4. Stress-test simulation for volatility and procurement delay.
5. Daily actual-vs-forecast comparison.
6. Monthly KPI aggregation.
7. Festival, weekend, and cost-phase analysis.
8. Chart generation.

## Forecast Logic

### Basic Forecast

- Date range: 2025-07-01 to 2026-01-31
- Unit growth: geometric growth from 10 to 130 units per day
- Selling price: INR 195
- Initial unit cost: INR 129.70
- Optimized unit cost from October 2025: INR 110.245

### Advanced Forecast

- Base trend: linear demand growth from 10 to 130 units
- Weekly seasonality: sinusoidal weekly factor
- Monthly seasonality: sinusoidal monthly factor
- Festival boosts: 50% demand uplift around 2025-10-20 and 2025-11-01
- Capacity cap: 130 units in the original advanced forecast
- Cost optimization: 15% cost reduction from October 2025

### Stress-Test Extension

The portfolio pipeline adds a reproducible stress-test layer:

- Random seed: 42
- Volatility factor: normal distribution with 8% standard deviation
- Delivery delay probability: 5%
- Delay impact: 30% reduction in units on delayed days

This layer creates `advanced_stress_test_forecast.csv` and the `volatility_delay_impact.png` chart.

## KPI Definitions

| KPI | Definition |
|---|---|
| Revenue | Units sold multiplied by selling price |
| Total cost | Units sold multiplied by unit cost |
| Profit | Revenue minus total cost |
| Gross margin | Profit divided by revenue |
| Revenue growth | Current month revenue divided by prior month revenue minus 1 |
| Forecast bias | Forecast revenue minus actual revenue, divided by actual revenue |
| MAE | Average absolute unit forecast error |
| RMSE | Square root of average squared unit forecast error |
| MAPE | Average absolute percentage revenue error |
| Revenue at risk from delay | Units lost from simulated delay multiplied by selling price |

## Processed Outputs

| File | Purpose |
|---|---|
| `actual_clean.csv` | Cleaned actuals with month, margin, weekend, and festival flags |
| `basic_forecast_rebuilt.csv` | Recreated phase 1 forecast |
| `advanced_forecast_clean.csv` | Cleaned phase 2 forecast |
| `advanced_stress_test_forecast.csv` | Scenario data with volatility and delivery delay impact |
| `daily_forecast_comparison.csv` | Actual vs basic vs advanced daily comparison |
| `monthly_kpis.csv` | Monthly revenue, profit, margin, growth, and unit metrics |
| `model_comparison.csv` | Forecast accuracy and bias metrics |
| `festival_analysis.csv` | Festival vs non-festival demand comparison |
| `cost_phase_analysis.csv` | Pre- and post-cost optimization unit economics |

## Modeling Caveats

- The advanced model is a scenario model, not a fully calibrated statistical forecast.
- Daily MAPE is high because early-stage demand is volatile and small daily denominators can exaggerate percentage error.
- The actual data peaks at 100 units per day, while the advanced scenario assumes capacity can reach 130 units.
- SKU-level detail, marketing spend, customer repeat rates, and procurement lead-time records would improve accuracy.

## Recommended Next Technical Improvements

- Add rolling forecast recalibration every month.
- Track actual supplier lead times and stockout days.
- Build SKU-level product mix forecasting.
- Add confidence intervals or Monte Carlo simulation bands.
- Add a Power BI dashboard connected directly to `data/processed/`.
- Store data in SQL tables for repeatable reporting.
