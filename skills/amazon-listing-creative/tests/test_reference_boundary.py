from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
TEXT = (ROOT / "skills/amazon-listing-creative/references/README.md").read_text(encoding="utf-8")


def test_reference_boundary_is_explicit():
    assert "Reference pages and competitor examples may inform structure only" in TEXT
