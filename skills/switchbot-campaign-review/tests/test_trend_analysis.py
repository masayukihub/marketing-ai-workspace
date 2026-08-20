from __future__ import annotations

import sys
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))

import pandas as pd

from analyze_trends import (
    build_action_plan,
    build_budget_recommendations,
    build_channel_evaluation,
    build_trend_table,
    classify_trend,
    role_for_channel,
)


def test_three_period_improvement() -> None:
    trend, confidence = classify_trend([1.0, 1.2, 1.5], higher_is_better=True)
    assert trend == "Sustained improvement"
    assert confidence in {"High", "Medium"}


def test_three_period_cost_decline_is_improvement() -> None:
    trend, _ = classify_trend([100, 80, 60], higher_is_better=False)
    assert trend == "Sustained improvement"


def test_monotonic_cost_decline_with_one_small_step_is_improvement() -> None:
    trend, _ = classify_trend([17.11, 16.44, 14.78], higher_is_better=False)
    assert trend == "Sustained improvement"


def test_two_periods_do_not_become_long_term_trend() -> None:
    trend, confidence = classify_trend([1.0, 2.0], higher_is_better=True)
    assert trend == "Insufficient history"
    assert confidence == "Low"


def test_reversals_are_high_volatility() -> None:
    trend, confidence = classify_trend([100, 150, 80, 160], higher_is_better=True)
    assert trend == "High volatility"
    assert confidence == "Medium"


def test_spend_increase_is_not_labeled_as_performance_improvement() -> None:
    overall = pd.DataFrame(
        {
            "period": ["2024", "2025", "2026"],
            "spend": [100, 120, 150],
            "revenue": [100, 120, 150],
        }
    )
    channels = pd.DataFrame(columns=["period", "channel"])
    trend = build_trend_table(overall, channels)
    spend = trend.loc[trend["Metric"].eq("spend")].iloc[0]
    assert spend["Trend"] == "Sustained increase"


def test_budget_index_and_action_match_slight_increase_direction() -> None:
    evaluation = pd.DataFrame(
        [
            {
                "Channel": "KOL",
                "Current Share": 0.16,
                "Decision": "Slightly Increase",
                "Evidence": "Cost/View improved",
                "Confidence": "Medium",
                "Risk": "Long-tail views may be incomplete.",
                "Primary Problem": "Long-tail views may be incomplete.",
            }
        ]
    )
    budget = build_budget_recommendations(evaluation)
    assert budget.iloc[0]["Recommended Budget Index"] == 1.1
    assert "Recommended Share" not in budget.columns
    actions = build_action_plan(evaluation, pd.DataFrame())
    assert "小幅增加 KOL" in actions.iloc[0]["Action"]


def test_brand_video_is_not_rejected_for_low_direct_roas() -> None:
    channels = pd.DataFrame(
        [
            {
                "period": "2031",
                "channel": "YouTube Ads",
                "spend": 100,
                "conversions": 1,
                "revenue": 5,
                "roas": 0.05,
                "views": 1000,
                "cost_per_view": 0.10,
                "revenue_contribution": 0.01,
                "spend_share": 0.20,
            },
            {
                "period": "2032",
                "channel": "YouTube Ads",
                "spend": 120,
                "conversions": 1,
                "revenue": 6,
                "roas": 0.05,
                "views": 1200,
                "cost_per_view": 0.10,
                "revenue_contribution": 0.01,
                "spend_share": 0.20,
            },
        ]
    )
    result = build_channel_evaluation(channels, "2032", "2031").iloc[0]
    assert result["Role"] == "Brand / Video"
    assert result["Decision"] == "Maintain"
    assert "Direct ROAS is not a complete" in result["Risk"]


