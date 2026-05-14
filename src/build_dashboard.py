"""Build an offline interactive HTML dashboard for Serene Scents.

The generated dashboard is self-contained: no CDN, no local server, and no
Power BI dependency. Open dashboard/index.html in any modern browser.
"""

from __future__ import annotations

import csv
import json
from collections import defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data" / "processed"
DASHBOARD_DIR = ROOT / "dashboard"
OUTPUT_PATH = DASHBOARD_DIR / "index.html"


def read_csv(name: str) -> list[dict[str, object]]:
    path = DATA_DIR / name
    with path.open(newline="", encoding="utf-8") as file:
        rows = list(csv.DictReader(file))
    return [coerce_row(row) for row in rows]


def coerce_row(row: dict[str, str]) -> dict[str, object]:
    output: dict[str, object] = {}
    for key, value in row.items():
        if value == "":
            output[key] = None
            continue
        if value in {"True", "False"}:
            output[key] = value == "True"
            continue
        try:
            output[key] = float(value)
            continue
        except ValueError:
            output[key] = value
    return output


def metric_map(rows: list[dict[str, object]]) -> dict[str, object]:
    return {str(row["metric"]): row["value"] for row in rows}


def build_daily_series(daily: list[dict[str, object]]) -> list[dict[str, object]]:
    trimmed = []
    for row in daily:
        trimmed.append(
            {
                "date": row["date"],
                "month": row["month"],
                "day": row["day_of_week"],
                "units": row["units_sold"],
                "revenue": row["revenue"],
                "profit": row["profit"],
                "margin": row["gross_margin"],
                "basicRevenue": row["basic_revenue"],
                "advancedRevenue": row["advanced_revenue"],
                "basicUnits": row["basic_units"],
                "advancedUnits": row["advanced_units"],
                "isWeekend": row["is_weekend"],
                "isFestival": row["is_festival_window"],
            }
        )
    return trimmed


def build_delay_monthly(stress: list[dict[str, object]]) -> list[dict[str, object]]:
    grouped: dict[str, dict[str, float | str]] = {}
    for row in stress:
        month = str(row["month"])
        item = grouped.setdefault(month, {"month": month, "risk": 0.0, "delayDays": 0.0})
        item["risk"] = float(item["risk"]) + float(row.get("revenue_at_risk_from_delay") or 0)
        item["delayDays"] = float(item["delayDays"]) + float(row.get("delay_flag") or 0)
    return [grouped[key] for key in sorted(grouped)]


def build_weekday_summary(daily: list[dict[str, object]]) -> list[dict[str, object]]:
    grouped: dict[str, list[float]] = defaultdict(list)
    order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    for row in daily:
        grouped[str(row["day_of_week"])].append(float(row["units_sold"]))
    return [
        {
            "day": day,
            "avgUnits": sum(grouped[day]) / len(grouped[day]) if grouped[day] else 0,
        }
        for day in order
    ]


def build_dashboard_data() -> dict[str, object]:
    daily = read_csv("daily_forecast_comparison.csv")
    monthly = read_csv("monthly_kpis.csv")
    monthly_forecast = read_csv("monthly_forecast_comparison.csv")
    executive = metric_map(read_csv("executive_kpis.csv"))
    model_comparison = read_csv("model_comparison.csv")
    festival = read_csv("festival_analysis.csv")
    cost_phase = read_csv("cost_phase_analysis.csv")
    stress = read_csv("advanced_stress_test_forecast.csv")

    best_day = max(daily, key=lambda row: float(row["profit"]))
    worst_day = min(daily, key=lambda row: float(row["profit"]))
    monthly_by_month = {str(row["month"]): row for row in monthly}
    december = monthly_by_month["2025-12"]
    january = monthly_by_month["2026-01"]
    january_revenue_change = (float(january["revenue"]) - float(december["revenue"])) / float(december["revenue"])
    january_unit_change = (float(january["units"]) - float(december["units"])) / float(december["units"])

    return {
        "meta": {
            "title": "Serene Scents",
            "subtitle": "Business analytics and forecasting dashboard",
            "period": executive["Tenure"],
            "generatedFrom": "Processed Serene Scents portfolio datasets",
        },
        "kpis": executive,
        "monthly": monthly,
        "monthlyForecast": monthly_forecast,
        "daily": build_daily_series(daily),
        "models": model_comparison,
        "festival": festival,
        "costPhase": cost_phase,
        "delayMonthly": build_delay_monthly(stress),
        "weekday": build_weekday_summary(daily),
        "bestDay": {
            "date": best_day["date"],
            "units": best_day["units_sold"],
            "revenue": best_day["revenue"],
            "profit": best_day["profit"],
        },
        "worstDay": {
            "date": worst_day["date"],
            "units": worst_day["units_sold"],
            "revenue": worst_day["revenue"],
            "profit": worst_day["profit"],
        },
        "postFestive": {
            "decemberRevenue": december["revenue"],
            "januaryRevenue": january["revenue"],
            "decemberUnits": december["units"],
            "januaryUnits": january["units"],
            "revenueDropPct": january_revenue_change,
            "unitDropPct": january_unit_change,
            "label": "January post-festive/New Year normalization",
        },
        "insights": [
            {
                "label": "Margin unlock",
                "text": "Procurement optimization lifted gross margin from 33.5% to 43.5% while the INR 195 selling price stayed constant.",
            },
            {
                "label": "Seasonal demand",
                "text": "Festival-window daily revenue was 54.2% above normal periods, so inventory should be built before demand arrives.",
            },
            {
                "label": "January sales fall",
                "text": f"After the festive and New Year sales period, January revenue fell {abs(january_revenue_change) * 100:.1f}% from December as gifting demand normalized.",
            },
            {
                "label": "Weekend behavior",
                "text": "Weekend unit demand was 61.6% higher than weekday demand, making staffing and fulfillment planning important.",
            },
            {
                "label": "Forecast governance",
                "text": "The advanced scenario was useful for stress testing, but over-forecasted revenue by 50.2% and needs monthly calibration.",
            },
        ],
        "suggestions": [
            "Create a festival readiness plan 3 to 4 weeks before Diwali and December gifting peaks.",
            "Treat January as a post-festive demand reset: reduce aggressive procurement after New Year sales and shift focus to retention, bundles, and repeat purchases.",
            "Use wholesale procurement contracts for wax, fragrance oils, jars, labels, and packaging to protect the 43.5% margin.",
            "Separate baseline demand, weekend uplift, and festival uplift in every forecast review.",
            "Track supplier lead time, stockout days, and reorder points to reduce simulated delay revenue risk.",
            "Use actual-vs-forecast review meetings monthly so the advanced model stays realistic rather than optimistic.",
        ],
    }


