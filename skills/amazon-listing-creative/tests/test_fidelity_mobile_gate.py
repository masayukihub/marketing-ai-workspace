from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
TEXT = (ROOT / "skills/amazon-listing-creative/references/copy-visual-fidelity.md").read_text(encoding="utf-8")


def test_mobile_proof_visibility_is_part_of_fidelity_gate():
    assert "mobile:" in TEXT
    assert "proof_visible:" in TEXT
    assert "Mobile 不是只检查文字能否读到" in TEXT
