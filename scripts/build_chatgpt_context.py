#!/usr/bin/env python3
"""Generate lightweight, read-only ChatGPT project context snapshots."""

from __future__ import annotations

import argparse
import importlib.util
import re
import sys
from datetime import date
from pathlib import Path
from typing import Any

import yaml

from runtime_contract import git_commit_exists


ROOT = Path(__file__).resolve().parents[1]
INDEX_PATH = ROOT / "chatgpt/context-index.yaml"
RESOLVER_PATH = ROOT / "skills/project-context-resolver/scripts/resolve_project_context.py"
SNAPSHOT_FIELDS = {
    "snapshot_contract",
    "snapshot_authority",
    "project_id",
    "current_main_commit",
    "generated_as_of",
    "state_as_of",
    "effective_freshness_status",
    "lifecycle_stage",
    "accepted_decisions",
    "blockers",
    "next_actions",
    "required_github_source_paths",
}


def load_resolver():
    spec = importlib.util.spec_from_file_location("project_context_resolver", RESOLVER_PATH)
    if not spec or not spec.loader:
        raise RuntimeError("RESOLVER_IMPORT_FAILED")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def load_yaml(path: Path) -> dict[str, Any]:
    value = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise RuntimeError(f"YAML_MAPPING_REQUIRED:{path}")
    return value


