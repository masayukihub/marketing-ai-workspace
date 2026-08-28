#!/usr/bin/env python3
"""Plan, verify, or apply one-way repository-to-Codex Skill mirror synchronization."""

from __future__ import annotations

import argparse
import json
import shutil
import sys
import uuid
from pathlib import Path
from typing import Any

from runtime_contract import (
    RuntimeContractError,
    compare_hashes,
    directory_file_hashes,
    git_branch,
    git_is_clean,
    load_skill_lock,
    repository_file_hashes,
    resolve_codex_home,
    tree_hash,
)
from verify_codex_runtime import verify_runtime


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_LOCK = ROOT / "runtime/skill-lock.json"


def sync_preconditions(workspace: Path, lock: dict[str, Any]) -> list[str]:
    reasons: list[str] = []
    if git_branch(workspace) != "main":
        reasons.append("SYNC_REQUIRES_MAIN_BRANCH")
    if not git_is_clean(workspace):
        reasons.append("SYNC_REQUIRES_CLEAN_WORKTREE")
    return reasons


def build_plan(workspace: Path, lock: dict[str, Any], codex_home: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for skill in lock["skills"]:
        if not skill.get("mirror_required", False):
            continue
        repository_hashes = repository_file_hashes(workspace, skill["repository_path"])
        target = codex_home / "skills" / skill["name"]
        mirror_hashes = directory_file_hashes(target)
        mismatches = compare_hashes(repository_hashes, mirror_hashes)
        rows.append({
            "name": skill["name"],
            "source": skill["repository_path"],
            "target": f"$CODEX_HOME/skills/{skill['name']}",
            "repository_tree_hash": tree_hash(repository_hashes),
            "global_tree_hash": tree_hash(mirror_hashes) if mirror_hashes else None,
            "status_before": "RUNTIME_IN_SYNC" if not mismatches else (
                "MIRROR_MISSING" if not mirror_hashes else "RUNTIME_DRIFT"
            ),
            "files_to_copy": sorted(repository_hashes),
            "mismatches": mismatches,
        })
    return rows


def apply_skill(workspace: Path, codex_home: Path, skill: dict[str, Any]) -> None:
    name = skill["name"]
    source_root = (workspace / skill["repository_path"]).resolve()
    mirror_parent = (codex_home / "skills").resolve()
    mirror_parent.mkdir(parents=True, exist_ok=True)
    target = (mirror_parent / name).resolve()
    if target.parent != mirror_parent or target.name != name or target.is_symlink():
        raise RuntimeContractError(f"UNSAFE_GLOBAL_MIRROR_TARGET:{name}")

    repository_hashes = repository_file_hashes(workspace, skill["repository_path"])
    token = uuid.uuid4().hex
    staging = mirror_parent / f".{name}.sync-{token}"
    backup = mirror_parent / f".{name}.backup-{token}"
    try:
        staging.mkdir()
        for relative in repository_hashes:
            source = source_root / relative
            destination = staging / relative
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, destination)
        staged_hashes = directory_file_hashes(staging)
        if compare_hashes(repository_hashes, staged_hashes):
            raise RuntimeContractError(f"STAGING_HASH_VERIFICATION_FAILED:{name}")
        if target.exists():
            target.rename(backup)
        staging.rename(target)
        if backup.exists():
            shutil.rmtree(backup)
    except Exception:
        if target.exists() and backup.exists():
            shutil.rmtree(target)
            backup.rename(target)
        elif backup.exists() and not target.exists():
            backup.rename(target)
        if staging.exists():
            shutil.rmtree(staging)
        raise


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workspace", default=str(ROOT))
    parser.add_argument("--lock", default=str(DEFAULT_LOCK))
    parser.add_argument("--codex-home")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--dry-run", action="store_true")
    mode.add_argument("--verify-only", action="store_true")
    mode.add_argument("--apply", action="store_true")
    args = parser.parse_args()
    workspace = Path(args.workspace).resolve()
    lock_path = Path(args.lock).resolve()
    codex_home = resolve_codex_home(args.codex_home)
    try:
        if args.verify_only:
            result = verify_runtime(workspace, lock_path, codex_home)
            print(json.dumps(result, ensure_ascii=False, indent=2))
            return 0 if result["status"] == "RUNTIME_IN_SYNC" else 2

        lock = load_skill_lock(lock_path)
        plan = build_plan(workspace, lock, codex_home)
        reasons = sync_preconditions(workspace, lock)
        repository_verification = verify_runtime(
            workspace,
            lock_path,
            codex_home,
            repository_only=True,
        )
        if repository_verification["status"] != "RUNTIME_IN_SYNC":
            reasons.append("SYNC_REQUIRES_VALID_REPOSITORY_SKILL_LOCK")
        result: dict[str, Any] = {
            "status": "SYNC_DRY_RUN" if not args.apply else "SYNC_PENDING",
            "execution_source": "repository",
            "direction": "repository_to_global_only",
            "apply_allowed": not reasons,
            "blocking_reasons": reasons,
            "repository_verification": repository_verification,
            "skills": plan,
        }
        if not args.apply:
            print(json.dumps(result, ensure_ascii=False, indent=2))
            return 0
        if reasons:
            result["status"] = "SYNC_BLOCKED"
            print(json.dumps(result, ensure_ascii=False, indent=2))
            return 2

        for skill in lock["skills"]:
            if skill.get("mirror_required", False):
                apply_skill(workspace, codex_home, skill)
        verification = verify_runtime(workspace, lock_path, codex_home)
        result["status"] = "SYNC_APPLIED" if verification["status"] == "RUNTIME_IN_SYNC" else "SYNC_VERIFY_FAILED"
        result["verification"] = verification
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0 if result["status"] == "SYNC_APPLIED" else 2
    except (OSError, RuntimeContractError) as exc:
        print(json.dumps({
            "status": "SYNC_BLOCKED",
            "execution_source": "repository",
            "error": str(exc),
        }, ensure_ascii=False, indent=2))
        return 2


if __name__ == "__main__":
    sys.exit(main())
