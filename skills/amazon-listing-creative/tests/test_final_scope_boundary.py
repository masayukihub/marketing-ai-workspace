from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
TEXT = (ROOT / "skills/amazon-listing-creative/references/implementation-summary.md").read_text(encoding="utf-8")


def test_final_scope_boundary():
    assert "not the production runtime" in TEXT
    assert "Product Truth" in TEXT
