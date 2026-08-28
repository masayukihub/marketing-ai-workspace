#!/usr/bin/env python3
"""Resolve task-scoped project context from lightweight project manifests."""

from __future__ import annotations

import argparse
import json
import re
import sys
import unicodedata
from datetime import date, datetime
from pathlib import Path
from typing import Any

import yaml


DEFAULT_WORKSPACE = Path(__file__).resolve().parents[3]
DEFAULT_FRESHNESS_THRESHOLD_DAYS = 7
LIFECYCLE_STAGES = {
    "discovery", "planning", "validation", "production",
    "launch", "live", "review", "archived",
}
GATE_STATUSES = {
    "not_started", "in_progress", "blocked", "ready_for_review",
    "approved", "rejected", "superseded",
}
PROJECT_STATUSES = {"active", "paused", "completed", "archived", "unknown"}
FRESHNESS_STATUSES = {"current", "stale", "unknown"}
ACTION_EXECUTION_CLASSES = {
    "read_only_audit", "source_refresh", "human_review_preparation",
    "state_dependent_execution",
}
STALE_SAFE_ACTION_CLASSES = {
    "read_only_audit", "source_refresh", "human_review_preparation",
}
SOURCE_KEYS = (
    "product_truth", "project_memory", "decisions", "approved_claims",
    "visual_context", "visual_profile", "visual_freeze", "assets",
)
OPTIONAL_SOURCE_KEYS = ("visual_planning_decision",)
TASK_TYPES = (
    "GTM", "Amazon", "PR", "KOL", "Campaign", "VOC", "Competitor",
    "Design", "Visual", "Product Knowledge", "Website", "SEO", "Review",
)
TASK_PATTERNS = (
    ("Product Knowledge", ("product knowledge", "product truth", "产品知识", "产品事实")),
    ("Amazon", ("amazon", "亚马逊", "日亚", "gallery", "a+")),
    ("PR", ("pr", "prtimes", "媒体稿", "新闻稿")),
    ("KOL", ("kol", "influencer", "creator", "达人", "网红")),
    ("Campaign", ("campaign", "活动", "大促", "促销")),
    ("VOC", ("voc", "customer review", "product review", "review intelligence", "ratings", "评价", "评论", "用户反馈")),
    ("Competitor", ("competitor", "竞品", "競合")),
    ("Design", ("design", "设计", "デザイン")),
    ("Visual", ("visual", "视觉", "ビジュアル")),
    ("Website", ("website", "官网", "网站", "lp")),
    ("SEO", ("seo",)),
    ("Review", ("review", "复盘", "retrospective", "审核")),
    ("GTM", ("gtm", "launch", "上市", "新品")),
)
TASK_SOURCE_KEYS = {
    "GTM": ("project_memory", "decisions", "product_truth", "approved_claims"),
    "Amazon": (
        "project_memory", "decisions", "product_truth", "approved_claims",
        "visual_context", "visual_profile", "visual_freeze", "assets",
    ),
    "PR": ("project_memory", "decisions", "product_truth", "approved_claims", "assets"),
    "KOL": ("project_memory", "decisions", "product_truth", "approved_claims", "assets"),
    "Campaign": ("project_memory", "decisions", "product_truth", "approved_claims", "assets"),
    "VOC": ("project_memory", "decisions", "product_truth"),
    "Competitor": ("project_memory", "decisions", "product_truth"),
    "Design": (
        "project_memory", "decisions", "product_truth", "approved_claims",
        "visual_context", "visual_profile", "visual_freeze", "assets",
    ),
    "Visual": (
        "project_memory", "decisions", "product_truth", "approved_claims",
        "visual_context", "visual_profile", "visual_freeze", "assets",
    ),
    "Product Knowledge": ("product_truth", "approved_claims", "project_memory"),
    "Website": ("project_memory", "decisions", "product_truth", "approved_claims", "assets"),
    "SEO": ("project_memory", "decisions", "product_truth", "approved_claims"),
    "Review": ("project_memory", "decisions"),
}
TASK_SKILLS = {
    "GTM": ("project-memory-manager", "product-knowledge"),
    "Amazon": ("jp-commerce-content-flow", "product-knowledge"),
    "PR": ("product-knowledge", "project-memory-manager"),
    "KOL": ("influencer-marketing", "product-knowledge"),
    "Campaign": ("switchbot-japan-campaign", "product-knowledge"),
    "VOC": ("customer-review-intelligence", "product-knowledge"),
    "Competitor": ("jp-commerce-insights", "product-knowledge", "project-memory-manager"),
    "Design": ("jp-commerce-content-flow", "product-knowledge"),
    "Visual": ("jp-commerce-content-flow", "product-knowledge"),
    "Product Knowledge": ("product-knowledge", "project-memory-manager"),
    "Website": ("product-knowledge", "project-memory-manager"),
    "SEO": ("product-knowledge", "project-memory-manager"),
    "Review": ("project-memory-manager",),
}
TASK_OPTIONAL_SKILLS = {
    "Amazon": ("amazon-japan-pdp-generator", "amazon-listing-creative", "jp-commerce-insights"),
    "Campaign": ("switchbot-campaign-review",),
    "VOC": ("jp-commerce-insights",),
    "Design": ("amazon-listing-creative", "amazon-japan-pdp-generator"),
    "Visual": ("amazon-listing-creative", "amazon-japan-pdp-generator"),
}
COMPLETED_ACTION_STATES = {"approved", "rejected", "superseded"}


