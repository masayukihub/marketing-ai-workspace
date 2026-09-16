from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
TEXT = (ROOT / "skills/amazon-listing-creative/references/qa-summary-contract.md").read_text(encoding="utf-8")


def test_qa_summary_blocks_on_hard_failures():
    assert "Page Story" in TEXT
    assert "Brand Story" in TEXT
    assert "Series Comparison" in TEXT
    assert "Copy ↔ Visual Fidelity" in TEXT
    assert "blocks whole-set approval" in TEXT
