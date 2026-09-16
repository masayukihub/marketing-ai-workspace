from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
TEXT = (ROOT / "skills/amazon-listing-creative/references/copy-render-gap-examples.md").read_text(encoding="utf-8")


def test_copy_render_examples_are_qa_patterns_only():
    assert "These examples illustrate QA logic only" in TEXT
    assert "Real assets must be evaluated against current Product Truth" in TEXT
