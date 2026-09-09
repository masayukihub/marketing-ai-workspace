"""Behavioral editor tests; Node DOM checks do not assert browser/inbox QA."""
import base64
import importlib.util
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
import unittest


SKILL = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("editable_review_under_test", SKILL / "scripts/editable_review.py")
editor = importlib.util.module_from_spec(spec)
spec.loader.exec_module(editor)
NODE = shutil.which("node")
DOM_MODULE = os.environ.get("EDM_TEST_DOM_MODULE")


class EditableReviewTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.data = {"subject": "秋のセール", "preheader": "対象価格を見る", "products": [
            {"id": "hub", "name": "SwitchBot テストハブ", "benefit": "Current benefit", "url": "https://example.invalid/hub",
             "offer": {"status": "CONFIRMED", "sale_price_jpy": 9980, "reference_price_jpy": 12000,
                       "source": "https://source.example.invalid/price"}}],
            "subject_options": [{"id": str(i), "label": "方向" + str(i), "subject": "件名" + str(i), "preheader": "副題" + str(i)} for i in range(3)]}
        self.native = '<!doctype html><html><head><title>Old</title></head><body><p data-edit="preheader">Old</p><tr data-module="coupon"><td>Coupon</td></tr><section data-offer-product="hub"><strong data-edit="products.0.offer.sale_price_jpy" data-edit-format="jpy">¥9,980</strong></section><a data-edit-href="products.0.url" href="https://example.invalid/hub">CTA</a><img src="https://assets.example.invalid/hub.png"></body></html>'
        self.preview = self.native.replace('https://assets.example.invalid/hub.png', 'data:image/png;base64,PREVIEW_ONLY')

    def tearDown(self):
        self.temp.cleanup()

    def js(self, body):
        if not NODE:
            self.skipTest("Node is unavailable")
        module = self.root / "core.cjs"
        module.write_text(editor.EDITOR_JS)
        script = "const assert=require('node:assert/strict'); const core=require(" + json.dumps(str(module)) + ");\n"
        script += "const data=" + json.dumps(self.data, ensure_ascii=False) + ";\n" + body
        result = subprocess.run([NODE, "-e", script], text=True, capture_output=True, timeout=20)
        self.assertEqual(result.returncode, 0, result.stderr)
        return result.stdout

    def test_payload_keeps_three_subjects_and_separate_original_email(self):
        path = self.root / "editor.html"
        report = editor.build_editor(self.data, self.preview, self.native, path)
        markup = path.read_text()
        payload = json.loads(re.search(r'<script id="edm-editor-payload" type="application/json">(.*?)</script>', markup, re.S)[1])
        self.assertEqual(len(payload["data"]["subject_options"]), 3)
        self.assertEqual(base64.b64decode(payload["native_b64"]).decode(), self.native)
        self.assertEqual(base64.b64decode(payload["preview_b64"]).decode(), self.preview)
        self.assertNotIn("PREVIEW_ONLY", base64.b64decode(payload["native_b64"]).decode())
        self.assertEqual(report["browser_qa"], "NOT_EXECUTED")
        self.assertEqual(report["storage"], "LOCAL_DOWNLOAD_ONLY")

    def test_embedded_copy_cannot_close_json_script(self):
        self.data["subject"] = '</script><script>alert("synthetic")</script>'
        output = self.root / "safe.html"
        editor.build_editor(self.data, self.preview, self.native, output)
        markup = output.read_text()
        raw = re.search(r'<script id="edm-editor-payload" type="application/json">(.*?)</script>', markup, re.S)[1]
        self.assertNotIn("</script", raw)
        self.assertEqual(json.loads(raw)["data"]["subject"], self.data["subject"])

    def test_duplicate_subject_ids_are_rejected(self):
        self.data["subject_options"][1]["id"] = "0"
        with self.assertRaises(ValueError):
            editor.build_editor(self.data, self.preview, self.native, self.root / "bad.html")

    def test_price_edits_downgrade_approval_and_json_reloads(self):
        self.js("""
        const original=JSON.parse(JSON.stringify(data));
        core.editValue(data,'products.0.offer.sale_price_jpy','8800','price');
        core.editValue(data,'products.0.benefit','新しい文案','text');
        assert.equal(data.products[0].offer.status,'DRAFT');
        const exported=core.exportData(data,['products.0.offer.sale_price_jpy','products.0.benefit']);
        assert.equal(exported._editor.qa_status,'REVIEW_REQUIRED');
        const loaded=core.importData(original,exported,[{path:'products.0.offer.sale_price_jpy',type:'price'},{path:'products.0.benefit',type:'text'}]);
        assert.equal(loaded.data.products[0].offer.sale_price_jpy,8800);
        assert.equal(loaded.data.products[0].offer.status,'DRAFT');
        assert.equal(loaded.data.products[0].benefit,'新しい文案');
        assert.equal(loaded.data.products[0].offer.source,original.products[0].offer.source);
        assert.equal(exported._editor.state,'INTERNAL_DRAFT');
        """)

    def test_import_cannot_change_product_identity_sources_or_authority(self):
        self.js("""
        const patch=JSON.parse(JSON.stringify(data));
        patch.products[0].offer.sale_price_jpy=100;
        patch.products[0].offer.status='CONFIRMED';
        patch.products[0].offer.source='https://fake.example.invalid/approval';
        patch.products[0].image='https://fake.example.invalid/product.png';
        const loaded=core.importData(data,patch,[{path:'products.0.offer.sale_price_jpy',type:'price'}]);
        assert.equal(loaded.data.products[0].offer.status,'DRAFT');
        assert.equal(loaded.data.products[0].offer.source,data.products[0].offer.source);
        assert.equal(loaded.data.products[0].image,undefined);
        patch.products[0].id='different';
        assert.throws(()=>core.importData(data,patch,[]));
        """)

    def test_bad_urls_negative_prices_and_prototype_mutation_are_rejected(self):
        self.js("""
        assert.throws(()=>core.editValue(data,'products.0.url','javascript:alert(1)','url'));
        assert.throws(()=>core.editValue(data,'products.0.url','https://name:pass@example.invalid','url'));
        assert.throws(()=>core.editValue(data,'products.0.offer.sale_price_jpy','-9','price'));
        assert.throws(()=>core.setValue(data,'__proto__.polluted',true));
        assert.throws(()=>core.setValue(data,'products.constructor.prototype.polluted',true));
        assert.equal({}.polluted,undefined);
        assert.equal(core.validURL('{{PRODUCT_URL}}'),true);
        assert.equal(core.validURL('https://www.amazon.co.jp/dp/SYNTHETIC'),true);
        """)

    def test_only_optional_modules_can_be_hidden_when_imported(self):
        self.js("""
        const patch=JSON.parse(JSON.stringify(data)); patch.module_enabled={coupon:false,line:false};
        const loaded=core.importData(data,patch,[]);
        assert.equal(loaded.data.module_enabled.coupon,false);
        patch.module_enabled.legal_footer=false;
        assert.throws(()=>core.importData(data,patch,[]));
        """)

    @unittest.skipUnless(DOM_MODULE, "Set EDM_TEST_DOM_MODULE to linkedom for nonbrowser DOM verification")
    def test_native_dom_export_applies_edits_without_preview_images_or_handlers(self):
        self.js("const {DOMParser}=require(" + json.dumps(DOM_MODULE) + ");\nconst native=" + json.dumps(self.native) + ";\n" + """
        core.editValue(data,'products.0.offer.sale_price_jpy','7777','price');
        core.editValue(data,'products.0.url','https://example.invalid/new','url');
        data.module_enabled={coupon:false};
        const doc=new DOMParser().parseFromString(native,'text/html');
        doc.querySelector('strong').setAttribute('contenteditable','true');
        doc.querySelector('img').setAttribute('onerror','alert(1)');
        const output=core.applyDocument(doc,data,true);
        assert(output.includes('¥7,777'));
        assert(output.includes('参考価格・要確認'));
        assert(output.includes('https://example.invalid/new'));
        assert(output.includes('https://assets.example.invalid/hub.png'));
        assert(!output.includes('data:image'));
        assert(!output.includes('contenteditable'));
        assert(!output.includes('onerror'));
        assert(!output.includes('data-edit='));
        assert(!output.includes('data-module="coupon"'));
        assert(output.includes('data-status="INTERNAL_DRAFT"'));
        """)

    @unittest.skipUnless(DOM_MODULE and NODE, "Node and linkedom are required for nonbrowser interaction verification")
    def test_subject_selection_price_edit_and_saved_review_survive_reload(self):
        self.data["products"][0]["offer"]["status"] = "UNKNOWN"
        self.data["products"][0]["offer"].pop("sale_price_jpy")
        self.data["products"][0]["offer"]["reference_price_jpy"] = None
        self.data["coupon"] = {"status": "UNKNOWN", "code": "", "valid_from": "", "valid_until": ""}
        self.native = self.native.replace("¥9,980", "要確認")
        self.preview = self.preview.replace("¥9,980", "要確認")
        self.native = self.native.replace("Coupon", '<span data-edit="coupon.code">発行内容を確認中</span>')
        self.preview = self.preview.replace("Coupon", '<span data-edit="coupon.code">発行内容を確認中</span>')
        target = self.root / "review.html"
        editor.build_editor(self.data, self.preview, self.native, target)
        code = """
        const assert=require('node:assert/strict'), fs=require('node:fs'), vm=require('node:vm');
        const {DOMParser}=require(DOM_MODULE);
        const original=fs.readFileSync(REVIEW_PATH,'utf8');
        async function openEditor(markup) {
          const document=new DOMParser().parseFromString(markup,'text/html');
          const saved=[];
          class LocalURL extends URL {}
          LocalURL.createObjectURL=blob=>{saved.push(blob);return 'blob:synthetic-'+saved.length;};
          LocalURL.revokeObjectURL=()=>{};
          const window=document.defaultView;
          const sandbox={window,document,DOMParser,URL:LocalURL,Blob,TextDecoder,Uint8Array,atob,
            navigator:{clipboard:{writeText:async()=>{}}},setTimeout:()=>1,clearTimeout:()=>{},console};
          const scripts=document.querySelectorAll('script');
          vm.runInNewContext(scripts[scripts.length-1].textContent,sandbox);
          return {document,window,saved};
        }
        (async()=>{
          const app=await openEditor(original);
          assert.equal(app.document.querySelectorAll('.subject-card').length,3);
          app.document.querySelectorAll('.subject-card')[2].click();
          assert.equal(app.document.getElementById('selected-subject').textContent,'件名2');
          const price=app.document.querySelector('[data-control-path="products.0.offer.sale_price_jpy"]');
          assert.equal(price.value,'');
          price.value='7777';price.dispatchEvent(new app.window.Event('input'));
          const reference=app.document.querySelector('[data-control-path="products.0.offer.reference_price_jpy"]');
          assert.equal(reference.value,'');
          assert(app.document.querySelector('[data-control-path="coupon.valid_from"]'));
          assert(app.document.querySelector('[data-control-path="coupon.valid_until"]'));
          reference.value='7000';reference.dispatchEvent(new app.window.Event('input'));
          app.document.getElementById('save-email').click();
          assert.equal(app.saved.length,0);
          assert(app.document.getElementById('toast').textContent.includes('比较价不能低于活动价'));
          reference.value='9999';reference.dispatchEvent(new app.window.Event('input'));
          app.document.getElementById('save-json').click();
          const json=JSON.parse(await app.saved.pop().text());
          assert.equal(json.products[0].offer.sale_price_jpy,7777);
          assert.equal(json.products[0].offer.reference_price_jpy,9999);
          assert.equal(json.products[0].offer.status,'DRAFT');
          assert.equal(json.subject,'件名2');assert.equal(json.preheader,'副題2');
          app.document.getElementById('save-email').click();
          const native=await app.saved.pop().text();
          assert(native.includes('¥7,777'));assert(native.includes('https://assets.example.invalid/hub.png'));
          assert(native.includes('¥9,999'));assert(native.includes('class="reference-price"'));
          assert(native.includes('発行内容を確認中'));
          assert(!native.includes('PREVIEW_ONLY'));assert(!native.includes('<script'));
          app.document.getElementById('save-review').click();
          const updated=await app.saved.pop().text();
          const reopened=await openEditor(updated);
          assert.equal(reopened.document.getElementById('selected-subject').textContent,'件名2');
          assert.equal(reopened.document.querySelector('[data-control-path="products.0.offer.sale_price_jpy"]').value,'7777');
          assert.equal(reopened.document.querySelector('[data-control-path="products.0.offer.reference_price_jpy"]').value,'9999');
          assert.equal(reopened.document.querySelectorAll('.subject-card.selected').length,1);
        })().catch(error=>{console.error(error);process.exit(1);});
        """
        code = "const DOM_MODULE=" + json.dumps(DOM_MODULE) + ";const REVIEW_PATH=" + json.dumps(str(target)) + ";\n" + code
        result = subprocess.run([NODE, "-e", code], text=True, capture_output=True, timeout=20)
        self.assertEqual(result.returncode, 0, result.stderr)

    @unittest.skipUnless(DOM_MODULE, "Set EDM_TEST_DOM_MODULE to linkedom for nonbrowser DOM verification")
    def test_line_url_change_removes_stale_qr_from_both_html_exports_and_json(self):
        self.js("const {DOMParser}=require(" + json.dumps(DOM_MODULE) + ");\n" + """
        data.line={status:'CONFIRMED',url:'https://line.example.invalid/old',qr_target:'https://line.example.invalid/old',
          qr_image:'assets/old-line-qr.png',qr_image_url:'https://assets.example.invalid/old-line-qr.png'};
        const markup='<html><head></head><body><table><tr data-module="line"><td><a data-edit-href="line.url" href="https://line.example.invalid/old"><img src="https://assets.example.invalid/old-line-qr.png" data-qr-target="https://line.example.invalid/old"></a><a data-edit-href="line.url" href="https://line.example.invalid/old">LINE CTA</a></td></tr></table></body></html>';
        const parse=html=>new DOMParser().parseFromString(html,'text/html');
        const before=core.applyDocument(parse(markup),data,true);
        assert(before.includes('data-qr-target="https://line.example.invalid/old"'));
        core.editValue(data,'line.url','https://line.example.invalid/new','url');
        assert.equal(data.line.status,'DRAFT');
        assert.equal(data.line.qr_status,'STALE_REGENERATE_REQUIRED');
        for(const native of [false,true]) {
          const result=core.applyDocument(parse(markup),data,native);
          assert(!result.includes('old-line-qr.png'));
          assert(!result.includes('data-qr-target'));
          assert(!result.includes('https://line.example.invalid/old'));
          assert(result.includes('https://line.example.invalid/new'));
          assert(result.includes('QRコードは更新確認中です。'));
        }
        const saved=core.exportData(data,['line.url']);
        assert.equal(saved.line.qr_image,undefined);
        assert.equal(saved.line.qr_image_url,undefined);
        assert.equal(saved.line.qr_status,'STALE_REGENERATE_REQUIRED');
        assert.equal(saved._editor.qa_status,'REVIEW_REQUIRED');
        """)


if __name__ == "__main__":
    unittest.main()
