#!/usr/bin/env node
import assert from "node:assert/strict";
import fs from "node:fs/promises";
import os from "node:os";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { spawnSync } from "node:child_process";
import { buildAssetProvenance, classifyAssetSource } from "../scripts/asset_provenance.mjs";
import { blockFinalOutputs, syncFinalExports } from "../scripts/phase_system.mjs";
import { ratingDisplayModel, renderFromSpec } from "../scripts/render_v4.mjs";
import { assertStoryMutationAllowed, assertStorySequenceIntegrity, assertStorySequenceStateIntegrity, lockStorySequence, storySequenceFingerprint } from "../scripts/story_sequence_lock.mjs";
import { brandFitAssessment, templateFeelingAssessment, visualQualityManifest, visualRhythmScore } from "../scripts/visual_quality_system.mjs";
import { buildProductPageSpec, readTemplateLibrary, refreshSpec, STAGES, validateSpec } from "../scripts/spec_system.mjs";

const root = path.dirname(path.dirname(fileURLToPath(import.meta.url)));
const clone = (value) => JSON.parse(JSON.stringify(value));
const temp = await fs.mkdtemp(path.join(os.tmpdir(), "pdp-production-safety-"));

const storySpec = {
  human_gates: { story_approval: { status: "Approved" } },
  product_images: Array.from({ length: 7 }, (_, index) => ({ id: `IMAGE-${String(index + 1).padStart(2, "0")}`, sequence: index + 1, stage: `stage-${index + 1}` })),
  aplus_modules: Array.from({ length: 7 }, (_, index) => ({ id: `APLUS-M${String(index + 1).padStart(2, "0")}`, sequence: index + 1, units: [{ id: `APLUS-U${String(index + 1).padStart(2, "0")}`, stage: `stage-${index + 1}` }] })),
};

// Even a complete set of varied profile tags cannot review pixels or approve
// commercial artwork. ON/OFF must not manufacture a brand score or LOW risk.
for (const mode of ["ON", "OFF"]) {
  const brand = brandFitAssessment(mode);
  assert.equal(brand.visual_review_status, "NOT_VISUALLY_REVIEWED");
  assert.equal(brand.score, null);
  assert.equal(brand.risk, "NOT_VISUALLY_REVIEWED");
  assert.ok(Object.values(brand.dimensions).every((value) => value === null));
  const feeling = templateFeelingAssessment(mode);
  assert.equal(feeling.visual_review_status, "NOT_VISUALLY_REVIEWED");
  for (const key of ["overall_risk", "gallery_risk", "aplus_risk"]) assert.equal(feeling[key], "NOT_VISUALLY_REVIEWED");
  assert.deepEqual(feeling.signals, []);
}
const qualityManifest = visualQualityManifest(storySpec);
assert.equal(qualityManifest.visual_review_status, "NOT_VISUALLY_REVIEWED");
assert.equal(qualityManifest.brand_fit.score, null);
assert.equal(qualityManifest.template_feeling.overall_risk, "NOT_VISUALLY_REVIEWED");
const rhythm = visualRhythmScore(qualityManifest);
assert.ok(Number.isFinite(rhythm.score));
assert.match(rhythm.score_scope, /STRUCTURAL_HEURISTIC.*not rendered-image quality/);
assert.equal(rhythm.visual_review_status, "NOT_VISUALLY_REVIEWED");

