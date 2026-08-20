#!/usr/bin/env python3
"""Run the complete SwitchBot Japan campaign review pipeline."""

from __future__ import annotations

import argparse
import html
import json
import math
from datetime import datetime
from pathlib import Path
from typing import Any

import pandas as pd
from jinja2 import Environment, FileSystemLoader, StrictUndefined, select_autoescape

from analyze_trends import analyze_trends
from build_charts import build_charts
from calculate_metrics import calculate_metrics
from clean_marketing_data import clean_marketing_data
from common import (
    LOGGER,
    configure_logging,
    dataframe_to_markdown,
    default_output_dir,
    write_json,
)

SKILL_DIR = Path(__file__).resolve().parent.parent
TEMPLATE_DIR = SKILL_DIR / "templates"

DISPLAY_COLUMNS_ZH = {
    "Metric": "指标",
    "Value": "数值",
    "Channel": "渠道",
    "Role": "渠道角色",
    "Current Performance": "当前表现",
    "YoY Change": "同比变化",
    "Primary Contribution": "主要贡献",
    "Primary Problem": "主要问题",
    "Decision": "决策建议",
    "Evidence": "数据依据",
    "Confidence": "置信度",
    "Risk": "潜在风险",
    "Current Share": "当前占比",
    "Recommended Share": "建议占比",
    "Recommended Budget Index": "建议预算指数（当前=1.00）",
    "Direction": "调整方向",
    "Previous Period": "对比周期",
    "Current Period": "当前周期",
    "Previous": "对比值",
    "Current": "当前值",
    "Absolute Change": "绝对变化",
    "YoY": "同比",
    "Status": "可比状态",
    "Business Interpretation": "业务解读",
    "Comparability Note": "可比性说明",
    "Scope": "范围",
    "Entity": "对象",
    "Periods": "周期",
    "Values": "数值序列",
    "Trend": "趋势",
    "Action": "行动",
    "Problem Solved": "解决问题",
    "Data Evidence": "数据依据",
    "Owner Suggestion": "负责人建议",
    "Deadline": "时间节点",
    "Priority": "优先级",
    "Success Metric": "验收指标",
    "channel": "渠道",
    "spend": "花费",
    "revenue": "跟踪收入",
    "conversions": "转化",
    "roas": "跟踪 ROAS",
}

DISPLAY_VALUES_ZH = {
    "Comparable": "可比",
    "Not Comparable": "不可比",
    "Not Available": "数据不可用",
    "Improved": "改善",
    "Declined": "恶化",
    "Broadly stable": "基本持平",
    "Scale/context metric; interpret with efficiency and mix.": "规模/背景指标，需结合效率和渠道结构解读。",
    "Sustained improvement": "持续改善",
    "Sustained deterioration": "持续恶化",
    "Sustained increase": "持续增加",
    "Sustained decrease": "持续减少",
    "Stable": "相对稳定",
    "High volatility": "波动较大",
    "Mixed change": "变化不一致",
    "Insufficient history": "历史周期不足",
    "Insufficient comparable history": "可比历史不足",
    "High": "高",
    "Medium": "中",
    "Low": "低",
    "Expand": "扩大",
    "Slightly Increase": "小幅增加",
    "Maintain": "保持",
    "Optimize and Continue": "优化后继续",
    "Slightly Reduce": "小幅削减",
    "Significantly Reduce": "大幅削减",
    "Pause": "暂停",
    "Continue Testing": "继续测试",
    "Insufficient Data": "数据不足，暂不判断",
    "Overall": "整体",
    "All": "全部",
    "Channel": "渠道",
    "No comparability issue detected for the available scope fields.": "基于现有范围字段，未发现可比性问题。",
    "Unique users, overlap, and post-click attribution may be missing.": "唯一用户数、跨渠道重叠和点击后归因可能缺失。",
    "Attribution and channel-role differences may limit direct comparison.": "归因口径和渠道角色差异可能限制直接比较。",
    "Content quality, creator fit, affiliate sales, and long-tail views may be incomplete.": "内容质量、达人匹配、联盟销售和长尾播放可能不完整。",
    "Direct ROAS is not a complete brand-media measure; brand search and assisted conversion may be missing.": "直接 ROAS 不能完整衡量品牌媒体；品牌搜索和助攻转化可能缺失。",
    "Unmapped fields": "未映射字段",
    "Exact duplicate rows": "完全重复记录",
    "Summary rows mixed with detail": "汇总行混入明细",
    "Unknown product alias": "未知产品别名",
    "Ambiguous product alias": "歧义产品别名",
    "Product knowledge index missing": "Product Knowledge 索引缺失",
    "Product knowledge index unreadable": "Product Knowledge 索引不可读",
    "Product knowledge validation failed": "Product Knowledge 校验失败",
    "Report campaign identity conflict": "报告活动身份冲突",
    "Report campaign identity unverified": "报告活动身份未验证",
    "Potential metrics may be omitted from standardized analysis.": "潜在指标可能未纳入标准化分析。",
    "Rows were identical across normalized analytical fields.": "记录在规范化分析字段上完全一致。",
    "Prevents duplicated totals.": "已避免重复计入汇总。",
    "Rows labeled Total/Subtotal/合計/总计 were found.": "发现标记为 Total/Subtotal/合計/总计 的汇总记录。",
    "Prevents double counting.": "已避免重复计算。",
    "Marketing Director + Channel Owner": "市场负责人 + 渠道负责人",
    "Channel Owner + Performance Marketing": "渠道负责人 + 效果营销负责人",
    "Channel Owner + Marketing Analytics": "渠道负责人 + 营销分析",
    "Marketing Analytics + Channel Owners": "营销分析 + 渠道负责人",
    "Marketing Analytics + Source Owners": "营销分析 + 数据源负责人",
    "Marketing Analytics": "营销分析",
    "Budget lock date": "预算锁定日前",
    "Next campaign T-14": "下次活动 T-14",
    "Next campaign T-21": "下次活动 T-21",
    "Critical data-quality issues reduced to 0": "Critical 数据质量问题降至 0",
}

