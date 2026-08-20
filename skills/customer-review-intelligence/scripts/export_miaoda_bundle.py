#!/usr/bin/env python3
"""Export an audited VOC result set as a Feishu Miaoda-ready data bundle."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import shutil
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo


SCHEMA_VERSION = "1.0"


def coverage_status(meta: dict) -> str:
    value = str(meta.get("coverage_status") or meta.get("status") or "Unverified").strip()
    aliases = {
        "完整": "Complete", "complete": "Complete",
        "零条已确认": "Zero Confirmed", "zero confirmed": "Zero Confirmed",
        "部分完整": "Partial", "partial": "Partial",
        "受阻": "Blocked", "blocked": "Blocked",
        "未配置": "Not Configured", "not configured": "Not Configured",
        "未验证": "Unverified", "unverified": "Unverified",
    }
    return aliases.get(value.lower(), aliases.get(value, value))


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def write_csv(path: Path, rows: list[dict], columns: list[str]) -> None:
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def scalar(value):
    if isinstance(value, (list, dict)):
        return json.dumps(value, ensure_ascii=False)
    if isinstance(value, bool):
        return "true" if value else "false"
    return value


def main() -> None:
    parser = argparse.ArgumentParser(description="Build a Miaoda import bundle from Dashboard V2 data.")
    parser.add_argument("--dashboard-dir", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--assets-dir", default=str(Path(__file__).resolve().parents[1] / "assets" / "miaoda"))
    args = parser.parse_args()

    dashboard_dir = Path(args.dashboard_dir).resolve()
    output = Path(args.output).resolve()
    assets = Path(args.assets_dir).resolve()
    data_path = dashboard_dir / "dashboard_data.json"
    if not data_path.is_file():
        raise SystemExit(f"Missing dashboard data: {data_path}")
    if not assets.is_dir():
        raise SystemExit(f"Missing Miaoda assets: {assets}")

    payload = json.loads(data_path.read_text(encoding="utf-8"))
    required = {"meta", "voices", "issues", "backlog", "marketing", "quality"}
    missing = sorted(required - payload.keys())
    if missing:
        raise SystemExit(f"Dashboard data is missing keys: {', '.join(missing)}")

    output.mkdir(parents=True, exist_ok=True)
    data_dir = output / "data"
    docs_dir = output / "docs"
    migrations_dir = output / "migrations"
    data_dir.mkdir(exist_ok=True)
    docs_dir.mkdir(exist_ok=True)
    migrations_dir.mkdir(exist_ok=True)

    voices = []
    for row in payload["voices"]:
        voices.append({
            "review_id": row.get("review_id"),
            "review_date": row.get("date"),
            "source": row.get("source"),
            "rating": row.get("rating"),
            "sentiment": row.get("sentiment"),
            "title": row.get("title"),
            "review_text": row.get("text"),
            "source_url": row.get("url"),
            "issues_json": scalar(row.get("issues", [])),
            "values_json": scalar(row.get("values", [])),
            "scenarios_json": scalar(row.get("scenarios", [])),
            "responsibility_owner": row.get("owner"),
            "analysis_confidence": row.get("confidence"),
            "manual_review_required": scalar(row.get("manual_review", False)),
        })
    write_csv(data_dir / "review.csv", voices, list(voices[0]) if voices else ["review_id"])

    issue_rows = [{k: scalar(v) for k, v in row.items()} for row in payload["issues"]]
    issue_columns = sorted({k for row in issue_rows for k in row}) or ["name"]
    write_csv(data_dir / "issue.csv", issue_rows, issue_columns)

    backlog_rows = [{k: scalar(v) for k, v in row.items()} for row in payload["backlog"]]
    backlog_columns = sorted({k for row in backlog_rows for k in row}) or ["Issue ID"]
    write_csv(data_dir / "action.csv", backlog_rows, backlog_columns)

    marketing_rows = [{k: scalar(v) for k, v in row.items()} for row in payload["marketing"]]
    marketing_columns = sorted({k for row in marketing_rows for k in row}) or ["类型"]
    write_csv(data_dir / "marketing_insight.csv", marketing_rows, marketing_columns)

    summary = {
        "schema_version": SCHEMA_VERSION,
        "generated_at_jst": datetime.now(ZoneInfo("Asia/Tokyo")).isoformat(timespec="seconds"),
        "meta": payload["meta"],
        "kpis": payload.get("kpis", {}),
        "ratings": payload.get("ratings", {}),
        "sentiments": payload.get("sentiments", {}),
        "executive": payload.get("executive", []),
        "quality": payload["quality"],
    }
    (data_dir / "dashboard_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    for source, destination in (
        (assets / "schema.sql", migrations_dir / "001_create_voc_tables.sql"),
        (assets / "app_blueprint.md", docs_dir / "app_blueprint.md"),
        (assets / "data_dictionary.md", docs_dir / "data_dictionary.md"),
    ):
        shutil.copy2(source, destination)

    copied_dashboard = output / "dashboard"
    copied_dashboard.mkdir(exist_ok=True)
    for name in ("index.html", "dashboard.css", "dashboard.js", "dashboard_data.json"):
        source = dashboard_dir / name
        if source.is_file():
            shutil.copy2(source, copied_dashboard / name)

    files = []
    for path in sorted(p for p in output.rglob("*") if p.is_file() and p.name != "manifest.json"):
        files.append({
            "path": str(path.relative_to(output)),
            "bytes": path.stat().st_size,
            "sha256": sha256(path),
        })
    manifest = {
        "bundle_type": "customer_review_intelligence_miaoda",
        "schema_version": SCHEMA_VERSION,
        "generated_at_jst": summary["generated_at_jst"],
        "product": payload["meta"].get("product"),
        "market": payload["meta"].get("market", "JP"),
        "coverage_status": coverage_status(payload["meta"]),
        "review_count": len(voices),
        "issue_count": len(issue_rows),
        "action_count": len(backlog_rows),
        "marketing_insight_count": len(marketing_rows),
        "contains_personal_display_names": False,
        "files": files,
    }
    (output / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(manifest, ensure_ascii=False))


if __name__ == "__main__":
    main()
