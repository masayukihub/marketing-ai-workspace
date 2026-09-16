from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
TEXT = (ROOT / "skills/amazon-listing-creative/references/review-site-gap-map.md").read_text(encoding="utf-8")


def test_gap_map_covers_framework_brand_comparison_and_copy_render():
    for token in ("Whole-page Framework", "Brand Introduction", "Comparison", "Copy vs Render"):
        assert token in TEXT
