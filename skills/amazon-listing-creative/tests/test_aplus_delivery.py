"""Synthetic, local-only regression tests. No product facts or external approvals."""
import copy
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "aplus_delivery.py"
loader = importlib.util.spec_from_file_location("aplus_delivery", SCRIPT)
delivery = importlib.util.module_from_spec(loader)
loader.loader.exec_module(delivery)


class RoutingTests(unittest.TestCase):
    def test_full_request_is_not_concept(self):
        r = delivery.route("full", "create")
        self.assertEqual(r["mode"], "FULL_FLOW")
        self.assertEqual(r["required_outputs"], ["gallery", "aplus"])
        self.assertFalse(r["execute"])

    def test_aplus_resume_preserves_gallery(self):
        r = delivery.route("aplus", "resume")
        self.assertEqual(r["entry"], "jp-commerce-content-flow")
        self.assertEqual(r["mode"], "RESUME")
        self.assertTrue(r["preserve_existing_gallery"])

    def test_gallery_scope_is_not_expanded(self):
        self.assertEqual(delivery.route("gallery", "create")["required_outputs"], ["gallery"])

    def test_plan_only_stays_plan_only(self):
        self.assertEqual(delivery.route("full", "plan")["mode"], "PLAN_ONLY")

    def test_explicit_concept_stays_local(self):
        self.assertEqual(delivery.route("concept", "explore")["entry"], "amazon-listing-creative")

    def test_full_scope_cannot_be_nine_grid(self):
        with self.assertRaises(ValueError):
            delivery.route("full", "explore")

    def test_cli_invalid_scope_intent_fails(self):
        result = subprocess.run([sys.executable, str(SCRIPT), "route", "--scope", "concept", "--intent", "create"], capture_output=True, text=True)
        self.assertEqual(result.returncode, 2)


