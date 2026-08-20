#!/usr/bin/env python3
"""Recalculate weighted campaign KPIs, contribution shares, and period comparisons."""

from __future__ import annotations

import argparse
import json
import math
import re
from pathlib import Path
from typing import Any, Iterable

import pandas as pd

from common import LOGGER, configure_logging, safe_divide, write_json

ADDITIVE_METRICS = [
    "budget",
    "spend",
    "impressions",
    "reach",
    "clicks",
    "conversions",
    "revenue",
    "views",
    "engagements",
    "sends",
    "delivered",
    "opens",
    "unsubscribes",
]

RATIO_FORMULAS = {
    "ctr": ("clicks", "impressions", 1.0),
    "cpc": ("spend", "clicks", 1.0),
    "cpm": ("spend", "impressions", 1000.0),
    "cvr": ("conversions", "clicks", 1.0),
    "cpa": ("spend", "conversions", 1.0),
    "roas": ("revenue", "spend", 1.0),
    "budget_utilization": ("spend", "budget", 1.0),
    "delivery_rate": ("delivered", "sends", 1.0),
    "open_rate": ("opens", "delivered", 1.0),
    "crm_click_rate": ("clicks", "delivered", 1.0),
    "engagement_rate": ("engagements", "reach", 1.0),
    "cost_per_view": ("spend", "views", 1.0),
}

HIGHER_IS_BETTER = {"impressions", "reach", "clicks", "conversions", "revenue", "views", "ctr", "cvr", "roas"}
LOWER_IS_BETTER = {"cpc", "cpm", "cpa", "cost_per_view"}
MONETARY_METRICS = {"budget", "spend", "revenue"}
MONETARY_COMPARISON_METRICS = {"budget", "spend", "revenue", "cpc", "cpm", "cpa", "roas"}
ATTRIBUTION_COMPARISON_METRICS = {"conversions", "revenue", "cvr", "cpa", "roas"}


def currency_scope(series: pd.Series) -> str:
    text = series.astype("string").str.strip()
    missing = text.isna() | text.str.lower().isin({"", "nan", "<na>"})
    known = sorted(set(text.loc[~missing].str.upper()))
    if not known:
        return "Unknown"
    if len(known) == 1 and not missing.any():
        return known[0]
    return "Mixed"


def _numeric_period_key(value: Any) -> tuple[int, str]:
    text = str(value)
    match = re.search(r"(19|20)\d{2}", text)
    return (int(match.group(0)) if match else -1, text)


def sorted_periods(values: Iterable[Any]) -> list[str]:
    periods = {str(value).strip() for value in values if pd.notna(value) and str(value).strip() not in {"", "nan", "<NA>"}}
    return sorted(periods, key=_numeric_period_key)


def select_periods(
    data: pd.DataFrame,
    current_period: str | None = None,
    comparison_period: str | None = None,
) -> tuple[str, str | None]:
    periods = sorted_periods(data["period"]) if "period" in data.columns else []
    if not periods:
        raise ValueError("No usable period field. Provide dates or a Year/Period column.")
    current = current_period or periods[-1]
    if current not in periods:
        raise ValueError(f"Current period {current!r} not found. Available: {periods}")
    prior_candidates = [period for period in periods if _numeric_period_key(period) < _numeric_period_key(current)]
    comparison = comparison_period or (prior_candidates[-1] if prior_candidates else None)
    if comparison and comparison not in periods:
        raise ValueError(f"Comparison period {comparison!r} not found. Available: {periods}")
    return current, comparison