const renderSpec = {
  meta: { spec_sha256: "production-safety-render-fixture" },
  strategy: { coreValue: "Synthetic render regression" },
  product: { name: "Synthetic render regression", main_asset: "assets/product.svg" },
  human_gates: { final_render_authorized: true, story_approval: { status: "Approved — Internal QA" }, layout_approval: { status: "Approved — Internal QA" } },
  template_library: { source_policy: {}, registered_template_count: 19 },
  titles: { recommendedKey: "main", main: "Synthetic render regression" },
  bullets: [], faq: [], sources: [],
  copy_review: { status: "Draft" },
  publish_gate: { status: "BLOCKED", sections: {} },
  asset_resolution_plan: { records: [] },
  product_images: ["P-MAIN-OFFICIAL", "P-TECHNICAL-PROOF"].map((template_id, index) => ({
    id: `IMAGE-0${index + 1}`, sequence: index + 1, template_id, headline: "Fixture", sub_copy: "Regression", key_message: "Fixture",
    layers: { product_layer: { source: "assets/product.svg" }, scene_layer: { source: "" } },
    template_snapshot: { name: "Regression", grid: {}, safe_area: {}, headline_length: {}, mobile_rules: [] },
    outputs: { svg: `design/svg/image_0${index + 1}.svg`, wireframe_svg: `design/svg/wireframe_0${index + 1}.svg`, jpeg: `design/product_images/image_0${index + 1}.jpg` },
    product_body_ai_generated: false, source_origin: "Internal Placeholder", asset_resolution: { product_layer_allowed: false },
  })),
  aplus_modules: [],
};
const visualQualityEnv = process.env.VISUAL_QUALITY;
try {
  for (const mode of ["ON", "OFF"]) {
    process.env.VISUAL_QUALITY = mode;
    for (const visualType of ["commercial_scene", "mechanism_visual"]) {
      for (const target of ["gallery", "module", "unit"]) {
        const request = clone(renderSpec);
        let expectedPath;
        if (target === "gallery") {
          request.product_images[1].visual_type = visualType;
          expectedPath = "product_images[1].visual_type";
        } else {
          request.aplus_modules = [{ id: "APLUS-M01", template_id: "A-50-50-FEATURE", units: [{ id: "APLUS-U01" }] }];
          if (target === "module") request.aplus_modules[0].visual_type = visualType;
          else request.aplus_modules[0].units[0].visual_type = visualType;
          expectedPath = target === "module" ? "aplus_modules[0].visual_type" : "aplus_modules[0].units[0].visual_type";
        }
        const targetDir = path.join(temp, `capability-${mode}-${visualType}-${target}`);
        // Exercise the renderer entry point, including incremental selection;
        // a selection cannot hide a declared unsupported visual in the Spec.
        const result = await renderFromSpec(request, targetDir, { product_ids: ["IMAGE-01"], aplus_ids: [] });
        assert.equal(result.status, "VISUAL_CAPABILITY_MISMATCH");
        assert.equal(result.rendered, false);
        assert.equal(result.visual_capability_check.mismatches[0].field_path, expectedPath);
        await assert.rejects(fs.access(targetDir), { code: "ENOENT" });
      }
    }
  }
  process.env.VISUAL_QUALITY = "ON";
  for (const declared of [false, true]) {
    const request = clone(renderSpec);
    if (declared) {
      request.product_images[0].visual_type = "official_packshot";
      request.product_images[1].visual_type = "information_graphic";
    }
    const targetDir = path.join(temp, declared ? "declared-template-render" : "legacy-template-render");
    await fs.mkdir(path.join(targetDir, "assets"), { recursive: true });
    await fs.writeFile(path.join(targetDir, "assets/product.svg"), '<svg xmlns="http://www.w3.org/2000/svg" width="100" height="100"><rect x="25" y="10" width="50" height="80" fill="#777"/></svg>');
    const result = await renderFromSpec(request, targetDir);
    assert.equal(result.status, "Rendered");
    assert.equal(result.rendered, true);
    for (const item of request.product_images) {
      const jpeg = await fs.readFile(path.join(targetDir, item.outputs.jpeg));
      assert.equal(jpeg.readUInt16BE(0), 0xffd8);
    }
    const manifest = JSON.parse(await fs.readFile(path.join(targetDir, "reports/visual_production_manifest.json"), "utf8"));
    assert.equal(manifest.visual_capability_check.status, "NO_EXPLICIT_CAPABILITY_MISMATCH");
    assert.match(manifest.visual_capability_check.scope, /Legacy records without visual_type are not covered/);
    assert.deepEqual(manifest.visual_capability_check.undeclared_visual_type_ids, declared ? [] : ["IMAGE-01", "IMAGE-02"]);
    assert.equal(request.publish_gate.status, "BLOCKED");
  }
} finally {
  if (visualQualityEnv === undefined) delete process.env.VISUAL_QUALITY;
  else process.env.VISUAL_QUALITY = visualQualityEnv;
}

