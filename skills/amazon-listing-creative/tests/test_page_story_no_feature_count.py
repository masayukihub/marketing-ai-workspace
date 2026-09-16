from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
TEXT = (ROOT / "skills/amazon-listing-creative/references/page-story-framework.md").read_text(encoding="utf-8")


def test_page_planning_is_not_feature_count_driven():
    assert "不要从 Feature 数量反推页面结构" in TEXT
    assert "Feature 列表错当故事" in TEXT
