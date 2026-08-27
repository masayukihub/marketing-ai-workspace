#!/usr/bin/env python3
"""Verify that an installed global Project Memory Skill mirrors the repository runtime."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from pathlib import Path
from typing import Any


DEFAULT_REPOSITORY_SKILL_ROOT = Path(__file__).resolve().parents[1]
RUNTIME_FILES = (
    "SKILL.md",
    "agents/openai.yaml",
    "references/governance.md",
    "references/integration.md",
    "scripts/project_memory.py",
)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def bundle_hash(file_hashes: dict[str, str]) -> str:
    digest = hashlib.sha256()
    for relative_path in sorted(file_hashes):
        digest.update(relative_path.encode("utf-8"))
        digest.update(b"\0")
        digest.update(file_hashes[relative_path].encode("ascii"))
        digest.update(b"\n")
    return digest.hexdigest()


def compare_mirror(repository_skill_root: Path, global_skill_root: Path) -> dict[str, Any]:
    repository_skill_root = repository_skill_root.resolve()
    global_skill_root = global_skill_root.resolve()
    repository_hashes: dict[str, str] = {}
    global_hashes: dict[str, str] = {}
    mismatches: list[dict[str, str]] = []

    for relative_path in RUNTIME_FILES:
        repository_path = repository_skill_root / relative_path
        global_path = global_skill_root / relative_path
        if not repository_path.is_file():
            mismatches.append({"path": relative_path, "reason": "repository_runtime_missing"})
            continue
        repository_hashes[relative_path] = sha256(repository_path)
        if not global_path.is_file():
            mismatches.append({"path": relative_path, "reason": "global_runtime_missing"})
            continue
        global_hashes[relative_path] = sha256(global_path)
        if repository_hashes[relative_path] != global_hashes[relative_path]:
            mismatches.append({
                "path": relative_path,
                "reason": "hash_mismatch",
                "repository_sha256": repository_hashes[relative_path],
                "global_sha256": global_hashes[relative_path],
            })

    status = "GLOBAL_SKILL_IN_SYNC" if not mismatches else "GLOBAL_SKILL_DRIFT"
    return {
        "status": status,
        "execution_source": "repository",
        "global_auto_use": False,
        "repository_skill_root": str(repository_skill_root),
        "global_skill_root": str(global_skill_root),
        "repository_bundle_sha256": bundle_hash(repository_hashes),
        "global_bundle_sha256": bundle_hash(global_hashes),
        "mismatches": mismatches,
    }


def default_global_skill_root() -> Path:
    codex_root = Path(os.environ.get("CODEX_HOME", Path.home() / ".codex"))
    return codex_root / "skills" / "project-memory-manager"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository-skill-root", default=str(DEFAULT_REPOSITORY_SKILL_ROOT))
    parser.add_argument("--global-skill-root", default=str(default_global_skill_root()))
    args = parser.parse_args()

    result = compare_mirror(
        Path(args.repository_skill_root).expanduser(),
        Path(args.global_skill_root).expanduser(),
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["status"] == "GLOBAL_SKILL_IN_SYNC" else 2


if __name__ == "__main__":
    sys.exit(main())
