from __future__ import annotations

import copy
import hashlib
import importlib.util
import subprocess
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


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def local_absolute_path_counts() -> dict[str, int]:
    result = subprocess.run(
        ["git", "ls-files", "--cached", "--others", "--exclude-standard", "-z"],
        cwd=ROOT,
        check=True,
        capture_output=True,
    )
    counts = {}
    user_prefix = "/" + "Users" + "/"
    home_prefix = "/" + "home" + "/"
    for raw_path in result.stdout.split(b"\0"):
        if not raw_path:
            continue
        path = ROOT / raw_path.decode("utf-8")
        if not path.is_file():
            continue
        text = path.read_bytes().decode("utf-8", errors="ignore")
        count = text.count(user_prefix) + text.count(home_prefix)
        if count:
            counts[str(path.relative_to(ROOT))] = count
    return counts


def build_profile_for_context(router, context, freeze=None):
    with tempfile.TemporaryDirectory(prefix="visual-router-context-", dir=ROOT) as directory:
        project_dir = Path(directory)
        (project_dir / "project-context.yaml").write_text(
            yaml.safe_dump(context, allow_unicode=True, sort_keys=False), encoding="utf-8"
        )
        if freeze is not None:
            (project_dir / "visual-freeze.yaml").write_text(
                yaml.safe_dump(freeze, allow_unicode=True, sort_keys=False), encoding="utf-8"
            )
        return router.build_profile(project_dir)


