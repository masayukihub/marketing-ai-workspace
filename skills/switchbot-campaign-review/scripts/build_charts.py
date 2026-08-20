#!/usr/bin/env python3
"""Build business-relevant campaign charts when the required data exists."""

from __future__ import annotations

import argparse
import json
import logging
from pathlib import Path
from typing import Any

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from calculate_metrics import metric_blocked_by_reasons, sorted_periods
from common import LOGGER, configure_logging, write_json

COLORS = ["#2F6FED", "#22A6B3", "#F4A261", "#7A5AF8", "#E76F51", "#137A4B", "#667085"]


def setup_matplotlib() -> None:
    logging.getLogger("matplotlib").setLevel(logging.WARNING)
    plt.rcParams.update(
        {
            "font.family": "sans-serif",
            "font.sans-serif": ["Arial Unicode MS", "Noto Sans CJK JP", "Noto Sans CJK SC", "DejaVu Sans"],
            "axes.spines.top": False,
            "axes.spines.right": False,
            "axes.grid": True,
            "axes.axisbelow": True,
            "grid.color": "#E4E7EC",
            "grid.linewidth": 0.7,
            "figure.facecolor": "white",
            "axes.facecolor": "white",
        }
    )


def save_chart(
    figure: plt.Figure,
    path: Path,
    title: str,
    source: str,
    period: str,
    manifest: list[dict[str, Any]],
) -> None:
    figure.text(0.01, 0.01, f"Source: {source} | Period: {period}", fontsize=8, color="#667085")
    figure.tight_layout(rect=(0, 0.04, 1, 1))
    figure.savefig(path, dpi=160, bbox_inches="tight")
    plt.close(figure)
    manifest.append({"file": path.name, "title": title, "source": source, "period": period})


