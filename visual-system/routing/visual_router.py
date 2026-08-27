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


ASSET_SCORES = {
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
        score = ASSET_SCORES.get(status, 0.0)
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
        "required_asset_gaps": asset_gaps,
        "historical_performance_status": historical.get("status", "UNKNOWN"),
        "sources": [pattern["_file"], *pattern.get("sources", [])],
    }


def approved_freeze_decision(
    context: dict[str, Any], freeze: dict[str, Any] | None, patterns_by_id: dict[str, dict[str, Any]]
) -> tuple[bool, list[str]]:
    if not freeze:
        return False, ["No visual-freeze.yaml"]
    reasons = []
    if freeze.get("status") != "APPROVED" or freeze.get("active") is not True:
        reasons.append("Freeze is not active APPROVED")
    approval = freeze.get("human_approval", {})
    if not approval.get("approved_by") or not approval.get("approved_at"):
        reasons.append("Freeze lacks named human approval metadata")
    channel = normalize(context.get("primary_channel"))
    pattern = patterns_by_id.get(freeze.get("pattern_id"))
    if not pattern:
        reasons.append("Freeze Pattern is not registered")
    elif pattern.get("lifecycle", {}).get("status") == "DEPRECATED":
        reasons.append("Freeze Pattern is DEPRECATED")
    elif channel not in values(pattern.get("fit", {}).get("channels")) and "all" not in values(pattern.get("fit", {}).get("channels")):
        reasons.append("Current channel is not supported by Freeze Pattern")
    if channel not in values(freeze.get("channel_scope")):
        reasons.append("Current channel conflicts with Freeze scope")
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


APPROVAL_SCORES = {
    "approved": 100.0,
    "verified_for_channel": 100.0,
    "available": 100.0,
    "verified": 80.0,
    "partial": 50.0,
    "available_review_only": 40.0,
    "pending_verification": 20.0,
    "unapproved_or_unverified": 0.0,
    "missing_or_unverified": 0.0,
    "unknown": 0.0,
    "not_available": 0.0,
}


def status_score(value: Any) -> float:
    return APPROVAL_SCORES.get(normalize(value), 0.0)


def metric_status(score: float) -> str:
    if score >= 75:
        return "HIGH"
    if score >= 55:
        return "MEDIUM"
    return "LOW"


def context_for_channel(context: dict[str, Any], channel: str) -> dict[str, Any]:
    routed = copy.deepcopy(context)
    routed["primary_channel"] = channel
    if channel == "edm":
        goals = ["understand_launch", "discover_primary_benefit", "reach_single_cta"]
        principles = values(routed.get("visual_inputs", {}).get("visual_direction", {}).get("principles"))
        if "mechanism_visible" in principles or "proof_before_persuasion" in principles:
            goals.append("understand_mechanism")
        routed.setdefault("visual_inputs", {})["consumer_goals"] = [
            {"id": goal, "status": "CHANNEL_ROUTING_CANDIDATE"} for goal in goals
        ]
    return routed


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
        "information_density": f"{complexity}_structured",
        "conversion_style": "single_verified_action_after_proof",
        "mobile_priority": normalize(visual_inputs.get("mobile_priority")) or "unknown",
        "content_boundary": [
            "No Product Truth, Claim, price, performance number, specification, or asset is approved by Visual DNA.",
            "Cross-channel inheritance excludes complete layout and channel-native module geometry.",
        ],
    }


