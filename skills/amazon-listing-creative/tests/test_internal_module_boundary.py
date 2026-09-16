from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
TEXT = (ROOT / "skills/amazon-listing-creative/SKILL.md").read_text(encoding="utf-8")


def test_internal_module_boundary_is_explicit():
    assert "内部创意方法" in TEXT
    assert "不是第二套完整 Listing Runtime" in TEXT
    assert "完整生产由主入口执行" in TEXT
