from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
TEXT = (ROOT / "skills/amazon-listing-creative/references/implementation-summary.md").read_text(encoding="utf-8")


def test_upgrade_summary_contract():
    assert "Page-level consumer decision story" in TEXT
    assert "Dedicated Brand Story contract" in TEXT
    assert "Copy ↔ Visual Fidelity hard gate" in TEXT
