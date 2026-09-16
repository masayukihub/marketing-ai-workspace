from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
TEXT = (ROOT / "skills/amazon-listing-creative/SKILL.md").read_text(encoding="utf-8")


def test_page_role_smoke_guard():
    assert "Gallery" in TEXT
    assert "A+" in TEXT
    assert "Brand Story" in TEXT
    assert "Series Comparison" in TEXT
    assert "FAQ" in TEXT
