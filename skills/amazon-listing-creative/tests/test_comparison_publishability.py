from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
TEXT = (ROOT / "skills/amazon-listing-creative/references/comparison-contract.md").read_text(encoding="utf-8")


def test_cross_brand_competitor_matrix_stays_internal_only():
    assert "Internal Competitor Matrix" in TEXT
    assert "INTERNAL_ONLY" in TEXT
    assert "NOT_PUBLISHABLE_AS_AMAZON_A_PLUS" in TEXT
    assert "Publishable Series Comparison" in TEXT
    assert "SAME_BRAND_CONFIRMED_PRODUCT" in TEXT