def pointer_values(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        return [value]
    if isinstance(value, list) and all(isinstance(item, str) for item in value):
        return value
    raise RuntimeError("INVALID_SOURCE_POINTER")


def required_source_paths(workspace: Path, manifest_path: Path, manifest: dict[str, Any], resolver) -> list[str]:
    pointers: list[str] = []
    for value in (manifest.get("sources") or {}).values():
        pointers.extend(pointer_values(value))
    pointers.extend(manifest.get("freshness_sources") or [])
    for record in manifest.get("approved") or []:
        if isinstance(record, dict) and isinstance(record.get("source"), str):
            pointers.append(record["source"])
    for record in manifest.get("blocking_items") or []:
        if isinstance(record, dict) and isinstance(record.get("source"), str):
            pointers.append(record["source"])
    latest = manifest.get("latest_decision")
    if isinstance(latest, dict) and isinstance(latest.get("source"), str):
        pointers.append(latest["source"])
    for priority in ("p0", "p1", "p2"):
        for action in (manifest.get("next_actions") or {}).get(priority, []):
            if isinstance(action, dict) and isinstance(action.get("source"), str):
                pointers.append(action["source"])

    paths = {manifest_path.relative_to(workspace).as_posix()}
    for pointer in pointers:
        display, exists = resolver.resolve_pointer(manifest_path, pointer, workspace)
        if exists and not Path(display).is_absolute():
            paths.add(display)
    return sorted(paths)


def accepted_decisions(manifest: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    seen: set[str] = set()
    latest = manifest.get("latest_decision")
    if isinstance(latest, dict) and latest.get("status") == "accepted":
        decision_id = str(latest.get("decision_id"))
        rows.append({
            "decision_id": decision_id,
            "summary": latest.get("summary"),
            "source": latest.get("source"),
        })
        seen.add(decision_id)
    for approval in manifest.get("approved") or []:
        decision_id = str(approval.get("approval_id"))
        if decision_id in seen:
            continue
        rows.append({
            "decision_id": decision_id,
            "summary": approval.get("subject"),
            "source": approval.get("source"),
        })
    return rows


def project_actions(manifest: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for priority in ("p0", "p1", "p2"):
        for action in (manifest.get("next_actions") or {}).get(priority, []):
            rows.append({
                "priority": priority,
                "action_id": action.get("action_id"),
                "action": action.get("action"),
                "status": action.get("status"),
                "requires_human_approval": action.get("requires_human_approval"),
                "blocked_by": action.get("blocked_by", []),
                "source": action.get("source"),
            })
    return rows


def snapshot_payload(
    workspace: Path,
    manifest_path: Path,
    manifest: dict[str, Any],
    main_commit: str,
    as_of: date,
    resolver,
) -> dict[str, Any]:
    freshness, _ = resolver.evaluate_freshness(manifest_path, manifest, workspace, as_of)
    effective = freshness.get("effective_freshness_status", freshness.get("effective_status"))
    payload = {
        "snapshot_contract": "chatgpt-project-context-v1",
        "snapshot_authority": "generated_read_only_not_truth_source",
        "project_id": manifest["project_id"],
        "current_main_commit": main_commit,
        "generated_as_of": as_of.isoformat(),
        "state_as_of": freshness.get("state_as_of"),
        "effective_freshness_status": effective,
        "lifecycle_stage": manifest["lifecycle_stage"],
        "accepted_decisions": accepted_decisions(manifest),
        "blockers": [
            {
                "blocker_id": item.get("blocker_id"),
                "summary": item.get("summary"),
                "status": item.get("status"),
                "source": item.get("source"),
            }
            for item in manifest.get("blocking_items") or []
        ],
        "next_actions": project_actions(manifest),
        "required_github_source_paths": required_source_paths(
            workspace, manifest_path, manifest, resolver
        ),
    }
    if set(payload) != SNAPSHOT_FIELDS:
        raise RuntimeError("CHATGPT_SNAPSHOT_FIELD_CONTRACT_VIOLATION")
    return payload


def snapshot_text(payload: dict[str, Any]) -> str:
    return "---\n" + yaml.safe_dump(payload, allow_unicode=True, sort_keys=False) + "---\n"


def build_outputs(workspace: Path, main_commit: str, as_of: date) -> tuple[str, dict[Path, str]]:
    if not re.fullmatch(r"[0-9a-f]{40}", main_commit) or not git_commit_exists(workspace, main_commit):
        raise RuntimeError(f"INVALID_MAIN_COMMIT:{main_commit}")
    resolver = load_resolver()
    snapshots: dict[Path, str] = {}
    index_projects: list[dict[str, str]] = []
    for manifest_path in sorted((workspace / "projects").glob("*/project.yaml")):
        manifest = load_yaml(manifest_path)
        if manifest.get("status") != "active":
            continue
        relative = Path("projects") / manifest["project_id"] / "chatgpt-context.md"
        payload = snapshot_payload(workspace, manifest_path, manifest, main_commit, as_of, resolver)
        snapshots[workspace / relative] = snapshot_text(payload)
        index_projects.append({
            "project_id": manifest["project_id"],
            "manifest": manifest_path.relative_to(workspace).as_posix(),
            "snapshot": relative.as_posix(),
        })
    index = {
        "contract": "chatgpt-context-index-v1",
        "snapshot_authority": "generated_read_only_not_truth_source",
        "current_main_commit": main_commit,
        "generated_as_of": as_of.isoformat(),
        "truth_precedence": [
            "github_product_knowledge_project_memory_decision",
            "chatgpt_snapshot",
            "chat_history_or_memory",
        ],
        "projects": index_projects,
    }
    return yaml.safe_dump(index, allow_unicode=True, sort_keys=False), snapshots


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workspace", default=str(ROOT))
    parser.add_argument("--main-commit")
    parser.add_argument("--as-of")
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    workspace = Path(args.workspace).resolve()
    index_path = workspace / "chatgpt/context-index.yaml"
    try:
        if args.check:
            index = load_yaml(index_path)
            main_commit = str(index["current_main_commit"])
            as_of = date.fromisoformat(str(index["generated_as_of"]))
        else:
            if not args.main_commit or not args.as_of:
                raise RuntimeError("MAIN_COMMIT_AND_AS_OF_REQUIRED_FOR_GENERATION")
            main_commit = args.main_commit
            as_of = date.fromisoformat(args.as_of)
        index_text, snapshots = build_outputs(workspace, main_commit, as_of)
        if args.check:
            errors = []
            if index_path.read_text(encoding="utf-8") != index_text:
                errors.append("CHATGPT_CONTEXT_INDEX_OUT_OF_DATE")
            for path, expected in snapshots.items():
                if not path.is_file() or path.read_text(encoding="utf-8") != expected:
                    errors.append(f"CHATGPT_CONTEXT_SNAPSHOT_OUT_OF_DATE:{path.relative_to(workspace)}")
            if errors:
                print("\n".join(errors))
                return 1
            print("CHATGPT_CONTEXT_REPRODUCIBLE")
            return 0
        index_path.parent.mkdir(parents=True, exist_ok=True)
        index_path.write_text(index_text, encoding="utf-8")
        for path, content in snapshots.items():
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding="utf-8")
        print(f"wrote {index_path.relative_to(workspace)} and {len(snapshots)} project snapshots")
        return 0
    except (OSError, KeyError, RuntimeError, ValueError, yaml.YAMLError) as exc:
        print(f"CHATGPT_CONTEXT_ERROR:{exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
