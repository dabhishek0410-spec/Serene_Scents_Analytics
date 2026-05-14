"""Serene Scents portfolio analytics pipeline.

This script rebuilds cleaned datasets, KPI tables, forecast diagnostics, and
visual assets for the Serene Scents business analytics case study.
"""

from __future__ import annotations

import json
import math
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = ROOT / "data" / "raw"
PROCESSED_DIR = ROOT / "data" / "processed"
FIGURE_DIR = ROOT / "outputs" / "figures"

SELLING_PRICE = 195.0
INITIAL_UNIT_COST = 129.70
OPTIMIZED_UNIT_COST = INITIAL_UNIT_COST * 0.85
START_DATE = "2025-07-01"
END_DATE = "2026-01-31"
FESTIVAL_DATES = ["2025-10-20", "2025-11-01"]


def ensure_output_dirs() -> None:
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    FIGURE_DIR.mkdir(parents=True, exist_ok=True)


def load_actuals() -> pd.DataFrame:
    actual = pd.read_csv(RAW_DIR / "serene_scents_actual_growth.csv")
    actual = actual.rename(columns=lambda col: col.strip().lower().replace(" ", "_"))
    actual = actual[["date", "units_sold", "unit_cost", "revenue", "total_cost", "profit"]]
    actual["date"] = pd.to_datetime(actual["date"])
    actual["month"] = actual["date"].dt.to_period("M").astype(str)
    actual["day_of_week"] = actual["date"].dt.day_name()
    actual["gross_margin"] = np.where(actual["revenue"] > 0, actual["profit"] / actual["revenue"], np.nan)
    actual["cost_phase"] = np.where(
        actual["date"] < pd.Timestamp("2025-10-01"),
        "Pre cost optimization",
        "Post cost optimization",
    )
    actual["is_weekend"] = actual["date"].dt.dayofweek >= 5
    actual["is_festival_window"] = festival_mask(actual["date"])
    return actual


def load_advanced_forecast() -> pd.DataFrame:
    forecast = pd.read_csv(RAW_DIR / "serene_scents_advanced_forecast.csv")
    forecast["date"] = pd.to_datetime(forecast["date"])
    forecast = forecast.rename(
        columns={
            "est_units_sold": "advanced_units",
            "est_unit_cost": "advanced_unit_cost",
            "est_revenue": "advanced_revenue",
            "est_total_cost": "advanced_total_cost",
            "est_profit": "advanced_profit",
        }
    )
    forecast["month"] = forecast["date"].dt.to_period("M").astype(str)
    forecast["advanced_margin"] = np.where(
        forecast["advanced_revenue"] > 0,
        forecast["advanced_profit"] / forecast["advanced_revenue"],
        np.nan,
    )
    return forecast


def generate_basic_forecast() -> pd.DataFrame:
    dates = pd.date_range(START_DATE, END_DATE, freq="D")
    n_days = len(dates)
    basic = pd.DataFrame({"date": dates})
    basic["basic_units"] = np.geomspace(10, 130, n_days).round().astype(int)
    basic["basic_unit_cost"] = INITIAL_UNIT_COST
    basic.loc[basic["date"] >= "2025-10-01", "basic_unit_cost"] = OPTIMIZED_UNIT_COST
    basic["basic_revenue"] = basic["basic_units"] * SELLING_PRICE
    basic["basic_total_cost"] = basic["basic_units"] * basic["basic_unit_cost"]
    basic["basic_profit"] = basic["basic_revenue"] - basic["basic_total_cost"]
    basic["month"] = basic["date"].dt.to_period("M").astype(str)
    return basic


def festival_mask(date_series: pd.Series) -> pd.Series:
    mask = pd.Series(False, index=date_series.index)
    for festival_date in FESTIVAL_DATES:
        center = pd.Timestamp(festival_date)
        mask = mask | ((date_series >= center - pd.Timedelta(days=3)) & (date_series <= center + pd.Timedelta(days=3)))
    return mask


