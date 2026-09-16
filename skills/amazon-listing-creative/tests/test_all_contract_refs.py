from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
TEXT = (ROOT / "skills/amazon-listing-creative/SKILL.md").read_text(encoding="utf-8")


def test_all_page_system_contract_refs_are_linked():
    for ref in (
        "page-story-framework.md",
        "brand-story-contract.md",
        "comparison-contract.md",
        "copy-visual-fidelity.md",
    ):
        assert ref in TEXT
