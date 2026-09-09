"""Synthetic rendering behavior, separate from any real Gmail design validation."""
import copy
import hashlib
from html.parser import HTMLParser
import importlib.util
import json
from pathlib import Path
import re
import struct
import tempfile
import unittest
import zlib


SKILL = Path(__file__).resolve().parents[1]


def load_module(name, filename):
    spec = importlib.util.spec_from_file_location(name, SKILL / "scripts" / filename)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


history = load_module("history_for_renderer_tests", "edm_history.py")
renderer = load_module("renderer_under_test", "render_edm.py")


def synthetic_png(rgb):
    """Generate an actual 8x8 RGB PNG without requiring image dependencies."""
    def chunk(kind, data):
        return struct.pack(">I", len(data)) + kind + data + struct.pack(">I", zlib.crc32(kind + data) & 0xffffffff)
    scanlines = b"".join(b"\x00" + bytes(rgb) * 8 for _ in range(8))
    return (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", 8, 8, 8, 2, 0, 0, 0))
            + chunk(b"IDAT", zlib.compress(scanlines)) + chunk(b"IEND", b""))


class Structure(HTMLParser):
    def __init__(self, markup):
        super().__init__()
        self.stack = []
        self.cards = []
        self.modules = []
        self.images = []
        self.feed(markup)

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        node = {"tag": tag, "attrs": attrs, "parent": self.stack[-1] if self.stack else None}
        if "data-module" in attrs:
            self.modules.append(node)
        if "data-card-product" in attrs:
            self.cards.append(node)
        if tag == "img":
            self.images.append(node)
        if tag not in {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "param", "source", "track", "wbr"}:
            self.stack.append(node)

    def handle_endtag(self, tag):
        for index in range(len(self.stack) - 1, -1, -1):
            if self.stack[index]["tag"] == tag:
                self.stack = self.stack[:index]
                break

    @staticmethod
    def inside(node, ancestor):
        cursor = node.get("parent")
        while cursor is not None:
            if cursor is ancestor:
                return True
            cursor = cursor["parent"]
        return False

    def groups(self):
        return {module["attrs"]["data-module"]: [card["attrs"]["data-card-product"] for card in self.cards
                                               if self.inside(card, module)] for module in self.modules}


class HistoryRendererTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.catalog = json.loads((SKILL / "assets/history-recipes.json").read_text(encoding="utf-8"))
        self.samples = []
        refs = sorted({ref for recipe in self.catalog["recipes"] for ref in recipe["source_refs"]})
        for index, ref in enumerate(refs):
            image = self.root / f"synthetic-history-{index}.png"
            image.write_bytes(synthetic_png((index * 31, 44, 160)))
            self.samples.append({"reference_id": ref, "delivery_status": "marketing_received_copy", "html_read": True,
                                 "visual_reviewed": True, "visual_files": [str(image)],
                                 "raw_html": "PRIVATE-HISTORICAL-COPY OLD99OFF OLDPRICE123456",
                                 "historic_offer": {"sale_price_jpy": 123456, "coupon": "OLD99OFF"}})
        logo = self.root / "synthetic-logo.png"
        logo.write_bytes(synthetic_png((220, 30, 30)))
        products = []
        for index, product_id in enumerate(("lock", "hub", "robot", "curtain")):
            image = self.root / f"synthetic-{product_id}.png"
            image.write_bytes(synthetic_png((50, 50 + index * 40, 190)))
            products.append({"id": product_id, "asset_product_id": product_id,
                             "name": f"SwitchBot Test {product_id}", "benefit": f"Current benefit {index + 1}",
                             "image": str(image), "image_url": f"https://assets.example.invalid/{product_id}.png",
                             "image_source": f"https://official.example.invalid/assets/{product_id}",
                             "product_source": f"https://official.example.invalid/products/{product_id}",
                             "url": f"https://www.amazon.co.jp/dp/SYNTHETIC{index}",
                             "offer": {"status": "UNCONFIRMED", "sale_price_jpy": 234567,
                                       "source": "https://official.example.invalid/draft-offers"}})
        self.data = {"subject": "秋のテスト Sale", "preheader": "Current preview 测试", "hero_title": "この秋の Test",
                     "channel": "amazon",
                     "campaign_name": "Autumn Test", "main_cta": "Amazonで見る", "logo": str(logo),
                     "logo_url": "https://assets.example.invalid/logo.png", "main_url": "https://www.amazon.co.jp/test-sale",
                     "products": products}
        self.brief = {"campaign_type": "sale_launch", "stage": "launch", "channel": "amazon", "product_count": 4}

    def tearDown(self):
        self.temp.cleanup()

    def plan(self, recipe_id="autumn-sale-open-v1"):
        plan = history.make_plan({**self.brief, "preferred_recipe": recipe_id}, {"samples": self.samples}, self.catalog,
                                 evidence_base_dir=self.root)
        self.assertEqual(plan["planning_status"], "READY_FOR_INTERNAL_RENDER")
        return plan

    def build(self, data=None, plan=None, label="draft", export=False):
        target = self.root / label
        report = renderer.build(data if data is not None else self.data, plan if plan is not None else self.plan(),
                                target, export=export)
        return target, report

    def test_autumn_and_pd_change_modules_and_product_grouping(self):
        autumn, _ = self.build(plan=self.plan("autumn-sale-open-v1"), label="autumn")
        pd, _ = self.build(plan=self.plan("pd-sale-open-v1"), label="pd")
        autumn_structure = Structure((autumn / "email.html").read_text())
        pd_structure = Structure((pd / "email.html").read_text())
        self.assertNotEqual([x["attrs"]["data-module"] for x in autumn_structure.modules],
                            [x["attrs"]["data-module"] for x in pd_structure.modules])
        self.assertEqual(autumn_structure.groups()["featured_product"], ["lock"])
        self.assertEqual(autumn_structure.groups()["secondary_products"], ["hub", "robot", "curtain"])
        self.assertEqual(pd_structure.groups()["featured_products"], ["lock", "hub"])
        self.assertEqual(pd_structure.groups()["secondary_products"], ["robot", "curtain"])

    def test_each_product_has_one_card_with_its_own_image_and_destination(self):
        for recipe_id in ("autumn-sale-open-v1", "pd-sale-open-v1"):
            with self.subTest(recipe=recipe_id):
                out, _ = self.build(plan=self.plan(recipe_id), label=recipe_id)
                markup = (out / "email.html").read_text()
                structure = Structure(markup)
                self.assertEqual([card["attrs"]["data-card-product"] for card in structure.cards],
                                 [product["id"] for product in self.data["products"]])
                for product in self.data["products"]:
                    card = next(card for card in structure.cards if card["attrs"]["data-card-product"] == product["id"])
                    images = [image for image in structure.images if structure.inside(image, card)]
                    self.assertEqual(len(images), 1)
                    self.assertEqual(images[0]["attrs"]["data-product-id"], product["id"])
                    self.assertEqual(images[0]["attrs"]["src"], product["image_url"])
                    self.assertIn(product["url"], markup)
                assets = json.loads((out / "asset-manifest.json").read_text())
                self.assertEqual(len({asset["sha256"] for asset in assets}), 4)
                self.assertEqual([asset["image_source"] for asset in assets],
                                 [product["image_source"] for product in self.data["products"]])

    def test_product_reveal_single_sku_renders_only_confirmed_current_details(self):
        brief = {"campaign_type": "product_launch", "stage": "launch", "channel": "official", "product_count": 1,
                 "preferred_recipe": "product-reveal-v1"}
        plan = history.make_plan(brief, {"samples": self.samples}, self.catalog, evidence_base_dir=self.root)
        self.assertEqual(plan["planning_status"], "READY_FOR_INTERNAL_RENDER")
        data = copy.deepcopy(self.data)
        data["products"] = data["products"][:1]
        data["channel"] = "official"
        data["main_url"] = "https://official.example.invalid/current-product"
        data["main_cta"] = "公式サイトで見る"
        data["products"][0]["url"] = "https://official.example.invalid/current-product"
        data["details"] = [
            {"title": "CURRENT-CONFIRMED-TITLE", "body": "CURRENT-CONFIRMED-BODY",
             "status": "CONFIRMED", "source": "https://official.example.invalid/current-detail"},
            {"title": "UNCONFIRMED-TITLE", "body": "UNCONFIRMED-BODY", "status": "UNCONFIRMED",
             "source": "https://official.example.invalid/draft-detail"},
            {"title": "MISSING-SOURCE-TITLE", "body": "MISSING-SOURCE-BODY", "status": "CONFIRMED"},
        ]
        out, report = self.build(data=data, plan=plan, label="single-product")
        markup = (out / "email.html").read_text()
        structure = Structure(markup)
        self.assertEqual([module["attrs"]["data-module"] for module in structure.modules],
                         ["product_hero", "value_story", "product_details", "closing_cta", "legal_footer"])
        self.assertEqual(structure.cards, [])
        self.assertEqual([image["attrs"]["data-product-id"] for image in structure.images if "data-product-id" in image["attrs"]],
                         ["lock"])
        self.assertIn("CURRENT-CONFIRMED-TITLE", markup)
        self.assertIn("CURRENT-CONFIRMED-BODY", markup)
        self.assertIn("公式サイトで見る", markup)
        self.assertNotIn("Amazon", markup)
        for forbidden in ("UNCONFIRMED-TITLE", "UNCONFIRMED-BODY", "MISSING-SOURCE-TITLE", "MISSING-SOURCE-BODY"):
            self.assertNotIn(forbidden, markup)
        self.assertEqual(report["offline_render"]["status"], "NOT_EXECUTED")

    def test_security_two_skus_render_scenario_products_and_selection_help(self):
        brief = {"campaign_type": "category_promotion", "stage": "mid_campaign", "channel": "amazon", "product_count": 2,
                 "preferred_recipe": "category-security-v1"}
        plan = history.make_plan(brief, {"samples": self.samples}, self.catalog, evidence_base_dir=self.root)
        self.assertEqual(plan["planning_status"], "READY_FOR_INTERNAL_RENDER")
        data = copy.deepcopy(self.data)
        data["products"] = data["products"][:2]
        out, report = self.build(data=data, plan=plan, label="security")
        markup = (out / "email.html").read_text()
        structure = Structure(markup)
        self.assertEqual([module["attrs"]["data-module"] for module in structure.modules],
                         ["scenario_hero", "scenario_products", "selection_help", "closing_cta", "legal_footer"])
        self.assertEqual(structure.groups()["scenario_products"], ["lock", "hub"])
        self.assertEqual(len(structure.cards), 2)
        for card, product in zip(structure.cards, data["products"]):
            images = [image for image in structure.images if structure.inside(image, card)]
            self.assertEqual(len(images), 1)
            self.assertEqual(images[0]["attrs"]["data-product-id"], product["id"])
            self.assertEqual(images[0]["attrs"]["src"], product["image_url"])
        self.assertIn("購入前に、設置条件をチェック。", markup)
        self.assertEqual(report["offline_render"]["status"], "NOT_EXECUTED")

    def test_missing_asset_source_or_wrong_product_binding_is_rejected(self):
        for patch in ({"image": str(self.root / "absent.png")}, {"image_source": ""}, {"product_source": ""},
                      {"asset_product_id": "another_product"}):
            with self.subTest(patch=patch):
                data = copy.deepcopy(self.data)
                data["products"][0].update(patch)
                with self.assertRaises(ValueError):
                    self.build(data=data)

    def test_history_payload_and_unconfirmed_current_offer_are_not_inherited(self):
        out, _ = self.build()
        for filename in ("email.html", "email-preview.html", "review.html", "plan.json", "inheritance-map.json"):
            content = (out / filename).read_text()
            for forbidden in ("PRIVATE-HISTORICAL-COPY", "OLD99OFF", "OLDPRICE123456", "¥123,456", "¥234,567"):
                self.assertNotIn(forbidden, content, filename)
        self.assertIn("セール価格・対象条件を", (out / "email.html").read_text())

    def test_confirmed_current_offer_uses_current_price_and_reference_price(self):
        data = copy.deepcopy(self.data)
        data["products"][0]["offer"] = {"status": "CONFIRMED", "source": "https://official.example.invalid/current-offer",
                                          "sale_price_jpy": 12980, "reference_price_jpy": 19980}
        out, _ = self.build(data=data)
        markup = (out / "email.html").read_text()
        self.assertIn("¥12,980", markup)
        self.assertIn("¥19,980", markup)
        self.assertIn("（税込）", markup)
        self.assertNotIn("¥234,567", markup)

    def test_confirmed_invalid_prices_are_rejected(self):
        for offer in ({"sale_price_jpy": -1}, {"sale_price_jpy": True}, {"sale_price_jpy": 15000, "reference_price_jpy": 10000}):
            with self.subTest(offer=offer):
                data = copy.deepcopy(self.data)
                data["products"][0]["offer"] = {"status": "CONFIRMED", "source": "https://official.example.invalid/current-offer", **offer}
                with self.assertRaises(ValueError):
                    self.build(data=data)

    def test_native_email_excludes_scripts_base64_and_event_handlers(self):
        data = copy.deepcopy(self.data)
        data["products"][0]["benefit"] = '<script>alert("x")</script><img src=x onerror="bad()">'
        out, report = self.build(data=data)
        markup = (out / "email.html").read_text()
        self.assertNotRegex(markup, r"(?i)<script\b|<iframe\b|data:image/|;base64,")
        self.assertFalse(any(re.search(r"(?i)\s+on[a-z]+\s*=", tag) for tag in re.findall(r"<img\b[^>]*>", markup)))
        self.assertIn("&lt;script&gt;", markup)
        self.assertEqual(report["static_qa"], "PASS")
        self.assertEqual(report["send_readiness"], "BLOCKED")

    def test_ineligible_or_unbacked_plan_is_rejected(self):
        for patch in ({"planning_status": "BLOCKED_HISTORY_EVIDENCE"}, {"visual_inheritance": "NONE"},
                      {"selected_reference_ids": [], "source_image_hashes": []}):
            with self.subTest(patch=patch):
                plan = self.plan()
                plan.update(patch)
                with self.assertRaises(ValueError):
                    self.build(plan=plan)

    def test_tampered_catalog_values_or_module_order_are_rejected(self):
        for mutate in (lambda recipe: recipe["tokens"].update({"accent": "#000000"}),
                       lambda recipe: recipe["modules"].reverse(),
                       lambda recipe: recipe.update({"card_layout": "unreviewed_geometry"})):
            plan = self.plan()
            mutate(plan["selected_recipe"])
            with self.assertRaises(ValueError):
                self.build(plan=plan)

    def test_renderer_rejects_current_channel_or_count_that_differs_from_plan(self):
        for patch in ({"channel": "official"}, {"products": self.data["products"][:2]}):
            with self.subTest(patch=list(patch)):
                data = copy.deepcopy(self.data)
                data.update(patch)
                with self.assertRaises(ValueError):
                    self.build(data=data)

    def test_input_cannot_self_assert_browser_qa_pass(self):
        data = copy.deepcopy(self.data)
        data["browser_qa"] = {"status": "PASS", "tested_widths": [320, 390, 600]}
        _, report = self.build(data=data)
        self.assertNotEqual(report["browser_qa"].get("status"), "PASS")

    @unittest.skipUnless(importlib.util.find_spec("weasyprint") and importlib.util.find_spec("fitz"),
                         "Optional offline export dependencies are unavailable")
    def test_offline_export_creates_two_real_pngs_without_claiming_browser_validation(self):
        out, report = self.build(label="offline-smoke", export=True)
        offline = report["offline_render"]
        self.assertEqual(offline["status"], "OFFLINE_REFERENCE_ONLY", offline)
        self.assertEqual({item["width_css_px"] for item in offline["outputs"]}, {390, 600})
        self.assertFalse(offline["browser_screenshot"])
        self.assertFalse(offline["network"])
        self.assertFalse(offline["javascript"])
        for item in offline["outputs"]:
            png = (out / item["file"]).read_bytes()
            self.assertTrue(png.startswith(b"\x89PNG\r\n\x1a\n"))
            self.assertGreater(len(png), 100)
            width, height = struct.unpack(">II", png[16:24])
            self.assertEqual((width, height), (item["png_width"], item["png_height"]))
            self.assertEqual(hashlib.sha256(png).hexdigest(), item["sha256"])
        self.assertEqual(report["status"], "INTERNAL_DRAFT")
        self.assertEqual(report["send_readiness"], "BLOCKED")
        self.assertNotEqual(report["browser_qa"].get("status"), "PASS")
        self.assertEqual(report["email_client_qa"], "NOT_EXECUTED")
        self.assertFalse(report["frozen_ruby_runtime_executed"])


if __name__ == "__main__":
    unittest.main()
