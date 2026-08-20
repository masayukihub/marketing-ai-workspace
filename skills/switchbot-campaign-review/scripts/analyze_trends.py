#!/usr/bin/env python3
"""Classify multi-period trends and create channel, budget, and action recommendations."""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Any, Iterable

import numpy as np
import pandas as pd

from calculate_metrics import (
    HIGHER_IS_BETTER,
    LOWER_IS_BETTER,
    comparability_reasons,
    metric_blocked_by_reasons,
    sorted_periods,
)
from common import LOGGER, configure_logging, safe_divide

CONTEXT_METRICS = {"spend", "budget", "impressions", "sends", "frequency"}


def classify_trend(values: Iterable[float], higher_is_better: bool = True) -> tuple[str, str]:
    clean = np.array([float(value) for value in values if pd.notna(value)], dtype=float)
    if len(clean) < 3:
        return "Insufficient history", "Low"
    previous = clean[:-1]
    current = clean[1:]
    changes = np.divide(current - previous, np.where(previous == 0, np.nan, np.abs(previous)))
    changes = changes[np.isfinite(changes)]
    if len(changes) < 2:
        return "Insufficient comparable history", "Low"
    effective = changes if higher_is_better else -changes
    coefficient = float(np.nanstd(clean) / abs(np.nanmean(clean))) if np.nanmean(clean) else math.inf

    if np.all(effective > 0.05):
        return "Sustained improvement", "High" if coefficient < 0.5 else "Medium"
    if np.all(effective < -0.05):
        return "Sustained deterioration", "High" if coefficient < 0.5 else "Medium"
    if np.all(np.abs(changes) <= 0.05):
        return "Stable", "High"
    cumulative_change = safe_divide(clean[-1] - clean[0], abs(clean[0]))
    cumulative_effective = cumulative_change if higher_is_better else -cumulative_change
    if np.all(effective > 0) and pd.notna(cumulative_effective) and cumulative_effective > 0.05:
        return "Sustained improvement", "High" if coefficient < 0.5 else "Medium"
    if np.all(effective < 0) and pd.notna(cumulative_effective) and cumulative_effective < -0.05:
        return "Sustained deterioration", "High" if coefficient < 0.5 else "Medium"
    if coefficient >= 0.3 or np.any(np.sign(effective[1:]) != np.sign(effective[:-1])):
        return "High volatility", "Medium"
    return "Mixed change", "Medium"


def role_for_channel(channel: str) -> str:
    token = channel.lower()
    if any(name in token for name in ("google", "meta", "yahoo ads", "amazon ads", "smartnews")):
        return "Performance Media"
    if "youtube" in token:
        return "Brand / Video"
    if token in {"pr"}:
        return "PR"
    if any(name in token for name in ("kol", "influencer")):
        return "KOL / Influencer"
    if any(name in token for name in ("edm", "line", "push")):
        return "CRM"
    if token == "x" or any(name in token for name in ("sns", "organic", "instagram", "tiktok")):
        return "SNS / Organic"
    return "Other / Mixed"


def relative_change(current: Any, previous: Any) -> float:
    return safe_divide(
        float(current) - float(previous) if pd.notna(current) and pd.notna(previous) else math.nan,
        previous,
    )


def _row(frame: pd.DataFrame, period: str | None, channel: str) -> pd.Series | None:
    if not period:
        return None
    match = frame.loc[
        frame["period"].astype(str).eq(str(period)) & frame["channel"].astype(str).eq(channel)
    ]
    return match.iloc[0] if not match.empty else None


