from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
TEXT = (ROOT / "skills/amazon-listing-creative/references/aplus-production-handoff.md").read_text(encoding="utf-8")


def test_full_page_handoff_tracks_brand_comparison_and_native_copy():
    assert "Brand Story" in TEXT
    assert "Series Comparison" in TEXT
    assert "Native Copy" in TEXT
    assert "Copy-Visual Fidelity" in TEXT
