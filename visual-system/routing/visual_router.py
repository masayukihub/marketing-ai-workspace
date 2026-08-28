#!/usr/bin/env python3
"""Deterministic project-level Visual Pattern Router.

The Router selects reusable visual structure. It never approves Product Truth,
Claims, assets, final visual output, publication, or sending.
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml


ROOT = Path(__file__).resolve().parents[2]
SYSTEM_ROOT = ROOT / "visual-system"
REGISTRY_FILE = SYSTEM_ROOT / "registry/pattern-registry.yaml"
WEIGHTS_FILE = SYSTEM_ROOT / "routing/weights.yaml"
ADAPTERS_FILE = SYSTEM_ROOT / "routing/channel-adapters.yaml"
RECIPE_REGISTRY_FILE = SYSTEM_ROOT / "registry/page-recipe-registry.yaml"
EDM_TEMPLATE_REGISTRY_FILE = ROOT / "skills/edm-generator/design_system/templates_v1.0.yaml"
EDM_MODULE_REGISTRY_FILE = ROOT / "skills/edm-generator/design_system/modules_v1.0.yaml"
WINDOWS_ABSOLUTE_PATH = re.compile(r"^[A-Za-z]:[\\/]")


class NoAliasSafeDumper(yaml.SafeDumper):
    """Keep generated profiles readable and diff-friendly."""

    def ignore_aliases(self, data: Any) -> bool:
        return True


def load_yaml(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise FileNotFoundError(path)
    value = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"Expected YAML object: {path}")
    return value


def normalize(value: Any) -> str:
    return str(value or "").strip().lower().replace("-", "_").replace(" ", "_")


def values(items: Any) -> list[str]:
    if items is None:
        return []
    if not isinstance(items, list):
        items = [items]
    result = []
    for item in items:
        if isinstance(item, dict):
            item = item.get("id") or item.get("value") or item.get("name")
        if item:
            result.append(normalize(item))
    return result


def is_local_absolute_path(value: Any) -> bool:
    if not isinstance(value, str) or not value:
        return False
    if value.startswith(("http://", "https://", "skill://")):
        return False
    return Path(value).is_absolute() or bool(WINDOWS_ABSOLUTE_PATH.match(value)) or value.startswith("\\\\")


def repository_relative_path(value: str) -> str | None:
    if WINDOWS_ABSOLUTE_PATH.match(value) or value.startswith("\\\\"):
        return None
    try:
        return str(Path(value).resolve().relative_to(ROOT.resolve()))
    except ValueError:
        return None


def external_source_reference(value: str) -> dict[str, str]:
    fingerprint = hashlib.sha256(value.encode("utf-8")).hexdigest()[:12].upper()
    return {
        "source_id": f"EXTERNAL-LOCAL-{fingerprint}",
        "source_type": "external_local_artifact",
        "locator_status": "REDACTED_LOCAL_PATH",
        "availability": "LOCAL_ONLY",
    }


def normalize_source_reference(source: Any) -> Any:
    """Keep repository locators portable and redact external machine paths."""
    if isinstance(source, str):
        if not is_local_absolute_path(source):
            return source
        relative = repository_relative_path(source)
        return relative if relative is not None else external_source_reference(source)
    if isinstance(source, list):
        return [normalize_source_reference(item) for item in source]
    if not isinstance(source, dict):
        return source

    normalized: dict[str, Any] = {}
    redacted_values: list[str] = []
    for key, value in source.items():
        if isinstance(value, str) and is_local_absolute_path(value):
            relative = repository_relative_path(value)
            if relative is not None:
                normalized[key] = relative
            else:
                redacted_values.append(value)
            continue
        normalized[key] = normalize_source_reference(value)
    if redacted_values:
        fingerprint = hashlib.sha256("\n".join(sorted(redacted_values)).encode("utf-8")).hexdigest()[:12].upper()
        normalized.setdefault("source_id", f"EXTERNAL-LOCAL-{fingerprint}")
        normalized.setdefault("source_type", "external_local_artifact")
        normalized["locator_status"] = "REDACTED_LOCAL_PATH"
        normalized.setdefault("availability", "LOCAL_ONLY")
    return normalized


def normalize_source_references(sources: list[Any]) -> list[Any]:
    normalized = []
    seen = set()
    for source in sources:
        item = normalize_source_reference(source)
        key = json.dumps(item, ensure_ascii=False, sort_keys=True) if not isinstance(item, str) else item
        if key in seen:
            continue
        seen.add(key)
        normalized.append(item)
    return normalized


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def decision_record_content_hash(record: dict[str, Any]) -> str:
    """Hash a Decision Record without its self-declared content hash."""
    canonical = copy.deepcopy(record)
    integrity = canonical.get("integrity")
    if isinstance(integrity, dict):
        integrity.pop("decision_record_content_sha256", None)
    payload = json.dumps(canonical, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def load_project_planning_decision(project_dir: Path) -> tuple[dict[str, Any] | None, list[str], str | None]:
    """Load and verify an accepted project-level visual planning decision."""
    manifest_file = project_dir / "project.yaml"
    if not manifest_file.is_file():
        return None, ["No project manifest visual planning decision"], None
    manifest = load_yaml(manifest_file)
    pointer = (manifest.get("sources") or {}).get("visual_planning_decision")
    if not isinstance(pointer, str) or not pointer.strip():
        return None, ["No accepted Project Visual Planning Decision"], None
    raw = Path(pointer)
    if raw.is_absolute() or WINDOWS_ABSOLUTE_PATH.match(pointer) or pointer.startswith("\\\\"):
        return None, ["Visual planning decision pointer must be repository-relative"], None
    record_file = (project_dir / raw).resolve()
    try:
        record_source = record_file.relative_to(ROOT.resolve()).as_posix()
    except ValueError:
        return None, ["Visual planning decision pointer escapes repository"], None
    if not record_file.is_file():
        return None, ["Visual planning decision record is missing"], record_source
    record = load_yaml(record_file)
    lock = record.get("project_planning_lock") or {}
    reasons = []
    if record.get("contract") != "visual-pattern-recipe-decision-record":
        reasons.append("Invalid visual planning decision contract")
    if record.get("project_id") != manifest.get("project_id"):
        reasons.append("Visual planning decision project mismatch")
    if str(record.get("record_status") or "").upper() != "ACCEPTED":
        reasons.append("Visual planning decision is not ACCEPTED")
    if str(lock.get("status") or "").upper() != "ACTIVE":
        reasons.append("Project Visual Planning Lock is not ACTIVE")
    integrity = record.get("integrity") or {}
    expected_record_hash = integrity.get("decision_record_content_sha256")
    if expected_record_hash != decision_record_content_hash(record):
        reasons.append("Decision Record content hash mismatch")
    template_pointer = (record.get("source") or {}).get("decision_template")
    if not isinstance(template_pointer, str) or Path(template_pointer).is_absolute():
        reasons.append("Decision template pointer is not repository-relative")
    else:
        template_file = (ROOT / template_pointer).resolve()
        try:
            template_file.relative_to(ROOT.resolve())
        except ValueError:
            reasons.append("Decision template pointer escapes repository")
        else:
            if not template_file.is_file():
                reasons.append("Decision template is missing")
            elif integrity.get("decision_template_sha256") != sha256_file(template_file):
                reasons.append("Decision template hash mismatch")
    return (None if reasons else record), reasons, record_source


def project_planning_lock_decision(
    context: dict[str, Any],
    record: dict[str, Any] | None,
    patterns_by_id: dict[str, dict[str, Any]],
    assignments: dict[str, dict[str, Any]],
    approved_freeze_inherited: bool,
    load_reasons: list[str] | None = None,
) -> dict[str, Any]:
    """Resolve Planning Lock applicability without changing production gates."""
    if not record:
        return {
            "status": "NOT_APPLIED",
            "applied": False,
            "project_visual_direction_status": "ROUTER_GENERATED_CANDIDATE",
            "reask_visual_direction": True,
            "reopen_reasons": list(load_reasons or []),
            "precedence": "VISUAL_ROUTER",
        }
    lock = record.get("project_planning_lock") or {}
    if approved_freeze_inherited:
        return {
            "status": "SUPERSEDED_BY_APPROVED_FREEZE",
            "applied": False,
            "project_visual_direction_status": "HUMAN_APPROVED_FINAL_FREEZE",
            "reask_visual_direction": False,
            "reopen_reasons": [],
            "precedence": "APPROVED_VISUAL_FREEZE",
            "review_id": record.get("review_id"),
        }

    reopen_reasons = []
    visual_inputs = context.get("visual_inputs") or {}
    governance = context.get("governance") or {}
    if visual_inputs.get("exploration_requested") is True:
        reopen_reasons.append("USER_EXPLICITLY_REQUESTS_VISUAL_CHANGE")
    approved_channels = set(values(lock.get("approved_channels")))
    requested_channels = set(values([context.get("primary_channel"), *(context.get("channels") or [])]))
    if approved_channels and requested_channels - approved_channels:
        reopen_reasons.append("CHANNEL_HARD_CONFLICT")
    if visual_inputs.get("channel_hard_conflict") is True:
        reopen_reasons.append("CHANNEL_HARD_CONFLICT")
    if governance.get("approved_project_direction_conflict") is True:
        reopen_reasons.append("APPROVED_PROJECT_DIRECTION_CONFLICT")
    for pattern_id in lock.get("reviewed_pattern_ids", []):
        pattern = patterns_by_id.get(pattern_id)
        if pattern and pattern.get("lifecycle", {}).get("status") == "DEPRECATED":
            reopen_reasons.append("SELECTED_PATTERN_DEPRECATED")
    for channel, assignment in assignments.items():
        if channel != "edm":
            continue
        recipe = assignment.get("recipe") or {}
        compatibility = recipe.get("template_compatibility") or {}
        if (
            recipe.get("selection_status") in {"EDM_INTENT_NOT_RESOLVED", "NO_COMPATIBLE_EDM_RECIPE"}
            or not compatibility.get("recommended_template_registered", False)
            or not compatibility.get("required_roles_resolved", False)
            or not compatibility.get("required_modules_satisfied", False)
            or not compatibility.get("additional_modules_are_optional_or_conditional", False)
        ):
            reopen_reasons.append("NO_COMPATIBLE_TEMPLATE")
    reopen_reasons = list(dict.fromkeys(reopen_reasons))
    if reopen_reasons:
        return {
            "status": "REOPEN_REQUIRED",
            "applied": False,
            "project_visual_direction_status": "HUMAN_REVIEW_REQUIRED",
            "reask_visual_direction": True,
            "reopen_reasons": reopen_reasons,
            "precedence": "PROJECT_PLANNING_DECISION",
            "review_id": record.get("review_id"),
        }
    return {
        "status": "ACTIVE",
        "applied": True,
        "project_visual_direction_status": lock.get(
            "project_visual_direction_status", "HUMAN_APPROVED_FOR_PROJECT_PLANNING"
        ),
        "reask_visual_direction": False,
        "reopen_reasons": [],
        "precedence": "PROJECT_PLANNING_DECISION",
        "review_id": record.get("review_id"),
        "approved_scope": copy.deepcopy(lock.get("approved_scope", [])),
        "does_not_approve": copy.deepcopy(lock.get("does_not_approve", [])),
    }


def resolve_project(value: str) -> Path:
    candidate = Path(value)
    if candidate.is_absolute() and candidate.is_dir():
        return candidate
    relative = (Path.cwd() / candidate).resolve()
    if relative.is_dir():
        return relative
    project = ROOT / "projects" / value
    if project.is_dir():
        return project
    raise FileNotFoundError(f"Project not found: {value}")


def load_patterns() -> list[dict[str, Any]]:
    registry = load_yaml(REGISTRY_FILE)
    patterns = []
    for entry in registry.get("patterns", []):
        path = (REGISTRY_FILE.parent / entry["file"]).resolve()
        pattern = load_yaml(path)
        if pattern.get("pattern_id") != entry.get("pattern_id"):
            raise ValueError(f"Registry id mismatch: {path}")
        if pattern.get("lifecycle", {}).get("status") != entry.get("status"):
            raise ValueError(f"Registry status mismatch: {path}")
        pattern["_file"] = str(path.relative_to(ROOT))
        patterns.append(pattern)
    return patterns


def load_page_recipes() -> dict[str, dict[str, Any]]:
    registry = load_yaml(RECIPE_REGISTRY_FILE)
    recipes = {}
    for entry in registry.get("recipes", []):
        path = (RECIPE_REGISTRY_FILE.parent / entry["file"]).resolve()
        recipe = load_yaml(path)
        if recipe.get("recipe_id") != entry.get("recipe_id"):
            raise ValueError(f"Recipe registry id mismatch: {path}")
        if recipe.get("lifecycle", {}).get("status") != entry.get("status"):
            raise ValueError(f"Recipe registry status mismatch: {path}")
        recipe["_file"] = str(path.relative_to(ROOT))
        recipes[recipe["recipe_id"]] = recipe
    return recipes


def overlap_score(target: list[str], supported: list[str], missing_score: float) -> float:
    if not target:
        return missing_score
    target_set = set(target)
    supported_set = set(supported)
    if "all" in supported_set:
        return 80.0
    overlap = target_set & supported_set
    return round(100.0 * len(overlap) / len(target_set), 1)


PATTERN_ASSET_FIT_SCORES = {
    "available": 100.0,
    "approved": 100.0,
    "partial": 60.0,
    "available_review_only": 60.0,
    "candidate": 40.0,
    "unknown": 0.0,
    "unverified": 0.0,
    "missing": 0.0,
    "missing_or_unverified": 0.0,
    "not_available": 0.0,
}


def asset_evaluation(context: dict[str, Any], pattern: dict[str, Any]) -> tuple[float, list[dict[str, str]]]:
    assets = context.get("visual_inputs", {}).get("assets", {})
    required = pattern.get("asset_requirements", {}).get("required", [])
    if not required:
        return 100.0, []
    scores = []
    gaps = []
    for asset_key in required:
        raw = assets.get(asset_key, "MISSING_OR_UNVERIFIED")
        if isinstance(raw, dict):
            raw = raw.get("status", "MISSING_OR_UNVERIFIED")
        status = normalize(raw)
        score = PATTERN_ASSET_FIT_SCORES.get(status, 0.0)
        scores.append(score)
        if score < 100:
            gaps.append({"asset": asset_key, "status": str(raw)})
    return round(sum(scores) / len(scores), 1), gaps


def score_pattern(
    context: dict[str, Any],
    pattern: dict[str, Any],
    weights: dict[str, float],
    missing_score: float,
) -> dict[str, Any]:
    fit = pattern.get("fit", {})
    channel = normalize(context.get("primary_channel"))
    supported_channels = values(fit.get("channels"))
    if pattern.get("lifecycle", {}).get("status") == "DEPRECATED":
        return {"excluded": True, "reason": "Pattern is DEPRECATED"}
    if channel not in supported_channels and "all" not in supported_channels:
        return {"excluded": True, "reason": f"Unsupported channel: {channel}"}

    visual_inputs = context.get("visual_inputs", {})
    category_tags = values([context.get("product", {}).get("category"), *visual_inputs.get("category_tags", [])])
    consumer_goals = values(visual_inputs.get("consumer_goals"))
    complexity = normalize(visual_inputs.get("information_complexity"))
    supported_complexity = values(fit.get("information_complexity"))
    asset_score, asset_gaps = asset_evaluation(context, pattern)
    historical = pattern.get("historical_performance", {})

    dimensions = {
        "channel_fit": 100.0,
        "category_fit": overlap_score(category_tags, values(fit.get("categories")), missing_score),
        "consumer_goal_fit": overlap_score(consumer_goals, values(fit.get("consumer_goals")), missing_score),
        "brand_fit": float(fit.get("brand_fit", missing_score)),
        "information_complexity": 100.0 if complexity and complexity in supported_complexity else missing_score if not complexity else 0.0,
        "asset_availability": asset_score,
        "mobile_fit": float(fit.get("mobile_fit", missing_score)),
        "historical_performance": float(historical.get("score", missing_score)),
    }
    total_weight = sum(float(weight) for weight in weights.values())
    weighted = sum(dimensions[key] * float(weight) for key, weight in weights.items()) / total_weight
    return {
        "excluded": False,
        "pattern_id": pattern["pattern_id"],
        "name": pattern["name"],
        "lifecycle": pattern.get("lifecycle", {}).get("status"),
        "score": round(weighted, 1),
        "dimensions": dimensions,
        "asset_requirements": copy.deepcopy(pattern.get("asset_requirements", {})),
        "required_asset_gaps": asset_gaps,
        "historical_performance_status": historical.get("status", "UNKNOWN"),
        "sources": [pattern["_file"], *pattern.get("sources", [])],
    }


def freeze_applicability(
    channel: str, freeze: dict[str, Any] | None, patterns_by_id: dict[str, dict[str, Any]]
) -> dict[str, Any]:
    if not freeze:
        return {"status": "NOT_AVAILABLE", "applicable": False, "reason_codes": ["NO_VISUAL_FREEZE"]}
    normalized_channel = normalize(channel)
    pattern = patterns_by_id.get(freeze.get("pattern_id"))
    reason_codes = []
    if normalized_channel not in values(freeze.get("channel_scope")):
        reason_codes.append("FREEZE_CHANNEL_SCOPE_EXCLUDES_CHANNEL")
    if pattern:
        supported_channels = values(pattern.get("fit", {}).get("channels"))
        if normalized_channel not in supported_channels and "all" not in supported_channels:
            reason_codes.append("FREEZE_PATTERN_CHANNEL_INCOMPATIBLE")
    if reason_codes:
        return {
            "status": "NOT_APPLICABLE_TO_CHANNEL",
            "applicable": False,
            "reason_codes": reason_codes,
        }
    return {"status": "APPLICABLE_TO_CHANNEL", "applicable": True, "reason_codes": []}


def approved_freeze_decision(
    context: dict[str, Any], freeze: dict[str, Any] | None, patterns_by_id: dict[str, dict[str, Any]]
) -> tuple[bool, list[str]]:
    if not freeze:
        return False, ["No visual-freeze.yaml"]
    channel = normalize(context.get("primary_channel"))
    applicability = freeze_applicability(channel, freeze, patterns_by_id)
    if not applicability["applicable"]:
        reasons = []
        if "FREEZE_PATTERN_CHANNEL_INCOMPATIBLE" in applicability["reason_codes"]:
            reasons.append("Current channel is not supported by Freeze Pattern")
        if "FREEZE_CHANNEL_SCOPE_EXCLUDES_CHANNEL" in applicability["reason_codes"]:
            reasons.append("Current channel conflicts with Freeze scope")
        return False, reasons
    reasons = []
    if freeze.get("status") != "APPROVED" or freeze.get("active") is not True:
        reasons.append("Freeze is not active APPROVED")
    approval = freeze.get("human_approval", {})
    if not approval.get("approved_by") or not approval.get("approved_at"):
        reasons.append("Freeze lacks named human approval metadata")
    pattern = patterns_by_id.get(freeze.get("pattern_id"))
    if not pattern:
        reasons.append("Freeze Pattern is not registered")
    elif pattern.get("lifecycle", {}).get("status") == "DEPRECATED":
        reasons.append("Freeze Pattern is DEPRECATED")
    if context.get("visual_inputs", {}).get("exploration_requested") is True:
        reasons.append("User requested visual exploration")
    if pattern:
        _, gaps = asset_evaluation(context, pattern)
        if gaps:
            reasons.append("Required assets no longer satisfy Freeze")
    return not reasons, reasons


def selection_reasons(top: dict[str, Any]) -> list[str]:
    dimensions = top["dimensions"]
    labels = {
        "channel_fit": "Channel Fit",
        "category_fit": "Category Fit",
        "consumer_goal_fit": "Consumer Goal Fit",
        "brand_fit": "Brand Fit",
        "information_complexity": "Information Complexity",
        "asset_availability": "Asset Availability",
        "mobile_fit": "Mobile Fit",
        "historical_performance": "Historical Performance",
    }
    ranked = sorted(dimensions.items(), key=lambda item: (-item[1], item[0]))
    return [f"{labels[key]}={value:.1f}" for key, value in ranked[:4]]


MATCH_DIMENSIONS = (
    "channel_fit",
    "category_fit",
    "consumer_goal_fit",
    "brand_fit",
    "information_complexity",
    "mobile_fit",
)


PRODUCT_TRUTH_SCORES = {
    "approved": 100.0,
    "verified_for_channel": 100.0,
    "not_required": 100.0,
    "verified": 80.0,
    "available": 60.0,
    "partial": 50.0,
    "pending_verification": 20.0,
    "unapproved_or_unverified": 0.0,
    "missing_or_unverified": 0.0,
    "unknown": 0.0,
    "not_available": 0.0,
}


CLAIM_GATE_SCORES = {
    "approved": 100.0,
    "verified_for_channel": 100.0,
    "not_required": 100.0,
    "verified": 80.0,
    "conditional": 60.0,
    "available": 40.0,
    "partial": 30.0,
    "pending_verification": 20.0,
    "unapproved_or_unverified": 0.0,
    "missing_or_unverified": 0.0,
    "unknown": 0.0,
    "not_available": 0.0,
}


ASSET_READINESS_SCORES = {
    "approved": 100.0,
    "verified_for_channel": 100.0,
    "not_required": 100.0,
    "verified": 80.0,
    "available": 80.0,
    "partial": 60.0,
    "available_review_only": 60.0,
    "candidate": 40.0,
    "pending_verification": 20.0,
    "unapproved_or_unverified": 0.0,
    "missing_or_unverified": 0.0,
    "unknown": 0.0,
    "missing": 0.0,
    "not_available": 0.0,
}


def governance_score(value: Any, scores: dict[str, float]) -> float:
    return scores.get(normalize(value), 0.0)


def freeze_is_active_approved(freeze: dict[str, Any] | None) -> bool:
    if not freeze or freeze.get("status") != "APPROVED" or freeze.get("active") is not True:
        return False
    approval = freeze.get("human_approval", {})
    return bool(approval.get("approved_by") and approval.get("approved_at"))


def metric_status(score: float) -> str:
    if score >= 75:
        return "HIGH"
    if score >= 55:
        return "MEDIUM"
    return "LOW"


def context_for_channel(context: dict[str, Any], channel: str) -> dict[str, Any]:
    routed = copy.deepcopy(context)
    routed["primary_channel"] = channel
    channel_context = copy.deepcopy(context.get("channel_contexts", {}).get(channel))
    if isinstance(channel_context, dict):
        routed["resolved_channel_context"] = channel_context
        if channel_context.get("consumer_goals") is not None:
            routed.setdefault("visual_inputs", {})["consumer_goals"] = copy.deepcopy(
                channel_context.get("consumer_goals")
            )
    return routed


def channel_intent(context: dict[str, Any], channel: str) -> dict[str, Any]:
    raw = context.get("channel_contexts", {}).get(channel)
    if not isinstance(raw, dict):
        return {
            "status": "UNRESOLVED" if channel == "edm" else "PROJECT_CONTEXT_DEFAULT",
            "resolved": channel != "edm",
            "campaign_type": None,
            "primary_objective": None,
            "consumer_goals": values(context.get("visual_inputs", {}).get("consumer_goals")),
        }
    campaign_type = normalize(raw.get("campaign_type")) or None
    primary_objective = normalize(raw.get("primary_objective")) or None
    status = normalize(raw.get("status")) or "unknown"
    resolved = bool(campaign_type and primary_objective and status not in {"unknown", "unresolved", "not_available"})
    return {
        "status": str(raw.get("status") or "UNKNOWN"),
        "resolved": resolved,
        "campaign_type": campaign_type,
        "primary_objective": primary_objective,
        "consumer_goals": values(raw.get("consumer_goals")),
    }


def rank_patterns(
    context: dict[str, Any],
    patterns: list[dict[str, Any]],
    weights: dict[str, float],
    missing_score: float,
) -> tuple[list[dict[str, Any]], list[dict[str, str]]]:
    ranked = []
    excluded = []
    for pattern in patterns:
        score = score_pattern(context, pattern, weights, missing_score)
        if score["excluded"]:
            excluded.append({"pattern_id": pattern["pattern_id"], "reason": score["reason"]})
        else:
            ranked.append(score)
    ranked.sort(key=lambda item: (-item["score"], item["pattern_id"]))
    for index, item in enumerate(ranked, 1):
        item["rank"] = index
    return ranked, excluded


def pattern_match_metric(top: dict[str, Any], weights: dict[str, float]) -> dict[str, Any]:
    match_weight = sum(weights[key] for key in MATCH_DIMENSIONS)
    score = round(sum(top["dimensions"][key] * weights[key] for key in MATCH_DIMENSIONS) / match_weight, 1)
    return {
        "score": score,
        "status": metric_status(score),
        "dimensions": {key: top["dimensions"][key] for key in MATCH_DIMENSIONS},
        "note": "Pattern Match excludes execution assets and is not a production decision.",
    }


def project_visual_dna(context: dict[str, Any]) -> dict[str, Any]:
    visual_inputs = context.get("visual_inputs", {})
    principles = values(visual_inputs.get("visual_direction", {}).get("principles"))
    tone = [item for item in principles if item in {"clean", "friendly", "modern", "japan_consumer_friendly", "trust_first"}]
    if not tone:
        tone = ["clean"]
    proof_strategy = "proof_before_persuasion" if "proof_before_persuasion" in principles else "evidence_before_conversion"
    if "product_first" in principles and "mechanism_visible" in principles:
        rhythm = "product_first_to_mechanism_to_proof"
    elif "trust_first" in principles:
        rhythm = "trust_context_to_evidence_to_action"
    else:
        rhythm = "context_to_evidence_to_action"
    complexity = normalize(visual_inputs.get("information_complexity")) or "unknown"
    return {
        "status": "ROUTER_GENERATED_CANDIDATE",
        "tone": tone,
        "proof_strategy": proof_strategy,
        "visual_rhythm": rhythm,
        "image_strategy": "official_product_and_approved_evidence_only",
        "information_strategy": {
            "source_complexity": complexity,
            "hierarchy_principle": "structured_progressive_disclosure",
        },
        "conversion_style": "single_verified_action_after_proof",
        "mobile_priority": normalize(visual_inputs.get("mobile_priority")) or "unknown",
        "content_boundary": [
            "No Product Truth, Claim, price, performance number, specification, or asset is approved by Visual DNA.",
            "Cross-channel inheritance excludes complete layout and channel-native module geometry.",
        ],
    }


def channel_information_density(context: dict[str, Any], channel: str) -> str:
    complexity = normalize(context.get("visual_inputs", {}).get("information_complexity")) or "unknown"
    if channel == "edm":
        return "medium_selective"
    if channel == "amazon_jp":
        return f"{complexity}_structured"
    return "channel_adapted"


def asset_readiness_evaluation(context: dict[str, Any], pattern: dict[str, Any]) -> tuple[float, list[dict[str, str]]]:
    assets = context.get("visual_inputs", {}).get("assets", {})
    required = pattern.get("asset_requirements", {}).get("required", [])
    if not required:
        return 100.0, []
    scores = []
    gaps = []
    for asset_key in required:
        raw = assets.get(asset_key, "MISSING_OR_UNVERIFIED")
        if isinstance(raw, dict):
            raw = raw.get("status", "MISSING_OR_UNVERIFIED")
        score = governance_score(raw, ASSET_READINESS_SCORES)
        scores.append(score)
        if score < 100:
            gaps.append({"asset": asset_key, "status": str(raw)})
    return round(sum(scores) / len(scores), 1), gaps


def execution_readiness(
    context: dict[str, Any],
    top: dict[str, Any],
    freeze: dict[str, Any] | None,
    recipe: dict[str, Any] | None,
    freeze_applicable: bool = True,
) -> tuple[dict[str, Any], list[str], list[str]]:
    governance = context.get("governance", {})
    truth_status = governance.get("product_truth_status") or context.get("product", {}).get("product_truth_status")
    claim_status = governance.get("claim_status", "UNAPPROVED_OR_UNVERIFIED")
    truth_score = governance_score(truth_status, PRODUCT_TRUTH_SCORES)
    claim_score = governance_score(claim_status, CLAIM_GATE_SCORES)
    asset_score, _ = asset_readiness_evaluation(context, top)
    pattern_score = 100.0 if top.get("lifecycle") == "VALIDATED" else 50.0
    review_clear = (
        truth_score == 100
        and claim_score == 100
        and asset_score == 100
        and pattern_score == 100
        and governance.get("human_review_status") in {"APPROVED", "NOT_REQUIRED"}
        and not (freeze_applicable and freeze and not freeze_is_active_approved(freeze))
        and not (recipe and recipe.get("lifecycle", {}).get("status") == "CANDIDATE")
    )
    human_score = 100.0 if review_clear else 0.0
    score = round(
        truth_score * 0.25 + claim_score * 0.20 + asset_score * 0.35 + pattern_score * 0.10 + human_score * 0.10,
        1,
    )
    blockers = []
    reason_codes = []
    if truth_score < 100:
        blockers.append(f"Product Truth is {truth_status or 'UNKNOWN'}")
        reason_codes.append("PRODUCT_TRUTH_NOT_APPROVED")
    if claim_score < 100:
        blockers.append(f"Claim Gate is {claim_status}")
        reason_codes.append("CLAIM_GATE_NOT_APPROVED")
    if asset_score < 100:
        blockers.append("Required assets are missing, partial, or review-only")
        reason_codes.append("ASSET_READINESS_BELOW_REQUIRED")
    if top.get("lifecycle") == "CANDIDATE":
        blockers.append("Primary Pattern is CANDIDATE")
        reason_codes.append("PATTERN_CANDIDATE_REQUIRES_REVIEW")
    if recipe and recipe.get("lifecycle", {}).get("status") == "CANDIDATE":
        blockers.append("Page Recipe is CANDIDATE")
        reason_codes.append("RECIPE_CANDIDATE_REQUIRES_REVIEW")
    if freeze_applicable and freeze and not freeze_is_active_approved(freeze):
        blockers.append("Candidate Freeze is not an active APPROVED Freeze")
        reason_codes.append("CANDIDATE_FREEZE_NOT_APPLIED")
    if governance.get("human_review_status") == "REQUIRED":
        reason_codes.append("HUMAN_REVIEW_REQUIRED")
    if asset_score < 100:
        status = "BLOCKED_BY_ASSET"
    elif blockers or not review_clear:
        status = "HUMAN_REVIEW_REQUIRED"
    else:
        status = "READY_FOR_PRODUCTION"
    metric = {
        "score": score,
        "status": status,
        "components": {
            "product_truth": {"status": truth_status or "UNKNOWN", "score": truth_score},
            "claim_gate": {"status": claim_status, "score": claim_score},
            "required_assets": {"status": "READY" if asset_score == 100 else "INCOMPLETE", "score": asset_score},
            "pattern_lifecycle": {"status": top.get("lifecycle"), "score": pattern_score},
            "human_review": {"status": governance.get("human_review_status", "REQUIRED"), "score": human_score},
        },
        "note": "Execution Readiness is evaluated independently from Pattern Match.",
    }
    return metric, list(dict.fromkeys(blockers)), list(dict.fromkeys(reason_codes))


def evidence_confidence_metric(readiness: dict[str, Any]) -> dict[str, Any]:
    components = readiness["components"]
    score = round(
        components["product_truth"]["score"] * 0.35
        + components["claim_gate"]["score"] * 0.25
        + components["required_assets"]["score"] * 0.25
        + components["pattern_lifecycle"]["score"] * 0.15,
        1,
    )
    return {
        "score": score,
        "status": metric_status(score),
        "note": "Confidence reflects governed evidence availability, not predicted conversion performance.",
    }


def freeze_reason_codes(applicability: dict[str, Any], freeze: dict[str, Any] | None) -> list[str]:
    codes = list(applicability.get("reason_codes", []))
    if applicability.get("applicable") and freeze and (
        freeze.get("status") != "APPROVED" or freeze.get("active") is not True
    ):
        codes.append("CANDIDATE_FREEZE_NOT_APPLIED")
    return list(dict.fromkeys(codes))


def select_recipe_for_channel(
    channel: str,
    intent: dict[str, Any],
    adapter: dict[str, Any],
    recipes: dict[str, dict[str, Any]],
) -> tuple[dict[str, Any] | None, str]:
    if channel != "edm":
        recipe_id = adapter.get("recipe", {}).get("recipe_id")
        return recipes.get(recipe_id), "EXISTING_RUNTIME"
    if not intent.get("resolved"):
        return None, "EDM_INTENT_NOT_RESOLVED"
    matches = []
    for recipe in recipes.values():
        if channel not in values(recipe.get("channels")):
            continue
        request = recipe.get("template_selection_request", {})
        if normalize(request.get("campaign_type")) != normalize(intent.get("campaign_type")):
            continue
        if normalize(request.get("primary_objective")) != normalize(intent.get("primary_objective")):
            continue
        matches.append(recipe)
    if not matches:
        return None, "NO_COMPATIBLE_EDM_RECIPE"
    matches.sort(key=lambda item: item["recipe_id"])
    return matches[0], "ROUTER_CANDIDATE_MATCH"


def recipe_template_compatibility(recipe: dict[str, Any] | None) -> dict[str, Any] | None:
    if not recipe:
        return None
    request = recipe.get("template_selection_request", {})
    compatibility = recipe.get("template_compatibility", {})
    recommended_template = compatibility.get("recommended_template")
    templates = {
        item["template_id"]: item for item in load_yaml(EDM_TEMPLATE_REGISTRY_FILE).get("templates", [])
    }
    registered_modules = {
        item["module_id"] for item in load_yaml(EDM_MODULE_REGISTRY_FILE).get("modules", [])
    }
    required_roles = request.get("required_roles", [])
    optional_roles = request.get("optional_roles", [])
    required_role_modules = [role.get("module_id") for role in required_roles if role.get("module_id")]
    optional_role_modules = [role.get("module_id") for role in optional_roles if role.get("module_id")]
    all_role_modules = required_role_modules + optional_role_modules
    missing_registered_modules = sorted(set(all_role_modules) - registered_modules)
    template = templates.get(recommended_template)
    template_required_modules = template.get("required_modules", []) if template else []
    missing_template_required_modules = sorted(set(template_required_modules) - set(required_role_modules))
    additional_recipe_modules = sorted(set(all_role_modules) - set(template_required_modules))
    optional_or_conditional_modules = {
        role.get("module_id")
        for role in optional_roles
        if role.get("requirement") in {"OPTIONAL", "CONDITIONAL"}
    }
    unclassified_additional_modules = sorted(
        module for module in additional_recipe_modules if module not in optional_or_conditional_modules
    )
    return {
        "recommended_template": recommended_template,
        "mapping_status": compatibility.get("mapping_status", "CANDIDATE_CONDITIONAL_MATCH"),
        "stable_selector_override_allowed": False,
        "selector_owner": compatibility.get("selector_owner", "skills/edm-generator"),
        "recommended_template_registered": template is not None,
        "required_roles_resolved": not missing_registered_modules,
        "required_modules_satisfied": not missing_template_required_modules,
        "additional_modules_are_optional_or_conditional": not unclassified_additional_modules,
        "missing_registered_modules": missing_registered_modules,
        "missing_template_required_modules": missing_template_required_modules,
        "unclassified_additional_modules": unclassified_additional_modules,
        "registry_sources": [
            str(EDM_TEMPLATE_REGISTRY_FILE.relative_to(ROOT)),
            str(EDM_MODULE_REGISTRY_FILE.relative_to(ROOT)),
        ],
    }


def channel_assignment(
    context: dict[str, Any],
    channel: str,
    patterns: list[dict[str, Any]],
    patterns_by_id: dict[str, dict[str, Any]],
    weights: dict[str, float],
    missing_score: float,
    adapters: dict[str, Any],
    recipes: dict[str, dict[str, Any]],
    freeze: dict[str, Any] | None,
) -> tuple[dict[str, Any], list[dict[str, Any]], list[dict[str, str]]]:
    routed_context = context_for_channel(context, channel)
    ranked, excluded = rank_patterns(routed_context, patterns, weights, missing_score)
    if not ranked:
        raise ValueError(f"No eligible Pattern for channel: {channel}")
    top = ranked[0]
    adapter = adapters.get(channel)
    if not adapter:
        raise ValueError(f"No channel adapter: {channel}")
    intent = channel_intent(context, channel)
    recipe_config = adapter.get("recipe", {})
    recipe, recipe_selection_status = select_recipe_for_channel(channel, intent, adapter, recipes)
    recipe_id = recipe.get("recipe_id") if recipe else recipe_config.get("recipe_id")
    applicability = freeze_applicability(channel, freeze, patterns_by_id)
    inherit, freeze_reasons = approved_freeze_decision(routed_context, freeze, patterns_by_id)
    readiness, blockers, reason_codes = execution_readiness(
        routed_context, top, freeze, recipe, freeze_applicable=bool(applicability.get("applicable"))
    )
    if channel == "edm" and recipe_selection_status in {"EDM_INTENT_NOT_RESOLVED", "NO_COMPATIBLE_EDM_RECIPE"}:
        reason_codes.append(recipe_selection_status)
        reason_codes.append("HUMAN_REVIEW_REQUIRED")
        blockers.append(
            "EDM channel intent is not resolved"
            if recipe_selection_status == "EDM_INTENT_NOT_RESOLVED"
            else "No EDM Recipe matches the resolved channel intent"
        )
        if readiness["status"] == "READY_FOR_PRODUCTION":
            readiness["status"] = "HUMAN_REVIEW_REQUIRED"
    match = pattern_match_metric(top, weights)
    confidence = evidence_confidence_metric(readiness)
    reason_codes.append(f"PATTERN_MATCH_{match['status']}")
    reason_codes.extend(freeze_reason_codes(applicability, freeze))
    if channel != normalize(context.get("primary_channel")):
        reason_codes.append("CROSS_CHANNEL_VISUAL_DNA_ONLY")
    auto_eligible = (
        readiness["status"] == "READY_FOR_PRODUCTION"
        and top.get("lifecycle") == "VALIDATED"
        and recipe_selection_status not in {"EDM_INTENT_NOT_RESOLVED", "NO_COMPATIBLE_EDM_RECIPE"}
    )
    compatibility = recipe_template_compatibility(recipe)
    routing_status = (
        "HUMAN_REVIEW_REQUIRED"
        if recipe_selection_status in {"EDM_INTENT_NOT_RESOLVED", "NO_COMPATIBLE_EDM_RECIPE"}
        else "CANDIDATE_ROUTE_SELECTED" if channel == "edm" else "EXISTING_RUNTIME"
    )
    recipe_payload = {
        "recipe_id": recipe_id,
        "status": recipe.get("lifecycle", {}).get("status") if recipe else (
            "NOT_SELECTED" if channel == "edm" else recipe_config.get("status")
        ),
        "selection_status": recipe_selection_status,
        "source": recipe.get("_file") if recipe else None,
        "section_patterns": [
            item["pattern_id"] for item in (recipe or {}).get("sequence", []) if item.get("pattern_id")
        ],
        "sections": [copy.deepcopy(item) for item in (recipe or {}).get("sequence", [])],
        "template_selection_request": copy.deepcopy((recipe or {}).get("template_selection_request")),
        "template_compatibility": compatibility,
    }
    return {
        "primary_pattern": {
            "pattern_id": top["pattern_id"],
            "status": top["lifecycle"],
            "legacy_ranking_score": top["score"],
        },
        "supporting_patterns": [item["pattern_id"] for item in ranked[1:3]],
        "routing_status": routing_status,
        "channel_intent": intent,
        "channel_information_density": channel_information_density(context, channel),
        "recipe": recipe_payload,
        "pattern_match": match,
        "execution_readiness": readiness,
        "evidence_confidence": confidence,
        "reason_codes": list(dict.fromkeys(reason_codes)),
        "blocking_reasons": blockers,
        "auto_apply": {
            "eligible": auto_eligible,
            "scope": "VISUAL_STRUCTURE_ONLY",
            "status": "ELIGIBLE" if auto_eligible else "BLOCKED",
        },
        "freeze": {
            "applied": inherit,
            "status": freeze.get("status") if freeze else "NOT_AVAILABLE",
            "applicability": applicability["status"],
            "channel_scope": freeze.get("channel_scope", []) if freeze else [],
            "reason_codes": freeze_reason_codes(applicability, freeze),
            "notes": [] if inherit else freeze_reasons,
        },
        "inheritance": {
            "project_visual_dna": True,
            "information_strategy": True,
            "channel_information_density": False,
            "layout_from_other_channel": False,
            "rule": "Cross-channel routing inherits Visual DNA, never a complete channel layout.",
        },
        "adapter": {
            "adapter_id": adapter.get("adapter_id"),
            "layout_contract": adapter.get("layout_contract"),
            "existing_skill": adapter.get("existing_skill"),
            "existing_template": adapter.get("existing_template"),
            "required_gates": adapter.get("required_gates", []),
            "source_runtime": adapter.get("source_runtime"),
        },
    }, ranked, excluded


def build_profile(project_dir: Path) -> dict[str, Any]:
    context_file = project_dir / "project-context.yaml"
    context = load_yaml(context_file)
    if context.get("contract") != "project-context":
        raise ValueError(f"Invalid project-context contract: {context_file}")
    patterns = load_patterns()
    patterns_by_id = {pattern["pattern_id"]: pattern for pattern in patterns}
    routing = load_yaml(WEIGHTS_FILE)
    weights = {key: float(value) for key, value in routing["weights"].items()}
    thresholds = routing["thresholds"]
    missing_score = float(routing["rules"].get("missing_context_score", 50))
    adapters = load_yaml(ADAPTERS_FILE).get("adapters", {})
    recipes = load_page_recipes()
    primary_channel = normalize(context.get("primary_channel"))
    adapter = adapters.get(primary_channel)
    if not adapter:
        raise ValueError(f"No channel adapter: {context.get('primary_channel')}")

    freeze_file = project_dir / "visual-freeze.yaml"
    freeze = load_yaml(freeze_file) if freeze_file.is_file() else None
    inherit, freeze_reasons = approved_freeze_decision(context, freeze, patterns_by_id)
    planning_record, planning_load_reasons, planning_record_source = load_project_planning_decision(project_dir)

    requested_channels = values(context.get("channels"))
    channels = list(dict.fromkeys([primary_channel, *requested_channels]))
    assignments = {}
    channel_rankings = {}
    channel_excluded = {}
    for channel in channels:
        assignment, channel_ranked, channel_excluded_patterns = channel_assignment(
            context,
            channel,
            patterns,
            patterns_by_id,
            weights,
            missing_score,
            adapters,
            recipes,
            freeze,
        )
        assignments[channel] = assignment
        channel_rankings[channel] = channel_ranked
        channel_excluded[channel] = channel_excluded_patterns

    planning_lock = project_planning_lock_decision(
        context,
        planning_record,
        patterns_by_id,
        assignments,
        inherit,
        planning_load_reasons,
    )

    ranked = channel_rankings[primary_channel]
    excluded = channel_excluded[primary_channel]

    top = ranked[0]
    fallback = ranked[1]["pattern_id"] if len(ranked) > 1 else None
    review_reasons = []
    visual_direction_review_reasons = []
    if inherit:
        selected_id = freeze["pattern_id"]
        mode = "INHERIT_FREEZE"
        human_review_required = False
        decision_reasons = ["Active human-approved Visual Freeze inherited without re-asking visual direction."]
    else:
        selected_id = top["pattern_id"]
        if len(ranked) > 1:
            gap = round(top["score"] - ranked[1]["score"], 1)
            if gap < float(thresholds["top_gap_human_review"]):
                visual_direction_review_reasons.append(
                    f"Top 1 / Top 2 score gap is {gap}, below {thresholds['top_gap_human_review']}"
                )
        if top["dimensions"]["brand_fit"] < float(thresholds["minimum_brand_fit"]):
            visual_direction_review_reasons.append("Brand Fit is below threshold")
        if top["required_asset_gaps"]:
            visual_direction_review_reasons.append("Required assets are missing, partial, or not approved")
        if top["lifecycle"] == "CANDIDATE":
            visual_direction_review_reasons.append("Selected Pattern is CANDIDATE")
        if top["score"] < float(thresholds["minimum_auto_select_score"]):
            visual_direction_review_reasons.append("Top score is below auto-select threshold")
        if context.get("visual_inputs", {}).get("exploration_requested") is True:
            visual_direction_review_reasons.append("User explicitly requested visual exploration")
        if freeze and freeze.get("status") != "APPROVED":
            visual_direction_review_reasons.append("Candidate Freeze exists but is not active APPROVED")
        if freeze and freeze.get("status") == "APPROVED" and freeze_reasons:
            visual_direction_review_reasons.extend(f"Freeze conflict: {reason}" for reason in freeze_reasons)
        if planning_lock["applied"]:
            decision_reasons = [
                "Accepted Project Visual Planning Decision inherited without re-asking visual direction."
            ]
        else:
            review_reasons.extend(visual_direction_review_reasons)
            if planning_lock["status"] == "REOPEN_REQUIRED":
                review_reasons.extend(
                    f"Planning Lock reopened: {reason}" for reason in planning_lock["reopen_reasons"]
                )
        human_review_required = bool(review_reasons)
        mode = "HUMAN_REVIEW_REQUIRED" if human_review_required else "AUTO_ROUTED"
        if not planning_lock["applied"]:
            decision_reasons = selection_reasons(top)

    primary_assignment = assignments[primary_channel]
    if not inherit:
        for blocker in primary_assignment["blocking_reasons"]:
            reason = f"Execution readiness: {blocker}"
            if reason not in review_reasons:
                review_reasons.append(reason)
        human_review_required = bool(review_reasons)
        mode = "HUMAN_REVIEW_REQUIRED" if human_review_required else "AUTO_ROUTED"

    sources = [
        str(context_file.relative_to(ROOT)),
        str(REGISTRY_FILE.relative_to(ROOT)),
        str(WEIGHTS_FILE.relative_to(ROOT)),
        str(ADAPTERS_FILE.relative_to(ROOT)),
        *top.get("sources", []),
        str(RECIPE_REGISTRY_FILE.relative_to(ROOT)),
    ]
    for assignment in assignments.values():
        recipe_source = assignment.get("recipe", {}).get("source")
        if recipe_source:
            sources.append(recipe_source)
        compatibility_sources = (
            assignment.get("recipe", {}).get("template_compatibility") or {}
        ).get("registry_sources", [])
        sources.extend(compatibility_sources)
    if freeze_file.is_file():
        sources.append(str(freeze_file.relative_to(ROOT)))
    if planning_record_source:
        sources.append(planning_record_source)
    sources.extend(context.get("sources", []))
    normalized_sources = normalize_source_references(sources)
    downstream_gates = []
    for assignment in assignments.values():
        downstream_gates.extend(assignment.get("adapter", {}).get("required_gates", []))
    downstream_gates = list(dict.fromkeys(downstream_gates))
    top_reason_codes = []
    top_blockers = []
    for assignment in assignments.values():
        top_reason_codes.extend(assignment.get("reason_codes", []))
        top_blockers.extend(assignment.get("blocking_reasons", []))

    visual_dna = project_visual_dna(context)
    visual_dna["status"] = planning_lock["project_visual_direction_status"]

    return {
        "schema_version": "1.1",
        "contract": "visual-profile",
        "project_id": context["project_id"],
        "generated_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "generated_by": "visual-system/routing/visual_router.py",
        "project_visual_dna": visual_dna,
        "project_visual_direction_status": planning_lock["project_visual_direction_status"],
        "project_planning_lock": planning_lock,
        "pattern_match": primary_assignment["pattern_match"],
        "execution_readiness": primary_assignment["execution_readiness"],
        "evidence_confidence": primary_assignment["evidence_confidence"],
        "channel_assignments": assignments,
        "reason_codes": list(dict.fromkeys(top_reason_codes)),
        "auto_apply": primary_assignment["auto_apply"],
        "blocking_reasons": list(dict.fromkeys(top_blockers)),
        "source_provenance": {
            "status": "MIXED_REVIEW_ONLY",
            "sources": normalized_sources,
            "evidence_limits": [
                "Visual routing does not approve Product Truth, Claim, price, performance, specification, or asset.",
                "Cross-channel inheritance is limited to Project Visual DNA and excludes complete layout.",
            ],
        },
        "decision": {
            "mode": mode,
            "selected_pattern": selected_id,
            "score": next((item["score"] for item in ranked if item["pattern_id"] == selected_id), None),
            "fallback_pattern": fallback,
            "human_review_required": human_review_required,
            "visual_direction_review_required": planning_lock["reask_visual_direction"],
            "reask_visual_direction": planning_lock["reask_visual_direction"],
            "selection_reasons": decision_reasons,
            "review_reasons": review_reasons,
        },
        "freeze": {
            "file_present": freeze_file.is_file(),
            "status": freeze.get("status") if freeze else "NOT_AVAILABLE",
            "inherited": inherit,
            "inheritance_check": "PASS" if inherit else "NOT_APPLIED",
            "notes": [] if inherit else freeze_reasons,
        },
        "channel_adapter": {
            "channel": primary_channel,
            **adapter,
        },
        "ranking": ranked,
        "excluded_patterns": excluded,
        "channel_rankings": channel_rankings,
        "channel_excluded_patterns": channel_excluded,
        "boundaries": {
            "does_not_approve": [
                "Product Truth",
                "Claim",
                "Asset",
                "Final Visual",
                "Amazon Upload",
                "Publication or Send",
            ],
            "downstream_must_keep": downstream_gates,
        },
        "sources": normalized_sources,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate a project visual-profile.yaml")
    parser.add_argument("--project", required=True, help="Project id or project directory")
    parser.add_argument("--output", help="Optional output path; defaults to project/visual-profile.yaml")
    parser.add_argument("--stdout", action="store_true", help="Print without writing")
    args = parser.parse_args()

    project_dir = resolve_project(args.project)
    profile = build_profile(project_dir)
    rendered = yaml.dump(
        profile,
        Dumper=NoAliasSafeDumper,
        allow_unicode=True,
        sort_keys=False,
        width=120,
    )
    if args.stdout:
        print(rendered, end="")
        return 0
    output = Path(args.output).resolve() if args.output else project_dir / "visual-profile.yaml"
    output.write_text(rendered, encoding="utf-8")
    print(f"WROTE {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
