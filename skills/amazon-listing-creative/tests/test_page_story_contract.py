from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
TEXT = (ROOT / "skills/amazon-listing-creative/references/page-story-framework.md").read_text(encoding="utf-8")


def test_page_story_starts_from_consumer_decision_questions():
    assert "Consumer Problem" in TEXT
    assert "Category Trade-off" in TEXT
    assert "Hero Promise" in TEXT
    assert "Consumer Decision Questions" in TEXT
    assert "不要从 Feature 数量反推页面结构" in TEXT