def decide_channel(
    current: pd.Series,
    previous: pd.Series | None,
    role: str,
    period_count: int,
) -> tuple[str, str, str, str]:
    confidence = "High" if period_count >= 3 else "Medium" if period_count == 2 else "Low"
    evidence: list[str] = []
    risk = "Attribution and channel-role differences may limit direct comparison."
    decision = "Insufficient Data"

    spend = current.get("spend")
    revenue = current.get("revenue")
    roas = current.get("roas")
    revenue_gap = current.get("revenue_contribution_gap")
    views = current.get("views")
    clicks = current.get("clicks")
    conversions = current.get("conversions")

    if role == "Performance Media":
        if pd.isna(spend) or pd.isna(roas):
            return decision, "Spend or attributable revenue is missing.", confidence, risk
        previous_roas = previous.get("roas") if previous is not None else math.nan
        roas_change = relative_change(roas, previous_roas)
        evidence.append(f"ROAS={roas:.2f}")
        if pd.notna(revenue_gap):
            evidence.append(f"revenue contribution gap={revenue_gap:.1%}")
        if pd.notna(roas_change):
            evidence.append(f"ROAS change={roas_change:.1%}")
        if pd.notna(revenue_gap) and revenue_gap >= 0.05 and roas >= 1:
            decision = "Expand"
        elif pd.notna(roas_change) and roas_change >= 0.1 and (pd.isna(revenue_gap) or revenue_gap >= 0):
            decision = "Slightly Increase"
        elif roas >= 1.5:
            decision = "Maintain"
        elif roas >= 1:
            decision = "Optimize and Continue"
        else:
            decision = "Slightly Reduce"
    elif role == "Brand / Video":
        if pd.isna(views) and pd.isna(current.get("impressions")):
            return decision, "Views and Impressions are both missing.", confidence, risk
        cpv = current.get("cost_per_view")
        previous_cpv = previous.get("cost_per_view") if previous is not None else math.nan
        cpv_change = relative_change(cpv, previous_cpv)
        evidence.append(f"Views={views:,.0f}" if pd.notna(views) else "Views=Not Available")
        if pd.notna(cpv):
            evidence.append(f"Cost/View={cpv:.2f}")
        decision = "Slightly Increase" if pd.notna(cpv_change) and cpv_change <= -0.1 else "Maintain"
        risk = "Direct ROAS is not a complete brand-media measure; brand search and assisted conversion may be missing."
    elif role == "KOL / Influencer":
        if pd.isna(views):
            return decision, "Creator views are missing.", confidence, risk
        cpv = current.get("cost_per_view")
        previous_cpv = previous.get("cost_per_view") if previous is not None else math.nan
        cpv_change = relative_change(cpv, previous_cpv)
        evidence.append(f"Views={views:,.0f}")
        if pd.notna(cpv):
            evidence.append(f"Cost/View={cpv:.2f}")
        decision = "Slightly Increase" if pd.notna(cpv_change) and cpv_change <= -0.1 else "Optimize and Continue"
        risk = "Content quality, creator fit, affiliate sales, and long-tail views may be incomplete."
    elif role == "CRM":
        delivered = current.get("delivered")
        if pd.isna(delivered) or pd.isna(clicks):
            return decision, "Delivered or Clicks is missing.", confidence, risk
        click_rate = current.get("crm_click_rate")
        previous_rate = previous.get("crm_click_rate") if previous is not None else math.nan
        rate_change = relative_change(click_rate, previous_rate)
        evidence.append(f"Delivered={delivered:,.0f}")
        evidence.append(f"Click rate={click_rate:.2%}" if pd.notna(click_rate) else "Click rate=Not Available")
        decision = "Slightly Increase" if pd.notna(rate_change) and rate_change >= 0.1 and pd.notna(conversions) else "Maintain"
        risk = "Unique users, overlap, and post-click attribution may be missing."
    elif role in {"PR", "SNS / Organic"}:
        observable = [current.get(metric) for metric in ("impressions", "reach", "views", "engagements", "clicks")]
        if all(pd.isna(value) for value in observable):
            return decision, "No exposure, engagement, or traffic metric is available.", confidence, risk
        decision = "Continue Testing" if pd.isna(revenue) else "Maintain"
        evidence.append("Observable reach/engagement data is available.")
        risk = "Tracked revenue does not capture all earned-media or organic value."
    else:
        decision = "Continue Testing" if any(pd.notna(current.get(metric)) for metric in ("spend", "clicks", "views")) else "Insufficient Data"
        evidence.append("Channel role requires business confirmation.")

    return decision, "; ".join(evidence), confidence, risk