@unittest.skipIf(delivery.Image is None, "Pillow missing; image regression has NOT run")
class ArtifactTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.spec = {
            "publish_gate": {"status": "BLOCKED"},
            "product_images": [{"id": "G01", "outputs": {"jpeg": "gallery/g01.jpg"}}],
            "aplus_modules": [{"id": "A01", "sequence": 1, "units": [{"id": "U01"}], "outputs": {"jpeg": "aplus/a01.jpg"}}],
        }
        for rel in ["gallery/g01.jpg", "aplus/a01.jpg", "design/aplus/mobile/aplus_01.jpg"]:
            self.image(rel)

    def tearDown(self):
        self.tmp.cleanup()

    def image(self, rel):
        f = self.root / rel
        f.parent.mkdir(parents=True, exist_ok=True)
        delivery.Image.new("RGB", (32, 16)).save(f)

    def result(self, scope="full"):
        return delivery.audit(self.spec, self.root, scope)

    def codes(self):
        return {i["code"] for i in self.result()["issues"]}

    def test_complete_legacy_files_do_not_approve_publication(self):
        r = self.result()
        self.assertEqual(r["status"], "ARTIFACTS_PRESENT")
        self.assertEqual(r["raster_files_decoded"], 3)
        self.assertEqual(r["publish_gate_in_spec"], "BLOCKED")
        self.assertIn("desktop/mobile browser QA", r["not_verified"])

    def test_gallery_only_cannot_satisfy_full_scope(self):
        self.spec["aplus_modules"] = []
        self.assertIn("REQUIRED_SCOPE_EMPTY", self.codes())
        self.assertEqual(self.result()["resume_queue"], ["aplus"])

    def test_gallery_only_request_does_not_require_aplus(self):
        self.spec["aplus_modules"] = []
        self.assertEqual(self.result("gallery")["status"], "ARTIFACTS_PRESENT")

    def test_missing_desktop_identifies_aplus_not_gallery(self):
        (self.root / "aplus/a01.jpg").unlink()
        self.assertEqual(self.result()["resume_queue"], ["A01"])

    def test_missing_mobile_cannot_be_covered_by_desktop(self):
        (self.root / "design/aplus/mobile/aplus_01.jpg").unlink()
        self.assertEqual(self.result()["raster_files_decoded"], 2)
        self.assertIn("MISSING_IMAGE", self.codes())

    def test_prompt_renamed_jpg_fails(self):
        (self.root / "aplus/a01.jpg").write_text("Create a beautiful A+ banner")
        self.assertIn("INVALID_IMAGE", self.codes())

    def test_truncated_image_fails(self):
        file = self.root / "aplus/a01.jpg"
        file.write_bytes(file.read_bytes()[:40])
        self.assertIn("INVALID_IMAGE", self.codes())

    def test_cross_root_path_is_blocked(self):
        self.spec["aplus_modules"][0]["outputs"]["jpeg"] = "../secret.jpg"
        self.assertIn("UNSAFE_OUTPUT_PATH", self.codes())

    def test_remote_image_is_not_local_delivery(self):
        self.spec["aplus_modules"][0]["outputs"]["jpeg"] = "https://example.invalid/image.jpg"
        self.assertIn("UNSAFE_OUTPUT_PATH", self.codes())

    def test_symlink_escape_is_blocked(self):
        with tempfile.TemporaryDirectory() as other:
            file = Path(other) / "outside.jpg"
            delivery.Image.new("RGB", (16, 16)).save(file)
            (self.root / "linked.jpg").symlink_to(file)
            self.spec["aplus_modules"][0]["outputs"]["jpeg"] = "linked.jpg"
            self.assertIn("UNSAFE_OUTPUT_PATH", self.codes())

    def test_duplicate_ids_fail(self):
        self.spec["aplus_modules"][0]["id"] = "G01"
        self.assertIn("DUPLICATE_ID", self.codes())

    def test_no_content_units_fails(self):
        self.spec["aplus_modules"][0]["units"] = []
        self.assertIn("APLUS_UNITS_EMPTY", self.codes())

    def test_carousel_cannot_be_one_composite(self):
        self.spec["aplus_modules"][0]["interaction"] = "carousel"
        self.assertIn("CAROUSEL_SLIDES_UNMAPPED", self.codes())

    def test_carousel_every_slide_and_mobile_required(self):
        module = self.spec["aplus_modules"][0]
        module["interaction"] = "carousel"
        module["slides"] = [
            {"id": "A01-S1", "outputs": {"jpeg": "aplus/a01.jpg", "mobile_jpeg": "design/aplus/mobile/aplus_01.jpg"}},
            {"id": "A01-S2", "outputs": {"jpeg": "aplus/a02.jpg", "mobile_jpeg": "aplus/a02-mobile.jpg"}},
        ]
        self.image("aplus/a02.jpg")
        self.assertEqual(self.result()["resume_queue"], ["A01-S2"])
        self.image("aplus/a02-mobile.jpg")
        self.assertEqual(self.result()["raster_files_expected"], 5)
        self.assertEqual(self.result()["status"], "ARTIFACTS_PRESENT")

    def test_native_text_not_forced_into_raster(self):
        module = self.spec["aplus_modules"][0]
        module.update(delivery_kind="native", native_content={"headline": "SYNTHETIC TEST", "body": "TEST ONLY"}, preview_binding="fixture-native-A01")
        module.pop("outputs")
        r = self.result()
        self.assertEqual(r["status"], "ARTIFACTS_PRESENT")
        self.assertEqual(r["raster_files_expected"], 1)
        self.assertIn("native text mounting", r["not_verified"])

    def test_native_without_binding_fails(self):
        self.spec["aplus_modules"][0].update(delivery_kind="native", native_content={"body": "TEST"})
        self.assertIn("NATIVE_BINDING_MISSING", self.codes())

    def test_missing_decoder_is_not_pass(self):
        with patch.object(delivery, "Image", None):
            self.assertIn("DECODER_UNAVAILABLE", self.codes())

    def test_spec_and_existing_files_are_unchanged(self):
        before_spec = copy.deepcopy(self.spec)
        before_files = {str(p.relative_to(self.root)): p.read_bytes() for p in self.root.rglob("*") if p.is_file()}
        self.result("aplus")
        self.assertEqual(self.spec, before_spec)
        self.assertEqual(before_files, {str(p.relative_to(self.root)): p.read_bytes() for p in self.root.rglob("*") if p.is_file()})

    def test_cli_has_nonzero_exit_for_missing_aplus(self):
        self.spec["aplus_modules"] = []
        file = self.root / "spec.json"
        file.write_text(json.dumps(self.spec))
        result = subprocess.run([sys.executable, str(SCRIPT), "audit", "--scope", "full", "--spec", str(file), "--output-dir", str(self.root)], capture_output=True, text=True)
        self.assertEqual(result.returncode, 1)
        self.assertEqual(json.loads(result.stdout)["resume_queue"], ["aplus"])

    def test_counts_follow_spec_not_seven_or_sixteen(self):
        self.spec["aplus_modules"].append({"id": "A02", "sequence": 2, "units": [{"id": "U02"}, {"id": "U03"}], "outputs": {"jpeg": "aplus/a02.jpg"}})
        self.image("aplus/a02.jpg")
        self.image("design/aplus/mobile/aplus_02.jpg")
        self.assertEqual(self.result()["summary"]["aplus"]["expected"], 2)
        self.assertEqual(self.result()["status"], "ARTIFACTS_PRESENT")


if __name__ == "__main__":
    unittest.main()
