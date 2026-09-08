#!/usr/bin/env python3
"""Plan or apply a reversible cleanup of duplicate Codex Skill discovery entries."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

import yaml

from runtime_contract import RuntimeContractError, git_branch, git_is_clean, resolve_codex_home
from verify_codex_runtime import verify_runtime


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SURFACE = ROOT / "runtime/skill-surface.yaml"
DEFAULT_LOCK = ROOT / "runtime/skill-lock.json"
DEFAULT_JOURNAL_NAME = ".jp-commerce-skill-surface-journal.json"
SAFE_NAME = re.compile(r"^[a-z0-9][a-z0-9-]{0,63}$")
VALID_SCOPES = {"codex_global", "project"}


class SurfaceError(RuntimeError):
    """Raised when the Skill surface cannot be changed safely."""


def path_present(path: Path) -> bool:
    return path.exists() or path.is_symlink()


def load_surface(path: Path) -> dict[str, Any]:
    try:
        payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError) as exc:
        raise SurfaceError(f"SKILL_SURFACE_READ_ERROR:{path}:{exc}") from exc
    if not isinstance(payload, dict) or payload.get("schema_version") != "1.0":
        raise SurfaceError("UNSUPPORTED_SKILL_SURFACE_SCHEMA")
    user_entries = payload.get("user_entries")
    internalized = payload.get("internalized_entries")
    if not isinstance(user_entries, list) or not user_entries:
        raise SurfaceError("SKILL_SURFACE_REQUIRES_USER_ENTRIES")
    if not isinstance(internalized, list):
        raise SurfaceError("SKILL_SURFACE_REQUIRES_INTERNALIZED_ENTRIES")
    user_ids = []
    for item in user_entries:
        skill_id = item.get("skill_id") if isinstance(item, dict) else None
        if not isinstance(skill_id, str) or not SAFE_NAME.fullmatch(skill_id):
            raise SurfaceError(f"INVALID_USER_ENTRY:{skill_id}")
        user_ids.append(skill_id)
    if len(user_ids) != len(set(user_ids)):
        raise SurfaceError("DUPLICATE_USER_ENTRY")
    internal_names = []
    for item in internalized:
        if not isinstance(item, dict):
            raise SurfaceError("INVALID_INTERNALIZED_ENTRY")
        name = item.get("directory_name")
        canonical = item.get("canonical_entry")
        scopes = item.get("scopes")
        if not isinstance(name, str) or not SAFE_NAME.fullmatch(name):
            raise SurfaceError(f"INVALID_INTERNAL_DIRECTORY:{name}")
        if canonical not in user_ids:
            raise SurfaceError(f"UNKNOWN_CANONICAL_ENTRY:{name}:{canonical}")
        if not isinstance(scopes, list) or not scopes or set(scopes) - VALID_SCOPES:
            raise SurfaceError(f"INVALID_INTERNAL_SCOPES:{name}")
        internal_names.append(name)
    if len(internal_names) != len(set(internal_names)):
        raise SurfaceError("DUPLICATE_INTERNAL_DIRECTORY")
    overlap = set(user_ids) & set(internal_names)
    if overlap:
        raise SurfaceError(f"USER_ENTRY_CANNOT_BE_INTERNALIZED:{','.join(sorted(overlap))}")
    return payload


def roots_for_scope(codex_home: Path, project_root: Path | None, scope: str) -> tuple[Path, Path] | None:
    if scope == "codex_global":
        return codex_home / "skills", codex_home / "internal-skills"
    if project_root is None:
        return None
    return project_root / ".agents/skills", project_root / ".agents/internal-skills"


def build_plan(
    surface: dict[str, Any], codex_home: Path, project_root: Path | None
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for entry in surface["internalized_entries"]:
        for scope in entry["scopes"]:
            roots = roots_for_scope(codex_home, project_root, scope)
            if roots is None:
                rows.append({
                    "directory_name": entry["directory_name"],
                    "canonical_entry": entry["canonical_entry"],
                    "internal_role": entry["internal_role"],
                    "scope": scope,
                    "status": "PROJECT_ROOT_NOT_PROVIDED",
                    "action": "NONE",
                })
                continue
            discovery_root, internal_root = roots
            discovery = discovery_root / entry["directory_name"]
            internal = internal_root / entry["directory_name"]
            source, target = discovery, internal
            source_exists = path_present(source)
            target_exists = path_present(target)
            if source_exists and target_exists:
                status = "TARGET_CONFLICT"
                action = "BLOCK"
            elif source_exists:
                status = "READY_TO_INTERNALIZE"
                action = "MOVE"
            elif target_exists:
                status = "ALREADY_INTERNAL"
                action = "NONE"
            else:
                status = "NOT_INSTALLED"
                action = "NONE"
            rows.append({
                "directory_name": entry["directory_name"],
                "declared_skill_name": entry["declared_skill_name"],
                "canonical_entry": entry["canonical_entry"],
                "internal_role": entry["internal_role"],
                "scope": scope,
                "source": str(source),
                "target": str(target),
                "status": status,
                "action": action,
            })
    return rows


def load_journal(path: Path) -> dict[str, Any] | None:
    if not path_present(path):
        return None
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise SurfaceError(f"SKILL_SURFACE_JOURNAL_READ_ERROR:{path}:{exc}") from exc
    if not isinstance(payload, dict) or payload.get("journal_version") != "1.0":
        raise SurfaceError("UNSUPPORTED_SKILL_SURFACE_JOURNAL")
    if payload.get("status") not in {"APPLIED", "RESTORED"}:
        raise SurfaceError("INVALID_SKILL_SURFACE_JOURNAL_STATUS")
    if not isinstance(payload.get("operations"), list):
        raise SurfaceError("INVALID_SKILL_SURFACE_JOURNAL_OPERATIONS")
    return payload


def save_journal(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.tmp")
    temporary.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    temporary.replace(path)


def journal_for_moves(rows: list[dict[str, Any]]) -> dict[str, Any]:
    operations = []
    for row in rows:
        if row.get("action") != "MOVE":
            continue
        operations.append({
            "directory_name": row["directory_name"],
            "scope": row["scope"],
            "source": row["source"],
            "target": row["target"],
        })
    return {
        "journal_version": "1.0",
        "surface_id": "jp-commerce-unified-skill-surface",
        "status": "APPLIED",
        "operations": operations,
    }


def build_restore_plan(
    surface: dict[str, Any],
    codex_home: Path,
    project_root: Path | None,
    journal: dict[str, Any],
) -> list[dict[str, Any]]:
    expected = {
        (row["scope"], row["directory_name"]): row
        for row in build_plan(surface, codex_home, project_root)
        if "source" in row
    }
    rows: list[dict[str, Any]] = []
    seen = set()
    for operation in journal["operations"]:
        if not isinstance(operation, dict):
            raise SurfaceError("INVALID_SKILL_SURFACE_JOURNAL_OPERATION")
        key = (operation.get("scope"), operation.get("directory_name"))
        if key in seen:
            raise SurfaceError(f"DUPLICATE_SKILL_SURFACE_JOURNAL_OPERATION:{key}")
        seen.add(key)
        base = expected.get(key)
        if base is None:
            raise SurfaceError(f"UNKNOWN_SKILL_SURFACE_JOURNAL_OPERATION:{key}")
        if operation.get("source") != base["source"] or operation.get("target") != base["target"]:
            raise SurfaceError(f"SKILL_SURFACE_JOURNAL_PATH_MISMATCH:{key}")
        source = Path(operation["target"])
        target = Path(operation["source"])
        source_exists = path_present(source)
        target_exists = path_present(target)
        if source_exists and target_exists:
            status, action = "TARGET_CONFLICT", "BLOCK"
        elif source_exists:
            status, action = "READY_TO_RESTORE", "MOVE"
        elif target_exists:
            status, action = "ALREADY_RESTORED", "NONE"
        else:
            status, action = "NOT_INSTALLED", "NONE"
        rows.append({
            **base,
            "source": str(source),
            "target": str(target),
            "status": status,
            "action": action,
        })
    return rows


def reversed_move_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            **row,
            "source": row["target"],
            "target": row["source"],
            "status": "READY_TO_ROLL_BACK",
            "action": "MOVE",
        }
        for row in rows
        if row.get("action") == "MOVE"
    ]


def user_entry_check(surface: dict[str, Any], codex_home: Path) -> list[str]:
    missing = []
    for entry in surface["user_entries"]:
        path = codex_home / "skills" / entry["skill_id"]
        if not path_present(path):
            missing.append(entry["skill_id"])
    return missing


def apply_moves(rows: list[dict[str, Any]]) -> int:
    conflicts = [row for row in rows if row["status"] == "TARGET_CONFLICT"]
    if conflicts:
        names = ",".join(f"{row['scope']}:{row['directory_name']}" for row in conflicts)
        raise SurfaceError(f"INTERNAL_TARGET_CONFLICT:{names}")
    moved_pairs: list[tuple[Path, Path]] = []
    try:
        for row in rows:
            if row["action"] != "MOVE":
                continue
            source = Path(row["source"])
            target = Path(row["target"])
            target.parent.mkdir(parents=True, exist_ok=True)
            source.rename(target)
            moved_pairs.append((source, target))
    except OSError as exc:
        rollback_failures = []
        for source, target in reversed(moved_pairs):
            try:
                target.rename(source)
            except OSError as rollback_exc:
                rollback_failures.append(f"{target}:{rollback_exc}")
        if rollback_failures:
            raise SurfaceError(
                "SURFACE_MOVE_PARTIAL_ROLLBACK_FAILED:" + "|".join(rollback_failures)
            ) from exc
        raise SurfaceError(f"SURFACE_MOVE_ROLLED_BACK:{exc}") from exc
    return len(moved_pairs)


def apply_preconditions(workspace: Path, lock_path: Path, codex_home: Path) -> list[str]:
    reasons = []
    if git_branch(workspace) != "main":
        reasons.append("SURFACE_APPLY_REQUIRES_MAIN_BRANCH")
    if not git_is_clean(workspace):
        reasons.append("SURFACE_APPLY_REQUIRES_CLEAN_WORKTREE")
    repository = verify_runtime(workspace, lock_path, codex_home, repository_only=True)
    if repository["status"] != "RUNTIME_IN_SYNC":
        reasons.append("SURFACE_APPLY_REQUIRES_VALID_REPOSITORY_RUNTIME")
    global_runtime = verify_runtime(workspace, lock_path, codex_home)
    if global_runtime["status"] != "RUNTIME_IN_SYNC":
        reasons.append("SURFACE_APPLY_REQUIRES_SYNCED_GLOBAL_RUNTIME")
    return reasons


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workspace", default=str(ROOT))
    parser.add_argument("--surface", default=str(DEFAULT_SURFACE))
    parser.add_argument("--lock", default=str(DEFAULT_LOCK))
    parser.add_argument("--codex-home")
    parser.add_argument("--project-root")
    parser.add_argument("--journal")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--apply", action="store_true")
    mode.add_argument("--restore", action="store_true")
    args = parser.parse_args()

    workspace = Path(args.workspace).resolve()
    codex_home = resolve_codex_home(args.codex_home)
    project_root = Path(args.project_root).resolve() if args.project_root else None
    surface_path = Path(args.surface).resolve()
    lock_path = Path(args.lock).resolve()
    journal_path = (
        Path(args.journal).resolve()
        if args.journal
        else codex_home / "internal-skills" / DEFAULT_JOURNAL_NAME
    )
    try:
        surface = load_surface(surface_path)
        restore = bool(args.restore)
        journal = load_journal(journal_path)
        rows = (
            build_restore_plan(surface, codex_home, project_root, journal)
            if restore and journal is not None
            else ([] if restore else build_plan(surface, codex_home, project_root))
        )
        missing_entries = user_entry_check(surface, codex_home)
        reasons = apply_preconditions(workspace, lock_path, codex_home)
        if missing_entries:
            reasons.append("CANONICAL_USER_ENTRIES_MISSING:" + ",".join(missing_entries))
        if restore and journal is None:
            reasons.append("SURFACE_RESTORE_JOURNAL_MISSING")
        if restore and journal is not None and journal["status"] != "APPLIED":
            reasons.append("SURFACE_RESTORE_JOURNAL_NOT_ACTIVE")
        if not restore and journal is not None and journal["status"] == "APPLIED" and any(
            row["action"] == "MOVE" for row in rows
        ):
            reasons.append("SURFACE_APPLY_JOURNAL_ALREADY_ACTIVE")
        if any(row["status"] == "TARGET_CONFLICT" for row in rows):
            reasons.append("INTERNAL_TARGET_CONFLICT")
        result: dict[str, Any] = {
            "status": "SURFACE_PLAN",
            "mode": "RESTORE" if restore else ("APPLY" if args.apply else "PLAN_ONLY"),
            "runtime_authority": surface["runtime_authority"],
            "user_entries": surface["user_entries"],
            "missing_user_entries": missing_entries,
            "project_root_included": project_root is not None,
            "journal": str(journal_path),
            "journal_status": journal["status"] if journal is not None else "MISSING",
            "apply_allowed": not reasons,
            "blocking_reasons": reasons,
            "operations": rows,
        }
        if not (args.apply or args.restore):
            print(json.dumps(result, ensure_ascii=False, indent=2))
            return 0
        if reasons:
            result["status"] = "SURFACE_CHANGE_BLOCKED"
            print(json.dumps(result, ensure_ascii=False, indent=2))
            return 2
        moved = apply_moves(rows)
        try:
            if restore:
                assert journal is not None
                journal["status"] = "RESTORED"
                save_journal(journal_path, journal)
            elif moved:
                save_journal(journal_path, journal_for_moves(rows))
        except (OSError, SurfaceError) as exc:
            apply_moves(reversed_move_rows(rows))
            raise SurfaceError(f"SURFACE_JOURNAL_WRITE_FAILED_AND_MOVES_ROLLED_BACK:{exc}") from exc
        result["status"] = "SURFACE_RESTORED" if restore else "SURFACE_INTERNALIZED"
        result["moved_entries"] = moved
        if restore:
            updated_journal = load_journal(journal_path)
            assert updated_journal is not None
            result["operations_after"] = build_restore_plan(
                surface, codex_home, project_root, updated_journal
            )
        else:
            result["operations_after"] = build_plan(surface, codex_home, project_root)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0
    except (OSError, RuntimeContractError, SurfaceError) as exc:
        print(json.dumps({
            "status": "SURFACE_CHANGE_BLOCKED",
            "runtime_authority": "repository",
            "error": str(exc),
        }, ensure_ascii=False, indent=2))
        return 2


if __name__ == "__main__":
    sys.exit(main())
