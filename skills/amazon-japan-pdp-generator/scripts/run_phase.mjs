#!/usr/bin/env node
import fs from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { validateData } from "./pdp_lib.mjs";
import {
  buildProductBrief,
  buildProductPageSpec,
  buildSellingPointMatrix,
  parseArgs,
  readSpec,
  readTemplateLibrary,
  refreshSpec,
  validateSpec,
  writePlanningBundle,
  writeSpecBundle,
} from "./spec_system.mjs";
import { renderFromSpec, writeLayoutReview, writeStoryReview } from "./render_v4.mjs";
import { writeReferenceSelection } from "./reference_matcher.mjs";
import { adaptReferencePlan, referenceTraceMarkdown } from "./reference_decision_adapter.mjs";
import {
  PHASES,
  approved,
  blockFinalOutputs,
  nextPhase,
  readProjectState,
  syncFinalExports,
  writeProductUnderstanding,
  writeProjectState,
} from "./phase_system.mjs";
import { assertStorySequenceIntegrity, assertStorySequenceStateIntegrity, lockStorySequence } from "./story_sequence_lock.mjs";

const args = parseArgs(process.argv);
if (!args.output) {
  console.error("Usage: node scripts/run_phase.mjs --output <dir> [--input <input.json>] [--phase know|reference|plan|design|produce] [--reference-mode on|off] [--resume] [--from-spec <PRODUCT_PAGE_SPEC.json>] [--rerender] [--gate-mode pending|internal-test] [--force]");
  process.exit(2);
}

const outputDir = path.resolve(args.output);
const inputFile = args.input ? path.resolve(args.input) : "";
const skillDir = path.dirname(path.dirname(fileURLToPath(import.meta.url)));
const state = await readProjectState(outputDir, inputFile);
if (inputFile) state.source_input = inputFile;
const explicitReferenceMode = args["reference-mode"] || args.reference || process.env.REFERENCE;
if (explicitReferenceMode !== undefined) {
  const normalized = String(explicitReferenceMode).trim().toUpperCase();
  if (!["ON", "OFF"].includes(normalized)) throw new Error(`Invalid Reference mode: ${explicitReferenceMode}. Expected ON or OFF.`);
  state.reference_mode = normalized;
  state.reference_mode_source = args["reference-mode"] || args.reference ? "cli" : "environment";
}
const referenceMode = state.reference_mode === "OFF" ? "OFF" : "ON";
let phase = args.rerender ? "produce" : String(args.phase || "").toLowerCase();
if (args.resume) {
  const resumable = nextPhase(state);
  if (!resumable) {
    const waiting_for = state.plan_status === "complete" && !approved(state.story_gate)
      ? "story_approval"
      : state.design_status === "complete" && !approved(state.layout_gate)
        ? "layout_approval"
        : state.produce_status === "complete"
          ? "none_complete"
          : "manual_review";
    console.log(JSON.stringify({ status: "waiting", waiting_for, project_state: "PROJECT_STATE.json" }, null, 2));
    process.exit(0);
  }
  phase = resumable;
}
if (!PHASES.includes(phase)) {
  console.error(`Invalid or missing phase: ${phase || "<none>"}. Expected ${PHASES.join("|")}.`);
  process.exit(2);
}

const forceWarnings = [];
function htmlEscape(value) {
  return String(value ?? "").replaceAll("&", "&amp;").replaceAll("<", "&lt;").replaceAll(">", "&gt;").replaceAll('"', "&quot;");
}

