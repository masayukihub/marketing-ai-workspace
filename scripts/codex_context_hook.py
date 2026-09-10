#!/usr/bin/env python3
"""Deterministic, local-only Codex lifecycle checkpoint hook."""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
import re
import subprocess
import sys
import uuid
from pathlib import Path
from typing import Any

import yaml


ROOT = Path(__file__).resolve().parents[1]
EVENTS = {"pre-compact", "post-compact", "session-end", "compact-failed"}
SECRET_ASSIGNMENT = re.compile(
    r"(?i)\b(api[_-]?key|access[_-]?token|refresh[_-]?token|client[_-]?secret|"
    r"password|cookie|authorization)\b(\s*[:=]\s*)([^\s,;\]}]+)"
)
BEARER = re.compile(r"(?i)\bBearer\s+[A-Za-z0-9._~+\-/=]{12,}")
KNOWN_TOKEN = re.compile(r"\b(?:sk|ghp|github_pat|xox[baprs]|ya29)[-_][A-Za-z0-9._-]{10,}\b", re.I)


def redact(value: str) -> str:
    value = SECRET_ASSIGNMENT.sub(lambda m: f"{m.group(1)}{m.group(2)}<REDACTED>", value)
    value = BEARER.sub("Bearer <REDACTED>", value)
    return KNOWN_TOKEN.sub("<REDACTED_TOKEN>", value)


def run_git(workspace: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", *args],
        cwd=workspace,
        text=True,
        capture_output=True,
        timeout=0.6,
        check=False,
    )
    return result.stdout.strip() if result.returncode == 0 else "unknown"


def read_event_payload() -> dict[str, Any]:
    if sys.stdin.isatty():
        return {}
    raw = sys.stdin.read(65536)
    if not raw.strip():
        return {}
    try:
        value = json.loads(raw)
        return value if isinstance(value, dict) else {}
    except json.JSONDecodeError:
        return {}


def safe_workspace() -> Path:
    override = os.environ.get("CODEX_CONTEXT_WORKSPACE")
    candidate = Path(override).resolve() if override else ROOT
    if not (candidate / ".git").exists():
        return ROOT
    return candidate


def project_from_payload(workspace: Path, payload: dict[str, Any]) -> str:
    explicit = os.environ.get("CODEX_CONTEXT_PROJECT") or payload.get("project_id")
    if isinstance(explicit, str) and re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", explicit):
        if (workspace / "projects" / explicit / "project.yaml").is_file():
            return explicit
    cwd = payload.get("cwd")
    if isinstance(cwd, str):
        parts = Path(cwd).parts
        if "projects" in parts:
            index = parts.index("projects")
            if index + 1 < len(parts):
                candidate = parts[index + 1]
                if (workspace / "projects" / candidate / "project.yaml").is_file():
                    return candidate
    return "general"


def next_project_action(workspace: Path, project_id: str) -> str | None:
    if project_id == "general":
        return None
    path = workspace / "projects" / project_id / "project.yaml"
    try:
        manifest = yaml.safe_load(path.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError):
        return None
    for priority in ("p0", "p1", "p2"):
        for action in manifest.get("next_actions", {}).get(priority, []):
            if action.get("status") not in {"approved", "superseded"}:
                return redact(str(action.get("action") or action.get("action_id")))[:800]
    return None


def latest_relative(root: Path, workspace: Path, pattern: str) -> str | None:
    candidates = sorted(root.glob(pattern), key=lambda path: path.stat().st_mtime, reverse=True)
    if not candidates:
        return None
    try:
        return candidates[0].resolve().relative_to(workspace.resolve()).as_posix()
    except ValueError:
        return None


def checkpoint(event: str) -> None:
    workspace = safe_workspace()
    payload = read_event_payload()
    project_id = project_from_payload(workspace, payload)
    status = run_git(workspace, "status", "--short").splitlines()[:200]
    session_value = payload.get("session_id") or payload.get("sessionId") or payload.get("thread_id") or "unknown"
    session_hash = hashlib.sha256(str(session_value).encode("utf-8")).hexdigest()[:12] if session_value != "unknown" else "unknown"
    manual_root = workspace / "private-runtime/thread-handoffs" / project_id
    automatic_root = workspace / "private-runtime/thread-handoffs/_automatic"
    latest_manual = latest_relative(manual_root, workspace, "*.yaml")
    latest_test = latest_relative(workspace / "private-runtime/context-runs", workspace, "*.context.log")
    next_action = next_project_action(workspace, project_id)
    now = dt.datetime.now(dt.timezone.utc)
    data = {
        "checkpoint_version": "1.0",
        "created_at": now.isoformat().replace("+00:00", "Z"),
        "event": event,
        "session_id_redacted": session_hash,
        "repository": {
            "branch": run_git(workspace, "branch", "--show-current"),
            "head_commit": run_git(workspace, "rev-parse", "HEAD"),
            "git_status": [redact(line)[:500] for line in status],
            "has_uncommitted_changes": bool(status),
        },
        "project_id": project_id,
        "existing_handoff": latest_manual,
        "handoff_present": latest_manual is not None,
        "latest_test_log": latest_test,
        "tests_complete": None,
        "next_action": next_action,
        "unresolved_next_action": next_action is not None,
        "payload_persisted": False,
        "network_used": False,
        "business_files_modified_by_hook": False,
    }
    automatic_root.mkdir(parents=True, exist_ok=True)
    filename = f"{now.strftime('%Y%m%dT%H%M%S%fZ')}-{event}-{uuid.uuid4().hex[:8]}.yaml"
    (automatic_root / filename).write_text(
        yaml.safe_dump(data, allow_unicode=True, sort_keys=False), encoding="utf-8"
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--event", required=True, choices=sorted(EVENTS))
    args = parser.parse_args()
    try:
        checkpoint(args.event)
    except Exception as exc:  # Hooks must never block code preservation or session exit.
        sys.stderr.write(f"context checkpoint warning: {redact(type(exc).__name__)}\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
