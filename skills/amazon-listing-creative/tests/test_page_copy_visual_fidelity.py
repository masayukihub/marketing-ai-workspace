from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
TEXT = (ROOT / "skills/amazon-listing-creative/references/output-templates.md").read_text(encoding="utf-8")


def test_listing_brief_includes_visual_proof_and_fidelity_target():
    assert "- Visual Proof:" in TEXT
    assert "- Copy-Visual Fidelity Target:" in TEXT