function referenceDecisionReview(selection, traces, patterns) {
  const candidates = (selection.top_references || []).map((item) => `<tr><td>${htmlEscape(item.brand)} ${htmlEscape(item.asin)}</td><td>${item.score}</td><td>${htmlEscape(item.structural_decision)}</td><td>${htmlEscape((item.allowed_influence || []).join(" / "))}</td></tr>`).join("");
  const decisions = traces.map((item) => `<tr><td>${htmlEscape(item.visual_id)}</td><td>${htmlEscape(item.story_role)}</td><td>${htmlEscape(item.selected_reference_pattern)}</td><td>${htmlEscape(item.primitive)}</td><td>${htmlEscape(item.final_plan_decision)}</td></tr>`).join("");
  return `<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><link rel="icon" href="data:,"><title>Reference Selection & Decision Trace</title><style>*{box-sizing:border-box}body{margin:0;background:#f4f7f6;color:#17212b;font-family:-apple-system,BlinkMacSystemFont,"PingFang SC",sans-serif}.wrap{max-width:1200px;margin:auto;padding:28px}.card{background:#fff;border:1px solid #dfe6e5;border-radius:16px;padding:22px;margin-bottom:18px}table{width:100%;border-collapse:collapse;font-size:14px}th,td{padding:10px;border-bottom:1px solid #e2e8e7;text-align:left;vertical-align:top}.pass{color:#087a66;font-weight:800}.muted{color:#607078}@media(max-width:700px){.wrap{padding:12px}table{font-size:12px;display:block;overflow:auto}}</style></head><body><main class="wrap"><section class="card"><h1>REFERENCE · Selection & Decision Trace</h1><p class="muted">Reference is a decision aid, not competitor copy, imagery, trade dress or complete layout.</p><p>Story <code>${htmlEscape(patterns.story.record.pattern_id)}</code> · Gallery <code>${htmlEscape(patterns.gallery.record.sequence_id)}</code> · A+ <code>${htmlEscape(patterns.aplus.record.sequence_id)}</code></p></section><section class="card"><h2>Matcher Selection</h2><table><thead><tr><th>Reference</th><th>Score</th><th>Structural Decision</th><th>Allowed Influence</th></tr></thead><tbody>${candidates}</tbody></table></section><section class="card"><h2>14 PLAN Decisions</h2><table><thead><tr><th>Visual</th><th>Story Role</th><th>Pattern</th><th>Primitive</th><th>Gate Result</th></tr></thead><tbody>${decisions}</tbody></table><p class="pass">Accepted ${traces.filter((item) => item.final_plan_decision === "ACCEPTED").length} / ${traces.length}</p></section></main></body></html>`;
}

function requireGate(name, value) {
  if (approved(value)) return;
  const message = `${name} is ${value || "pending"}; ${phase.toUpperCase()} is blocked.`;
  if (!args.force) throw new Error(message);
  const warning = `FORCE OVERRIDE: ${message} Output is review-only and cannot be treated as publish-approved.`;
  forceWarnings.push(warning);
  console.error(warning);
}

async function loadInput() {
  const source = inputFile || state.source_input;
  if (!source) throw new Error(`${phase.toUpperCase()} requires --input or PROJECT_STATE.source_input.`);
  const input = JSON.parse(await fs.readFile(source, "utf8"));
  const check = validateData(input);
  if (check.errors.length) throw new Error(`Input Structural Gate blocked: ${check.errors.join("; ")}`);
  return { input, source, warnings: check.warnings };
}

async function loadPhaseSpec(library) {
  const specFile = args["from-spec"] ? path.resolve(args["from-spec"]) : path.join(outputDir, "spec", "PRODUCT_PAGE_SPEC.json");
  const spec = refreshSpec(await readSpec(specFile), library);
  const errors = validateSpec(spec, library);
  if (errors.length) throw new Error(`Spec Structural Gate blocked: ${errors.join("; ")}`);
  return spec;
}

