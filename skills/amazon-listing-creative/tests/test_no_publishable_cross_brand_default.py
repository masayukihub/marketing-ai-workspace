from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
TEXT = (ROOT / "skills/amazon-listing-creative/references/comparison-contract.md").read_text(encoding="utf-8")


def test_cross_brand_default_is_internal_only():
    assert "默认状态" in TEXT
    assert "INTERNAL_ONLY" in TEXT
    assert "不得直接作为 Amazon 发布资产" in TEXT
