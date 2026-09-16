from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
SKILL = (ROOT / "skills/amazon-listing-creative/SKILL.md").read_text(encoding="utf-8")
MODE = (ROOT / "skills/amazon-listing-creative/references/mode-contracts.md").read_text(encoding="utf-8")


def test_gallery_count_comes_from_spec():
    assert "不得固定机械要求 Image 1–9" in SKILL
    assert "不得固定要求 9 张" in MODE
