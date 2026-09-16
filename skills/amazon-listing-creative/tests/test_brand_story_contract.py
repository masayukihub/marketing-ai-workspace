from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
TEXT = (ROOT / "skills/amazon-listing-creative/references/brand-story-contract.md").read_text(encoding="utf-8")


def test_brand_story_keeps_product_and_brand_roles_separate():
    assert "Brand Promise" in TEXT
    assert "Product Philosophy" in TEXT
    assert "Ecosystem / Trust" in TEXT
    assert "BRAND_STORY_DUPLICATES_PRODUCT_STORY" in TEXT
    assert "No.1" in TEXT
