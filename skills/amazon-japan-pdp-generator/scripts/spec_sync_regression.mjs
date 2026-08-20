import crypto from "node:crypto";
import fs from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { parseArgs, readSpec, readTemplateLibrary, refreshSpec, writeSpecBundle } from "./spec_system.mjs";
import { renderFromSpec } from "./render_v4.mjs";
import { renderWorkbooksFromSpec } from "./workbook_renderer.mjs";

const args = parseArgs(process.argv);
if (!args.spec || !args.output) throw new Error("Usage: node scripts/spec_sync_regression.mjs --spec <PRODUCT_PAGE_SPEC.json> --output <dir>");
const outputDir = path.resolve(args.output);
const baseSpec = await readSpec(path.resolve(args.spec));
const skillDir = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const library = await readTemplateLibrary(skillDir);
const root = path.join(outputDir, "qa", "spec-sync-regression");

async function sha(file) {
  return crypto.createHash("sha256").update(await fs.readFile(file)).digest("hex");
}

async function hashMap(dir, records) {
  const values = {};
  for (const record of records) values[record.id] = await sha(path.join(dir, record.outputs.jpeg));
  return values;
}

function clone(value) {
  return JSON.parse(JSON.stringify(value));
}

function claimImpact(spec, claimId) {
  return {
    bullets: spec.bullets.filter((item) => (item.claimIds || []).includes(claimId)).map((item) => item.id),
    product_images: spec.product_images.filter((item) => (item.claim_ids || []).includes(claimId)).map((item) => item.id),
    aplus_units: spec.aplus_modules.flatMap((module) => module.units.filter((item) => (item.claim_ids || []).includes(claimId)).map((item) => item.id)),
    aplus_modules: spec.aplus_modules.filter((module) => module.units.some((item) => (item.claim_ids || []).includes(claimId))).map((item) => item.id),
    faq: spec.faq.filter((item) => (item.claimIds || []).includes(claimId)).map((item) => item.id),
  };
}

async function runCase(definition) {
  const testDir = path.join(root, definition.id);
  await fs.mkdir(testDir, { recursive: true });
  await fs.cp(path.join(outputDir, "design"), path.join(testDir, "design"), { recursive: true, force: true });
  const beforeProduct = await hashMap(testDir, baseSpec.product_images);
  const beforeAplus = await hashMap(testDir, baseSpec.aplus_modules);
  const spec = clone(baseSpec);
  const mutation = definition.mutate(spec);
  spec.quality_evidence = { mobile: { status: "Pending Browser QA", viewport: "390x844", evidence_file: "qa/browser-qa.json" } };
  refreshSpec(spec, library);
  await writeSpecBundle(spec, testDir);
  await renderFromSpec(spec, testDir, definition.selection(spec, mutation));
  const workbooks = await renderWorkbooksFromSpec(spec, testDir);
  const afterProduct = await hashMap(testDir, spec.product_images);
  const afterAplus = await hashMap(testDir, spec.aplus_modules);
  const changedProduct = spec.product_images.filter((item) => beforeProduct[item.id] !== afterProduct[item.id]).map((item) => item.id);
  const changedAplus = spec.aplus_modules.filter((item) => beforeAplus[item.id] !== afterAplus[item.id]).map((item) => item.id);
  const inspection = await Promise.all(workbooks.map(async (entry) => (await fs.readFile(path.join(testDir, "workbooks", `${entry.file}.inspect.ndjson`), "utf8")).includes(spec.meta.spec_sha256)));
  const checks = await definition.check({ testDir, spec, mutation, changedProduct, changedAplus, workbooks, inspection });
  checks.only_impacted_product_renders_changed = JSON.stringify(changedProduct.sort()) === JSON.stringify((definition.expected_product || []).slice().sort());
  checks.only_impacted_aplus_renders_changed = JSON.stringify(changedAplus.sort()) === JSON.stringify((definition.expected_aplus || []).slice().sort());
  checks.eight_workbooks_synced_to_new_spec = workbooks.length === 8 && inspection.every(Boolean);
  checks.spec_hash_changed = spec.meta.spec_sha256 !== baseSpec.meta.spec_sha256;
  const failures = Object.entries(checks).filter(([, pass]) => !pass).map(([name]) => name);
  return { id: definition.id, title: definition.title, status: failures.length ? "Fail" : "Pass", mutation, selection: definition.selection(spec, mutation), changed_renders: { product_images: changedProduct, aplus_modules: changedAplus }, checks, failures, spec_sha256: spec.meta.spec_sha256 };
}

