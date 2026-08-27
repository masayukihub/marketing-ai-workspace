#!/usr/bin/env python3
"""Deterministic project-level Visual Pattern Router.

The Router selects reusable visual structure. It never approves Product Truth,
Claims, assets, final visual output, publication, or sending.
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml


ROOT = Path(__file__).resolve().parents[2]
SYSTEM_ROOT = ROOT / "visual-system"
REGISTRY_FILE = SYSTEM_ROOT / "registry/pattern-registry.yaml"
WEIGHTS_FILE = SYSTEM_ROOT / "routing/weights.yaml"
ADAPTERS_FILE = SYSTEM_ROOT / "routing/channel-adapters.yaml"


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
    pattern = patterns_by_id.get(freeze.get("pattern_id"))
    if not pattern:
        reasons.append("Freeze Pattern is not registered")
    elif pattern.get("lifecycle", {}).get("status") == "DEPRECATED":
        reasons.append("Freeze Pattern is DEPRECATED")
    channel = normalize(context.get("primary_channel"))
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
    adapter = adapters.get(normalize(context.get("primary_channel")))
    if not adapter:
        raise ValueError(f"No channel adapter: {context.get('primary_channel')}")

    freeze_file = project_dir / "visual-freeze.yaml"
    freeze = load_yaml(freeze_file) if freeze_file.is_file() else None
    inherit, freeze_reasons = approved_freeze_decision(context, freeze, patterns_by_id)

    excluded = []
    ranked = []
    for pattern in patterns:
        score = score_pattern(context, pattern, weights, missing_score)
        if score["excluded"]:
            excluded.append({"pattern_id": pattern["pattern_id"], "reason": score["reason"]})
        else:
            ranked.append(score)
    ranked.sort(key=lambda item: (-item["score"], item["pattern_id"]))
    for index, item in enumerate(ranked, 1):
        item["rank"] = index
    if not ranked:
        raise ValueError("No eligible Pattern for current channel")

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

    sources = [
        str(context_file.relative_to(ROOT)),
        str(REGISTRY_FILE.relative_to(ROOT)),
        str(WEIGHTS_FILE.relative_to(ROOT)),
        str(ADAPTERS_FILE.relative_to(ROOT)),
        *top.get("sources", []),
    ]
    if freeze_file.is_file():
        sources.append(str(freeze_file.relative_to(ROOT)))
    sources.extend(context.get("sources", []))

    return {
        "schema_version": "1.0",
        "contract": "visual-profile",
        "project_id": context["project_id"],
        "generated_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "generated_by": "visual-system/routing/visual_router.py",
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
            "channel": normalize(context.get("primary_channel")),
            **adapter,
        },
        "ranking": ranked,
        "excluded_patterns": excluded,
        "boundaries": {
            "does_not_approve": [
                "Product Truth",
                "Claim",
                "Asset",
                "Final Visual",
                "Amazon Upload",
                "Publication or Send",
            ],
            "downstream_must_keep": adapter.get("required_gates", []),
        },
        "sources": list(dict.fromkeys(sources)),
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