class VisualSystemRegressionTest(unittest.TestCase):
    def test_visual_profile_schema_v11_required_fields(self):
        schema = load_yaml(SYSTEM / "registry/project-contract.schema.json")
        required = set(schema["$defs"]["visualProfile"]["required"])
        for project in ("s30-mini", "lock-ultra-max"):
            profile = load_yaml(ROOT / "projects" / project / "visual-profile.yaml")
            self.assertEqual(profile["schema_version"], "1.1")
            self.assertTrue(required.issubset(profile), f"missing v1.1 fields in {project}")

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

    def test_edm_master_ingestion_remains_structural_candidate(self):
        directory = SYSTEM / "references/ingested/switchbot-edm-master-v1"
        candidate = load_yaml(directory / "candidate-pattern.yaml")
        originality = load_yaml(directory / "originality-check.yaml")
        metadata = load_yaml(directory / "source-metadata.yaml")
        self.assertEqual(candidate["lifecycle"]["status"], "CANDIDATE")
        self.assertFalse(candidate["lifecycle"]["auto_promotion_allowed"])
        self.assertEqual(metadata["locator_status"], "REPOSITORY_RELATIVE")
        self.assertEqual(originality["status"], "PASS")
        self.assertTrue(all(value == "NOT_STORED" for value in originality["rejected_layers"].values()))
        self.assertNotIn("recovered_html", originality["stored_layers"])

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

    def test_cross_channel_inherits_visual_dna_not_layout(self):
        router = load_router()
        profile = router.build_profile(ROOT / "projects/s30-mini")
        amazon = profile["channel_assignments"]["amazon_jp"]
        edm = profile["channel_assignments"]["edm"]
        self.assertEqual(profile["project_visual_dna"]["status"], "ROUTER_GENERATED_CANDIDATE")
        self.assertTrue(amazon["inheritance"]["project_visual_dna"])
        self.assertTrue(edm["inheritance"]["project_visual_dna"])
        self.assertFalse(edm["inheritance"]["layout_from_other_channel"])
        self.assertNotEqual(amazon["adapter"]["layout_contract"], edm["adapter"]["layout_contract"])

    def test_cross_channel_inherits_information_strategy_not_identical_density(self):
        router = load_router()
        profile = router.build_profile(ROOT / "projects/s30-mini")
        dna = profile["project_visual_dna"]
        amazon = profile["channel_assignments"]["amazon_jp"]
        edm = profile["channel_assignments"]["edm"]
        self.assertNotIn("information_density", dna)
        self.assertEqual(
            dna["information_strategy"],
            {"source_complexity": "high", "hierarchy_principle": "structured_progressive_disclosure"},
        )
        self.assertEqual(amazon["channel_information_density"], "high_structured")
        self.assertEqual(edm["channel_information_density"], "medium_selective")
        self.assertNotEqual(amazon["channel_information_density"], edm["channel_information_density"])
        self.assertTrue(edm["inheritance"]["information_strategy"])
        self.assertFalse(edm["inheritance"]["channel_information_density"])

    def test_high_pattern_match_low_readiness_does_not_auto_produce(self):
        router = load_router()
        edm = router.build_profile(ROOT / "projects/s30-mini")["channel_assignments"]["edm"]
        self.assertEqual(edm["pattern_match"]["status"], "HIGH")
        self.assertEqual(edm["execution_readiness"]["status"], "BLOCKED_BY_ASSET")
        self.assertLess(edm["execution_readiness"]["score"], edm["pattern_match"]["score"])
        self.assertFalse(edm["auto_apply"]["eligible"])

    def test_candidate_freeze_does_not_apply_to_edm(self):
        router = load_router()
        edm = router.build_profile(ROOT / "projects/s30-mini")["channel_assignments"]["edm"]
        self.assertEqual(edm["freeze"]["status"], "CANDIDATE")
        self.assertFalse(edm["freeze"]["applied"])
        self.assertIn("FREEZE_CHANNEL_SCOPE_EXCLUDES_CHANNEL", edm["freeze"]["reason_codes"])
        self.assertIn("FREEZE_PATTERN_CHANNEL_INCOMPATIBLE", edm["freeze"]["reason_codes"])

    def test_out_of_scope_candidate_freeze_is_recorded_but_not_readiness_blocker(self):
        router = load_router()
        context = load_yaml(ROOT / "projects/s30-mini/project-context.yaml")
        with_freeze = router.build_profile(ROOT / "projects/s30-mini")["channel_assignments"]["edm"]
        without_freeze = build_profile_for_context(router, context)["channel_assignments"]["edm"]
        self.assertEqual(with_freeze["freeze"]["applicability"], "NOT_APPLICABLE_TO_CHANNEL")
        self.assertFalse(with_freeze["freeze"]["applied"])
        self.assertNotIn(
            "Candidate Freeze is not an active APPROVED Freeze", with_freeze["blocking_reasons"]
        )
        self.assertEqual(with_freeze["execution_readiness"]["score"], without_freeze["execution_readiness"]["score"])

    def test_in_scope_candidate_freeze_remains_human_review_blocker(self):
        router = load_router()
        amazon = router.build_profile(ROOT / "projects/s30-mini")["channel_assignments"]["amazon_jp"]
        self.assertEqual(amazon["freeze"]["applicability"], "APPLICABLE_TO_CHANNEL")
        self.assertFalse(amazon["freeze"]["applied"])
        self.assertIn("Candidate Freeze is not an active APPROVED Freeze", amazon["blocking_reasons"])
        self.assertIn("CANDIDATE_FREEZE_NOT_APPLIED", amazon["reason_codes"])

    def test_edm_recipe_requires_resolved_channel_intent(self):
        router = load_router()
        context = copy.deepcopy(load_yaml(ROOT / "projects/s30-mini/project-context.yaml"))
        context.pop("channel_contexts", None)
        edm = build_profile_for_context(router, context)["channel_assignments"]["edm"]
        self.assertIsNone(edm["recipe"]["recipe_id"])
        self.assertEqual(edm["recipe"]["selection_status"], "EDM_INTENT_NOT_RESOLVED")
        self.assertEqual(edm["routing_status"], "HUMAN_REVIEW_REQUIRED")
        self.assertIn("EDM_INTENT_NOT_RESOLVED", edm["reason_codes"])

    def test_non_launch_edm_does_not_receive_launch_recipe(self):
        router = load_router()
        context = copy.deepcopy(load_yaml(ROOT / "projects/s30-mini/project-context.yaml"))
        context["channel_contexts"]["edm"].update(
            {
                "campaign_type": "lifecycle_reminder",
                "primary_objective": "existing_user_reengagement",
                "consumer_goals": ["return_to_product"],
                "status": "CANDIDATE_ROUTING_INPUT",
            }
        )
        edm = build_profile_for_context(router, context)["channel_assignments"]["edm"]
        self.assertIsNone(edm["recipe"]["recipe_id"])
        self.assertEqual(edm["recipe"]["selection_status"], "NO_COMPATIBLE_EDM_RECIPE")
        self.assertEqual(edm["routing_status"], "HUMAN_REVIEW_REQUIRED")

    def test_s30_product_launch_intent_selects_launch_recipe(self):
        router = load_router()
        edm = router.build_profile(ROOT / "projects/s30-mini")["channel_assignments"]["edm"]
        self.assertEqual(edm["channel_intent"]["campaign_type"], "product_launch")
        self.assertEqual(edm["channel_intent"]["primary_objective"], "new_product_value_understanding")
        self.assertEqual(edm["recipe"]["recipe_id"], "RECIPE-EDM-PRODUCT-LAUNCH-PROOF")
        self.assertEqual(edm["recipe"]["selection_status"], "ROUTER_CANDIDATE_MATCH")

    def test_edm_recipe_maps_to_existing_skill_template(self):
        recipe_registry = load_yaml(SYSTEM / "registry/page-recipe-registry.yaml")
        self.assertEqual(len(recipe_registry["recipes"]), 1)
        recipe = load_yaml((SYSTEM / "registry" / recipe_registry["recipes"][0]["file"]).resolve())
        self.assertEqual(recipe["recipe_id"], "RECIPE-EDM-PRODUCT-LAUNCH-PROOF")
        self.assertEqual(recipe["lifecycle"]["status"], "CANDIDATE")
        self.assertEqual(recipe["template_compatibility"]["recommended_template"], "TPL-LAUNCH-A")
        templates = load_yaml(ROOT / "skills/edm-generator/design_system/templates_v1.0.yaml")
        self.assertIn("TPL-LAUNCH-A", {item["template_id"] for item in templates["templates"]})
        mapping = (ROOT / "skills/switchbot-japan-edm/references/visual-pattern-integration.md").read_text()
        self.assertIn("RECIPE-EDM-PRODUCT-LAUNCH-PROOF", mapping)
        self.assertIn("ESP Gate", mapping)
        adapter = load_yaml(SYSTEM / "routing/channel-adapters.yaml")["adapters"]["edm"]
        self.assertTrue(
            {
                "Product Truth",
                "Claim Gate",
                "Product Layer",
                "Asset Gate",
                "Human Review",
                "Hardening",
                "Mobile QA",
                "ESP Gate",
            }.issubset(adapter["required_gates"])
        )

    def test_recipe_required_roles_resolve_to_registered_modules(self):
        router = load_router()
        recipe = router.load_page_recipes()["RECIPE-EDM-PRODUCT-LAUNCH-PROOF"]
        compatibility = router.recipe_template_compatibility(recipe)
        self.assertTrue(compatibility["recommended_template_registered"])
        self.assertTrue(compatibility["required_roles_resolved"])
        self.assertTrue(compatibility["required_modules_satisfied"])
        self.assertEqual(compatibility["missing_registered_modules"], [])

    def test_recipe_does_not_override_stable_template_selector(self):
        router = load_router()
        recipe = router.load_page_recipes()["RECIPE-EDM-PRODUCT-LAUNCH-PROOF"]
        adapter = load_yaml(SYSTEM / "routing/channel-adapters.yaml")["adapters"]["edm"]
        compatibility = router.recipe_template_compatibility(recipe)
        self.assertFalse(recipe["template_compatibility"]["stable_selector_override_allowed"])
        self.assertFalse(compatibility["stable_selector_override_allowed"])
        self.assertEqual(adapter["existing_template"]["selection_mode"], "STABLE_TEMPLATE_SELECTOR")
        self.assertFalse(adapter["existing_template"]["override_allowed"])

    def test_tpl_launch_a_mapping_is_conditional_not_verified(self):
        router = load_router()
        edm = router.build_profile(ROOT / "projects/s30-mini")["channel_assignments"]["edm"]
        compatibility = edm["recipe"]["template_compatibility"]
        self.assertEqual(compatibility["recommended_template"], "TPL-LAUNCH-A")
        self.assertEqual(compatibility["mapping_status"], "CANDIDATE_CONDITIONAL_MATCH")
        self.assertNotEqual(compatibility["mapping_status"], "VERIFIED")

    def test_optional_problem_and_app_modules_do_not_block_base_launch_recipe(self):
        router = load_router()
        recipe = router.load_page_recipes()["RECIPE-EDM-PRODUCT-LAUNCH-PROOF"]
        request = recipe["template_selection_request"]
        required = {role["role_id"] for role in request["required_roles"]}
        optional = {role["role_id"]: role["requirement"] for role in request["optional_roles"]}
        compatibility = router.recipe_template_compatibility(recipe)
        self.assertNotIn("consumer_problem", required)
        self.assertNotIn("app_or_automation", required)
        self.assertEqual(optional["consumer_problem"], "CONDITIONAL")
        self.assertEqual(optional["app_or_automation"], "CONDITIONAL")
        self.assertTrue(compatibility["additional_modules_are_optional_or_conditional"])

    def test_visual_review_exposes_amendment_decisions_without_edm_freeze_blocker(self):
        html = (ROOT / "projects/s30-mini/visual-review.html").read_text(encoding="utf-8")
        for phrase in (
            "Freeze Applicability",
            "Channel Intent",
            "Channel Information Density",
            "Template Compatibility Status",
            "Required / Optional Section",
            "Architecture Approval ≠ Pattern Approval",
            "NOT_APPLICABLE_TO_CHANNEL",
        ):
            self.assertIn(phrase, html)
        blockers = html.split("<h3>EDM 正式生产 Blocker</h3>", 1)[1].split("</article>", 1)[0]
        self.assertNotIn("Candidate Freeze is not an active APPROVED Freeze", blockers)

    def test_available_claim_is_not_treated_as_approved(self):
        router = load_router()
        self.assertLess(router.governance_score("AVAILABLE", router.CLAIM_GATE_SCORES), 100)

    def test_available_asset_is_not_channel_approved(self):
        router = load_router()
        context = {"visual_inputs": {"assets": {"official_product": {"status": "AVAILABLE"}}}}
        top = {"asset_requirements": {"required": ["official_product"]}}
        score, gaps = router.asset_readiness_evaluation(context, top)
        self.assertLess(score, 100)
        self.assertEqual(gaps[0]["status"], "AVAILABLE")

    def test_only_approved_governance_can_reach_ready_for_production(self):
        router = load_router()
        base_context = {
            "governance": {
                "product_truth_status": "APPROVED",
                "claim_status": "APPROVED",
                "human_review_status": "APPROVED",
            },
            "visual_inputs": {"assets": {"official_product": {"status": "APPROVED"}}},
        }
        top = {"lifecycle": "VALIDATED", "asset_requirements": {"required": ["official_product"]}}
        ready, _, _ = router.execution_readiness(base_context, top, None, None, freeze_applicable=False)
        self.assertEqual(ready["status"], "READY_FOR_PRODUCTION")
        for gate, value in (
            ("product_truth_status", "AVAILABLE"),
            ("claim_status", "AVAILABLE"),
        ):
            context = copy.deepcopy(base_context)
            context["governance"][gate] = value
            metric, _, _ = router.execution_readiness(context, top, None, None, freeze_applicable=False)
            self.assertNotEqual(metric["status"], "READY_FOR_PRODUCTION")
        context = copy.deepcopy(base_context)
        context["visual_inputs"]["assets"]["official_product"]["status"] = "AVAILABLE"
        metric, _, _ = router.execution_readiness(context, top, None, None, freeze_applicable=False)
        self.assertNotEqual(metric["status"], "READY_FOR_PRODUCTION")

    def test_new_patterns_remain_candidate(self):
        registry = load_yaml(SYSTEM / "registry/section-pattern-registry.yaml")
        self.assertEqual(len(registry["patterns"]), 6)
        required_files = {
            "pattern.yaml",
            "anatomy.zh-CN.md",
            "slots.yaml",
            "channel-map.yaml",
            "anti-patterns.md",
            "validation.yaml",
        }
        for entry in registry["patterns"]:
            package = (SYSTEM / "registry" / entry["file"]).resolve().parent
            pattern = load_yaml(package / "pattern.yaml")
            validation = load_yaml(package / "validation.yaml")
            self.assertTrue(required_files.issubset({path.name for path in package.iterdir()}))
            self.assertEqual(entry["status"], "CANDIDATE")
            self.assertEqual(pattern["lifecycle"]["status"], "CANDIDATE")
            self.assertEqual(validation["status"], "CANDIDATE")

    def test_lock_ultra_max_asset_block_preserved(self):
        router = load_router()
        profile = router.build_profile(ROOT / "projects/lock-ultra-max")
        self.assertEqual(profile["pattern_match"]["status"], "HIGH")
        self.assertEqual(profile["execution_readiness"]["status"], "BLOCKED_BY_ASSET")
        self.assertFalse(profile["auto_apply"]["eligible"])
        self.assertFalse((ROOT / "projects/lock-ultra-max/visual-freeze.yaml").exists())
        self.assertEqual(profile["decision"]["mode"], "HUMAN_REVIEW_REQUIRED")

    def test_product_truth_hash_unchanged(self):
        baseline = load_yaml(SYSTEM / "tests/phase2a-protected-hashes.yaml")
        for relative, expected in baseline["product_truth"].items():
            self.assertEqual(sha256(ROOT / relative), expected, relative)

    def test_claim_hash_unchanged(self):
        baseline = load_yaml(SYSTEM / "tests/phase2a-protected-hashes.yaml")
        for relative, expected in baseline["claim"].items():
            self.assertEqual(sha256(ROOT / relative), expected, relative)

    def test_no_new_local_absolute_paths(self):
        baseline = load_yaml(SYSTEM / "tests/local-absolute-path-baseline.yaml")
        current = local_absolute_path_counts()
        allowed = baseline["allowlist"]
        self.assertFalse(set(current) - set(allowed), f"new files with local absolute paths: {set(current) - set(allowed)}")
        for relative, count in current.items():
            self.assertLessEqual(count, allowed[relative], f"local absolute path count increased: {relative}")
        self.assertLessEqual(len(current), baseline["baseline_file_count"])
        self.assertLessEqual(sum(current.values()), baseline["baseline_occurrence_count"])

    def test_existing_amazon_ranking_preserved(self):
        router = load_router()
        s30 = router.build_profile(ROOT / "projects/s30-mini")
        lock = router.build_profile(ROOT / "projects/lock-ultra-max")
        self.assertEqual((s30["ranking"][0]["pattern_id"], s30["ranking"][0]["score"]), ("VP-AMZ-MECHANISM-PROOF", 89.7))
        self.assertEqual((lock["ranking"][0]["pattern_id"], lock["ranking"][0]["score"]), ("VP-AMZ-JAPAN-FIT-TRUST", 81.1))


if __name__ == "__main__":
    unittest.main()
