from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
REFS = ROOT / "skills/amazon-listing-creative/references"
INDEX = (REFS / "README.md").read_text(encoding="utf-8")


def test_reference_index_consistency():
    for name in ("page-story-framework.md", "brand-story-contract.md", "comparison-contract.md", "copy-visual-fidelity.md"):
        assert name in INDEX
        assert (REFS / name).exists()
