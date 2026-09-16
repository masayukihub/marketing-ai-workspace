from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
TEXT = (ROOT / "skills/amazon-listing-creative/references/page-story-framework.md").read_text(encoding="utf-8")


def test_story_map_maps_question_to_unit_and_proof():
    assert "Consumer Question" in TEXT
    assert "Story Role" in TEXT
    assert "Main Message" in TEXT
    assert "Evidence / Proof" in TEXT
    assert "Page Unit" in TEXT