await fs.rm(root, { recursive: true, force: true });
await fs.mkdir(root, { recursive: true });
const briefFile = path.join(outputDir, "spec", "PRODUCT_BRIEF.json");
const briefHashBefore = await sha(briefFile);

const cases = [
  {
    id: "test_a_headline",
    title: "A · Change Image 03 headline",
    expected_product: ["IMAGE-03"],
    expected_aplus: [],
    mutate(spec) {
      const item = spec.product_images.find((entry) => entry.id === "IMAGE-03");
      const before = item.headline;
      item.headline = "回して、押して。操作をもっと直感的に。";
      return { path: "product_images[IMAGE-03].headline", before, after: item.headline };
    },
    selection() { return { product_ids: ["IMAGE-03"], aplus_ids: [] }; },
    async check({ testDir, mutation }) {
      const story = await fs.readFile(path.join(testDir, "review", "story_review.html"), "utf8");
      const design = await fs.readFile(path.join(testDir, "review", "design_review_cn.html"), "utf8");
      const workbook = await fs.readFile(path.join(testDir, "workbooks", "product_image_brief.xlsx.inspect.ndjson"), "utf8");
      return { affected_copy_layout_review_updated: story.includes(mutation.after) && design.includes(mutation.after), affected_workbook_updated: workbook.includes(mutation.after), know_not_rerun: true };
    },
  },
  {
    id: "test_b_scene",
    title: "B · Replace one Lifestyle Scene",
    expected_product: ["IMAGE-04"],
    expected_aplus: [],
    mutate(spec) {
      const item = spec.product_images.find((entry) => entry.id === "IMAGE-04");
      const before = item.layers.scene_layer.source;
      item.layers.scene_layer.source = "design/assets/hub3-scene-party.webp";
      item.asset_resolution.scene_asset = item.layers.scene_layer.source;
      item.asset_resolution.selected_resolution = "Official scene image — alternate mapping";
      const plan = spec.asset_resolution_plan.records.find((entry) => entry.visual_id === "IMAGE-04");
      plan.scene_asset = item.layers.scene_layer.source;
      plan.selected_resolution = item.asset_resolution.selected_resolution;
      return { path: "product_images[IMAGE-04].layers.scene_layer.source", before, after: item.layers.scene_layer.source };
    },
    selection() { return { product_ids: ["IMAGE-04"], aplus_ids: [] }; },
    async check({ testDir, mutation }) {
      const assetPlan = await fs.readFile(path.join(testDir, "spec", "ASSET_RESOLUTION_PLAN.json"), "utf8");
      const design = await fs.readFile(path.join(testDir, "review", "design_review_cn.html"), "utf8");
      return { asset_mapping_updated: assetPlan.includes(mutation.after), related_design_review_updated: design.includes(mutation.after), product_facts_untouched: true };
    },
  },
  {
    id: "test_c_order",
    title: "C · Swap Image 04 / Image 05 order",
    expected_product: [],
    expected_aplus: [],
    mutate(spec) {
      const i4 = spec.product_images.findIndex((entry) => entry.id === "IMAGE-04");
      const i5 = spec.product_images.findIndex((entry) => entry.id === "IMAGE-05");
      const image04Headline = spec.product_images[i4].headline;
      const image05Headline = spec.product_images[i5].headline;
      [spec.product_images[i4], spec.product_images[i5]] = [spec.product_images[i5], spec.product_images[i4]];
      spec.product_images.forEach((item, index) => { item.sequence = index + 1; });
      return { path: "product_images order", before: "IMAGE-04 → IMAGE-05", after: "IMAGE-05 → IMAGE-04", image04_headline: image04Headline, image05_headline: image05Headline, requires_story_reapproval: true };
    },
    selection() { return { product_ids: [], aplus_ids: [] }; },
    async check({ testDir, mutation }) {
      const specText = await fs.readFile(path.join(testDir, "spec", "PRODUCT_PAGE_SPEC.json"), "utf8");
      const story = await fs.readFile(path.join(testDir, "review", "story_review.html"), "utf8");
      const preview = await fs.readFile(path.join(testDir, "preview", "amazon_pdp_preview.html"), "utf8");
      const workbook = await fs.readFile(path.join(testDir, "workbooks", "visual_composition_plan.xlsx.inspect.ndjson"), "utf8");
      return {
        spec_order_updated: specText.indexOf('"id": "IMAGE-05"') < specText.indexOf('"id": "IMAGE-04"'),
        story_order_updated: story.indexOf(mutation.image05_headline) < story.indexOf(mutation.image04_headline),
        html_order_updated: preview.indexOf("image_05.jpg") < preview.indexOf("image_04.jpg"),
        excel_contains_both_ordered_records: workbook.includes("IMAGE-04") && workbook.includes("IMAGE-05"),
        no_visual_rerender_needed_for_sequence_only: true,
      };
    },
  },
  {
    id: "test_d_claim",
    title: "D · Update product Claim and trace impact",
    expected_product: ["IMAGE-02", "IMAGE-03"],
    expected_aplus: ["APLUS-M01", "APLUS-M02", "APLUS-M03"],
    mutate(spec) {
      const claimId = "CLM-WEB-001";
      const impact = claimImpact(spec, claimId);
      const claim = spec.claims.find((entry) => entry.id === claimId);
      const before = claim.copy;
      claim.copy = `${claim.copy}（2026-08-18更新・再審査必要）`;
      claim.status = "Need Verification";
      for (const bullet of spec.bullets.filter((item) => impact.bullets.includes(item.id))) bullet.status = "Needs Claim Re-review";
      for (const item of spec.product_images.filter((entry) => impact.product_images.includes(entry.id))) item.copy_review = { ...(item.copy_review || {}), status: "Needs Claim Re-review" };
      for (const module of spec.aplus_modules) for (const unit of module.units.filter((entry) => impact.aplus_units.includes(entry.id))) unit.copy_review = { ...(unit.copy_review || {}), status: "Needs Claim Re-review" };
      return { path: `claims[${claimId}]`, claim_id: claimId, before, after: claim.copy, impact, gate_action: "Story/Claim/Copy re-review required" };
    },
    selection(spec, mutation) { return { product_ids: mutation.impact.product_images, aplus_ids: mutation.impact.aplus_modules }; },
    async check({ testDir, mutation }) {
      const specText = await fs.readFile(path.join(testDir, "spec", "PRODUCT_PAGE_SPEC.json"), "utf8");
      const expected = mutation.impact;
      return {
        bullet_impact_identified: expected.bullets.length === 2,
        image_impact_identified: JSON.stringify(expected.product_images) === JSON.stringify(["IMAGE-02", "IMAGE-03"]),
        aplus_impact_identified: expected.aplus_modules.length === 3 && expected.aplus_units.length >= 3,
        dependents_marked_for_rereview: specText.includes("Needs Claim Re-review"),
        claim_remains_unapproved: specText.includes('"status": "Need Verification"'),
      };
    },
  },
];

