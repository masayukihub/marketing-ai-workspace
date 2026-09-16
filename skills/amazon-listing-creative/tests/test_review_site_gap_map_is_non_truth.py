from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
TEXT = (ROOT / "skills/amazon-listing-creative/references/review-site-gap-map.md").read_text(encoding="utf-8")


def test_review_site_gap_map_is_not_truth_source():
    assert "不把参考站内容当 Product Truth" in TEXT
    assert "不复制页面布局、图像、文案或 Trade Dress" in TEXT