def build_trend_table(
    overall: pd.DataFrame,
    channels: pd.DataFrame,
    normalized: pd.DataFrame | None = None,
) -> pd.DataFrame:
    records: list[dict[str, Any]] = []
    metrics = ["spend", "revenue", "conversions", "ctr", "cpc", "cpm", "cvr", "cpa", "roas"]
    scopes = [("Overall", "All", overall)]
    for channel in sorted(channels["channel"].dropna().astype(str).unique()):
        scopes.append(("Channel", channel, channels.loc[channels["channel"].astype(str).eq(channel)]))

    for scope, entity, frame in scopes:
        ordered = frame.copy()
        ordered["_key"] = ordered["period"].map(lambda value: sorted_periods([value])[0] if sorted_periods([value]) else str(value))
        period_order = sorted_periods(ordered["period"])
        ordered["period"] = pd.Categorical(ordered["period"].astype(str), categories=period_order, ordered=True)
        ordered = ordered.sort_values("period")
        for metric in metrics:
            if metric not in ordered.columns or ordered[metric].notna().sum() == 0:
                continue
            values = ordered[metric].tolist()
            higher_is_better = metric not in LOWER_IS_BETTER
            blocking_reasons: list[str] = []
            if normalized is not None and len(period_order) >= 2:
                scope_data = normalized
                if scope == "Channel":
                    scope_data = normalized.loc[
                        normalized["channel"].astype(str).eq(str(entity))
                    ]
                for previous_period, current_period in zip(period_order, period_order[1:]):
                    pair_reasons = comparability_reasons(
                        scope_data,
                        str(current_period),
                        str(previous_period),
                    )
                    blocking_reasons.extend(
                        reason
                        for reason in pair_reasons
                        if metric_blocked_by_reasons(metric, [reason])
                    )
            if blocking_reasons:
                trend, confidence = "Insufficient comparable history", "Low"
            else:
                trend, confidence = classify_trend(values, higher_is_better=higher_is_better)
            if metric in CONTEXT_METRICS:
                trend = {
                    "Sustained improvement": "Sustained increase",
                    "Sustained deterioration": "Sustained decrease",
                }.get(trend, trend)
            records.append(
                {
                    "Scope": scope,
                    "Entity": entity,
                    "Metric": metric,
                    "Periods": " → ".join(ordered["period"].astype(str)),
                    "Values": " → ".join("" if pd.isna(value) else f"{value:.4g}" for value in values),
                    "Trend": trend,
                    "Confidence": confidence,
                    "Evidence": (
                        f"{len([value for value in values if pd.notna(value)])} usable period(s); "
                        f"comparability blocked by {blocking_reasons[0]}"
                        if blocking_reasons
                        else f"{len([value for value in values if pd.notna(value)])} usable period(s)"
                    ),
                }
            )
    return pd.DataFrame.from_records(records)


def build_channel_evaluation(
    channels: pd.DataFrame,
    current_period: str,
    comparison_period: str | None,
    normalized: pd.DataFrame | None = None,
) -> pd.DataFrame:
    records: list[dict[str, Any]] = []
    for channel in sorted(channels["channel"].dropna().astype(str).unique()):
        current = _row(channels, current_period, channel)
        if current is None:
            continue
        previous = _row(channels, comparison_period, channel)
        role = role_for_channel(channel)
        period_count = channels.loc[channels["channel"].astype(str).eq(channel), "period"].nunique()
        channel_reasons: list[str] = []
        yoy_blocked = False
        if normalized is not None and comparison_period:
            channel_data = normalized.loc[
                normalized["channel"].astype(str).eq(channel)
            ]
            channel_reasons = comparability_reasons(
                channel_data,
                str(current_period),
                str(comparison_period),
            )
            yoy_blocked = metric_blocked_by_reasons("roas", channel_reasons)
        comparison_row = None if yoy_blocked else previous
        decision, evidence, confidence, risk = decide_channel(
            current,
            comparison_row,
            role,
            1 if yoy_blocked else period_count,
        )
        if yoy_blocked:
            if decision == "Expand":
                decision = "Continue Testing"
            elif decision == "Slightly Increase":
                decision = "Maintain"
            confidence = "Low"
            blocking_reason = next(
                (
                    reason
                    for reason in channel_reasons
                    if metric_blocked_by_reasons("roas", [reason])
                ),
                "Period comparison is not reliable.",
            )
            risk = f"{risk} Comparison blocked: {blocking_reason}"
        elif role in {"Brand / Video", "KOL / Influencer", "CRM", "PR", "SNS / Organic"} and confidence == "High":
            confidence = "Medium"
        yoy_roas = relative_change(
            current.get("roas"),
            comparison_row.get("roas") if comparison_row is not None else math.nan,
        )
        records.append(
            {
                "Channel": channel,
                "Role": role,
                "Current Performance": (
                    f"Spend={current.get('spend', math.nan):,.0f}; "
                    f"Conversions={current.get('conversions', math.nan):,.0f}; "
                    f"ROAS={current.get('roas', math.nan):.2f}"
                ),
                "YoY Change": f"ROAS {yoy_roas:+.1%}" if pd.notna(yoy_roas) else "Not Comparable",
                "Primary Contribution": (
                    f"Revenue share={current.get('revenue_contribution', math.nan):.1%}; "
                    f"Spend share={current.get('spend_share', math.nan):.1%}"
                ),
                "Primary Problem": risk,
                "Decision": decision,
                "Evidence": evidence,
                "Confidence": confidence,
                "Risk": risk,
                "Current Share": current.get("spend_share"),
            }
        )
    return pd.DataFrame.from_records(records)