// Build a structurally valid full Spec through the production builder, then
// exercise the real CLI, including refresh/validation and persisted Spec read.
const cliFixtureDir = path.join(temp, "cli-fixture");
await fs.mkdir(cliFixtureDir, { recursive: true });
await fs.writeFile(path.join(cliFixtureDir, "placeholder.svg"), '<svg xmlns="http://www.w3.org/2000/svg" width="100" height="100"><rect width="100" height="100" fill="#ddd"/></svg>');
const cliInput = {
  meta: { market: "JP", productAssetOrigin: "Internal Placeholder", externalPublishReady: false },
  product: { name: "CLI Regression Fixture", mainImage: "placeholder.svg", productBodyAiGenerated: false },
  strategy: { coreValue: "回帰テスト" },
  titles: { main: "回帰テスト", recommendedKey: "main" },
  bullets: Array.from({ length: 5 }, () => ({ headline: "確認", body: "構造テスト用です。" })),
  images: STAGES.map(([stage], index) => ({ id: `IMAGE-0${index + 1}`, stage, headline: index === 0 ? "" : "確認", subcopy: "構造テスト用です。" })),
  aplusModules: Array.from({ length: 7 }, (_, index) => ({ id: `APLUS-M0${index + 1}`, purpose: "構造確認", units: [{ id: `APLUS-U0${index + 1}`, headline: "確認", copy: "構造テスト用です。" }] })),
  journey: [], comparison: {}, seo: {}, faq: [], claims: [], sources: [],
};
const cliInputFile = path.join(cliFixtureDir, "input.json");
await fs.writeFile(cliInputFile, JSON.stringify(cliInput));
const library = await readTemplateLibrary(root);
const cliBaseSpec = await buildProductPageSpec(cliInput, cliInputFile, path.join(cliFixtureDir, "built"), library, "internal-test");
assert.deepEqual(validateSpec(cliBaseSpec, library), []);
assert.equal(cliBaseSpec.human_gates.final_render_authorized, true);
assert.equal(cliBaseSpec.publish_gate.status, "BLOCKED");
for (const visualType of ["commercial_scene", "mechanism_visual"]) {
  const request = clone(cliBaseSpec);
  request.product_images[1].visual_type = visualType;
  refreshSpec(request, library);
  assert.deepEqual(validateSpec(request, library), []);
  const specFile = path.join(cliFixtureDir, `${visualType}.json`);
  const cliOutput = path.join(temp, `cli-${visualType}`);
  await fs.writeFile(specFile, JSON.stringify(request));
  const child = spawnSync(process.execPath, [path.join(root, "scripts/render_from_spec.mjs"), "--spec", specFile, "--output", cliOutput], { encoding: "utf8", timeout: 30000 });
  assert.ifError(child.error);
  assert.equal(child.status, 1, child.stderr);
  assert.equal(child.stdout.trim(), "");
  const result = JSON.parse(child.stderr);
  assert.equal(result.structural_gate, "Pass");
  assert.equal(result.render, "VISUAL_CAPABILITY_MISMATCH");
  assert.equal(result.rendered, false);
  assert.match(result.reason, /no completed-artwork input path/);
  assert.equal(result.visual_capability_check.mismatches[0].visual_type, visualType);
  assert.equal(result.visual_capability_check.mismatches[0].field_path, "product_images[1].visual_type");
  assert.equal(result.workbooks, 0);
  assert.equal(result.publish_gate, "BLOCKED");
  const persisted = JSON.parse(await fs.readFile(path.join(cliOutput, "spec/PRODUCT_PAGE_SPEC.json"), "utf8"));
  assert.deepEqual(validateSpec(persisted, library), []);
  assert.equal(persisted.product_images[1].visual_type, visualType);
  assert.deepEqual(await fs.readdir(cliOutput), ["spec"]);
}

