from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
TEXT = (ROOT / "skills/amazon-listing-creative/SKILL.md").read_text(encoding="utf-8")


def test_brand_story_is_independent_page_role():
    assert "Brand Story 不等于 Gallery 最后一张" in TEXT