HTML_TEMPLATE = r"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Serene Scents Dashboard</title>
  <style>
    :root {
      --ink: #f4fff8;
      --muted: #a8beb4;
      --line: rgba(207, 236, 221, 0.16);
      --paper: #07100d;
      --panel: rgba(15, 29, 25, 0.82);
      --panel-strong: rgba(19, 38, 33, 0.94);
      --sage: #62d2a2;
      --blue: #5ac8fa;
      --gold: #f2c14e;
      --coral: #ff7a66;
      --plum: #b68cff;
      --mint: #9ef0c1;
      --shadow: 0 24px 70px rgba(0, 0, 0, 0.38);
      --glow-blue: 0 0 28px rgba(90, 200, 250, 0.26);
      --glow-sage: 0 0 30px rgba(98, 210, 162, 0.22);
      --glow-gold: 0 0 28px rgba(242, 193, 78, 0.22);
    }

    * { box-sizing: border-box; }

    body {
      margin: 0;
      background:
        linear-gradient(135deg, #07100d 0%, #0c1915 34%, #15101c 66%, #07100d 100%);
      color: var(--ink);
      font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      font-size: 16px;
      min-height: 100vh;
    }

    body::before {
      content: "";
      position: fixed;
      inset: 0;
      pointer-events: none;
      background:
        linear-gradient(90deg, rgba(158, 240, 193, 0.065) 0 1px, transparent 1px 128px),
        linear-gradient(180deg, rgba(90, 200, 250, 0.045) 0 1px, transparent 1px 128px),
        linear-gradient(120deg, rgba(90, 200, 250, 0.10), transparent 34%, rgba(242, 193, 78, 0.08) 68%, transparent);
      opacity: 0.65;
      mask-image: linear-gradient(to bottom, black, transparent 82%);
    }

    body::after {
      content: "";
      position: fixed;
      top: 0;
      left: -30%;
      width: 60%;
      height: 2px;
      pointer-events: none;
      background: linear-gradient(90deg, transparent, rgba(158, 240, 193, 0.85), rgba(90, 200, 250, 0.65), transparent);
      animation: scanline 8s ease-in-out infinite;
      opacity: 0.75;
    }

    @keyframes scanline {
      0%, 100% { transform: translateX(0); }
      50% { transform: translateX(210%); }
    }

    button, select {
      font: inherit;
    }

    .app {
      min-height: 100vh;
      position: relative;
      isolation: isolate;
    }

    .topbar {
      position: sticky;
      top: 0;
      z-index: 20;
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 18px;
      padding: 16px 26px;
      background: rgba(5, 13, 11, 0.82);
      border-bottom: 1px solid var(--line);
      box-shadow: 0 18px 48px rgba(0, 0, 0, 0.30);
      backdrop-filter: blur(20px) saturate(1.25);
    }

    .brand {
      display: flex;
      flex-direction: column;
      min-width: 220px;
    }

    .brand strong {
      font-size: 22px;
      line-height: 1.1;
      color: var(--ink);
      text-shadow: 0 0 18px rgba(158, 240, 193, 0.18);
    }

    .brand span {
      color: var(--muted);
      margin-top: 4px;
      font-size: 13px;
    }

    .nav {
      display: flex;
      gap: 8px;
      flex-wrap: wrap;
      justify-content: center;
    }

    .nav button,
    .utility button,
    .toggle button {
      border: 1px solid var(--line);
      background: rgba(255, 255, 255, 0.035);
      color: var(--ink);
      border-radius: 8px;
      padding: 9px 13px;
      cursor: pointer;
      transition: 160ms ease;
      min-height: 42px;
      box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.08);
    }

    .nav button.active,
    .toggle button.active {
      color: #06100d;
      background: linear-gradient(135deg, var(--mint), var(--blue));
      border-color: rgba(158, 240, 193, 0.62);
      box-shadow: var(--glow-blue);
    }

    .nav button:hover,
    .utility button:hover,
    .toggle button:hover {
      transform: translateY(-1px);
      border-color: rgba(158, 240, 193, 0.44);
      box-shadow: 0 12px 28px rgba(0, 0, 0, 0.30), var(--glow-sage);
    }

    .utility {
      display: flex;
      gap: 8px;
      justify-content: flex-end;
      min-width: 190px;
    }

    main {
      max-width: 1500px;
      margin: 0 auto;
      padding: 28px;
    }

    .hero {
      display: grid;
      grid-template-columns: 1.1fr 0.9fr;
      gap: 22px;
      align-items: stretch;
      margin-bottom: 22px;
    }

    .hero-main,
    .section,
    .chart-panel,
    .insight-panel,
    .rec-panel,
    .metric-card {
      position: relative;
      overflow: hidden;
      background:
        linear-gradient(145deg, rgba(255, 255, 255, 0.085), rgba(255, 255, 255, 0.025)),
        var(--panel);
      border: 1px solid var(--line);
      border-radius: 8px;
      box-shadow: var(--shadow);
      backdrop-filter: blur(18px) saturate(1.15);
    }

    .hero-main::before,
    .section::before,
    .chart-panel::before,
    .insight-panel::before,
    .rec-panel::before,
    .metric-card::before {
      content: "";
      position: absolute;
      inset: 0 0 auto 0;
      height: 1px;
      background: linear-gradient(90deg, transparent, rgba(158, 240, 193, 0.65), rgba(90, 200, 250, 0.42), transparent);
      opacity: 0.9;
    }

    .hero-main > *,
    .section > *,
    .chart-panel > *,
    .insight-panel > *,
    .rec-panel > *,
    .metric-card > * {
      position: relative;
    }

    .hero-main {
      padding: 30px;
      display: flex;
      flex-direction: column;
      justify-content: space-between;
      min-height: 260px;
    }

    h1 {
      font-size: 46px;
      line-height: 1.02;
      margin: 0 0 14px;
      max-width: 760px;
      letter-spacing: 0;
      color: transparent;
      background: linear-gradient(90deg, #f4fff8 0%, #9ef0c1 42%, #f2c14e 100%);
      -webkit-background-clip: text;
      background-clip: text;
      text-shadow: 0 0 34px rgba(158, 240, 193, 0.14);
    }

    .hero-main p {
      color: var(--muted);
      max-width: 840px;
      font-size: 18px;
      line-height: 1.55;
      margin: 0;
    }

    .hero-strip {
      display: grid;
      grid-template-columns: repeat(3, minmax(0, 1fr));
      gap: 12px;
      margin-top: 26px;
    }

    .strip-item {
      border-left: 4px solid var(--sage);
      padding: 8px 10px;
      background: rgba(98, 210, 162, 0.10);
      border-radius: 6px;
      box-shadow: inset 0 0 0 1px rgba(98, 210, 162, 0.11);
    }

    .strip-item:nth-child(2) { border-left-color: var(--gold); background: rgba(242, 193, 78, 0.11); box-shadow: inset 0 0 0 1px rgba(242, 193, 78, 0.13); }
    .strip-item:nth-child(3) { border-left-color: var(--coral); background: rgba(255, 122, 102, 0.10); box-shadow: inset 0 0 0 1px rgba(255, 122, 102, 0.12); }

    .strip-item span {
      display: block;
      color: var(--muted);
      font-size: 12px;
      margin-bottom: 4px;
    }

    .strip-item strong {
      font-size: 20px;
      color: var(--ink);
    }

    .hero-side {
      display: grid;
      grid-template-columns: repeat(2, minmax(0, 1fr));
      gap: 14px;
    }

    .metric-card {
      padding: 18px;
      min-height: 122px;
      display: flex;
      flex-direction: column;
      justify-content: space-between;
      transition: transform 180ms ease, border-color 180ms ease, box-shadow 180ms ease;
    }

    .metric-card:nth-child(1),
    .metric-card:nth-child(4) {
      background:
        linear-gradient(145deg, rgba(90, 200, 250, 0.17), rgba(255, 255, 255, 0.025)),
        var(--panel);
    }

    .metric-card:nth-child(2),
    .metric-card:nth-child(3) {
      background:
        linear-gradient(145deg, rgba(98, 210, 162, 0.17), rgba(255, 255, 255, 0.025)),
        var(--panel);
    }

    .metric-card:nth-child(5),
    .metric-card:nth-child(6) {
      background:
        linear-gradient(145deg, rgba(242, 193, 78, 0.16), rgba(255, 122, 102, 0.04)),
        var(--panel);
    }

    .metric-card:hover {
      transform: translateY(-3px);
      border-color: rgba(158, 240, 193, 0.36);
      box-shadow: var(--shadow), var(--glow-sage);
    }

    .metric-card .label {
      color: var(--muted);
      font-size: 13px;
      line-height: 1.3;
    }

    .metric-card .value {
      font-size: 31px;
      font-weight: 750;
      line-height: 1.05;
      margin-top: 12px;
      color: var(--ink);
      text-shadow: 0 0 22px rgba(158, 240, 193, 0.16);
    }

    .metric-card .note {
      color: var(--muted);
      font-size: 12px;
      margin-top: 8px;
    }

    .section {
      padding: 22px;
      margin-bottom: 22px;
    }

    .section-header {
      display: flex;
      justify-content: space-between;
      gap: 18px;
      align-items: flex-start;
      margin-bottom: 18px;
    }

    .section-header h2,
    .chart-panel h3,
    .insight-panel h3,
    .rec-panel h3 {
      margin: 0;
      font-size: 24px;
      line-height: 1.2;
    }

    .section-header p {
      margin: 6px 0 0;
      color: var(--muted);
      line-height: 1.45;
      max-width: 780px;
    }

    .grid-2 {
      display: grid;
      grid-template-columns: repeat(2, minmax(0, 1fr));
      gap: 18px;
    }

    .grid-3 {
      display: grid;
      grid-template-columns: repeat(3, minmax(0, 1fr));
      gap: 18px;
    }

    .chart-panel,
    .insight-panel,
    .rec-panel {
      padding: 18px;
      min-height: 420px;
    }

    .chart-panel h3 {
      font-size: 18px;
      margin-bottom: 8px;
    }

    .chart-note {
      color: var(--muted);
      font-size: 13px;
      margin-bottom: 12px;
      min-height: 38px;
      line-height: 1.45;
    }

    .chart {
      width: 100%;
      height: 320px;
      position: relative;
      border-radius: 8px;
      background:
        linear-gradient(180deg, rgba(255, 255, 255, 0.035), rgba(255, 255, 255, 0.012)),
        rgba(3, 10, 9, 0.22);
    }

    .chart.tall {
      height: 440px;
    }

    svg {
      width: 100%;
      height: 100%;
      overflow: visible;
    }

    .chart rect,
    .chart circle,
    .chart path {
      transition: opacity 150ms ease, filter 150ms ease, transform 150ms ease;
    }

    .chart rect:hover,
    .chart circle:hover {
      filter: drop-shadow(0 0 12px rgba(158, 240, 193, 0.42));
    }

    .axis text {
      fill: var(--muted);
      font-size: 12px;
    }

    .axis line,
    .axis path,
    .grid-line {
      stroke: rgba(214, 236, 224, 0.14);
      stroke-width: 1;
    }

    .legend {
      display: flex;
      align-items: center;
      gap: 12px;
      flex-wrap: wrap;
      color: var(--muted);
      font-size: 13px;
      margin-top: 8px;
    }

    .legend span {
      display: inline-flex;
      align-items: center;
      gap: 6px;
    }

    .swatch {
      width: 12px;
      height: 12px;
      border-radius: 3px;
      display: inline-block;
    }

    .insight-list,
    .rec-list {
      display: grid;
      gap: 12px;
      margin-top: 12px;
    }

    .insight-item,
    .rec-item {
      border: 1px solid var(--line);
      background:
        linear-gradient(135deg, rgba(255, 255, 255, 0.055), rgba(255, 255, 255, 0.018));
      border-radius: 8px;
      padding: 14px;
      box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.05);
      transition: transform 160ms ease, border-color 160ms ease;
    }

    .insight-item:hover,
    .rec-item:hover {
      transform: translateY(-2px);
      border-color: rgba(158, 240, 193, 0.35);
    }

    .insight-item strong,
    .rec-item strong {
      display: block;
      margin-bottom: 5px;
      font-size: 15px;
    }

    .insight-item p,
    .rec-item p {
      color: var(--muted);
      line-height: 1.45;
      margin: 0;
    }

    .table-wrap {
      overflow-x: auto;
      border: 1px solid var(--line);
      border-radius: 8px;
      background: rgba(4, 12, 10, 0.42);
      box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.04);
    }

    table {
      width: 100%;
      border-collapse: collapse;
      min-width: 760px;
    }

    th, td {
      text-align: left;
      padding: 12px 14px;
      border-bottom: 1px solid var(--line);
      white-space: nowrap;
    }

    th {
      background: rgba(158, 240, 193, 0.08);
      color: var(--muted);
      font-size: 12px;
      text-transform: uppercase;
    }

    td {
      font-size: 14px;
      color: var(--ink);
    }

    tbody tr:hover {
      background: rgba(90, 200, 250, 0.07);
    }

    .view {
      display: none;
    }

    .view.active {
      display: block;
    }

    .tooltip {
      position: fixed;
      z-index: 40;
      pointer-events: none;
      background: rgba(4, 12, 10, 0.96);
      color: var(--ink);
      padding: 10px 12px;
      border-radius: 8px;
      border: 1px solid rgba(158, 240, 193, 0.30);
      box-shadow: 0 18px 42px rgba(0, 0, 0, 0.45), var(--glow-sage);
      font-size: 13px;
      line-height: 1.45;
      max-width: 280px;
      opacity: 0;
      transform: translate(-50%, -110%);
      transition: opacity 100ms ease;
    }

    .callout {
      border-left: 5px solid var(--gold);
      background: rgba(242, 193, 78, 0.12);
      padding: 16px 18px;
      border-radius: 8px;
      line-height: 1.5;
      color: #f8e9b9;
      margin-bottom: 18px;
      box-shadow: inset 0 0 0 1px rgba(242, 193, 78, 0.15);
    }

    .focus-mode .topbar {
      padding: 10px 26px;
    }

    .focus-mode h1 {
      font-size: 54px;
    }

    .focus-mode .metric-card .value {
      font-size: 36px;
    }

    .focus-mode main {
      max-width: 1680px;
      padding: 22px;
    }

    @media (max-width: 1100px) {
      .hero,
      .grid-2,
      .grid-3 {
        grid-template-columns: 1fr;
      }

      .hero-side {
        grid-template-columns: repeat(2, minmax(0, 1fr));
      }

      .topbar {
        align-items: flex-start;
        flex-direction: column;
      }

      .utility {
        justify-content: flex-start;
      }
    }

    @media (max-width: 720px) {
      main {
        padding: 16px;
      }

      h1 {
        font-size: 36px;
      }

      .hero-strip,
      .hero-side {
        grid-template-columns: 1fr;
      }

      .chart {
        height: 280px;
      }
    }
  </style>
