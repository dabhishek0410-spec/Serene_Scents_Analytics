# Dashboard Blueprint

This project is Power BI-ready. The processed CSV files in `data/processed/` can be loaded directly into Power BI, Tableau, Looker Studio, or a Python dashboard.

## Page 1: Executive Overview

Purpose: Give a founder, recruiter, or hiring manager a fast read on business performance.

Recommended visuals:

- KPI cards: revenue, profit, gross margin, units sold, average daily units, peak daily units.
- Monthly revenue and profit combo chart.
- Gross margin line chart with October cost optimization marker.
- Actual-vs-forecast revenue variance card.
- Short insight text box: "Margin expansion came from procurement improvement, not price increases."

## Page 2: Revenue and Profit Growth

Recommended visuals:

- Daily revenue and profit trend with 7-day moving average.
- Monthly revenue growth waterfall.
- Revenue by weekday vs weekend.
- Best and worst operating days table.

Business question: Is the business scaling profitably, or only growing revenue?

## Page 3: Forecast Performance

Recommended visuals:

- Actual revenue vs basic forecast vs advanced scenario by month.
- Daily unit forecast error distribution.
- Forecast bias KPI by model.
- MAE, RMSE, and MAPE cards.
- Calibration recommendation panel.

Business question: Which assumptions need to be updated before the next planning cycle?

## Page 4: Seasonality and Festival Demand

Recommended visuals:

- Seasonal demand heatmap by month and day of week.
- Festival-window revenue comparison.
- Weekend vs weekday demand cards.
- Diwali uplift annotation.

Business question: When should inventory and production be ramped up?

## Page 5: Operations and Risk

Recommended visuals:

- Delivery delay impact simulation.
- Revenue at risk from delay by month.
- Capacity pressure indicator: actual daily units vs modeled capacity.
- Raw material reorder-point table.

Business question: Which operational bottlenecks can prevent revenue capture?

## Suggested Power BI Measures

```DAX
Total Revenue = SUM(actual_clean[revenue])
Total Profit = SUM(actual_clean[profit])
Gross Margin = DIVIDE([Total Profit], [Total Revenue])
Total Units = SUM(actual_clean[units_sold])
Average Daily Units = AVERAGE(actual_clean[units_sold])
Revenue Growth % =
VAR CurrentRevenue = [Total Revenue]
VAR PreviousRevenue =
    CALCULATE([Total Revenue], DATEADD(actual_clean[date], -1, MONTH))
RETURN DIVIDE(CurrentRevenue - PreviousRevenue, PreviousRevenue)
```

## Dashboard Design Notes

- Keep the design executive-friendly: clean KPI cards, strong labels, and limited colors.
- Use annotations for October cost optimization and festival windows.
- Avoid overloading the first page; move model diagnostics to a dedicated forecast page.
- Use INR formatting consistently.
- Use variance colors only where they add interpretation.
