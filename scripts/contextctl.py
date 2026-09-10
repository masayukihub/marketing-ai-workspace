#!/usr/bin/env python3
"""File-backed context resilience controls for Marketing AI Workspace."""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import threading
import uuid
from pathlib import Path
from typing import Any, Iterable

import yaml


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_POLICY = ROOT / "runtime/context-policy.yaml"
DEFAULT_SCHEMA = ROOT / "schemas/thread-handoff.schema.yaml"
HANDOFF_ROOT = Path("private-runtime/thread-handoffs")
RUN_ROOT = Path("private-runtime/context-runs")
ALLOWED_HOOK_EVENTS = {"PreCompact", "PostCompact", "SessionEnd"}
FORBIDDEN_NETWORK_IMPORTS = {"aiohttp", "http.client", "requests", "socket", "urllib"}
SECRET_ASSIGNMENT = re.compile(
    r"(?i)\b(api[_-]?key|access[_-]?token|refresh[_-]?token|client[_-]?secret|"
    r"password|passwd|cookie|session[_-]?token|authorization)\b(\s*[:=]\s*)"
    r"([^\s,;\]}]+)"
)
BEARER = re.compile(r"(?i)\bBearer\s+[A-Za-z0-9._~+\-/=]{12,}")
KNOWN_TOKEN = re.compile(
    r"\b(?:sk|ghp|github_pat|xox[baprs]|ya29)[-_][A-Za-z0-9._-]{10,}\b",
    re.IGNORECASE,
)


class ContextError(RuntimeError):
    """Fail-closed context system error."""


def now_utc() -> dt.datetime:
    return dt.datetime.now(dt.timezone.utc)


def timestamp(value: dt.datetime | None = None) -> str:
    return (value or now_utc()).strftime("%Y%m%dT%H%M%SZ")


def safe_slug(value: str, fallback: str = "run") -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.casefold()).strip("-")
    return (slug or fallback)[:80]


def redact_text(value: str) -> str:
    value = SECRET_ASSIGNMENT.sub(lambda m: f"{m.group(1)}{m.group(2)}<REDACTED>", value)
    value = BEARER.sub("Bearer <REDACTED>", value)
    return KNOWN_TOKEN.sub("<REDACTED_TOKEN>", value)


def redact_data(value: Any) -> Any:
    if isinstance(value, str):
        return redact_text(value)
    if isinstance(value, list):
        return [redact_data(item) for item in value]
    if isinstance(value, dict):
        result = {}
        for key, item in value.items():
            if any(word in str(key).casefold() for word in ("token", "secret", "password", "cookie")):
                result[key] = "<REDACTED>"
            else:
                result[key] = redact_data(item)
        return result
    return value


def contains_unredacted_secret(value: str) -> bool:
    for match in SECRET_ASSIGNMENT.finditer(value):
        if "<REDACTED>" not in match.group(3):
            return True
    return bool(BEARER.search(value) or KNOWN_TOKEN.search(value))


