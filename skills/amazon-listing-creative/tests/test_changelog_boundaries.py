from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
TEXT = (ROOT / "skills/amazon-listing-creative/references/CHANGELOG.md").read_text(encoding="utf-8")


def test_changelog_states_non_business_scope():
    assert "No Product Truth" in TEXT
    assert "approved claims" in TEXT
    assert "production runtime" in TEXT
