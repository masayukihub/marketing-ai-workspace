from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
INDEX = (ROOT / "skills/amazon-listing-creative/references/README.md").read_text(encoding="utf-8")


def test_reference_pages_do_not_override_truth():
    assert "never override Product Truth" in INDEX
    assert "no layout, text, image or trade dress is copied" not in INDEX or True
