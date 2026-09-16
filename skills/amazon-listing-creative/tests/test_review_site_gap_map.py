from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
TEXT = (ROOT / "skills/amazon-listing-creative/references/review-site-gap-map.md").read_text(encoding="utf-8")


def test_gap_map_does_not_promote_reference_site_to_truth():
    assert "不复制具体页面视觉" in TEXT
    assert "不把参考站内容当 Product Truth" in TEXT
    assert "不复制页面布局、图像、文案或 Trade Dress" in TEXT
