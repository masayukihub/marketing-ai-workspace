#!/usr/bin/env python3
"""Build a stable, fail-closed product index for downstream skills."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path

from product_data import (
    dump_json, load_rows, parse_claims, parse_iso, parse_profiles,
    parse_source_registry,
)


def run_gate(command: list[str]) -> tuple[int, str]:
    result = subprocess.run(command, text=True, capture_output=True)
    return result.returncode, (result.stdout + result.stderr).strip()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--skill-dir", required=True)
    parser.add_argument("--as-of", default=datetime.now().date().isoformat())
    args = parser.parse_args()
    as_of_date = parse_iso(args.as_of)
    skill_dir = Path(args.skill_dir).resolve()
    output_dir = skill_dir / "outputs"
    output_dir.mkdir(parents=True, exist_ok=True)
    python = sys.executable

    validation = output_dir / "validation_report.md"
    conflict = output_dir / "conflict_report.md"
    validate_code, validate_message = run_gate([
        python, str(skill_dir / "scripts" / "validate_product_data.py"),
        "--skill-dir", str(skill_dir), "--output", str(validation),
    ])
    conflict_code, conflict_message = run_gate([
        python, str(skill_dir / "scripts" / "check_conflicts.py"),
        "--skill-dir", str(skill_dir), "--as-of", args.as_of,
        "--output", str(conflict),
    ])
    if validate_code or conflict_code:
        print(json.dumps({
            "ok": False,
            "reason": "Critical validation or unresolved critical conflict",
            "validation": validate_message,
            "conflicts": conflict_message,
        }, ensure_ascii=False, indent=2))
        return 1

    reference_dir = skill_dir / "references"
    _, products = load_rows(reference_dir / "product_master.xlsx")
    _, entities = load_rows(reference_dir / "product_entities.xlsx")
    _, aliases = load_rows(reference_dir / "product_aliases.xlsx")
    _, compatibility = load_rows(reference_dir / "compatibility.xlsx")
    _, facts = load_rows(reference_dir / "product_facts.xlsx")
    _, prices = load_rows(reference_dir / "pricing.xlsx")
    _, competitors = load_rows(reference_dir / "competitor.xlsx")
    _, launches = load_rows(reference_dir / "launch_calendar.xlsx")
    profiles = parse_profiles(skill_dir / "products")
    claims = parse_claims(reference_dir / "claim.md")
    sources = parse_source_registry(reference_dir / "source_registry.md")

    aliases_by_product = defaultdict(list)
    alias_lookup = defaultdict(list)
    excluded_aliases = []
    for row in aliases:
        item = {
            "alias": row.get("alias"),
            "language": row.get("language"),
            "alias_type": row.get("alias_type"),
            "usage_status": row.get("usage_status"),
        }
        aliases_by_product[row.get("product_id")].append(item)
        if row.get("usage_status") == "current":
            alias_lookup[row.get("alias")].append(row.get("product_id"))
        else:
            excluded_aliases.append(item | {"product_id": row.get("product_id")})

    related = defaultdict(set)
    for row in compatibility:
        source = row.get("source_product_id")
        target = row.get("target_product_id")
        if source and target:
            related[source].add(target)
            related[target].add(source)
    for row in facts:
        subject = row.get("subject_product_id")
        for field in ("capability_owner_product_id", "required_product_id"):
            target = row.get(field)
            if subject and target and target != subject:
                related[subject].add(target)

    product_records = []
    for row in products:
        product_id = row["product_id"]
        profile = profiles[product_id]
        reviews = [
            fact.get("review_status") for fact in facts
            if fact.get("subject_product_id") == product_id and fact.get("review_status")
        ]
        approved_claims = []
        for claim_id, claim in claims.items():
            if claim.get("Product ID") != product_id or claim.get("Status") != "Approved":
                continue
            source = sources.get(claim.get("Source ID"), {})
            external_source = "external" in source.get("Allowed Use", "").casefold()
            allowed_channel = claim.get("Allowed Channels", "").casefold() not in {
                "", "none", "none until approval",
            }
            if external_source and allowed_channel:
                approved_claims.append(claim_id)
        current_prices = [
            price for price in prices
            if price.get("product_id") == product_id
            and price.get("review_status") == "approved"
            and parse_iso(price.get("start_date", ""))
            and parse_iso(price.get("end_date", ""))
            and parse_iso(price.get("start_date", "")) <= as_of_date
            <= parse_iso(price.get("end_date", ""))
        ]
        launch_ready = any(
            launch.get("product_id") == product_id
            and launch.get("actual_date")
            and launch.get("review_status") in {"verified", "approved"}
            for launch in launches
        )
        competitor_ready = any(
            competitor.get("our_product_id") == product_id
            and competitor.get("source_url")
            and competitor.get("last_verified_date")
            for competitor in competitors
        )
        blocking_reasons = []
        if profile.get("completeness") != "verified":
            blocking_reasons.append("profile_not_verified")
        if profile.get("review_status") == "conflict":
            blocking_reasons.append("profile_conflict")
        if row.get("status") != "active":
            blocking_reasons.append("lifecycle_not_verified_active")
        if not approved_claims:
            blocking_reasons.append("no_approved_external_claim")
        if any(value in {"draft", "pending_verification", "conflict"} for value in reviews):
            blocking_reasons.append("facts_not_fully_verified")
        external_publish_ready = not blocking_reasons
        product_records.append({
            "product_id": product_id,
            "official_name": {
                "en": row.get("official_name_en"),
                "ja": row.get("official_name_ja"),
                "zh": row.get("official_name_zh"),
            },
            "aliases": aliases_by_product.get(product_id, []),
            "model_number": row.get("model_number"),
            "market": row.get("market"),
            "status": row.get("status"),
            "profile_path": str(profile["path"].relative_to(skill_dir)),
            "completeness": profile.get("completeness"),
            "related_product_ids": sorted(related.get(product_id, set())),
            "review_status": (
                "conflict" if profile.get("review_status") == "conflict"
                else "pending_verification" if not reviews or any(value in {"draft", "pending_verification"} for value in reviews)
                else "verified"
            ),
            "last_verified_date": row.get("last_verified_date"),
            "external_publish_ready": external_publish_ready,
            "readiness": {
                "approved_external_claim_ids": approved_claims,
                "approved_external_claim_count": len(approved_claims),
                "current_price_ready": bool(current_prices),
                "launch_status_ready": launch_ready,
                "competitor_evidence_ready": competitor_ready,
                "blocking_reasons": blocking_reasons,
            },
        })

    entity_records = []
    identifier_lookup = {
        "asin": defaultdict(list),
        "sku": defaultdict(list),
        "jan": defaultdict(list),
        "model_number": defaultdict(list),
    }
    for row in entities:
        entity = {
            "entity_id": row.get("entity_id"),
            "product_id": row.get("product_id"),
            "entity_type": row.get("entity_type"),
            "variant_id": row.get("variant_id"),
            "bundle_id": row.get("bundle_id"),
            "official_name": row.get("official_name"),
            "market": row.get("market"),
            "identifiers": {
                field: row.get(field)
                for field in ("asin", "sku", "jan", "model_number")
                if row.get(field)
            },
            "valid_from": row.get("valid_from"),
            "valid_to": row.get("valid_to"),
            "source_id": row.get("source_id"),
            "review_status": row.get("review_status"),
            "last_verified_date": row.get("last_verified_date"),
            "notes": row.get("notes"),
        }
        entity_records.append(entity)
        if row.get("review_status") in {"verified", "approved"}:
            for field in identifier_lookup:
                value = row.get(field)
                if value:
                    identifier_lookup[field][value].append(row.get("entity_id"))

    generated_at = datetime.now().astimezone().isoformat(timespec="seconds")
    payload = {
        "schema_version": "1.1",
        "generated_at": generated_at,
        "as_of": args.as_of,
        "structural_validation_status": "pass",
        "validation_status": "pass",
        "conflict_status": "pass_with_noncritical_findings",
        "external_publication_ready": all(
            product["external_publish_ready"] for product in product_records
        ),
        "publication_note": "Structural PASS does not mean a product or claim is approved for external publication.",
        "products": product_records,
        "entities": entity_records,
        "identifier_lookup": {
            field: dict(sorted(values.items()))
            for field, values in identifier_lookup.items()
        },
        "alias_lookup": dict(sorted(alias_lookup.items())),
        "excluded_aliases": excluded_aliases,
        "quality_reports": {
            "validation": "outputs/validation_report.md",
            "conflicts": "outputs/conflict_report.md",
        },
    }
    dump_json(output_dir / "product_index.json", payload)
    print(json.dumps({"ok": True, "products": len(product_records), "generated_at": generated_at}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