CHART_TITLES_ZH = {
    "Spend and Revenue by Period": "各周期花费与跟踪收入",
    "Channel Spend Share": "当前周期渠道花费占比",
    "Channel Spend Share and Revenue Contribution": "渠道花费占比与跟踪收入贡献",
    "Tracked ROAS by Channel": "各渠道跟踪 ROAS",
    "Daily Spend and Revenue": "每日花费与跟踪收入",
}


def format_value(metric: str, value: Any) -> str:
    if pd.isna(value):
        return "Not Available"
    number = float(value)
    if metric in {
        "ctr",
        "cvr",
        "budget_utilization",
        "delivery_rate",
        "open_rate",
        "crm_click_rate",
        "spend_share",
        "revenue_contribution",
        "conversion_contribution",
        "YoY",
    }:
        return f"{number:.1%}"
    if metric in {"roas"}:
        return f"{number:.2f}x"
    if metric in {"spend", "budget", "revenue", "cpc", "cpm", "cpa", "cost_per_view"}:
        return f"{number:,.2f}"
    return f"{number:,.0f}"


def bullet_list(items: list[str]) -> str:
    return "\n".join(f"- {item}" for item in items) if items else "- [Data Gap] Not Available"


def simple_markdown_html(markdown_text: str) -> str:
    lines = [line.strip() for line in markdown_text.splitlines() if line.strip()]
    output: list[str] = []
    list_items: list[str] = []
    for line in lines:
        if line.startswith("- "):
            list_items.append(f"<li>{html.escape(line[2:])}</li>")
            continue
        if list_items:
            output.append("<ul>" + "".join(list_items) + "</ul>")
            list_items = []
        output.append(f"<p>{html.escape(line)}</p>")
    if list_items:
        output.append("<ul>" + "".join(list_items) + "</ul>")
    return "".join(output)


def display_frame(frame: pd.DataFrame, language: str) -> pd.DataFrame:
    """Localize report-only tables while preserving stable English CSV schemas."""
    if language != "zh-CN":
        return frame.copy()
    localized = frame.copy()

    def localize_value(value: Any) -> Any:
        if pd.isna(value):
            return value
        if isinstance(value, str):
            value = display_text(value)
            replacements = (
                ("Spend=", "花费="),
                ("Conversions=", "转化="),
                ("Revenue share=", "跟踪收入占比="),
                ("Spend share=", "花费占比="),
                ("Delivered=", "送达="),
                ("Click rate=", "点击率="),
                ("Views=", "观看量="),
                ("Cost/View=", "单次观看成本="),
                ("revenue contribution gap=", "跟踪收入贡献差="),
                ("ROAS change=", "ROAS 变化="),
            )
            for source, target in replacements:
                value = value.replace(source, target)
        return value

    for column in localized.columns:
        if localized[column].dtype == object:
            localized[column] = localized[column].map(localize_value)
    return localized.rename(columns=DISPLAY_COLUMNS_ZH)


