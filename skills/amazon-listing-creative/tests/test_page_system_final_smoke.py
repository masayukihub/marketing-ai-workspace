from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
TEXT = (ROOT / "skills/amazon-listing-creative/SKILL.md").read_text(encoding="utf-8")


def test_page_system_final_smoke():
    assert "Why This Product Exists" in TEXT
    assert "Copy ↔ Visual Fidelity Contract" in TEXT
