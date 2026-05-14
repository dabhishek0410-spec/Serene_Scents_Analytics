import pandas as pd
import numpy as np

# Timeline
dates = pd.date_range('2025-07-01', '2026-01-31', freq='D')
df = pd.DataFrame({'date': dates})
n = len(df)

# Growth
df['est_units_sold'] = np.geomspace(10, 130, n).round().astype(int)

# Pricing & cost
unit_cost = 129.70
price = 195.0

df['est_unit_cost'] = unit_cost
df.loc[df['date'] >= '2025-10-01', 'est_unit_cost'] = unit_cost * 0.85

# Financials
df['est_revenue'] = df['est_units_sold'] * price
df['est_total_cost'] = df['est_units_sold'] * df['est_unit_cost']
df['est_profit'] = df['est_revenue'] - df['est_total_cost']

# Export
df.to_csv('serene_scents_july_forecast_v3.csv', index=False)