def display_text(value: Any) -> str:
    text = str(value)
    if text in DISPLAY_VALUES_ZH:
        return str(DISPLAY_VALUES_ZH[text])
    for source in (
        "Unique users, overlap, and post-click attribution may be missing.",
        "Attribution and channel-role differences may limit direct comparison.",
        "Content quality, creator fit, affiliate sales, and long-tail views may be incomplete.",
        "Direct ROAS is not a complete brand-media measure; brand search and assisted conversion may be missing.",
    ):
        text = text.replace(source, str(DISPLAY_VALUES_ZH[source]))
    if "Comparison blocked: " in text:
        prefix, reason = text.split("Comparison blocked: ", 1)
        text = f"{prefix}对比受限：{display_comparability_reason(reason)}"
    if " usable period(s); comparability blocked by " in text:
        count, reason = text.split(" usable period(s); comparability blocked by ", 1)
        text = f"{count} 个可用周期；可比性受限：{display_comparability_reason(reason)}"
    elif text.endswith(" usable period(s)"):
        text = text.replace(" usable period(s)", " 个可用周期")
    if text.startswith(
        (
            "Currency",
            "Tax basis",
            "Attribution window",
            "Conversion definition",
            "Agency-fee basis",
            "Channel coverage",
            "Product mix",
            "Campaign duration",
            "Date coverage",
        )
    ):
        text = display_comparability_reason(text)
    replacements = (
        ("Unrecognized product values:", "未识别的产品值："),
        (
            "Preserved product_raw; left product_id blank; product-level analysis blocked.",
            "已保留 product_raw、将 product_id 留空，并阻断产品级分析。",
        ),
        (
            "Add an exact, sourced alias to Product Knowledge and rebuild its index.",
            "在 Product Knowledge 中补充有来源的精确别名并重建索引。",
        ),
        ("critical issue(s) in the quality report", "个 Critical 数据质量问题"),
        ("needs-confirmation issue(s) in the quality report", "个待确认数据质量问题"),
    )
    for source, target in replacements:
        text = text.replace(source, target)
    return text


def display_comparability_reason(reason: str) -> str:
    replacements = (
        ("Currency", "币种"),
        ("Tax basis", "税口径"),
        ("Attribution window", "归因窗口"),
        ("Conversion definition", "转化定义"),
        ("Agency-fee basis", "代理费口径"),
        ("Channel coverage", "渠道覆盖"),
        ("Product mix", "产品组合"),
        ("Campaign duration/date granularity", "活动周期/日期粒度"),
        ("Campaign duration", "活动周期"),
        ("Date coverage", "日期覆盖"),
        ("Report campaign identity conflicts with source", "报告活动身份与源数据冲突"),
        (" differs", "不一致"),
        (" is missing on one side", "仅一侧有值"),
        ("current=", "当前="),
        ("previous=", "对比="),
        ("current_dates=", "当前日期数="),
        ("previous_dates=", "对比日期数="),
        ("current_days=", "当前天数="),
        ("previous_days=", "对比天数="),
    )
    localized = reason
    for source, target in replacements:
        localized = localized.replace(source, target)
    return localized


def current_row(overall: pd.DataFrame, period: str) -> pd.Series:
    match = overall.loc[overall["period"].astype(str).eq(str(period))]
    if match.empty:
        raise ValueError(f"No overall metrics for current period {period}")
    return match.iloc[0]


