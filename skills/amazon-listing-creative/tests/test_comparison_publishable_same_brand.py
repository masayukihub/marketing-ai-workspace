from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
TEXT = (ROOT / "skills/amazon-listing-creative/references/comparison-contract.md").read_text(encoding="utf-8")


def test_publishable_comparison_defaults_to_same_brand():
    assert "SAME_BRAND_CONFIRMED_PRODUCT" in TEXT
    assert "默认只允许" in TEXT
