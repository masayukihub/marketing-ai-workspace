from __future__ import annotations

import argparse
import ast
import hashlib
import importlib.util
import json
import os
import subprocess
import sys
import time
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


contextctl = load_module("contextctl", ROOT / "scripts/contextctl.py")


def git(repo: Path, *args: str) -> str:
    return subprocess.check_output(["git", *args], cwd=repo, text=True).strip()


def write_manifest(repo: Path, project_id: str, blocker: str) -> None:
    project = repo / "projects" / project_id
    project.mkdir(parents=True)
    memory = repo / "memory" / "project-memory" / project_id
    memory.mkdir(parents=True)
    for name in ("PROJECT.md", "DECISIONS.md"):
        (memory / name).write_text(f"# {project_id} {name}\n", encoding="utf-8")
    manifest = {
        "project_id": project_id,
        "project_name": project_id,
        "aliases": [project_id.replace("-", " ")],
        "state_as_of": "2026-09-10",
        "status": "active",
        "sources": {
            "project_memory": f"../../memory/project-memory/{project_id}/PROJECT.md",
            "decisions": f"../../memory/project-memory/{project_id}/DECISIONS.md",
            "product_truth": None,
            "approved_claims": None,
        },
        "blocking_items": [{"blocker_id": blocker, "summary": f"{blocker} remains open", "status": "blocked"}],
        "latest_decision": {"status": "accepted", "decision_id": f"DEC-{project_id}", "source": f"../../memory/project-memory/{project_id}/DECISIONS.md"},
        "next_actions": {
            "p0": [{"action_id": f"{blocker}-ACTION", "action": f"Resolve {blocker}", "status": "not_started"}],
            "p1": [],
            "p2": [],
        },
    }
    (project / "project.yaml").write_text(yaml.safe_dump(manifest, sort_keys=False), encoding="utf-8")


def make_repo(tmp_path: Path) -> Path:
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / "AGENTS.md").write_text("# Test rules\n", encoding="utf-8")
    (repo / ".gitignore").write_text("private-runtime/\n.codex-local/\n*.context.log\n", encoding="utf-8")
    (repo / "operator").mkdir()
    for name in ("profile.yaml", "task-routing.yaml", "review-policy.yaml"):
        (repo / "operator" / name).write_text("version: test\n", encoding="utf-8")
    freshness = repo / "skills/project-context-resolver/config"
    freshness.mkdir(parents=True)
    (freshness / "freshness.yaml").write_text("active_project_max_age_days: 7\n", encoding="utf-8")
    policy = repo / "runtime"
    policy.mkdir()
    (policy / "context-policy.yaml").write_text((ROOT / "runtime/context-policy.yaml").read_text(encoding="utf-8"), encoding="utf-8")
    write_manifest(repo, "s30-mini", "S30-BLOCKER")
    write_manifest(repo, "lock-ultra-max", "LUM-BLOCKER")
    subprocess.run(["git", "init", "-q", "-b", "main"], cwd=repo, check=True)
    subprocess.run(["git", "add", "."], cwd=repo, check=True)
    subprocess.run(
        ["git", "-c", "user.name=Test", "-c", "user.email=test@example.invalid", "commit", "-qm", "init"],
        cwd=repo,
        check=True,
    )
    return repo


def handoff_args(project: str, task: str, next_action: str, input_path: str | None = None):
    return argparse.Namespace(project=project, task=task, next_action=next_action, input=input_path)


def latest_handoff(repo: Path, project: str) -> Path:
    return sorted((repo / "private-runtime/thread-handoffs" / project).glob("*.yaml"))[-1]


def test_handoff_reads_git_and_redacts_secrets_without_embedding_diff_or_log(tmp_path: Path, capsys):
    repo = make_repo(tmp_path)
    tracked = repo / "AGENTS.md"
    tracked.write_text("# Test rules\n" + "changed\n" * 1000, encoding="utf-8")
    supplement = repo / "private-runtime/handoff-input.yaml"
    supplement.parent.mkdir(parents=True)
    supplement.write_text(
        "goal: Finish EBC QA\n"
        "completed:\n  - Layout audit complete\n"
        "unresolved:\n  - access_token=EXAMPLE_REDACTION_VALUE_12345\n"
        "forbidden_changes:\n  - Product Truth\n  - Approved Claim\n",
        encoding="utf-8",
    )

    result = contextctl.create_handoff(
        handoff_args("s30-mini", "Amazon EBC QA", "Run mobile A+ raster QA", str(supplement)), repo
    )
    assert result == 0
    output = json.loads(capsys.readouterr().out)
    assert output["status"] == "HANDOFF_SCHEMA_PASS"
    payload = yaml.safe_load(latest_handoff(repo, "s30-mini").read_text(encoding="utf-8"))
    text = yaml.safe_dump(payload, allow_unicode=True)

    assert payload["repository"]["branch"] == "main"
    assert payload["repository"]["head_commit"] == git(repo, "rev-parse", "HEAD")
    assert "AGENTS.md" in payload["changed_files"]
    assert "diff --git" not in text
    assert "EXAMPLE_REDACTION_VALUE_12345" not in text
    assert "<REDACTED>" in text
    assert len(payload["required_reads"]) <= 12
    assert len(payload["resume"]["bootstrap_prompt"]) < 6000
    assert payload["next_action"] == "Run mobile A+ raster QA"