def build_findings(
    campaign_name: str,
    overall: pd.DataFrame,
    channels: pd.DataFrame,
    yoy: pd.DataFrame,
    evaluation: pd.DataFrame,
    issues: pd.DataFrame,
    summary: dict[str, Any],
    snapshot_manifest: dict[str, Any] | None = None,
) -> dict[str, Any]:
    current_period = str(summary["current_period"])
    comparison_period = summary.get("comparison_period")
    current = current_row(overall, current_period)
    comparable_yoy = yoy.loc[yoy["Status"].astype(str).eq("Comparable")].copy()

    identity_status = summary.get("campaign_identity_status", "not_requested")
    fact_subject = (
        f"{campaign_name}（{current_period}）"
        if identity_status == "verified"
        else f"当前源数据（{current_period}）"
    )
    executive_lines = [
        (
            f"[Fact] {fact_subject}记录 Spend {format_value('spend', current.get('spend'))}、"
            f"Revenue {format_value('revenue', current.get('revenue'))}、Conversions "
            f"{format_value('conversions', current.get('conversions'))}、ROAS {format_value('roas', current.get('roas'))}。"
        )
    ]
    if identity_status == "conflict":
        executive_lines.append(
            f"[Risk] 指定报告名称“{campaign_name}”与源数据活动名"
            f"{summary.get('source_campaign_names', [])}不一致；本报告不得直接视为该活动的绩效事实。"
        )
    elif identity_status == "unverified":
        executive_lines.append(
            f"[Data Gap] 源数据未提供可验证的活动名；“{campaign_name}”仅作为报告标签。"
        )
    roas_yoy = comparable_yoy.loc[comparable_yoy["Metric"].eq("roas")]
    if not roas_yoy.empty:
        change = roas_yoy.iloc[0]["YoY"]
        direction = "改善" if change > 0.05 else "恶化" if change < -0.05 else "基本持平"
        executive_lines.append(
            f"[Insight] 与 {comparison_period} 相比，跟踪 ROAS {direction}（{change:+.1%}）；该结论仅代表可归因数据。"
        )
    else:
        executive_lines.append("[Data Gap] 当前数据无法形成可比的 ROAS 同比结论。")

    current_channels = channels.loc[channels["period"].astype(str).eq(current_period)].copy()
    top_revenue = current_channels.dropna(subset=["revenue_contribution"]).sort_values(
        "revenue_contribution", ascending=False
    )
    if not top_revenue.empty:
        top = top_revenue.iloc[0]
        executive_lines.append(
            f"[Insight] {top['channel']} 是跟踪 Revenue 的最大贡献渠道，占比 "
            f"{format_value('revenue_contribution', top['revenue_contribution'])}；需结合渠道角色和归因边界判断真实增量。"
        )
    critical_count = int((issues["Severity"].astype(str) == "Critical").sum()) if not issues.empty else 0
    if critical_count:
        executive_lines.append(
            f"[Risk] 数据质量报告包含 {critical_count} 个 Critical 问题，预算和跨期结论应先解决对应口径。"
        )

    highlights: list[str] = []
    for _, row in comparable_yoy.iterrows():
        metric = str(row["Metric"])
        change = row["YoY"]
        improved = (metric in {"cpc", "cpm", "cpa"} and change < -0.05) or (
            metric not in {"cpc", "cpm", "cpa", "spend", "budget"} and change > 0.05
        )
        if improved:
            highlights.append(
                f"[Fact] {metric.upper()} 较 {row['Previous Period']} 改善 {abs(change):.1%}；"
                f"[Insight] {display_text(row['Business Interpretation'])}。"
            )
    positive_gaps = current_channels.dropna(subset=["revenue_contribution_gap"]).sort_values(
        "revenue_contribution_gap", ascending=False
    )
    for _, row in positive_gaps.head(2).iterrows():
        if row["revenue_contribution_gap"] > 0:
            highlights.append(
                f"[Insight] {row['channel']} 的 Revenue 贡献占比高于 Spend 占比 "
                f"{row['revenue_contribution_gap']:.1%}，具备进一步验证边际效率的价值。"
            )
    highlights = highlights[:5] or ["[Data Gap] 暂无足够可比证据确认可复制的亮点。"]

    problems: list[str] = []
    for _, row in comparable_yoy.iterrows():
        metric = str(row["Metric"])
        change = row["YoY"]
        worsened = (metric in {"cpc", "cpm", "cpa"} and change > 0.05) or (
            metric not in {"cpc", "cpm", "cpa", "spend", "budget"} and change < -0.05
        )
        if worsened:
            problems.append(
                f"[Fact] {metric.upper()} 较 {row['Previous Period']} 恶化 {abs(change):.1%}。"
                "[Hypothesis] 可能来自流量成本、素材、受众、渠道结构或转化链路变化；需按渠道和日期验证。"
            )
    if not issues.empty:
        for _, row in issues.sort_values(
            "Severity", key=lambda series: series.map({"Critical": 0, "Warning": 1, "Info": 2}).fillna(3)
        ).head(3).iterrows():
            diagnosis = {
                "Unmapped fields": (
                    "可能来自字段命名未进入映射表；替代解释是该字段仅为备注、并非分析指标。",
                    "确认字段定义后，将其加入 mapping JSON 或明确列为审计备注。",
                ),
                "Exact duplicate rows": (
                    "可能来自重复导出或合并；替代解释是两条业务记录碰巧在现有维度和指标上完全相同。",
                    "回查来源记录 ID、时间戳和导出批次，确认是否为真实重复。",
                ),
                "Summary rows mixed with detail": (
                    "可能来自平台导出同时包含汇总与明细；替代解释是 Total/合计 只是合法的产品或活动名称。",
                    "回查来源表的行级含义，确认汇总标签后再保留排除规则。",
                ),
            }.get(
                str(row["Issue Type"]),
                (
                    "可能来自源表口径或维护流程；也可能是当前分析字段不足以解释的正常业务记录。",
                    "回查来源位置和字段定义后，再决定是否修复或纳入计算。",
                ),
            )
            problems.append(
                f"[Risk] {display_text(row['Issue Type'])}：{display_text(row['Detail'])} "
                f"影响：{display_text(row['Decision Impact'])} "
                f"[Hypothesis] {diagnosis[0]} "
                f"[Recommendation] {diagnosis[1]} 来源：{row['Source File']} / {row['Source Table']}。"
            )
    problems = problems[:5] or [
        "[Insight] 未发现达到报告阈值的明确恶化项。"
        "[Hypothesis] 仍可能存在目标值未提供或归因链路不可见的问题；替代解释是活动确实保持稳定。"
        "[Recommendation] 补充目标值和渠道增量验证后再确认是否达成预期。"
    ]

    core_findings = executive_lines + highlights[:2] + problems[:2]
    limitations: list[str] = []
    limitations.extend(
        f"[Risk] {display_comparability_reason(reason)}"
        for reason in summary.get("comparability_reasons", [])
    )
    if not summary.get("product_analysis_allowed", True):
        limitations.append(
            "[Data Gap] 产品级分析及产品汇总已省略：Product Knowledge 未能对所有产品完成安全的精确解析；"
            "请查看 data_quality_report.md 和 _intermediate/run_manifest.json。"
        )
    if not issues.empty:
        material = issues.loc[
            issues["Repair Class"].astype(str).isin(["Material impact", "Needs confirmation"])
        ]
        limitations.extend(
            f"[Data Gap] {display_text(row['Issue Type'])}: {display_text(row['Decision Impact'])}"
            for _, row in material.head(8).iterrows()
        )
    for _, row in evaluation.iterrows():
        risk = str(row.get("Risk", "")).strip()
        if risk and risk.lower() != "nan":
            limitations.append(f"[Data Gap] {row['Channel']}: {display_text(risk)}")
    limitations.append(
        "[Risk] 报告中的 Revenue 和 Conversions 为输入数据中的跟踪结果，不等同于营销渠道的增量因果贡献。"
    )
    snapshot_lines: list[str] = []
    if snapshot_manifest:
        source_entries = snapshot_manifest.get("sources", [])
        status_counts: dict[str, int] = {}
        for entry in source_entries:
            status = str(entry.get("status") or "Unverified")
            status_counts[status] = status_counts.get(status, 0) + 1
            if entry.get("required", True) and status in {
                "Partial",
                "Failed",
                "Permission Required",
                "Unverified",
            }:
                limitations.append(
                    f"[Data Gap] 必需数据源 {entry.get('source_id')} 状态为 {status}："
                    f"{entry.get('error') or '; '.join(entry.get('warning') or []) or '完整性未确认'}。"
                )
        snapshot_lines = [
            f"[Fact] 分析仅使用快照批次 `{snapshot_manifest.get('snapshot_batch', 'Unknown')}` 的 normalized 文件。",
            f"[Fact] 数据截点：`{snapshot_manifest.get('analysis_cutoff', 'Unknown')}`；"
            f"登记数据源 {snapshot_manifest.get('source_count', len(source_entries))} 个，"
            f"清单对象 {len(source_entries)} 个。",
            f"[Risk] 快照状态：{snapshot_manifest.get('status', 'Unverified')}；"
            f"对象状态分布：{json.dumps(status_counts, ensure_ascii=False, sort_keys=True)}。",
        ]
    else:
        snapshot_lines = [
            "[Fact] 本次为本地文件模式；分析输入来自执行时指定的 input-dir，未动态读取飞书页面。"
        ]
    limitations = list(dict.fromkeys(limitations))

    priorities = []
    for _, row in evaluation.iterrows():
        if row["Decision"] in {
            "Expand",
            "Slightly Increase",
            "Slightly Reduce",
            "Pause",
            "Continue Testing",
            "Insufficient Data",
        }:
            priorities.append(
                f"[Recommendation] {row['Channel']}：{display_text(row['Decision'])}"
                f"（置信度：{display_text(row['Confidence'])}）。"
            )
    if not priorities:
        priorities.append("[Recommendation] 在补齐渠道角色指标后，再进行预算结构调整。")

    return {
        "executive_lines": executive_lines,
        "highlights": highlights,
        "problems": problems,
        "core_findings": core_findings,
        "limitations": limitations,
        "priorities": priorities,
        "snapshot_lines": snapshot_lines,
    }


