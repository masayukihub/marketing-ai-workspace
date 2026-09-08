from __future__ import annotations

import csv
import json
import shutil
import subprocess
import sys
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from runtime_contract import repository_file_hashes, tree_hash  # noqa: E402
from sync_codex_skill_mirror import apply_skill, sync_preconditions  # noqa: E402
from verify_codex_runtime import verify_runtime  # noqa: E402


LOCKED_SKILLS = {
    "project-context-resolver",
    "project-memory-manager",
    "product-knowledge",
    "jp-commerce-insights",
    "jp-commerce-content-flow",
    "switchbot-japan-campaign",
    "switchbot-japan-edm",
}


def load_yaml(path: Path):
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def test_skill_lock_covers_required_runtime_and_matches_repository():
    lock = json.loads((ROOT / "runtime/skill-lock.json").read_text(encoding="utf-8"))

    assert lock["runtime_authority"] == "repository"
    assert {item["name"] for item in lock["skills"]} == LOCKED_SKILLS
    for item in lock["skills"]:
        assert item["repository_tree_hash"] == tree_hash(
            repository_file_hashes(ROOT, item["repository_path"])
        )
        assert item["required_runtime_files"]
        assert item["mirror_required"] is True


def test_runtime_verifier_statuses_are_fail_closed(tmp_path: Path):
    workspace = tmp_path / "repo"
    skill = workspace / "skills/demo"
    skill.mkdir(parents=True)
    (skill / "SKILL.md").write_text("---\nname: demo\ndescription: Demo\n---\n", encoding="utf-8")
    subprocess.run(["git", "init", "-q"], cwd=workspace, check=True)
    subprocess.run(["git", "add", "."], cwd=workspace, check=True)
    subprocess.run(
        ["git", "-c", "user.name=Test", "-c", "user.email=test@example.invalid", "commit", "-qm", "init"],
        cwd=workspace,
        check=True,
    )
    hashes = repository_file_hashes(workspace, "skills/demo")
    lock = {
        "lock_version": "1.0",
        "runtime_authority": "repository",
        "skills": [{
            "name": "demo",
            "role": "test",
            "repository_path": "skills/demo",
            "repository_tree_hash": tree_hash(hashes),
            "required_runtime_files": ["SKILL.md"],
            "user_visible": False,
            "mirror_required": True,
            "last_verified_commit": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=workspace, text=True).strip(),
        }],
    }
    lock_path = workspace / "runtime/skill-lock.json"
    lock_path.parent.mkdir()
    lock_path.write_text(json.dumps(lock), encoding="utf-8")
    codex_home = tmp_path / "codex"

    repository = verify_runtime(workspace, lock_path, codex_home, repository_only=True)
    missing = verify_runtime(workspace, lock_path, codex_home)
    assert repository["status"] == "RUNTIME_IN_SYNC"
    assert missing["status"] == "MIRROR_MISSING"
    assert missing["execution_source"] == "repository"
    assert missing["global_auto_use"] is False

    mirror = codex_home / "skills/demo"
    mirror.mkdir(parents=True)
    shutil.copy2(skill / "SKILL.md", mirror / "SKILL.md")
    assert verify_runtime(workspace, lock_path, codex_home)["status"] == "RUNTIME_IN_SYNC"
    (mirror / "SKILL.md").write_text("drift\n", encoding="utf-8")
    assert verify_runtime(workspace, lock_path, codex_home)["status"] == "RUNTIME_DRIFT"


def test_sync_apply_is_blocked_outside_clean_main():
    lock = json.loads((ROOT / "runtime/skill-lock.json").read_text(encoding="utf-8"))
    reasons = sync_preconditions(ROOT, lock)

    assert "SYNC_REQUIRES_MAIN_BRANCH" in reasons


