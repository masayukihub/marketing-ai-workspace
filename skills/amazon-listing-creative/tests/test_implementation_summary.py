from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
TEXT = (ROOT / "skills/amazon-listing-creative/references/implementation-summary.md").read_text(encoding="utf-8")


def test_upgrade_keeps_production_runtime_boundary():
    assert "jp-commerce-content-flow" in TEXT
    assert "Product Truth" in TEXT
    assert "Amazon Renderer / delivery runtime is unchanged" in TEXT
