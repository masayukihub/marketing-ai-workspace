from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
TEXT = (ROOT / "skills/amazon-listing-creative/references/copy-visual-fidelity.md").read_text(encoding="utf-8")


def test_copy_visual_fail_blocks_whole_set_approval():
    assert "PASS" in TEXT
    assert "WEAK" in TEXT
    assert "FAIL" in TEXT
    assert "FAIL 不得进入 Whole-set Approval" in TEXT
    assert "proof_visible_without_copy" in TEXT
