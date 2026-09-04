#!/usr/bin/env python3
"""Shared deterministic helpers for repository-owned Codex Skill runtimes."""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
from pathlib import Path
from typing import Any, Iterable


IGNORED_PARTS = {".git", ".pytest_cache", "__pycache__", "node_modules"}
IGNORED_SUFFIXES = {".pyc", ".pyo"}
PROHIBITED_NAMES = {
    ".env",
    ".env.local",
    "credentials.json",
    "token.json",
}
PROHIBITED_SUFFIXES = {".key", ".pem", ".p12"}


class RuntimeContractError(RuntimeError):
    """Raised when a runtime contract cannot be evaluated safely."""


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def tree_hash(file_hashes: dict[str, str]) -> str:
    digest = hashlib.sha256()
    for relative_path in sorted(file_hashes):
        digest.update(relative_path.encode("utf-8"))
        digest.update(b"\0")
        digest.update(file_hashes[relative_path].encode("ascii"))
        digest.update(b"\n")
    return digest.hexdigest()


def is_safe_runtime_file(relative_path: str) -> bool:
    path = Path(relative_path)
    if path.is_absolute() or ".." in path.parts:
        return False
    if any(part in IGNORED_PARTS or part == "private-runtime" for part in path.parts):
        return False
    if path.name.lower() in PROHIBITED_NAMES:
        return False
    if path.suffix.lower() in PROHIBITED_SUFFIXES | IGNORED_SUFFIXES:
        return False
    return True


def _git_tracked_paths(workspace: Path, repository_path: str) -> list[str]:
    result = subprocess.run(
        ["git", "ls-files", "-z", "--", repository_path],
        cwd=workspace,
        capture_output=True,
        check=False,
    )
    if result.returncode != 0:
        raise RuntimeContractError(result.stderr.decode("utf-8", errors="replace").strip())
    return [item.decode("utf-8") for item in result.stdout.split(b"\0") if item]


def repository_file_hashes(workspace: Path, repository_path: str) -> dict[str, str]:
    workspace = workspace.resolve()
    root = (workspace / repository_path).resolve()
    try:
        root.relative_to(workspace)
    except ValueError as exc:
        raise RuntimeContractError(f"REPOSITORY_PATH_OUTSIDE_WORKSPACE:{repository_path}") from exc
    if not root.is_dir():
        raise RuntimeContractError(f"REPOSITORY_RUNTIME_MISSING:{repository_path}")

    hashes: dict[str, str] = {}
    for tracked in _git_tracked_paths(workspace, repository_path):
        tracked_path = workspace / tracked
        if not tracked_path.is_file():
            continue
        relative = tracked_path.relative_to(root).as_posix()
        if not is_safe_runtime_file(relative):
            raise RuntimeContractError(f"PROHIBITED_RUNTIME_FILE:{repository_path}/{relative}")
        hashes[relative] = sha256_file(tracked_path)
    if not hashes:
        raise RuntimeContractError(f"REPOSITORY_RUNTIME_MISSING:{repository_path}")
    return dict(sorted(hashes.items()))


def directory_file_hashes(root: Path) -> dict[str, str]:
    if not root.is_dir():
        return {}
    hashes: dict[str, str] = {}
    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        relative = path.relative_to(root).as_posix()
        if not is_safe_runtime_file(relative):
            continue
        hashes[relative] = sha256_file(path)
    return hashes


def load_skill_lock(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise RuntimeContractError(f"SKILL_LOCK_READ_ERROR:{path}:{exc}") from exc
    if payload.get("lock_version") != "1.0":
        raise RuntimeContractError("UNSUPPORTED_SKILL_LOCK_VERSION")
    if payload.get("runtime_authority") != "repository":
        raise RuntimeContractError("INVALID_RUNTIME_AUTHORITY")
    skills = payload.get("skills")
    if not isinstance(skills, list) or not skills:
        raise RuntimeContractError("SKILL_LOCK_REQUIRES_SKILLS")
    names: set[str] = set()
    for item in skills:
        if not isinstance(item, dict):
            raise RuntimeContractError("SKILL_LOCK_ENTRY_MUST_BE_OBJECT")
        name = item.get("name")
        if not isinstance(name, str) or not name:
            raise RuntimeContractError("SKILL_LOCK_ENTRY_NAME_REQUIRED")
        if name in names:
            raise RuntimeContractError(f"DUPLICATE_SKILL_LOCK_ENTRY:{name}")
        names.add(name)
        expected_path = f"skills/{name}"
        if item.get("repository_path") != expected_path:
            raise RuntimeContractError(f"INVALID_REPOSITORY_SKILL_PATH:{name}")
        required = item.get("required_runtime_files")
        if not isinstance(required, list) or not required:
            raise RuntimeContractError(f"REQUIRED_RUNTIME_FILES_MISSING:{name}")
        if any(not isinstance(value, str) or not is_safe_runtime_file(value) for value in required):
            raise RuntimeContractError(f"INVALID_REQUIRED_RUNTIME_FILE:{name}")
    return payload


def resolve_codex_home(value: str | None = None) -> Path:
    if value:
        return Path(value).expanduser().resolve()
    configured = os.environ.get("CODEX_HOME")
    return Path(configured).expanduser().resolve() if configured else (Path.home() / ".codex").resolve()


def compare_hashes(expected: dict[str, str], actual: dict[str, str]) -> list[dict[str, str]]:
    mismatches: list[dict[str, str]] = []
    for relative in sorted(set(expected) | set(actual)):
        if relative not in actual:
            mismatches.append({"path": relative, "reason": "mirror_file_missing"})
        elif relative not in expected:
            mismatches.append({"path": relative, "reason": "unexpected_mirror_file"})
        elif expected[relative] != actual[relative]:
            mismatches.append({
                "path": relative,
                "reason": "hash_mismatch",
                "repository_sha256": expected[relative],
                "global_sha256": actual[relative],
            })
    return mismatches


def git_text(workspace: Path, args: Iterable[str]) -> str:
    result = subprocess.run(
        ["git", *args],
        cwd=workspace,
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        raise RuntimeContractError(result.stderr.strip() or "GIT_COMMAND_FAILED")
    return result.stdout.strip()


def git_is_clean(workspace: Path) -> bool:
    return not git_text(workspace, ["status", "--porcelain", "--untracked-files=all"])


def git_branch(workspace: Path) -> str:
    return git_text(workspace, ["branch", "--show-current"])


def git_head(workspace: Path) -> str:
    return git_text(workspace, ["rev-parse", "HEAD"])


def git_commit_exists(workspace: Path, commit: str) -> bool:
    result = subprocess.run(
        ["git", "cat-file", "-e", f"{commit}^{{commit}}"],
        cwd=workspace,
        capture_output=True,
        check=False,
    )
    return result.returncode == 0