def execution_readiness(
    context: dict[str, Any],
    top: dict[str, Any],
    freeze: dict[str, Any] | None,
    recipe: dict[str, Any] | None,
) -> tuple[dict[str, Any], list[str], list[str]]:
    governance = context.get("governance", {})
    truth_status = governance.get("product_truth_status") or context.get("product", {}).get("product_truth_status")
    claim_status = governance.get("claim_status", "UNAPPROVED_OR_UNVERIFIED")
    truth_score = status_score(truth_status)
    claim_score = status_score(claim_status)
    asset_score = float(top["dimensions"]["asset_availability"])
    pattern_score = 100.0 if top.get("lifecycle") == "VALIDATED" else 50.0
    review_clear = (
        truth_score == 100
        and claim_score == 100
        and asset_score == 100
        and pattern_score == 100
        and governance.get("human_review_status") in {"APPROVED", "NOT_REQUIRED"}
        and not (freeze and freeze.get("status") != "APPROVED")
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
    if freeze and freeze.get("status") != "APPROVED":
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


def freeze_reason_codes(channel: str, freeze: dict[str, Any] | None, freeze_reasons: list[str]) -> list[str]:
    if not freeze:
        return ["NO_VISUAL_FREEZE"]
    codes = []
    if freeze.get("status") != "APPROVED" or freeze.get("active") is not True:
        codes.append("CANDIDATE_FREEZE_NOT_APPLIED")
    if channel not in values(freeze.get("channel_scope")):
        codes.append("FREEZE_CHANNEL_SCOPE_EXCLUDES_CHANNEL")
    if any("not supported by Freeze Pattern" in reason for reason in freeze_reasons):
        codes.append("FREEZE_PATTERN_CHANNEL_INCOMPATIBLE")
    return list(dict.fromkeys(codes))


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
    recipe_config = adapter.get("recipe", {})
    recipe = recipes.get(recipe_config.get("recipe_id"))
    inherit, freeze_reasons = approved_freeze_decision(routed_context, freeze, patterns_by_id)
    readiness, blockers, reason_codes = execution_readiness(routed_context, top, freeze, recipe)
    match = pattern_match_metric(top, weights)
    confidence = evidence_confidence_metric(readiness)
    reason_codes.append(f"PATTERN_MATCH_{match['status']}")
    reason_codes.extend(freeze_reason_codes(channel, freeze, freeze_reasons))
    if channel != normalize(context.get("primary_channel")):
        reason_codes.append("CROSS_CHANNEL_VISUAL_DNA_ONLY")
    auto_eligible = readiness["status"] == "READY_FOR_PRODUCTION" and top.get("lifecycle") == "VALIDATED"
    recipe_payload = {
        "recipe_id": recipe_config.get("recipe_id"),
        "status": recipe.get("lifecycle", {}).get("status") if recipe else recipe_config.get("status"),
        "source": recipe.get("_file") if recipe else None,
        "section_patterns": [
            item["pattern_id"] for item in (recipe or {}).get("sequence", []) if item.get("pattern_id")
        ],
    }
    return {
        "primary_pattern": {
            "pattern_id": top["pattern_id"],
            "status": top["lifecycle"],
            "legacy_ranking_score": top["score"],
        },
        "supporting_patterns": [item["pattern_id"] for item in ranked[1:3]],
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
            "channel_scope": freeze.get("channel_scope", []) if freeze else [],
            "reason_codes": freeze_reason_codes(channel, freeze, freeze_reasons),
            "notes": [] if inherit else freeze_reasons,
        },
        "inheritance": {
            "project_visual_dna": True,
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

    ranked = channel_rankings[primary_channel]
    excluded = channel_excluded[primary_channel]

    top = ranked[0]
    fallback = ranked[1]["pattern_id"] if len(ranked) > 1 else None
    review_reasons = []
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
                review_reasons.append(f"Top 1 / Top 2 score gap is {gap}, below {thresholds['top_gap_human_review']}")
        if top["dimensions"]["brand_fit"] < float(thresholds["minimum_brand_fit"]):
            review_reasons.append("Brand Fit is below threshold")
        if top["required_asset_gaps"]:
            review_reasons.append("Required assets are missing, partial, or not approved")
        if top["lifecycle"] == "CANDIDATE":
            review_reasons.append("Selected Pattern is CANDIDATE")
        if top["score"] < float(thresholds["minimum_auto_select_score"]):
            review_reasons.append("Top score is below auto-select threshold")
        if context.get("visual_inputs", {}).get("exploration_requested") is True:
            review_reasons.append("User explicitly requested visual exploration")
        if freeze and freeze.get("status") != "APPROVED":
            review_reasons.append("Candidate Freeze exists but is not active APPROVED")
        if freeze and freeze.get("status") == "APPROVED" and freeze_reasons:
            review_reasons.extend(f"Freeze conflict: {reason}" for reason in freeze_reasons)
        human_review_required = bool(review_reasons)
        mode = "HUMAN_REVIEW_REQUIRED" if human_review_required else "AUTO_ROUTED"
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
    if freeze_file.is_file():
        sources.append(str(freeze_file.relative_to(ROOT)))
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

    return {
        "schema_version": "1.1",
        "contract": "visual-profile",
        "project_id": context["project_id"],
        "generated_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "generated_by": "visual-system/routing/visual_router.py",
        "project_visual_dna": project_visual_dna(context),
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