def kpi_frame(current: pd.Series) -> pd.DataFrame:
    metrics = ["budget", "spend", "impressions", "clicks", "conversions", "revenue", "ctr", "cpc", "cpm", "cvr", "cpa", "roas"]
    return pd.DataFrame(
        [{"Metric": metric.upper(), "Value": format_value(metric, current.get(metric))} for metric in metrics]
    )


def prepare_output_directory(path: Path) -> None:
    if path.exists() and any(path.iterdir()):
        raise FileExistsError(f"Output directory is not empty; refusing to overwrite: {path}")
    path.mkdir(parents=True, exist_ok=True)


def apply_snapshot_confidence(
    output_dir: Path,
    snapshot_manifest: dict[str, Any] | None,
) -> list[str]:
    """Lower decision confidence when required snapshot sources are incomplete."""
    if not snapshot_manifest:
        return []
    material_statuses = {"Partial", "Failed", "Permission Required", "Unverified"}
    affected = [
        str(entry.get("source_id"))
        for entry in snapshot_manifest.get("sources", [])
        if entry.get("required", True) and entry.get("status") in material_statuses
    ]
    if not affected:
        return []
    note = f"Required source snapshot incomplete: {', '.join(affected)}"
    evaluation_path = output_dir / "channel_evaluation.csv"
    if evaluation_path.is_file():
        evaluation = pd.read_csv(evaluation_path)
        evaluation["Confidence"] = "Low"
        evaluation["Decision"] = "Insufficient Data"
        evaluation["Risk"] = evaluation["Risk"].fillna("").map(
            lambda value: f"{value} {note}".strip()
        )
        evaluation.to_csv(evaluation_path, index=False, encoding="utf-8-sig")
    trend_path = output_dir / "trend_analysis.csv"
    if trend_path.is_file():
        trend = pd.read_csv(trend_path)
        trend["Confidence"] = "Low"
        trend["Evidence"] = trend["Evidence"].fillna("").map(
            lambda value: f"{value}; {note}".strip("; ")
        )
        trend.to_csv(trend_path, index=False, encoding="utf-8-sig")
    budget_path = output_dir / "_intermediate" / "budget_recommendations.csv"
    if budget_path.is_file():
        budget = pd.read_csv(budget_path)
        budget["Recommended Budget Index"] = math.nan
        budget["Direction"] = "Insufficient Data"
        budget["Confidence"] = "Low"
        budget["Risk"] = budget["Risk"].fillna("").map(
            lambda value: f"{value} {note}".strip()
        )
        budget.to_csv(budget_path, index=False, encoding="utf-8-sig")
    action_path = output_dir / "action_plan.csv"
    if action_path.is_file():
        actions = pd.read_csv(action_path)
        governance_mask = (
            actions["Owner Suggestion"].astype(str).str.contains("Marketing Analytics", na=False)
            & ~actions["Owner Suggestion"].astype(str).str.contains("Channel Owner", na=False)
        )
        governance_actions = actions.loc[governance_mask].copy()
        gate = pd.DataFrame(
            [
                {
                    "Action": f"补齐并重新抓取必需数据源（{', '.join(affected)}），通过快照完整性校验后再批准渠道预算调整",
                    "Problem Solved": note,
                    "Data Evidence": "source_integrity_report.md and manifest.json",
                    "Owner Suggestion": "Marketing Analytics + Source Owners",
                    "Deadline": "Before budget approval",
                    "Priority": "P0",
                    "Success Metric": "All required sources are Complete or Complete with Warnings and every normalized checksum passes",
                }
            ]
        )
        actions = pd.concat([gate, governance_actions], ignore_index=True)
        actions["Confidence"] = "Low"
        actions.to_csv(action_path, index=False, encoding="utf-8-sig")
    return affected


