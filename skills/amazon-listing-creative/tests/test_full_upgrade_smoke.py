from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
BASE = ROOT / "skills/amazon-listing-creative"


def test_full_upgrade_smoke_guard():
    refs = BASE / "references"
    for name in (
        "page-story-framework.md",
        "brand-story-contract.md",
        "comparison-contract.md",
        "copy-visual-fidelity.md",
    ):
        assert (refs / name).exists()
