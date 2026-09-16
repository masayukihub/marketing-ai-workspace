from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
TEXT = (ROOT / "skills/amazon-listing-creative/references/aplus-production-handoff.md").read_text(encoding="utf-8")


def test_aplus_handoff_includes_brand_comparison_and_fidelity():
    assert "Brand Story" in TEXT
    assert "Series Comparison" in TEXT
    assert "Internal Competitor Matrix" in TEXT
    assert "Copy ↔ Visual Fidelity" in TEXT
    assert "Gallery 完成不意味着 FULL_FLOW 完成" in TEXT
