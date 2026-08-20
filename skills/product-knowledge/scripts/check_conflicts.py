#!/usr/bin/env python3
"""Detect unresolved product, capability, price, lifecycle, and alias conflicts."""

from __future__ import annotations

import argparse
from collections import defaultdict
from datetime import date
from pathlib import Path

from product_data import (
    add_issue, counts, load_rows, normalize_alias, parse_iso, parse_profiles,
    write_markdown_report,
)


def intervals_overlap(a_start, a_end, b_start, b_end) -> bool:
    low = date.min
    high = date.max
    return (a_start or low) <= (b_end or high) and (b_start or low) <= (a_end or high)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--skill-dir", required=True)
    parser.add_argument("--as-of", required=True)
    parser.add_argument("--output")
    args = parser.parse_args()
    skill_dir = Path(args.skill_dir).resolve()
    reference_dir = skill_dir / "references"
    as_of = date.fromisoformat(args.as_of)
    output = Path(args.output) if args.output else skill_dir / "outputs" / "conflict_report.md"
    issues: list[dict] = []

    _, products = load_rows(reference_dir / "product_master.xlsx")
    _, facts = load_rows(reference_dir / "product_facts.xlsx")
    _, prices = load_rows(reference_dir / "pricing.xlsx")
    _, aliases = load_rows(reference_dir / "product_aliases.xlsx")
    _, discontinued = load_rows(reference_dir / "discontinued_products.xlsx")
    profiles = parse_profiles(skill_dir / "products")

    grouped_facts = defaultdict(list)
    for fact in facts:
        key = (
            fact.get("subject_product_id"), fact.get("fact_name"),
            fact.get("market"), fact.get("valid_from"), fact.get("valid_to"),
        )
        grouped_facts[key].append(fact)
        name = fact.get("fact_name", "").casefold()
        if "face" in name and fact.get("capability_owner_product_id") == "lock_ultra":
            add_issue(issues, "Critical", "CAPABILITY_OWNER_INVALID", "Face-recognition capability is assigned to Lock Ultra instead of Keypad Vision Pro.", fact_id=fact.get("fact_id"))
        if fact.get("review_status") == "approved" and fact.get("release_status") in {"unknown", "announced", "firmware_required"}:
            add_issue(issues, "Critical", "APPROVED_SUPPORT_CONFLICT", "Approved fact is not currently released without qualification.", fact_id=fact.get("fact_id"))
        if fact.get("review_status") == "approved" and fact.get("fact_type") in {"performance", "battery", "speed", "noise", "range", "design"} and not fact.get("conditions"):
            add_issue(issues, "Critical", "APPROVED_CONDITIONS_MISSING", "Approved performance claim lacks conditions.", fact_id=fact.get("fact_id"))

    for key, rows in grouped_facts.items():
        values = {row.get("fact_value") for row in rows}
        if len(values) > 1:
            add_issue(issues, "Critical", "FACT_MULTI_VALUE", "Same fact scope contains multiple values; source priority must not silently overwrite.", subject=key[0], fact_name=key[1], values=" | ".join(sorted(values)))

    by_price_scope = defaultdict(list)
    for row in prices:
        scope = (row.get("product_id"), row.get("channel"), row.get("market"), row.get("price_type"), row.get("currency"), row.get("tax_included"))
        by_price_scope[scope].append(row)
        start, end = parse_iso(row.get("start_date", "")), parse_iso(row.get("end_date", ""))
        is_current = (start is None or start <= as_of) and (end is None or as_of <= end)
        if is_current and not all(row.get(field) for field in ("channel", "market", "price_type", "currency", "tax_included", "start_date", "end_date")):
            add_issue(issues, "Critical", "CURRENT_PRICE_CONTEXT_INCOMPLETE", "Current price lacks complete channel, market, type, tax, or validity context.", product_id=row.get("product_id"))
        if end and end < as_of and row.get("review_status") not in {"expired", "rejected"}:
            add_issue(issues, "High", "PRICE_EXPIRED_ACTIVE", "Expired price remains in a non-expired review state.", product_id=row.get("product_id"), end_date=end)

    for scope, rows in by_price_scope.items():
        for index, left in enumerate(rows):
            for right in rows[index + 1:]:
                if intervals_overlap(parse_iso(left.get("start_date", "")), parse_iso(left.get("end_date", "")), parse_iso(right.get("start_date", "")), parse_iso(right.get("end_date", ""))):
                    left_value = left.get("sale_price") or left.get("regular_price")
                    right_value = right.get("sale_price") or right.get("regular_price")
                    if left_value != right_value:
                        add_issue(issues, "Critical", "PRICE_INTERVAL_CONFLICT", "Overlapping price records disagree.", product_id=scope[0], channel=scope[1], values=f"{left_value} | {right_value}")

    alias_targets = defaultdict(set)
    for row in aliases:
        if row.get("usage_status") == "current":
            alias_targets[normalize_alias(row.get("alias", ""))].add(row.get("product_id"))
        elif row.get("usage_status") == "ambiguous":
            add_issue(issues, "High", "ALIAS_AMBIGUOUS", "Alias is intentionally excluded from exact product resolution.", alias=row.get("alias"), product_id=row.get("product_id"))
    for alias, targets in alias_targets.items():
        if len(targets) > 1:
            add_issue(issues, "Critical", "ALIAS_ONE_TO_MANY", "Current alias maps to multiple products.", alias=alias, products=", ".join(sorted(targets)))

    status_by_product = {row.get("product_id"): row.get("status") for row in products}
    for row in discontinued:
        if status_by_product.get(row.get("product_id")) == "active":
            add_issue(issues, "Critical", "DISCONTINUED_STILL_ACTIVE", "Discontinued product is still active in product master.", product_id=row.get("product_id"))

    fact_ids = {row.get("fact_id") for row in facts}
    for product_id, profile in profiles.items():
        missing = set(profile["linked"].get("Fact IDs", [])) - fact_ids
        if missing:
            add_issue(issues, "Critical", "PROFILE_FACT_DRIFT", "Profile links facts not present in the fact layer.", product_id=product_id, fact_ids=", ".join(sorted(missing)))
        if profile.get("review_status") == "conflict":
            add_issue(issues, "High", "PROFILE_REVIEW_CONFLICT", "Profile remains conflict-marked and cannot support external claims.", product_id=product_id)

    totals = counts(issues)
    write_markdown_report(output, "Product Knowledge Conflict Report", issues, {"As Of": as_of, "Products": len(products), "Facts": len(facts), "Prices": len(prices)})
    return 1 if totals["Critical"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
