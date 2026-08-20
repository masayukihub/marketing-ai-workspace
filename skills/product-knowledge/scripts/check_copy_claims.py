#!/usr/bin/env python3
"""Deterministically lint draft copy against publication-readiness gates."""

from __future__ import annotations

import argparse
import json
import re
import unicodedata
from pathlib import Path

from product_data import add_issue, counts, write_markdown_report

NUMBERED_PERFORMANCE = re.compile(
    r"(?:\d+(?:\.\d+)?|[０-９]+(?:[．.][０-９]+)?)\s*"
    r"(?:秒|分|時間|日|週間|か月|ヶ月|年|dB|台|個|%|％|m|cm|mm|W|Pa)",
    re.IGNORECASE,
)
COMPARATIVE = re.compile(
    r"より(?:安全|安い|速い|静か)|最安|最も安全|最速|safer|cheaper|more secure|best",
    re.IGNORECASE,
)
LAUNCH = re.compile(r"正式発売|発売中|販売中|好評発売|now available|available now", re.IGNORECASE)
UNIVERSAL = re.compile(
    r"あらゆる|すべての(?:家電|Matter)|全ての(?:家電|Matter)|"
    r"所有.{0,12}(?:Matter|产品|產品|设备|設備)|全部.{0,12}(?:Matter|产品|產品|设备|設備)|"
    r"universal|every appliance|all Matter",
    re.IGNORECASE,
)
SUPERLATIVE = re.compile(
    r"日本(?:第一|一)|No\.?\s*1|ナンバーワン|業界初|世界初|"
    r"最先端|最先进|最先進|最高|最強|绝对|絕對|100\s*[%％]|"
    r"best in Japan|number one",
    re.IGNORECASE,
)
FACE_RECOGNITION = re.compile(
    r"顔認証|顔認識|人脸识别|人臉識別|面部识别|面部識別|face recognition",
    re.IGNORECASE,
)


def normalize(value: str) -> str:
    return unicodedata.normalize("NFKC", value).casefold()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--skill-dir", required=True)
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--text")
    source.add_argument("--input", type=Path)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    skill_dir = Path(args.skill_dir).resolve()
    text = args.text if args.text is not None else args.input.read_text(encoding="utf-8")
    normalized = normalize(text)
    index = json.loads(
        (skill_dir / "outputs" / "product_index.json").read_text(encoding="utf-8")
    )
    products = {item["product_id"]: item for item in index.get("products", [])}
    detected = set()
    for alias, product_ids in index.get("alias_lookup", {}).items():
        if normalize(alias) in normalized:
            detected.update(product_ids)
    for product_id in products:
        if normalize(product_id) in normalized:
            detected.add(product_id)

    issues: list[dict] = []
    if not detected:
        add_issue(
            issues, "High", "PRODUCT_NOT_DETECTED",
            "No product was resolved from the draft; manual entity confirmation is required.",
        )
    for product_id in sorted(detected):
        product = products[product_id]
        if not product.get("external_publish_ready"):
            add_issue(
                issues, "Critical", "PRODUCT_NOT_PUBLICATION_READY",
                "Detected product is not ready to support external factual claims.",
                product_id=product_id,
                reasons=", ".join(product.get("readiness", {}).get("blocking_reasons", [])),
            )
    if NUMBERED_PERFORMANCE.search(text):
        add_issue(
            issues, "Critical", "NUMERIC_PERFORMANCE_REQUIRES_APPROVED_CLAIM",
            "Draft contains a performance-like number; link an Approved Claim and every test condition before publication.",
            matches=", ".join(match.group(0) for match in NUMBERED_PERFORMANCE.finditer(text)),
        )
    if "lock ultra" in normalized and FACE_RECOGNITION.search(text) and (
        "keypad vision pro" not in normalized
        and "keypad vision" not in normalized
    ):
        add_issue(
            issues, "Critical", "CAPABILITY_OWNER_COPY_ERROR",
            "Face recognition is attributed to Lock Ultra without the Keypad Vision Pro capability owner.",
        )
    if COMPARATIVE.search(text):
        not_ready = [
            product_id for product_id in detected
            if not products[product_id].get("readiness", {}).get("competitor_evidence_ready")
        ]
        if not_ready or not detected:
            add_issue(
                issues, "Critical", "COMPARATIVE_EVIDENCE_MISSING",
                "Comparative language lacks ready, same-scope competitor evidence.",
                product_ids=", ".join(sorted(not_ready)),
            )
    if LAUNCH.search(text):
        not_ready = [
            product_id for product_id in detected
            if not products[product_id].get("readiness", {}).get("launch_status_ready")
        ]
        if not_ready or not detected:
            add_issue(
                issues, "Critical", "LAUNCH_STATUS_NOT_READY",
                "Launch or on-sale statement is not backed by verified launch status.",
                product_ids=", ".join(sorted(not_ready)),
            )
    if UNIVERSAL.search(text):
        add_issue(
            issues, "Critical", "UNIVERSAL_COMPATIBILITY_CLAIM",
            "Universal compatibility language is prohibited without explicit complete-scope evidence.",
        )
    if SUPERLATIVE.search(text):
        add_issue(
            issues, "Critical", "UNSUPPORTED_SUPERLATIVE_CLAIM",
            "No.1, first, best, absolute, or similar superlative language requires approved, current, market-specific substantiation.",
        )

    totals = counts(issues)
    write_markdown_report(
        Path(args.output), "Draft Claim Lint Report", issues,
        {
            "Detected Products": ", ".join(sorted(detected)) or "None",
            "Publication Decision": "BLOCK" if totals["Critical"] else "MANUAL REVIEW REQUIRED",
        },
    )
    return 1 if totals["Critical"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
