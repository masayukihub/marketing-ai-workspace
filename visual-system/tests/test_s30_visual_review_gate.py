from __future__ import annotations

import hashlib
import unittest
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[2]
REVIEW = ROOT / "projects/s30-mini/reviews/visual-pattern-recipe-20260827"


def load_yaml(path: Path):
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


class S30VisualPatternRecipeReviewGateTest(unittest.TestCase):
    def test_review_package_is_complete(self):
        expected = {
            "review.html",
            "decision-template.yaml",
            "asset-gap-register.yaml",
            "review-scope.md",
            "README.zh-CN.md",
        }
        self.assertTrue(expected.issubset({path.name for path in REVIEW.iterdir()}))

    def test_human_decision_fields_are_blank(self):
        decision = load_yaml(REVIEW / "decision-template.yaml")
        self.assertEqual(decision["review_status"], "PENDING_HUMAN")
        self.assertIsNone(decision["reviewer"]["name"])
        self.assertIsNone(decision["reviewer"]["reviewed_at"])
        for review_object in decision["decisions"].values():
            self.assertIsNone(review_object["decision"])
            self.assertIsNone(review_object["modification_notes"])
        optional = decision["decisions"]["optional_sections"]
        for key in ("consumer_problem", "lifestyle_context", "app_automation", "legal_note"):
            self.assertIsNone(optional[key])
        self.assertIsNone(decision["decisions"]["approval_scope"]["project_pilot_use"])
        self.assertIsNone(decision["next_gate"])
        self.assertEqual(
            decision["decision_options"],
            ["APPROVE", "APPROVE_WITH_MODIFICATION", "REJECT", "DEFER"],
        )

    def test_recommendations_do_not_promote_governance(self):
        decision = load_yaml(REVIEW / "decision-template.yaml")
        lifecycle = decision["decisions"]["lifecycle"]
        freeze = decision["decisions"]["visual_freeze"]
        scope = decision["decisions"]["approval_scope"]
        self.assertEqual(lifecycle["recipe_status"], "KEEP_CANDIDATE")
        self.assertEqual(lifecycle["section_pattern_status"], "KEEP_CANDIDATE")
        self.assertFalse(lifecycle["promotion_approved"])
        self.assertFalse(freeze["create_edm_freeze"])
        self.assertFalse(scope["reusable_pattern_validation"])
        self.assertFalse(scope["production_use"])
        self.assertFalse(scope["send_or_publish"])
        self.assertEqual(decision["recommended_decisions"]["production"], "REMAIN_BLOCKED")

    def test_asset_gap_register_records_exact_review_scope(self):
        register = load_yaml(REVIEW / "asset-gap-register.yaml")
        items = {item["item"]: item for item in register["items"]}
        self.assertEqual(
            set(items),
            {
                "Approved Product Truth",
                "Approved JP Claim",
                "Official Product Asset",
                "Approved Mechanism Proof",
                "Optional Lifestyle Asset",
                "Optional App / UI Asset",
                "Verified CTA Destination",
                "Legal / Footer Inputs",
            },
        )
        for item in items.values():
            self.assertEqual(item["owner"], "TBD")
            self.assertEqual(item["due_date"], "TBD")
            self.assertTrue(item["source"])
            self.assertTrue(item["blocking_scope"])
        self.assertEqual(register["summary"]["gaps_auto_resolved"], 0)

    def test_review_html_is_marketing_readable_and_human_blank(self):
        html = (REVIEW / "review.html").read_text(encoding="utf-8")
        for phrase in (
            "Project Visual DNA",
            "Channel Comparison",
            "Recipe Review",
            "Product-first Hero",
            "REQUIRED_WHEN_APPROVED_EVIDENCE_AVAILABLE",
            "TPL-LAUNCH-A",
            "CANDIDATE_CONDITIONAL_MATCH",
            "Architecture Approval ≠ Pattern Lifecycle Promotion",
            "S30_VISUAL_PATTERN_RECIPE_HUMAN_REVIEW",
        ):
            self.assertIn(phrase, html)
        self.assertEqual(html.count('data-human-decision=""'), 9)
        self.assertNotIn('data-human-decision="APPROVE', html)

    def test_visual_governance_state_remains_unchanged(self):
        decision = load_yaml(REVIEW / "decision-template.yaml")
        expected_hashes = decision["baseline"]["protected_contract_hashes"]
        protected_contracts = {
            "approved_asset_context": ROOT / "projects/s30-mini/project-context.yaml",
            "visual_profile": ROOT / "projects/s30-mini/visual-profile.yaml",
            "visual_freeze": ROOT / "projects/s30-mini/visual-freeze.yaml",
            "recipe": ROOT / "visual-system/patterns/recipes/edm-product-launch-proof/recipe.yaml",
            "section_pattern_registry": ROOT / "visual-system/registry/section-pattern-registry.yaml",
            "recipe_registry": ROOT / "visual-system/registry/page-recipe-registry.yaml",
        }
        for contract, path in protected_contracts.items():
            self.assertEqual(sha256(path), expected_hashes[contract], contract)
        s30 = load_yaml(ROOT / "projects/s30-mini/visual-profile.yaml")
        freeze = load_yaml(ROOT / "projects/s30-mini/visual-freeze.yaml")
        lock = load_yaml(ROOT / "projects/lock-ultra-max/visual-profile.yaml")
        recipe = load_yaml(ROOT / "visual-system/patterns/recipes/edm-product-launch-proof/recipe.yaml")
        sections = load_yaml(ROOT / "visual-system/registry/section-pattern-registry.yaml")
        self.assertEqual(s30["decision"]["score"], 89.7)
        self.assertEqual(s30["channel_assignments"]["edm"]["execution_readiness"]["status"], "BLOCKED_BY_ASSET")
        self.assertFalse(s30["channel_assignments"]["edm"]["auto_apply"]["eligible"])
        self.assertEqual(freeze["status"], "CANDIDATE")
        self.assertFalse(freeze["active"])
        self.assertIsNone(freeze["human_approval"]["approved_by"])
        self.assertEqual(lock["decision"]["score"], 81.1)
        self.assertFalse((ROOT / "projects/lock-ultra-max/visual-freeze.yaml").exists())
        self.assertEqual(recipe["lifecycle"]["status"], "CANDIDATE")
        self.assertTrue(all(item["status"] == "CANDIDATE" for item in sections["patterns"]))

    def test_product_truth_and_claim_hashes_remain_unchanged(self):
        baseline = load_yaml(ROOT / "visual-system/tests/phase2a-protected-hashes.yaml")
        for group in ("product_truth", "claim"):
            for relative, expected in baseline[group].items():
                self.assertEqual(sha256(ROOT / relative), expected, relative)

    def test_review_package_has_no_local_absolute_paths(self):
        forbidden = ("/" + "Users" + "/", "/" + "home" + "/")
        offenders = []
        for path in [*REVIEW.iterdir(), Path(__file__)]:
            if path.is_file():
                text = path.read_text(encoding="utf-8", errors="ignore")
                if any(prefix in text for prefix in forbidden):
                    offenders.append(str(path.relative_to(ROOT)))
        self.assertEqual(offenders, [])


if __name__ == "__main__":
    unittest.main()