def test_resume_prompt_is_pointer_only_and_does_not_require_old_chat(tmp_path: Path, capsys):
    repo = make_repo(tmp_path)
    contextctl.create_handoff(handoff_args("s30-mini", "Amazon EBC QA", "Run mobile A+ raster QA"), repo)
    capsys.readouterr()
    args = argparse.Namespace(project="s30-mini", latest=True, handoff=None)

    assert contextctl.resume_handoff(args, repo) == 0
    prompt = capsys.readouterr().out
    assert len(prompt) < 6000
    assert "AGENTS.md" in prompt
    assert "projects/s30-mini/project.yaml" in prompt
    assert "git status --short --branch" in prompt
    assert "Run mobile A+ raster QA" in prompt
    assert "不要依赖旧聊天" in prompt
    assert "不要重新扫描整个仓库" in prompt


def test_project_isolation_for_s30_lock_and_general(tmp_path: Path, capsys):
    repo = make_repo(tmp_path)
    for project, blocker in (("s30-mini", "S30-BLOCKER"), ("lock-ultra-max", "LUM-BLOCKER")):
        contextctl.create_handoff(handoff_args(project, "Review", f"Resolve {blocker}"), repo)
        capsys.readouterr()
        text = latest_handoff(repo, project).read_text(encoding="utf-8")
        assert blocker in text
        assert ("LUM-BLOCKER" if project == "s30-mini" else "S30-BLOCKER") not in text

    contextctl.create_handoff(handoff_args("general", "Architecture audit", "Run context verify"), repo)
    capsys.readouterr()
    general = yaml.safe_load(latest_handoff(repo, "general").read_text(encoding="utf-8"))
    assert general["project"]["project_id"] == "general"
    assert general["project"]["manifest"] is None
    assert "S30-BLOCKER" not in yaml.safe_dump(general)
    assert "LUM-BLOCKER" not in yaml.safe_dump(general)


def test_large_output_capture_writes_5000_lines_limits_summary_and_preserves_exit_code(tmp_path: Path, capsys):
    repo = make_repo(tmp_path)
    secret = "sk-" + "abcdefghijklmnopqrstuvwxyz123456"
    code = f"import sys; [print('line-%04d' % i) for i in range(4999)]; print('api_key={secret}'); sys.exit(7)"
    args = argparse.Namespace(
        name="large-regression",
        timeout=30,
        command=[sys.executable, "-c", code],
    )

    assert contextctl.capture_command(args, repo) == 7
    summary = capsys.readouterr().out.splitlines()
    logs = list((repo / "private-runtime/context-runs").glob("*.context.log"))
    assert len(logs) == 1
    log_text = logs[0].read_text(encoding="utf-8")
    assert len(log_text.splitlines()) == 5000
    assert secret not in log_text
    assert "<REDACTED>" in log_text
    assert len(summary) <= 40
    assert "exit_code: 7" in summary


def test_large_output_capture_times_out_silent_process(tmp_path: Path, capsys):
    repo = make_repo(tmp_path)
    args = argparse.Namespace(
        name="silent-timeout",
        timeout=1,
        command=[sys.executable, "-c", "import time; time.sleep(30)"],
    )

    started = time.monotonic()
    assert contextctl.capture_command(args, repo) == 124
    elapsed = time.monotonic() - started
    summary = capsys.readouterr().out
    log = next((repo / "private-runtime/context-runs").glob("*.context.log"))

    assert elapsed < 5
    assert "LARGE_OUTPUT_CAPTURE_TIMEOUT" in summary
    assert "exit_code: 124" in summary
    assert "CONTEXT_CAPTURE_TIMEOUT after 1s" in log.read_text(encoding="utf-8")


