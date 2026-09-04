#!/usr/bin/env python3
"""Verify repository Skill Lock and optional Codex global installation mirrors."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from runtime_contract import (
    RuntimeContractError,
    compare_hashes,
    directory_file_hashes,
    load_skill_lock,
    repository_file_hashes,
    resolve_codex_home,
    tree_hash,
)


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_LOCK = ROOT / "runtime/skill-lock.json"
VALID_STATUSES = {
    "RUNTIME_IN_SYNC",
    "RUNTIME_DRIFT",
    "MIRROR_MISSING",
    "REPOSITORY_RUNTIME_MISSING",
}


def verify_runtime(
    workspace: Path,
    lock_path: Path,
    codex_home: Path,
    repository_only: bool = False,
    selected_skills: set[str] | None = None,
) -> dict[str, Any]:
    workspace = workspace.resolve()
    lock = load_skill_lock(lock_path)
    rows: list[dict[str, Any]] = []
    for skill in lock["skills"]:
        name = skill["name"]
        if selected_skills and name not in selected_skills:
            continue
        repository_hashes: dict[str, str] = {}
        mismatches: list[dict[str, str]] = []
        try:
            repository_hashes = repository_file_hashes(workspace, skill["repository_path"])
        except RuntimeContractError as exc:
            rows.append({
                "name": name,
                "role": skill["role"],
                "status": "REPOSITORY_RUNTIME_MISSING",
                "repository_path": skill["repository_path"],
                "repository_tree_hash_expected": skill["repository_tree_hash"],
                "repository_tree_hash_actual": None,
                "global_skill_path": f"$CODEX_HOME/skills/{name}",
                "global_tree_hash": None,
                "mismatches": [{"reason": str(exc)}],
            })
            continue

        repository_tree = tree_hash(repository_hashes)
        for required in skill["required_runtime_files"]:
            if required not in repository_hashes:
                mismatches.append({"path": required, "reason": "required_runtime_file_missing"})
        if repository_tree != skill["repository_tree_hash"]:
            mismatches.append({
                "reason": "repository_tree_hash_mismatch",
                "expected": skill["repository_tree_hash"],
                "actual": repository_tree,
            })

        global_tree: str | None = None
        if repository_only or not skill.get("mirror_required", False):
            status = "RUNTIME_DRIFT" if mismatches else "RUNTIME_IN_SYNC"
        else:
            global_root = codex_home / "skills" / name
            global_hashes = directory_file_hashes(global_root)
            if not global_hashes:
                status = "RUNTIME_DRIFT" if mismatches else "MIRROR_MISSING"
            else:
                global_tree = tree_hash(global_hashes)
                mismatches.extend(compare_hashes(repository_hashes, global_hashes))
                status = "RUNTIME_DRIFT" if mismatches else "RUNTIME_IN_SYNC"

        rows.append({
            "name": name,
            "role": skill["role"],
            "status": status,
            "repository_path": skill["repository_path"],
            "repository_tree_hash_expected": skill["repository_tree_hash"],
            "repository_tree_hash_actual": repository_tree,
            "global_skill_path": f"$CODEX_HOME/skills/{name}",
            "global_tree_hash": global_tree,
            "mismatches": mismatches,
        })

    if selected_skills:
        found = {row["name"] for row in rows}
        missing = sorted(selected_skills - found)
        if missing:
            raise RuntimeContractError(f"SKILL_NOT_IN_LOCK:{','.join(missing)}")
    statuses = {row["status"] for row in rows}
    if "REPOSITORY_RUNTIME_MISSING" in statuses:
        overall = "REPOSITORY_RUNTIME_MISSING"
    elif "RUNTIME_DRIFT" in statuses:
        overall = "RUNTIME_DRIFT"
    elif "MIRROR_MISSING" in statuses:
        overall = "MIRROR_MISSING"
    else:
        overall = "RUNTIME_IN_SYNC"
    assert overall in VALID_STATUSES
    return {
        "status": overall,
        "verification_scope": "repository_only" if repository_only else "repository_and_global_mirror",
        "execution_source": "repository",
        "global_auto_use": False,
        "lock_path": lock_path.relative_to(workspace).as_posix() if lock_path.is_relative_to(workspace) else str(lock_path),
        "skills": rows,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workspace", default=str(ROOT))
    parser.add_argument("--lock", default=str(DEFAULT_LOCK))
    parser.add_argument("--codex-home")
    parser.add_argument("--repository-only", action="store_true")
    parser.add_argument("--skill", action="append", default=[])
    args = parser.parse_args()
    try:
        result = verify_runtime(
            Path(args.workspace),
            Path(args.lock),
            resolve_codex_home(args.codex_home),
            repository_only=args.repository_only,
            selected_skills=set(args.skill) or None,
        )
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0 if result["status"] == "RUNTIME_IN_SYNC" else 2
    except (OSError, RuntimeContractError) as exc:
        print(json.dumps({
            "status": "REPOSITORY_RUNTIME_MISSING",
            "execution_source": "repository",
            "global_auto_use": False,
            "error": str(exc),
        }, ensure_ascii=False, indent=2))
        return 2


if __name__ == "__main__":
    sys.exit(main())