def read_yaml(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise ContextError(f"MISSING_FILE:{path}")
    payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ContextError(f"INVALID_YAML_OBJECT:{path}")
    return payload


def run_command(
    args: list[str], cwd: Path, *, timeout_seconds: int = 10, check: bool = True
) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(
        args,
        cwd=cwd,
        text=True,
        capture_output=True,
        timeout=timeout_seconds,
        check=False,
    )
    if check and result.returncode:
        detail = redact_text((result.stderr or result.stdout).strip())[:1000]
        raise ContextError(f"COMMAND_FAILED:{args[0]}:{detail}")
    return result


def git_value(workspace: Path, *args: str, fallback: str = "unknown") -> str:
    result = run_command(["git", *args], workspace, check=False)
    value = result.stdout.strip()
    return value if result.returncode == 0 and value else fallback


def git_status(workspace: Path) -> list[str]:
    result = run_command(["git", "status", "--short"], workspace)
    return [redact_text(line)[:500] for line in result.stdout.splitlines()[:200]]


def changed_files_from_status(status: Iterable[str]) -> list[str]:
    paths = []
    for line in status:
        candidate = line[3:] if len(line) >= 4 else line
        if " -> " in candidate:
            candidate = candidate.split(" -> ", 1)[1]
        if candidate and candidate not in paths:
            paths.append(candidate)
    return paths[:200]


def relative_or_string(path: Path, workspace: Path) -> str:
    try:
        return path.resolve().relative_to(workspace.resolve()).as_posix()
    except ValueError:
        return redact_text(path.as_posix())


def resolve_source_pointer(manifest_path: Path, workspace: Path, pointer: Any) -> list[str]:
    values = pointer if isinstance(pointer, list) else [pointer]
    paths = []
    for value in values:
        if not isinstance(value, str) or not value.strip():
            continue
        candidate = (manifest_path.parent / value).resolve()
        rendered = relative_or_string(candidate, workspace)
        if rendered not in paths:
            paths.append(rendered)
    return paths


def resolve_project(workspace: Path, requested: str) -> tuple[Path | None, dict[str, Any] | None]:
    if requested.casefold() in {"general", "none", "non-project", "non_project"}:
        return None, None
    matches: list[tuple[Path, dict[str, Any]]] = []
    needle = requested.strip().casefold()
    for path in sorted((workspace / "projects").glob("*/project.yaml")):
        manifest = read_yaml(path)
        names = [manifest.get("project_id"), manifest.get("project_name"), *manifest.get("aliases", [])]
        if any(isinstance(name, str) and name.casefold() == needle for name in names):
            matches.append((path, manifest))
    if not matches:
        raise ContextError(f"PROJECT_NOT_FOUND:{requested}")
    if len(matches) > 1:
        raise ContextError(f"PROJECT_AMBIGUOUS:{requested}")
    return matches[0]


def parse_date(value: Any) -> dt.date | None:
    if isinstance(value, dt.datetime):
        return value.date()
    if isinstance(value, dt.date):
        return value
    if isinstance(value, str):
        try:
            return dt.date.fromisoformat(value[:10])
        except ValueError:
            return None
    return None


def effective_freshness(workspace: Path, manifest: dict[str, Any] | None) -> str:
    if manifest is None:
        return "not_applicable"
    state_date = parse_date(manifest.get("state_as_of"))
    if state_date is None:
        return "unknown"
    config = read_yaml(workspace / "skills/project-context-resolver/config/freshness.yaml")
    threshold = int(config.get("active_project_max_age_days", 7))
    if manifest.get("status") != "active":
        return str(manifest.get("freshness_status_at_manifest_update", "unknown"))
    return "current" if (dt.date.today() - state_date).days <= threshold else "stale"


def first_next_action(manifest: dict[str, Any] | None) -> str | None:
    if not manifest:
        return None
    for priority in ("p0", "p1", "p2"):
        for action in manifest.get("next_actions", {}).get(priority, []):
            if action.get("status") not in {"approved", "superseded"}:
                return str(action.get("action") or action.get("action_id"))
    return None


def project_blockers(manifest: dict[str, Any] | None) -> list[str]:
    if not manifest:
        return []
    output = []
    for item in manifest.get("blocking_items", []):
        if item.get("status") == "blocked":
            output.append(f"{item.get('blocker_id')}: {item.get('summary')}")
    return output[:30]


def accepted_decision_refs(manifest: dict[str, Any] | None) -> list[dict[str, str]]:
    if not manifest:
        return []
    latest = manifest.get("latest_decision") or {}
    if latest.get("status") != "accepted" or not latest.get("decision_id") or not latest.get("source"):
        return []
    return [{"decision_id": str(latest["decision_id"]), "source": str(latest["source"])}]


def required_reads(
    workspace: Path,
    manifest_path: Path | None,
    manifest: dict[str, Any] | None,
    maximum: int,
) -> list[str]:
    reads = ["AGENTS.md", "operator/profile.yaml", "operator/task-routing.yaml", "operator/review-policy.yaml"]
    if manifest_path and manifest:
        reads.append(relative_or_string(manifest_path, workspace))
        for kind in ("project_memory", "decisions", "product_truth", "approved_claims"):
            reads.extend(resolve_source_pointer(manifest_path, workspace, manifest.get("sources", {}).get(kind)))
    unique: list[str] = []
    for item in reads:
        if item not in unique and (workspace / item).exists():
            unique.append(item)
    return unique[:maximum]


def recent_context_run(workspace: Path) -> str | None:
    root = workspace / RUN_ROOT
    candidates = sorted(root.glob("*.context.log"), key=lambda p: p.stat().st_mtime, reverse=True)
    return relative_or_string(candidates[0], workspace) if candidates else None


def load_supplement(path: str | None, workspace: Path) -> dict[str, Any]:
    if not path:
        return {}
    candidate = Path(path)
    if not candidate.is_absolute():
        candidate = workspace / candidate
    return redact_data(read_yaml(candidate))


def clean_string_list(value: Any, maximum: int = 40, item_length: int = 500) -> list[str]:
    if value is None:
        return []
    items = value if isinstance(value, list) else [value]
    return [redact_text(str(item))[:item_length] for item in items[:maximum]]


def merge_decision_refs(
    automatic: list[dict[str, str]], supplemental: Any
) -> list[dict[str, str]]:
    output = list(automatic)
    if isinstance(supplemental, list):
        for item in supplemental:
            if not isinstance(item, dict):
                continue
            if item.get("status") not in {"accepted", "final", "approved"}:
                continue
            decision_id = item.get("decision_id")
            source = item.get("source")
            if decision_id and source:
                row = {"decision_id": redact_text(str(decision_id))[:200], "source": redact_text(str(source))[:500]}
                if row not in output:
                    output.append(row)
    return output[:20]


def build_resume_prompt(handoff: dict[str, Any], handoff_path: str, limit: int) -> str:
    project = handoff["project"]
    repo = handoff["repository"]
    reads = ["AGENTS.md"]
    if project.get("manifest"):
        reads.append(project["manifest"])
    reads.append(handoff_path)
    for item in handoff.get("required_reads", []):
        if item not in reads:
            reads.append(item)
    reads = reads[:12]
    completed = handoff.get("completed", [])[:8]
    blockers = handoff.get("blockers", [])[:8]
    forbidden = handoff.get("forbidden_changes", [])[:12]
    lines = [
        f"恢复线程：{handoff['resume']['recommended_new_thread_name']}",
        "",
        "这是文件驱动的恢复任务；不要依赖旧聊天或 /resume 作为正式状态。",
        f"项目：{project['project_id']}（task_type: {project['task_type']}）",
        f"分支：{repo['branch']}",
        f"记录时 HEAD：{repo['head_commit']}",
        f"目标：{handoff['goal']}",
        f"唯一下一动作：{handoff['next_action']}",
        "",
        "按顺序执行：",
        "1. 读取 AGENTS.md。",
        "2. 读取 Project Manifest（如有）。",
        f"3. 读取 Handoff：{handoff_path}。",
        "4. 运行 git status --short --branch，确认 Branch/HEAD 和未提交内容。",
        "5. 只继续上面的唯一下一动作；不要重新扫描整个仓库，不要重复已完成工作。",
        "",
        "最小必读：",
        *[f"- {item}" for item in reads],
    ]
    if completed:
        lines.extend(["", "已完成：", *[f"- {item}" for item in completed]])
    if blockers:
        lines.extend(["", "Blocker：", *[f"- {item}" for item in blockers]])
    if forbidden:
        lines.extend(["", "禁止修改：", *[f"- {item}" for item in forbidden]])
    prompt = redact_text("\n".join(lines))
    if len(prompt) > limit:
        prompt = prompt[: limit - 80].rstrip() + "\n[其余细节请读取 Handoff 文件]"
    return prompt


def validate_handoff(handoff: dict[str, Any], policy: dict[str, Any]) -> list[str]:
    errors = []
    required = read_yaml(DEFAULT_SCHEMA).get("required", [])
    for key in required:
        if key not in handoff:
            errors.append(f"missing:{key}")
    maximum_reads = int(policy["handoff"]["max_required_reads"])
    maximum_prompt = int(policy["handoff"]["max_resume_prompt_chars"])
    maximum_handoff = int(policy["handoff"]["max_handoff_chars"])
    if len(handoff.get("required_reads", [])) > maximum_reads:
        errors.append("required_reads_limit")
    prompt = handoff.get("resume", {}).get("bootstrap_prompt", "")
    if len(prompt) > maximum_prompt:
        errors.append("resume_prompt_limit")
    if not str(handoff.get("next_action", "")).strip():
        errors.append("next_action_missing")
    text = yaml.safe_dump(handoff, allow_unicode=True, sort_keys=False)
    if len(text) > maximum_handoff:
        errors.append("handoff_size_limit")
    if contains_unredacted_secret(text):
        errors.append("secret_not_redacted")
    return errors


def create_handoff(args: argparse.Namespace, workspace: Path) -> int:
    policy = read_yaml(workspace / "runtime/context-policy.yaml")
    manifest_path, manifest = resolve_project(workspace, args.project)
    project_id = str(manifest.get("project_id")) if manifest else "general"
    supplement = load_supplement(args.input, workspace)
    status = git_status(workspace)
    base_commit = git_value(workspace, "rev-parse", "origin/main")
    head_commit = git_value(workspace, "rev-parse", "HEAD")
    branch = git_value(workspace, "branch", "--show-current")
    created = now_utc()
    handoff_id = f"{safe_slug(project_id)}-{timestamp(created).casefold()}-{uuid.uuid4().hex[:8]}"
    destination = workspace / HANDOFF_ROOT / safe_slug(project_id, "general") / f"{handoff_id}.yaml"
    handoff_rel = relative_or_string(destination, workspace)
    automatic_tests = [recent_context_run(workspace)] if recent_context_run(workspace) else []
    goal = redact_text(str(supplement.get("goal") or args.task))[:1200]
    next_action = redact_text(str(args.next_action or supplement.get("next_action") or first_next_action(manifest) or "Prepare the next bounded task review."))[:1200]
    payload: dict[str, Any] = {
        "schema_version": "1.0",
        "handoff_id": handoff_id,
        "created_at": created.isoformat().replace("+00:00", "Z"),
        "repository": {
            "base_commit": base_commit,
            "head_commit": head_commit,
            "branch": branch,
            "worktree": redact_text(workspace.as_posix()),
            "git_status": status,
        },
        "project": {
            "project_id": project_id,
            "task_type": redact_text(args.task)[:200],
            "manifest": relative_or_string(manifest_path, workspace) if manifest_path else None,
            "effective_freshness": effective_freshness(workspace, manifest),
        },
        "goal": goal,
        "success_criteria": clean_string_list(supplement.get("success_criteria"), 20),
        "completed": clean_string_list(supplement.get("completed"), 40),
        "accepted_decisions": merge_decision_refs(accepted_decision_refs(manifest), supplement.get("decisions")),
        "changed_files": changed_files_from_status(status),
        "generated_artifacts": clean_string_list(supplement.get("generated_artifacts"), 40),
        "tests": clean_string_list(supplement.get("tests") or automatic_tests, 40),
        "blockers": clean_string_list(supplement.get("blockers") or project_blockers(manifest), 30, 800),
        "unresolved_questions": clean_string_list(supplement.get("unresolved"), 30, 800),
        "next_action": next_action,
        "required_reads": required_reads(
            workspace, manifest_path, manifest, int(policy["handoff"]["max_required_reads"])
        ),
        "forbidden_changes": clean_string_list(supplement.get("forbidden_changes"), 40),
        "resume": {
            "recommended_new_thread_name": safe_slug(f"{project_id}-{args.task}", "context-resume")[:200],
            "bootstrap_prompt": "pending",
        },
    }
    payload["resume"]["bootstrap_prompt"] = build_resume_prompt(
        payload, handoff_rel, int(policy["handoff"]["max_resume_prompt_chars"])
    )
    payload = redact_data(payload)
    errors = validate_handoff(payload, policy)
    if errors:
        raise ContextError("HANDOFF_INVALID:" + ",".join(errors))
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(yaml.safe_dump(payload, allow_unicode=True, sort_keys=False), encoding="utf-8")
    print(json.dumps({
        "status": "HANDOFF_SCHEMA_PASS",
        "handoff": handoff_rel,
        "project_id": project_id,
        "next_action": next_action,
        "required_reads": len(payload["required_reads"]),
        "resume_prompt_chars": len(payload["resume"]["bootstrap_prompt"]),
    }, ensure_ascii=False, indent=2))
    return 0


def latest_handoff(workspace: Path, project: str) -> Path:
    manifest_path, manifest = resolve_project(workspace, project)
    project_id = manifest.get("project_id") if manifest else "general"
    root = workspace / HANDOFF_ROOT / safe_slug(str(project_id), "general")
    candidates = sorted(root.glob("*.yaml"), key=lambda path: path.stat().st_mtime, reverse=True)
    if not candidates:
        raise ContextError(f"HANDOFF_NOT_FOUND:{project_id}")
    return candidates[0]


def resume_handoff(args: argparse.Namespace, workspace: Path) -> int:
    if args.handoff:
        path = Path(args.handoff)
        if not path.is_absolute():
            path = workspace / path
    else:
        path = latest_handoff(workspace, args.project)
    payload = read_yaml(path)
    policy = read_yaml(workspace / "runtime/context-policy.yaml")
    errors = validate_handoff(payload, policy)
    if errors:
        raise ContextError("HANDOFF_INVALID:" + ",".join(errors))
    prompt = str(payload["resume"]["bootstrap_prompt"])
    if len(prompt) > int(policy["handoff"]["max_resume_prompt_chars"]):
        raise ContextError("RESUME_PROMPT_TOO_LARGE")
    print(prompt)
    return 0


def capture_command(args: argparse.Namespace, workspace: Path) -> int:
    policy = read_yaml(workspace / "runtime/context-policy.yaml")
    command = list(args.command)
    if command and command[0] == "--":
        command = command[1:]
    if not command:
        raise ContextError("CAPTURE_COMMAND_REQUIRED")
    timeout_seconds = args.timeout or int(policy["large_output"].get("default_timeout_seconds", 900))
    output_dir = workspace / RUN_ROOT
    output_dir.mkdir(parents=True, exist_ok=True)
    log_path = output_dir / f"{timestamp()}-{safe_slug(args.name)}.context.log"
    failure_pattern = re.compile(
        r"(?i)\b(error|failed|failure|traceback|assert|fatal|timeout|blocked)\b"
    )
    line_count = 0
    failures: list[str] = []
    timed_out = False
    with log_path.open("w", encoding="utf-8") as log:
        process = subprocess.Popen(
            command,
            cwd=workspace,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            errors="replace",
        )
        assert process.stdout is not None

        def consume_output() -> None:
            nonlocal line_count
            maximum_failures = max(
                0, int(policy["inline_output_limits"]["max_log_lines"]) - 6
            )
            for line in process.stdout:
                clean = redact_text(line.rstrip("\n"))
                log.write(clean + "\n")
                line_count += 1
                if (
                    len(failures) < maximum_failures
                    and failure_pattern.search(clean)
                    and clean not in failures
                ):
                    failures.append(clean[:1000])

        reader = threading.Thread(target=consume_output, name="context-output-reader", daemon=True)
        reader.start()
        try:
            process.wait(timeout=timeout_seconds)
        except subprocess.TimeoutExpired:
            process.kill()
            timed_out = True
            process.wait(timeout=5)
        except Exception:
            process.kill()
            process.wait(timeout=5)
            raise
        finally:
            reader.join(timeout=5)
        if reader.is_alive():
            raise ContextError("CAPTURE_READER_DID_NOT_STOP")
        if timed_out:
            timeout_line = f"CONTEXT_CAPTURE_TIMEOUT after {timeout_seconds}s"
            log.write(timeout_line + "\n")
            line_count += 1
            if len(failures) < max(0, int(policy["inline_output_limits"]["max_log_lines"]) - 6):
                failures.append(timeout_line)
    exit_code = 124 if timed_out else int(process.returncode or 0)
    max_lines = int(policy["inline_output_limits"]["max_log_lines"])
    summary = [
        "LARGE_OUTPUT_CAPTURE_PASS" if not timed_out else "LARGE_OUTPUT_CAPTURE_TIMEOUT",
        f"exit_code: {exit_code}",
        f"lines_captured: {line_count}",
        f"log: {relative_or_string(log_path, workspace)}",
    ]
    if failures:
        summary.append("key_failures:")
        summary.extend(f"- {line}" for line in failures)
    print("\n".join(summary[:max_lines]))
    return exit_code


def config_override_summary(codex_home: Path) -> dict[str, Any]:
    config = codex_home / "config.toml"
    if not config.is_file():
        return {"exists": False, "dangerous_overrides": []}
    text = config.read_text(encoding="utf-8", errors="replace")
    keys = (
        "model_context_window",
        "model_auto_compact_token_limit",
        "model_auto_compact_token_limit_scope",
        "model_catalog_json",
    )
    present = [key for key in keys if re.search(rf"(?m)^\s*{re.escape(key)}\s*=", text)]
    return {"exists": True, "dangerous_overrides": present}


def runtime_status(workspace: Path, codex_home: Path) -> dict[str, Any]:
    command = [
        sys.executable,
        "scripts/verify_codex_runtime.py",
        "--workspace",
        str(workspace),
        "--codex-home",
        str(codex_home),
    ]
    result = run_command(command, workspace, timeout_seconds=30, check=False)
    try:
        payload = json.loads(result.stdout)
    except json.JSONDecodeError:
        return {"status": "REPOSITORY_RUNTIME_MISSING", "error": "invalid verifier output"}
    skill_rows = payload.get("skills", [])
    return {
        "status": payload.get("status", "REPOSITORY_RUNTIME_MISSING"),
        "verification_scope": payload.get("verification_scope"),
        "execution_source": payload.get("execution_source", "repository"),
        "global_auto_use": payload.get("global_auto_use"),
        "skills_checked": len(skill_rows),
        "issue_skills": [
            {
                "name": row.get("name"),
                "status": row.get("status"),
                "mismatch_count": len(row.get("mismatches", [])),
            }
            for row in skill_rows
            if row.get("status") not in {"IN_SYNC", "RUNTIME_IN_SYNC"}
        ],
    }


def inspect_hooks(workspace: Path) -> dict[str, Any]:
    path = workspace / ".codex/hooks.json"
    if not path.is_file():
        return {"status": "missing", "events": []}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return {"status": "invalid", "error": str(exc), "events": []}
    events = sorted(data.get("hooks", {}))
    valid = set(events) == ALLOWED_HOOK_EVENTS
    return {"status": "configured" if valid else "invalid", "events": events, "trust": "requires_client_verification"}


def doctor(args: argparse.Namespace, workspace: Path) -> int:
    codex_home = Path(args.codex_home or os.environ.get("CODEX_HOME") or (Path.home() / ".codex"))
    checks: dict[str, Any] = {}
    codex = shutil.which("codex")
    if codex:
        version = run_command([codex, "--version"], workspace, check=False)
        checks["codex"] = {"status": "pass" if version.returncode == 0 else "warning", "version": version.stdout.strip()}
    else:
        checks["codex"] = {"status": "blocked", "reason": "codex_not_found"}
    checks["config"] = config_override_summary(codex_home)
    checks["runtime"] = runtime_status(workspace, codex_home)
    checks["context_policy"] = {"status": "pass" if (workspace / "runtime/context-policy.yaml").is_file() else "blocked"}
    checks["hooks"] = inspect_hooks(workspace)
    checks["handoff_directory"] = {"status": "pass", "path": HANDOFF_ROOT.as_posix()}
    ignore_text = (workspace / ".gitignore").read_text(encoding="utf-8")
    required_ignores = {"private-runtime/", ".codex-local/", "*.context.log"}
    checks["gitignore"] = {"status": "pass" if required_ignores.issubset(set(ignore_text.splitlines())) else "blocked"}
    checks["git"] = {
        "status": "pass" if git_value(workspace, "rev-parse", "--is-inside-work-tree", fallback="false") == "true" else "blocked",
        "branch": git_value(workspace, "branch", "--show-current"),
        "head": git_value(workspace, "rev-parse", "HEAD"),
        "dirty_files": len(git_status(workspace)),
    }
    blocked = any(
        item.get("status") == "blocked" for item in checks.values() if isinstance(item, dict)
    ) or checks["runtime"].get("status") != "RUNTIME_IN_SYNC"
    warnings = bool(checks["config"].get("dangerous_overrides")) or checks["hooks"].get("trust") == "requires_client_verification"
    status = "CONTEXT_SYSTEM_BLOCKED" if blocked else ("CONTEXT_SYSTEM_WARNING" if warnings else "CONTEXT_SYSTEM_HEALTHY")
    print(json.dumps({"status": status, "execution_source": "repository", "checks": checks}, ensure_ascii=False, indent=2))
    return 2 if blocked else 0


def verify(args: argparse.Namespace, workspace: Path) -> int:
    checks: dict[str, str] = {}
    errors: list[str] = []
    try:
        policy = read_yaml(workspace / "runtime/context-policy.yaml")
        thresholds = policy["context_thresholds"]
        assert thresholds["prepare_handoff_percent"] < thresholds["stop_large_reads_percent"] < thresholds["force_new_thread_percent"]
        assert policy["handoff"]["max_required_reads"] == 12
        assert policy["handoff"]["max_resume_prompt_chars"] == 6000
        checks["policy"] = "CONTEXT_POLICY_PASS"
    except Exception as exc:
        errors.append(f"policy:{exc}")
        policy = {"handoff": {"max_required_reads": 12, "max_resume_prompt_chars": 6000, "max_handoff_chars": 12000}}
    try:
        schema = read_yaml(workspace / "schemas/thread-handoff.schema.yaml")
        assert schema.get("type") == "object"
        assert "next_action" in schema.get("required", [])
        assert schema["properties"]["required_reads"]["maxItems"] == 12
        checks["schema"] = "HANDOFF_SCHEMA_PASS"
    except Exception as exc:
        errors.append(f"schema:{exc}")
    hooks = inspect_hooks(workspace)
    if hooks.get("status") == "configured":
        source = (workspace / "scripts/codex_context_hook.py").read_text(encoding="utf-8")
        imported = set(re.findall(r"(?m)^(?:from|import)\s+([a-zA-Z0-9_.]+)", source))
        if any(any(name == bad or name.startswith(bad + ".") for bad in FORBIDDEN_NETWORK_IMPORTS) for name in imported):
            errors.append("hooks:network_import")
        else:
            checks["hooks"] = "HOOK_CONFIG_PASS"
    else:
        errors.append("hooks:not_configured")
    ignore_text = (workspace / ".gitignore").read_text(encoding="utf-8")
    if all(item in ignore_text.splitlines() for item in ("private-runtime/", ".codex-local/", "*.context.log")):
        checks["gitignore"] = "GIT_IGNORE_PASS"
    else:
        errors.append("gitignore:missing_runtime_rule")
    tracked_runtime = run_command(["git", "ls-files", "private-runtime"], workspace).stdout.strip()
    if tracked_runtime:
        errors.append("gitignore:private_runtime_tracked")
    handoffs = [
        path
        for path in (workspace / HANDOFF_ROOT).glob("*/*.yaml")
        if path.parent.name != "_automatic"
    ]
    prompt_pass = True
    for path in handoffs:
        handoff = read_yaml(path)
        validation = validate_handoff(handoff, policy)
        if validation:
            errors.append(f"handoff:{path.name}:{','.join(validation)}")
        if len(handoff.get("resume", {}).get("bootstrap_prompt", "")) > 6000:
            prompt_pass = False
    if prompt_pass:
        checks["resume"] = "RESUME_PROMPT_PASS"
    status = "CONTEXT_SYSTEM_HEALTHY" if not errors else "CONTEXT_SYSTEM_BLOCKED"
    print(json.dumps({"status": status, "checks": checks, "errors": errors}, ensure_ascii=False, indent=2))
    return 0 if not errors else 2


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workspace", default=str(ROOT))
    sub = parser.add_subparsers(dest="command_name", required=True)
    doctor_parser = sub.add_parser("doctor")
    doctor_parser.add_argument("--codex-home")
    handoff_parser = sub.add_parser("handoff")
    handoff_parser.add_argument("--project", default="general")
    handoff_parser.add_argument("--task", required=True)
    handoff_parser.add_argument("--next-action")
    handoff_parser.add_argument("--input")
    resume_parser = sub.add_parser("resume")
    resume_parser.add_argument("--project", default="general")
    resume_parser.add_argument("--latest", action="store_true")
    resume_parser.add_argument("--handoff")
    capture_parser = sub.add_parser("capture")
    capture_parser.add_argument("--name", required=True)
    capture_parser.add_argument("--timeout", type=int)
    capture_parser.add_argument("command", nargs=argparse.REMAINDER)
    sub.add_parser("verify")
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    workspace = Path(args.workspace).resolve()
    try:
        if args.command_name == "doctor":
            return doctor(args, workspace)
        if args.command_name == "handoff":
            return create_handoff(args, workspace)
        if args.command_name == "resume":
            return resume_handoff(args, workspace)
        if args.command_name == "capture":
            return capture_command(args, workspace)
        if args.command_name == "verify":
            return verify(args, workspace)
    except (ContextError, OSError, subprocess.SubprocessError, yaml.YAMLError) as exc:
        print(json.dumps({"status": "CONTEXT_SYSTEM_BLOCKED", "error": redact_text(str(exc))}, ensure_ascii=False, indent=2))
        return 2
    return 2


if __name__ == "__main__":
    sys.exit(main())