</head>
<body>
  <div class="app">
    <header class="topbar">
      <div class="brand">
        <strong>Serene Scents</strong>
        <span>Interactive business analytics dashboard</span>
      </div>
      <nav class="nav" aria-label="Dashboard views">
        <button class="active" data-view="overview">Overview</button>
        <button data-view="trends">Trends</button>
        <button data-view="forecast">Forecast</button>
        <button data-view="operations">Operations</button>
        <button data-view="recommendations">Recommendations</button>
      </nav>
      <div class="utility">
        <button id="focusBtn">Meeting mode</button>
        <button id="fullBtn">Fullscreen</button>
      </div>
    </header>

    <main>
      <section class="hero">
        <div class="hero-main">
          <div>
            <h1>Scaling a handmade candle venture with sharper forecasting and operating discipline.</h1>
            <p>Projection-ready view of revenue growth, profit progression, seasonality, forecast accuracy, procurement risk, and founder decisions for July 2025 to January 2026.</p>
          </div>
          <div class="hero-strip">
            <div class="strip-item"><span>Analysis period</span><strong id="periodLabel"></strong></div>
            <div class="strip-item"><span>Best operating day</span><strong id="bestDayLabel"></strong></div>
            <div class="strip-item"><span>Primary decision</span><strong>Plan before peaks</strong></div>
          </div>
        </div>
        <div class="hero-side" id="kpiCards"></div>
      </section>

      <section id="overview" class="view active">
        <div class="section">
          <div class="section-header">
            <div>
              <h2>Executive Snapshot</h2>
              <p>The business reached nearly INR 20 lakh revenue while improving margin after procurement optimization. Seasonal demand created major upside, but forecast calibration and supplier readiness became the next management priorities.</p>
            </div>
          </div>
          <div class="grid-2">
            <div class="chart-panel">
              <h3>Monthly revenue, profit, and margin</h3>
              <div class="chart-note">Revenue scaled into December while margin stepped up after October cost optimization.</div>
              <div class="chart" id="monthlyCombo"></div>
              <div class="legend">
                <span><i class="swatch" style="background: var(--blue)"></i>Revenue</span>
                <span><i class="swatch" style="background: var(--sage)"></i>Profit</span>
                <span><i class="swatch" style="background: var(--coral)"></i>Gross margin</span>
              </div>
            </div>
            <div class="insight-panel">
              <h3>Meeting talking points</h3>
              <div class="insight-list" id="insightList"></div>
            </div>
          </div>
        </div>
      </section>

      <section id="trends" class="view">
        <div class="section">
          <div class="section-header">
            <div>
              <h2>Revenue and Demand Trends</h2>
              <p>Use this view to explain how sales matured from small-batch volume into seasonal scale, with visible weekend and festival effects.</p>
            </div>
          </div>
          <div class="grid-2">
            <div class="chart-panel">
              <h3>Daily revenue and 7-day trend</h3>
              <div class="chart-note">The moving average smooths daily noise and makes the October to December growth curve easier to present.</div>
              <div class="chart" id="dailyTrend"></div>
            </div>
            <div class="chart-panel">
              <h3>Seasonality heatmap</h3>
              <div class="chart-note">Average units by month and day of week. Darker cells show stronger demand concentration.</div>
              <div class="chart tall" id="heatmap"></div>
            </div>
          </div>
        </div>
      </section>

      <section id="forecast" class="view">
        <div class="section">
          <div class="section-header">
            <div>
              <h2>Forecast Performance</h2>
              <p>The basic forecast was close in aggregate, while the advanced model became more useful as a stress-test scenario that needs calibration.</p>
            </div>
            <div class="toggle" aria-label="Forecast metric">
              <button class="active" data-forecast-metric="revenue">Revenue</button>
              <button data-forecast-metric="units">Units</button>
              <button data-forecast-metric="profit">Profit</button>
            </div>
          </div>
          <div class="grid-2">
            <div class="chart-panel">
              <h3>Actual vs forecast by month</h3>
              <div class="chart-note">Compare actuals with the original basic forecast and the advanced operating scenario.</div>
              <div class="chart" id="forecastChart"></div>
            </div>
            <div class="chart-panel">
              <h3>Model diagnostics</h3>
              <div class="chart-note">Lower unit error is better. Revenue bias shows optimism or conservatism across the full period.</div>
              <div class="chart" id="modelDiagnostics"></div>
            </div>
          </div>
          <div class="section" style="box-shadow: none; margin: 18px 0 0; padding: 0; border: none; background: transparent;">
            <div class="table-wrap">
              <table id="modelTable"></table>
            </div>
          </div>
        </div>
      </section>

      <section id="operations" class="view">
        <div class="section">
          <div class="section-header">
            <div>
              <h2>Operations and Risk</h2>
              <p>Use this section to discuss procurement, capacity pressure, festival readiness, and revenue at risk from delivery disruptions.</p>
            </div>
          </div>
          <div class="grid-2">
            <div class="chart-panel">
              <h3>Margin before and after cost optimization</h3>
              <div class="chart-note">The biggest profitability unlock came from unit cost reduction, not price increases.</div>
              <div class="chart" id="marginBars"></div>
            </div>
            <div class="chart-panel">
              <h3>Simulated delivery delay risk</h3>
              <div class="chart-note">Monthly revenue at risk from modeled procurement and delivery disruption days.</div>
              <div class="chart" id="delayRisk"></div>
            </div>
          </div>
          <div class="grid-2" style="margin-top: 18px;">
            <div class="chart-panel">
              <h3>Weekend demand lift</h3>
              <div class="chart-note">Weekend demand required stronger production and fulfillment readiness.</div>
              <div class="chart" id="weekdayBars"></div>
            </div>
            <div class="insight-panel">
              <h3>Operating readout</h3>
              <div class="callout" id="operatingCallout"></div>
              <div class="table-wrap">
                <table id="monthlyTable"></table>
              </div>
            </div>
          </div>
        </div>
      </section>

      <section id="recommendations" class="view">
        <div class="section">
          <div class="section-header">
            <div>
              <h2>Founder Recommendations</h2>
              <p>Meeting-ready actions that connect the analysis to inventory, procurement, capacity, and forecast governance.</p>
            </div>
          </div>
          <div class="grid-2">
            <div class="rec-panel">
              <h3>Suggested decisions</h3>
              <div class="rec-list" id="recList"></div>
            </div>
            <div class="chart-panel">
              <h3>Monthly performance table</h3>
              <div class="chart-note">Use this table for direct Q&A when someone asks for the numbers behind the story.</div>
              <div class="table-wrap">
                <table id="performanceTable"></table>
              </div>
            </div>
          </div>
        </div>
      </section>
    </main>
  </div>

  <div class="tooltip" id="tooltip"></div>

  <script>
    const DASHBOARD_DATA = __DASHBOARD_DATA__;

    const colors = {
      ink: "#f4fff8",
      muted: "#a8beb4",
      line: "rgba(207, 236, 221, 0.16)",
      blue: "#5ac8fa",
      sage: "#62d2a2",
      gold: "#f2c14e",
      coral: "#ff7a66",
      plum: "#b68cff",
      mint: "#9ef0c1"
    };

    const tooltip = document.getElementById("tooltip");
    let forecastMetric = "revenue";

    function number(value) {
      return Number(value || 0);
    }

    function fmtINR(value) {
      value = number(value);
      if (Math.abs(value) >= 100000) return "INR " + (value / 100000).toFixed(2) + "L";
      return "INR " + value.toLocaleString("en-IN", { maximumFractionDigits: 0 });
    }

    function fmtFullINR(value) {
      return "INR " + number(value).toLocaleString("en-IN", { maximumFractionDigits: 0 });
    }

    function fmtPct(value) {
      return (number(value) * 100).toFixed(1) + "%";
    }

    function fmtUnits(value) {
      return number(value).toLocaleString("en-IN", { maximumFractionDigits: 0 });
    }

    function showTip(event, html) {
      tooltip.innerHTML = html;
      tooltip.style.left = event.clientX + "px";
      tooltip.style.top = event.clientY + "px";
      tooltip.style.opacity = "1";
    }

    function hideTip() {
      tooltip.style.opacity = "0";
    }

    function createSvg(containerId, width = 900, height = 360) {
      const container = document.getElementById(containerId);
      container.innerHTML = "";
      const svg = document.createElementNS("http://www.w3.org/2000/svg", "svg");
      svg.setAttribute("viewBox", `0 0 ${width} ${height}`);
      svg.setAttribute("role", "img");
      container.appendChild(svg);
      return { svg, width, height };
    }

    function el(name, attrs = {}) {
      const node = document.createElementNS("http://www.w3.org/2000/svg", name);
      Object.entries(attrs).forEach(([key, value]) => node.setAttribute(key, value));
      return node;
    }

    function appendText(svg, x, y, text, attrs = {}) {
      const node = el("text", { x, y, ...attrs });
      node.textContent = text;
      svg.appendChild(node);
      return node;
    }

    function linearScale(domainMin, domainMax, rangeMin, rangeMax) {
      const span = domainMax - domainMin || 1;
      return value => rangeMin + ((value - domainMin) / span) * (rangeMax - rangeMin);
    }

    function drawGrid(svg, plot, maxValue, ticks = 4, formatter = fmtINR) {
      for (let i = 0; i <= ticks; i++) {
        const value = (maxValue / ticks) * i;
        const y = linearScale(0, maxValue, plot.bottom, plot.top)(value);
        svg.appendChild(el("line", { x1: plot.left, x2: plot.right, y1: y, y2: y, class: "grid-line" }));
        appendText(svg, plot.left - 10, y + 4, formatter(value), {
          "text-anchor": "end",
          fill: colors.muted,
          "font-size": 12
        });
      }
    }

    function pathFromPoints(points) {
      return points.map((point, index) => `${index === 0 ? "M" : "L"}${point[0]},${point[1]}`).join(" ");
    }

    function drawMonthlyCombo() {
      const data = DASHBOARD_DATA.monthly;
      const { svg, width, height } = createSvg("monthlyCombo", 900, 360);
      const plot = { left: 86, right: width - 36, top: 22, bottom: height - 54 };
      const maxMoney = Math.max(...data.map(d => Math.max(number(d.revenue), number(d.profit)))) * 1.15;
      const yMoney = linearScale(0, maxMoney, plot.bottom, plot.top);
      const yMargin = linearScale(0.30, 0.46, plot.bottom, plot.top);
      drawGrid(svg, plot, maxMoney, 4, fmtINR);
      const group = (plot.right - plot.left) / data.length;
      const barWidth = Math.min(42, group * 0.28);
      const marginPoints = [];
      data.forEach((d, i) => {
        const center = plot.left + group * i + group / 2;
        const revHeight = plot.bottom - yMoney(number(d.revenue));
        const profitHeight = plot.bottom - yMoney(number(d.profit));
        const rev = el("rect", { x: center - barWidth - 3, y: yMoney(number(d.revenue)), width: barWidth, height: revHeight, rx: 3, fill: colors.blue });
        const profit = el("rect", { x: center + 3, y: yMoney(number(d.profit)), width: barWidth, height: profitHeight, rx: 3, fill: colors.sage });
        [rev, profit].forEach(node => {
          node.addEventListener("mousemove", event => showTip(event, `<strong>${d.month}</strong><br>Revenue: ${fmtFullINR(d.revenue)}<br>Profit: ${fmtFullINR(d.profit)}<br>Margin: ${fmtPct(d.gross_margin)}`));
          node.addEventListener("mouseleave", hideTip);
          svg.appendChild(node);
        });
        marginPoints.push([center, yMargin(number(d.gross_margin))]);
        appendText(svg, center, plot.bottom + 24, d.month.slice(5), { "text-anchor": "middle", fill: colors.muted, "font-size": 12 });
      });
      svg.appendChild(el("path", { d: pathFromPoints(marginPoints), fill: "none", stroke: colors.coral, "stroke-width": 3 }));
      marginPoints.forEach((point, i) => {
        const dot = el("circle", { cx: point[0], cy: point[1], r: 5, fill: colors.coral });
        dot.addEventListener("mousemove", event => showTip(event, `<strong>${data[i].month}</strong><br>Gross margin: ${fmtPct(data[i].gross_margin)}`));
        dot.addEventListener("mouseleave", hideTip);
        svg.appendChild(dot);
      });
      const decIndex = data.findIndex(d => d.month === "2025-12");
      const janIndex = data.findIndex(d => d.month === "2026-01");
      if (decIndex >= 0 && janIndex >= 0) {
        const dec = data[decIndex];
        const jan = data[janIndex];
        const decCenter = plot.left + group * decIndex + group / 2;
        const janCenter = plot.left + group * janIndex + group / 2;
        const decY = yMoney(number(dec.revenue));
        const janY = yMoney(number(jan.revenue));
        svg.appendChild(el("line", {
          x1: decCenter + 16,
          y1: decY - 16,
          x2: janCenter - 16,
          y2: janY - 16,
          stroke: colors.coral,
          "stroke-width": 2.4,
          "stroke-dasharray": "6 5",
          filter: "drop-shadow(0 0 7px rgba(255, 122, 102, 0.38))"
        }));
        appendText(svg, janCenter - 18, janY - 42, `Jan fall ${fmtPct(DASHBOARD_DATA.postFestive.revenueDropPct)}`, {
          "text-anchor": "middle",
          fill: colors.coral,
          "font-size": 13,
          "font-weight": 800
        });
        appendText(svg, janCenter - 18, janY - 25, "post festive/New Year", {
          "text-anchor": "middle",
          fill: colors.muted,
          "font-size": 11
        });
      }
      appendText(svg, plot.left, height - 8, "Month", { fill: colors.muted, "font-size": 12 });
    }

    function rollingAverage(values, windowSize) {
      return values.map((_, index) => {
        const start = Math.max(0, index - windowSize + 1);
        const slice = values.slice(start, index + 1);
        return slice.reduce((sum, value) => sum + value, 0) / slice.length;
      });
    }

    function drawDailyTrend() {
      const data = DASHBOARD_DATA.daily;
      const values = data.map(d => number(d.revenue));
      const rolling = rollingAverage(values, 7);
      const { svg, width, height } = createSvg("dailyTrend", 900, 360);
      const plot = { left: 86, right: width - 34, top: 22, bottom: height - 54 };
      const maxRevenue = Math.max(...values) * 1.12;
      const y = linearScale(0, maxRevenue, plot.bottom, plot.top);
      const x = linearScale(0, data.length - 1, plot.left, plot.right);
      drawGrid(svg, plot, maxRevenue, 4, fmtINR);
      const areaPoints = data.map((d, i) => [x(i), y(number(d.revenue))]);
      svg.appendChild(el("path", { d: pathFromPoints(areaPoints), fill: "none", stroke: "rgba(90, 200, 250, 0.42)", "stroke-width": 1.5, opacity: 0.75 }));
      const rollingPoints = rolling.map((value, i) => [x(i), y(value)]);
      svg.appendChild(el("path", { d: pathFromPoints(rollingPoints), fill: "none", stroke: colors.mint, "stroke-width": 3.2, filter: "drop-shadow(0 0 7px rgba(158, 240, 193, 0.45))" }));
      data.forEach((d, i) => {
        if (d.isFestival) {
          svg.appendChild(el("circle", { cx: x(i), cy: y(number(d.revenue)), r: 3.2, fill: colors.gold, opacity: 0.95 }));
        }
      });
      const labels = ["2025-07", "2025-09", "2025-11", "2026-01"];
      labels.forEach(label => {
        const index = data.findIndex(d => d.month === label);
        if (index >= 0) appendText(svg, x(index), plot.bottom + 24, label, { "text-anchor": "middle", fill: colors.muted, "font-size": 12 });
      });
      const overlay = el("rect", { x: plot.left, y: plot.top, width: plot.right - plot.left, height: plot.bottom - plot.top, fill: "transparent" });
      overlay.addEventListener("mousemove", event => {
        const rect = svg.getBoundingClientRect();
        const pos = (event.clientX - rect.left) / rect.width * width;
        const index = Math.max(0, Math.min(data.length - 1, Math.round((pos - plot.left) / (plot.right - plot.left) * (data.length - 1))));
        const d = data[index];
        showTip(event, `<strong>${d.date}</strong><br>Revenue: ${fmtFullINR(d.revenue)}<br>Profit: ${fmtFullINR(d.profit)}<br>Units: ${fmtUnits(d.units)}${d.isFestival ? "<br>Festival window" : ""}`);
      });
      overlay.addEventListener("mouseleave", hideTip);
      svg.appendChild(overlay);
    }

    function drawHeatmap() {
      const data = DASHBOARD_DATA.daily;
      const months = [...new Set(data.map(d => d.month))];
      const days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"];
      const grouped = {};
      data.forEach(d => {
        const key = d.month + "|" + d.day;
        grouped[key] = grouped[key] || [];
        grouped[key].push(number(d.units));
      });
      const cells = [];
      months.forEach(month => {
        days.forEach(day => {
          const values = grouped[month + "|" + day] || [];
          const avg = values.length ? values.reduce((a, b) => a + b, 0) / values.length : 0;
          cells.push({ month, day, avg });
        });
      });
      const maxAvg = Math.max(...cells.map(d => d.avg));
      const { svg, width, height } = createSvg("heatmap", 900, 460);
      const plot = { left: 98, right: width - 26, top: 28, bottom: height - 52 };
      const cellW = (plot.right - plot.left) / months.length;
      const cellH = (plot.bottom - plot.top) / days.length;
      months.forEach((month, i) => appendText(svg, plot.left + cellW * i + cellW / 2, plot.top - 10, month.slice(5), { "text-anchor": "middle", fill: colors.muted, "font-size": 12 }));
      days.forEach((day, i) => appendText(svg, plot.left - 10, plot.top + cellH * i + cellH / 2 + 4, day.slice(0, 3), { "text-anchor": "end", fill: colors.muted, "font-size": 12 }));
      cells.forEach(cell => {
        const x = plot.left + months.indexOf(cell.month) * cellW;
        const y = plot.top + days.indexOf(cell.day) * cellH;
        const intensity = cell.avg / maxAvg;
        const fill = interpolateColor([17, 31, 28], [98, 210, 162], intensity);
        const rect = el("rect", { x: x + 3, y: y + 3, width: cellW - 6, height: cellH - 6, rx: 5, fill });
        rect.addEventListener("mousemove", event => showTip(event, `<strong>${cell.month} ${cell.day}</strong><br>Avg units: ${cell.avg.toFixed(1)}`));
        rect.addEventListener("mouseleave", hideTip);
        svg.appendChild(rect);
        appendText(svg, x + cellW / 2, y + cellH / 2 + 5, Math.round(cell.avg), { "text-anchor": "middle", fill: intensity > 0.62 ? "#06100d" : colors.ink, "font-size": 12, "font-weight": 700 });
      });
    }

    function interpolateColor(from, to, amount) {
      const values = from.map((start, i) => Math.round(start + (to[i] - start) * amount));
      return `rgb(${values[0]}, ${values[1]}, ${values[2]})`;
    }

    function drawForecastChart() {
      const data = DASHBOARD_DATA.monthlyForecast;
      const metric = forecastMetric;
      const columns = metric === "revenue"
        ? ["actual_revenue", "basic_revenue", "advanced_revenue"]
        : metric === "profit"
          ? ["actual_profit", "basic_profit", "advanced_profit"]
          : ["actual_units", "basic_units", "advanced_units"];
      const labels = ["Actual", "Basic", "Advanced"];
      const palette = [colors.mint, colors.blue, colors.gold];
      const formatter = metric === "units" ? fmtUnits : fmtINR;
      const { svg, width, height } = createSvg("forecastChart", 900, 360);
      const plot = { left: 86, right: width - 34, top: 22, bottom: height - 54 };
      const maxValue = Math.max(...data.flatMap(d => columns.map(column => number(d[column])))) * 1.15;
      const y = linearScale(0, maxValue, plot.bottom, plot.top);
      drawGrid(svg, plot, maxValue, 4, formatter);
      const group = (plot.right - plot.left) / data.length;
      const barW = Math.min(28, group * 0.21);
      data.forEach((d, i) => {
        const center = plot.left + group * i + group / 2;
        columns.forEach((column, j) => {
          const x = center + (j - 1) * (barW + 4);
          const value = number(d[column]);
          const bar = el("rect", { x, y: y(value), width: barW, height: plot.bottom - y(value), rx: 3, fill: palette[j] });
          bar.addEventListener("mousemove", event => showTip(event, `<strong>${d.month}</strong><br>${labels[j]} ${metric}: ${formatter(value)}`));
          bar.addEventListener("mouseleave", hideTip);
          svg.appendChild(bar);
        });
        appendText(svg, center, plot.bottom + 24, d.month.slice(5), { "text-anchor": "middle", fill: colors.muted, "font-size": 12 });
      });
      drawInlineLegend(svg, plot.left, height - 12, labels, palette);
    }

    function drawInlineLegend(svg, x, y, labels, palette) {
      labels.forEach((label, i) => {
        const offset = i * 112;
        svg.appendChild(el("rect", { x: x + offset, y: y - 10, width: 12, height: 12, rx: 2, fill: palette[i] }));
        appendText(svg, x + offset + 18, y, label, { fill: colors.muted, "font-size": 12 });
      });
    }

    function drawModelDiagnostics() {
      const data = DASHBOARD_DATA.models;
      const { svg, width, height } = createSvg("modelDiagnostics", 900, 360);
      const plot = { left: 86, right: width - 34, top: 24, bottom: height - 58 };
      const maxMae = Math.max(...data.map(d => number(d.unit_mae))) * 1.25;
      const x = linearScale(0, maxMae, plot.left, plot.right - 160);
      data.forEach((d, i) => {
        const y = plot.top + i * 105 + 30;
        appendText(svg, plot.left, y - 14, d.model, { fill: colors.ink, "font-size": 16, "font-weight": 750 });
        svg.appendChild(el("rect", { x: plot.left, y, width: x(number(d.unit_mae)) - plot.left, height: 30, rx: 5, fill: i === 0 ? colors.blue : colors.gold, filter: i === 0 ? "drop-shadow(0 0 8px rgba(90, 200, 250, 0.32))" : "drop-shadow(0 0 8px rgba(242, 193, 78, 0.30))" }));
        appendText(svg, x(number(d.unit_mae)) + 10, y + 20, `${number(d.unit_mae).toFixed(1)} MAE`, { fill: colors.muted, "font-size": 13 });
        appendText(svg, plot.right - 150, y + 20, `Bias ${fmtPct(d.revenue_bias_pct)}`, { fill: number(d.revenue_bias_pct) > 0 ? colors.coral : colors.sage, "font-size": 14, "font-weight": 750 });
        appendText(svg, plot.left, y + 58, `RMSE ${number(d.unit_rmse).toFixed(1)} | MAPE ${(number(d.revenue_mape) * 100).toFixed(1)}%`, { fill: colors.muted, "font-size": 12 });
      });
    }

    function drawMarginBars() {
      const data = DASHBOARD_DATA.costPhase;
      const { svg, width, height } = createSvg("marginBars", 900, 360);
      const plot = { left: 90, right: width - 42, top: 28, bottom: height - 70 };
      const maxMargin = Math.max(...data.map(d => number(d.gross_margin))) * 1.25;
      const y = linearScale(0, maxMargin, plot.bottom, plot.top);
      drawGrid(svg, plot, maxMargin, 4, value => (value * 100).toFixed(0) + "%");
      const group = (plot.right - plot.left) / data.length;
      data.forEach((d, i) => {
        const barW = Math.min(120, group * 0.36);
        const center = plot.left + group * i + group / 2;
        const value = number(d.gross_margin);
        const bar = el("rect", { x: center - barW / 2, y: y(value), width: barW, height: plot.bottom - y(value), rx: 6, fill: i === 0 ? colors.gold : colors.sage, filter: i === 0 ? "drop-shadow(0 0 8px rgba(242, 193, 78, 0.28))" : "drop-shadow(0 0 9px rgba(98, 210, 162, 0.32))" });
        bar.addEventListener("mousemove", event => showTip(event, `<strong>${d.cost_phase}</strong><br>Margin: ${fmtPct(d.gross_margin)}<br>Avg unit cost: ${fmtFullINR(d.avg_unit_cost)}<br>Profit: ${fmtFullINR(d.profit)}`));
        bar.addEventListener("mouseleave", hideTip);
        svg.appendChild(bar);
        appendText(svg, center, y(value) - 10, fmtPct(value), { "text-anchor": "middle", fill: colors.ink, "font-size": 15, "font-weight": 750 });
        appendText(svg, center, plot.bottom + 24, i === 0 ? "Pre Oct" : "Post Oct", { "text-anchor": "middle", fill: colors.muted, "font-size": 12 });
      });
    }

    function drawDelayRisk() {
      const data = DASHBOARD_DATA.delayMonthly;
      const { svg, width, height } = createSvg("delayRisk", 900, 360);
      const plot = { left: 86, right: width - 34, top: 26, bottom: height - 54 };
      const maxRisk = Math.max(...data.map(d => number(d.risk)), 1) * 1.2;
      const y = linearScale(0, maxRisk, plot.bottom, plot.top);
      drawGrid(svg, plot, maxRisk, 4, fmtINR);
      const group = (plot.right - plot.left) / data.length;
      const barW = Math.min(52, group * 0.42);
      data.forEach((d, i) => {
        const center = plot.left + group * i + group / 2;
        const risk = number(d.risk);
        const bar = el("rect", { x: center - barW / 2, y: y(risk), width: barW, height: plot.bottom - y(risk), rx: 5, fill: risk > 0 ? colors.coral : "rgba(207, 236, 221, 0.18)", filter: risk > 0 ? "drop-shadow(0 0 8px rgba(255, 122, 102, 0.30))" : "none" });
        bar.addEventListener("mousemove", event => showTip(event, `<strong>${d.month}</strong><br>Revenue at risk: ${fmtFullINR(risk)}<br>Delay days: ${number(d.delayDays).toFixed(0)}`));
        bar.addEventListener("mouseleave", hideTip);
        svg.appendChild(bar);
        appendText(svg, center, plot.bottom + 24, d.month.slice(5), { "text-anchor": "middle", fill: colors.muted, "font-size": 12 });
      });
    }

    function drawWeekdayBars() {
      const data = DASHBOARD_DATA.weekday;
      const { svg, width, height } = createSvg("weekdayBars", 900, 360);
      const plot = { left: 76, right: width - 32, top: 24, bottom: height - 56 };
      const maxUnits = Math.max(...data.map(d => number(d.avgUnits))) * 1.2;
      const y = linearScale(0, maxUnits, plot.bottom, plot.top);
      drawGrid(svg, plot, maxUnits, 4, value => value.toFixed(0));
      const group = (plot.right - plot.left) / data.length;
      const barW = Math.min(56, group * 0.48);
      data.forEach((d, i) => {
        const center = plot.left + group * i + group / 2;
        const value = number(d.avgUnits);
        const isWeekend = d.day === "Saturday" || d.day === "Sunday";
        const bar = el("rect", { x: center - barW / 2, y: y(value), width: barW, height: plot.bottom - y(value), rx: 5, fill: isWeekend ? colors.plum : colors.sage });
        bar.addEventListener("mousemove", event => showTip(event, `<strong>${d.day}</strong><br>Avg units: ${value.toFixed(1)}`));
        bar.addEventListener("mouseleave", hideTip);
        svg.appendChild(bar);
        appendText(svg, center, plot.bottom + 24, d.day.slice(0, 3), { "text-anchor": "middle", fill: colors.muted, "font-size": 12 });
      });
      appendText(svg, plot.left, height - 8, "Average units sold", { fill: colors.muted, "font-size": 12 });
    }

    function buildCards() {
      const k = DASHBOARD_DATA.kpis;
      const cards = [
        ["Actual revenue", fmtINR(k["Actual revenue"]), "Total operating revenue"],
        ["Actual profit", fmtINR(k["Actual profit"]), "Profit after production cost"],
        ["Gross margin", fmtPct(k["Actual gross margin"]), "Full-period margin"],
        ["Units sold", fmtUnits(k["Units sold"]), "Actual units"],
        ["Dec revenue", fmtINR(k["December revenue"]), "Peak monthly revenue"],
        ["Jan sales fall", fmtPct(DASHBOARD_DATA.postFestive.revenueDropPct), "Post-festive/New Year drop"],
        ["Forecast bias", fmtPct(k["Advanced forecast revenue bias"]), "Advanced scenario optimism"]
      ];
      document.getElementById("kpiCards").innerHTML = cards.map(card => `
        <article class="metric-card">
          <div class="label">${card[0]}</div>
          <div class="value">${card[1]}</div>
          <div class="note">${card[2]}</div>
        </article>
      `).join("");
      document.getElementById("periodLabel").textContent = DASHBOARD_DATA.meta.period;
      document.getElementById("bestDayLabel").textContent = `${DASHBOARD_DATA.bestDay.date} | ${fmtUnits(DASHBOARD_DATA.bestDay.units)} units`;
    }

    function buildInsights() {
      document.getElementById("insightList").innerHTML = DASHBOARD_DATA.insights.map(item => `
        <div class="insight-item">
          <strong>${item.label}</strong>
          <p>${item.text}</p>
        </div>
      `).join("");
      document.getElementById("recList").innerHTML = DASHBOARD_DATA.suggestions.map((text, index) => `
        <div class="rec-item">
          <strong>${index + 1}. ${recommendationTitle(text)}</strong>
          <p>${text}</p>
        </div>
      `).join("");
      document.getElementById("operatingCallout").textContent = `Simulated delivery delays created ${fmtFullINR(DASHBOARD_DATA.kpis["Simulated delay revenue at risk"])} of revenue at risk across ${fmtUnits(DASHBOARD_DATA.kpis["Simulated delay days"])} delay days. The operational priority is to protect raw material availability before weekend and festival peaks.`;
    }

    function recommendationTitle(text) {
      if (text.includes("festival")) return "Seasonal readiness";
      if (text.includes("January")) return "January reset";
      if (text.includes("wholesale")) return "Procurement discipline";
      if (text.includes("baseline")) return "Demand planning";
      if (text.includes("supplier")) return "Risk tracking";
      return "Forecast governance";
    }

    function buildTables() {
      document.getElementById("modelTable").innerHTML = `
        <thead><tr><th>Model</th><th>Forecast revenue</th><th>Forecast profit</th><th>Unit MAE</th><th>Revenue MAPE</th><th>Revenue bias</th></tr></thead>
        <tbody>${DASHBOARD_DATA.models.map(d => `
          <tr><td>${d.model}</td><td>${fmtFullINR(d.forecast_revenue)}</td><td>${fmtFullINR(d.forecast_profit)}</td><td>${number(d.unit_mae).toFixed(1)}</td><td>${fmtPct(d.revenue_mape)}</td><td>${fmtPct(d.revenue_bias_pct)}</td></tr>
        `).join("")}</tbody>
      `;
      const monthlyRows = DASHBOARD_DATA.monthly.map(d => `
        <tr><td>${d.month}</td><td>${fmtUnits(d.units)}</td><td>${fmtFullINR(d.revenue)}</td><td>${fmtFullINR(d.profit)}</td><td>${fmtPct(d.gross_margin)}</td><td>${d.revenue_growth_pct === null ? "-" : fmtPct(d.revenue_growth_pct)}</td></tr>
      `).join("");
      const monthlyTable = `<thead><tr><th>Month</th><th>Units</th><th>Revenue</th><th>Profit</th><th>Margin</th><th>Growth</th></tr></thead><tbody>${monthlyRows}</tbody>`;
      document.getElementById("monthlyTable").innerHTML = monthlyTable;
      document.getElementById("performanceTable").innerHTML = monthlyTable;
    }

    function bindNavigation() {
      document.querySelectorAll(".nav button").forEach(button => {
        button.addEventListener("click", () => {
          document.querySelectorAll(".nav button").forEach(btn => btn.classList.remove("active"));
          document.querySelectorAll(".view").forEach(view => view.classList.remove("active"));
          button.classList.add("active");
          document.getElementById(button.dataset.view).classList.add("active");
          requestAnimationFrame(drawAll);
        });
      });
      document.querySelectorAll("[data-forecast-metric]").forEach(button => {
        button.addEventListener("click", () => {
          document.querySelectorAll("[data-forecast-metric]").forEach(btn => btn.classList.remove("active"));
          button.classList.add("active");
          forecastMetric = button.dataset.forecastMetric;
          drawForecastChart();
        });
      });
      document.getElementById("focusBtn").addEventListener("click", () => {
        document.body.classList.toggle("focus-mode");
        requestAnimationFrame(drawAll);
      });
      document.getElementById("fullBtn").addEventListener("click", () => {
        if (!document.fullscreenElement) document.documentElement.requestFullscreen();
        else document.exitFullscreen();
      });
      window.addEventListener("resize", drawAll);
    }

    function drawAll() {
      if (document.getElementById("overview").classList.contains("active")) drawMonthlyCombo();
      if (document.getElementById("trends").classList.contains("active")) {
        drawDailyTrend();
        drawHeatmap();
      }
      if (document.getElementById("forecast").classList.contains("active")) {
        drawForecastChart();
        drawModelDiagnostics();
      }
      if (document.getElementById("operations").classList.contains("active")) {
        drawMarginBars();
        drawDelayRisk();
        drawWeekdayBars();
      }
    }

    function init() {
      buildCards();
      buildInsights();
      buildTables();
      bindNavigation();
      drawAll();
    }

    init();
  </script>
</body>
</html>
"""


def main() -> None:
    DASHBOARD_DIR.mkdir(parents=True, exist_ok=True)
    data = build_dashboard_data()
    html = HTML_TEMPLATE.replace("__DASHBOARD_DATA__", json.dumps(data, separators=(",", ":")))
    OUTPUT_PATH.write_text(html, encoding="utf-8")
    print(OUTPUT_PATH)


if __name__ == "__main__":
    main()
