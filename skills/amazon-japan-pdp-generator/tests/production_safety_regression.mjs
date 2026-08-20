#!/usr/bin/env node
import assert from "node:assert/strict";
import fs from "node:fs/promises";
import os from "node:os";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { buildAssetProvenance, classifyAssetSource } from "../scripts/asset_provenance.mjs";
import { blockFinalOutputs, syncFinalExports } from "../scripts/phase_system.mjs";
import { ratingDisplayModel } from "../scripts/render_v4.mjs";
import { assertStoryMutationAllowed, assertStorySequenceIntegrity, assertStorySequenceStateIntegrity, lockStorySequence, storySequenceFingerprint } from "../scripts/story_sequence_lock.mjs";

const root = path.dirname(path.dirname(fileURLToPath(import.meta.url)));
const clone = (value) => JSON.parse(JSON.stringify(value));
const temp = await fs.mkdtemp(path.join(os.tmpdir(), "pdp-production-safety-"));

const storySpec = {
  human_gates: { story_approval: { status: "Approved" } },
  product_images: Array.from({ length: 7 }, (_, index) => ({ id: `IMAGE-${String(index + 1).padStart(2, "0")}`, sequence: index + 1, stage: `stage-${index + 1}` })),
  aplus_modules: Array.from({ length: 7 }, (_, index) => ({ id: `APLUS-M${String(index + 1).padStart(2, "0")}`, sequence: index + 1, units: [{ id: `APLUS-U${String(index + 1).padStart(2, "0")}`, stage: `stage-${index + 1}` }] })),
};
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
  placeholder_provenance: "PASS",
  external_reference: "PASS",
  publish_blocked: "PASS",
  publish_pass: "PASS",
  fixture_scan: "PASS",
}, null, 2));
