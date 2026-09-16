from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
TEXT = (ROOT / "skills/amazon-listing-creative/SKILL.md").read_text(encoding="utf-8")


def test_page_creative_system_remains_internal_module():
    assert "内部创意模块" in TEXT
    assert "不是第二套完整 Listing Runtime" in TEXT
    assert "jp-commerce-content-flow" in TEXT
