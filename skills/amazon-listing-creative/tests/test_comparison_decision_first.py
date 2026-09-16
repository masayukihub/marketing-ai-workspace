from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
TEXT = (ROOT / "skills/amazon-listing-creative/references/comparison-contract.md").read_text(encoding="utf-8")


def test_comparison_prioritizes_decision_dimensions():
    first = TEXT.index("Recommended For")
    specs = TEXT.index("Body Size")
    assert first < specs
    assert "Home / Usage Fit" in TEXT
    assert "Key Differentiator" in TEXT
