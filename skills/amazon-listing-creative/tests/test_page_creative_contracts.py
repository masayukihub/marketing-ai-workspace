from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
SKILL = ROOT / "skills/amazon-listing-creative"


def read(path: str) -> str:
    return (SKILL / path).read_text(encoding="utf-8")


def test_skill_requires_page_story_brand_comparison_and_fidelity():
    text = read("SKILL.md")
    for token in (
        "Page Story Spine",
        "Why This Product Exists",
        "Brand Story",
        "Internal Competitor Matrix",
        "Publishable Series Comparison",
        "Copy ↔ Visual Fidelity Contract",
        "proof_visible_without_copy",
    ):
        assert token in text


def test_page_story_framework_is_consumer_question_first():
    text = read("references/page-story-framework.md")
    for question in (
        "What is it?",
        "Why should I care?",
        "Why is it different?",
        "Can I believe it?",
        "Is it for me?",
        "Which one should I buy?",
        "Why this brand?",
    ):
        assert question in text
    assert "不要从 Feature 数量反推页面结构" in text


def test_brand_story_separates_brand_promise_from_product_philosophy():
    text = read("references/brand-story-contract.md")
    assert "Brand Promise" in text
    assert "Product Philosophy" in text
    assert "Ecosystem / Trust" in text
    assert "BRAND_STORY_DUPLICATES_PRODUCT_STORY" in text


def test_comparison_separates_internal_competitors_from_publishable_series():
    text = read("references/comparison-contract.md")
    assert "Internal Competitor Matrix" in text
    assert "Publishable Series Comparison" in text
    assert "INTERNAL_ONLY" in text
    assert "NOT_PUBLISHABLE_AS_AMAZON_A_PLUS" in text
    assert "Recommended For" in text
    assert "Home / Usage Fit" in text


def test_copy_visual_contract_has_hard_fail_gate():
    text = read("references/copy-visual-fidelity.md")
    for gate in ("PASS", "WEAK", "FAIL"):
        assert gate in text
    assert "proof_visible_without_copy" in text
    assert "AI Render 不负责" in text
    assert "FAIL 不得进入 Whole-set Approval" in text


def test_output_templates_expose_page_level_review_artifacts():
    text = read("references/output-templates.md")
    for heading in (
        "## Page Story Map",
        "## Brand Story Brief",
        "## Series Comparison Matrix",
        "## Copy Visual Fidelity",
    ):
        assert heading in text
    assert "Copy-Visual Fidelity" in text