def aggregate_metrics(data: pd.DataFrame, group_columns: list[str]) -> pd.DataFrame:
    frame = data.copy()
    for metric in ADDITIVE_METRICS:
        if metric not in frame.columns:
            frame[metric] = math.nan
        frame[metric] = pd.to_numeric(frame[metric], errors="coerce")

    if group_columns:
        for column in group_columns:
            frame[column] = frame[column].fillna("Unassigned").astype(str)
        grouped = frame.groupby(group_columns, dropna=False)[ADDITIVE_METRICS].sum(min_count=1).reset_index()
        if "currency" in frame.columns:
            scopes = (
                frame.groupby(group_columns, dropna=False)["currency"]
                .apply(currency_scope)
                .reset_index(name="currency_scope")
            )
            grouped = grouped.merge(scopes, on=group_columns, how="left")
    else:
        grouped = pd.DataFrame([{metric: frame[metric].sum(min_count=1) for metric in ADDITIVE_METRICS}])
        if "currency" in frame.columns:
            grouped["currency_scope"] = currency_scope(frame["currency"])

    if "currency_scope" in grouped.columns:
        mixed_currency = grouped["currency_scope"].eq("Mixed")
        grouped.loc[mixed_currency, list(MONETARY_METRICS)] = math.nan

    for metric, (numerator, denominator, multiplier) in RATIO_FORMULAS.items():
        grouped[metric] = safe_divide(grouped[numerator], grouped[denominator]) * multiplier
    grouped["frequency"] = safe_divide(grouped["impressions"], grouped["reach"])
    return grouped


def add_contributions(channel_metrics: pd.DataFrame) -> pd.DataFrame:
    frame = channel_metrics.copy()
    if frame.empty:
        return frame
    for metric, target in (
        ("spend", "spend_share"),
        ("impressions", "impression_contribution"),
        ("clicks", "click_contribution"),
        ("conversions", "conversion_contribution"),
        ("revenue", "revenue_contribution"),
    ):
        totals = frame.groupby("period")[metric].transform(lambda series: series.sum(min_count=1))
        frame[target] = safe_divide(frame[metric], totals)
    if "currency_scope" in frame.columns:
        invalid_currency_period = frame.groupby("period")["currency_scope"].transform(
            lambda series: (
                series.eq("Mixed").any()
                or len(set(series.dropna().astype(str))) > 1
            )
        )
        frame.loc[
            invalid_currency_period,
            ["spend_share", "revenue_contribution"],
        ] = math.nan
    frame["revenue_contribution_gap"] = frame["revenue_contribution"] - frame["spend_share"]
    frame["conversion_contribution_gap"] = frame["conversion_contribution"] - frame["spend_share"]
    frame["impressions_per_10000_spend"] = safe_divide(frame["impressions"], frame["spend"]) * 10000
    frame["clicks_per_10000_spend"] = safe_divide(frame["clicks"], frame["spend"]) * 10000
    frame["conversions_per_10000_spend"] = safe_divide(frame["conversions"], frame["spend"]) * 10000
    return frame


def period_scope(data: pd.DataFrame, period: str, field: str) -> set[str]:
    if field not in data.columns:
        return set()
    values = data.loc[data["period"].astype(str).eq(period), field].dropna().astype(str).str.strip()
    return {value for value in values if value and value.lower() != "nan"}


