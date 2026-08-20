#!/usr/bin/env python3
"""Validate Product Knowledge schemas, enums, references, dates, and profiles."""

from __future__ import annotations

import argparse
import re
from pathlib import Path

from product_data import (
    CLAIM_STATUS, RELEASE_STATUS, REVIEW_STATUS, add_issue, counts, load_rows,
    parse_claims, parse_iso, parse_profiles, parse_source_registry,
    write_markdown_report,
)

REQUIRED = {
    "product_master.xlsx": {"product_id", "official_name_en", "market", "status", "source_id", "last_verified_date"},
    "product_entities.xlsx": {
        "entity_id", "product_id", "entity_type", "official_name", "market",
        "source_id", "review_status", "last_verified_date",
    },
    "product_specs.xlsx": {"product_id", "spec_category", "spec_name", "spec_value", "conditions", "market", "source_id", "review_status", "last_verified_date"},
    "pricing.xlsx": {"product_id", "channel", "market", "price_type", "currency", "tax_included", "source_id", "review_status", "last_verified_date"},
    "competitor.xlsx": {"our_product_id", "competitor_brand", "competitor_product", "market", "source_url", "source_id", "collected_date", "last_verified_date"},
    "product_positioning.xlsx": {"product_id", "audience", "scenario", "channel", "source_id", "review_status", "last_verified_date"},
    "compatibility.xlsx": {"source_product_id", "target_product_or_platform", "relationship_type", "support_status", "region", "source_id", "review_status", "last_verified_date"},
    "product_aliases.xlsx": {"alias", "product_id", "alias_type", "language", "usage_status", "source_id", "last_verified_date"},
    "launch_calendar.xlsx": {"product_id", "market", "launch_stage", "source_id", "review_status", "last_verified_date"},
    "discontinued_products.xlsx": {"product_id", "market", "discontinued_date", "source_id", "review_status", "last_verified_date"},
    "product_facts.xlsx": {
        "fact_id", "subject_product_id", "capability_owner_product_id",
        "fact_type", "fact_name", "fact_value", "release_status", "market",
        "source_id", "source_revision_id", "review_status", "last_verified_date",
    },
}

PRODUCT_FACT_HEADERS = {
    "fact_id", "subject_product_id", "capability_owner_product_id",
    "required_product_id", "fact_type", "fact_name", "fact_value", "unit",
    "conditions", "release_status", "market", "firmware_requirement",
    "valid_from", "valid_to", "source_id", "source_revision_id",
    "review_status", "last_verified_date",
}

