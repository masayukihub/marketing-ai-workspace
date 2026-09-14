import fs from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { readSpec, readTemplateLibrary, refreshSpec, writeSpecBundle, parseArgs } from "./spec_system.mjs";
import { renderFromSpec } from "./render_v4.mjs";
import { readProjectState, syncFinalExports, writeProjectState } from "./phase_system.mjs";

const args = parseArgs(process.argv);
if (!args.spec || !args.output || !args.qa) throw new Error("Usage: node scripts/attach_browser_qa.mjs --spec <PRODUCT_PAGE_SPEC.json> --output <dir> --qa <browser-qa.json>");

const skillDir = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const spec = await readSpec(path.resolve(args.spec));
const qa = JSON.parse(await fs.readFile(path.resolve(args.qa), "utf8"));
if (qa.status !== "Pass") throw new Error(`Browser QA must Pass before attachment; received ${qa.status}`);
if (qa.spec_sha256 !== spec.meta.spec_sha256) throw new Error("Browser QA evidence does not match the current Spec hash");

spec.quality_evidence = spec.quality_evidence || {};
spec.quality_evidence.mobile = {
  status: "Pass",
  viewport: qa.pages?.mobile?.viewport || "390x844",
  root_width: qa.pages?.mobile?.root_width,
  document_width: qa.pages?.mobile?.document_width,
  overflow_nodes: qa.pages?.mobile?.overflow_nodes?.length || 0,
  evidence_file: "qa/browser-qa.json",
  checked_at: qa.checked_at,
  validated_spec_sha256: qa.spec_sha256,
};
const library = await readTemplateLibrary(skillDir);
refreshSpec(spec, library);
await writeSpecBundle(spec, path.resolve(args.output));
const render = await renderFromSpec(spec, path.resolve(args.output));
if (render.status === "VISUAL_CAPABILITY_MISMATCH") {
  const state = await readProjectState(path.resolve(args.output));
  state.qa_status = "blocked_visual_capability";
  state.publish_gate = "blocked";
  await writeProjectState(path.resolve(args.output), state);
  console.error(JSON.stringify({ ...render, workbooks: 0, project_state_qa: state.qa_status }, null, 2));
  process.exit(1);
}
const { renderWorkbooksFromSpec } = await import("./workbook_renderer.mjs");
const workbooks = await renderWorkbooksFromSpec(spec, path.resolve(args.output));
const exports = await syncFinalExports(spec, path.resolve(args.output));
const state = await readProjectState(path.resolve(args.output));
state.qa_status = "pass";
state.publish_gate = spec.publish_gate.status.toLowerCase();
await writeProjectState(path.resolve(args.output), state);
console.log(JSON.stringify({ mobile_gate: spec.publish_gate.sections.mobile.status, publish_gate: spec.publish_gate.status, spec_sha256: spec.meta.spec_sha256, render: render.status, workbooks: workbooks.length, export_workbooks: exports.workbook_count, project_state_qa: state.qa_status }, null, 2));