def build_budget_recommendations(channel_evaluation: pd.DataFrame) -> pd.DataFrame:
    if channel_evaluation.empty:
        return pd.DataFrame()
    factors = {
        "Expand": 1.20,
        "Slightly Increase": 1.10,
        "Maintain": 1.00,
        "Optimize and Continue": 1.00,
        "Slightly Reduce": 0.90,
        "Significantly Reduce": 0.70,
        "Pause": 0.00,
        "Continue Testing": 1.00,
        "Insufficient Data": 1.00,
    }
    frame = channel_evaluation.copy()
    frame["Recommended Budget Index"] = frame["Decision"].map(factors).fillna(1)
    return frame[
        [
            "Channel",
            "Current Share",
            "Recommended Budget Index",
            "Decision",
            "Evidence",
            "Confidence",
            "Risk",
        ]
    ].rename(columns={"Decision": "Direction"})


def build_action_plan(
    channel_evaluation: pd.DataFrame,
    issues: pd.DataFrame,
) -> pd.DataFrame:
    actions: list[dict[str, Any]] = []
    if not issues.empty:
        critical = issues.loc[issues["Severity"].astype(str).eq("Critical")]
        if not critical.empty:
            types = ", ".join(critical["Issue Type"].drop_duplicates().astype(str).head(4))
            actions.append(
                {
                    "Action": "在下次复盘前修复关键数据口径并补齐来源字段",
                    "Problem Solved": types,
                    "Data Evidence": f"{len(critical)} critical issue(s) in the quality report",
                    "Owner Suggestion": "Marketing Analytics + Channel Owners",
                    "Deadline": "Next campaign T-14",
                    "Priority": "P0",
                    "Success Metric": "Critical data-quality issues reduced to 0",
                }
            )
        needs_confirmation = issues.loc[
            issues["Repair Class"].astype(str).eq("Needs confirmation")
        ]
        if not needs_confirmation.empty:
            types = ", ".join(
                needs_confirmation["Issue Type"].drop_duplicates().astype(str).head(4)
            )
            actions.append(
                {
                    "Action": "逐项确认未映射字段、疑似重复和歧义格式，并记录保留或修复结论",
                    "Problem Solved": types,
                    "Data Evidence": (
                        f"{len(needs_confirmation)} needs-confirmation issue(s) "
                        "in the quality report"
                    ),
                    "Owner Suggestion": "Marketing Analytics + Source Owners",
                    "Deadline": "Next campaign T-14",
                    "Priority": "P1",
                    "Success Metric": "100%待确认问题均标记为已修复、明确保留或暂缓并说明原因",
                }
            )
    for _, row in channel_evaluation.iterrows():
        if row["Decision"] in {"Optimize and Continue", "Slightly Reduce", "Significantly Reduce", "Pause"}:
            actions.append(
                {
                    "Action": f"为 {row['Channel']} 制定两项效率修正测试并设置暂停阈值",
                    "Problem Solved": row["Primary Problem"],
                    "Data Evidence": row["Evidence"],
                    "Owner Suggestion": "Channel Owner + Performance Marketing",
                    "Deadline": "Next campaign T-14",
                    "Priority": "P1",
                    "Success Metric": "核心效率指标较本次改善至少10%，否则按阈值降档",
                }
            )
        elif row["Decision"] in {"Expand", "Slightly Increase"}:
            action_verb = "扩大" if row["Decision"] == "Expand" else "小幅增加"
            actions.append(
                {
                    "Action": f"在保留对照组的前提下{action_verb} {row['Channel']}，分阶段释放新增预算",
                    "Problem Solved": "放大已验证贡献并控制边际回报风险",
                    "Data Evidence": row["Evidence"],
                    "Owner Suggestion": "Marketing Director + Channel Owner",
                    "Deadline": "Budget lock date",
                    "Priority": "P1",
                    "Success Metric": "新增预算段的效率不低于本次基准90%",
                }
            )
        elif row["Decision"] in {"Continue Testing", "Insufficient Data"}:
            actions.append(
                {
                    "Action": f"保持 {row['Channel']} 预算不扩张，建立同周期、同归因口径的对照测试",
                    "Problem Solved": row["Primary Problem"],
                    "Data Evidence": row["Evidence"],
                    "Owner Suggestion": "Channel Owner + Marketing Analytics",
                    "Deadline": "Next campaign T-14",
                    "Priority": "P1",
                    "Success Metric": "获得至少一个可比周期，并明确渠道角色核心指标与预算升级阈值",
                }
            )
    if not actions:
        actions.append(
            {
                "Action": "补齐渠道级目标、归因窗口和结果指标后再做预算调整",
                "Problem Solved": "当前证据不足以形成稳健的资源配置结论",
                "Data Evidence": "Channel evaluation returned no actionable expansion or reduction signal",
                "Owner Suggestion": "Marketing Analytics",
                "Deadline": "Next campaign T-21",
                "Priority": "P1",
                "Success Metric": "All active channels have role-specific target and outcome fields",
            }
        )
    return pd.DataFrame.from_records(actions)


