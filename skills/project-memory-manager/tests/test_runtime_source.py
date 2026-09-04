from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
SKILL_ROOT = ROOT / "skills/project-memory-manager"
SCRIPT = SKILL_ROOT / "scripts/verify_global_mirror.py"


def test_repository_runtime_is_the_default_source():
    skill_text = (SKILL_ROOT / "SKILL.md").read_text(encoding="utf-8")

    assert "python3 skills/project-memory-manager/scripts/project_memory.py --workspace ." in skill_text
    assert 'python3 "$HOME/.codex/skills/project-memory-manager/scripts/project_memory.py"' not in skill_text
    assert "python3 scripts/verify_codex_runtime.py" in skill_text


def test_legacy_verifier_is_only_a_repository_wide_adapter():
    text = SCRIPT.read_text(encoding="utf-8")

    assert "verify_runtime" in text
    assert 'selected_skills={"project-memory-manager"}' in text
    assert "GLOBAL_SKILL_IN_SYNC" not in text
    assert "GLOBAL_SKILL_DRIFT" not in text