def comparability_reasons(data: pd.DataFrame, current: str, comparison: str | None) -> list[str]:
    if not comparison:
        return ["No comparison period"]
    reasons: list[str] = []
    identity_statuses = {
        str(value)
        for value in data.get(
            "campaign_identity_status", pd.Series(dtype="object")
        ).dropna()
    }
    if "conflict" in identity_statuses:
        expected = period_scope(data, current, "report_campaign_name")
        source = period_scope(data, current, "campaign")
        reasons.append(
            f"Report campaign identity conflicts with source: expected={sorted(expected)}, source={sorted(source)}"
        )
    for field, label in (
        ("currency", "Currency"),
        ("tax_basis", "Tax basis"),
        ("attribution_window", "Attribution window"),
        ("conversion_definition", "Conversion definition"),
        ("agency_fee_basis", "Agency-fee basis"),
    ):
        current_values = period_scope(data, current, field)
        comparison_values = period_scope(data, comparison, field)
        if bool(current_values) != bool(comparison_values):
            reasons.append(
                f"{label} is missing on one side: current={sorted(current_values)}, previous={sorted(comparison_values)}"
            )
        elif len(current_values) > 1 or len(comparison_values) > 1 or (
            current_values and comparison_values and current_values != comparison_values
        ):
            reasons.append(f"{label} differs: current={sorted(current_values)}, previous={sorted(comparison_values)}")

    current_channels = period_scope(data, current, "channel")
    comparison_channels = period_scope(data, comparison, "channel")
    if current_channels and comparison_channels and current_channels != comparison_channels:
        reasons.append(
            f"Channel coverage differs: current={sorted(current_channels)}, previous={sorted(comparison_channels)}"
        )

    current_products = period_scope(data, current, "product_id")
    comparison_products = period_scope(data, comparison, "product_id")
    if current_products and comparison_products and current_products != comparison_products:
        reasons.append(
            f"Product mix differs: current={sorted(current_products)}, previous={sorted(comparison_products)}"
        )

    if "date" in data.columns:
        def date_profile(period: str) -> tuple[int, int | None]:
            dates = pd.to_datetime(
                data.loc[data["period"].astype(str).eq(period), "date"],
                errors="coerce",
            ).dropna()
            unique_dates = dates.dt.normalize().drop_duplicates()
            if unique_dates.empty:
                return 0, None
            span = int((unique_dates.max() - unique_dates.min()).days) + 1
            return len(unique_dates), span

        current_date_count, current_span = date_profile(current)
        previous_date_count, previous_span = date_profile(comparison)
        if bool(current_date_count) != bool(previous_date_count):
            reasons.append(
                f"Date coverage is missing on one side: current_dates={current_date_count}, previous_dates={previous_date_count}"
            )
        elif current_date_count and previous_date_count:
            if (current_date_count == 1) != (previous_date_count == 1):
                reasons.append(
                    f"Campaign duration/date granularity differs: current_dates={current_date_count}, previous_dates={previous_date_count}"
                )
            elif current_date_count > 1 and previous_date_count > 1 and current_span != previous_span:
                reasons.append(
                    f"Campaign duration differs: current_days={current_span}, previous_days={previous_span}"
                )
    return reasons


def metric_blocked_by_reasons(metric: str, reasons: Iterable[str]) -> bool:
    for reason in reasons:
        if reason.startswith(
            (
                "Report campaign identity",
                "Campaign duration",
                "Date coverage",
                "Channel coverage",
            )
        ):
            return True
        if reason.startswith(("Currency", "Tax basis", "Agency-fee basis")):
            if metric in MONETARY_COMPARISON_METRICS:
                return True
        if reason.startswith(("Attribution window", "Conversion definition")):
            if metric in ATTRIBUTION_COMPARISON_METRICS:
                return True
    return False


def build_yoy_table(
    overall: pd.DataFrame,
    data: pd.DataFrame,
    current: str,
    comparison: str | None,
) -> pd.DataFrame:
    metrics = ["budget", "spend", "impressions", "clicks", "conversions", "revenue", "ctr", "cpc", "cpm", "cvr", "cpa", "roas"]
    current_row = overall.loc[overall["period"].astype(str).eq(current)]
    previous_row = overall.loc[overall["period"].astype(str).eq(comparison)] if comparison else pd.DataFrame()
    scope_reasons = comparability_reasons(data, current, comparison)
    records: list[dict[str, Any]] = []

    for metric in metrics:
        current_value = current_row.iloc[0][metric] if not current_row.empty else math.nan
        previous_value = previous_row.iloc[0][metric] if not previous_row.empty else math.nan
        absolute = current_value - previous_value if pd.notna(current_value) and pd.notna(previous_value) else math.nan
        yoy = safe_divide(absolute, previous_value)
        status = "Comparable"
        reasons = list(scope_reasons)
        if pd.isna(current_value) or pd.isna(previous_value):
            status = "Not Available"
            reasons.append("Current or previous value is missing")
        elif previous_value == 0:
            status = "Not Comparable"
            reasons.append("Previous denominator is zero")
        elif metric_blocked_by_reasons(metric, scope_reasons):
            status = "Not Comparable"
        interpretation = "Scale/context metric; interpret with efficiency and mix."
        if status == "Comparable" and pd.notna(yoy):
            if metric in HIGHER_IS_BETTER:
                interpretation = "Improved" if yoy > 0.05 else "Declined" if yoy < -0.05 else "Broadly stable"
            elif metric in LOWER_IS_BETTER:
                interpretation = "Improved" if yoy < -0.05 else "Declined" if yoy > 0.05 else "Broadly stable"
        records.append(
            {
                "Metric": metric,
                "Previous Period": comparison or "",
                "Current Period": current,
                "Previous": previous_value,
                "Current": current_value,
                "Absolute Change": absolute,
                "YoY": yoy if status == "Comparable" else math.nan,
                "Status": status,
                "Business Interpretation": interpretation,
                "Comparability Note": (
                    "; ".join(reasons)
                    if reasons
                    else "No comparability issue detected for the available scope fields."
                ),
            }
        )
    return pd.DataFrame.from_records(records)