def test_sync_replaces_legacy_symlink_but_preserves_its_source(tmp_path: Path):
    workspace = tmp_path / "repo"
    skill = workspace / "skills/demo"
    skill.mkdir(parents=True)
    (skill / "SKILL.md").write_text("repository runtime\n", encoding="utf-8")
    subprocess.run(["git", "init", "-q"], cwd=workspace, check=True)
    subprocess.run(["git", "add", "."], cwd=workspace, check=True)
    subprocess.run(
        ["git", "-c", "user.name=Test", "-c", "user.email=test@example.invalid", "commit", "-qm", "init"],
        cwd=workspace,
        check=True,
    )

    legacy_source = tmp_path / "legacy-runtime"
    legacy_source.mkdir()
    (legacy_source / "legacy.txt").write_text("preserve me\n", encoding="utf-8")
    codex_home = tmp_path / "codex"
    target = codex_home / "skills/demo"
    target.parent.mkdir(parents=True)
    target.symlink_to(legacy_source, target_is_directory=True)

    apply_skill(workspace, codex_home, {"name": "demo", "repository_path": "skills/demo"})

    assert target.is_dir()
    assert not target.is_symlink()
    assert (target / "SKILL.md").read_text(encoding="utf-8") == "repository runtime\n"
    assert (legacy_source / "legacy.txt").read_text(encoding="utf-8") == "preserve me\n"


def test_inventory_is_repository_owned_and_has_no_machine_paths():
    with (ROOT / "inventory/skill_inventory.csv").open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    names = {row["skill_name"] for row in rows}
    text = (ROOT / "inventory/skill_inventory.csv").read_text(encoding="utf-8")

    assert "project-context-resolver" in names
    assert LOCKED_SKILLS.issubset(names)
    assert all(row["runtime_authority"] == "repository" for row in rows)
    forbidden = ("/" + "Users" + "/", "/" + "home" + "/")
    assert not any(prefix in text for prefix in forbidden)
    assert "local-installed" not in text


def test_chatgpt_snapshots_are_read_only_and_point_to_github_sources():
    index = load_yaml(ROOT / "chatgpt/context-index.yaml")
    assert index["snapshot_authority"] == "generated_read_only_not_truth_source"
    assert index["truth_precedence"][0] == "github_product_knowledge_project_memory_decision"
    assert len(index["projects"]) == 4
    for item in index["projects"]:
        path = ROOT / item["snapshot"]
        text = path.read_text(encoding="utf-8")
        payload = yaml.safe_load(text.removeprefix("---\n").removesuffix("---\n"))
        assert payload["snapshot_authority"] == "generated_read_only_not_truth_source"
        assert payload["project_id"] == item["project_id"]
        assert payload["effective_freshness_status"] in {"current", "stale", "unknown"}
        assert item["manifest"] in payload["required_github_source_paths"]
        assert "product_truth_values" not in payload
        assert "approved_claims" not in payload


def test_chatgpt_bootstrap_contract_is_fail_closed():
    text = (ROOT / "chatgpt/PROJECT_INSTRUCTIONS.md").read_text(encoding="utf-8")
    for phrase in (
        "GitHub `main`",
        "GITHUB_CONTEXT_UNVERIFIED",
        "ChatGPT Memory",
        "合并到 `main`",
    ):
        assert phrase in text


def test_manifests_use_maintenance_time_freshness_field_only():
    for path in sorted((ROOT / "projects").glob("*/project.yaml")):
        manifest = load_yaml(path)
        assert "freshness_status_at_manifest_update" in manifest
        assert "freshness_status" not in manifest
        assert "effective_freshness_status" not in manifest


def test_s30_project_and_channel_blockers_coexist_without_scope_promotion():
    manifest = load_yaml(ROOT / "projects/s30-mini/project.yaml")
    blocker_ids = [item["blocker_id"] for item in manifest["blocking_items"]]

    assert manifest["current_phase"] == "context_migration_and_gate_1_evidence_review"
    assert blocker_ids == [
        "S30-PRODUCT-TRUTH",
        "S30-COMMERCIAL",
        "S30-CONTENT-CLAIM-ASSET-UNLOCK",
    ]
    assert manifest["gate_status"]["visual_planning"] == "approved"
    assert manifest["gate_status"]["visual_freeze"] != "approved"


def test_consistency_artifacts_do_not_contain_absolute_machine_paths():
    paths = [
        ROOT / "runtime/skill-lock.json",
        ROOT / "inventory/skill_inventory.csv",
        ROOT / "docs/SKILL_CATALOG.md",
        ROOT / "chatgpt/PROJECT_INSTRUCTIONS.md",
        ROOT / "chatgpt/context-index.yaml",
        *sorted((ROOT / "projects").glob("*/chatgpt-context.md")),
    ]
    forbidden = ("/" + "Users" + "/", "/" + "home" + "/")
    offenders = []
    for path in paths:
        text = path.read_text(encoding="utf-8")
        if any(prefix in text for prefix in forbidden):
            offenders.append(path.relative_to(ROOT).as_posix())
    assert offenders == []
