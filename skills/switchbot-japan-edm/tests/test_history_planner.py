"""Behavioral regression tests; all messages/assets are synthetic."""
import base64
import copy
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


SCRIPT = Path(__file__).resolve().parents[1] / "scripts/edm_history.py"
spec = importlib.util.spec_from_file_location("edm_history", SCRIPT)
history = importlib.util.module_from_spec(spec)
spec.loader.exec_module(history)
PNG = base64.b64decode("iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+jCZkAAAAASUVORK5CYII=")


def recipe(identifier="autumn", refs=None, **overrides):
    item = {"id": identifier, "campaign_types": ["sale_launch"], "stages": ["launch"],
            "channels": ["amazon"], "product_range": [4, 6], "source_refs": refs or ["SYNTHETIC-A"],
            "hero_style": "offer_hero", "card_layout": "two_columns", "modules": ["hero", "product_grid", "footer"],
            "tokens": {"canvas_width": 600, "accent": "#cc2222"}, "status": "OBSERVED_CANDIDATE"}
    item.update(overrides)
    return item


class HistoryPlannerTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.image = self.root / "reference.png"
        self.image.write_bytes(PNG)
        self.brief = {"campaign_type": "sale_launch", "stage": "launch", "channel": "amazon", "product_count": 4,
                      "explicit_new_design": False}
        self.sample = {"reference_id": "SYNTHETIC-A", "delivery_status": "marketing_received_copy", "html_read": True,
                       "visual_reviewed": True, "visual_files": [str(self.image)]}
        self.catalog = {"schema_version": "1.0", "recipes": [recipe()]}

    def tearDown(self):
        self.temp.cleanup()

    def plan(self, samples=None, brief=None, catalog=None):
        return history.make_plan(brief or self.brief, {"samples": samples if samples is not None else [self.sample]},
                                 catalog or self.catalog, evidence_base_dir=self.root)

    def test_no_history_never_claims_visual_inheritance(self):
        plan = self.plan(samples=[])
        self.assertEqual(plan["status"], "INTERNAL_DRAFT")
        self.assertEqual(plan["planning_status"], "BLOCKED_HISTORY_EVIDENCE")
        self.assertIsNone(plan["selected_recipe"])
        self.assertEqual(plan["visual_inheritance"], "NONE")
        self.assertTrue(plan["next_actions"])

    def test_metadata_only_test_and_duplicate_cannot_qualify(self):
        for patch in ({"html_read": False}, {"visual_reviewed": False}, {"visual_files": []},
                      {"delivery_status": "test"}, {"delivery_status": "duplicate"}, {"delivery_status": "communication"}):
            with self.subTest(patch=patch):
                sample = {**self.sample, **patch}
                self.assertEqual(self.plan(samples=[sample])["planning_status"], "BLOCKED_HISTORY_EVIDENCE")

    def test_compatible_candidate_beats_incompatible_candidate_with_evidence(self):
        catalog = {"schema_version": "1.0", "recipes": [recipe("wrong-channel", channels=["official"]), recipe("matching")]}
        plan = self.plan(catalog=catalog)
        self.assertEqual(plan["selected_recipe"]["id"], "matching")
        self.assertEqual(plan["visual_inheritance"], "EVIDENCE_BACKED_CANDIDATE")
        self.assertEqual(plan["approval"], "NOT_APPROVED")
        self.assertEqual(plan["campaign_context"], {key: self.brief[key] for key in
                                                   ("campaign_type", "stage", "channel", "product_count")})

    def test_product_count_requires_positive_integer(self):
        for value in (None, "4", 4.5, 0, -1, True):
            with self.subTest(value=value):
                plan = self.plan(brief={**self.brief, "product_count": value})
                self.assertEqual(plan["planning_status"], "INVALID_INPUT")

    def test_preferred_eligible_choice_is_respected(self):
        catalog = {"schema_version": "1.0", "recipes": [recipe("first"), recipe("requested")]}
        plan = self.plan(brief={**self.brief, "preferred_recipe": "requested"}, catalog=catalog)
        self.assertEqual(plan["selected_recipe"]["id"], "requested")

    def test_preferred_missing_evidence_does_not_silently_fallback(self):
        catalog = {"schema_version": "1.0", "recipes": [recipe("available"), recipe("requested", ["UNREAD"])]}
        plan = self.plan(brief={**self.brief, "preferred_recipe": "requested"}, catalog=catalog)
        self.assertEqual(plan["planning_status"], "BLOCKED_HISTORY_EVIDENCE")
        self.assertIsNone(plan["selected_recipe"])

    def test_missing_empty_or_non_image_file_blocks(self):
        empty = self.root / "empty.png"
        empty.touch()
        text = self.root / "fake.png"
        text.write_text("metadata-only")
        for path in (self.root / "missing.png", empty, text):
            with self.subTest(path=path.name):
                plan = self.plan(samples=[{**self.sample, "visual_files": [str(path)]}])
                self.assertEqual(plan["planning_status"], "BLOCKED_HISTORY_EVIDENCE")

    def test_relative_evidence_paths_resolve_against_evidence_directory(self):
        plan = self.plan(samples=[{**self.sample, "visual_files": ["reference.png"]}])
        self.assertEqual(plan["planning_status"], "READY_FOR_INTERNAL_RENDER")

    def test_primary_reference_is_required(self):
        catalog = {"schema_version": "1.0", "recipes": [recipe(refs=["UNREAD-AUTUMN", "SYNTHETIC-A"],
                                                              primary_source_ref="UNREAD-AUTUMN")]}
        plan = self.plan(catalog=catalog)
        self.assertEqual(plan["planning_status"], "BLOCKED_HISTORY_EVIDENCE")

    def test_optional_unread_reference_is_not_claimed_in_mapping(self):
        catalog = {"schema_version": "1.0", "recipes": [recipe(refs=["SYNTHETIC-A", "UNREAD"],
                                                              primary_source_ref="SYNTHETIC-A")]}
        plan = self.plan(catalog=catalog)
        self.assertEqual(plan["selected_reference_ids"], ["SYNTHETIC-A"])
        self.assertTrue(all(x["source_reference_ids"] == ["SYNTHETIC-A"] for x in plan["module_mapping"]
                            if x["module"] != "footer"))

    def test_module_provenance_does_not_invent_footer_or_missing_reference_inheritance(self):
        catalog = {"schema_version": "1.0", "recipes": [recipe(
            refs=["SYNTHETIC-A", "UNREAD"], primary_source_ref="SYNTHETIC-A",
            modules=["hero", "product_grid", "legal_footer"],
            module_treatments={
                "hero": {"treatment": "inherited", "source_refs": ["SYNTHETIC-A", "UNREAD"],
                         "reason": "Combine two campaign references", "raw_html": "PRIVATE-MODULE-PAYLOAD"},
                "product_grid": {"treatment": "inherited", "source_refs": ["UNREAD"], "reason": "Historical grid"},
            })]}
        plan = self.plan(catalog=catalog)
        modules = {entry["module"]: entry for entry in plan["module_mapping"]}
        self.assertEqual(modules["hero"]["inheritance"], "adapted_with_evidence_gap")
        self.assertEqual(modules["hero"]["source_reference_ids"], ["SYNTHETIC-A"])
        self.assertEqual(modules["hero"]["missing_reference_ids"], ["UNREAD"])
        self.assertEqual(modules["product_grid"]["inheritance"], "new")
        self.assertEqual(modules["product_grid"]["source_reference_ids"], [])
        self.assertEqual(modules["legal_footer"]["inheritance"], "new")
        self.assertEqual(modules["legal_footer"]["source_reference_ids"], [])
        self.assertNotIn("PRIVATE-MODULE-PAYLOAD", json.dumps(plan))
        self.assertNotIn("raw_html", json.dumps(plan))

    def test_unknown_campaign_recipe_or_tied_match_requires_review(self):
        cases = [({**self.brief, "campaign_type": "unsupported"}, self.catalog),
                 ({**self.brief, "preferred_recipe": "does-not-exist"}, self.catalog),
                 (self.brief, {"schema_version": "1.0", "recipes": [recipe("a"), recipe("b")]}),
                 ({**self.brief, "explicit_new_design": True}, self.catalog)]
        for brief, catalog in cases:
            with self.subTest(brief=brief):
                self.assertEqual(self.plan(brief=brief, catalog=catalog)["planning_status"], "BLOCKED_RUNTIME_SCOPE")

    def test_raw_email_payload_and_paths_are_not_copied_to_plan(self):
        private = {**self.sample, "raw_html": "PRIVATE-BODY", "gmail_id": "PRIVATE-GMAIL-ID",
                   "gmail_url": "https://mail.google.com/mail/u/0/#PRIVATE", "recipient": "private@example.invalid"}
        catalog = copy.deepcopy(self.catalog)
        catalog["recipes"][0]["raw_email"] = "PRIVATE-CATALOG-PAYLOAD"
        plan = self.plan(samples=[private], catalog=catalog)
        serialized = json.dumps(plan)
        for forbidden in ("PRIVATE", "gmail_id", "gmail_url", "recipient", "raw_html", str(self.image)):
            self.assertNotIn(forbidden, serialized)
        self.assertEqual(len(plan["source_image_hashes"][0]["sha256"]), 64)

    def test_duplicate_ids_or_exact_visuals_do_not_create_extra_evidence(self):
        same_id = self.plan(samples=[self.sample, self.sample])
        self.assertEqual(same_id["planning_status"], "BLOCKED_HISTORY_EVIDENCE")
        different_id = {**self.sample, "reference_id": "SYNTHETIC-B"}
        result = self.plan(samples=[self.sample, different_id])
        self.assertEqual(result["selected_reference_ids"], ["SYNTHETIC-A"])
        self.assertIn("DUPLICATE_VISUAL_EVIDENCE", result["rejected_references"][0]["reasons"])

    def test_cli_clean_checkout_missing_private_evidence_writes_blocked_plan(self):
        brief = self.root / "brief.json"
        catalog = self.root / "catalog.json"
        brief.write_text(json.dumps(self.brief))
        catalog.write_text(json.dumps(self.catalog))
        out = self.root / "output"
        run = subprocess.run([sys.executable, str(SCRIPT), "plan", "--brief", str(brief), "--catalog", str(catalog),
                              "--evidence", str(self.root / "not-committed-private-evidence.json"), "--out", str(out)],
                             capture_output=True, text=True)
        self.assertEqual(run.returncode, 2, run.stderr)
        plan = json.loads((out / "plan.json").read_text())
        self.assertEqual(plan["planning_status"], "BLOCKED_HISTORY_EVIDENCE")
        self.assertIsNone(plan["selected_recipe"])


if __name__ == "__main__":
    unittest.main()
