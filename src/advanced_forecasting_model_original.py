import pandas as pd
import numpy as np

# 1. Timeline Setup
date_rng = pd.date_range(start='2025-07-01', end='2026-01-31', freq='D')
forecast_df = pd.DataFrame(date_rng, columns=['date'])
n_days = len(forecast_df)

# 2. Base growth (trend)
trend = np.linspace(10, 130, n_days)
weekly = 1 + 0.2 * np.sin(2 * np.pi * np.arange(n_days) / 7)
monthly = 1 + 0.15 * np.sin(2 * np.pi * np.arange(n_days) / 30)
noise = np.random.normal(0, 5, n_days)
forecast_df['est_units_sold'] = (
    trend * weekly * monthly + noise
).clip(0).round().astype(int)

# Define key dates
festival_dates = ['2025-10-20', '2025-11-01']  # Diwali period
forecast_df['festival_boost'] = 1.0

for date in festival_dates:
    forecast_df.loc[
        (forecast_df['date'] >= pd.to_datetime(date) - pd.Timedelta(days=3)) &
        (forecast_df['date'] <= pd.to_datetime(date) + pd.Timedelta(days=3)),
        'festival_boost'
    ] = 1.5  # 50% demand spike

forecast_df['est_units_sold'] = (
    forecast_df['est_units_sold'] * forecast_df['festival_boost']
).round().astype(int)

# Cap demand at max capacity (130 units)
forecast_df['est_units_sold'] = forecast_df['est_units_sold'].clip(upper=130)   

# 3. Parameters from the Financial Plan
unit_cost_initial = 129.70 # Baseline from doc
selling_price = 195.0      # 1.5x margin rule

# 4. Strategic Cost Reduction (Targeted for Oct 2025)
forecast_df['est_unit_cost'] = unit_cost_initial
forecast_df.loc[forecast_df['date'] >= '2025-10-01', 'est_unit_cost'] = unit_cost_initial * 0.85

# 5. Financial Projections
forecast_df['est_revenue'] = forecast_df['est_units_sold'] * selling_price
forecast_df['est_total_cost'] = forecast_df['est_units_sold'] * forecast_df['est_unit_cost']
forecast_df['est_profit'] = forecast_df['est_revenue'] - forecast_df['est_total_cost']

# 6. Save the final forecast
forecast_df.to_csv('serene_scents_july_realworld.csv', index=False)