try {
  await fs.mkdir(outputDir, { recursive: true });
  const library = await readTemplateLibrary(skillDir);
  let result = {};

  if (phase === "know") {
    const { input, source, warnings } = await loadInput();
    const brief = buildProductBrief(input, source);
    await fs.mkdir(path.join(outputDir, "spec"), { recursive: true });
    await fs.writeFile(path.join(outputDir, "spec", "PRODUCT_BRIEF.json"), `${JSON.stringify(brief, null, 2)}\n`, "utf8");
    await writeProductUnderstanding(brief, outputDir);
    state.current_phase = "know";
    state.know_status = "complete";
    state.reference_status = referenceMode === "ON" ? "pending" : "disabled";
    state.plan_status = "pending";
    state.story_gate = "pending";
    state.story_sequence_locked = false;
    state.story_sequence_fingerprint = "";
    state.design_status = "pending";
    state.layout_gate = "pending";
    state.produce_status = "pending";
    await blockFinalOutputs(outputDir, "KNOW invalidated downstream approval");
    result = { phase, status: "complete", reference_mode: referenceMode, artifact: "spec/PRODUCT_BRIEF.json", review: "review/product_understanding_cn.html", warnings };
  }

  if (phase === "reference") {
    if (state.know_status !== "complete" && !args.force) throw new Error("REFERENCE requires completed KNOW. Run --phase know first.");
    let brief;
    try {
      brief = JSON.parse(await fs.readFile(path.join(outputDir, "spec", "PRODUCT_BRIEF.json"), "utf8"));
    } catch {
      throw new Error("REFERENCE requires spec/PRODUCT_BRIEF.json from KNOW.");
    }
    if (referenceMode === "OFF") {
      const targetDir = path.join(outputDir, "reference");
      await fs.mkdir(targetDir, { recursive: true });
      const disabled = { schema_version: "2.0", artifact: "REFERENCE_SELECTION", status: "disabled", mode: "OFF", is_human_gate: false, top_references: [], structural_references: [], inspiration_only_references: [], note: "Reference Matcher and Decision Adapter were intentionally disabled for regression or troubleshooting." };
      await fs.writeFile(path.join(targetDir, "REFERENCE_SELECTION.json"), `${JSON.stringify(disabled, null, 2)}\n`, "utf8");
      await fs.writeFile(path.join(targetDir, "REFERENCE_SELECTION.md"), "# REFERENCE_SELECTION\n\nStatus: **disabled** (`REFERENCE=OFF`). Matcher and Decision Adapter were not called.\n", "utf8");
      state.current_phase = "reference";
      state.reference_status = "disabled";
      result = { phase, status: "disabled", reference_mode: "OFF", is_human_gate: false, artifact: "reference/REFERENCE_SELECTION.md", top_references: [] };
    } else {
      const selection = await writeReferenceSelection(brief, outputDir, path.join(skillDir, "reference-library"), "spec/PRODUCT_BRIEF.json");
      state.current_phase = "reference";
      state.reference_status = selection.status === "complete" ? "complete" : "blocked";
      result = {
        phase,
        status: selection.status,
        reference_mode: "ON",
        is_human_gate: false,
        artifact: "reference/REFERENCE_SELECTION.md",
        top_references: selection.top_references.map(({ rank, asin, brand, score, structural_decision }) => ({ rank, asin, brand, score, structural_decision })),
        missing_fields: selection.missing_fields,
      };
    }
    state.plan_status = "pending";
    state.story_gate = "pending";
    state.story_sequence_locked = false;
    state.story_sequence_fingerprint = "";
    state.design_status = "pending";
    state.layout_gate = "pending";
    state.produce_status = "pending";
    await blockFinalOutputs(outputDir, "REFERENCE invalidated downstream approval");
  }

  if (phase === "plan") {
    if (approved(state.story_gate) || state.story_sequence_locked) {
      throw new Error("Story Sequence Lock BLOCKED PLAN. Reset Story Gate to pending and return to Story Review before rerunning PLAN or Reference Adapter.");
    }
    if (state.know_status !== "complete" && !args.force) throw new Error("PLAN requires completed KNOW. Run --phase know first.");
    if (referenceMode === "ON" && state.reference_status !== "complete") {
      const message = "PLAN requires completed REFERENCE. Run --phase reference first.";
      if (!args.force) throw new Error(message);
      const warning = `FORCE OVERRIDE: ${message} Reference strategy is missing; output is review-only.`;
      forceWarnings.push(warning);
      console.error(warning);
    }
    const { input, source, warnings } = await loadInput();
    let brief;
    let referenceSelection;
    try {
      brief = JSON.parse(await fs.readFile(path.join(outputDir, "spec", "PRODUCT_BRIEF.json"), "utf8"));
    } catch {
      if (!args.force) throw new Error("PLAN requires spec/PRODUCT_BRIEF.json from KNOW.");
      brief = buildProductBrief(input, source);
    }
    if (referenceMode === "ON") {
      try {
        referenceSelection = JSON.parse(await fs.readFile(path.join(outputDir, "reference", "REFERENCE_SELECTION.json"), "utf8"));
      } catch {
        if (!args.force) throw new Error("PLAN requires reference/REFERENCE_SELECTION.json from REFERENCE.");
        referenceSelection = { status: "missing_force_override", top_references: [], structural_references: [], inspiration_only_references: [], reference_strategy: {}, principle: "Reference selection missing under --force." };
      }
    } else {
      referenceSelection = { status: "disabled", top_references: [], structural_references: [], inspiration_only_references: [], reference_strategy: {}, principle: "REFERENCE=OFF" };
    }
    const matrix = buildSellingPointMatrix(input, brief);
    await writePlanningBundle(brief, matrix, outputDir);
    let spec = await buildProductPageSpec(input, source, outputDir, library, "pending");
    spec.reference_selection = {
      source_artifact: "reference/REFERENCE_SELECTION.json",
      status: referenceSelection.status,
      top_references: referenceSelection.top_references,
      structural_references: referenceSelection.structural_references,
      inspiration_only_references: referenceSelection.inspiration_only_references,
      reference_strategy: referenceSelection.reference_strategy,
      principle: referenceSelection.principle,
    };
    let referenceTraces = [];
    if (referenceMode === "ON") {
      const adapted = await adaptReferencePlan({ baselineSpec: spec, brief, selection: referenceSelection, templateLibrary: library, referenceLibraryRoot: path.join(skillDir, "reference-library") });
      spec = adapted.spec;
      referenceTraces = adapted.traces;
      const traceJson = { schema_version: "2.0", selection: { status: referenceSelection.status, structural_references: referenceSelection.structural_references, inspiration_only_references: referenceSelection.inspiration_only_references }, patterns: adapted.patterns, decisions: adapted.traces };
      const traceMarkdown = referenceTraceMarkdown({ traces: adapted.traces, selection: referenceSelection, patterns: adapted.patterns });
      await Promise.all([path.join(outputDir, "reference"), path.join(outputDir, "reports")].map((dir) => fs.mkdir(dir, { recursive: true })));
      await fs.writeFile(path.join(outputDir, "reference", "REFERENCE_DECISION_TRACE_V2.json"), `${JSON.stringify(traceJson, null, 2)}\n`, "utf8");
      await fs.writeFile(path.join(outputDir, "reference", "REFERENCE_DECISION_TRACE_V2.md"), traceMarkdown, "utf8");
      await fs.writeFile(path.join(outputDir, "reference", "reference_decision_review.html"), referenceDecisionReview(referenceSelection, adapted.traces, adapted.patterns), "utf8");
      await fs.writeFile(path.join(outputDir, "reports", "REFERENCE_DECISION_TRACE.md"), traceMarkdown, "utf8");
    } else {
      spec.reference_application = { mode: "OFF", adapter: "Not applied", plan_changed: false, reason: state.reference_mode_source === "legacy_fallback" ? "Backward-compatible legacy fallback" : "Explicit regression/troubleshooting mode" };
    }
    if (args["gate-mode"] === "internal-test") {
      spec.human_gates.story_approval = {
        status: "Approved — Internal QA",
        approved_by: "Codex Hub 3 phase simulation",
        approved_on: "2026-08-18",
        scope: "Story structure regression only; not business/legal/publication approval",
      };
      lockStorySequence(spec, { lockedBy: "Story Gate — Internal QA", lockedOn: "2026-08-19" });
    }
    spec.human_gates.layout_approval = {
      status: "Pending Review",
      approved_by: "",
      approved_on: "",
      scope: "Final templates, layout, product placement and placeholder-scene composition",
    };
    spec.human_gates.final_render_authorized = false;
    refreshSpec(spec, library);
    await writeSpecBundle(spec, outputDir, { derived: false });
    await writeStoryReview(spec, outputDir);
    state.current_phase = "plan";
    if (referenceMode === "OFF") state.reference_status = state.reference_mode_source === "legacy_fallback" ? "legacy_fallback" : "disabled";
    state.plan_status = "complete";
    state.story_gate = approved(spec.human_gates.story_approval) ? "approved_internal_test" : "pending";
    state.story_sequence_locked = Boolean(spec.story_sequence_lock?.locked);
    state.story_sequence_fingerprint = spec.story_sequence_lock?.fingerprint || "";
    state.design_status = "pending";
    state.layout_gate = "pending";
    await blockFinalOutputs(outputDir, "Story/Layout/Publish Gate not complete");
    result = { phase, status: "stopped_at_story_gate", reference_mode: referenceMode, reference_adapter_applied: referenceMode === "ON", reference_decisions: referenceTraces.length, story_gate: state.story_gate, spec_sha256: spec.meta.spec_sha256, warnings };
  }

  if (phase === "design") {
    requireGate("Story Gate", state.story_gate);
    const spec = await loadPhaseSpec(library);
    requireGate("Spec Story Approval", spec.human_gates?.story_approval?.status);
    if (args.force && !approved(spec.human_gates?.story_approval)) {
      spec.human_gates.story_approval = { status: "Approved — Force Override", approved_by: "CLI --force", approved_on: "2026-08-18", scope: "Risk override; not publication approval" };
    }
    const stateIntegrity = assertStorySequenceStateIntegrity(spec, state, { allowInitialLock: true });
    if (stateIntegrity.initial_lock_required) {
      lockStorySequence(spec, {
        lockedBy: spec.human_gates.story_approval.approved_by || "Story Gate",
        lockedOn: spec.human_gates.story_approval.approved_on || "2026-08-19",
      });
    }
    assertStorySequenceIntegrity(spec);
    if (args["gate-mode"] === "internal-test") {
      spec.human_gates.layout_approval = {
        status: "Approved — Internal QA",
        approved_by: "Codex Hub 3 phase simulation",
        approved_on: "2026-08-18",
        scope: "Template/layout regression only; not business/legal/publication approval",
      };
    } else if (!spec.human_gates.layout_approval) {
      spec.human_gates.layout_approval = { status: "Pending Review", approved_by: "", approved_on: "", scope: "Template and layout" };
    }
    spec.human_gates.final_render_authorized = approved(spec.human_gates.layout_approval);
    refreshSpec(spec, library);
    await writeSpecBundle(spec, outputDir);
    await writeLayoutReview(spec, outputDir);
    state.current_phase = "design";
    state.design_status = "complete";
    state.story_gate = approved(spec.human_gates.story_approval) ? state.story_gate === "pending" ? "approved" : state.story_gate : "pending";
    state.story_sequence_locked = true;
    state.story_sequence_fingerprint = spec.story_sequence_lock.fingerprint;
    state.layout_gate = approved(spec.human_gates.layout_approval) ? "approved_internal_test" : "pending";
    await blockFinalOutputs(outputDir, "Layout/Publish Gate not complete");
    result = { phase, status: "stopped_at_layout_gate", layout_gate: state.layout_gate, spec_sha256: spec.meta.spec_sha256 };
  }

  if (phase === "produce") {
    requireGate("Layout Gate", state.layout_gate);
    const spec = await loadPhaseSpec(library);
    assertStorySequenceStateIntegrity(spec, state);
    assertStorySequenceIntegrity(spec);
    requireGate("Spec Layout Approval", spec.human_gates?.layout_approval?.status);
    if (args.force && !approved(spec.human_gates?.layout_approval)) {
      spec.human_gates.layout_approval = { status: "Approved — Force Override", approved_by: "CLI --force", approved_on: "2026-08-18", scope: "Risk override; not publication approval" };
    }
    spec.human_gates.final_render_authorized = true;
    refreshSpec(spec, library);
    await writeSpecBundle(spec, outputDir);
    const render = await renderFromSpec(spec, outputDir);
    if (render.status === "VISUAL_CAPABILITY_MISMATCH") {
      state.produce_status = "blocked";
      state.qa_status = "blocked_visual_capability";
      state.publish_gate = "blocked";
      throw new Error(`${render.status}: ${render.reason} ${JSON.stringify(render.visual_capability_check.mismatches)}`);
    }
    const { renderWorkbooksFromSpec } = await import("./workbook_renderer.mjs");
    const workbooks = await renderWorkbooksFromSpec(spec, outputDir);
    const exports = await syncFinalExports(spec, outputDir);
    state.current_phase = "produce";
    state.produce_status = render.rendered && render.mobile_readability === "PASS" ? "complete" : "blocked";
    state.qa_status = render.mobile_readability === "PASS" ? "pending_browser_qa" : "blocked_mobile_readability";
    state.publish_gate = spec.publish_gate.status.toLowerCase();
    result = { phase, status: state.produce_status, render, workbook_count: workbooks.length, export_workbook_count: exports.workbook_count, final_output_generated: exports.generated, final_output_reason: exports.reason, publish_gate: spec.publish_gate.status, spec_sha256: spec.meta.spec_sha256 };
    await fs.mkdir(path.join(outputDir, "qa"), { recursive: true });
    await fs.writeFile(path.join(outputDir, "qa", "generation.json"), `${JSON.stringify(result, null, 2)}\n`, "utf8");
  }

  state.force_warnings = [...(state.force_warnings || []), ...forceWarnings];
  await writeProjectState(outputDir, state);
  console.log(JSON.stringify({ ...result, project_state: "PROJECT_STATE.json", force_warnings: forceWarnings }, null, 2));
} catch (error) {
  state.current_phase = phase;
  state.force_warnings = [...(state.force_warnings || []), ...forceWarnings];
  await writeProjectState(outputDir, state);
  console.error(JSON.stringify({ phase, status: "blocked", error: error.message, project_state: "PROJECT_STATE.json", force_warnings: forceWarnings }, null, 2));
  process.exit(1);
}