def calculate_metrics(
    normalized_csv: Path,
    output_dir: Path,
    current_period: str | None = None,
    comparison_period: str | None = None,
    product_analysis_allowed: bool | None = None,
) -> dict[str, Path]:
    data = pd.read_csv(normalized_csv)
    data["period"] = data["period"].astype(str)
    current, comparison = select_periods(data, current_period, comparison_period)

    overall = aggregate_metrics(data, ["period"])
    channels = add_contributions(aggregate_metrics(data, ["period", "channel"]))
    if product_analysis_allowed is None:
        populated_products = (
            "product_raw" in data.columns
            and data["product_raw"].notna().any()
        )
        fully_resolved = (
            "product_id" in data.columns
            and data.loc[data["product_raw"].notna(), "product_id"].notna().all()
        ) if populated_products else True
        product_analysis_allowed = bool(fully_resolved)
    products = (
        aggregate_metrics(data, ["period", "product_id"])
        if product_analysis_allowed
        else pd.DataFrame(columns=["period", "product_id"])
    )
    yoy = build_yoy_table(overall, data, current, comparison)

    intermediate = output_dir / "_intermediate"
    intermediate.mkdir(parents=True, exist_ok=True)
    paths = {
        "overall": intermediate / "overall_metrics.csv",
        "channels": intermediate / "channel_metrics.csv",
        "products": intermediate / "product_metrics.csv",
        "yoy": intermediate / "yoy_metrics.csv",
    }
    overall.to_csv(paths["overall"], index=False, encoding="utf-8-sig")
    channels.to_csv(paths["channels"], index=False, encoding="utf-8-sig")
    products.to_csv(paths["products"], index=False, encoding="utf-8-sig")
    yoy.to_csv(paths["yoy"], index=False, encoding="utf-8-sig")
    summary = {
        "current_period": current,
        "comparison_period": comparison,
        "periods": sorted_periods(data["period"]),
        "comparability_reasons": comparability_reasons(data, current, comparison),
        "product_analysis_allowed": product_analysis_allowed,
        "campaign_identity_status": (
            str(data["campaign_identity_status"].dropna().iloc[0])
            if "campaign_identity_status" in data.columns
            and data["campaign_identity_status"].notna().any()
            else "not_requested"
        ),
        "report_campaign_name": (
            str(data["report_campaign_name"].dropna().iloc[0])
            if "report_campaign_name" in data.columns
            and data["report_campaign_name"].notna().any()
            else None
        ),
        "source_campaign_names": (
            sorted(
                {
                    name
                    for value in data["source_campaign_names"].dropna().astype(str)
                    for name in value.split(" | ")
                    if name
                }
            )
            if "source_campaign_names" in data.columns
            else []
        ),
        "current_overall": overall.loc[overall["period"].astype(str).eq(current)].to_dict(orient="records"),
    }
    write_json(intermediate / "metrics_summary.json", summary)
    LOGGER.info("Calculated metrics for periods: %s", ", ".join(summary["periods"]))
    return paths | {"summary": intermediate / "metrics_summary.json"}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True, help="Normalized CSV from clean_marketing_data.py")
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--current-period")
    parser.add_argument("--comparison-period")
    parser.add_argument("--verbose", action="store_true")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    configure_logging(args.verbose)
    outputs = calculate_metrics(
        args.input.resolve(),
        args.output_dir.resolve(),
        args.current_period,
        args.comparison_period,
    )
    for name, path in outputs.items():
        print(f"{name}: {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
