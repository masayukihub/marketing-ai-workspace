#!/usr/bin/env python3
"""Create a channel-separated Miaoda import bundle from normalized VOC history."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo


def read_csv(path: Path) -> list[dict]:
    with path.open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict], fields: list[str] | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = fields or sorted({key for row in rows for key in row}) or ["status"]
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows or [{"status": "Not Available"}])


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def business_sentiment(row: dict) -> str:
    core = row.get("sentiment") or "Neutral"
    try:
        rating = float(row.get("rating") or 0)
    except ValueError:
        rating = 0
    if core == "Mixed":
        return "Mixed"
    if core == "Positive" and rating == 5:
        return "Strong Positive"
    if core == "Negative" and rating and rating <= 2:
        return "Strong Negative"
    return core


def canonical_record_type(value: str) -> str:
    return {
        "video_comment": "comment",
        "social_post": "sns_post",
        "official_content": "official_post",
        "media_content": "media_article",
    }.get(value, value)


def split_terms(*values: str) -> list[str]:
    """Split classifier multi-label cells into stable, atomic taxonomy terms."""
    terms: list[str] = []
    for value in values:
        for part in (value or "").replace("；", ";").split(";"):
            term = part.strip()
            if term and term not in terms:
                terms.append(term)
    return terms


def main() -> None:
    parser = argparse.ArgumentParser(description="Export all-channel VOC data for Miaoda.")
    parser.add_argument("--normalized", required=True)
    parser.add_argument("--coverage", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--product", default="ai_art_canvas")
    parser.add_argument("--batch-id", default="miaoda-multichannel-20260803")
    args = parser.parse_args()

    source_rows = [row for row in read_csv(Path(args.normalized)) if row.get("product_id") == args.product]
    coverage_rows = read_csv(Path(args.coverage))
    output = Path(args.output)
    data_dir = output / "data"
    data_dir.mkdir(parents=True, exist_ok=True)

    review_fields = [
        "review_id", "version_id", "batch_id", "product_id", "variant_id", "bundle_id", "source",
        "record_type", "source_record_type", "relationship_type", "voc_eligibility", "review_date", "rating", "sentiment",
        "business_sentiment", "review_title", "review_body", "review_url", "source_url", "primary_topic",
        "secondary_topics", "issue_category", "issue_subcategory", "purchase_motivation", "usage_scenario",
        "praised_feature", "complained_feature", "expectation_gap", "severity", "return_intent",
        "responsibility_owner", "analysis_confidence", "manual_review_required", "coverage_status",
        "review_status", "mapping_status", "mapping_basis", "raw_file_path", "collected_at", "last_checked_at",
    ]
    reviews = []
    for row in source_rows:
        exported = {field: row.get(field, "") for field in review_fields}
        exported["source_record_type"] = row.get("record_type", "")
        exported["record_type"] = canonical_record_type(row.get("record_type", ""))
        exported["business_sentiment"] = business_sentiment(row)
        reviews.append(exported)
    write_csv(data_dir / "voc_review.csv", reviews, review_fields)

    coverage_fields = [
        "batch_id", "source", "unit_type", "observed_units", "declared_total", "raw_records",
        "analyzable_records", "natural_voc", "context_only", "incomplete", "coverage_rate",
        "coverage_status", "comparison_status", "denominator_note", "failure_reason", "next_step",
    ]
    coverage_export = []
    for row in coverage_rows:
        current = {field: row.get(field, "") for field in coverage_fields}
        current["batch_id"] = args.batch_id
        current["failure_reason"] = row.get("failure_reason") or (row.get("denominator_note") if row.get("coverage_status") in {"Partial", "Blocked"} else "")
        coverage_export.append(current)
    write_csv(data_dir / "voc_source_coverage.csv", coverage_export, coverage_fields)

    analyzable = [
        row for row in reviews
        if row["voc_eligibility"] == "Natural VOC" and row["review_status"] in {"Active", "Updated"}
    ]
    negative = [row for row in analyzable if row["business_sentiment"] in {"Negative", "Strong Negative", "Mixed"}]
    issue_groups: dict[str, list[dict]] = defaultdict(list)
    for row in negative:
        candidates = split_terms(
            row.get("issue_subcategory", ""),
            row.get("issue_category", ""),
            row.get("primary_topic", ""),
        ) or ["Other"]
        for issue in candidates:
            if issue not in {"Purchase Motivation", "Positive Experience", "Other"}:
                issue_groups[issue].append(row)
    max_count = max((len(rows) for rows in issue_groups.values()), default=1)
    issues = []
    for issue, rows in issue_groups.items():
        sources = Counter(row["source"] for row in rows)
        strong = sum(row["business_sentiment"] == "Strong Negative" for row in rows)
        high = sum(row.get("severity") in {"Critical", "High"} for row in rows)
        frequency = len(rows) / max_count * 100
        intensity = (strong * 100 + (len(rows) - strong) * 60) / len(rows)
        breadth = min(100, len(sources) / 3 * 100)
        score = round(frequency * .4 + intensity * .35 + breadth * .25, 1)
        priority = "P0" if any(row.get("severity") == "Critical" for row in rows) else "P1" if score >= 70 or (high >= 2 and len(rows) >= 2) else "P2" if score >= 40 and len(rows) >= 2 else "Monitor"
        confidence = "High" if len(rows) >= 5 and len(sources) >= 2 else "Medium" if len(rows) >= 2 else "Low"
        issue_key = "issue_" + hashlib.sha256(f"{args.product}|{issue}".encode()).hexdigest()[:16]
        issues.append({
            "issue_key": issue_key, "batch_id": args.batch_id, "product_id": args.product,
            "source_scope": json.dumps(sources, ensure_ascii=False), "issue_name": issue,
            "priority": priority, "sample_count": len(rows), "denominator": len(analyzable),
            "negative_rate": round(len(rows) / len(analyzable), 4) if analyzable else "",
            "trend": "Data Insufficient", "confidence": confidence,
            "evidence_review_ids": json.dumps([row["review_id"] for row in rows], ensure_ascii=False),
            "workflow_status": "new", "owner": "", "due_date": "", "review_note": "",
            "priority_score": score,
        })
    priority_rank = {"P0": 0, "P1": 1, "P2": 2, "Monitor": 3}
    issues.sort(key=lambda row: (priority_rank[row["priority"]], -row["sample_count"]))
    write_csv(data_dir / "voc_issue.csv", issues)

    actions = []
    for issue in issues:
        if issue["priority"] == "Monitor":
            continue
        actions.append({
            "action_key": "action_" + issue["issue_key"].split("_")[-1], "batch_id": args.batch_id,
            "product_id": args.product, "issue_key": issue["issue_key"], "priority": issue["priority"],
            "action_text": f"Validate root cause and define acceptance criteria for {issue['issue_name']}",
            "evidence_text": issue["evidence_review_ids"],
            "success_metric": "Root cause documented; recurrence and negative rate tracked by channel",
            "workflow_status": "new", "owner": "", "due_date": "", "validation_result": "",
        })
    write_csv(data_dir / "voc_action.csv", actions)

    positive = [row for row in analyzable if row["business_sentiment"] in {"Positive", "Strong Positive", "Mixed"}]
    value_groups: dict[str, list[dict]] = defaultdict(list)
    for row in positive:
        value = row.get("praised_feature") or row.get("primary_topic") or "Other"
        if value != "Other":
            value_groups[value].append(row)
    insights = []
    for value, rows in sorted(value_groups.items(), key=lambda item: -len(item[1]))[:15]:
        sources = Counter(row["source"] for row in rows)
        insight_key = "insight_" + hashlib.sha256(f"{args.product}|{value}".encode()).hexdigest()[:16]
        insights.append({
            "insight_key": insight_key, "batch_id": args.batch_id, "product_id": args.product,
            "insight_type": "recognized_value", "value_or_concern": value, "sample_count": len(rows),
            "denominator": len(analyzable), "recommended_message": f"Demonstrate {value} with verified user scenes",
            "avoid_message": "Do not generalize across channels or make absolute performance claims",
            "channels": json.dumps(sources, ensure_ascii=False), "confidence": "High" if len(rows) >= 5 and len(sources) >= 2 else "Medium" if len(rows) >= 2 else "Low",
            "evidence_review_ids": json.dumps([row["review_id"] for row in rows], ensure_ascii=False),
            "workflow_status": "new", "owner": "", "experiment_result": "",
        })
    write_csv(data_dir / "voc_marketing_insight.csv", insights)

    source_summary = {}
    for source in sorted({row["source"] for row in reviews}):
        rows = [row for row in reviews if row["source"] == source]
        source_summary[source] = {
            "records": len(rows),
            "natural_voc": sum(row["voc_eligibility"] == "Natural VOC" for row in rows),
            "context_only": sum(row["voc_eligibility"] == "Context Only" for row in rows),
            "analyzable_natural_voc": sum(row["voc_eligibility"] == "Natural VOC" and row["review_status"] in {"Active", "Updated"} for row in rows),
        }
    summary = {
        "batch_id": args.batch_id, "product_id": args.product, "market": "JP",
        "generated_at_jst": datetime.now(ZoneInfo("Asia/Tokyo")).isoformat(timespec="seconds"),
        "total_records": len(reviews), "natural_voc": sum(row["voc_eligibility"] == "Natural VOC" for row in reviews),
        "context_only": sum(row["voc_eligibility"] == "Context Only" for row in reviews),
        "analyzable_natural_voc": len(analyzable), "source_summary": source_summary,
        "business_sentiment": Counter(row["business_sentiment"] for row in analyzable),
        "coverage": {row["source"]: row["coverage_status"] for row in coverage_export},
        "comparison_note": "Channel units and audiences differ. Do not rank unlike channels as if directly comparable.",
    }
    (data_dir / "voc_dashboard_summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    batch = [{
        "batch_id": args.batch_id, "product_id": args.product, "market": "JP", "coverage_status": "Partial",
        "review_count": len(reviews), "manifest_sha256": "", "review_note": "Mixed source coverage; see voc_source_coverage.",
    }]
    write_csv(data_dir / "voc_import_batch.csv", batch)

    files = []
    for path in sorted(data_dir.glob("*")):
        files.append({"path": str(path.relative_to(output)), "bytes": path.stat().st_size, "sha256": digest(path)})
    manifest = {
        "bundle_type": "customer_review_intelligence_miaoda_multichannel", "schema_version": "1.1",
        "batch_id": args.batch_id, "product_id": args.product, "market": "JP", "coverage_status": "Partial",
        "total_records": len(reviews), "natural_voc": summary["natural_voc"], "context_only": summary["context_only"],
        "analyzable_natural_voc": len(analyzable), "contains_personal_display_names": False,
        "files": files,
    }
    (output / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(manifest, ensure_ascii=False))


if __name__ == "__main__":
    main()
