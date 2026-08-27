#!/usr/bin/env python3
"""Resolve task-scoped project context from lightweight project manifests."""

from __future__ import annotations

import argparse
import json
import re
import sys
import unicodedata
from pathlib import Path
from typing import Any

import yaml


DEFAULT_WORKSPACE = Path(__file__).resolve().parents[3]
LIFECYCLE_STAGES = {
    "discovery", "planning", "validation", "production",
    "launch", "live", "review", "archived",
}
GATE_STATUSES = {
    "not_started", "in_progress", "blocked", "ready_for_review",
    "approved", "rejected", "superseded",
}
PROJECT_STATUSES = {"active", "paused", "completed", "archived", "unknown"}
SOURCE_KEYS = (
    "product_truth", "project_memory", "decisions", "approved_claims",
    "visual_context", "visual_profile", "visual_freeze", "assets",
)
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
    except (OSError, yaml.YAMLError, ResolverError) as exc:
        return [f"MANIFEST_READ_ERROR:{path}:{exc}"]

    required = (
        "manifest_version", "project_id", "project_name", "aliases", "market",
        "status", "lifecycle_stage", "sources", "current_phase", "gate_status",
        "approved", "blocking_items", "latest_decision", "next_actions", "skills",
        "last_updated",
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
                validate_record_source(f"next_actions.{priority}.{action.get('action_id')}", action)

    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", str(data.get("last_updated") or "")):
        errors.append("LAST_UPDATED_MUST_BE_DATE")
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


def infer_task_type(request: str, explicit_task_type: str | None = None) -> tuple[str, list[str]]:
    if explicit_task_type:
        lookup = {normalize(item): item for item in TASK_TYPES}
        resolved = lookup.get(normalize(explicit_task_type))
        if not resolved:
            raise ResolverError(f"UNSUPPORTED_TASK_TYPE:{explicit_task_type}")
        return resolved, []
    normalized_request = normalize(request)
    for task_type, patterns in TASK_PATTERNS:
        if any(normalize(pattern) in normalized_request for pattern in patterns):
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
    text = decision_path.read_text(encoding="utf-8")
    blocks = re.findall(r"^###\s+DEC-[^\n]+\n(.*?)(?=^###\s+DEC-|\Z)", text, re.MULTILINE | re.DOTALL)
    return any(re.search(r"^- Status:\s*(?:Accepted|Approved)\s*$", block, re.MULTILINE | re.IGNORECASE) for block in blocks)


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


def select_next_action(manifest: dict[str, Any]) -> list[dict[str, Any]]:
    blocking_states = {"blocked", "in_progress", "ready_for_review"}
    blockers = {
        str(item.get("blocker_id"))
        for item in manifest.get("blocking_items") or []
        if item.get("status") in blocking_states
    }
    for priority in ("p0", "p1", "p2"):
        for action in (manifest.get("next_actions") or {}).get(priority, []):
            if action.get("status") in COMPLETED_ACTION_STATES:
                continue
            blocked_by = [item for item in action.get("blocked_by", []) if item in blockers]
            if action.get("status") == "blocked" or blocked_by:
                execution = "blocked_by_manifest"
            elif action.get("requires_human_approval"):
                execution = "human_review_required"
            else:
                execution = "executable"
            return [{**action, "priority": priority, "execution": execution}]
    return []


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


def build_context(
    workspace: Path,
    request: str,
    explicit_project: str | None = None,
    explicit_task_type: str | None = None,
) -> dict[str, Any]:
    manifests = discover_manifests(workspace)
    manifest_path, manifest = identify_project(manifests, request, explicit_project)
    errors = validate_manifest(manifest_path, workspace)
    if errors:
        raise ResolverError("MANIFEST_INVALID:" + "|".join(errors))
    task_type, warnings = infer_task_type(request, explicit_task_type)
    source_rows, source_warnings = required_source_rows(manifest_path, manifest, workspace, task_type)
    skill_rows, skill_warnings = relevant_skills(manifest, task_type, workspace)
    warnings.extend(source_warnings)
    warnings.extend(skill_warnings)
    warnings.extend(decision_conflict_warning(manifest_path, manifest, workspace))

    latest_decision = manifest.get("latest_decision")
    approved_decisions = []
    if isinstance(latest_decision, dict) and latest_decision.get("status") == "accepted":
        approved_decisions.append(latest_decision)

    product_truth_row = next((row for row in source_rows if row["kind"] == "product_truth"), None)
    current_truth = {
        "status": (manifest.get("gate_status") or {}).get("product_truth", "not_started"),
        "source": None if product_truth_row is None else product_truth_row["paths"],
    }
    return {
        "project": {
            "project_id": manifest["project_id"],
            "project_name": manifest["project_name"],
            "manifest_path": manifest_path.relative_to(workspace).as_posix(),
        },
        "task_type": task_type,
        "current_stage": {
            "lifecycle_stage": manifest["lifecycle_stage"],
            "current_phase": manifest["current_phase"],
            "gate_status": manifest["gate_status"],
        },
        "current_truth": current_truth,
        "approved_decisions": approved_decisions,
        "blocking_items": manifest.get("blocking_items") or [],
        "required_sources": source_rows,
        "relevant_skills": skill_rows,
        "next_valid_actions": select_next_action(manifest),
        "warnings": sorted(set(warnings)),
    }


def dump_context(context: dict[str, Any], output_format: str) -> str:
    if output_format == "json":
        return json.dumps(context, ensure_ascii=False, indent=2) + "\n"
    return yaml.safe_dump(context, allow_unicode=True, sort_keys=False)


def write_human_review(context: dict[str, Any], output_dir: Path) -> Path | None:
    actions = context.get("next_valid_actions") or []
    if not actions or actions[0].get("execution") != "human_review_required":
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
    except (OSError, yaml.YAMLError, ResolverError) as exc:
        print(json.dumps({"status": "ERROR", "error": str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
