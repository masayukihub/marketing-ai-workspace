import assert from "node:assert/strict";
import fs from "node:fs/promises";
import os from "node:os";
import path from "node:path";
import { createRequire } from "node:module";
import { test } from "node:test";
import { CREATIVE_DIMENSIONS, evaluateCreativeReview } from "../scripts/creative_review.mjs";
import { finalAudit, produceFinalVisuals, evaluatePublishGate } from "../scripts/visual_pipeline.mjs";
import { brandFitAssessment, templateFeelingAssessment, visualRhythmScore } from "../scripts/visual_quality_system.mjs";
import { buildArtDirectionSpec } from "../scripts/art_direction_system.mjs";
import { selectCompositionSvg } from "../scripts/render_v4.mjs";

const sharp = createRequire(import.meta.url)("sharp");
const output = { id: "SYNTHETIC-01", path: "synthetic.jpg", sha256: "a".repeat(64) };
function reviewFor(target = output) {
  // Test-only observations exercise the record contract, not aesthetic quality.
  return {
    asset_id: target.id, output_ref: target.path, output_sha256: target.sha256,
    reviewer: { kind: "model", name: "synthetic test reviewer" },
    inspected_at: "2026-09-07T00:00:00Z", viewing_context: "Synthetic test views",
    five_second_takeaway: "A synthetic rectangular object",
    findings: Object.fromEntries(CREATIVE_DIMENSIONS.map((key) => [key, {
      verdict: "PASS", observation: "Synthetic observation for " + key,
    }])),
  };
}

test("rendering toggles cannot manufacture aesthetic scores", () => {
  for (const mode of ["ON", "OFF"]) {
    assert.equal(brandFitAssessment(mode).score, null);
    assert.equal(brandFitAssessment(mode).risk, "NOT_ASSESSED");
    assert.equal(templateFeelingAssessment(mode).overall_risk, "NOT_ASSESSED");
  }
  const spec = {
    meta: { spec_sha256: "synthetic" }, product: { name: "Generic Device", category: "generic", sku: "TEST" },
    story_sequence_lock: { fingerprint: "synthetic" }, claims: [], reference_selection: {},
    product_images: [{ id: "IMAGE-01", sequence: 1, stage: "understand", role: "Identity",
      template_id: "P-MAIN-OFFICIAL", headline: "", claim_ids: [], status: "Need Verification" }],
    aplus_modules: [],
  };
  const art = buildArtDirectionSpec(spec);
  assert.equal(art.quality.score.overall, null);
  assert.equal(art.quality.current_baseline_score, null);
  assert.equal(art.quality.jp_lifestyle_fit.score, null);
  assert.equal(art.quality.semantic_relevance.status, "PASS");
});

test("low-density runs are not counted as high-density overload", () => {
  const manifest = { gallery: ["low", "low", "low", "low", "high", "high"].map((density, i) => ({
    id: String(i), information_density: density, visual_role: "EXPLAIN",
  })), aplus: [] };
  assert.equal(visualRhythmScore(manifest).evidence.high_density_longest_run, 2);
  manifest.gallery[4].information_density = "low";
  manifest.gallery[5].information_density = "low";
  assert.equal(visualRhythmScore(manifest).evidence.high_density_longest_run, 0);
});

test("registered reference composition takes priority over quality presets", () => {
  assert.equal(selectCompositionSvg("<svg id='reference'/>", "<svg id='preset'/>", "fallback"), "<svg id='reference'/>");
  assert.equal(selectCompositionSvg(null, "preset", "fallback"), "preset");
  assert.equal(selectCompositionSvg(null, null, "fallback"), "fallback");
  assert.equal(selectCompositionSvg("reference", "preset", () => { throw new Error("Fallback must not run"); }), "reference");
});

