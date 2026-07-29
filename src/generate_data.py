"""Generate a reproducible synthetic marketing campaign dataset.

The data is deliberately synthetic so the project can be shared publicly while
still representing realistic marketing KPIs and business trade-offs.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

DEFAULT_OUTPUT = Path("data/marketing_campaign_data.csv")
RANDOM_SEED = 42


def generate_dataset(
    output_path: Path | str = DEFAULT_OUTPUT,
    seed: int = RANDOM_SEED,
) -> pd.DataFrame:
    """Create daily campaign-channel observations for a UK-focused retailer."""
    output_path = Path(output_path)
    rng = np.random.default_rng(seed)

    dates = pd.date_range("2025-01-01", "2025-12-31", freq="D")
    channel_config = {
        "Paid Search": {
            "impressions": 9_000, "ctr": 0.047, "cvr": 0.045, "cpm": 0.0, "cpc": 1.70
        },
        "Paid Social": {
            "impressions": 14_000, "ctr": 0.024, "cvr": 0.029, "cpm": 8.0, "cpc": 0.65
        },
        "Email": {
            "impressions": 7_500, "ctr": 0.072, "cvr": 0.032, "cpm": 18.0, "cpc": 0.18
        },
        "Display": {
            "impressions": 18_000, "ctr": 0.010, "cvr": 0.014, "cpm": 6.5, "cpc": 0.35
        },
    }
    campaigns = ["Always On", "Product Launch", "Seasonal Sale", "Retention"]
    segments = ["New Prospects", "Returning Customers", "High Value", "Price Sensitive"]
    regions = ["London", "Midlands", "North", "Scotland", "Wales"]
    rows: list[dict[str, object]] = []

    for day_index, date in enumerate(dates):
        annual_wave = 1 + 0.14 * np.sin(2 * np.pi * day_index / 365)
        q4_uplift = 1.22 if date.month in (11, 12) else 1.0
        weekend_factor = 1.08 if date.dayofweek >= 5 else 1.0

        for channel, cfg in channel_config.items():
            campaign = rng.choice(campaigns, p=[0.45, 0.17, 0.23, 0.15])
            segment = rng.choice(segments, p=[0.38, 0.31, 0.14, 0.17])
            region = rng.choice(regions, p=[0.33, 0.23, 0.22, 0.13, 0.09])
            variant = rng.choice(["A", "B"])
            device = rng.choice(["Mobile", "Desktop", "Tablet"], p=[0.62, 0.31, 0.07])

            campaign_factor = {
                "Always On": 1.00,
                "Product Launch": 1.15,
                "Seasonal Sale": 1.28,
                "Retention": 0.82,
            }[campaign]
            segment_cvr_factor = {
                "New Prospects": 0.78,
                "Returning Customers": 1.24,
                "High Value": 1.43,
                "Price Sensitive": 0.91,
            }[segment]
            mobile_ctr_factor = 1.08 if device == "Mobile" else 1.0
            variant_ctr_factor = 1.05 if variant == "B" else 1.0
            variant_cvr_factor = 1.08 if variant == "B" else 1.0

            expected_impressions = (
                cfg["impressions"]
                * annual_wave
                * q4_uplift
                * weekend_factor
                * campaign_factor
            )
            impressions = max(500, int(rng.poisson(expected_impressions)))

            ctr = float(
                np.clip(
                    cfg["ctr"]
                    * mobile_ctr_factor
                    * variant_ctr_factor
                    * rng.normal(1.0, 0.08),
                    0.002,
                    0.20,
                )
            )
            clicks = int(rng.binomial(impressions, ctr))

            cvr = float(
                np.clip(
                    cfg["cvr"]
                    * segment_cvr_factor
                    * variant_cvr_factor
                    * rng.normal(1.0, 0.10),
                    0.003,
                    0.25,
                )
            )
            conversions = int(rng.binomial(clicks, cvr)) if clicks else 0

            media_cost = (impressions / 1_000) * cfg["cpm"] + clicks * cfg["cpc"]
            spend = max(20.0, media_cost * rng.normal(1.0, 0.06))
            base_order_value = {
                "New Prospects": 72,
                "Returning Customers": 89,
                "High Value": 148,
                "Price Sensitive": 61,
            }[segment]
            revenue = max(
                0.0,
                conversions * base_order_value * rng.normal(1.0, 0.12),
            )

            rows.append(
                {
                    "date": date.date().isoformat(),
                    "campaign": campaign,
                    "channel": channel,
                    "customer_segment": segment,
                    "region": region,
                    "device": device,
                    "ab_variant": variant,
                    "impressions": impressions,
                    "clicks": clicks,
                    "conversions": conversions,
                    "spend_gbp": round(spend, 2),
                    "revenue_gbp": round(revenue, 2),
                }
            )

    dataframe = pd.DataFrame(rows).sort_values(["date", "channel"]).reset_index(drop=True)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    dataframe.to_csv(output_path, index=False)
    return dataframe


if __name__ == "__main__":
    df = generate_dataset()
    print(f"Generated {len(df):,} rows at {DEFAULT_OUTPUT}")
