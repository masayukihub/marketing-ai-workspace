import fs from "node:fs/promises";
import path from "node:path";

function esc(value) {
  return String(value ?? "").replaceAll("&", "&amp;").replaceAll("<", "&lt;").replaceAll(">", "&gt;").replaceAll('"', "&quot;").replaceAll("'", "&#039;");
}

export const PHASES = ["know", "reference", "plan", "design", "produce"];

export function approved(value) {
  const status = typeof value === "object" ? value?.status : value;
  return /^approved(?:\b|\s|_|—|-)/i.test(String(status || ""));
}

export function defaultProjectState(inputFile = "") {
  return {
    schema_version: "1.0",
    system: "amazon-japan-pdp-generator-v4",
    source_input: inputFile,
    current_phase: "not_started",
    know_status: "pending",
    reference_mode: "ON",
    reference_mode_source: "default",
    reference_status: "pending",
    plan_status: "pending",
    story_gate: "pending",
    story_sequence_locked: false,
    story_sequence_fingerprint: "",
    design_status: "pending",
    layout_gate: "pending",
    produce_status: "pending",
    qa_status: "pending",
    publish_gate: "not_evaluated",
    last_updated: "2026-08-19",
    force_warnings: [],
  };
}

export async function readProjectState(outputDir, inputFile = "") {
  const stateFile = path.join(outputDir, "PROJECT_STATE.json");
  try {
    const stored = JSON.parse(await fs.readFile(stateFile, "utf8"));
    const legacyReferenceFallback = !Object.hasOwn(stored, "reference_mode");
    return {
      ...defaultProjectState(inputFile),
      ...stored,
      ...(legacyReferenceFallback ? { reference_mode: "OFF", reference_mode_source: "legacy_fallback" } : {}),
    };
  } catch {
    return defaultProjectState(inputFile);
  }
}

export async function writeProjectState(outputDir, state) {
  state.last_updated = "2026-08-19";
  await fs.mkdir(outputDir, { recursive: true });
  await fs.writeFile(path.join(outputDir, "PROJECT_STATE.json"), `${JSON.stringify(state, null, 2)}\n`, "utf8");
}

export function nextPhase(state) {
  if (state.know_status !== "complete") return "know";
  if (state.reference_mode !== "OFF" && state.reference_status !== "complete") return "reference";
  if (state.plan_status !== "complete") return "plan";
  if (approved(state.story_gate) && state.design_status !== "complete") return "design";
  if (approved(state.layout_gate) && state.produce_status !== "complete") return "produce";
  return null;
}

function rows(items, columns) {
  return items.map((item) => `<tr>${columns.map(([, key]) => `<td>${esc(item?.[key] ?? "")}</td>`).join("")}</tr>`).join("");
}

export async function writeProductUnderstanding(productBrief, outputDir) {
  const reviewDir = path.join(outputDir, "review");
  await fs.mkdir(reviewDir, { recursive: true });
  const claims = [...(productBrief.approved_claims || []), ...(productBrief.unverified_claims || [])];
  const html = `<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><link rel="icon" href="data:,"><title>产品理解 · KNOW</title><style>body{margin:0;background:#f4f7f6;color:#17212b;font-family:-apple-system,BlinkMacSystemFont,"PingFang SC","Hiragino Sans",sans-serif}.top{padding:18px 28px;background:#101820;color:#fff}.wrap{max-width:1180px;margin:auto;padding:28px}.card{background:#fff;border:1px solid #dfe6e5;border-radius:16px;padding:22px;margin:0 0 18px}.grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:18px}.label{font-size:12px;color:#087a66;font-weight:800;letter-spacing:.08em}.value{font-size:20px;font-weight:700;line-height:1.5}table{border-collapse:collapse;width:100%;font-size:14px}th,td{padding:10px;border-bottom:1px solid #e2e8e7;text-align:left;vertical-align:top}.warn{color:#a2461c;font-weight:700}.muted{color:#64757c}@media(max-width:700px){.wrap{padding:14px}.grid{grid-template-columns:1fr}}</style></head><body><div class="top"><strong>PHASE 1 · KNOW</strong>　产品理解审阅</div><main class="wrap"><section class="card"><h1>${esc(productBrief.product?.name || "Product")}</h1><p class="muted">本页只确认产品、受众、问题、价值、证据与限制；不包含图片结构、A+ Layout、AI 场景或最终视觉。</p></section><section class="grid"><article class="card"><div class="label">TARGET AUDIENCE</div><div class="value">${esc(productBrief.target_audience)}</div></article><article class="card"><div class="label">CORE PROBLEM</div><div class="value">${esc(productBrief.core_problem)}</div></article><article class="card"><div class="label">CORE VALUE</div><div class="value">${esc(productBrief.core_value)}</div></article><article class="card"><div class="label">FACT CHECK</div><div class="value ${productBrief.fact_checks.status === "Pass" ? "" : "warn"}">${esc(productBrief.fact_checks.status)}</div><p>${esc(productBrief.fact_checks.unverified_claim_count)} 条 Claim 尚未 Approved</p></article></section><section class="card"><h2>卖点候选（尚未形成页面结构）</h2><table><thead><tr><th>层级</th><th>Feature</th><th>Benefit</th><th>Proof</th><th>Status</th></tr></thead><tbody>${rows(productBrief.selling_points || [], [["层级","level"],["Feature","feature"],["Benefit","benefit"],["Proof","proof"],["Status","status"]])}</tbody></table></section><section class="card"><h2>Claim 与来源状态</h2><table><thead><tr><th>ID</th><th>Copy</th><th>Status</th><th>Source</th><th>Risk</th></tr></thead><tbody>${rows(claims, [["ID","id"],["Copy","copy"],["Status","status"],["Source","sourceId"],["Risk","risk"]])}</tbody></table></section><section class="card"><h2>购买顾虑与限制</h2><ul>${(productBrief.objections || []).map((item) => `<li>${esc(item)}</li>`).join("")}</ul><p class="warn">Need Verification / Blocked / Prohibited 不会在此阶段被推断为事实。</p></section></main></body></html>`;
  await fs.writeFile(path.join(reviewDir, "product_understanding_cn.html"), html, "utf8");
}

