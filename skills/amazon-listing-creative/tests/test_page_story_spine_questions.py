from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
TEXT = (ROOT / "skills/amazon-listing-creative/SKILL.md").read_text(encoding="utf-8")


def test_page_story_spine_has_all_decision_questions():
    for q in (
        "What is it?",
        "Why should I care?",
        "Why is it different?",
        "Can I believe it?",
        "Is it for me?",
        "Which one should I buy?",
        "Why this brand?",
    ):
        assert q in TEXT
