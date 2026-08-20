#!/usr/bin/env python3
"""Run the standardized VOC pipeline and optional business/Miaoda outputs."""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path


def run(command: list[str]) -> None:
    print("+", " ".join(command), flush=True)
    subprocess.run(command, check=True)


def main() -> None:
    parser = argparse.ArgumentParser(description="Standard Customer Review Intelligence workflow.")
    parser.add_argument("--workspace", required=True, help="Product run workspace containing normalized/, outputs/, and state/.")
    parser.add_argument("--config-dir", required=True)
    parser.add_argument("--product-knowledge-dir", required=True)
    parser.add_argument("--mode", choices=("full", "incremental"), default="incremental")
    parser.add_argument("--initial-full", action="store_true")
    parser.add_argument("--modules", default="ec,sns,kol,pr,official,competitor")
    parser.add_argument("--products", default="")
    parser.add_argument("--date-from")
    parser.add_argument("--date-to")
    parser.add_argument("--input")
    parser.add_argument("--input-manifest")
    parser.add_argument("--analyze-only", action="store_true")
    parser.add_argument("--batch-id")
    parser.add_argument("--output-dir", help="Override the report/output directory; database and state remain in the workspace.")
    parser.add_argument("--skip-core", action="store_true", help="Reuse existing normalized data and outputs.")
    parser.add_argument("--build-business", action="store_true")
    parser.add_argument("--build-dashboard-v2", action="store_true")
    parser.add_argument("--export-miaoda", action="store_true")
    parser.add_argument("--export-miaoda-multichannel", action="store_true")
    parser.add_argument("--coverage-csv", help="Channel coverage CSV used by the multichannel Miaoda export.")
    parser.add_argument("--source", default="amazon_jp")
    parser.add_argument("--product", default="ai_art_canvas")
    args = parser.parse_args()

    skill_dir = Path(__file__).resolve().parents[1]
    workspace = Path(args.workspace).resolve()
    output_dir = Path(args.output_dir).resolve() if args.output_dir else workspace / "outputs"
    normalized = workspace / "normalized" / "reviews.csv"

    completed = []
    if not args.skip_core:
        command = [
            sys.executable, str(skill_dir / "scripts" / "run_review_intelligence.py"),
            "--workspace", str(workspace), "--config-dir", str(Path(args.config_dir).resolve()),
            "--product-knowledge-dir", str(Path(args.product_knowledge_dir).resolve()),
            "--mode", args.mode, "--modules", args.modules,
        ]
        for flag, value in (("--products", args.products), ("--date-from", args.date_from), ("--date-to", args.date_to), ("--input", args.input), ("--input-manifest", args.input_manifest), ("--batch-id", args.batch_id)):
            if value:
                command.extend([flag, value])
        if args.initial_full:
            command.append("--initial-full")
        if args.analyze_only:
            command.append("--analyze-only")
        if args.output_dir:
            command.extend(["--output-dir", str(output_dir)])
        run(command)
        completed.append("core")

    if not normalized.is_file():
        raise SystemExit(f"Missing normalized input: {normalized}")
    output_dir.mkdir(parents=True, exist_ok=True)

    if args.build_business:
        run([sys.executable, str(skill_dir / "scripts" / "build_business_applications.py"), "--input", str(normalized), "--output", str(output_dir), "--source", args.source, "--product", args.product, "--batch-id", args.batch_id or ""])
        completed.append("business")

    dashboard_dir = output_dir / "dashboard_v2"
    if args.build_dashboard_v2:
        run([sys.executable, str(skill_dir / "scripts" / "build_dashboard_v2.py"), "--input", str(normalized), "--output", str(dashboard_dir)])
        completed.append("dashboard_v2")

    if args.export_miaoda:
        if not (dashboard_dir / "dashboard_data.json").is_file():
            raise SystemExit("Miaoda export requires outputs/dashboard_v2/dashboard_data.json; add --build-dashboard-v2 or provide an existing dashboard.")
        run([sys.executable, str(skill_dir / "scripts" / "export_miaoda_bundle.py"), "--dashboard-dir", str(dashboard_dir), "--output", str(workspace / "miaoda_bundle")])
        completed.append("miaoda_bundle")

    if args.export_miaoda_multichannel:
        coverage_csv = Path(args.coverage_csv).resolve() if args.coverage_csv else output_dir / "unified_channel_statistics.csv"
        if not coverage_csv.is_file():
            raise SystemExit(f"Missing multichannel coverage input: {coverage_csv}")
        run([
            sys.executable, str(skill_dir / "scripts" / "export_multichannel_miaoda_bundle.py"),
            "--normalized", str(normalized), "--coverage", str(coverage_csv),
            "--output", str(workspace / "miaoda_bundle_multichannel"),
            "--product", args.product, "--batch-id", args.batch_id or "miaoda-multichannel",
        ])
        completed.append("miaoda_bundle_multichannel")

    print(json.dumps({"workspace": str(workspace), "completed": completed}, ensure_ascii=False))


if __name__ == "__main__":
    main()
