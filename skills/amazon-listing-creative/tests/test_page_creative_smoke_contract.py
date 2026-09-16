from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
BASE = ROOT / "skills/amazon-listing-creative"


def test_page_creative_upgrade_smoke():
    skill = (BASE / "SKILL.md").read_text(encoding="utf-8")
    assert "Page Story Spine" in skill
    assert "Brand Story" in skill
    assert "Publishable Series Comparison" in skill
    assert "Copy ↔ Visual Fidelity Contract" in skill
