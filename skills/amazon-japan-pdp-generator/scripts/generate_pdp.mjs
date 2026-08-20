#!/usr/bin/env node
import fs from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { validateData } from "./pdp_lib.mjs";
import { buildProductPageSpec, parseArgs, readSpec, readTemplateLibrary, validateSpec, writeSpecBundle } from "./spec_system.mjs";
import { renderFromSpec } from "./render_v4.mjs";
import { renderWorkbooksFromSpec } from "./workbook_renderer.mjs";

const args = parseArgs(process.argv);
if (!args.input || !args.output) {
  console.error("Usage: node scripts/generate_pdp.mjs --input <pdp-input.json> --output <output-dir> [--gate-mode pending|internal-test]");
  process.exit(2);
}

const inputFile = path.resolve(args.input);
const outputDir = path.resolve(args.output);
const skillDir = path.dirname(path.dirname(fileURLToPath(import.meta.url)));
const input = JSON.parse(await fs.readFile(inputFile, "utf8"));
const inputValidation = validateData(input);
if (inputValidation.errors.length) {
  console.error(JSON.stringify({ structural_gate: "Blocked", errors: inputValidation.errors, warnings: inputValidation.warnings }, null, 2));
  process.exit(1);
}

await fs.mkdir(outputDir, { recursive: true });
await fs.mkdir(path.join(outputDir, "qa"), { recursive: true });
const library = await readTemplateLibrary(skillDir);
const spec = await buildProductPageSpec(input, inputFile, outputDir, library, args["gate-mode"] || "pending");
const specErrors = validateSpec(spec, library);
if (specErrors.length) {
  console.error(JSON.stringify({ structural_gate: "Blocked", spec_errors: specErrors }, null, 2));
  process.exit(1);
}
await writeSpecBundle(spec, outputDir);

// Downstream renderers reload the persisted Spec. The input object is never used again.
const persistedSpec = await readSpec(path.join(outputDir, "spec", "PRODUCT_PAGE_SPEC.json"));
const renderResult = await renderFromSpec(persistedSpec, outputDir);
const workbooks = await renderWorkbooksFromSpec(persistedSpec, outputDir);
const report = {
  structural_gate: "Pass",
  publish_gate: persistedSpec.publish_gate.status,
  story_gate: persistedSpec.human_gates.story_approval.status,
  layout_gate: persistedSpec.human_gates.layout_approval.status,
  final_render: renderResult.status,
  spec_sha256: persistedSpec.meta.spec_sha256,
  product_images: persistedSpec.product_images.length,
  aplus_modules: persistedSpec.aplus_modules.length,
  aplus_content_units: persistedSpec.aplus_modules.reduce((sum, module) => sum + module.units.length, 0),
  workbooks: workbooks.length,
  warnings: inputValidation.warnings,
};
await fs.writeFile(path.join(outputDir, "qa", "generation.json"), `${JSON.stringify(report, null, 2)}\n`, "utf8");
console.log(JSON.stringify(report, null, 2));
if (renderResult.mobile_readability === "FAIL") process.exitCode = 1;