def test_channel_roles_use_channel_specific_evaluation_families() -> None:
    assert role_for_channel("Google Ads") == "Performance Media"
    assert role_for_channel("YouTube Ads") == "Brand / Video"
    assert role_for_channel("PR") == "PR"
    assert role_for_channel("KOL") == "KOL / Influencer"
    assert role_for_channel("LINE") == "CRM"
    assert role_for_channel("Instagram") == "SNS / Organic"

    channels = pd.DataFrame(
        [
            {
                "period": "2032",
                "channel": "PR",
                "spend": 100,
                "impressions": 10000,
                "reach": 8000,
                "revenue": pd.NA,
            },
            {
                "period": "2032",
                "channel": "Instagram",
                "spend": 50,
                "views": 5000,
                "engagements": 500,
                "revenue": pd.NA,
            },
        ]
    )
    result = build_channel_evaluation(channels, "2032", None).set_index("Channel")
    assert result.loc["PR", "Decision"] == "Continue Testing"
    assert result.loc["Instagram", "Decision"] == "Continue Testing"
    assert "Tracked revenue does not capture all" in result.loc["PR", "Risk"]


def test_channel_yoy_and_expansion_are_downgraded_when_scope_is_not_comparable() -> None:
    channels = pd.DataFrame(
        [
            {
                "period": "2031",
                "channel": "Google Ads",
                "spend": 100,
                "conversions": 10,
                "revenue": 150,
                "roas": 1.5,
                "revenue_contribution": 0.50,
                "spend_share": 0.40,
                "revenue_contribution_gap": 0.10,
            },
            {
                "period": "2032",
                "channel": "Google Ads",
                "spend": 120,
                "conversions": 12,
                "revenue": 240,
                "roas": 2.0,
                "revenue_contribution": 0.60,
                "spend_share": 0.45,
                "revenue_contribution_gap": 0.15,
            },
        ]
    )
    normalized = pd.DataFrame(
        {
            "period": ["2031", "2032", "2032"],
            "date": ["2031-01-01", "2032-01-01", "2032-01-02"],
            "channel": ["Google Ads"] * 3,
            "currency": ["JPY"] * 3,
        }
    )
    result = build_channel_evaluation(
        channels,
        "2032",
        "2031",
        normalized,
    ).iloc[0]
    assert result["YoY Change"] == "Not Comparable"
    assert result["Decision"] == "Continue Testing"
    assert result["Confidence"] == "Low"
    assert "Comparison blocked" in result["Risk"]


def test_three_period_path_is_blocked_when_periods_are_not_comparable() -> None:
    overall = pd.DataFrame(
        {
            "period": ["2030", "2031", "2032"],
            "spend": [100, 110, 120],
            "revenue": [200, 220, 240],
        }
    )
    normalized = pd.DataFrame(
        {
            "period": ["2030", "2031", "2032", "2032"],
            "date": ["2030-01-01", "2031-01-01", "2032-01-01", "2032-01-02"],
            "channel": ["Google Ads"] * 4,
            "currency": ["JPY"] * 4,
        }
    )
    trend = build_trend_table(
        overall,
        pd.DataFrame(columns=["period", "channel"]),
        normalized,
    )
    revenue = trend.loc[trend["Metric"].eq("revenue")].iloc[0]
    assert revenue["Trend"] == "Insufficient comparable history"
    assert revenue["Confidence"] == "Low"


def test_action_plan_covers_needs_confirmation_with_owner_timing_and_metric() -> None:
    issues = pd.DataFrame(
        [
            {
                "Severity": "Warning",
                "Repair Class": "Needs confirmation",
                "Issue Type": "Mixed percentage scale",
            }
        ]
    )
    actions = build_action_plan(pd.DataFrame(), issues)
    assert set(
        [
            "Action",
            "Problem Solved",
            "Data Evidence",
            "Owner Suggestion",
            "Deadline",
            "Priority",
            "Success Metric",
        ]
    ).issubset(actions.columns)
    assert actions.iloc[0]["Owner Suggestion"]
    assert actions.iloc[0]["Deadline"]
    assert actions.iloc[0]["Success Metric"]
