from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
TEXT = (ROOT / "skills/amazon-listing-creative/references/implementation-summary.md").read_text(encoding="utf-8")


def test_upgrade_is_method_only():
    assert "changes the internal creative method, not the production runtime" in TEXT
