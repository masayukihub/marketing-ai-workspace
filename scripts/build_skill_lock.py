#!/usr/bin/env python3
"""Refresh deterministic repository tree hashes in runtime/skill-lock.json."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from runtime_contract import (
    RuntimeContractError,
    git_commit_exists,
    git_head,
    load_skill_lock,
    repository_file_hashes,
    tree_hash,
)


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_LOCK = ROOT / "runtime/skill-lock.json"


def refreshed_lock(workspace: Path, lock_path: Path, commit: str) -> dict:
    payload = load_skill_lock(lock_path)
    if not git_commit_exists(workspace, commit):
        raise RuntimeContractError(f"LAST_VERIFIED_COMMIT_NOT_FOUND:{commit}")
    for skill in payload["skills"]:
        hashes = repository_file_hashes(workspace, skill["repository_path"])
        missing = [item for item in skill["required_runtime_files"] if item not in hashes]
        if missing:
            raise RuntimeContractError(f"REQUIRED_RUNTIME_FILES_MISSING:{skill['name']}:{','.join(missing)}")
        skill["repository_tree_hash"] = tree_hash(hashes)
        skill["last_verified_commit"] = commit
    return payload


def serialized(payload: dict) -> str:
    return json.dumps(payload, ensure_ascii=False, indent=2) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workspace", default=str(ROOT))
    parser.add_argument("--lock", default=str(DEFAULT_LOCK))
    parser.add_argument("--commit")
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    workspace = Path(args.workspace).resolve()
    lock_path = Path(args.lock).resolve()
    try:
        if args.check and not args.commit:
            existing = load_skill_lock(lock_path)
            commits = {item["last_verified_commit"] for item in existing["skills"]}
            if len(commits) != 1:
                raise RuntimeContractError("SKILL_LOCK_LAST_VERIFIED_COMMIT_INCONSISTENT")
            commit = next(iter(commits))
        else:
            commit = args.commit or git_head(workspace)
        output = serialized(refreshed_lock(workspace, lock_path, commit))
        if args.check:
            if lock_path.read_text(encoding="utf-8") != output:
                print("SKILL_LOCK_OUT_OF_DATE")
                return 1
            print("SKILL_LOCK_REPRODUCIBLE")
            return 0
        if args.write:
            lock_path.write_text(output, encoding="utf-8")
            print(f"wrote {lock_path.relative_to(workspace)}")
        else:
            print(output, end="")
        return 0
    except (OSError, RuntimeContractError) as exc:
        print(f"SKILL_LOCK_ERROR:{exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