def test_hook_simulation_creates_mechanical_checkpoints_without_business_changes(tmp_path: Path):
    repo = make_repo(tmp_path)
    contextctl.create_handoff(handoff_args("s30-mini", "Amazon EBC QA", "Run mobile A+ raster QA"), repo)
    business = repo / "projects/s30-mini/project.yaml"
    before = hashlib.sha256(business.read_bytes()).hexdigest()
    head_before = git(repo, "rev-parse", "HEAD")
    env = os.environ.copy()
    env["CODEX_CONTEXT_WORKSPACE"] = str(repo)
    env["CODEX_CONTEXT_PROJECT"] = "s30-mini"
    payload = json.dumps(
        {"session_id": "session-example", "access_token": "EXAMPLE_REDACTION_VALUE_12345"}
    )
    started = time.monotonic()

    for event in ("pre-compact", "post-compact", "session-end", "compact-failed"):
        result = subprocess.run(
            [sys.executable, str(ROOT / "scripts/codex_context_hook.py"), "--event", event],
            input=payload,
            text=True,
            capture_output=True,
            env=env,
            check=False,
            timeout=3,
        )
        assert result.returncode == 0

    assert time.monotonic() - started < 8
    checkpoints = list((repo / "private-runtime/thread-handoffs/_automatic").glob("*.yaml"))
    assert len(checkpoints) == 4
    combined = "\n".join(path.read_text(encoding="utf-8") for path in checkpoints)
    assert "EXAMPLE_REDACTION_VALUE_12345" not in combined
    assert "session-example" not in combined
    assert "payload_persisted: false" in combined
    assert "network_used: false" in combined
    assert "handoff_present: true" in combined
    assert hashlib.sha256(business.read_bytes()).hexdigest() == before
    assert git(repo, "rev-parse", "HEAD") == head_before
    assert git(repo, "status", "--short") == ""


def test_hook_source_has_no_network_imports_or_commit_command():
    source = (ROOT / "scripts/codex_context_hook.py").read_text(encoding="utf-8")
    tree = ast.parse(source)
    imports = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imports.add(node.module)
    assert not imports.intersection({"requests", "socket", "urllib", "http.client", "aiohttp"})
    assert "git\", \"commit" not in source
    assert "http://" not in source and "https://" not in source


def test_policy_schema_hooks_status_line_and_private_runtime_contracts():
    policy = yaml.safe_load((ROOT / "runtime/context-policy.yaml").read_text(encoding="utf-8"))
    schema = yaml.safe_load((ROOT / "schemas/thread-handoff.schema.yaml").read_text(encoding="utf-8"))
    hooks = json.loads((ROOT / ".codex/hooks.json").read_text(encoding="utf-8"))
    status_line = (ROOT / ".codex/config.toml").read_text(encoding="utf-8")
    ignore = (ROOT / ".gitignore").read_text(encoding="utf-8").splitlines()

    assert policy["context_thresholds"] == {
        "prepare_handoff_percent": 70,
        "stop_large_reads_percent": 80,
        "force_new_thread_percent": 90,
        "measurement_source": "client_status_line_when_available",
        "unknown_behavior": "apply_operator_rules_without_inventing_a_percentage",
    }
    assert schema["properties"]["required_reads"]["maxItems"] == 12
    assert schema["properties"]["resume"]["properties"]["bootstrap_prompt"]["maxLength"] == 6000
    assert set(hooks["hooks"]) == {"PreCompact", "PostCompact", "SessionEnd"}
    for groups in hooks["hooks"].values():
        for group in groups:
            for hook in group["hooks"]:
                assert hook["type"] == "command"
                assert hook["timeout"] == 2
                assert "codex_context_hook.py" in hook["command"]
    for item in ("model-with-reasoning", "git-branch", "context-used", "thread-id"):
        assert item in status_line
    assert {"private-runtime/", ".codex-local/", "*.context.log"}.issubset(ignore)


def test_no_new_user_visible_skill_and_locked_runtime_remains_valid():
    lock = json.loads((ROOT / "runtime/skill-lock.json").read_text(encoding="utf-8"))
    visible = {item["name"] for item in lock["skills"] if item["user_visible"]}
    assert visible == {
        "jp-commerce-insights",
        "jp-commerce-content-flow",
        "switchbot-japan-campaign",
        "switchbot-japan-edm",
    }
    result = subprocess.run(
        [sys.executable, "scripts/verify_codex_runtime.py", "--repository-only"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    assert result.returncode == 0
    assert json.loads(result.stdout)["status"] == "RUNTIME_IN_SYNC"
