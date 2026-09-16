from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
BASE = ROOT / "skills/amazon-listing-creative/references"


def test_new_reference_files_exist():
    for name in (
        "page-story-framework.md",
        "brand-story-contract.md",
        "comparison-contract.md",
        "copy-visual-fidelity.md",
        "page-unit-contract.md",
    ):
        assert (BASE / name).is_file(), name
