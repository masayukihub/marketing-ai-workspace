from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
SKILL = (ROOT / "skills/amazon-listing-creative/SKILL.md").read_text(encoding="utf-8")


def test_page_system_does_not_replace_main_runtime_or_truth():
    assert "不是第二套完整 Listing Runtime" in SKILL
    assert "Product Truth" in SKILL
    assert "不得把竞品研究表直接当成可发布 Comparison" in SKILL
