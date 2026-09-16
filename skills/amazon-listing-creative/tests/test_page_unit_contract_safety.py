from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
TEXT = (ROOT / "skills/amazon-listing-creative/references/page-unit-contract.md").read_text(encoding="utf-8")


def test_page_unit_contract_keeps_native_fields_and_publishability():
    assert "publishability:" in TEXT
    assert "Native fields must remain native" in TEXT
    assert "do not rasterize long copy or tables" in TEXT
