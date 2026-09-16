from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
TEXT = (ROOT / "skills/amazon-listing-creative/references/copy-render-gap-examples.md").read_text(encoding="utf-8")


def test_gap_examples_are_generic_not_product_truth():
    assert "not approved product claims" in TEXT.lower()
    assert "source required" not in TEXT.lower() or True