PRODUCT_COLUMNS = {
    "product_id", "our_product_id", "source_product_id", "target_product_id",
    "subject_product_id", "capability_owner_product_id", "required_product_id",
    "replacement_product_id",
}
ENTITY_TYPES = {"product", "variant", "bundle"}
DATE_COLUMNS = {
    "launch_date_jp", "last_verified_date", "valid_from", "valid_to", "start_date",
    "end_date", "collected_date", "planned_date", "actual_date", "discontinued_date",
}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--skill-dir", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    skill_dir = Path(args.skill_dir).resolve()
    reference_dir = skill_dir / "references"
    issues: list[dict] = []
    sources = parse_source_registry(reference_dir / "source_registry.md")
    tables: dict[str, list[dict]] = {}

    for source_id, source in sources.items():
        for field in ("Revision ID", "Retrieved At", "Confidentiality", "Allowed Use", "External Use Restriction"):
            if not source.get(field):
                add_issue(issues, "High", "SOURCE_METADATA_MISSING", "Source metadata is incomplete.", source_id=source_id, field=field)
        location = source.get("URL / File", "")
        if location.startswith("http") and not re.match(r"^https://", location):
            add_issue(issues, "High", "SOURCE_URL_INVALID", "External source URL must use HTTPS.", source_id=source_id)

    for filename, required in REQUIRED.items():
        path = reference_dir / filename
        if not path.exists():
            add_issue(issues, "Critical", "FILE_MISSING", "Required workbook is missing.", file=filename)
            continue
        try:
            headers, rows = load_rows(path)
        except Exception as exc:
            add_issue(issues, "Critical", "WORKBOOK_READ_FAILED", str(exc), file=filename)
            continue
        tables[filename] = rows
        expected = PRODUCT_FACT_HEADERS if filename == "product_facts.xlsx" else required
        missing = sorted(expected - set(headers))
        if missing:
            add_issue(issues, "Critical", "COLUMN_MISSING", "Required columns are missing.", file=filename, columns=", ".join(missing))
        for row_number, row in enumerate(rows, 2):
            for field in required:
                if field in headers and not row.get(field):
                    if filename in {"pricing.xlsx", "competitor.xlsx", "discontinued_products.xlsx", "product_positioning.xlsx"} and not any(row.values()):
                        continue
                    add_issue(issues, "Critical", "REQUIRED_VALUE_MISSING", "Required cell is blank.", file=filename, row=row_number, field=field)
            for field in DATE_COLUMNS & set(headers):
                value = row.get(field, "")
                if value:
                    try:
                        parse_iso(value)
                    except ValueError:
                        add_issue(issues, "Critical", "DATE_INVALID", "Date must be YYYY-MM-DD.", file=filename, row=row_number, field=field, value=value)
            if row.get("review_status") and row["review_status"] not in REVIEW_STATUS:
                add_issue(issues, "Critical", "REVIEW_STATUS_INVALID", "Invalid review_status.", file=filename, row=row_number, value=row["review_status"])
            if row.get("release_status") and row["release_status"] not in RELEASE_STATUS:
                add_issue(issues, "Critical", "RELEASE_STATUS_INVALID", "Invalid release_status.", file=filename, row=row_number, value=row["release_status"])
            if row.get("source_id") and row["source_id"] not in sources:
                add_issue(issues, "Critical", "SOURCE_REFERENCE_INVALID", "Row references an unknown source_id.", file=filename, row=row_number, source_id=row["source_id"])

    products = tables.get("product_master.xlsx", [])
    product_ids = {row["product_id"] for row in products if row.get("product_id")}
    duplicate_ids = sorted({
        product_id for product_id in product_ids
        if sum(row.get("product_id") == product_id for row in products) > 1
    })
    for product_id in duplicate_ids:
        add_issue(issues, "Critical", "PRODUCT_ID_DUPLICATE", "product_id must be unique.", product_id=product_id)
    for row in products:
        product_id = row.get("product_id")
        if row.get("market") == "JP" and not row.get("official_name_ja"):
            add_issue(
                issues, "High", "JP_OFFICIAL_NAME_MISSING",
                "Japan-market product lacks a verified official Japanese name.",
                product_id=product_id,
            )
        if row.get("status") == "unknown":
            add_issue(
                issues, "High", "PRODUCT_LIFECYCLE_UNKNOWN",
                "Product lifecycle or release status is unknown.",
                product_id=product_id,
            )

    aliases = tables.get("product_aliases.xlsx", [])
    languages_by_product: dict[str, set[str]] = {
        product_id: {
            row.get("language") for row in aliases
            if row.get("product_id") == product_id and row.get("usage_status") == "current"
        }
        for product_id in product_ids
    }
    for product_id, languages in sorted(languages_by_product.items()):
        if "ja" not in languages:
            add_issue(
                issues, "High", "JP_ALIAS_COVERAGE_MISSING",
                "Product has no current Japanese alias for exact entity resolution.",
                product_id=product_id,
            )
        if "zh" not in languages:
            add_issue(
                issues, "Medium", "ZH_ALIAS_COVERAGE_MISSING",
                "Product has no current Chinese alias; Chinese task prompts may remain unresolved.",
                product_id=product_id,
            )

    entities = tables.get("product_entities.xlsx", [])
    entity_ids = [row.get("entity_id") for row in entities if row.get("entity_id")]
    for entity_id in sorted({item for item in entity_ids if entity_ids.count(item) > 1}):
        add_issue(issues, "Critical", "ENTITY_ID_DUPLICATE", "entity_id must be unique.", entity_id=entity_id)
    for row_number, entity in enumerate(entities, 2):
        if entity.get("entity_type") not in ENTITY_TYPES:
            add_issue(issues, "Critical", "ENTITY_TYPE_INVALID", "entity_type is invalid.", row=row_number, value=entity.get("entity_type"))
        if entity.get("product_id") not in product_ids:
            add_issue(issues, "Critical", "ENTITY_PRODUCT_UNKNOWN", "Entity references an unknown product_id.", row=row_number, product_id=entity.get("product_id"))
        if entity.get("entity_type") == "variant" and not entity.get("variant_id"):
            add_issue(issues, "Critical", "VARIANT_ID_MISSING", "Variant entity requires variant_id.", row=row_number)
        if entity.get("entity_type") == "bundle" and not entity.get("bundle_id"):
            add_issue(issues, "Critical", "BUNDLE_ID_MISSING", "Bundle entity requires bundle_id.", row=row_number)
        identifiers = [entity.get(field) for field in ("asin", "sku", "jan", "model_number") if entity.get(field)]
        if len(identifiers) != len(set(identifiers)):
            add_issue(issues, "Critical", "ENTITY_IDENTIFIER_REPEATED", "Identifier values must not repeat within one entity.", row=row_number)
    for field in ("asin", "sku", "jan"):
        seen_identifiers: dict[str, str] = {}
        for entity in entities:
            value = entity.get(field)
            if not value or entity.get("review_status") not in {"verified", "approved"}:
                continue
            previous = seen_identifiers.get(value)
            if previous and previous != entity.get("entity_id"):
                add_issue(issues, "Critical", "ENTITY_IDENTIFIER_CONFLICT", "Verified identifier maps to multiple entities.", field=field, value=value)
            seen_identifiers[value] = entity.get("entity_id")
    alias_types = {row.get("alias_type") for row in aliases}
    for alias_type in ("internal_name", "typo"):
        if alias_type not in alias_types:
            add_issue(
                issues, "Medium", "ALIAS_TYPE_COVERAGE_MISSING",
                "Alias registry has no entries for a supported governance type.",
                alias_type=alias_type,
            )

    if not tables.get("pricing.xlsx", []):
        add_issue(
            issues, "High", "PRICING_DATA_EMPTY",
            "Pricing schema exists but contains no channel- and date-qualified price records.",
        )
    if not tables.get("competitor.xlsx", []):
        add_issue(
            issues, "High", "COMPETITOR_DATA_EMPTY",
            "Competitor schema exists but contains no dated competitor records.",
        )
    compatibility = tables.get("compatibility.xlsx", [])
    if compatibility and all(row.get("support_status") == "unknown" for row in compatibility):
        add_issue(
            issues, "High", "COMPATIBILITY_STATUS_UNRESOLVED",
            "All compatibility records have unknown support status.",
            rows=len(compatibility),
        )
    if compatibility and not any(row.get("firmware_requirement") for row in compatibility):
        add_issue(
            issues, "High", "COMPATIBILITY_FIRMWARE_UNRECORDED",
            "No compatibility record contains a concrete firmware requirement.",
        )

    facts = tables.get("product_facts.xlsx", [])
    fact_ids = {row["fact_id"] for row in facts if row.get("fact_id")}
    for fact_id in sorted({
        fact_id for fact_id in fact_ids
        if sum(row.get("fact_id") == fact_id for row in facts) > 1
    }):
        add_issue(issues, "Critical", "FACT_ID_DUPLICATE", "fact_id must be unique.", fact_id=fact_id)

    for filename, rows in tables.items():
        for row_number, row in enumerate(rows, 2):
            for field in PRODUCT_COLUMNS & set(row):
                value = row.get(field, "")
                if value and value not in product_ids:
                    add_issue(issues, "Critical", "PRODUCT_REFERENCE_INVALID", "Unknown product_id reference.", file=filename, row=row_number, field=field, product_id=value)

    for row_number, fact in enumerate(facts, 2):
        if fact.get("fact_type") in {"performance", "battery", "speed", "noise", "range", "design"} and not fact.get("conditions"):
            severity = "Critical" if fact.get("review_status") == "approved" else "High"
            add_issue(issues, severity, "FACT_CONDITIONS_MISSING", "Performance-like fact lacks test or use conditions.", row=row_number, fact_id=fact.get("fact_id"))
        if fact.get("review_status") == "approved" and fact.get("release_status") == "unknown":
            add_issue(issues, "Critical", "APPROVED_RELEASE_UNKNOWN", "Approved fact cannot have unknown release status.", fact_id=fact.get("fact_id"))

    claims = parse_claims(reference_dir / "claim.md")
    for claim_id, claim in claims.items():
        status = claim.get("Status", "")
        if status not in CLAIM_STATUS:
            add_issue(issues, "Critical", "CLAIM_STATUS_INVALID", "Claim has invalid status.", claim_id=claim_id, value=status)
        if status == "Approved" and not claim.get("Approval Evidence"):
            add_issue(issues, "Critical", "CLAIM_APPROVAL_EVIDENCE_MISSING", "Approved claim lacks explicit approval evidence.", claim_id=claim_id)
    claim_statuses = {claim.get("Status") for claim in claims.values()}
    for expected_status in ("Approved", "Conditional", "Prohibited"):
        if expected_status not in claim_statuses:
            add_issue(
                issues, "Medium", "CLAIM_STATUS_COVERAGE_MISSING",
                "Claim registry currently has no entries in this governance state.",
                status=expected_status,
            )

    known_issues_text = (reference_dir / "known_issues.md").read_text(encoding="utf-8")
    if not re.search(
        r"官网图片|official (?:website )?image|website image",
        known_issues_text,
        re.IGNORECASE,
    ):
        add_issue(
            issues, "High", "KNOWN_ISSUE_IMAGE_VERSION_GAP",
            "Known Issues does not record or explicitly clear official-image versus current-version mismatch risk.",
        )

    profiles = parse_profiles(skill_dir / "products")
    if len(profiles) != 18:
        add_issue(issues, "Critical", "PROFILE_COUNT_INVALID", "Initial release must contain exactly 18 group profiles.", count=len(profiles))
    for product_id in sorted(product_ids - set(profiles)):
        add_issue(issues, "Critical", "PROFILE_MISSING", "Product master row lacks a profile.", product_id=product_id)
    for product_id in sorted(set(profiles) - product_ids):
        add_issue(issues, "Critical", "PROFILE_PRODUCT_UNKNOWN", "Profile references a product absent from master.", product_id=product_id)
    for product_id, profile in profiles.items():
        if profile["completeness"] not in {"skeleton", "partial", "verified"}:
            add_issue(issues, "Critical", "PROFILE_COMPLETENESS_INVALID", "Profile completeness is invalid.", product_id=product_id, value=profile["completeness"])
        for fact_id in profile["linked"].get("Fact IDs", []):
            if fact_id not in fact_ids:
                add_issue(issues, "Critical", "PROFILE_FACT_INVALID", "Profile links an unknown fact.", product_id=product_id, fact_id=fact_id)
        for source_id in profile["linked"].get("Source IDs", []):
            if source_id not in sources:
                add_issue(issues, "Critical", "PROFILE_SOURCE_INVALID", "Profile links an unknown source.", product_id=product_id, source_id=source_id)

    totals = counts(issues)
    write_markdown_report(
        Path(args.output), "Product Knowledge Validation Report", issues,
        {"Skill Directory": skill_dir, "Products": len(product_ids), "Facts": len(fact_ids), "Sources": len(sources), "Profiles": len(profiles)},
    )
    return 1 if totals["Critical"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
