import importlib.util
import unittest
from pathlib import Path

spec = importlib.util.spec_from_file_location(
    "creative_brief", Path(__file__).resolve().parents[1] / "scripts/prepare_creative_brief.py")
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def fixture():
    # Synthetic pointers and copy, never product facts or approval records.
    return {
        "asset_id": "SYNTHETIC-01", "placement": "gallery",
        "shopper_task": "Recognize the object", "primary_message": "One object",
        "desired_takeaway": "Recognize its silhouette", "proof_object": "Source silhouette",
        "production_mode": "GENERATIVE_SCENE", "evidence_mode": "CREATIVE_MOCK",
        "canvas": {"width": 2000, "height": 2000, "mobile_width": 390},
        "composition": {"scene": "An empty entryway with a plain wall", "camera": "Front view",
                        "light": "Soft window light from left", "product_placement": "Right",
                        "negative_space": "Empty right insertion area, empty upper left copy area"},
        "sources": {"product": ["synthetic/product.png"], "scene": ["synthetic/scene.png"]},
        "must_show": ["Clear silhouette"], "must_not_show": ["Invented functionality"],
        "locks": ["Current source silhouette"], "copy_layer": ["サンプル"],
    }


class CreativeBriefTests(unittest.TestCase):
    def test_scene_request_excludes_product_copy_research_and_gates(self):
        brief = fixture()
        brief.update({"research": "PRIVATE_RESEARCH", "gate": "PRIVATE_GATE", "other_candidates": ["OTHER_CANDIDATE"]})
        result = module.compile_brief(brief)
        scene = result["scene_request"]
        for value in ("PRIVATE_RESEARCH", "PRIVATE_GATE", "OTHER_CANDIDATE", "サンプル", "synthetic/product.png"):
            self.assertNotIn(value, str(scene))
        self.assertEqual(scene["reference_sources"], ["synthetic/scene.png"])
        self.assertIn("Invented functionality", scene["prompt"])
        self.assertEqual(result["copy_layer"], brief["copy_layer"])
        self.assertEqual(result["locks"], brief["locks"])
        self.assertEqual(result["status"], "BRIEF_PREPARED_NOT_RENDERED")

    def test_non_generative_modes_do_not_emit_scene_requests(self):
        for mode in module.MODES - {"GENERATIVE_SCENE"}:
            with self.subTest(mode=mode):
                brief = fixture()
                brief["production_mode"] = mode
                brief["sources"].update({"proof": ["synthetic/proof.json"], "ui": ["synthetic/ui.png"]})
                self.assertIsNone(module.compile_brief(brief)["scene_request"])

    def test_required_identity_proof_and_ui_sources(self):
        for changes, source in [({}, "product"), ({"production_mode": "PROOF_COMPOSITE"}, "proof"),
                                ({"evidence_mode": "PROOF_VISUAL"}, "proof"),
                                ({"production_mode": "UI_COMPOSITE"}, "ui")]:
            with self.subTest(changes=changes, source=source):
                brief = fixture()
                brief.update(changes)
                brief["sources"][source] = []
                with self.assertRaises(ValueError):
                    module.compile_brief(brief)

    def test_incomplete_composition_and_invalid_types_fail(self):
        for key, value in [("canvas", []), ("composition", {"scene": "Only adjectives"}),
                           ("sources", None), ("locks", "Everything"),
                           ("production_mode", "DRAW_PRODUCT"), ("asset_id", " "),
                           ("must_show", [])]:
            with self.subTest(key=key):
                brief = fixture()
                brief[key] = value
                with self.assertRaises(ValueError):
                    module.compile_brief(brief)
        brief = fixture()
        brief["canvas"]["width"] = True
        with self.assertRaises(ValueError):
            module.compile_brief(brief)


if __name__ == "__main__":
    unittest.main()
