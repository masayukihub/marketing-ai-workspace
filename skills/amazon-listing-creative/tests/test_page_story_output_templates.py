from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
TEXT = (ROOT / "skills/amazon-listing-creative/references/output-templates.md").read_text(encoding="utf-8")


def test_output_templates_cover_page_system():
    assert "## Page Story Map" in TEXT
    assert "## Brand Story Brief" in TEXT
    assert "## Series Comparison Matrix" in TEXT
    assert "## Copy Visual Fidelity" in TEXT
