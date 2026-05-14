# Business Case Presentation Outline

## Slide 1: Title

Serene Scents: Business Analytics and Forecasting Case Study

Subtitle: Revenue growth, unit economics, seasonality, and operational risk for an early-stage candle venture.

## Slide 2: Business Context

- Handmade scented candle and home fragrance venture.
- Demand influenced by gifting, festivals, weekends, pricing, and production capacity.
- Analysis period: July 2025 to January 2026.
- Founder needed better forecasting for production, procurement, and cash planning.

## Slide 3: Business Objective

- Track revenue and profitability progression.
- Identify seasonal demand patterns.
- Evaluate forecast model evolution.
- Quantify procurement and delay risks.
- Convert insights into founder decisions.

## Slide 4: Data and Model Inputs

- Daily actual units, revenue, cost, and profit.
- Basic forecast script.
- Advanced forecast script with seasonality and festival logic.
- Business plan assumptions: INR 129.70 cost, INR 195 price, October cost reduction.

## Slide 5: Executive KPI Summary

- Revenue: INR 1,996,800.
- Profit: INR 834,328.
- Units sold: 10,240.
- Gross margin: 41.8%.
- Peak actual day: 100 units.
- July to December revenue growth: 676.6%.

## Slide 6: Revenue and Profit Growth

Visual: `outputs/figures/monthly_growth_dashboard.png`

Message: Revenue scaled sharply through October to December, while profit expanded because cost discipline improved margin.

## Slide 7: Margin Improvement

Visual: `outputs/figures/margin_analysis.png`

Message: Margin improved from 33.5% to 43.5% after modeled procurement optimization reduced unit cost by 15%.

## Slide 8: Seasonality and Festival Demand

Visual: `outputs/figures/seasonal_demand_heatmap.png`

Message: Demand concentrated around weekends and festival windows. Festival-window average daily revenue was 54.2% higher.

## Slide 9: Forecast Model Evolution

- Phase 1: Basic growth and unit economics model.
- Phase 2: Advanced seasonality, festival, volatility, delivery delay, and capacity model.
- Key lesson: more realistic assumptions need continuous calibration.

## Slide 10: Forecast vs Actual

Visual: `outputs/figures/forecast_vs_actual_revenue.png`

Message: The basic forecast had -1.5% aggregate revenue bias, while the advanced scenario over-forecasted by 50.2%. This becomes a governance insight, not a failure.

## Slide 11: Operational Risk

Visual: `outputs/figures/volatility_delay_impact.png`

Message: Simulated procurement and delivery delays created INR 37,635 revenue at risk. Supplier reliability becomes a growth constraint.

## Slide 12: Strategic Recommendations

- Pre-build inventory before festival and gifting windows.
- Use wholesale procurement to preserve margins.
- Separate baseline demand from seasonal uplift.
- Track actual-vs-forecast variance monthly.
- Build reorder-point logic and safety stock thresholds.
- Expand SKU strategy for premium gifting bundles.

## Slide 13: Technical Stack

- Python, Pandas, NumPy, Matplotlib.
- SQL for KPI logic.
- Power BI for executive reporting.
- Forecasting methods: trend, seasonality, scenario modeling, actual-vs-forecast diagnostics.

## Slide 14: Closing

Serene Scents shows how analytics can help an early-stage venture move from intuition to operating discipline: forecast demand, protect margin, prepare inventory, and scale with fewer surprises.