def render_reports(
    campaign_name: str,
    language: str,
    output_dir: Path,
    chart_manifest: list[dict[str, Any]],
    snapshot_manifest: dict[str, Any] | None = None,
) -> None:
    intermediate = output_dir / "_intermediate"
    overall = pd.read_csv(intermediate / "overall_metrics.csv")
    channels = pd.read_csv(intermediate / "channel_metrics.csv")
    yoy = pd.read_csv(intermediate / "yoy_metrics.csv")
    issues = pd.read_csv(intermediate / "quality_issues.csv") if (intermediate / "quality_issues.csv").exists() else pd.DataFrame()
    evaluation = pd.read_csv(output_dir / "channel_evaluation.csv")
    actions = pd.read_csv(output_dir / "action_plan.csv")
    trend = pd.read_csv(output_dir / "trend_analysis.csv")
    budget = pd.read_csv(intermediate / "budget_recommendations.csv")
    summary = json.loads((intermediate / "metrics_summary.json").read_text(encoding="utf-8"))
    current_period = str(summary["current_period"])
    current = current_row(overall, current_period)
    findings = build_findings(
        campaign_name,
        overall,
        channels,
        yoy,
        evaluation,
        issues,
        summary,
        snapshot_manifest,
    )
    chart_files = {str(chart.get("file")) for chart in chart_manifest}
    expected_charts = {
        "spend_revenue_by_period.png": "跨周期花费与跟踪收入图",
        "channel_spend_share.png": "渠道花费占比图",
        "channel_spend_vs_revenue_contribution.png": "渠道花费与跟踪收入贡献对比图",
        "tracked_roas_by_channel.png": "渠道跟踪 ROAS 图",
        "daily_spend_revenue.png": "当前周期每日花费与跟踪收入图",
    }
    for file_name, label in expected_charts.items():
        if file_name not in chart_files:
            findings["limitations"].append(
                f"[Data Gap] {label}未生成：缺少所需数据、有效日期不足或存在不可比口径。"
            )
    kpis = kpi_frame(current)

    environment = Environment(
        loader=FileSystemLoader(TEMPLATE_DIR),
        undefined=StrictUndefined,
        autoescape=select_autoescape(["html"]),
        trim_blocks=True,
        lstrip_blocks=True,
    )

    executive_template = environment.get_template("executive_summary_template.md")
    executive_markdown = executive_template.render(
        campaign_name=campaign_name,
        executive_summary="\n\n".join(findings["executive_lines"]),
        kpi_table=dataframe_to_markdown(display_frame(kpis, language)),
        highlights=bullet_list(findings["highlights"]),
        problems=bullet_list(findings["problems"]),
        priorities=bullet_list(findings["priorities"]),
        data_limitations=bullet_list(findings["limitations"]),
        data_snapshot=bullet_list(findings["snapshot_lines"]),
    )
    (output_dir / "executive_summary.md").write_text(executive_markdown, encoding="utf-8")

    full_template = environment.get_template("full_report_template.md")
    current_channels = channels.loc[channels["period"].astype(str).eq(current_period)]
    overall_table = kpis
    full_markdown = full_template.render(
        campaign_name=campaign_name,
        executive_summary="\n\n".join(findings["executive_lines"]),
        core_findings=bullet_list(findings["core_findings"]),
        overall_performance=dataframe_to_markdown(display_frame(overall_table, language)),
        channel_evaluation=dataframe_to_markdown(display_frame(evaluation, language)),
        yoy_analysis=dataframe_to_markdown(display_frame(yoy, language)),
        trend_analysis=dataframe_to_markdown(display_frame(trend, language)),
        highlights=bullet_list(findings["highlights"]),
        problems=bullet_list(findings["problems"]),
        priorities=bullet_list(findings["priorities"]),
        budget_recommendations=dataframe_to_markdown(display_frame(budget, language)),
        action_plan=dataframe_to_markdown(display_frame(actions, language)),
        data_limitations=bullet_list(findings["limitations"]),
        data_snapshot=bullet_list(findings["snapshot_lines"]),
    )
    (output_dir / "full_analysis.md").write_text(full_markdown, encoding="utf-8")

    kpi_cards = "".join(
        f'<div class="card"><div class="label">{html.escape(str(row["Metric"]))}</div>'
        f'<div class="value">{html.escape(str(row["Value"]))}</div></div>'
        for _, row in kpis.iterrows()
    )
    charts_html = "".join(
        f'<figure><img src="charts/{html.escape(chart["file"])}" '
        f'alt="{html.escape(CHART_TITLES_ZH.get(chart["title"], chart["title"]) if language == "zh-CN" else chart["title"])}">'
        f'<figcaption>{html.escape(CHART_TITLES_ZH.get(chart["title"], chart["title"]) if language == "zh-CN" else chart["title"])}'
        f' · {html.escape(chart["period"])}</figcaption></figure>'
        for chart in chart_manifest
    ) or "<p>Not Available — required chart data was not present.</p>"
    html_template = environment.get_template("report_template.html")
    report_html = html_template.render(
        language=language,
        campaign_name=campaign_name,
        generated_at=datetime.now().strftime("%Y-%m-%d %H:%M"),
        executive_summary_html=simple_markdown_html(bullet_list(findings["executive_lines"])),
        kpi_cards_html=kpi_cards,
        overall_html=display_frame(
            current_channels[["channel", "spend", "revenue", "conversions", "roas"]], language
        ).to_html(
            index=False, border=0, na_rep="Not Available"
        ),
        channel_table_html=display_frame(evaluation, language).to_html(index=False, border=0, na_rep="数据不可用"),
        yoy_table_html=display_frame(yoy, language).to_html(index=False, border=0, na_rep="数据不可用"),
        trend_table_html=display_frame(trend, language).to_html(index=False, border=0, na_rep="数据不可用"),
        charts_html=charts_html,
        highlights_html=simple_markdown_html(bullet_list(findings["highlights"])),
        problems_html=simple_markdown_html(bullet_list(findings["problems"])),
        budget_html=display_frame(budget, language).to_html(index=False, border=0, na_rep="数据不可用"),
        action_table_html=display_frame(actions, language).to_html(index=False, border=0, na_rep="数据不可用"),
        limitations_html=simple_markdown_html(bullet_list(findings["limitations"])),
        data_snapshot_html=simple_markdown_html(bullet_list(findings["snapshot_lines"])),
    )
    (output_dir / "report.html").write_text(report_html, encoding="utf-8")


