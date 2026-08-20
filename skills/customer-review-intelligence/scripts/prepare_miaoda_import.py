#!/usr/bin/env python3
"""Transform a multichannel bundle into the exact Miaoda application schema."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path


def read(path: Path) -> list[dict]:
    with path.open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def write(path: Path, rows: list[dict], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def snake(value: str) -> str:
    return value.strip().lower().replace(" ", "_")


def confidence(value: str) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return {"high": .9, "medium": .7, "low": .4}.get(snake(value or ""), .5)


def json_list(value: str) -> str:
    if not value:
        return "[]"
    try:
        parsed = json.loads(value)
    except json.JSONDecodeError:
        parsed = [part.strip() for part in value.replace(";", ",").split(",") if part.strip()]
    if isinstance(parsed, dict):
        parsed = list(parsed)
    if not isinstance(parsed, list):
        parsed = [str(parsed)]
    return json.dumps(parsed, ensure_ascii=False)


def split_terms(*values: str) -> list[str]:
    terms: list[str] = []
    for value in values:
        for part in (value or "").replace("；", ";").split(";"):
            term = part.strip()
            if term and term not in terms:
                terms.append(term)
    return terms


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--bundle", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--batch-id", required=True)
    args = parser.parse_args()
    bundle = Path(args.bundle)
    output = Path(args.output)
    data = bundle / "data"

    review_fields = ["review_id", "batch_id", "product_id", "variant_id", "bundle_id", "source", "record_type", "relationship_type", "voc_eligibility", "review_date", "rating", "sentiment", "title", "review_text", "source_url", "issues_json", "values_json", "scenarios_json", "responsibility_owner", "analysis_confidence", "manual_review_required", "coverage_status", "review_status", "analysis_eligible"]
    reviews = []
    for row in read(data / "voc_review.csv"):
        sentiment = snake(row.get("sentiment") or "neutral")
        if sentiment not in {"positive", "negative", "neutral", "mixed"}:
            sentiment = "neutral"
        is_negative = sentiment in {"negative", "mixed"}
        is_positive = sentiment in {"positive", "mixed"}
        issue_values = split_terms(row.get("issue_subcategory", ""), row.get("issue_category", ""), row.get("primary_topic", ""))
        value_values = split_terms(row.get("praised_feature", ""), row.get("primary_topic", ""))
        scenario_values = [x.strip() for x in (row.get("usage_scenario") or "").replace(";", ",").split(",") if x.strip()]
        reviews.append({
            "review_id": row["review_id"], "batch_id": args.batch_id, "product_id": row.get("product_id") or "ai_art_canvas",
            "variant_id": row.get("variant_id"), "bundle_id": row.get("bundle_id"), "source": row.get("source"),
            "record_type": row.get("record_type"), "relationship_type": row.get("relationship_type"),
            "voc_eligibility": snake(row.get("voc_eligibility") or "unverified"), "review_date": row.get("review_date"),
            "rating": row.get("rating"), "sentiment": sentiment, "title": row.get("review_title"),
            "review_text": row.get("review_body") or "", "source_url": row.get("review_url") or row.get("source_url"),
            "issues_json": json.dumps(list(dict.fromkeys(issue_values)) if is_negative else [], ensure_ascii=False),
            "values_json": json.dumps(list(dict.fromkeys(value_values)) if is_positive else [], ensure_ascii=False),
            "scenarios_json": json.dumps(scenario_values, ensure_ascii=False), "responsibility_owner": row.get("responsibility_owner"),
            "analysis_confidence": confidence(row.get("analysis_confidence")),
            "manual_review_required": "true" if snake(row.get("manual_review_required") or "no") in {"yes", "true", "1"} else "false",
            "coverage_status": snake(row.get("coverage_status") or "unverified"),
            "review_status": snake(row.get("review_status") or "unverified"),
            "analysis_eligible": "true" if row.get("review_status") in {"Active", "Updated"} else "false",
        })
    write(output / "voc_review.csv", reviews, review_fields)

    coverage_fields = ["batch_id", "source", "declared_total", "observed_units", "analyzable_records", "natural_voc", "context_only", "coverage_status", "coverage_rate", "failure_reason", "next_step"]
    coverages = []
    for row in read(data / "voc_source_coverage.csv"):
        rate = (row.get("coverage_rate") or "").replace("%", "")
        try:
            rate_value = float(rate) / (100 if "%" in (row.get("coverage_rate") or "") else 1)
        except ValueError:
            rate_value = 0
        def integer(key: str) -> int:
            try:
                return int(float(row.get(key) or 0))
            except ValueError:
                return 0
        coverages.append({"batch_id": args.batch_id, "source": row["source"], "declared_total": integer("declared_total"), "observed_units": integer("observed_units"), "analyzable_records": integer("analyzable_records"), "natural_voc": integer("natural_voc"), "context_only": integer("context_only"), "coverage_status": snake(row.get("coverage_status") or "unverified"), "coverage_rate": rate_value, "failure_reason": row.get("failure_reason"), "next_step": row.get("next_step")})
    write(output / "voc_source_coverage.csv", coverages, coverage_fields)

    issue_fields = ["issue_key", "batch_id", "product_id", "source_scope", "issue_name", "priority", "sample_count", "denominator", "negative_rate", "trend", "confidence", "evidence_review_ids", "workflow_status", "review_note"]
    issues = []
    for row in read(data / "voc_issue.csv"):
        sources = json.loads(row.get("source_scope") or "{}")
        issues.append({"issue_key": row["issue_key"], "batch_id": args.batch_id, "product_id": row["product_id"], "source_scope": json.dumps(sources, ensure_ascii=False), "issue_name": row["issue_name"], "priority": "P3" if row["priority"] == "Monitor" else row["priority"], "sample_count": row["sample_count"], "denominator": row["denominator"], "negative_rate": row["negative_rate"], "trend": snake(row.get("trend") or "data_insufficient"), "confidence": confidence(row.get("confidence")), "evidence_review_ids": json_list(row.get("evidence_review_ids") or "[]"), "workflow_status": "open", "review_note": ""})
    write(output / "voc_issue.csv", issues, issue_fields)

    action_fields = ["action_key", "product_id", "issue_key", "priority", "action_text", "evidence_text", "success_metric", "workflow_status", "validation_result"]
    actions = []
    for row in read(data / "voc_action.csv"):
        actions.append({"action_key": row["action_key"], "product_id": row["product_id"], "issue_key": row["issue_key"], "priority": row["priority"], "action_text": row["action_text"], "evidence_text": row["evidence_text"], "success_metric": row["success_metric"], "workflow_status": "pending", "validation_result": ""})
    write(output / "voc_action.csv", actions, action_fields)

    insight_fields = ["insight_key", "product_id", "insight_type", "value_or_concern", "sample_count", "denominator", "recommended_message", "avoid_message", "channels", "confidence", "evidence_review_ids", "workflow_status", "experiment_result"]
    insights = []
    for row in read(data / "voc_marketing_insight.csv"):
        insights.append({"insight_key": row["insight_key"], "product_id": row["product_id"], "insight_type": "value_reinforcement" if row.get("insight_type") == "recognized_value" else "concern_handling", "value_or_concern": row["value_or_concern"], "sample_count": row["sample_count"], "denominator": row["denominator"], "recommended_message": row["recommended_message"], "avoid_message": row["avoid_message"], "channels": json_list(row.get("channels") or "[]"), "confidence": confidence(row.get("confidence")), "evidence_review_ids": json_list(row.get("evidence_review_ids") or "[]"), "workflow_status": "draft", "experiment_result": ""})
    write(output / "voc_marketing_insight.csv", insights, insight_fields)

    manifest_hash = hashlib.sha256((bundle / "manifest.json").read_bytes()).hexdigest()
    batch_fields = ["batch_id", "product_id", "market", "coverage_status", "review_count", "manifest_sha256", "review_note"]
    write(output / "voc_import_batch.csv", [{"batch_id": args.batch_id, "product_id": "ai_art_canvas", "market": "japan", "coverage_status": "partial", "review_count": len(reviews), "manifest_sha256": manifest_hash, "review_note": "566 all-channel records; 492 Natural VOC, 74 Context Only, 437 analyzable Natural VOC. See source coverage."}], batch_fields)
    print(json.dumps({"reviews": len(reviews), "coverage": len(coverages), "issues": len(issues), "actions": len(actions), "marketing_insights": len(insights), "manifest_sha256": manifest_hash}, ensure_ascii=False))


if __name__ == "__main__":
    main()
