from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
TEXT = (ROOT / "skills/amazon-listing-creative/references/README.md").read_text(encoding="utf-8")


def test_reference_index_lists_new_contracts():
    for name in (
        "page-story-framework.md",
        "brand-story-contract.md",
        "comparison-contract.md",
        "copy-visual-fidelity.md",
    ):
        assert name in TEXT
