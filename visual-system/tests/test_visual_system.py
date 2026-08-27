from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[2]
SYSTEM = ROOT / "visual-system"


def load_yaml(path: Path):
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def load_router():
    path = SYSTEM / "routing/visual_router.py"
    spec = importlib.util.spec_from_file_location("visual_router", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader
    spec.loader.exec_module(module)
    return module


def contains_pattern_binding(value) -> bool:
    if isinstance(value, dict):
        for key, child in value.items():
            if str(key).lower() in {"pattern", "pattern_id", "selected_pattern", "recommended_pattern"}:
                return True
            if contains_pattern_binding(child):
                return True
    elif isinstance(value, list):
        return any(contains_pattern_binding(item) for item in value)
    return False


class VisualSystemRegressionTest(unittest.TestCase):
    def test_registry_patterns_and_weights(self):
        registry = load_yaml(SYSTEM / "registry/pattern-registry.yaml")
        weights = load_yaml(SYSTEM / "routing/weights.yaml")
        self.assertEqual(sum(weights["weights"].values()), 100)
        self.assertEqual(
            set(weights["weights"]),
            {
                "channel_fit",
                "category_fit",
                "consumer_goal_fit",
                "brand_fit",
                "information_complexity",
                "asset_availability",
                "mobile_fit",
                "historical_performance",
            },
        )
        for entry in registry["patterns"]:
            pattern = load_yaml((SYSTEM / "registry" / entry["file"]).resolve())
            self.assertEqual(pattern["pattern_id"], entry["pattern_id"])
            self.assertEqual(pattern["lifecycle"]["status"], entry["status"])
            self.assertTrue(set(pattern["prohibited_layers"]))
            self.assertTrue(pattern["sources"])

    def test_project_context_does_not_bind_pattern(self):
        for project in ("s30-mini", "lock-ultra-max"):
            context = load_yaml(ROOT / "projects" / project / "project-context.yaml")
            self.assertEqual(context["contract"], "project-context")
            self.assertFalse(contains_pattern_binding(context))

    def test_real_project_rankings_and_gates(self):
        router = load_router()
        s30 = router.build_profile(ROOT / "projects/s30-mini")
        lock = router.build_profile(ROOT / "projects/lock-ultra-max")

        self.assertEqual(s30["decision"]["selected_pattern"], "VP-AMZ-MECHANISM-PROOF")
        self.assertEqual(s30["decision"]["mode"], "HUMAN_REVIEW_REQUIRED")
        self.assertEqual(s30["freeze"]["status"], "CANDIDATE")
        self.assertFalse(s30["freeze"]["inherited"])
        self.assertIn("Product Truth", s30["boundaries"]["does_not_approve"])
        self.assertIn("Hardening", s30["boundaries"]["downstream_must_keep"])

        self.assertEqual(lock["decision"]["selected_pattern"], "VP-AMZ-JAPAN-FIT-TRUST")
        self.assertEqual(lock["decision"]["mode"], "HUMAN_REVIEW_REQUIRED")
        self.assertEqual(lock["freeze"]["status"], "NOT_AVAILABLE")
        self.assertTrue(lock["ranking"][0]["required_asset_gaps"])
        self.assertIn("Mobile QA", lock["boundaries"]["downstream_must_keep"])

    def test_approved_freeze_inheritance_and_conflicts(self):
        router = load_router()
        context = load_yaml(ROOT / "projects/s30-mini/project-context.yaml")
        context["visual_inputs"]["assets"]["official_product"] = {"status": "AVAILABLE"}
        context["visual_inputs"]["assets"]["mechanism_proof"] = {"status": "AVAILABLE"}
        pattern = load_yaml(SYSTEM / "patterns/amazon-mechanism-proof.yaml")
        freeze = {
            "status": "APPROVED",
            "active": True,
            "pattern_id": "VP-AMZ-MECHANISM-PROOF",
            "channel_scope": ["amazon_jp"],
            "human_approval": {"approved_by": "Named Reviewer", "approved_at": "2026-08-27T00:00:00Z"},
        }
        ok, reasons = router.approved_freeze_decision(context, freeze, {pattern["pattern_id"]: pattern})
        self.assertTrue(ok)
        self.assertEqual(reasons, [])

        context["primary_channel"] = "edm"
        ok, reasons = router.approved_freeze_decision(context, freeze, {pattern["pattern_id"]: pattern})
        self.assertFalse(ok)
        self.assertIn("Current channel conflicts with Freeze scope", reasons)

        context["primary_channel"] = "amazon_jp"
        pattern["lifecycle"]["status"] = "DEPRECATED"
        ok, reasons = router.approved_freeze_decision(context, freeze, {pattern["pattern_id"]: pattern})
        self.assertFalse(ok)
        self.assertIn("Freeze Pattern is DEPRECATED", reasons)

    def test_reference_ingestion_non_copy_boundary(self):
        ingestion = load_yaml(SYSTEM / "references/reference-ingestion.yaml")
        self.assertEqual(
            ingestion["workflow"],
            [
                "receive_reference",
                "analyze_source_and_rights",
                "extract_reusable_principles",
                "normalize_pattern_candidate",
                "tag_fit_and_asset_requirements",
                "register_as_candidate",
                "human_review",
                "validate_before_reuse",
            ],
        )
        self.assertTrue(
            {"third_party_logo", "original_copy", "third_party_image", "trade_dress", "complete_layout"}.issubset(
                set(ingestion["never_store_as_pattern"])
            )
        )

    def test_existing_skill_entrypoints_keep_visual_and_release_gates(self):
        amazon = (ROOT / "skills/jp-commerce-content-flow/SKILL.md").read_text(encoding="utf-8")
        edm = (ROOT / "skills/switchbot-japan-edm/SKILL.md").read_text(encoding="utf-8")
        for phrase in (
            "resolve_project",
            "load_visual_freeze",
            "load_visual_profile",
            "visual_router_if_needed",
            "apply_channel_adapter",
            "Product Truth",
            "Claim Gate",
            "Product Layer",
            "Hardening",
            "Mobile QA",
        ):
            self.assertIn(phrase, amazon)
        self.assertIn("ADAPTER-EDM-JP", edm)
        self.assertIn("Final Human", edm)
        self.assertIn("ESP Gate", edm)


if __name__ == "__main__":
    unittest.main()
