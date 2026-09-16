from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
SKILL = (ROOT / "skills/amazon-listing-creative/SKILL.md").read_text(encoding="utf-8")


def test_page_story_links_brand_and_comparison_contracts():
    assert "brand-story-contract.md" in SKILL
    assert "comparison-contract.md" in SKILL
    assert "copy-visual-fidelity.md" in SKILL
    assert "page-story-framework.md" in SKILL
