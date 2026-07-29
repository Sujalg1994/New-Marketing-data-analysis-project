import pandas as pd
import pytest

from src.marketing_analysis import add_kpis, two_proportion_z_test


def test_add_kpis_uses_correct_formulas():
    df = pd.DataFrame(
        {
            "impressions": [1_000],
            "clicks": [100],
            "conversions": [10],
            "spend_gbp": [200.0],
            "revenue_gbp": [600.0],
        }
    )
    result = add_kpis(df).iloc[0]
    assert result["ctr"] == pytest.approx(0.10)
    assert result["conversion_rate"] == pytest.approx(0.10)
    assert result["cpa_gbp"] == pytest.approx(20.0)
    assert result["roas"] == pytest.approx(3.0)
    assert result["romi"] == pytest.approx(2.0)


def test_two_proportion_test_detects_large_lift():
    result = two_proportion_z_test(
        conversions_a=50,
        clicks_a=1_000,
        conversions_b=90,
        clicks_b=1_000,
    )
    assert result["relative_lift"] > 0
    assert result["p_value"] < 0.05
    assert result["decision"] == "Statistically significant"
