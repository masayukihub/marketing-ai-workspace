from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
TEXT = (ROOT / "skills/amazon-listing-creative/references/mobile-fidelity-checklist.md").read_text(encoding="utf-8")


def test_mobile_qa_checks_proof_not_only_text():
    assert "semantic proof" in TEXT
    assert "Scale cues" in TEXT
    assert "Mechanism detail" in TEXT
    assert "desktop PASS does not automatically imply mobile PASS" in TEXT
