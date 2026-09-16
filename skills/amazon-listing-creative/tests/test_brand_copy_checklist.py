from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
TEXT = (ROOT / "skills/amazon-listing-creative/references/brand-copy-checklist.md").read_text(encoding="utf-8")


def test_brand_copy_checklist_rejects_unsupported_superlatives():
    assert "No.1" in TEXT
    assert "product philosophy" in TEXT.lower()
    assert "ecosystem" in TEXT.lower()
