from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
TEXT = (ROOT / "skills/amazon-listing-creative/references/page-story-framework.md").read_text(encoding="utf-8")


def test_page_units_have_distinct_roles():
    for unit in ("Gallery", "A+", "Brand Story", "Series Comparison", "FAQ"):
        assert unit in TEXT