def build_stress_test_forecast(advanced: pd.DataFrame) -> pd.DataFrame:
    rng = np.random.default_rng(42)
    stress = advanced.copy()

    stress["volatility_factor"] = 1 + rng.normal(0, 0.08, len(stress))
    stress["units_after_volatility"] = (
        stress["advanced_units"] * stress["volatility_factor"]
    ).clip(lower=0).round().astype(int)

    stress["delay_flag"] = rng.choice([0, 1], size=len(stress), p=[0.95, 0.05])
    stress["stress_units"] = np.where(
        stress["delay_flag"] == 1,
        stress["units_after_volatility"] * 0.70,
        stress["units_after_volatility"],
    ).round().astype(int)

    stress["stress_revenue_pre_delay"] = stress["units_after_volatility"] * SELLING_PRICE
    stress["stress_revenue"] = stress["stress_units"] * SELLING_PRICE
    stress["stress_total_cost"] = stress["stress_units"] * stress["advanced_unit_cost"]
    stress["stress_profit"] = stress["stress_revenue"] - stress["stress_total_cost"]
    stress["lost_units_from_delay"] = stress["units_after_volatility"] - stress["stress_units"]
    stress["revenue_at_risk_from_delay"] = stress["lost_units_from_delay"] * SELLING_PRICE
    return stress


def build_comparison(actual: pd.DataFrame, basic: pd.DataFrame, advanced: pd.DataFrame) -> pd.DataFrame:
    comparison = (
        actual.merge(
            basic[
                [
                    "date",
                    "basic_units",
                    "basic_revenue",
                    "basic_profit",
                    "basic_unit_cost",
                ]
            ],
            on="date",
            how="left",
        )
        .merge(
            advanced[
                [
                    "date",
                    "advanced_units",
                    "advanced_revenue",
                    "advanced_profit",
                    "advanced_unit_cost",
                    "festival_boost",
                ]
            ],
            on="date",
            how="left",
        )
    )

    comparison["basic_unit_error"] = comparison["basic_units"] - comparison["units_sold"]
    comparison["advanced_unit_error"] = comparison["advanced_units"] - comparison["units_sold"]
    comparison["basic_revenue_error"] = comparison["basic_revenue"] - comparison["revenue"]
    comparison["advanced_revenue_error"] = comparison["advanced_revenue"] - comparison["revenue"]
    return comparison


def safe_mape(actual: pd.Series, predicted: pd.Series) -> float:
    valid = actual.replace(0, np.nan)
    return float(((actual - predicted).abs() / valid).mean())


def model_metrics(label: str, comparison: pd.DataFrame) -> dict[str, float | str]:
    units = comparison[f"{label}_units"]
    revenue = comparison[f"{label}_revenue"]
    profit = comparison[f"{label}_profit"]
    unit_error = units - comparison["units_sold"]
    revenue_error = revenue - comparison["revenue"]

    return {
        "model": label.title(),
        "forecast_units": float(units.sum()),
        "forecast_revenue": float(revenue.sum()),
        "forecast_profit": float(profit.sum()),
        "unit_mae": float(unit_error.abs().mean()),
        "unit_rmse": float(math.sqrt((unit_error**2).mean())),
        "revenue_mape": safe_mape(comparison["revenue"], revenue),
        "revenue_bias_pct": float(revenue_error.sum() / comparison["revenue"].sum()),
    }


