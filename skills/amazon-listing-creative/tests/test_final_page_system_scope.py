from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
TEXT = (ROOT / "skills/amazon-listing-creative/SKILL.md").read_text(encoding="utf-8")


def test_final_page_system_scope_guard():
    assert "Page Creative System" in TEXT
    assert "完整生产由主入口执行" in TEXT
