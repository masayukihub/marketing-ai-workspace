from __future__ import annotations

import importlib.util
import tempfile
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


def walk_strings(value):
    if isinstance(value, str):
        yield value
    elif isinstance(value, dict):
        for child in value.values():
            yield from walk_strings(child)
    elif isinstance(value, list):
        for child in value:
            yield from walk_strings(child)


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
        self.assertEqual(s30["decision"]["score"], 89.7)
        self.assertEqual(s30["decision"]["mode"], "HUMAN_REVIEW_REQUIRED")
        self.assertEqual(s30["freeze"]["status"], "CANDIDATE")
        self.assertFalse(s30["freeze"]["inherited"])
        self.assertIn("Product Truth", s30["boundaries"]["does_not_approve"])
        self.assertIn("Hardening", s30["boundaries"]["downstream_must_keep"])

        self.assertEqual(lock["decision"]["selected_pattern"], "VP-AMZ-JAPAN-FIT-TRUST")
        self.assertEqual(lock["decision"]["score"], 81.1)
        self.assertEqual(lock["decision"]["mode"], "HUMAN_REVIEW_REQUIRED")
        self.assertEqual(lock["freeze"]["status"], "NOT_AVAILABLE")
        self.assertTrue(lock["ranking"][0]["required_asset_gaps"])
        self.assertIn("Mobile QA", lock["boundaries"]["downstream_must_keep"])

        freeze = load_yaml(ROOT / "projects/s30-mini/visual-freeze.yaml")
        self.assertEqual(freeze["status"], "CANDIDATE")
        self.assertFalse(freeze["active"])
        self.assertIsNone(freeze["human_approval"]["approved_by"])
        self.assertFalse((ROOT / "projects/lock-ultra-max/visual-freeze.yaml").exists())

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

    def test_approved_freeze_rejected_when_pattern_channel_is_incompatible(self):
        router = load_router()
        context = load_yaml(ROOT / "projects/s30-mini/project-context.yaml")
        context["primary_channel"] = "edm"
        context["visual_inputs"]["assets"]["official_product"] = {"status": "AVAILABLE"}
        context["visual_inputs"]["assets"]["mechanism_proof"] = {"status": "AVAILABLE"}
        pattern = load_yaml(SYSTEM / "patterns/amazon-mechanism-proof.yaml")
        freeze = {
            "status": "APPROVED",
            "active": True,
            "pattern_id": "VP-AMZ-MECHANISM-PROOF",
            "channel_scope": ["edm"],
            "human_approval": {"approved_by": "Named Reviewer", "approved_at": "2026-08-27T00:00:00Z"},
        }
        ok, reasons = router.approved_freeze_decision(context, freeze, {pattern["pattern_id"]: pattern})
        self.assertFalse(ok)
        self.assertIn("Current channel is not supported by Freeze Pattern", reasons)

    def test_committed_visual_contracts_do_not_contain_local_absolute_paths(self):
        router = load_router()
        contracts = [
            ROOT / "projects/s30-mini/project-context.yaml",
            ROOT / "projects/s30-mini/visual-profile.yaml",
            ROOT / "projects/s30-mini/visual-freeze.yaml",
            ROOT / "projects/lock-ultra-max/project-context.yaml",
            ROOT / "projects/lock-ultra-max/visual-profile.yaml",
            SYSTEM / "registry/reference-registry.yaml",
        ]
        for path in contracts:
            data = load_yaml(path)
            offenders = [value for value in walk_strings(data) if router.is_local_absolute_path(value)]
            self.assertEqual(offenders, [], f"local absolute path in {path}: {offenders}")

    def test_generated_visual_profile_does_not_output_local_absolute_paths(self):
        router = load_router()
        context = load_yaml(ROOT / "projects/s30-mini/project-context.yaml")
        context["project_id"] = "absolute-path-normalization-test"
        context["sources"].extend(
            [
                str(ROOT / "memory/project-memory/s30-mini/PROJECT.md"),
                str(Path("/").joinpath("Users", "example", "Documents", "private-evidence", "source.json")),
            ]
        )
        with tempfile.TemporaryDirectory(prefix="visual-router-test-", dir=ROOT) as directory:
            project_dir = Path(directory)
            (project_dir / "project-context.yaml").write_text(
                yaml.safe_dump(context, allow_unicode=True, sort_keys=False), encoding="utf-8"
            )
            profile = router.build_profile(project_dir)
        offenders = [value for value in walk_strings(profile) if router.is_local_absolute_path(value)]
        self.assertEqual(offenders, [])
        self.assertIn("memory/project-memory/s30-mini/PROJECT.md", profile["sources"])
        self.assertTrue(
            any(
                isinstance(source, dict)
                and source.get("locator_status") == "REDACTED_LOCAL_PATH"
                and source.get("availability") == "LOCAL_ONLY"
                for source in profile["sources"]
            )
        )

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