def build_kpi_tables(
    actual: pd.DataFrame,
    basic: pd.DataFrame,
    advanced: pd.DataFrame,
    comparison: pd.DataFrame,
    stress: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    monthly = actual.groupby("month").agg(
        days=("date", "count"),
        units=("units_sold", "sum"),
        revenue=("revenue", "sum"),
        total_cost=("total_cost", "sum"),
        profit=("profit", "sum"),
        avg_daily_units=("units_sold", "mean"),
        avg_daily_revenue=("revenue", "mean"),
    )
    monthly["gross_margin"] = monthly["profit"] / monthly["revenue"]
    monthly["revenue_growth_pct"] = monthly["revenue"].pct_change()

    forecast_monthly = comparison.groupby("month").agg(
        actual_revenue=("revenue", "sum"),
        basic_revenue=("basic_revenue", "sum"),
        advanced_revenue=("advanced_revenue", "sum"),
        actual_profit=("profit", "sum"),
        basic_profit=("basic_profit", "sum"),
        advanced_profit=("advanced_profit", "sum"),
        actual_units=("units_sold", "sum"),
        basic_units=("basic_units", "sum"),
        advanced_units=("advanced_units", "sum"),
    )
    forecast_monthly["basic_revenue_variance_pct"] = (
        forecast_monthly["basic_revenue"] - forecast_monthly["actual_revenue"]
    ) / forecast_monthly["actual_revenue"]
    forecast_monthly["advanced_revenue_variance_pct"] = (
        forecast_monthly["advanced_revenue"] - forecast_monthly["actual_revenue"]
    ) / forecast_monthly["actual_revenue"]

    festival = actual.groupby("is_festival_window").agg(
        days=("date", "count"),
        avg_daily_units=("units_sold", "mean"),
        avg_daily_revenue=("revenue", "mean"),
        avg_daily_profit=("profit", "mean"),
        total_revenue=("revenue", "sum"),
        total_profit=("profit", "sum"),
    )
    festival.index = festival.index.map({False: "Non-festival window", True: "Festival window"})

    cost_phase = actual.groupby("cost_phase").agg(
        days=("date", "count"),
        units=("units_sold", "sum"),
        revenue=("revenue", "sum"),
        profit=("profit", "sum"),
        avg_unit_cost=("unit_cost", "mean"),
    )
    cost_phase["gross_margin"] = cost_phase["profit"] / cost_phase["revenue"]

    stress_delay_days = int(stress["delay_flag"].sum())
    delay_revenue_loss = float(stress["revenue_at_risk_from_delay"].sum())
    actual_total_revenue = float(actual["revenue"].sum())
    actual_total_profit = float(actual["profit"].sum())

    executive_kpis = pd.DataFrame(
        [
            ("Tenure", f"{actual['date'].min().date()} to {actual['date'].max().date()}"),
            ("Actual revenue", actual_total_revenue),
            ("Actual profit", actual_total_profit),
            ("Actual gross margin", actual_total_profit / actual_total_revenue),
            ("Units sold", float(actual["units_sold"].sum())),
            ("Average units per day", float(actual["units_sold"].mean())),
            ("Peak actual units per day", float(actual["units_sold"].max())),
            ("July revenue", float(monthly.loc["2025-07", "revenue"])),
            ("December revenue", float(monthly.loc["2025-12", "revenue"])),
            ("July to December revenue growth", float(monthly.loc["2025-12", "revenue"] / monthly.loc["2025-07", "revenue"] - 1)),
            ("Pre-optimization margin", float(cost_phase.loc["Pre cost optimization", "gross_margin"])),
            ("Post-optimization margin", float(cost_phase.loc["Post cost optimization", "gross_margin"])),
            ("Festival avg daily revenue lift", float(festival.loc["Festival window", "avg_daily_revenue"] / festival.loc["Non-festival window", "avg_daily_revenue"] - 1)),
            ("Advanced forecast revenue bias", float((comparison["advanced_revenue"].sum() - comparison["revenue"].sum()) / comparison["revenue"].sum())),
            ("Basic forecast revenue bias", float((comparison["basic_revenue"].sum() - comparison["revenue"].sum()) / comparison["revenue"].sum())),
            ("Simulated delay days", stress_delay_days),
            ("Simulated delay revenue at risk", delay_revenue_loss),
        ],
        columns=["metric", "value"],
    )

    model_comparison = pd.DataFrame(
        [
            model_metrics("basic", comparison),
            model_metrics("advanced", comparison),
        ]
    )

    return executive_kpis, monthly.reset_index(), model_comparison, forecast_monthly.reset_index(), festival.reset_index(), cost_phase.reset_index()


def style_axis(ax: plt.Axes) -> None:
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.grid(axis="y", alpha=0.25)
    ax.tick_params(axis="x", rotation=0)


def save_revenue_profit_trend(actual: pd.DataFrame) -> None:
    fig, ax = plt.subplots(figsize=(13, 6))
    rolling_revenue = actual["revenue"].rolling(7, min_periods=1).mean()
    rolling_profit = actual["profit"].rolling(7, min_periods=1).mean()
    ax.plot(actual["date"], actual["revenue"], color="#8fb8de", alpha=0.35, linewidth=1, label="Daily revenue")
    ax.plot(actual["date"], rolling_revenue, color="#1f5f99", linewidth=2.5, label="7-day avg revenue")
    ax.plot(actual["date"], rolling_profit, color="#2a9d8f", linewidth=2.5, label="7-day avg profit")
    ax.axvline(pd.Timestamp("2025-10-01"), color="#b56576", linestyle="--", linewidth=1.5, label="Cost optimization")
    ax.set_title("Serene Scents Actual Revenue and Profit Trend")
    ax.set_ylabel("INR")
    ax.legend(ncol=2, frameon=False)
    style_axis(ax)
    fig.tight_layout()
    fig.savefig(FIGURE_DIR / "revenue_profit_trend.png", dpi=180)
    plt.close(fig)


def save_monthly_dashboard(monthly: pd.DataFrame) -> None:
    fig, ax1 = plt.subplots(figsize=(12, 6))
    x = np.arange(len(monthly))
    ax1.bar(x - 0.18, monthly["revenue"], width=0.36, color="#3d6f8e", label="Revenue")
    ax1.bar(x + 0.18, monthly["profit"], width=0.36, color="#76a66f", label="Profit")
    ax1.set_ylabel("INR")
    ax1.set_xticks(x)
    ax1.set_xticklabels(monthly["month"])
    ax2 = ax1.twinx()
    ax2.plot(x, monthly["gross_margin"] * 100, color="#c45a4f", marker="o", linewidth=2.5, label="Gross margin")
    ax2.set_ylabel("Gross margin %")
    ax1.set_title("Monthly Growth Dashboard")
    lines1, labels1 = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax1.legend(lines1 + lines2, labels1 + labels2, loc="upper left", frameon=False)
    style_axis(ax1)
    ax2.spines["top"].set_visible(False)
    fig.tight_layout()
    fig.savefig(FIGURE_DIR / "monthly_growth_dashboard.png", dpi=180)
    plt.close(fig)


def save_forecast_vs_actual(forecast_monthly: pd.DataFrame) -> None:
    fig, ax = plt.subplots(figsize=(12, 6))
    x = np.arange(len(forecast_monthly))
    width = 0.25
    ax.bar(x - width, forecast_monthly["actual_revenue"], width=width, color="#2f4858", label="Actual")
    ax.bar(x, forecast_monthly["basic_revenue"], width=width, color="#86bbd8", label="Basic forecast")
    ax.bar(x + width, forecast_monthly["advanced_revenue"], width=width, color="#f6ae2d", label="Advanced scenario")
    ax.set_xticks(x)
    ax.set_xticklabels(forecast_monthly["month"])
    ax.set_title("Forecast vs Actual Monthly Revenue")
    ax.set_ylabel("INR")
    ax.legend(frameon=False)
    style_axis(ax)
    fig.tight_layout()
    fig.savefig(FIGURE_DIR / "forecast_vs_actual_revenue.png", dpi=180)
    plt.close(fig)


def save_margin_analysis(cost_phase: pd.DataFrame, monthly: pd.DataFrame) -> None:
    fig, axes = plt.subplots(1, 2, figsize=(13, 5))
    axes[0].bar(cost_phase["cost_phase"], cost_phase["gross_margin"] * 100, color=["#8fb8de", "#76a66f"])
    axes[0].set_title("Margin Before and After Cost Optimization")
    axes[0].set_ylabel("Gross margin %")
    axes[0].tick_params(axis="x", rotation=12)
    style_axis(axes[0])

    axes[1].plot(monthly["month"], monthly["gross_margin"] * 100, color="#c45a4f", marker="o", linewidth=2.5)
    axes[1].set_title("Monthly Gross Margin Progression")
    axes[1].set_ylabel("Gross margin %")
    style_axis(axes[1])
    fig.tight_layout()
    fig.savefig(FIGURE_DIR / "margin_analysis.png", dpi=180)
    plt.close(fig)


def save_festival_heatmap(actual: pd.DataFrame) -> None:
    dow_order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    pivot = (
        actual.pivot_table(index="day_of_week", columns="month", values="units_sold", aggfunc="mean")
        .reindex(dow_order)
        .round(1)
    )
    fig, ax = plt.subplots(figsize=(11, 5.5))
    image = ax.imshow(pivot.values, cmap="YlGnBu", aspect="auto")
    ax.set_xticks(np.arange(len(pivot.columns)))
    ax.set_xticklabels(pivot.columns)
    ax.set_yticks(np.arange(len(pivot.index)))
    ax.set_yticklabels(pivot.index)
    for i in range(len(pivot.index)):
        for j in range(len(pivot.columns)):
            value = pivot.iloc[i, j]
            ax.text(j, i, f"{value:.0f}", ha="center", va="center", color="#1c1c1c", fontsize=9)
    ax.set_title("Seasonal Demand Heatmap: Average Units Sold")
    cbar = fig.colorbar(image, ax=ax)
    cbar.set_label("Avg units")
    fig.tight_layout()
    fig.savefig(FIGURE_DIR / "seasonal_demand_heatmap.png", dpi=180)
    plt.close(fig)


def save_volatility_delay_impact(stress: pd.DataFrame) -> None:
    monthly_delay = stress.groupby("month", as_index=False)["revenue_at_risk_from_delay"].sum()
    delayed_days = stress[stress["delay_flag"] == 1]

    fig, axes = plt.subplots(2, 1, figsize=(13, 8), gridspec_kw={"height_ratios": [1.3, 1]})
    axes[0].plot(stress["date"], stress["stress_revenue_pre_delay"], color="#8fb8de", linewidth=1.8, label="Revenue before delay impact")
    axes[0].plot(stress["date"], stress["stress_revenue"], color="#2f4858", linewidth=1.8, label="Revenue after delay impact")
    axes[0].scatter(delayed_days["date"], delayed_days["stress_revenue"], color="#c45a4f", s=26, label="Simulated delay day", zorder=3)
    axes[0].set_title("Volatility and Procurement Delay Stress Test")
    axes[0].set_ylabel("INR")
    axes[0].legend(frameon=False, ncol=3)
    style_axis(axes[0])

    axes[1].bar(monthly_delay["month"], monthly_delay["revenue_at_risk_from_delay"], color="#c45a4f")
    axes[1].set_title("Monthly Revenue at Risk from Delivery Disruptions")
    axes[1].set_ylabel("INR")
    style_axis(axes[1])
    fig.tight_layout()
    fig.savefig(FIGURE_DIR / "volatility_delay_impact.png", dpi=180)
    plt.close(fig)


def save_outputs() -> dict[str, str]:
    ensure_output_dirs()
    actual = load_actuals()
    basic = generate_basic_forecast()
    advanced = load_advanced_forecast()
    stress = build_stress_test_forecast(advanced)
    comparison = build_comparison(actual, basic, advanced)

    (
        executive_kpis,
        monthly,
        model_comparison,
        forecast_monthly,
        festival,
        cost_phase,
    ) = build_kpi_tables(actual, basic, advanced, comparison, stress)

    actual.to_csv(PROCESSED_DIR / "actual_clean.csv", index=False)
    basic.to_csv(PROCESSED_DIR / "basic_forecast_rebuilt.csv", index=False)
    advanced.to_csv(PROCESSED_DIR / "advanced_forecast_clean.csv", index=False)
    stress.to_csv(PROCESSED_DIR / "advanced_stress_test_forecast.csv", index=False)
    comparison.to_csv(PROCESSED_DIR / "daily_forecast_comparison.csv", index=False)
    executive_kpis.to_csv(PROCESSED_DIR / "executive_kpis.csv", index=False)
    monthly.to_csv(PROCESSED_DIR / "monthly_kpis.csv", index=False)
    model_comparison.to_csv(PROCESSED_DIR / "model_comparison.csv", index=False)
    forecast_monthly.to_csv(PROCESSED_DIR / "monthly_forecast_comparison.csv", index=False)
    festival.to_csv(PROCESSED_DIR / "festival_analysis.csv", index=False)
    cost_phase.to_csv(PROCESSED_DIR / "cost_phase_analysis.csv", index=False)

    save_revenue_profit_trend(actual)
    save_monthly_dashboard(monthly)
    save_forecast_vs_actual(forecast_monthly)
    save_margin_analysis(cost_phase, monthly)
    save_festival_heatmap(actual)
    save_volatility_delay_impact(stress)

    summary = {
        "actual_revenue": float(actual["revenue"].sum()),
        "actual_profit": float(actual["profit"].sum()),
        "actual_margin": float(actual["profit"].sum() / actual["revenue"].sum()),
        "total_units_sold": int(actual["units_sold"].sum()),
        "basic_revenue_bias_pct": float(model_comparison.loc[model_comparison["model"] == "Basic", "revenue_bias_pct"].iloc[0]),
        "advanced_revenue_bias_pct": float(model_comparison.loc[model_comparison["model"] == "Advanced", "revenue_bias_pct"].iloc[0]),
        "simulated_delay_revenue_at_risk": float(stress["revenue_at_risk_from_delay"].sum()),
        "figure_count": len(list(FIGURE_DIR.glob("*.png"))),
    }
    (ROOT / "outputs" / "serene_scents_executive_summary.json").write_text(
        json.dumps(summary, indent=2),
        encoding="utf-8",
    )
    return {key: str(value) for key, value in summary.items()}


if __name__ == "__main__":
    result = save_outputs()
    print(json.dumps(result, indent=2))
