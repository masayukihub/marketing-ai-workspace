from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
BASE = ROOT / "skills/amazon-listing-creative"


def test_page_system_contract_complete():
    assert (BASE / "references/page-story-framework.md").exists()
    assert (BASE / "references/brand-story-contract.md").exists()
    assert (BASE / "references/comparison-contract.md").exists()
    assert (BASE / "references/copy-visual-fidelity.md").exists()