def analyze_trends(
    output_dir: Path,
    current_period: str | None = None,
    comparison_period: str | None = None,
) -> dict[str, Path]:
    intermediate = output_dir / "_intermediate"
    overall = pd.read_csv(intermediate / "overall_metrics.csv")
    channels = pd.read_csv(intermediate / "channel_metrics.csv")
    issues_path = intermediate / "quality_issues.csv"
    issues = pd.read_csv(issues_path) if issues_path.exists() and issues_path.stat().st_size else pd.DataFrame()
    normalized = pd.read_csv(intermediate / "normalized_data.csv")
    normalized["period"] = normalized["period"].astype(str)
    summary = json.loads((intermediate / "metrics_summary.json").read_text(encoding="utf-8"))
    current = current_period or str(summary["current_period"])
    comparison = comparison_period or summary.get("comparison_period")

    trend = build_trend_table(overall, channels, normalized)
    evaluation = build_channel_evaluation(
        channels,
        current,
        str(comparison) if comparison else None,
        normalized,
    )
    budget = build_budget_recommendations(evaluation)
    actions = build_action_plan(evaluation, issues)

    paths = {
        "trend": output_dir / "trend_analysis.csv",
        "channel_evaluation": output_dir / "channel_evaluation.csv",
        "action_plan": output_dir / "action_plan.csv",
        "budget": intermediate / "budget_recommendations.csv",
    }
    trend.to_csv(paths["trend"], index=False, encoding="utf-8-sig")
    evaluation.drop(columns=["Current Share"], errors="ignore").to_csv(
        paths["channel_evaluation"], index=False, encoding="utf-8-sig"
    )
    budget.to_csv(paths["budget"], index=False, encoding="utf-8-sig")
    actions.to_csv(paths["action_plan"], index=False, encoding="utf-8-sig")
    LOGGER.info("Created %d channel evaluations and %d actions", len(evaluation), len(actions))
    return paths


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--current-period")
    parser.add_argument("--comparison-period")
    parser.add_argument("--verbose", action="store_true")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    configure_logging(args.verbose)
    outputs = analyze_trends(
        args.output_dir.resolve(),
        args.current_period,
        args.comparison_period,
    )
    for name, path in outputs.items():
        print(f"{name}: {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
