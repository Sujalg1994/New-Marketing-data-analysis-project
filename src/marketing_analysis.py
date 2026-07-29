"""End-to-end marketing performance analysis.

Outputs executive KPIs, channel and segment performance, A/B test results,
monthly trends, and a rule-based budget recommendation.
"""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from statistics import NormalDist

import numpy as np
import pandas as pd

try:
    from src.generate_data import DEFAULT_OUTPUT, generate_dataset
except ModuleNotFoundError:
    from generate_data import DEFAULT_OUTPUT, generate_dataset

DEFAULT_OUTPUT_DIR = Path("outputs")


def safe_divide(numerator: pd.Series, denominator: pd.Series) -> pd.Series:
    """Vectorised division that returns zero when the denominator is zero."""
    denominator = denominator.replace(0, np.nan)
    return numerator.div(denominator).replace([np.inf, -np.inf], np.nan).fillna(0.0)


def add_kpis(dataframe: pd.DataFrame) -> pd.DataFrame:
    """Add row-level marketing KPIs using standard definitions."""
    df = dataframe.copy()
    required = {
        "impressions",
        "clicks",
        "conversions",
        "spend_gbp",
        "revenue_gbp",
    }
    missing = sorted(required.difference(df.columns))
    if missing:
        raise ValueError(f"Missing required columns: {', '.join(missing)}")

    df["ctr"] = safe_divide(df["clicks"], df["impressions"])
    df["conversion_rate"] = safe_divide(df["conversions"], df["clicks"])
    df["cpc_gbp"] = safe_divide(df["spend_gbp"], df["clicks"])
    df["cpa_gbp"] = safe_divide(df["spend_gbp"], df["conversions"])
    df["roas"] = safe_divide(df["revenue_gbp"], df["spend_gbp"])
    df["profit_gbp"] = df["revenue_gbp"] - df["spend_gbp"]
    df["romi"] = safe_divide(df["profit_gbp"], df["spend_gbp"])
    return df


def aggregate_performance(dataframe: pd.DataFrame, group_columns: list[str]) -> pd.DataFrame:
    """Aggregate raw totals first, then calculate non-additive KPIs correctly."""
    summary = (
        dataframe.groupby(group_columns, as_index=False)
        .agg(
            impressions=("impressions", "sum"),
            clicks=("clicks", "sum"),
            conversions=("conversions", "sum"),
            spend_gbp=("spend_gbp", "sum"),
            revenue_gbp=("revenue_gbp", "sum"),
        )
    )
    return add_kpis(summary).sort_values("revenue_gbp", ascending=False)


def two_proportion_z_test(
    conversions_a: int,
    clicks_a: int,
    conversions_b: int,
    clicks_b: int,
) -> dict[str, float | str]:
    """Compare conversion rates for variants A and B with a two-sided z-test."""
    if min(clicks_a, clicks_b) <= 0:
        raise ValueError("Both variants need at least one click.")

    rate_a = conversions_a / clicks_a
    rate_b = conversions_b / clicks_b
    pooled_rate = (conversions_a + conversions_b) / (clicks_a + clicks_b)
    standard_error = math.sqrt(
        pooled_rate * (1 - pooled_rate) * ((1 / clicks_a) + (1 / clicks_b))
    )
    z_score = 0.0 if standard_error == 0 else (rate_b - rate_a) / standard_error
    p_value = 2 * (1 - NormalDist().cdf(abs(z_score)))
    relative_lift = 0.0 if rate_a == 0 else (rate_b / rate_a) - 1

    return {
        "variant_a_conversion_rate": rate_a,
        "variant_b_conversion_rate": rate_b,
        "absolute_lift": rate_b - rate_a,
        "relative_lift": relative_lift,
        "z_score": z_score,
        "p_value": p_value,
        "decision": "Statistically significant" if p_value < 0.05 else "Not significant",
    }


def budget_recommendation(channel_summary: pd.DataFrame, total_budget: float) -> pd.DataFrame:
    """Allocate budget using profitability and conversion evidence, with guardrails."""
    result = channel_summary.copy()
    efficiency_score = (
        np.maximum(result["roas"] - 1, 0.05)
        * np.sqrt(np.maximum(result["conversions"], 1))
    )
    raw_share = efficiency_score / efficiency_score.sum()

    # Keep every tested channel active and prevent a single channel dominating.
    guarded_share = np.clip(raw_share, 0.10, 0.45)
    guarded_share = guarded_share / guarded_share.sum()

    result["recommended_budget_share"] = guarded_share
    result["recommended_budget_gbp"] = guarded_share * total_budget
    result["current_spend_share"] = result["spend_gbp"] / result["spend_gbp"].sum()
    result["share_change_pp"] = (
        result["recommended_budget_share"] - result["current_spend_share"]
    ) * 100
    return result.sort_values("recommended_budget_gbp", ascending=False)


