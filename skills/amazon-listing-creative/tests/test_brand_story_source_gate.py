from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
TEXT = (ROOT / "skills/amazon-listing-creative/references/brand-story-contract.md").read_text(encoding="utf-8")


def test_brand_story_requires_formal_source():
    assert "必须来自当前正式品牌资料或已接受项目 Decision" in TEXT
    assert "Pending Verification" in TEXT
