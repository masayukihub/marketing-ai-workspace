#!/usr/bin/env python3
"""Compile audited browser snapshots into pipeline input plus resumable manifest."""

from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime
from pathlib import Path


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def iso_date(value: str) -> str:
    value = str(value or "").strip()
    if len(value) >= 10 and value[4] == "-" and value[7] == "-":
        return value[:10]
    return value


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--raw-root", required=True)
    p.add_argument("--output", required=True)
    p.add_argument("--manifest", required=True)
    p.add_argument("--resume-state", required=True)
    p.add_argument("--batch-id", required=True)
    p.add_argument("--date-from", required=True)
    p.add_argument("--date-to", required=True)
    args = p.parse_args()
    root, out, manifest_path, state_path = map(Path, (args.raw_root, args.output, args.manifest, args.resume_state))
    sources = {
        "switchbot_official": ("switchbot_official", "Complete", 34, "7/7 pages; page records 5,5,5,5,5,5,4"),
        "rakuten": ("rakuten", "Complete", 83, "3/3 pages; page records 30,30,23"),
        "yahoo_shopping": ("yahoo_shopping", "Complete", 7, "3/3 size listing pages; declared 1,6,0; 31.5-inch zero confirmed"),
        "amazon_jp": ("amazon_jp", "Partial", 106, "8 public product-page reviews captured of 106 declared; all-review page 1 redirects to sign-in"),
        "x": ("x", "Partial", 40, "40-result public search ceiling; no auditable historical pagination"),
        "youtube": ("youtube", "Partial", 7, "7 relevant video pages captured; comment pagination unavailable without additional access"),
        "media": ("media", "Partial", 5, "5 pages captured; 1 known page failed; keyword-led media scope is not exhaustive"),
    }
    records, coverage, files, completed_pages, failed_pages = [], [], [], {}, []
    for folder, (source, status, expected, boundary) in sources.items():
        base = root / folder / args.batch_id
        pages_path = base / "pages.json"
        pages = json.loads(pages_path.read_text(encoding="utf-8"))
        page_records = []
        if source in {"switchbot_official", "rakuten", "yahoo_shopping", "amazon_jp"}:
            for page in pages:
                page_records.extend(page.get("reviews", []))
        elif source == "x":
            for page in pages:
                page_records.extend(page.get("records", []))
        elif source == "youtube":
            for item in pages:
                page_records.append({
                    "source": "youtube", "source_review_id": item.get("videoId", ""),
                    "product_id": "ai_art_canvas", "channel_product_name": "SwitchBot AIアートキャンバス",
                    "channel_product_url": "https://www.switchbot.jp/products/switchbot-ai-art-frame",
                    "review_url": item.get("url", ""), "review_title": item.get("title", ""),
                    "review_body": item.get("description", ""), "review_date": iso_date(item.get("date", "")),
                    "reviewer_display_name": item.get("channel", ""), "helpful_votes": item.get("likes", ""),
                    "record_type": item.get("record_type", "kol_content"),
                    "relationship_type": item.get("relationship_type", "unknown"),
                    "voc_eligibility": "Context Only", "verified_purchase": "Unknown",
                    "notes": f"views={item.get('views','')}; YouTube video context, not Natural VOC",
                })
        else:
            for item in pages:
                if item.get("url") == "about:blank" or not item.get("review_body"):
                    failed_pages.append({"source": "media", "page": item.get("url") or "known-link-4", "reason": "Navigation unavailable; no raw page content"})
                    continue
                row = {k: v for k, v in item.items() if k not in {"body", "description", "path", "sha256", "bytes", "published", "title", "author"}}
                row["review_date"] = iso_date(row.get("review_date") or item.get("published"))
                row["voc_eligibility"] = "Context Only"
                page_records.append(row)
        for row in page_records:
            row["review_date"] = iso_date(row.get("review_date", ""))
            if row["review_date"] and not args.date_from <= row["review_date"] <= args.date_to:
                continue
            row["coverage_status"] = status
            row["_raw_file_path"] = str(pages_path)
            if source == "amazon_jp":
                variant = row.get("variant_text", "")
                row["asin"] = "B0FVFQBCNW" if "13.3" in variant or "M(" in variant else "B0FVFS6FKN" if "31.5" in variant or "L(" in variant else "B0FVFPD7D5"
            records.append(row)
        actual = len(page_records)
        if source == "media": actual = len(page_records)
        coverage.append({
            "product_id": "ai_art_canvas", "source": source,
            "module": "ec" if source in {"switchbot_official", "rakuten", "yahoo_shopping", "amazon_jp"} else "sns" if source == "x" else "kol" if source == "youtube" else "pr",
            "url": str(pages_path), "required": True, "coverage_status": status,
            "records": actual, "declared_records": expected,
            "failure_reason": "" if status == "Complete" else boundary,
            "pagination_boundary": boundary,
        })
        page_files = sorted(p for p in base.iterdir() if p.is_file() and p.name != "pages.json")
        files.extend({"path": str(f), "sha256": sha256(f), "bytes": f.stat().st_size, "immutable": True} for f in page_files)
        completed_pages[source] = [x.get("page", i + 1) if isinstance(x, dict) else i + 1 for i, x in enumerate(pages)]
    coverage.append({
        "product_id": "ai_art_canvas", "source": "specified_links", "module": "import",
        "url": "", "required": False, "coverage_status": "Not Configured", "records": "",
        "failure_reason": "No specified links were provided", "pagination_boundary": "Not Configured",
    })
    failed_pages.extend([
        {"source": "amazon_jp", "page": "all-reviews-page-1", "reason": "Redirected to sign-in; downstream page count unavailable"},
        {"source": "youtube", "page": "comments-pagination", "reason": "No auditable public full-comment pagination"},
        {"source": "x", "page": "historical-pagination", "reason": "Public search stopped at 40 visible results"},
    ])
    manifest = {
        "schema_version": "1.1", "batch_id": args.batch_id,
        "collected_at": "2026-07-31T23:59:59+09:00",
        "requested_window": {"date_from": args.date_from, "date_to": args.date_to},
        "coverage": coverage, "files": files, "failed_pages": failed_pages,
        "resume_state": str(state_path),
    }
    state = {"schema_version": "1.0", "batch_id": args.batch_id, "completed_pages": completed_pages, "failed_pages": failed_pages, "safe_to_resume": True}
    for path in (out, manifest_path, state_path): path.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(records, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    state_path.write_text(json.dumps(state, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"records": len(records), "coverage": {x["source"]: x["coverage_status"] for x in coverage}, "failed_pages": len(failed_pages)}, ensure_ascii=False))
    return 0


if __name__ == "__main__": raise SystemExit(main())
