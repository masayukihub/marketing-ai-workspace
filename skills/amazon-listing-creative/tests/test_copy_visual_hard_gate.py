from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
TEXT = (ROOT / "skills/amazon-listing-creative/SKILL.md").read_text(encoding="utf-8")


def test_copy_visual_fail_is_hard_blocker():
    assert "Copy-Visual Fidelity 为 FAIL" in TEXT
    assert "Blocked" in TEXT
