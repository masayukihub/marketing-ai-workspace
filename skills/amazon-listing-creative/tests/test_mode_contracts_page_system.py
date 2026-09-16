from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
TEXT = (ROOT / "skills/amazon-listing-creative/references/mode-contracts.md").read_text(encoding="utf-8")


def test_mode_contracts_include_page_creative_system():
    assert "Page Creative System" in TEXT
    assert "Why This Product Exists" in TEXT
    assert "Brand Story" in TEXT
    assert "Publishable Series Comparison" in TEXT
    assert "Copy ↔ Visual Fidelity Gate" in TEXT
