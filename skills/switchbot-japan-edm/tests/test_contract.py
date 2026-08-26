from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]


def _frontmatter(text: str) -> dict:
    assert text.startswith("---\n")
    return yaml.safe_load(text.split("---\n", 2)[1])


def test_edm_entry_contract():
    skill = (ROOT / "SKILL.md").read_text(encoding="utf-8")
    ui = yaml.safe_load((ROOT / "agents" / "openai.yaml").read_text(encoding="utf-8"))
    reference = (ROOT / "references" / "edm-production-method.md").read_text(encoding="utf-8")

    meta = _frontmatter(skill)
    assert meta["name"] == "switchbot-japan-edm"
    assert "BLOCKED_RUNTIME_MISSING" in skill
    assert "VISUAL_DELIVERABLE_CANDIDATE" in skill
    assert "PRODUCTION_READY" in skill
    assert "不自动发送 EDM" in skill
    assert "不用 AI 重绘" in skill
    assert ui["policy"]["allow_implicit_invocation"] is True
    assert ui["interface"]["display_name"] == "日本EDM制作"

    for legacy in ("optimize-japan-edm", "edm-generator", "switchbot-japan-edm-generator-v1-1-internal", "switchbot-japan-edm-visual-template-skill"):
        assert legacy in reference


def test_edm_human_and_browser_gates():
    skill = (ROOT / "SKILL.md").read_text(encoding="utf-8")
    assert "Codex 不能代签" in skill
    assert "浏览器 QA 没有实际运行时" in skill
    assert "ESP_READY" in skill