lockStorySequence(storySpec, { lockedBy: "Regression", lockedOn: "2026-08-19" });
assert.throws(() => assertStoryMutationAllowed(storySpec, "REORDER"), /Story Sequence Lock BLOCKED REORDER/);
const reordered = clone(storySpec);
[reordered.product_images[1], reordered.product_images[2]] = [reordered.product_images[2], reordered.product_images[1]];
assert.throws(() => assertStorySequenceIntegrity(storySpec, reordered), /integrity failure/);
const storyState = { story_sequence_locked: true, story_sequence_fingerprint: storySpec.story_sequence_lock.fingerprint };
const forged = clone(storySpec);
[forged.product_images[1], forged.product_images[2]] = [forged.product_images[2], forged.product_images[1]];
forged.story_sequence_lock.fingerprint = storySequenceFingerprint(forged);
forged.human_gates.story_approval.story_sequence_fingerprint = forged.story_sequence_lock.fingerprint;
assert.throws(() => assertStorySequenceStateIntegrity(forged, storyState), /state\/spec fingerprint mismatch/);
const removedLock = clone(storySpec);
delete removedLock.story_sequence_lock;
delete removedLock.human_gates.story_approval.story_sequence_fingerprint;
removedLock.human_gates.story_approval.story_sequence_locked = false;
assert.throws(() => assertStorySequenceStateIntegrity(removedLock, storyState), /removed from the approved Spec/);

assert.deepEqual(ratingDisplayModel({ rating: null }), { available: false, text: "—", value: null, count: null });
assert.equal(ratingDisplayModel({ rating: { value: 4.5, count: 1234, source: "Amazon API snapshot 2026-08-19", source_type: "amazon_verified_snapshot", status: "confirmed" } }).available, true);
assert.equal(ratingDisplayModel({ rating: { value: 4.5, count: 1234, source: "fixture", source_type: "amazon_verified_snapshot", status: "confirmed" } }).available, false);
assert.equal(ratingDisplayModel({ rating: { value: 4.5, count: 1234, source: "random string", status: "confirmed" } }).available, false);
assert.equal(ratingDisplayModel({ rating: { value: 4.5, count: 1234, source: "random string", source_type: "unknown", status: "confirmed" } }).available, false);

const placeholder = buildAssetProvenance({
  asset: { path: "design/assets/placeholder-product.svg", exists: true },
  meta: { source_origin: "Internal Placeholder", source_asset_type: "Official PNG", product_body_ai_generated: false },
  layer: "product",
});
assert.equal(placeholder.source_type, "placeholder");
assert.equal(placeholder.source_verified, false);
assert.equal(placeholder.product_layer_allowed, false);
assert.equal(placeholder.resolved, true);

assert.equal(classifyAssetSource({ sourcePath: "https://competitor.example/product.jpg", sourceOrigin: "External Reference", sourceAssetType: "Reference", layer: "product" }), "external_reference");
const external = buildAssetProvenance({
  asset: { path: "https://competitor.example/product.jpg", exists: true },
  meta: { source_origin: "External Reference", source_asset_type: "Reference", product_body_ai_generated: false },
  layer: "product",
});
assert.equal(external.product_layer_allowed, false);

const officialUnapproved = buildAssetProvenance({
  asset: { path: "assets/official-product.png", exists: true },
  meta: { source_origin: "User Provided Official", source_asset_type: "Official PNG", product_body_ai_generated: false, verification_status: "verified", usage_approved: false },
  layer: "product",
});
assert.equal(officialUnapproved.source_verified, true);
assert.equal(officialUnapproved.usage_approved, false);
assert.equal(officialUnapproved.product_layer_allowed, false);
const officialApproved = buildAssetProvenance({
  asset: { path: "assets/official-product.png", exists: true },
  meta: { source_origin: "User Provided Official", source_asset_type: "Official PNG", product_body_ai_generated: false, verification_status: "verified", usage_approved: true },
  layer: "product",
});
assert.equal(officialApproved.product_layer_allowed, true);

