from __future__ import annotations

import importlib.util
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
SKILL_ROOT = ROOT / "skills/project-memory-manager"
SCRIPT = SKILL_ROOT / "scripts/verify_global_mirror.py"
SPEC = importlib.util.spec_from_file_location("verify_global_mirror", SCRIPT)
mirror = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(mirror)


def write_bundle(root: Path, suffix: str = "") -> None:
    for relative_path in mirror.RUNTIME_FILES:
        target = root / relative_path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(f"runtime:{relative_path}{suffix}\n", encoding="utf-8")


def test_repository_runtime_is_the_default_source():
    skill_text = (SKILL_ROOT / "SKILL.md").read_text(encoding="utf-8")

    assert "python3 skills/project-memory-manager/scripts/project_memory.py --workspace ." in skill_text
    assert 'python3 "$HOME/.codex/skills/project-memory-manager/scripts/project_memory.py"' not in skill_text
    assert mirror.DEFAULT_REPOSITORY_SKILL_ROOT == SKILL_ROOT


def test_matching_global_mirror_is_explicitly_in_sync(tmp_path: Path):
    repository = tmp_path / "repository"
    global_mirror = tmp_path / "global"
    write_bundle(repository)
    write_bundle(global_mirror)

    result = mirror.compare_mirror(repository, global_mirror)

    assert result["status"] == "GLOBAL_SKILL_IN_SYNC"
    assert result["global_auto_use"] is False
    assert result["repository_bundle_sha256"] == result["global_bundle_sha256"]


def test_hash_mismatch_reports_global_skill_drift(tmp_path: Path):
    repository = tmp_path / "repository"
    global_mirror = tmp_path / "global"
    write_bundle(repository)
    write_bundle(global_mirror)
    (global_mirror / "SKILL.md").write_text("drift\n", encoding="utf-8")

    result = mirror.compare_mirror(repository, global_mirror)

    assert result["status"] == "GLOBAL_SKILL_DRIFT"
    assert result["execution_source"] == "repository"
    assert any(item["path"] == "SKILL.md" and item["reason"] == "hash_mismatch" for item in result["mismatches"])


def test_missing_global_runtime_reports_drift_without_fallback(tmp_path: Path):
    repository = tmp_path / "repository"
    global_mirror = tmp_path / "global"
    write_bundle(repository)

    result = mirror.compare_mirror(repository, global_mirror)

    assert result["status"] == "GLOBAL_SKILL_DRIFT"
    assert result["global_auto_use"] is False
    assert any(item["reason"] == "global_runtime_missing" for item in result["mismatches"])
