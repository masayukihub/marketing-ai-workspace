from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
TEXT = (ROOT / "skills/amazon-listing-creative/references/decision-oriented-comparison-example.md").read_text(encoding="utf-8")


def test_comparison_example_contains_no_product_truth():
    assert "generic structure example only" in TEXT
    assert "must not be reused as factual product data" in TEXT