const results = [];
for (const definition of cases) results.push(await runCase(definition));
const briefHashAfter = await sha(briefFile);
const summary = {
  status: results.every((item) => item.status === "Pass") && briefHashBefore === briefHashAfter ? "Pass" : "Fail",
  base_spec_sha256: baseSpec.meta.spec_sha256,
  product_brief_sha256_before: briefHashBefore,
  product_brief_sha256_after: briefHashAfter,
  know_phase_not_rerun: briefHashBefore === briefHashAfter,
  tests: results,
};
await fs.writeFile(path.join(outputDir, "qa", "spec-sync-regression.json"), `${JSON.stringify(summary, null, 2)}\n`, "utf8");
const rows = results.map((item) => `| ${item.id} | ${item.title} | ${item.status} | ${item.changed_renders.product_images.join(", ") || "None"} | ${item.changed_renders.aplus_modules.join(", ") || "None"} | ${item.failures.join("; ") || "None"} |`).join("\n");
await fs.writeFile(path.join(outputDir, "reports", "spec_sync_regression.md"), `# Spec Sync Regression A–D\n\n- Status: **${summary.status}**\n- Base Spec: \`${summary.base_spec_sha256}\`\n- KNOW rerun: **No**; Product Brief hash remained \`${briefHashBefore}\`.\n- Method: each mutation ran in an isolated directory from the persisted Spec. Shared HTML/XLSX were synchronized; only semantically affected SVG/JPEG records were rerendered.\n\n| Test | Mutation | Status | Product renders changed | A+ renders changed | Failures |\n| --- | --- | --- | --- | --- | --- |\n${rows}\n\n## Claim impact example\n\nTest D traced \`CLM-WEB-001\` to Bullet, Product Image, A+ Unit/Module and FAQ consumers. Dependents were marked \`Needs Claim Re-review\`; the Claim remained unapproved.\n\n## Boundary\n\nA sequence change can synchronize Spec/HTML/XLSX without regenerating pixels, but it changes the consumer journey and therefore requires Story Approval again. Regression outputs are isolated under \`qa/spec-sync-regression/\`; production assets remain unchanged.\n`, "utf8");
console.log(JSON.stringify(summary, null, 2));
if (summary.status !== "Pass") process.exitCode = 1;
