#!/usr/bin/env node
import path from "node:path";
import { fileURLToPath } from "node:url";
import { parseArgs, readSpec, readTemplateLibrary, refreshSpec, validateSpec, writeSpecBundle } from "./spec_system.mjs";
import { renderFromSpec } from "./render_v4.mjs";
import { renderWorkbooksFromSpec } from "./workbook_renderer.mjs";

const args = parseArgs(process.argv);
if (!args.spec || !args.output) {
  console.error("Usage: node scripts/render_from_spec.mjs --spec <PRODUCT_PAGE_SPEC.json> --output <output-dir>");
  process.exit(2);
}

const outputDir = path.resolve(args.output);
const skillDir = path.dirname(path.dirname(fileURLToPath(import.meta.url)));
const library = await readTemplateLibrary(skillDir);
const spec = refreshSpec(await readSpec(path.resolve(args.spec)), library);
const errors = validateSpec(spec, library);
if (errors.length) {
  console.error(JSON.stringify({ structural_gate: "Blocked", spec_errors: errors }, null, 2));
  process.exit(1);
}
await writeSpecBundle(spec, outputDir);
const persistedSpec = await readSpec(path.join(outputDir, "spec", "PRODUCT_PAGE_SPEC.json"));
const renderResult = await renderFromSpec(persistedSpec, outputDir);
const workbookResult = await renderWorkbooksFromSpec(persistedSpec, outputDir);
console.log(JSON.stringify({ structural_gate: "Pass", publish_gate: persistedSpec.publish_gate.status, render: renderResult.status, workbooks: workbookResult.length, spec_sha256: persistedSpec.meta.spec_sha256 }, null, 2));
if (renderResult.mobile_readability === "FAIL") process.exitCode = 1;