class ResolverError(RuntimeError):
    """A deterministic project-resolution failure."""


def normalize(value: Any) -> str:
    text = unicodedata.normalize("NFKC", str(value or "")).casefold().strip()
    return re.sub(r"[\s_]+", "-", text)


def task_pattern_matches(request: str, pattern: str) -> bool:
    request_text = unicodedata.normalize("NFKC", str(request or "")).casefold()
    pattern_text = unicodedata.normalize("NFKC", str(pattern or "")).casefold().strip()
    if not pattern_text:
        return False
    if re.search(r"[a-z0-9]", pattern_text):
        parts = [re.escape(item) for item in re.split(r"[\s_-]+", pattern_text) if item]
        expression = r"[\s_-]+".join(parts)
        return re.search(rf"(?<![a-z0-9]){expression}(?![a-z0-9])", request_text) is not None
    return pattern_text in request_text


def load_yaml(path: Path) -> dict[str, Any]:
    value = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ResolverError(f"MANIFEST_NOT_MAPPING:{path}")
    return value


def pointer_values(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        return [value]
    if isinstance(value, list) and all(isinstance(item, str) for item in value):
        return value
    raise ResolverError("SOURCE_POINTER_MUST_BE_NULL_STRING_OR_STRING_LIST")


def resolve_pointer(manifest_path: Path, pointer: str, workspace: Path) -> tuple[str, bool]:
    raw = Path(pointer).expanduser()
    resolved = raw.resolve() if raw.is_absolute() else (manifest_path.parent / raw).resolve()
    try:
        display = resolved.relative_to(workspace.resolve()).as_posix()
    except ValueError:
        display = str(resolved)
    return display, resolved.exists()


def validate_manifest(path: Path, workspace: Path) -> list[str]:
    errors: list[str] = []
    try:
        data = load_yaml(path)
    except (OSError, ValueError, yaml.YAMLError, ResolverError) as exc:
        return [f"MANIFEST_READ_ERROR:{path}:{exc}"]

    required = (
        "manifest_version", "project_id", "project_name", "aliases", "market",
        "status", "lifecycle_stage", "sources", "current_phase", "gate_status",
        "approved", "blocking_items", "latest_decision", "next_actions", "skills",
        "last_updated", "manifest_updated_at", "state_as_of", "freshness_status",
        "freshness_sources",
    )
    for key in required:
        if key not in data:
            errors.append(f"MISSING_REQUIRED_FIELD:{key}")

    project_id = str(data.get("project_id") or "")
    if not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", project_id):
        errors.append("INVALID_PROJECT_ID")
    if project_id and path.parent.name != project_id:
        errors.append(f"PROJECT_ID_DIRECTORY_MISMATCH:{project_id}:{path.parent.name}")
    if data.get("lifecycle_stage") not in LIFECYCLE_STAGES:
        errors.append(f"INVALID_LIFECYCLE_STAGE:{data.get('lifecycle_stage')}")
    if data.get("status") not in PROJECT_STATUSES:
        errors.append(f"INVALID_PROJECT_STATUS:{data.get('status')}")
    if not isinstance(data.get("aliases"), list):
        errors.append("ALIASES_MUST_BE_LIST")
    alias_notes = data.get("alias_notes")
    if alias_notes is not None:
        if not isinstance(alias_notes, dict):
            errors.append("ALIAS_NOTES_MUST_BE_MAPPING")
        else:
            normalized_aliases = {normalize(item) for item in data.get("aliases") or []}
            for alias, note in alias_notes.items():
                if normalize(alias) not in normalized_aliases:
                    errors.append(f"ALIAS_NOTE_WITHOUT_ALIAS:{alias}")
                if not isinstance(note, str) or not note.strip():
                    errors.append(f"ALIAS_NOTE_MUST_BE_NONEMPTY:{alias}")

    gate_status = data.get("gate_status")
    if not isinstance(gate_status, dict) or not gate_status:
        errors.append("GATE_STATUS_MUST_BE_NONEMPTY_MAPPING")
    else:
        for gate, status in gate_status.items():
            if status not in GATE_STATUSES:
                errors.append(f"INVALID_GATE_STATUS:{gate}:{status}")

    sources = data.get("sources")
    if not isinstance(sources, dict):
        errors.append("SOURCES_MUST_BE_MAPPING")
    else:
        for key in SOURCE_KEYS:
            if key not in sources:
                errors.append(f"MISSING_SOURCE_KEY:{key}")
                continue
            try:
                values = pointer_values(sources.get(key))
            except ResolverError as exc:
                errors.append(f"INVALID_SOURCE_POINTER:{key}:{exc}")
                continue
            for pointer in values:
                _, exists = resolve_pointer(path, pointer, workspace)
                if not exists:
                    errors.append(f"SOURCE_PATH_MISSING:{key}:{pointer}")
        for key in OPTIONAL_SOURCE_KEYS:
            if key not in sources:
                continue
            try:
                values = pointer_values(sources.get(key))
            except ResolverError as exc:
                errors.append(f"INVALID_SOURCE_POINTER:{key}:{exc}")
                continue
            for pointer in values:
                _, exists = resolve_pointer(path, pointer, workspace)
                if not exists:
                    errors.append(f"SOURCE_PATH_MISSING:{key}:{pointer}")

    def validate_record_source(label: str, record: Any) -> None:
        if not isinstance(record, dict):
            return
        source = record.get("source")
        if not isinstance(source, str) or not source.strip():
            errors.append(f"RECORD_SOURCE_MISSING:{label}")
            return
        _, exists = resolve_pointer(path, source, workspace)
        if not exists:
            errors.append(f"RECORD_SOURCE_PATH_MISSING:{label}:{source}")

    for index, item in enumerate(data.get("approved") or []):
        validate_record_source(f"approved[{index}]", item)
    for index, item in enumerate(data.get("blocking_items") or []):
        validate_record_source(f"blocking_items[{index}]", item)
    validate_record_source("latest_decision", data.get("latest_decision"))

    next_actions = data.get("next_actions")
    if not isinstance(next_actions, dict):
        errors.append("NEXT_ACTIONS_MUST_BE_MAPPING")
    else:
        for priority in ("p0", "p1", "p2"):
            actions = next_actions.get(priority)
            if not isinstance(actions, list):
                errors.append(f"NEXT_ACTIONS_{priority.upper()}_MUST_BE_LIST")
                continue
            for action in actions:
                if not isinstance(action, dict):
                    errors.append(f"NEXT_ACTION_MUST_BE_MAPPING:{priority}")
                    continue
                if action.get("status") not in GATE_STATUSES:
                    errors.append(f"INVALID_ACTION_STATUS:{action.get('action_id')}")
                if not isinstance(action.get("requires_human_approval"), bool):
                    errors.append(f"ACTION_APPROVAL_FLAG_MUST_BE_BOOLEAN:{action.get('action_id')}")
                if action.get("execution_class") not in ACTION_EXECUTION_CLASSES:
                    errors.append(f"INVALID_ACTION_EXECUTION_CLASS:{action.get('action_id')}")
                validate_record_source(f"next_actions.{priority}.{action.get('action_id')}", action)

    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", str(data.get("last_updated") or "")):
        errors.append("LAST_UPDATED_MUST_BE_DATE")
    try:
        manifest_updated_at = str(data.get("manifest_updated_at") or "")
        datetime.fromisoformat(manifest_updated_at)
        if "T" not in manifest_updated_at:
            raise ValueError
    except ValueError:
        errors.append("MANIFEST_UPDATED_AT_MUST_BE_ISO_DATETIME")
    state_as_of = data.get("state_as_of")
    if state_as_of is not None:
        try:
            date.fromisoformat(str(state_as_of))
        except ValueError:
            errors.append("STATE_AS_OF_MUST_BE_DATE_OR_NULL")
    if data.get("freshness_status") not in FRESHNESS_STATUSES:
        errors.append(f"INVALID_FRESHNESS_STATUS:{data.get('freshness_status')}")
    if data.get("freshness_status") == "current" and state_as_of is None:
        errors.append("CURRENT_FRESHNESS_REQUIRES_STATE_AS_OF")
    freshness_sources = data.get("freshness_sources")
    if not isinstance(freshness_sources, list) or not freshness_sources:
        errors.append("FRESHNESS_SOURCES_MUST_BE_NONEMPTY_LIST")
    else:
        for pointer in freshness_sources:
            if not isinstance(pointer, str) or not pointer.strip():
                errors.append("FRESHNESS_SOURCE_MUST_BE_NONEMPTY_STRING")
                continue
            _, exists = resolve_pointer(path, pointer, workspace)
            if not exists:
                errors.append(f"FRESHNESS_SOURCE_PATH_MISSING:{pointer}")
    return sorted(set(errors))


def discover_manifests(workspace: Path) -> list[tuple[Path, dict[str, Any]]]:
    base = workspace / "projects"
    manifests = []
    for path in sorted(base.glob("*/project.yaml")):
        manifests.append((path, load_yaml(path)))
    if not manifests:
        raise ResolverError("NO_PROJECT_MANIFESTS")
    return manifests


def project_aliases(path: Path, manifest: dict[str, Any]) -> list[str]:
    values = [manifest.get("project_id"), manifest.get("project_name"), path.parent.name]
    values.extend(manifest.get("aliases") or [])
    return [str(value) for value in values if str(value or "").strip()]


def identify_project(
    manifests: list[tuple[Path, dict[str, Any]]], request: str, explicit_project: str | None = None
) -> tuple[Path, dict[str, Any]]:
    needle = normalize(explicit_project or request)
    exact: list[tuple[Path, dict[str, Any]]] = []
    contained: list[tuple[int, Path, dict[str, Any]]] = []
    for path, manifest in manifests:
        for alias in project_aliases(path, manifest):
            normalized_alias = normalize(alias)
            if needle == normalized_alias:
                exact.append((path, manifest))
            elif normalized_alias and normalized_alias in needle:
                contained.append((len(normalized_alias), path, manifest))
    matches = exact
    if not matches and contained:
        best = max(item[0] for item in contained)
        matches = [(path, manifest) for length, path, manifest in contained if length == best]
    unique = {(path.resolve(), str(manifest.get("project_id"))): (path, manifest) for path, manifest in matches}
    if not unique:
        raise ResolverError(f"PROJECT_NOT_FOUND:{explicit_project or request}")
    if len(unique) > 1:
        ids = ",".join(sorted(project_id for _, project_id in unique))
        raise ResolverError(f"PROJECT_AMBIGUOUS:{ids}")
    return next(iter(unique.values()))


def routing_alias_context(manifest: dict[str, Any], request: str) -> tuple[str | None, str | None]:
    candidates: list[tuple[int, str, str]] = []
    normalized_request = normalize(request)
    for alias, note in (manifest.get("alias_notes") or {}).items():
        normalized_alias = normalize(alias)
        if normalized_alias and normalized_alias in normalized_request:
            candidates.append((len(normalized_alias), str(alias), str(note)))
    if not candidates:
        return None, None
    _, alias, note = max(candidates, key=lambda item: item[0])
    return alias, note


def infer_task_type(request: str, explicit_task_type: str | None = None) -> tuple[str, list[str]]:
    if explicit_task_type:
        lookup = {normalize(item): item for item in TASK_TYPES}
        resolved = lookup.get(normalize(explicit_task_type))
        if not resolved:
            raise ResolverError(f"UNSUPPORTED_TASK_TYPE:{explicit_task_type}")
        return resolved, []
    for task_type, patterns in TASK_PATTERNS:
        if any(task_pattern_matches(request, pattern) for pattern in patterns):
            return task_type, []
    return "GTM", ["TASK_TYPE_DEFAULTED_TO_GTM_FOR_PROJECT_CONTINUATION"]


def required_source_rows(
    manifest_path: Path, manifest: dict[str, Any], workspace: Path, task_type: str
) -> tuple[list[dict[str, Any]], list[str]]:
    rows = [{"kind": "manifest", "status": "available", "paths": [manifest_path.relative_to(workspace).as_posix()]}]
    warnings: list[str] = []
    sources = manifest.get("sources") or {}
    for kind in TASK_SOURCE_KEYS[task_type]:
        resolved_paths: list[str] = []
        missing = False
        for pointer in pointer_values(sources.get(kind)):
            display, exists = resolve_pointer(manifest_path, pointer, workspace)
            if exists:
                resolved_paths.append(display)
            else:
                missing = True
                warnings.append(f"SOURCE_PATH_MISSING:{kind}:{display}")
        if not resolved_paths:
            missing = True
            warnings.append(f"SOURCE_POINTER_MISSING:{kind}")
        rows.append({"kind": kind, "status": "missing" if missing else "available", "paths": resolved_paths})
    return rows, sorted(set(warnings))


def has_accepted_decision(decision_path: Path) -> bool:
    if not decision_path.is_file():
        return False
    if decision_path.suffix.lower() in {".yaml", ".yml"}:
        try:
            decision = load_yaml(decision_path)
        except (OSError, ValueError, yaml.YAMLError, ResolverError):
            return False
        return (
            str(decision.get("record_status") or "").upper() == "ACCEPTED"
            and str(decision.get("decision_result") or "").upper()
            in {"APPROVED", "APPROVED_WITH_MODIFICATION"}
        )
    text = decision_path.read_text(encoding="utf-8")
    blocks = re.findall(r"^###\s+DEC-[^\n]+\n(.*?)(?=^###\s+DEC-|\Z)", text, re.MULTILINE | re.DOTALL)
    return any(re.search(r"^- Status:\s*(?:Accepted|Approved)\s*$", block, re.MULTILINE | re.IGNORECASE) for block in blocks)


def accepted_visual_planning_decision(
    manifest_path: Path, manifest: dict[str, Any], workspace: Path
) -> dict[str, Any] | None:
    pointers = pointer_values((manifest.get("sources") or {}).get("visual_planning_decision"))
    if not pointers:
        return None
    display, exists = resolve_pointer(manifest_path, pointers[0], workspace)
    if not exists:
        return None
    path = workspace / display if not Path(display).is_absolute() else Path(display)
    try:
        record = load_yaml(path)
    except (OSError, ValueError, yaml.YAMLError, ResolverError):
        return None
    lock = record.get("project_planning_lock") or {}
    if (
        record.get("contract") != "visual-pattern-recipe-decision-record"
        or str(record.get("record_status") or "").upper() != "ACCEPTED"
        or str(lock.get("status") or "").upper() != "ACTIVE"
    ):
        return None
    return {
        "status": "ACCEPTED",
        "project_visual_direction_status": lock.get("project_visual_direction_status"),
        "reask_visual_direction": lock.get("reask_visual_direction"),
        "review_id": record.get("review_id"),
        "source": display,
        "reopen_when": lock.get("reopen_when", []),
    }


def decision_conflict_warning(manifest_path: Path, manifest: dict[str, Any], workspace: Path) -> list[str]:
    latest = manifest.get("latest_decision") or {}
    target_gate = latest.get("target_gate")
    expected_status = latest.get("expected_status")
    source = latest.get("source")
    if latest.get("status") != "accepted" or not target_gate or not expected_status or not source:
        return []
    display, exists = resolve_pointer(manifest_path, source, workspace)
    candidate = workspace / display if not Path(display).is_absolute() else Path(display)
    evidence_is_accepted = exists and has_accepted_decision(candidate)
    formal_status = (manifest.get("gate_status") or {}).get(target_gate)
    if evidence_is_accepted and formal_status != expected_status:
        return [
            "FORMAL_STATUS_DECISION_CONFLICT:"
            f"{target_gate}={formal_status};accepted_decision_expected={expected_status};"
            "project.yaml current formal status takes precedence"
        ]
    return []


def load_freshness_threshold(workspace: Path) -> int:
    config_path = workspace / "skills/project-context-resolver/config/freshness.yaml"
    if not config_path.is_file():
        return DEFAULT_FRESHNESS_THRESHOLD_DAYS
    config = load_yaml(config_path)
    value = config.get("active_project_max_age_days", DEFAULT_FRESHNESS_THRESHOLD_DAYS)
    if not isinstance(value, int) or value < 1:
        raise ResolverError("INVALID_FRESHNESS_THRESHOLD")
    return value


def evaluate_freshness(
    manifest_path: Path,
    manifest: dict[str, Any],
    workspace: Path,
    as_of: date | None = None,
) -> tuple[dict[str, Any], list[str]]:
    threshold_days = load_freshness_threshold(workspace)
    as_of = as_of or date.today()
    declared_status = manifest.get("freshness_status", "unknown")
    state_value = manifest.get("state_as_of")
    warnings: list[str] = []
    state_date: date | None = None
    age_days: int | None = None

    if state_value is not None:
        try:
            state_date = date.fromisoformat(str(state_value))
            age_days = (as_of - state_date).days
        except ValueError:
            state_date = None
    if state_date is None or age_days is None or age_days < 0:
        effective_status = "unknown"
        warnings.append("PROJECT_STATE_UNKNOWN:state_as_of is missing, invalid, or in the future")
    elif manifest.get("status") == "active" and age_days > threshold_days:
        effective_status = "stale"
        warnings.append(
            "PROJECT_STATE_STALE:"
            f"state_as_of={state_date.isoformat()};age_days={age_days};threshold_days={threshold_days}"
        )
    elif declared_status == "stale":
        effective_status = "stale"
        warnings.append(
            "PROJECT_STATE_STALE:"
            f"declared_status=stale;state_as_of={state_date.isoformat()};threshold_days={threshold_days}"
        )
    elif declared_status == "unknown":
        effective_status = "unknown"
        warnings.append("PROJECT_STATE_UNKNOWN:manifest freshness_status is unknown")
    else:
        effective_status = "current"

    resolved_sources: list[str] = []
    for pointer in manifest.get("freshness_sources") or []:
        display, exists = resolve_pointer(manifest_path, pointer, workspace)
        if exists:
            resolved_sources.append(display)

    return {
        "manifest_updated_at": str(manifest.get("manifest_updated_at")),
        "state_as_of": None if state_date is None else state_date.isoformat(),
        "declared_status": declared_status,
        "effective_status": effective_status,
        "evaluated_at": as_of.isoformat(),
        "threshold_days": threshold_days,
        "age_days": age_days,
        "sources": resolved_sources,
    }, warnings


def select_next_action(manifest: dict[str, Any], freshness_status: str = "current") -> list[dict[str, Any]]:
    blocking_states = {"blocked", "in_progress", "ready_for_review"}
    blockers = {
        str(item.get("blocker_id"))
        for item in manifest.get("blocking_items") or []
        if item.get("status") in blocking_states
    }
    freshness_blocked_candidate: dict[str, Any] | None = None
    for priority in ("p0", "p1", "p2"):
        for action in (manifest.get("next_actions") or {}).get(priority, []):
            if action.get("status") in COMPLETED_ACTION_STATES:
                continue
            blocked_by = [item for item in action.get("blocked_by", []) if item in blockers]
            execution_class = action.get("execution_class", "state_dependent_execution")
            if action.get("status") == "blocked" or blocked_by:
                execution = "blocked_by_manifest"
            elif freshness_status in {"stale", "unknown"} and execution_class not in STALE_SAFE_ACTION_CLASSES:
                if freshness_blocked_candidate is None:
                    freshness_blocked_candidate = {
                        **action,
                        "priority": priority,
                        "execution": "blocked_by_freshness",
                    }
                continue
            elif freshness_status in {"stale", "unknown"} and execution_class == "human_review_preparation":
                execution = "human_review_preparation_allowed"
            elif freshness_status in {"stale", "unknown"}:
                execution = "read_only_allowed_with_unverified_state"
            elif action.get("requires_human_approval"):
                execution = "human_review_required"
            else:
                execution = "executable"
            return [{**action, "priority": priority, "execution": execution}]
    return [] if freshness_blocked_candidate is None else [freshness_blocked_candidate]


def relevant_skills(manifest: dict[str, Any], task_type: str, workspace: Path) -> tuple[dict[str, list[str]], list[str]]:
    requested = ["project-context-resolver", *TASK_SKILLS[task_type]]
    primary: list[str] = []
    optional: list[str] = []
    warnings: list[str] = []
    for skill in requested:
        if skill not in primary:
            primary.append(skill)
        if not (workspace / "skills" / skill / "SKILL.md").is_file():
            warnings.append(f"SKILL_NOT_IN_REPOSITORY:{skill}")
    manifest_optional = set((manifest.get("skills") or {}).get("optional") or [])
    for skill in TASK_OPTIONAL_SKILLS.get(task_type, ()):
        if skill in manifest_optional and skill not in primary and skill not in optional:
            optional.append(skill)
            if not (workspace / "skills" / skill / "SKILL.md").is_file():
                warnings.append(f"SKILL_NOT_IN_REPOSITORY:{skill}")
    return {"primary": primary, "optional": optional}, warnings


def project_bootstrap_result(request: str) -> dict[str, Any]:
    return {
        "resolution_status": "PROJECT_BOOTSTRAP_REQUIRED",
        "request": request,
        "recommended_skill": "project-memory-manager",
        "auto_create": False,
        "allowed_action": "prepare_project_discovery_review",
        "warnings": ["PROJECT_NOT_FOUND:NO_MANIFEST_MATCH"],
    }


def build_context(
    workspace: Path,
    request: str,
    explicit_project: str | None = None,
    explicit_task_type: str | None = None,
    as_of: date | None = None,
) -> dict[str, Any]:
    manifests = discover_manifests(workspace)
    try:
        manifest_path, manifest = identify_project(manifests, request, explicit_project)
    except ResolverError as exc:
        if str(exc).startswith("PROJECT_NOT_FOUND:"):
            return project_bootstrap_result(explicit_project or request)
        raise
    errors = validate_manifest(manifest_path, workspace)
    if errors:
        raise ResolverError("MANIFEST_INVALID:" + "|".join(errors))
    task_type, warnings = infer_task_type(request, explicit_task_type)
    freshness, freshness_warnings = evaluate_freshness(manifest_path, manifest, workspace, as_of)
    source_rows, source_warnings = required_source_rows(manifest_path, manifest, workspace, task_type)
    skill_rows, skill_warnings = relevant_skills(manifest, task_type, workspace)
    warnings.extend(freshness_warnings)
    warnings.extend(source_warnings)
    warnings.extend(skill_warnings)
    warnings.extend(decision_conflict_warning(manifest_path, manifest, workspace))

    latest_decision = manifest.get("latest_decision")
    approved_decisions = []
    if isinstance(latest_decision, dict) and latest_decision.get("status") == "accepted":
        approved_decisions.append(latest_decision)
    visual_planning_decision = accepted_visual_planning_decision(manifest_path, manifest, workspace)

    product_truth_row = next((row for row in source_rows if row["kind"] == "product_truth"), None)
    current_truth = {
        "status": (manifest.get("gate_status") or {}).get("product_truth", "not_started"),
        "source": None if product_truth_row is None else product_truth_row["paths"],
    }
    matched_alias, alias_note = routing_alias_context(manifest, explicit_project or request)
    if matched_alias and alias_note:
        warnings.append(f"PROJECT_ROUTING_ALIAS_ONLY:{matched_alias}:{alias_note}")
    return {
        "resolution_status": "RESOLVED",
        "project": {
            "project_id": manifest["project_id"],
            "project_name": manifest["project_name"],
            "manifest_path": manifest_path.relative_to(workspace).as_posix(),
            "routing_alias": matched_alias,
            "routing_alias_note": alias_note,
        },
        "task_type": task_type,
        "current_stage": {
            "lifecycle_stage": manifest["lifecycle_stage"],
            "current_phase": manifest["current_phase"],
            "gate_status": manifest["gate_status"],
        },
        "freshness": freshness,
        "current_truth": current_truth,
        "approved_decisions": approved_decisions,
        "project_visual_decision": visual_planning_decision,
        "blocking_items": manifest.get("blocking_items") or [],
        "required_sources": source_rows,
        "relevant_skills": skill_rows,
        "next_valid_actions": select_next_action(manifest, freshness["effective_status"]),
        "warnings": sorted(set(warnings)),
    }


def dump_context(context: dict[str, Any], output_format: str) -> str:
    if output_format == "json":
        return json.dumps(context, ensure_ascii=False, indent=2) + "\n"
    return yaml.safe_dump(context, allow_unicode=True, sort_keys=False)


def write_human_review(context: dict[str, Any], output_dir: Path) -> Path | None:
    actions = context.get("next_valid_actions") or []
    if not actions or actions[0].get("execution") not in {
        "human_review_required", "human_review_preparation_allowed",
    }:
        return None
    output_dir.mkdir(parents=True, exist_ok=True)
    target = output_dir / "HUMAN_REVIEW_REQUIRED.md"
    action = actions[0]
    body = f"""# Human Review Required

- Project: `{context['project']['project_id']}`
- Action: `{action['action_id']}` — {action['action']}
- Manifest: `{context['project']['manifest_path']}`
- Execution: `NOT_EXECUTED`

```yaml
decision: ""
reviewer: ""
reviewed_at: ""
evidence_reviewed: ""
comments: ""
```
"""
    target.write_text(body, encoding="utf-8")
    return target


def validate_all(workspace: Path) -> dict[str, Any]:
    rows = []
    for path in sorted((workspace / "projects").glob("*/project.yaml")):
        errors = validate_manifest(path, workspace)
        rows.append({
            "manifest": path.relative_to(workspace).as_posix(),
            "status": "PASS" if not errors else "FAIL",
            "errors": errors,
        })
    return {"status": "PASS" if rows and all(row["status"] == "PASS" for row in rows) else "FAIL", "manifests": rows}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workspace", default=str(DEFAULT_WORKSPACE))
    parser.add_argument("--request")
    parser.add_argument("--project")
    parser.add_argument("--task-type")
    parser.add_argument("--format", choices=("yaml", "json"), default="yaml")
    parser.add_argument("--output")
    parser.add_argument("--human-review-dir")
    parser.add_argument("--as-of", help="Evaluate freshness on YYYY-MM-DD; defaults to today")
    parser.add_argument("--validate-all", action="store_true")
    args = parser.parse_args()
    workspace = Path(args.workspace).expanduser().resolve()

    try:
        if args.validate_all:
            result = validate_all(workspace)
            print(dump_context(result, args.format), end="")
            return 0 if result["status"] == "PASS" else 1
        if not args.request and not args.project:
            parser.error("--request or --project is required unless --validate-all is used")
        context = build_context(
            workspace,
            request=args.request or args.project,
            explicit_project=args.project,
            explicit_task_type=args.task_type,
            as_of=None if not args.as_of else date.fromisoformat(args.as_of),
        )
        payload = dump_context(context, args.format)
        if args.output:
            output = Path(args.output).expanduser().resolve()
            output.parent.mkdir(parents=True, exist_ok=True)
            output.write_text(payload, encoding="utf-8")
        else:
            print(payload, end="")
        if args.human_review_dir:
            write_human_review(context, Path(args.human_review_dir).expanduser().resolve())
        return 0
    except (OSError, ValueError, yaml.YAMLError, ResolverError) as exc:
        print(json.dumps({"status": "ERROR", "error": str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
