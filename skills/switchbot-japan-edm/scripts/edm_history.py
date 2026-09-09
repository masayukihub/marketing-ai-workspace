#!/usr/bin/env python3
"""Plan evidence-backed EDM inheritance without copying private email content.

Python 3 standard library only. This planner verifies local evidence availability;
it does not perform visual review, approve a template, or measure performance.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import sys
from typing import Any


SCHEMA_VERSION = "1.0"
DEFAULT_CATALOG = Path(__file__).resolve().parents[1] / "assets/history-recipes.json"
LIVE_DELIVERIES = {"marketing_received_copy", "sent_marketing"}
CAMPAIGN_TYPES = {"sale_launch", "seasonal_promotion", "category_promotion", "product_launch"}
SAFE_ID = re.compile(r"^[A-Za-z][A-Za-z0-9_.:-]{0,127}$")
RECIPE_FIELDS = {
    "id", "campaign_types", "stages", "channels", "product_range", "source_refs",
    "primary_source_ref", "hero_style", "card_layout", "modules", "tokens", "status",
    "module_treatments",
}


def digest(value: Any) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False,
                                     separators=(",", ":")).encode("utf-8")).hexdigest()


def file_digest(path: Path) -> str:
    sha = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            sha.update(chunk)
    return sha.hexdigest()


def valid_id(value: Any) -> bool:
    return isinstance(value, str) and bool(SAFE_ID.fullmatch(value))


def image_evidence(path: Path) -> dict[str, Any] | None:
    """Require a nonempty recognizable raster; never fetch remote evidence."""
    try:
        if not path.is_file() or path.stat().st_size == 0:
            return None
        with path.open("rb") as stream:
            head = stream.read(32)
        is_image = (
            head.startswith(b"\x89PNG\r\n\x1a\n")
            or head.startswith(b"\xff\xd8\xff")
            or head.startswith((b"GIF87a", b"GIF89a"))
            or (head.startswith(b"RIFF") and head[8:12] == b"WEBP")
        )
        if not is_image:
            return None
        return {"sha256": file_digest(path), "bytes": path.stat().st_size}
    except (OSError, ValueError):
        return None


def validate_brief(brief: Any) -> list[str]:
    if not isinstance(brief, dict):
        return ["brief must be an object"]
    errors = []
    for key in ("campaign_type", "stage", "channel"):
        if not isinstance(brief.get(key), str) or not brief[key].strip():
            errors.append(f"{key} must be a nonempty string")
    count = brief.get("product_count")
    if isinstance(count, bool) or not isinstance(count, int) or count < 1:
        errors.append("product_count must be a positive integer")
    if "explicit_new_design" in brief and not isinstance(brief["explicit_new_design"], bool):
        errors.append("explicit_new_design must be a boolean")
    if brief.get("preferred_recipe") is not None and not valid_id(brief["preferred_recipe"]):
        errors.append("preferred_recipe must be a stable recipe ID")
    return errors


def validated_recipes(catalog: Any) -> list[dict[str, Any]]:
    if not isinstance(catalog, dict) or catalog.get("schema_version") != SCHEMA_VERSION:
        raise ValueError("catalog.schema_version must be 1.0")
    recipes = catalog.get("recipes")
    if not isinstance(recipes, list):
        raise ValueError("catalog.recipes must be an array")
    seen = set()
    result = []
    for recipe in recipes:
        if not isinstance(recipe, dict) or not valid_id(recipe.get("id")):
            raise ValueError("each recipe needs a stable ID")
        if recipe["id"] in seen:
            raise ValueError("recipe IDs must be unique")
        seen.add(recipe["id"])
        for key in ("campaign_types", "stages", "channels", "source_refs", "modules"):
            values = recipe.get(key)
            if not isinstance(values, list) or not values or not all(valid_id(x) for x in values):
                raise ValueError(f"recipe.{key} must contain stable identifiers")
        bounds = recipe.get("product_range")
        if (not isinstance(bounds, list) or len(bounds) != 2
                or not all(isinstance(x, int) and not isinstance(x, bool) for x in bounds)
                or bounds[0] < 1 or bounds[1] < bounds[0]):
            raise ValueError("recipe.product_range must be [positive minimum, maximum]")
        if recipe.get("status") != "OBSERVED_CANDIDATE":
            raise ValueError("this catalog accepts OBSERVED_CANDIDATE recipes only")
        primary = recipe.get("primary_source_ref")
        if primary is not None and (not valid_id(primary) or primary not in recipe["source_refs"]):
            raise ValueError("primary_source_ref must occur in source_refs")
        for key in ("hero_style", "card_layout"):
            if not isinstance(recipe.get(key), str) or not recipe[key]:
                raise ValueError(f"recipe.{key} must be a nonempty string")
        if not isinstance(recipe.get("tokens"), dict):
            raise ValueError("recipe.tokens must be an object")
        treatments = recipe.get("module_treatments", {})
        if not isinstance(treatments, dict):
            raise ValueError("recipe.module_treatments must be an object")
        clean_treatments = {}
        for module, treatment in treatments.items():
            if module not in recipe["modules"] or not isinstance(treatment, dict):
                raise ValueError("module_treatments must name existing recipe modules")
            if treatment.get("treatment") not in {"inherited", "adapted", "new"}:
                raise ValueError("module treatment must be inherited, adapted or new")
            refs = treatment.get("source_refs", [])
            if (not isinstance(refs, list) or not all(valid_id(ref) for ref in refs)
                    or not set(refs).issubset(recipe["source_refs"])):
                raise ValueError("module source_refs must be stable recipe source identifiers")
            if not isinstance(treatment.get("reason", ""), str):
                raise ValueError("module treatment reason must be a string")
            clean_treatments[module] = {"treatment": treatment["treatment"], "source_refs": refs,
                                        "reason": treatment.get("reason", "")}
        # Explicit allowlist prevents accidentally publishing raw sample payloads.
        clean_recipe = {key: value for key, value in recipe.items() if key in RECIPE_FIELDS}
        if "module_treatments" in clean_recipe:
            clean_recipe["module_treatments"] = clean_treatments
        result.append(clean_recipe)
    return result


def map_modules(recipe: dict, qualified_refs: list[str]) -> list[dict]:
    """Attribute individual modules only to evidence actually qualified for this run."""
    primary = recipe.get("primary_source_ref") or qualified_refs[0]
    configured = recipe.get("module_treatments", {})
    mappings = []
    for module in recipe["modules"]:
        treatment = configured.get(module)
        if treatment is None:
            footer = module in {"legal_footer", "footer"}
            treatment = {
                "treatment": "new" if footer else "adapted",
                "source_refs": [] if footer else [primary],
                "reason": ("Use the current approved footer and current unsubscribe configuration; no historical footer was verified."
                           if footer else "Adapt the observed module role and hierarchy to the current brief."),
            }
        requested = treatment["treatment"]
        required = treatment["source_refs"] if requested != "new" else []
        available = [ref for ref in required if ref in qualified_refs]
        missing = [ref for ref in required if ref not in qualified_refs]
        actual = requested
        reason = treatment["reason"]
        if requested != "new" and (missing or not available):
            actual = "adapted_with_evidence_gap" if available else "new"
            reason = ("Required module evidence is incomplete. Use only the listed qualified references; "
                      "the missing historical structure has not been verified." if available else
                      "No qualified source supports this module. Treat its layout as a new internal candidate.")
        mappings.append({
            "module": module,
            "inheritance": actual,
            "requested_treatment": requested,
            "source_reference_ids": available,
            "missing_reference_ids": missing,
            "reason": reason,
            "inherit": ("No historical module inheritance." if actual == "new" else
                        "Only the module structure supported by the listed qualified references; no historical commercial facts."),
            "adapt": ("Use the current approved footer and current destination settings." if module in {"legal_footer", "footer"} else
                      "Use current approved product assets and current brief copy; never carry over historical offers, dates or links."),
        })
    return mappings


def qualify_evidence(evidence: Any, evidence_base_dir: Path) -> tuple[dict, list, list]:
    if not isinstance(evidence, dict) or not isinstance(evidence.get("samples"), list):
        raise ValueError("evidence.samples must be an array")
    qualified: dict[str, dict] = {}
    rejected = []
    warnings = []
    identifiers: dict[str, int] = {}
    for sample in evidence["samples"]:
        if isinstance(sample, dict) and valid_id(sample.get("reference_id")):
            ref = sample["reference_id"]
            identifiers[ref] = identifiers.get(ref, 0) + 1
    seen_images: dict[str, str] = {}
    for index, sample in enumerate(evidence["samples"]):
        ref = sample.get("reference_id") if isinstance(sample, dict) else None
        # Bad IDs might contain addresses or Gmail URLs; do not echo them.
        safe_ref = ref if valid_id(ref) else f"INVALID-REFERENCE-{index + 1}"
        reasons = []
        if not isinstance(sample, dict) or not valid_id(ref):
            rejected.append({"reference_id": safe_ref, "reasons": ["INVALID_REFERENCE_ID"]})
            continue
        if identifiers[ref] > 1:
            reasons.append("DUPLICATE_REFERENCE_ID")
        if sample.get("delivery_status") not in LIVE_DELIVERIES:
            reasons.append("NOT_LIVE_MARKETING_SAMPLE")
        if sample.get("html_read") is not True:
            reasons.append("HTML_NOT_READ")
        if sample.get("visual_reviewed") is not True:
            reasons.append("VISUAL_NOT_REVIEWED")
        paths = sample.get("visual_files")
        images = []
        if not isinstance(paths, list) or not paths:
            reasons.append("NO_VISUAL_FILES")
        else:
            for raw in paths:
                if not isinstance(raw, str) or not raw or "://" in raw:
                    reasons.append("INVALID_VISUAL_FILE")
                    continue
                path = Path(raw)
                if not path.is_absolute():
                    path = evidence_base_dir / path
                info = image_evidence(path)
                if info is None:
                    reasons.append("MISSING_OR_INVALID_VISUAL_FILE")
                elif info["sha256"] not in {image["sha256"] for image in images}:
                    images.append(info)
        if reasons:
            rejected.append({"reference_id": safe_ref, "reasons": sorted(set(reasons))})
            continue
        # Exact screenshot reuse cannot masquerade as independent historical samples.
        duplicate_of = sorted({seen_images[x["sha256"]] for x in images
                               if x["sha256"] in seen_images})
        if duplicate_of:
            rejected.append({"reference_id": ref, "reasons": ["DUPLICATE_VISUAL_EVIDENCE"],
                             "duplicate_of": duplicate_of})
            continue
        qualified[ref] = {"reference_id": ref, "delivery_status": sample["delivery_status"],
                          "source_images": images}
        for info in images:
            seen_images[info["sha256"]] = ref
    return qualified, rejected, warnings


def make_plan(brief: Any, evidence: Any, catalog: Any,
              evidence_base_dir: Path | str = ".", input_hashes: dict | None = None) -> dict:
    """Return a privacy-minimized plan; no email body/headers/URLs are inherited."""
    plan: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "status": "INTERNAL_DRAFT",
        "planning_status": "INVALID_INPUT",
        "visual_inheritance": "NONE",
        "campaign_context": None,
        "selected_recipe": None,
        "selected_reference_ids": [],
        "top_matches": [],
        "rejected_references": [],
        "module_mapping": [],
        "input_hashes": input_hashes or {"brief_sha256": digest(brief),
                                         "evidence_sha256": digest(evidence),
                                         "catalog_sha256": digest(catalog)},
        "source_image_hashes": [],
        "blockers": [],
        "next_actions": [],
        "approval": "NOT_APPROVED",
        "performance_evidence": "NOT_ASSESSED",
        "match_score_meaning": "Structural fit only; not performance or approval.",
    }
    errors = validate_brief(brief)
    try:
        recipes = validated_recipes(catalog)
        qualified, rejected, warnings = qualify_evidence(evidence, Path(evidence_base_dir))
    except ValueError as error:
        errors.append(str(error))
        recipes, qualified, rejected, warnings = [], {}, [], []
    plan["rejected_references"] = rejected
    if errors:
        plan["blockers"] = [{"code": "INVALID_INPUT", "details": errors}]
        plan["next_actions"] = ["Correct the named input fields and rerun the planner."]
        return plan
    if brief["campaign_type"] not in CAMPAIGN_TYPES or brief.get("explicit_new_design"):
        plan["planning_status"] = "BLOCKED_RUNTIME_SCOPE"
        plan["blockers"] = [{"code": "NEW_DESIGN_REVIEW_REQUIRED" if brief.get("explicit_new_design")
                              else "UNSUPPORTED_CAMPAIGN_TYPE"}]
        plan["next_actions"] = ["Prepare a new-design brief for review; do not claim historical inheritance."]
        return plan
    for recipe in recipes:
        low, high = recipe["product_range"]
        fit = {
            "campaign_type": brief["campaign_type"] in recipe["campaign_types"],
            "stage": brief["stage"] in recipe["stages"],
            "channel": brief["channel"] in recipe["channels"],
            "product_count": low <= brief["product_count"] <= high,
        }
        refs = [ref for ref in recipe["source_refs"] if ref in qualified]
        primary = recipe.get("primary_source_ref")
        evidence_ok = bool(refs) and (primary is None or primary in refs)
        compatible = all(fit.values())
        match = {
            "recipe_id": recipe["id"], "compatible": compatible,
            "fit_score": sum(weight for key, weight in (("campaign_type", 30), ("stage", 30),
                                                        ("channel", 25), ("product_count", 15)) if fit[key]),
            "fit": fit, "qualified_reference_ids": refs,
            "missing_reference_ids": [ref for ref in recipe["source_refs"] if ref not in qualified],
            "primary_reference_qualified": primary is None or primary in refs,
            "evidence_qualified": evidence_ok, "eligible": compatible and evidence_ok,
            "product_range_span": high - low,
        }
        plan["top_matches"].append(match)
    ranking = lambda match: (match["eligible"], match["compatible"], match["fit_score"],
                             len(match["qualified_reference_ids"]), -match["product_range_span"])
    plan["top_matches"].sort(key=ranking, reverse=True)
    preferred = brief.get("preferred_recipe")
    selected = None
    if preferred:
        selected = next((x for x in plan["top_matches"] if x["recipe_id"] == preferred), None)
        if selected is None or not selected["compatible"]:
            plan["planning_status"] = "BLOCKED_RUNTIME_SCOPE"
            plan["blockers"] = [{"code": "PREFERRED_RECIPE_UNKNOWN_OR_INCOMPATIBLE"}]
            plan["next_actions"] = ["Review the requested recipe or correct its campaign scope; no fallback was selected."]
            return plan
        if not selected["evidence_qualified"]:
            selected = None
    else:
        eligible = [x for x in plan["top_matches"] if x["eligible"]]
        if eligible:
            if len(eligible) > 1 and ranking(eligible[0]) == ranking(eligible[1]):
                plan["planning_status"] = "BLOCKED_RUNTIME_SCOPE"
                plan["blockers"] = [{"code": "AMBIGUOUS_RECIPE_MATCH"}]
                plan["next_actions"] = ["Review equally fitting candidates and set preferred_recipe; no arbitrary fallback was selected."]
                return plan
            selected = eligible[0]
    if selected is None:
        compatible = [x for x in plan["top_matches"] if x["compatible"]]
        if not compatible:
            plan["planning_status"] = "BLOCKED_RUNTIME_SCOPE"
            plan["blockers"] = [{"code": "NO_COMPATIBLE_RECIPE"}]
            plan["next_actions"] = ["Prepare a scoped template candidate matching campaign, stage, channel and product count."]
        else:
            plan["planning_status"] = "BLOCKED_HISTORY_EVIDENCE"
            plan["blockers"] = [{"code": "NO_QUALIFIED_HISTORY_FOR_RECIPE"}]
            plan["next_actions"] = [
                "Read the actual marketing email HTML and inspect its locally saved image or screenshot.",
                "Record a live marketing delivery status, stable reference ID, html_read, visual_reviewed and existing visual_files.",
                "Include the recipe primary_source_ref when required; keep raw Gmail content outside the repository.",
            ]
        return plan
    recipe = next(recipe for recipe in recipes if recipe["id"] == selected["recipe_id"])
    refs = selected["qualified_reference_ids"]
    plan.update({
        "planning_status": "READY_FOR_INTERNAL_RENDER",
        "visual_inheritance": "EVIDENCE_BACKED_CANDIDATE",
        "campaign_context": {key: brief[key] for key in ("campaign_type", "stage", "channel", "product_count")},
        "selected_recipe": recipe,
        "selected_reference_ids": refs,
        "module_mapping": map_modules(recipe, refs),
        "source_image_hashes": [
            {"reference_id": ref, **info} for ref in refs for info in qualified[ref]["source_images"]
        ],
        "next_actions": ["Render an internal candidate using the selected recipe and current verified content.",
                         "Compare the rendered desktop/mobile visuals with the inspected source; retain human and ESP gates."],
    })
    return plan


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    command = subparsers.add_parser("plan", help="Select a compatible recipe backed by inspected historical emails")
    command.add_argument("--brief", required=True, type=Path)
    command.add_argument("--evidence", required=True, type=Path)
    command.add_argument("--out", required=True, type=Path)
    command.add_argument("--catalog", default=DEFAULT_CATALOG, type=Path)
    args = parser.parse_args(argv)
    payloads = {}
    hashes = {}
    file_errors = []
    for label in ("brief", "evidence", "catalog"):
        path = getattr(args, label)
        try:
            payloads[label] = json.loads(path.read_text(encoding="utf-8"))
            hashes[f"{label}_sha256"] = file_digest(path)
        except (OSError, ValueError, UnicodeError):
            payloads[label] = {"samples": []} if label == "evidence" else {}
            hashes[f"{label}_sha256"] = None
            file_errors.append(label)
    plan = make_plan(payloads["brief"], payloads["evidence"], payloads["catalog"],
                     evidence_base_dir=args.evidence.resolve().parent, input_hashes=hashes)
    if "evidence" in file_errors:
        plan["blockers"].append({"code": "EVIDENCE_FILE_UNAVAILABLE"})
    if any(label in file_errors for label in ("brief", "catalog")):
        plan["planning_status"] = "INVALID_INPUT"
        plan["blockers"].append({"code": "INPUT_FILE_UNAVAILABLE", "fields": [
            label for label in file_errors if label != "evidence"]})
    args.out.mkdir(parents=True, exist_ok=True)
    (args.out / "plan.json").write_text(json.dumps(plan, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": plan["status"], "planning_status": plan["planning_status"],
                      "selected_recipe_id": (plan["selected_recipe"] or {}).get("id")}, ensure_ascii=False))
    return 0 if plan["planning_status"] == "READY_FOR_INTERNAL_RENDER" else 2


if __name__ == "__main__":
    sys.exit(main())
