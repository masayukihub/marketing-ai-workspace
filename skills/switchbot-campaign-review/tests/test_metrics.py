from __future__ import annotations

import math
import sys
from pathlib import Path

import pandas as pd
import pytest

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))

from calculate_metrics import (
    add_contributions,
    aggregate_metrics,
    build_yoy_table,
    select_periods,
)
from common import safe_divide


def test_safe_divide_handles_zero_and_missing() -> None:
    assert math.isnan(safe_divide(10, 0))
    assert math.isnan(safe_divide(None, 2))
    assert safe_divide(10, 2) == 5


def test_weighted_metrics_use_summed_numerators_and_denominators() -> None:
    frame = pd.DataFrame(
        {
            "period": ["2026", "2026"],
            "spend": [100, 900],
            "budget": [200, 1000],
            "impressions": [100, 900],
            "clicks": [20, 45],
            "conversions": [10, 9],
            "revenue": [300, 900],
        }
    )
    result = aggregate_metrics(frame, ["period"]).iloc[0]
    assert result["ctr"] == pytest.approx(65 / 1000)
    assert result["cpc"] == pytest.approx(1000 / 65)
    assert result["cpm"] == pytest.approx(1000)
    assert result["cvr"] == pytest.approx(19 / 65)
    assert result["cpa"] == pytest.approx(1000 / 19)
    assert result["roas"] == pytest.approx(1.2)
    assert result["budget_utilization"] == pytest.approx(1000 / 1200)


def test_yoy_and_zero_previous_are_not_comparable() -> None:
    overall = pd.DataFrame(
        [
            {"period": "2025", "spend": 0, "budget": 100, "impressions": 100, "clicks": 10, "conversions": 1, "revenue": 0, "ctr": 0.1, "cpc": 0, "cpm": 0, "cvr": 0.1, "cpa": 0, "roas": math.nan},
            {"period": "2026", "spend": 100, "budget": 100, "impressions": 120, "clicks": 12, "conversions": 2, "revenue": 200, "ctr": 0.1, "cpc": 8.3333, "cpm": 833.3333, "cvr": 1 / 6, "cpa": 50, "roas": 2},
        ]
    )
    raw = pd.DataFrame(
        {
            "period": ["2025", "2026"],
            "currency": ["JPY", "JPY"],
            "tax_basis": ["Tax Included", "Tax Included"],
            "attribution_window": ["7-day click", "7-day click"],
        }
    )
    yoy = build_yoy_table(overall, raw, "2026", "2025")
    spend = yoy.loc[yoy["Metric"].eq("spend")].iloc[0]
    assert spend["Status"] == "Not Comparable"
    conversions = yoy.loc[yoy["Metric"].eq("conversions")].iloc[0]
    assert conversions["YoY"] == pytest.approx(1.0)
    assert (
        conversions["Comparability Note"]
        == "No comparability issue detected for the available scope fields."
    )


def test_zero_denominators_stay_blank_instead_of_zero_or_infinity() -> None:
    frame = pd.DataFrame(
        {
            "period": ["2032"],
            "budget": [0],
            "spend": [0],
            "impressions": [0],
            "reach": [0],
            "clicks": [0],
            "conversions": [0],
            "revenue": [0],
        }
    )
    result = aggregate_metrics(frame, ["period"]).iloc[0]
    for metric in ("ctr", "cpc", "cpm", "cvr", "cpa", "roas", "budget_utilization", "frequency"):
        assert pd.isna(result[metric]), metric


def test_mixed_currency_never_creates_cross_currency_monetary_totals_or_shares() -> None:
    frame = pd.DataFrame(
        {
            "period": ["2032", "2032"],
            "channel": ["Google Ads", "Meta Ads"],
            "currency": ["JPY", "USD"],
            "budget": [1000, 1000],
            "spend": [800, 900],
            "impressions": [10000, 20000],
            "clicks": [100, 200],
            "conversions": [10, 20],
            "revenue": [1600, 1800],
        }
    )
    overall = aggregate_metrics(frame, ["period"]).iloc[0]
    assert overall["currency_scope"] == "Mixed"
    assert pd.isna(overall["spend"])
    assert pd.isna(overall["revenue"])
    assert overall["clicks"] == 300
    assert overall["ctr"] == pytest.approx(300 / 30000)

    channels = add_contributions(aggregate_metrics(frame, ["period", "channel"]))
    assert channels["spend_share"].isna().all()
    assert channels["revenue_contribution"].isna().all()


def test_attribution_window_difference_blocks_conversion_metrics_only() -> None:
    overall = pd.DataFrame(
        [
            {"period": "2031", "budget": 100, "spend": 100, "impressions": 1000, "clicks": 100, "conversions": 10, "revenue": 200, "ctr": 0.1, "cpc": 1, "cpm": 100, "cvr": 0.1, "cpa": 10, "roas": 2},
            {"period": "2032", "budget": 120, "spend": 110, "impressions": 1100, "clicks": 110, "conversions": 11, "revenue": 220, "ctr": 0.1, "cpc": 1, "cpm": 100, "cvr": 0.1, "cpa": 10, "roas": 2},
        ]
    )
    raw = pd.DataFrame(
        {
            "period": ["2031", "2032"],
            "currency": ["JPY", "JPY"],
            "tax_basis": ["Tax Included", "Tax Included"],
            "attribution_window": ["1-day click", "7-day click"],
        }
    )
    yoy = build_yoy_table(overall, raw, "2032", "2031").set_index("Metric")
    assert yoy.loc["spend", "Status"] == "Comparable"
    assert yoy.loc["clicks", "Status"] == "Comparable"
    for metric in ("conversions", "revenue", "cvr", "cpa", "roas"):
        assert yoy.loc[metric, "Status"] == "Not Comparable"


def test_date_granularity_difference_blocks_yoy() -> None:
    overall = pd.DataFrame(
        [
            {"period": "2031", "budget": 100, "spend": 100, "impressions": 1000, "clicks": 100, "conversions": 10, "revenue": 200, "ctr": 0.1, "cpc": 1, "cpm": 100, "cvr": 0.1, "cpa": 10, "roas": 2},
            {"period": "2032", "budget": 120, "spend": 110, "impressions": 1100, "clicks": 110, "conversions": 11, "revenue": 220, "ctr": 0.1, "cpc": 1, "cpm": 100, "cvr": 0.1, "cpa": 10, "roas": 2},
        ]
    )
    raw = pd.DataFrame(
        {
            "period": ["2031", "2032", "2032"],
            "date": ["2031-11-20", "2032-11-20", "2032-11-21"],
            "currency": ["JPY", "JPY", "JPY"],
        }
    )
    yoy = build_yoy_table(overall, raw, "2032", "2031")
    assert set(yoy["Status"]) == {"Not Comparable"}
    assert yoy["Comparability Note"].str.contains("granularity differs").all()


def test_period_selection_supports_future_non_prime_campaigns() -> None:
    data = pd.DataFrame({"period": ["2030 Launch", "2031 Launch", "2032 Launch"]})
    assert select_periods(data) == ("2032 Launch", "2031 Launch")
