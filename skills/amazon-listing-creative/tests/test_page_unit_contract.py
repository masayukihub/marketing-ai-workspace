from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
TEXT = (ROOT / "skills/amazon-listing-creative/references/page-unit-contract.md").read_text(encoding="utf-8")


def test_page_unit_contract_requires_consumer_question_and_publishability():
    assert "consumer_question:" in TEXT
    assert "visual_proof:" in TEXT
    assert "publishability:" in TEXT
    assert "brand_story" in TEXT
    assert "series_comparison" in TEXT
    assert "do not rasterize long copy or tables" in TEXT
