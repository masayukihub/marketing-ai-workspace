from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
TEXT = (ROOT / "skills/amazon-listing-creative/references/copy-render-gap-examples.md").read_text(encoding="utf-8")


def test_visual_proof_examples_cover_scale_mechanism_performance_automation():
    for token in ("## Scale", "## Mechanism", "## Performance number", "## Automation"):
        assert token in TEXT