def build_charts(output_dir: Path) -> list[dict[str, Any]]:
    setup_matplotlib()
    intermediate = output_dir / "_intermediate"
    charts_dir = output_dir / "charts"
    charts_dir.mkdir(parents=True, exist_ok=True)
    overall = pd.read_csv(intermediate / "overall_metrics.csv")
    channels = pd.read_csv(intermediate / "channel_metrics.csv")
    normalized = pd.read_csv(intermediate / "normalized_data.csv")
    summary = json.loads((intermediate / "metrics_summary.json").read_text(encoding="utf-8"))
    current = str(summary["current_period"])
    periods = sorted_periods(overall["period"])
    period_label = " → ".join(periods)
    source = "normalized_data.csv"
    comparison_reasons = summary.get("comparability_reasons", [])
    comparison_blocked = any(
        metric_blocked_by_reasons(metric, comparison_reasons)
        for metric in ("spend", "revenue")
    )
    manifest: list[dict[str, Any]] = []

    ordered = overall.copy()
    ordered["period"] = pd.Categorical(ordered["period"].astype(str), categories=periods, ordered=True)
    ordered = ordered.sort_values("period")
    if not comparison_blocked and ordered[["spend", "revenue"]].notna().any().all():
        figure, axis = plt.subplots(figsize=(8, 4.8))
        positions = np.arange(len(ordered))
        width = 0.36
        axis.bar(positions - width / 2, ordered["spend"], width, label="Spend", color=COLORS[0])
        axis.bar(positions + width / 2, ordered["revenue"], width, label="Revenue", color=COLORS[1])
        axis.set_xticks(positions, ordered["period"].astype(str))
        axis.set_ylabel("Amount (source currency)")
        axis.set_title("Spend and Revenue by Period")
        axis.legend(frameon=False)
        save_chart(
            figure,
            charts_dir / "spend_revenue_by_period.png",
            "Spend and Revenue by Period",
            source,
            period_label,
            manifest,
        )

    current_channels = channels.loc[channels["period"].astype(str).eq(current)].copy()
    current_channels = current_channels.sort_values("spend_share", ascending=True)
    if not current_channels.empty and current_channels["spend_share"].notna().any():
        figure, axis = plt.subplots(figsize=(8, max(4.5, len(current_channels) * 0.45)))
        axis.barh(current_channels["channel"], current_channels["spend_share"], color=COLORS[0])
        axis.set_xlabel("Share of Spend")
        axis.set_title("Channel Spend Share")
        axis.xaxis.set_major_formatter(lambda value, _: f"{value:.0%}")
        save_chart(
            figure,
            charts_dir / "channel_spend_share.png",
            "Channel Spend Share",
            source,
            current,
            manifest,
        )

    contribution = current_channels.dropna(
        subset=["spend_share", "revenue_contribution"], how="all"
    ).sort_values("revenue_contribution", ascending=False)
    if not contribution.empty:
        figure, axis = plt.subplots(figsize=(9, max(4.5, len(contribution) * 0.5)))
        positions = np.arange(len(contribution))
        width = 0.36
        axis.barh(positions - width / 2, contribution["spend_share"], width, label="Spend share", color=COLORS[0])
        axis.barh(
            positions + width / 2,
            contribution["revenue_contribution"],
            width,
            label="Revenue contribution",
            color=COLORS[1],
        )
        axis.set_yticks(positions, contribution["channel"])
        axis.set_xlabel("Share")
        axis.set_title("Channel Spend Share and Revenue Contribution")
        axis.xaxis.set_major_formatter(lambda value, _: f"{value:.0%}")
        axis.legend(frameon=False)
        save_chart(
            figure,
            charts_dir / "channel_spend_vs_revenue_contribution.png",
            "Channel Spend Share and Revenue Contribution",
            source,
            current,
            manifest,
        )

    efficiency = current_channels.dropna(subset=["roas"]).sort_values("roas", ascending=True)
    if not efficiency.empty:
        figure, axis = plt.subplots(figsize=(8, max(4.5, len(efficiency) * 0.45)))
        axis.barh(efficiency["channel"], efficiency["roas"], color=COLORS[2])
        axis.axvline(
            1,
            color="#B42318",
            linestyle="--",
            linewidth=1,
            label="Tracked revenue/spend = 1.0 (not a profit threshold)",
        )
        axis.set_xlabel("Revenue / Spend")
        axis.set_title("Tracked ROAS by Channel")
        axis.legend(frameon=False)
        save_chart(
            figure,
            charts_dir / "tracked_roas_by_channel.png",
            "Tracked ROAS by Channel",
            source,
            current,
            manifest,
        )

    if "date" in normalized.columns:
        if "period" in normalized.columns:
            normalized = normalized.loc[
                normalized["period"].astype(str).eq(current)
            ].copy()
        normalized["date"] = pd.to_datetime(normalized["date"], errors="coerce")
        daily = (
            normalized.dropna(subset=["date"])
            .groupby("date")[["spend", "revenue"]]
            .sum(min_count=1)
            .reset_index()
            .sort_values("date")
        )
        if len(daily) >= 3 and daily[["spend", "revenue"]].notna().any().all():
            figure, axis = plt.subplots(figsize=(9, 4.8))
            axis.plot(daily["date"], daily["spend"], marker="o", label="Spend", color=COLORS[0])
            axis.plot(daily["date"], daily["revenue"], marker="o", label="Revenue", color=COLORS[1])
            axis.set_ylabel("Amount (source currency)")
            axis.set_title("Daily Spend and Revenue")
            axis.legend(frameon=False)
            figure.autofmt_xdate()
            save_chart(
                figure,
                charts_dir / "daily_spend_revenue.png",
                "Daily Spend and Revenue",
                source,
                f"{daily['date'].min().date()} to {daily['date'].max().date()}",
                manifest,
            )

    write_json(intermediate / "chart_manifest.json", manifest)
    LOGGER.info("Generated %d chart(s)", len(manifest))
    return manifest


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--verbose", action="store_true")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    configure_logging(args.verbose)
    for chart in build_charts(args.output_dir.resolve()):
        print(f"{chart['title']}: {chart['file']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
