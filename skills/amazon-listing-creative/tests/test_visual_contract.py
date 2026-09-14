"""Generic synthetic fixtures only; no private images, product facts or approvals."""
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import struct
import subprocess
import sys
import tempfile
import unittest
import zlib

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "visual_contract.py"
DELIVERY = SCRIPT.with_name("aplus_delivery.py")
loader = importlib.util.spec_from_file_location("visual_contract", SCRIPT)
visual = importlib.util.module_from_spec(loader)
loader.loader.exec_module(visual)


def png_bytes():
    """A reproducible 1x1 synthetic PNG, not a real reviewed scene."""
    def chunk(kind, payload):
        return struct.pack(">I", len(payload)) + kind + payload + struct.pack(">I", zlib.crc32(kind + payload))
    return (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", 1, 1, 8, 2, 0, 0, 0)) +
            chunk(b"IDAT", zlib.compress(b"\x00\x80\x80\x80")) + chunk(b"IEND", b""))


class VisualContractTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.file = self.root / "anchor.png"
        self.file.write_bytes(png_bytes())
        self.contract = {
            "schema_version": "1.0",
            "references": [{"id": "R1", "url": "https://example.invalid/generic-reference",
                            "evidence_level": "PIXELS_VIEWED", "observations": "Synthetic observation fixture: plain tabletop and side lighting."}],
            "assets": [{"id": "A1", "visual_type": "commercial_scene", "reference_ids": ["R1"],
                        "visual_proof": {"object": "Generic object", "action": "Hand places object on a table", "visible_result": "Object contacts table"},
                        "production_method": "official_composite", "product_body_source": "official_asset", "geometry_view": "exterior"}],
            "anchor_asset_ids": ["A1"],
            "anchor_reviews": [{"asset_id": "A1", "file": "anchor.png", "sha256": self.digest(),
                                "observed_visual_type": "commercial_scene", "reviewer_type": "model",
                                "checks": {name: {"status": "PASS", "observation": observation} for name, observation in {
                                    "integration": "Synthetic record: table contact and shadow are coherent.",
                                    "visual_proof": "Synthetic record: hand, object and contact are visible.",
                                    "reference_match": "Synthetic record: side lighting matches the declared reference.",
                                }.items()}}],
        }

    def tearDown(self):
        self.tmp.cleanup()

    def digest(self):
        return hashlib.sha256(self.file.read_bytes()).hexdigest()

    @property
    def asset(self):
        return self.contract["assets"][0]

    @property
    def review(self):
        return self.contract["anchor_reviews"][0]

    def result(self):
        return visual.check(self.contract, self.root)

    def codes(self):
        return {issue["code"] for issue in self.result()["issues"]}

    def target(self, kind, method="official_composite"):
        self.asset.update(visual_type=kind, production_method=method)
        self.review["observed_visual_type"] = kind

    def geometry(self):
        file = self.root / "generic-geometry.step"
        file.write_text("SYNTHETIC GEOMETRY RECORD, NOT PRODUCT DATA")
        self.asset["geometry_evidence"] = {"source_type": "approved_cad", "file": file.name,
                                            "sha256": hashlib.sha256(file.read_bytes()).hexdigest()}

    def test_consistent_records_do_not_verify_visual_quality_or_approval(self):
        result = self.result()
        self.assertEqual(result["status"], "EVIDENCE_RECORDED")
        self.assertEqual(result["anchor_evidence"]["recorded"], ["A1"])
        for item in ("aesthetic quality", "claim approval", "human approval", "browser QA", "Seller Central rendering"):
            self.assertIn(item, result["not_verified"])
        self.assertIn("not a visual-quality verdict", result["meaning"])

    def test_commercial_goal_cannot_use_information_graphic_production(self):
        self.asset["production_method"] = "information_graphic"
        self.assertIn("PRODUCTION_TYPE_MISMATCH", self.codes())

    def test_mechanism_goal_cannot_use_information_graphic_production(self):
        self.target("mechanism_visual", "information_graphic")
        self.assertIn("PRODUCTION_TYPE_MISMATCH", self.codes())

    def test_observed_information_graphic_does_not_satisfy_scene(self):
        self.review["observed_visual_type"] = "information_graphic"
        self.assertIn("OBSERVED_TYPE_MISMATCH", self.codes())

    def test_observed_scene_does_not_satisfy_mechanism(self):
        self.asset["visual_type"] = "mechanism_visual"
        self.assertIn("OBSERVED_TYPE_MISMATCH", self.codes())

    def test_dom_or_unavailable_reference_cannot_be_styling_evidence(self):
        for level in ("DOM_ONLY", "UNAVAILABLE"):
            with self.subTest(level=level):
                self.contract["references"][0]["evidence_level"] = level
                self.assertIn("STYLING_REFERENCE_NOT_VIEWED", self.codes())

    def test_unused_dom_metadata_is_allowed(self):
        self.contract["references"].append({"id": "R2", "url": "https://example.invalid/metadata", "evidence_level": "DOM_ONLY", "observations": ""})
        self.assertEqual(self.result()["status"], "EVIDENCE_RECORDED")

    def test_pixels_viewed_requires_observations(self):
        self.contract["references"][0]["observations"] = "  "
        self.assertIn("REFERENCE_OBSERVATION_MISSING", self.codes())

    def test_geometry_evidence_required_for_cutaway_transparent_exploded(self):
        self.target("mechanism_visual", "approved_cg")
        for view in ("cutaway", "transparent", "exploded"):
            with self.subTest(view=view):
                self.asset["geometry_view"] = view
                self.assertIn("GEOMETRY_EVIDENCE_MISSING", self.codes())

    def test_information_graphic_does_not_waive_geometry_evidence(self):
        self.target("information_graphic", "information_graphic")
        self.asset["geometry_view"] = "cutaway"
        self.assertIn("GEOMETRY_EVIDENCE_MISSING", self.codes())

    def test_bound_geometry_record_is_accepted_without_proving_its_authority(self):
        self.target("mechanism_visual", "approved_cg")
        self.asset.update(geometry_view="cutaway", product_body_source="approved_cad")
        self.geometry()
        self.assertEqual(self.result()["status"], "EVIDENCE_RECORDED")
        self.assertIn("product accuracy or geometry authority", self.result()["not_verified"])
        (self.root / "generic-geometry.step").write_text("CHANGED")
        self.assertIn("HASH_MISMATCH", self.codes())

    def test_cad_product_body_requires_geometry_even_for_exterior(self):
        self.asset["product_body_source"] = "approved_cad"
        self.assertIn("GEOMETRY_EVIDENCE_MISSING", self.codes())

    def test_ai_generated_product_body_is_invalid(self):
        self.asset["product_body_source"] = "ai_generated"
        self.assertEqual(self.result()["status"], "INVALID_INPUT")

    def test_scene_requires_declared_product_body(self):
        self.asset["product_body_source"] = "none"
        self.assertIn("PRODUCT_BODY_SOURCE_MISSING", self.codes())

    def test_actual_file_hash_is_checked(self):
        self.file.write_bytes(self.file.read_bytes() + b"changed")
        self.assertIn("HASH_MISMATCH", self.codes())
        self.assertEqual(self.result()["anchor_evidence"]["recorded"], [])

    def test_uppercase_hash_is_accepted(self):
        self.review["sha256"] = self.digest().upper()
        self.assertEqual(self.result()["status"], "EVIDENCE_RECORDED")

    def test_missing_and_malformed_hashes_fail(self):
        self.review.pop("sha256")
        self.assertIn("MISSING_SHA256", self.codes())
        self.review["sha256"] = "not-a-digest"
        self.assertEqual(self.result()["status"], "INVALID_INPUT")

    def test_missing_actual_file_fails(self):
        self.file.unlink()
        self.assertIn("MISSING_FILE", self.codes())

    def test_revise_or_not_checked_cannot_count_as_complete_review(self):
        for status in ("REVISE", "NOT_CHECKED"):
            with self.subTest(status=status):
                self.review["checks"]["integration"]["status"] = status
                self.assertIn("REVIEW_NEEDS_REVISION", self.codes())
                self.assertEqual(self.result()["anchor_evidence"]["recorded"], [])

    def test_empty_observation_and_missing_check_fail(self):
        self.review["checks"]["visual_proof"]["observation"] = " "
        self.assertIn("REVIEW_OBSERVATION_MISSING", self.codes())
        self.review["checks"].pop("reference_match")
        self.assertIn("CHECK_NOT_RECORDED", self.codes())

    def test_legitimate_information_graphic_accepts_svg_without_rendering_it(self):
        self.target("information_graphic", "information_graphic")
        self.asset["product_body_source"] = "none"
        file = self.root / "diagram.svg"
        file.write_text('<svg xmlns="http://www.w3.org/2000/svg"><rect width="1" height="1"/></svg>')
        self.review.update(file=file.name, sha256=hashlib.sha256(file.read_bytes()).hexdigest())
        self.assertEqual(self.result()["status"], "EVIDENCE_RECORDED")

    def test_white_background_official_packshot_is_legitimate(self):
        self.target("official_packshot")
        self.asset["visual_proof"] = {"object": "Generic official product image", "action": "Static presentation", "visible_result": "Product silhouette on white background"}
        self.assertEqual(self.result()["status"], "EVIDENCE_RECORDED")

    def test_no_anchors_or_missing_review_cannot_be_complete(self):
        self.contract["anchor_reviews"] = []
        self.assertIn("ANCHOR_REVIEW_MISSING", self.codes())
        self.contract["anchor_asset_ids"] = []
        self.assertIn("ANCHORS_MISSING", self.codes())

    def test_each_target_visual_type_needs_a_representative(self):
        other = copy.deepcopy(self.asset)
        other.update(id="A2", visual_type="mechanism_visual")
        self.contract["assets"].append(other)
        self.assertIn("VISUAL_TYPE_UNREPRESENTED", self.codes())

    def test_few_anchors_can_cover_larger_set_of_same_type(self):
        other = copy.deepcopy(self.asset)
        other["id"] = "A2"
        self.contract["assets"].append(other)
        self.assertEqual(self.result()["status"], "EVIDENCE_RECORDED")

    def test_extra_review_with_revise_still_fails(self):
        other = copy.deepcopy(self.asset)
        other["id"] = "A2"
        self.contract["assets"].append(other)
        review = copy.deepcopy(self.review)
        review["asset_id"] = "A2"
        review["checks"]["integration"]["status"] = "REVISE"
        self.contract["anchor_reviews"].append(review)
        self.assertIn("REVIEW_NEEDS_REVISION", self.codes())

    def test_unknown_and_duplicate_ids_are_invalid(self):
        for field, value in (("anchor_asset_ids", ["A1", "A1"]), ("anchor_asset_ids", ["unknown"])):
            with self.subTest(value=value):
                contract = copy.deepcopy(self.contract)
                contract[field] = value
                self.assertEqual(visual.check(contract, self.root)["status"], "INVALID_INPUT")
        self.asset["reference_ids"] = ["unknown"]
        self.assertEqual(self.result()["status"], "INVALID_INPUT")

    def test_duplicate_review_is_invalid(self):
        self.contract["anchor_reviews"].append(copy.deepcopy(self.review))
        self.assertEqual(self.result()["status"], "INVALID_INPUT")

    def test_unsafe_paths_are_invalid(self):
        for path in ("../outside.png", "/tmp/outside.png", "https://example.invalid/a.png", "C:\\outside.png", "nested/../../outside.png", "a\x00.png"):
            with self.subTest(path=path):
                self.review["file"] = path
                self.assertEqual(self.result()["status"], "INVALID_INPUT")

    def test_symlink_escape_is_invalid(self):
        with tempfile.TemporaryDirectory() as other:
            file = Path(other) / "outside.png"
            file.write_bytes(png_bytes())
            (self.root / "linked.png").symlink_to(file)
            self.review["file"] = "linked.png"
            self.assertEqual(self.result()["status"], "INVALID_INPUT")

    def test_geometry_path_uses_same_safety_rules(self):
        self.geometry()
        self.asset["geometry_evidence"]["file"] = "../geometry.step"
        self.assertEqual(self.result()["status"], "INVALID_INPUT")

    def test_malformed_roots_and_enum_types_are_invalid(self):
        for contract in (None, [], {}, {**self.contract, "references": {}}, {**self.contract, "schema_version": 1}):
            with self.subTest(contract=contract):
                self.assertEqual(visual.check(contract, self.root)["status"], "INVALID_INPUT")
        self.asset["visual_type"] = []
        self.assertEqual(self.result()["status"], "INVALID_INPUT")

    def test_files_and_contract_are_unchanged(self):
        before = copy.deepcopy(self.contract)
        data = {p.name: p.read_bytes() for p in self.root.iterdir()}
        self.result()
        self.assertEqual(self.contract, before)
        self.assertEqual({p.name: p.read_bytes() for p in self.root.iterdir()}, data)

    def test_cli_and_delivery_subcommand_have_same_contract(self):
        file = self.root / "contract.json"
        file.write_text(json.dumps(self.contract))
        for script, command in ((SCRIPT, "check"), (DELIVERY, "visual-check")):
            with self.subTest(script=script):
                result = subprocess.run([sys.executable, str(script), command, "--contract", str(file), "--output-dir", str(self.root)], capture_output=True, text=True)
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertEqual(json.loads(result.stdout)["status"], "EVIDENCE_RECORDED")

    def test_cli_invalid_and_incomplete_inputs_return_distinct_codes(self):
        file = self.root / "contract.json"
        for text, expected_code, expected_status in (("[]", 2, "INVALID_INPUT"), ("broken", 2, "INVALID_INPUT")):
            file.write_text(text)
            result = subprocess.run([sys.executable, str(SCRIPT), "check", "--contract", str(file), "--output-dir", str(self.root)], capture_output=True, text=True)
            self.assertEqual(result.returncode, expected_code)
            self.assertEqual(json.loads(result.stdout)["status"], expected_status)
        self.contract["anchor_reviews"] = []
        file.write_text(json.dumps(self.contract))
        result = subprocess.run([sys.executable, str(DELIVERY), "visual-check", "--contract", str(file), "--output-dir", str(self.root)], capture_output=True, text=True)
        self.assertEqual(result.returncode, 1)
        self.assertEqual(json.loads(result.stdout)["status"], "NEEDS_REVISION")

    def test_generic_example_does_not_pretend_to_have_viewed_pixels(self):
        file = SCRIPT.parents[1] / "references" / "visual-contract-example.json"
        result = visual.check_file(file, self.root)
        self.assertEqual(result["status"], "NEEDS_REVISION")
        self.assertEqual(result["anchor_evidence"]["recorded"], [])


if __name__ == "__main__":
    unittest.main()
