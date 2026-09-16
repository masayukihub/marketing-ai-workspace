from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
TEXT = (ROOT / "skills/amazon-listing-creative/references/comparison-copy-checklist.md").read_text(encoding="utf-8")


def test_comparison_copy_checklist_requires_publishability_and_sources():
    assert "Publishable Series Comparison" in TEXT
    assert "current source" in TEXT.lower()
    assert "internal cross-brand competitor findings" in TEXT.lower()