def run_analysis(
    input_path: Path = DEFAULT_OUTPUT,
    output_dir: Path = DEFAULT_OUTPUT_DIR,
    planning_budget: float = 100_000,
) -> dict[str, object]:
    """Run the full workflow and write portfolio-ready outputs."""
    if not input_path.exists():
        generate_dataset(input_path)

    df = pd.read_csv(input_path, parse_dates=["date"])
    df = add_kpis(df)
    df["month"] = df["date"].dt.to_period("M").astype(str)

    channel = aggregate_performance(df, ["channel"])
    segment = aggregate_performance(df, ["customer_segment"])
    campaign = aggregate_performance(df, ["campaign"])
    monthly = aggregate_performance(df, ["month"]).sort_values("month")
    budget = budget_recommendation(channel, planning_budget)

    ab_counts = (
        df.groupby("ab_variant", as_index=True)
        .agg(clicks=("clicks", "sum"), conversions=("conversions", "sum"))
    )
    ab_result = two_proportion_z_test(
        conversions_a=int(ab_counts.loc["A", "conversions"]),
        clicks_a=int(ab_counts.loc["A", "clicks"]),
        conversions_b=int(ab_counts.loc["B", "conversions"]),
        clicks_b=int(ab_counts.loc["B", "clicks"]),
    )

    totals = {
        "impressions": int(df["impressions"].sum()),
        "clicks": int(df["clicks"].sum()),
        "conversions": int(df["conversions"].sum()),
        "spend_gbp": round(float(df["spend_gbp"].sum()), 2),
        "revenue_gbp": round(float(df["revenue_gbp"].sum()), 2),
    }
    totals["ctr"] = totals["clicks"] / totals["impressions"]
    totals["conversion_rate"] = totals["conversions"] / totals["clicks"]
    totals["cpa_gbp"] = totals["spend_gbp"] / totals["conversions"]
    totals["roas"] = totals["revenue_gbp"] / totals["spend_gbp"]
    totals["profit_gbp"] = totals["revenue_gbp"] - totals["spend_gbp"]

    best_channel = channel.sort_values("roas", ascending=False).iloc[0]
    best_segment = segment.sort_values("revenue_gbp", ascending=False).iloc[0]
    executive_summary = {
        "portfolio_note": "Results are based on reproducible synthetic data.",
        "overall_kpis": totals,
        "best_channel_by_roas": {
            "channel": best_channel["channel"],
            "roas": round(float(best_channel["roas"]), 3),
            "cpa_gbp": round(float(best_channel["cpa_gbp"]), 2),
        },
        "highest_revenue_segment": {
            "customer_segment": best_segment["customer_segment"],
            "revenue_gbp": round(float(best_segment["revenue_gbp"]), 2),
        },
        "ab_test": ab_result,
        "planning_budget_gbp": planning_budget,
    }

    output_dir.mkdir(parents=True, exist_ok=True)
    channel.to_csv(output_dir / "channel_performance.csv", index=False)
    segment.to_csv(output_dir / "segment_performance.csv", index=False)
    campaign.to_csv(output_dir / "campaign_performance.csv", index=False)
    monthly.to_csv(output_dir / "monthly_performance.csv", index=False)
    budget.to_csv(output_dir / "budget_recommendation.csv", index=False)
    pd.DataFrame([ab_result]).to_csv(output_dir / "ab_test_results.csv", index=False)
    (output_dir / "executive_summary.json").write_text(
        json.dumps(executive_summary, indent=2),
        encoding="utf-8",
    )

    return executive_summary


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run marketing campaign analysis.")
    parser.add_argument("--input", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--budget", type=float, default=100_000)
    return parser


if __name__ == "__main__":
    args = build_parser().parse_args()
    summary = run_analysis(args.input, args.output_dir, args.budget)
    kpis = summary["overall_kpis"]
    print(
        "Analysis complete | "
        f"Revenue: £{kpis['revenue_gbp']:,.0f} | "
        f"ROAS: {kpis['roas']:.2f}x | "
        f"CPA: £{kpis['cpa_gbp']:.2f}"
    )
