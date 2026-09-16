from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
TEXT = (ROOT / "skills/amazon-listing-creative/SKILL.md").read_text(encoding="utf-8")


def test_skill_references_brand_story_contract():
    assert "references/brand-story-contract.md" in TEXT
