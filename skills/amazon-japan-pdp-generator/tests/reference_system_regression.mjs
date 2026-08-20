#!/usr/bin/env node
import assert from "node:assert/strict";
import fs from "node:fs/promises";
import os from "node:os";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { buildReferenceRendererSnapshots } from "../scripts/reference_renderers.mjs";
import { REQUIRED_REFERENCE_RENDERERS, RENDERER_REGISTRY, assertRendererCoverage } from "../scripts/renderer_registry.mjs";
import { loadReferenceLibrary, matchReferences } from "../scripts/reference_matcher.mjs";
import { readProjectState } from "../scripts/phase_system.mjs";

const root = path.dirname(path.dirname(fileURLToPath(import.meta.url)));
const expected = JSON.parse(await fs.readFile(path.join(root, "tests", "snapshots", "reference_renderer_snapshot.json"), "utf8"));
const actual = await buildReferenceRendererSnapshots(root);
assert.equal(REQUIRED_REFERENCE_RENDERERS.length, 5);
assert.equal(actual.length, 10);
assert.deepEqual(actual, expected, "Renderer snapshot drift detected; do not auto-accept.");
assertRendererCoverage(REQUIRED_REFERENCE_RENDERERS);
for (const templateId of REQUIRED_REFERENCE_RENDERERS) {
  const capability = RENDERER_REGISTRY[templateId];
  assert.equal(capability.renderer_available, true);
  assert.equal(capability.deterministic, true);
  assert.ok(capability.desktop_layout && capability.mobile_layout && capability.safe_fallback);
  assert.ok(capability.slots.title && capability.slots.body && capability.slots.image && capability.slots.claim);
}

const syntheticS30Brief = {
  reference_profile: {
    category: ["robot vacuum", "floor-cleaning appliance", "home cleaning"],
    product_complexity: ["high", "system product"],
    primary_usp: ["compact body", "roller floor washing", "automated station closeout"],
    consumer_tension: ["limited space", "cleaning performance", "post-cleaning maintenance"],
    product_type: ["robot vacuum", "floor-washing robot", "station ecosystem"],
    story_requirement: ["performance-led", "technology-led", "problem-solution", "scenario-led"],
    technical_complexity: ["high", "mechanism explanation required"],
    target_audience: ["Japanese compact-home households", "replacement buyers", "pet households"],
  },
};
const references = await loadReferenceLibrary(path.join(root, "reference-library"));
const selection = matchReferences(syntheticS30Brief, references);
assert.equal(selection.status, "complete");
assert.deepEqual(selection.structural_references.map((item) => item.brand), ["Eufy", "ECOVACS"]);
assert.ok(selection.inspiration_only_references.some((item) => item.brand === "Levoit"));
assert.ok(!selection.structural_references.some((item) => item.brand === "Levoit"));

const temp = await fs.mkdtemp(path.join(os.tmpdir(), "pdp-legacy-state-"));
await fs.writeFile(path.join(temp, "PROJECT_STATE.json"), JSON.stringify({ schema_version: "1.0", know_status: "complete", plan_status: "pending" }), "utf8");
const legacyState = await readProjectState(temp);
assert.equal(legacyState.reference_mode, "OFF");
assert.equal(legacyState.reference_mode_source, "legacy_fallback");

console.log(JSON.stringify({ status: "PASS", renderer_snapshot_cases: actual.length, structural_references: selection.structural_references.map((item) => item.brand), levoit_structural_filter: "PASS", legacy_reference_fallback: "PASS" }, null, 2));
