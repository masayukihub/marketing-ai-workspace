#!/usr/bin/env python3
"""Generate the derived Product Knowledge Hub without changing canonical facts."""

from __future__ import annotations

import argparse
import csv
import json
import re
from collections import defaultdict
from datetime import date, datetime
from pathlib import Path

from product_data import load_rows, parse_claims, parse_iso, parse_profiles, parse_source_registry


SECTIONS = (
    "overview", "positioning", "specs", "selling_points", "claims", "compatibility",
    "faq", "target_audience", "use_cases", "competitors", "channel_messages", "sources",
)


def write_csv(path: Path, headers: list[str], rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=headers, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def linked_product_ids(raw: str) -> list[str]:
    return re.findall(r"[a-z0-9]+(?:_[a-z0-9]+)+", raw or "")


def source_priority(source: dict[str, str]) -> str:
    try:
        level = int(source.get("Reliability Level", ""))
    except ValueError:
        return "P5"
    if level == 1:
        return "P1"
    if level in {2, 3, 4}:
        return "P2"
    if level == 5:
        return "P3"
    if level in {6, 7}:
        return "P4"
    return "P5"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--skill-dir", required=True)
    parser.add_argument("--as-of", default=date.today().isoformat())
    parser.add_argument("--write-baseline-snapshot", action="store_true")
    args = parser.parse_args()
    skill_dir = Path(args.skill_dir).resolve()
    ref = skill_dir / "references"
    knowledge = skill_dir / "knowledge"
    product_dir = knowledge / "products"
    product_dir.mkdir(parents=True, exist_ok=True)
    as_of = parse_iso(args.as_of) or date.today()

    _, products = load_rows(ref / "product_master.xlsx")
    _, facts = load_rows(ref / "product_facts.xlsx")
    _, specs = load_rows(ref / "product_specs.xlsx")
    _, pricing = load_rows(ref / "pricing.xlsx")
    _, compatibility = load_rows(ref / "compatibility.xlsx")
    _, competitors = load_rows(ref / "competitor.xlsx")
    _, positioning = load_rows(ref / "product_positioning.xlsx")
    claims = parse_claims(ref / "claim.md")
    sources = parse_source_registry(ref / "source_registry.md")
    profiles = parse_profiles(skill_dir / "products")
    faq_text = (ref / "faq.md").read_text(encoding="utf-8")
    conflict_path = skill_dir / "outputs" / "conflict_report.md"
    conflict_text = conflict_path.read_text(encoding="utf-8") if conflict_path.exists() else ""

    by_subject = defaultdict(list)
    by_spec = defaultdict(list)
    by_price = defaultdict(list)
    by_compatibility = defaultdict(list)
    by_competitor = defaultdict(list)
    by_positioning = defaultdict(list)
    by_claim = defaultdict(list)
    for row in facts:
        by_subject[row.get("subject_product_id")].append(row)
    for row in specs:
        by_spec[row.get("product_id")].append(row)
    for row in pricing:
        by_price[row.get("product_id")].append(row)
    for row in compatibility:
        by_compatibility[row.get("source_product_id")].append(row)
    for row in competitors:
        by_competitor[row.get("our_product_id")].append(row)
    for row in positioning:
        by_positioning[row.get("product_id")].append(row)
    for claim_id, claim in claims.items():
        by_claim[claim.get("Product ID")].append((claim_id, claim))

    index_rows: list[dict[str, object]] = []
    source_products: dict[str, set[str]] = defaultdict(set)
    for product in products:
        product_id = product["product_id"]
        profile = profiles.get(product_id, {})
        facts_for = by_subject[product_id]
        specs_for = by_spec[product_id]
        claims_for = by_claim[product_id]
        compat_for = by_compatibility[product_id]
        sources_for = {product.get("source_id")}
        for rows in (facts_for, specs_for, by_price[product_id], compat_for, by_competitor[product_id], by_positioning[product_id]):
            sources_for.update(row.get("source_id") for row in rows if row.get("source_id"))
        sources_for.update(claim.get("Source ID") for _, claim in claims_for if claim.get("Source ID"))
        sources_for.discard("")
        for source_id in sources_for:
            source_products[source_id].add(product_id)
        dates = [parse_iso(product.get("last_verified_date", ""))]
        for rows in (facts_for, specs_for, by_price[product_id], compat_for, by_competitor[product_id], by_positioning[product_id]):
            dates.extend(parse_iso(row.get("last_verified_date", "")) for row in rows)
        last_verified = max((item for item in dates if item), default=None)
        freshness = max(0, 100 - max(0, (as_of - last_verified).days)) if last_verified else 0
        faq_present = bool(re.search(rf"(?m)^- Product ID:.*\b{re.escape(product_id)}\b", faq_text))
        section_presence = {
            "overview": bool(product.get("official_name_en") and product.get("source_id")),
            "positioning": bool(product.get("one_sentence_positioning") or by_positioning[product_id]),
            "specs": bool(specs_for),
            "selling_points": bool(facts_for or product.get("key_feature_1")),
            "claims": bool(claims_for),
            "compatibility": bool(compat_for),
            "faq": faq_present,
            "target_audience": bool(product.get("primary_target")),
            "use_cases": bool(product.get("primary_use_case")),
            "competitors": bool(by_competitor[product_id]),
            "channel_messages": bool(by_positioning[product_id]),
            "sources": bool(sources_for),
        }
        completeness = round(sum(section_presence.values()) / len(SECTIONS) * 100)
        conflicts = len(re.findall(rf"product_id={re.escape(product_id)}\b", conflict_text))
        missing = "; ".join(name for name, present in section_presence.items() if not present)
        index_rows.append({
            "product_id": product_id,
            "product_name_en": product.get("official_name_en"),
            "product_name_ja": product.get("official_name_ja"),
            "category": product.get("category"),
            "series": product.get("product_series"),
            "launch_date": product.get("launch_date_jp"),
            "lifecycle_status": product.get("status"),
            "product_owner": product.get("data_owner"),
            "knowledge_status": profile.get("review_status", "pending_verification"),
            "completeness_score": completeness,
            "freshness_score": freshness,
            "last_updated": last_verified.isoformat() if last_verified else "",
            "source_count": len(sources_for),
            "unresolved_conflict_count": conflicts,
            "missing": missing,
        })

        fact_lines = [f"- `{row.get('fact_id')}` — {row.get('fact_name')}: {row.get('fact_value')} ({row.get('review_status')}; {row.get('source_id')})" for row in facts_for] or ["- 未确认：尚无可复用的原子事实。"]
        claim_lines = [f"- `{claim_id}` — {claim.get('Claim')} ({claim.get('Status')}; {claim.get('Source ID')})" for claim_id, claim in claims_for] or ["- 未确认：尚无Claim记录。"]
        source_lines = [f"- `{source_id}` — {sources.get(source_id, {}).get('Source Name', '未登记来源')}" for source_id in sorted(sources_for)] or ["- 未确认：无来源。"]
        approved_claims = [item for item in claims_for if item[1].get("Status") == "Approved"]
        channel_message = (
            "- 可复用外发Message：暂无。必须先获得Approved Claim。"
            if not approved_claims else "- 可复用外发Message：请仅使用下列Approved Claim并保留条件。"
        )
        page = [
            f"# {product.get('official_name_en') or product_id}", "",
            "此文件为从规范事实层生成的营销知识摘要，不是事实源。每次更新后重新生成。", "",
            "## Overview", "",
            f"- Product ID: {product_id}",
            f"- 日本正式名称: {product.get('official_name_ja') or '未确认'}",
            f"- 中文名称: {product.get('official_name_zh') or '未确认'}",
            f"- Category: {product.get('category') or '未确认'}",
            f"- Lifecycle: {product.get('status') or 'unknown'}",
            f"- Completeness: {completeness}/100; Freshness: {freshness}/100", "",
            "## Positioning", "", f"- {product.get('one_sentence_positioning') or '未确认'}", "",
            "## Selling Points", "", *fact_lines, "",
            "## Specifications", "", *([f"- {row.get('spec_name')}: {row.get('spec_value')} {row.get('unit')} ({row.get('review_status')}; {row.get('source_id')})" for row in specs_for] or ["- 未确认。"]), "",
            "## Claims", "", *claim_lines, "",
            "## Compatibility", "", *([f"- {row.get('target_product_or_platform')}: {row.get('support_status')} ({row.get('requirements') or '条件未确认'}; {row.get('source_id')})" for row in compat_for] or ["- 未确认。"]), "",
            "## FAQ", "", "- 已登记。" if faq_present else "- 未确认。", "",
            "## Channel Reuse", "", channel_message, "",
            "## Risks and Limitations", "", "- 未确认、冲突或非Approved Claim不得用于外发。", "",
            "## Sources", "", *source_lines, "",
        ]
        (product_dir / f"{product_id}.md").write_text("\n".join(page), encoding="utf-8")

    index_headers = list(index_rows[0]) if index_rows else []
    write_csv(knowledge / "product_index.csv", index_headers, index_rows)
    source_rows = []
    for source_id, source in sorted(sources.items()):
        mapped_products = sorted(source_products.get(source_id) or linked_product_ids(source.get("Applicable Products", "")) or [""])
        for product_id in mapped_products:
            source_rows.append({
                "source_id": source_id,
                "product_id": product_id,
                "information_type": source.get("Source Type", ""),
                "source_name": source.get("Source Name", ""),
                "source_url": source.get("URL / File", ""),
                "source_type": source.get("Source Type", ""),
                "owner": source.get("Owner", ""),
                "document_updated_at": source.get("Last Updated", ""),
                "retrieved_at": source.get("Retrieved At", ""),
                "source_priority": source_priority(source),
                "status": source.get("Allowed Use", ""),
                "notes": source.get("Notes", ""),
            })
    write_csv(knowledge / "source_registry.csv", list(source_rows[0]) if source_rows else [], source_rows)
    conflicts = []
    for line in conflict_text.splitlines():
        match = re.match(r"- \[(?P<severity>[^\]]+)\] `(?P<code>[^`]+)` — (?P<message>.*)", line)
        if match:
            conflicts.append({"severity": match.group("severity"), "code": match.group("code"), "detail": match.group("message"), "status": "Needs Review"})
    write_csv(knowledge / "conflict_registry.csv", ["severity", "code", "detail", "status"], conflicts)
    summary = ["# Product Knowledge Hub Status", "", f"- Generated at: {datetime.now().astimezone().isoformat(timespec='seconds')}", f"- Products: {len(index_rows)}", f"- Sources: {len(source_rows)}", f"- Open conflicts: {len(conflicts)}", "", "## Completeness ranking", "", "| Product | Completeness | Freshness | Sources | Conflicts | Missing |", "|---|---:|---:|---:|---:|---|"]
    for row in sorted(index_rows, key=lambda item: (item["completeness_score"], item["product_id"]), reverse=True):
        summary.append(f"| {row['product_id']} | {row['completeness_score']} | {row['freshness_score']} | {row['source_count']} | {row['unresolved_conflict_count']} | {row['missing'] or '-'} |")
    (knowledge / "latest_update_summary.md").write_text("\n".join(summary) + "\n", encoding="utf-8")
    payload = {"schema_version": "2.0", "generated_at": datetime.now().astimezone().isoformat(timespec="seconds"), "as_of": args.as_of, "products": len(index_rows), "sources": len(source_rows), "knowledge_index": "knowledge/product_index.csv", "summary": "knowledge/latest_update_summary.md"}
    (skill_dir / "outputs" / "knowledge_hub_status.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    if args.write_baseline_snapshot:
        snapshots = skill_dir / "snapshots"
        snapshots.mkdir(parents=True, exist_ok=True)
        (snapshots / f"hub-baseline-{args.as_of}.json").write_text(json.dumps(payload | {"kind": "hub_baseline"}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"ok": True, "products": len(index_rows), "knowledge_dir": str(knowledge)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