const output = path.join(temp, "output");
await fs.mkdir(path.join(output, "design", "product_images"), { recursive: true });
await fs.mkdir(path.join(output, "design", "aplus"), { recursive: true });
await fs.mkdir(path.join(output, "design", "svg"), { recursive: true });
await fs.mkdir(path.join(output, "workbooks"), { recursive: true });
await fs.writeFile(path.join(output, "design", "product_images", "image_01.jpg"), "jpeg-fixture");
await fs.writeFile(path.join(output, "design", "aplus", "aplus_01.jpg"), "jpeg-fixture");
await fs.writeFile(path.join(output, "design", "svg", "editable.svg"), "<svg/>");
await fs.writeFile(path.join(output, "workbooks", "fixture.xlsx"), "xlsx-fixture");

const deliverySpec = {
  publish_gate: { status: "BLOCKED" },
  product_images: [{ id: "IMAGE-01", outputs: { jpeg: "design/product_images/image_01.jpg" } }],
  aplus_modules: [{ id: "APLUS-M01", template_id: "A-HERO", outputs: { jpeg: "design/aplus/aplus_01.jpg" } }],
};
await fs.mkdir(path.join(output, "final", "stale"), { recursive: true });
await fs.writeFile(path.join(output, "final", "stale", "unsafe.txt"), "stale");
const blocked = await syncFinalExports(deliverySpec, output);
assert.equal(blocked.generated, false);
await assert.rejects(fs.access(path.join(output, "final")));
await assert.rejects(fs.access(path.join(output, "export")));
assert.match(await fs.readFile(path.join(output, "reports", "FINAL_OUTPUT_NOT_GENERATED.md"), "utf8"), /FINAL_OUTPUT_NOT_GENERATED\nReason: Publish Gate BLOCKED/);

deliverySpec.publish_gate.status = "PASS";
const passed = await syncFinalExports(deliverySpec, output);
assert.equal(passed.generated, true);
await fs.access(path.join(output, "final", "product_images", "image_01.jpg"));
await fs.access(path.join(output, "final", "aplus", "aplus_01.jpg"));
await fs.access(path.join(output, "export", "fixture.xlsx"));
await assert.rejects(fs.access(path.join(output, "reports", "FINAL_OUTPUT_NOT_GENERATED.md")));

await blockFinalOutputs(output, "Regression cleanup");
await assert.rejects(fs.access(path.join(output, "final")));

async function files(dir) {
  const result = [];
  for (const entry of await fs.readdir(dir, { withFileTypes: true })) {
    if (entry.name === "snapshots") continue;
    const target = path.join(dir, entry.name);
    if (entry.isDirectory()) result.push(...await files(target));
    else if (/\.(?:mjs|js|html|json|md)$/i.test(entry.name)) result.push(target);
  }
  return result;
}
const starFixture = String.fromCodePoint(0x2605).repeat(4) + String.fromCodePoint(0x2606);
const forbiddenFixtures = [starFixture, `${999} review${"s"}`, `${1},${234} review${"s"}`];
const fixtureHits = [];
for (const file of await files(root)) {
  const value = await fs.readFile(file, "utf8");
  for (const fixture of forbiddenFixtures) if (value.includes(fixture)) fixtureHits.push(`${path.relative(root, file)}:${fixture}`);
}
assert.deepEqual(fixtureHits, []);

console.log(JSON.stringify({
  status: "PASS",
  story_lock_negative: "PASS",
  fake_rating: "PASS",
  visual_quality_not_auto_approved: "PASS",
  explicit_visual_capability_guard: "PASS",
  cli_visual_capability_exit: "PASS",
  legacy_and_template_render_entry: "PASS",
  placeholder_provenance: "PASS",
  external_reference: "PASS",
  publish_blocked: "PASS",
  publish_pass: "PASS",
  fixture_scan: "PASS",
}, null, 2));