async function copyIfExists(source, target) {
  try {
    await fs.access(source);
  } catch {
    return false;
  }
  await fs.mkdir(path.dirname(target), { recursive: true });
  await fs.copyFile(source, target);
  return true;
}

export function publishGatePassed(spec) {
  return String(spec?.publish_gate?.status || "").trim().toUpperCase() === "PASS";
}

export async function blockFinalOutputs(outputDir, reason = "Publish Gate BLOCKED") {
  const finalDir = path.join(outputDir, "final");
  const exportDir = path.join(outputDir, "export");
  await fs.rm(finalDir, { recursive: true, force: true });
  await fs.rm(exportDir, { recursive: true, force: true });
  const reportsDir = path.join(outputDir, "reports");
  await fs.mkdir(reportsDir, { recursive: true });
  const marker = "FINAL_OUTPUT_NOT_GENERATED.md";
  await fs.writeFile(path.join(reportsDir, marker), `FINAL_OUTPUT_NOT_GENERATED\nReason: ${reason}\n`, "utf8");
  return { generated: false, workbook_count: 0, reason, marker: `reports/${marker}` };
}

export async function syncFinalExports(spec, outputDir) {
  if (!publishGatePassed(spec)) {
    return blockFinalOutputs(outputDir, `Publish Gate ${spec?.publish_gate?.status || "BLOCKED"}`);
  }
  const finalDir = path.join(outputDir, "final");
  await Promise.all([
    path.join(finalDir, "product_images"),
    path.join(finalDir, "aplus"),
    path.join(finalDir, "comparison"),
    path.join(finalDir, "editable"),
    path.join(outputDir, "export"),
  ].map((dir) => fs.mkdir(dir, { recursive: true })));
  await fs.rm(path.join(outputDir, "reports", "FINAL_OUTPUT_NOT_GENERATED.md"), { force: true });
  for (const item of spec.product_images || []) {
    await copyIfExists(path.join(outputDir, item.outputs.jpeg), path.join(finalDir, "product_images", path.basename(item.outputs.jpeg)));
  }
  for (const module of spec.aplus_modules || []) {
    const target = path.join(finalDir, "aplus", path.basename(module.outputs.jpeg));
    await copyIfExists(path.join(outputDir, module.outputs.jpeg), target);
    if (module.template_id === "A-COMPARISON") await copyIfExists(path.join(outputDir, module.outputs.jpeg), path.join(finalDir, "comparison", path.basename(module.outputs.jpeg)));
  }
  try {
    await fs.cp(path.join(outputDir, "design", "svg"), path.join(finalDir, "editable"), { recursive: true, force: true });
  } catch {}
  let workbookCount = 0;
  try {
    const files = (await fs.readdir(path.join(outputDir, "workbooks"))).filter((name) => name.endsWith(".xlsx"));
    for (const name of files) {
      if (await copyIfExists(path.join(outputDir, "workbooks", name), path.join(outputDir, "export", name))) workbookCount += 1;
    }
  } catch {}
  return { generated: true, workbook_count: workbookCount, reason: "Publish Gate PASS" };
}