test("metadata checks cannot claim observed five-second understanding", () => {
  const result = finalAudit({ headline: "サンプル", layoutId: "A", productBodyAiGenerated: false });
  assert.equal(result.status, "Pass");
  assert.equal(result.scope, "CONTENT_AND_LAYOUT_METADATA_ONLY");
  assert.equal(result.fiveSecondMessage, null);
});

test("review is bound to asset, path and exported bytes", () => {
  const review = reviewFor();
  assert.equal(evaluateCreativeReview(review, output).status, "Pass");
  for (const [key, value] of [["id", "OTHER"], ["path", "other.jpg"], ["sha256", "b".repeat(64)]]) {
    const result = evaluateCreativeReview(review, { ...output, [key]: value });
    assert.equal(result.status, "Needs Visual Review");
    assert.equal(result.stale, true);
  }
});

test("missing observations, skipped core checks and concrete defects cannot pass", () => {
  assert.equal(evaluateCreativeReview(null, output).status, "Needs Visual Review");
  const review = reviewFor();
  review.findings.realism.observation = "";
  assert.equal(evaluateCreativeReview(review, output).status, "Needs Visual Review");
  review.findings.realism = { verdict: "REVISE", observation: "Shadow falls opposite the scene light." };
  assert.equal(evaluateCreativeReview(review, output).status, "Reject");
  const skipped = reviewFor();
  skipped.findings.product_fidelity.verdict = "NOT_APPLICABLE";
  assert.equal(evaluateCreativeReview(skipped, output).status, "Needs Visual Review");
});

test("legacy render stays pending, accepts recorded review, and invalidates it after source change", async () => {
  const dir = await fs.mkdtemp(path.join(os.tmpdir(), "creative-quality-"));
  try {
    // A solid rectangle is intentionally synthetic, not an official product fixture.
    await sharp({ create: { width: 80, height: 120, channels: 3, background: "#345678" } }).png().toFile(path.join(dir, "source.png"));
    const data = {
      product: { mainImage: "source.png", mainImageOrigin: "User Provided Official", mainImageType: "Official PNG", productBodyAiGenerated: false },
      meta: { externalPublishReady: true, moduleAvailability: "Confirmed", japanLocalizationStatus: "Natural", visualConsistencyStatus: "Pass" },
      claims: [], images: [{ id: "IMAGE-01", headline: "", status: "Approved" }],
      aplusModules: [{ id: "APLUS-M01", templateType: "SB-A01", purpose: "Synthetic", moduleAvailability: "Confirmed", units: [
        { id: "UNIT-01", headline: "", copy: "", status: "Approved" },
      ] }],
    };
    const first = await produceFinalVisuals(data, dir);
    for (const record of [...data.images, ...data.aplusModules]) {
      assert.equal(record.round2Qa.status, "Pass");
      assert.equal(record.designQaStatus, "Needs Visual Review");
      assert.equal(record.visualProductionStatus, "Need Verification");
      record.creativeReview = reviewFor({ id: record.id, path: record.finalPath, sha256: record.outputSha256 });
    }
    assert.ok(!first.productImages[0].operations.includes("visual review"));
    await produceFinalVisuals(data, dir);
    assert.equal(evaluatePublishGate(data).gate, "Ready");
    // Human publication permission remains independent from recorded model observations.
    data.meta.externalPublishReady = false;
    assert.equal(evaluatePublishGate(data).gate, "Blocked");
    data.meta.externalPublishReady = true;
    await sharp({ create: { width: 80, height: 120, channels: 3, background: "#cc9933" } }).png().toFile(path.join(dir, "source.png"));
    await produceFinalVisuals(data, dir);
    for (const record of [...data.images, ...data.aplusModules]) {
      assert.equal(record.creativeReviewResult.stale, true);
      assert.equal(record.visualProductionStatus, "Need Verification");
    }
    assert.equal(evaluatePublishGate(data).gate, "Blocked");
  } finally {
    await fs.rm(dir, { recursive: true, force: true });
  }
});