def build_report(
    input_dir: Path,
    campaign_name: str,
    output_dir: Path | None = None,
    language: str = "zh-CN",
    mapping_file: Path | None = None,
    currency: str | None = None,
    current_period: str | None = None,
    comparison_period: str | None = None,
    product_knowledge_dir: Path | None = None,
    snapshot_manifest: Path | None = None,
) -> Path:
    snapshot_payload = (
        json.loads(snapshot_manifest.resolve().read_text(encoding="utf-8"))
        if snapshot_manifest
        else None
    )
    destination = output_dir or default_output_dir(campaign_name)
    destination = destination.resolve()
    prepare_output_directory(destination)
    clean_outputs = clean_marketing_data(
        input_dir.resolve(), destination, mapping_file, currency,
        product_knowledge_dir, campaign_name, language,
    )
    campaign_identity = clean_outputs["campaign_identity"]
    product_knowledge = clean_outputs["product_knowledge"]
    calculate_metrics(
        clean_outputs["normalized_csv"],
        destination,
        current_period,
        comparison_period,
        product_analysis_allowed=product_knowledge.get("product_analysis_allowed", False),
    )
    analyze_trends(destination, current_period, comparison_period)
    snapshot_required_gaps = apply_snapshot_confidence(destination, snapshot_payload)
    chart_manifest = build_charts(destination)
    render_reports(campaign_name, language, destination, chart_manifest, snapshot_payload)
    final_outputs = [
        "executive_summary.md",
        "full_analysis.md",
        "data_quality_report.md",
        "cleaned_data.xlsx",
        "channel_evaluation.csv",
        "trend_analysis.csv",
        "action_plan.csv",
        "report.html",
    ]
    write_json(
        destination / "_intermediate" / "run_manifest.json",
        {
            "campaign_name": campaign_name,
            "generated_at": datetime.now().isoformat(timespec="seconds"),
            "input_dir": str(input_dir.resolve()),
            "output_dir": str(destination),
            "outputs": final_outputs,
            "chart_count": len(chart_manifest),
            "status": (
                "completed"
                if product_knowledge.get("product_analysis_allowed", False)
                and campaign_identity.get("status") in {"verified", "not_requested"}
                and not snapshot_required_gaps
                else "partial"
            ),
            "campaign_identity": campaign_identity,
            "product_knowledge": product_knowledge,
            "source_snapshot": (
                {
                    "manifest": str(snapshot_manifest.resolve()),
                    "snapshot_batch": snapshot_payload.get("snapshot_batch"),
                    "analysis_cutoff": snapshot_payload.get("analysis_cutoff"),
                    "status": snapshot_payload.get("status"),
                    "required_source_gaps": snapshot_required_gaps,
                }
                if snapshot_manifest and snapshot_payload
                else None
            ),
            "assumptions": [
                "Latest sortable period is current unless overridden.",
                "Nearest earlier sortable period is the comparison period unless overridden.",
                "Tracked revenue is not treated as incremental causal revenue.",
                (
                    "Product-level analysis was omitted because Product Knowledge resolution was not safe."
                    if not product_knowledge.get("product_analysis_allowed", False)
                    else "Product-level analysis used exact Product Knowledge identifiers."
                ),
                (
                    f"Decision confidence was lowered because required snapshot sources were incomplete: {snapshot_required_gaps}."
                    if snapshot_required_gaps
                    else "No required snapshot source had a material completeness failure."
                ),
            ],
        },
    )
    LOGGER.info("Campaign review completed: %s", destination)
    return destination


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-dir", type=Path, default=Path("."))
    parser.add_argument("--campaign-name", required=True)
    parser.add_argument("--output-dir", type=Path)
    parser.add_argument("--language", default="zh-CN")
    parser.add_argument("--mapping-file", type=Path)
    parser.add_argument("--currency")
    parser.add_argument("--current-period")
    parser.add_argument("--comparison-period")
    parser.add_argument("--product-knowledge-dir", type=Path)
    parser.add_argument("--snapshot-manifest", type=Path)
    parser.add_argument("--verbose", action="store_true")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    configure_logging(args.verbose)
    output = build_report(
        input_dir=args.input_dir,
        campaign_name=args.campaign_name,
        output_dir=args.output_dir,
        language=args.language,
        mapping_file=args.mapping_file,
        currency=args.currency,
        current_period=args.current_period,
        comparison_period=args.comparison_period,
        product_knowledge_dir=args.product_knowledge_dir,
        snapshot_manifest=args.snapshot_manifest,
    )
    print(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
