/** Real raster-output smoke test using the existing compatibility renderer.
 * Synthetic text and neutral placeholder only. NOT an S30 production run,
 * a visual-quality assessment, a browser test, or a publication approval.
 */
import assert from "node:assert/strict";
import crypto from "node:crypto";
import fs from "node:fs/promises";
import os from "node:os";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { createRequire } from "node:module";
import { spawnSync } from "node:child_process";
import { writeReferenceRenderedAsset } from "../../amazon-japan-pdp-generator/scripts/reference_renderers.mjs";

const require = createRequire(new URL("../../amazon-japan-pdp-generator/package.json", import.meta.url));
const sharp = require("sharp");
const auditScript = fileURLToPath(new URL("../scripts/aplus_delivery.py", import.meta.url));
const root = await fs.mkdtemp(path.join(os.tmpdir(), "aplus-runtime-smoke-"));
const sha = async file => crypto.createHash("sha256").update(await fs.readFile(file)).digest("hex");

function audit(specFile) {
  const result = spawnSync("python3", [auditScript, "audit", "--scope", "full", "--spec", specFile, "--output-dir", root], { encoding: "utf8" });
  if (result.error) throw result.error;
  assert.notEqual(result.status, 2, result.stderr + result.stdout);
  return { code: result.status, value: JSON.parse(result.stdout) };
}

try {
  const spec = { fixture: "SYNTHETIC_RUNTIME_SAMPLE_NOT_PRODUCT_FACTS", publish_gate: { status: "BLOCKED" }, product_images: [], aplus_modules: [] };
  const galleryBefore = new Map();
  for (let i = 1; i <= 7; i++) {
    const rel = `gallery/g${i}.jpg`;
    const target = path.join(root, rel);
    await fs.mkdir(path.dirname(target), { recursive: true });
    await sharp({ create: { width: 64, height: 64, channels: 3, background: "white" } }).jpeg().toFile(target);
    spec.product_images.push({ id: `G${i}`, outputs: { jpeg: rel } });
    galleryBefore.set(rel, await sha(target));
  }
  // Historical 7/16 shape is a test fixture, not a fixed Amazon requirement.
  const types = ["A-BRAND", "A-INSTALLATION", "A-BRAND", "A-INSTALLATION", "A-50-50-FEATURE", "A-INSTALLATION", "A-INSTALLATION"];
  const counts = [1, 3, 1, 3, 2, 3, 3];
  let unitId = 0;
  for (let i = 0; i < types.length; i++) {
    const n = i + 1;
    spec.aplus_modules.push({
      id: `A${n}`, sequence: n, template_id: types[i], module_headline: `TEST MODULE ${n}`,
      units: Array.from({ length: counts[i] }, () => ({
        id: `U${++unitId}`, headline: `TEST ${unitId}`, copy: "SYNTHETIC TEST ONLY",
        claim_sources: [{ conditions: "テスト用・商品仕様ではありません。" }],
        layers: { product_layer: { source: "" } },
      })),
      outputs: { jpeg: `aplus/a${n}.jpg`, mobile_jpeg: `aplus/a${n}-mobile.jpg` },
    });
  }
  assert.equal(unitId, 16);
  const specFile = path.join(root, "spec.json");
  await fs.writeFile(specFile, JSON.stringify(spec, null, 2));
  const specHash = await sha(specFile);
  const missing = audit(specFile);
  assert.equal(missing.code, 1);
  assert.equal(missing.value.raster_files_decoded, 7);
  assert.deepEqual(missing.value.resume_queue, spec.aplus_modules.map(m => m.id));

  let rendered = 0;
  for (const module of spec.aplus_modules) {
    for (const viewport of ["desktop", "mobile"]) {
      const jpegPath = viewport === "mobile" ? module.outputs.mobile_jpeg : module.outputs.jpeg;
      const result = await writeReferenceRenderedAsset({
        templateId: module.template_id, record: module, outputDir: root,
        svgPath: jpegPath.replace(/\.jpg$/, ".svg"), jpegPath, viewport,
        metadata: "SYNTHETIC RUNTIME TEST; NOT A PRODUCT ASSET",
      });
      assert.equal(result.fallback_used, true, "Test must not imply use of official product assets");
      const metadata = await sharp(path.join(root, jpegPath)).metadata();
      assert.equal(metadata.format, "jpeg");
      assert.equal(metadata.width, viewport === "mobile" ? 780 : 1464);
      rendered++;
    }
  }
  const complete = audit(specFile);
  assert.equal(complete.code, 0, JSON.stringify(complete.value.issues));
  assert.equal(complete.value.raster_files_decoded, 21);
  assert.equal(complete.value.publish_gate_in_spec, "BLOCKED");

  // A single missing mobile A+ must invalidate full delivery, not reuse desktop.
  const missingModule = spec.aplus_modules[2];
  await fs.unlink(path.join(root, missingModule.outputs.mobile_jpeg));
  const incomplete = audit(specFile);
  assert.equal(incomplete.code, 1);
  assert.deepEqual(incomplete.value.resume_queue, [missingModule.id]);

  assert.equal(await sha(specFile), specHash, "Audit/render helpers must not rewrite frozen Spec");
  for (const [rel, hash] of galleryBefore) assert.equal(await sha(path.join(root, rel)), hash, `Gallery changed: ${rel}`);
  console.log(JSON.stringify({
    status: "PASS", test: "SYNTHETIC_APLUS_RENDERER_SMOKE", aplus_modules: 7, content_units: 16,
    actual_aplus_jpegs_written: rendered, desktop_jpegs: 7, mobile_jpegs: 7,
    missing_aplus_detected: true, missing_mobile_detected: true, gallery_hashes_unchanged: 7,
    spec_unchanged: true, publish_gate: "BLOCKED", s30_production: "NOT_RUN",
    browser_qa: "NOT_RUN", quality_or_channel_approval: "NOT_TESTED",
  }, null, 2));
} finally {
  await fs.rm(root, { recursive: true, force: true });
}
