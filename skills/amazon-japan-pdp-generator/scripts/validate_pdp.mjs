#!/usr/bin/env node
import fs from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { parseArgs, readSpec, readTemplateLibrary, validateSpec } from "./spec_system.mjs";
import { rendererCapability } from "./renderer_registry.mjs";
import { publishGatePassed } from "./phase_system.mjs";

const args = parseArgs(process.argv);
if (!args.output) {
  console.error("Usage: node scripts/validate_pdp.mjs --output <output-dir> [--spec <PRODUCT_PAGE_SPEC.json>]");
  process.exit(2);
}

async function exists(file) {
  try { await fs.access(file); return true; } catch { return false; }
}

const output = path.resolve(args.output);
const specFile = path.resolve(args.spec || path.join(output, "spec", "PRODUCT_PAGE_SPEC.json"));
const skillDir = path.dirname(path.dirname(fileURLToPath(import.meta.url)));
const library = await readTemplateLibrary(skillDir);
const spec = await readSpec(specFile);
const errors = validateSpec(spec, library);
const checks = [];
const required = [
  "PROJECT_STATE.json",
  "spec/PRODUCT_BRIEF.json",
  "spec/SELLING_POINT_MATRIX.json",
  "spec/PRODUCT_PAGE_SPEC.json",
  "spec/ASSET_RESOLUTION_PLAN.json",
  "spec/asset_resolution_plan.json",
  "spec/copy_deck.json",
  "review/product_understanding_cn.html",
  "review/story_review.html",
  "review/layout_review.html",
  "workbooks/visual_composition_plan.xlsx",
  "workbooks/selling_point_matrix.xlsx",
  "workbooks/product_image_brief.xlsx",
  "workbooks/aplus_content_plan.xlsx",
  "workbooks/comparison_chart.xlsx",
  "workbooks/amazon_seo_keywords.xlsx",
  "workbooks/asset_requirements.xlsx",
  "workbooks/asset_gap_analysis.xlsx",
  "qa/workbook-inspection.json",
];
if (spec.human_gates.final_render_authorized) required.push(
  "review/design_review_cn.html",
  "preview/amazon_pdp_preview.html",
  "preview/mobile_preview.html",
  "reports/publish_gate.md",
  "reports/asset_resolution_report.md",
  "reports/japan_localization_review.md",
  "reports/visual_consistency_report.md",
  "reports/visual_production_manifest.json",
  "qa/mobile-readability-gate.json",
);
if (spec.reference_application?.mode === "ON") required.push(
  "reference/REFERENCE_SELECTION.json",
  "reference/REFERENCE_SELECTION.md",
  "reference/REFERENCE_DECISION_TRACE_V2.json",
  "reference/REFERENCE_DECISION_TRACE_V2.md",
  "reference/reference_decision_review.html",
  "reports/REFERENCE_DECISION_TRACE.md",
);
for (const relative of required) checks.push({ check:`file:${relative}`, pass:await exists(path.join(output,relative)) });

const templateIds = new Set((library.templates || []).map(template=>template.template_id));
checks.push({check:"count:product-images",pass:spec.product_images.length===7});
checks.push({check:"count:aplus-modules",pass:spec.aplus_modules.length>=5&&spec.aplus_modules.length<=8});
checks.push({check:"count:aplus-units",pass:spec.aplus_modules.reduce((sum,module)=>sum+module.units.length,0)>0});
for(const item of spec.product_images){
  checks.push({check:`template:${item.id}`,pass:templateIds.has(item.template_id)});
  checks.push({check:`renderer:${item.id}`,pass:rendererCapability(item.template_id).renderer_available});
  checks.push({check:`ai-product:${item.id}`,pass:item.product_body_ai_generated!==true});
  checks.push({check:`copy-options:${item.id}`,pass:item.id==="IMAGE-01"||(item.copy_review?.options||[]).length===3});
}
for(const module of spec.aplus_modules){
  checks.push({check:`template:${module.id}`,pass:templateIds.has(module.template_id)});
  checks.push({check:`renderer:${module.id}`,pass:rendererCapability(module.template_id).renderer_available});
  for(const unit of module.units){checks.push({check:`ai-product:${unit.id}`,pass:unit.product_body_ai_generated!==true});checks.push({check:`copy-options:${unit.id}`,pass:(unit.copy_review?.options||[]).length===3});}
}

if(spec.human_gates.final_render_authorized){
  for(const record of [...spec.product_images,...spec.aplus_modules]){
    const jpeg=path.join(output,record.outputs.jpeg);const svg=path.join(output,record.outputs.svg);const wireframe=path.join(output,record.outputs.wireframe_svg);
    let signature=Buffer.alloc(0);try{signature=(await fs.readFile(jpeg)).subarray(0,2);}catch{}
    checks.push({check:`jpeg:${record.id}`,pass:signature[0]===0xff&&signature[1]===0xd8});
    checks.push({check:`svg:${record.id}`,pass:await exists(svg)});
    checks.push({check:`wireframe:${record.id}`,pass:await exists(wireframe)});
    let svgText="";try{svgText=await fs.readFile(svg,"utf8");}catch{}
    checks.push({check:`svg-spec-hash:${record.id}`,pass:svgText.includes(spec.meta.spec_sha256)});
  }
  const visibleCharacters = (value) => [...String(value || "")].filter((character) => !/\s/.test(character)).slice(0,8);
  const decodeXml = (value) => String(value || "")
    .replaceAll("&lt;", "<").replaceAll("&gt;", ">").replaceAll("&quot;", '"')
    .replaceAll("&#039;", "'").replaceAll("&amp;", "&");
  const renderedContractValue = (svgText, unitId, field) => {
    const unit = String(unitId || "").replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
    const key = String(field || "").replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
    const pattern = new RegExp(`<g[^>]*data-field="${key}"[^>]*data-unit-id="${unit}"[^>]*>([\\s\\S]*?)<\\/g>`);
    const match = svgText.match(pattern);
    if (!match) return null;
    return decodeXml([...match[1].matchAll(/<text\b[^>]*>([\s\S]*?)<\/text>/g)].map((item) => item[1].replace(/<[^>]+>/g, "")).join(""));
  };
  for (const item of spec.product_images.filter((record) => record.id !== "IMAGE-01")) {
    const svgText = await fs.readFile(path.join(output,item.outputs.svg),"utf8").catch(()=>"");
    checks.push({check:`missing-text:${item.id}:headline`,pass:visibleCharacters(item.headline).every((character)=>svgText.includes(character))});
    checks.push({check:`missing-text:${item.id}:body`,pass:visibleCharacters(item.sub_copy).every((character)=>svgText.includes(character))});
  }
  for (const module of spec.aplus_modules) {
    const mobileSvgRelative=`design/aplus/mobile/aplus_${String(module.sequence).padStart(2,"0")}.svg`;
    const mobileJpegRelative=`design/aplus/mobile/aplus_${String(module.sequence).padStart(2,"0")}.jpg`;
    const mobileSvgText=await fs.readFile(path.join(output,mobileSvgRelative),"utf8").catch(()=>"");
    let mobileSignature=Buffer.alloc(0);try{mobileSignature=(await fs.readFile(path.join(output,mobileJpegRelative))).subarray(0,2);}catch{}
    checks.push({check:`mobile-svg:${module.id}`,pass:Boolean(mobileSvgText)});
    checks.push({check:`mobile-jpeg:${module.id}`,pass:mobileSignature[0]===0xff&&mobileSignature[1]===0xd8});
    for(const unit of module.units){
      const visualQualityContract = mobileSvgText.includes("visual-quality ON mobile");
      const headline = String(unit.headline || "").trim();
      const body = String(unit.copy || unit.body || "").trim();
      const renderedHeadline = renderedContractValue(mobileSvgText,unit.id,"headline");
      const renderedBody = renderedContractValue(mobileSvgText,unit.id,"body");
      checks.push({check:`missing-text:${unit.id}:title`,pass:visualQualityContract?renderedHeadline===headline:visibleCharacters(headline).every((character)=>mobileSvgText.includes(character))});
      checks.push({check:`missing-text:${unit.id}:body`,pass:visualQualityContract?renderedBody===body:visibleCharacters(body).every((character)=>mobileSvgText.includes(character))});
      for(const [field,value] of [["condition",unit.condition||unit.conditions||unit.consumer_condition||""],["annotation",unit.annotation||unit.technical_annotation||unit.annotation_text||""]]){
        if(!String(value||"").trim()) continue;
        checks.push({check:`missing-text:${unit.id}:${field}`,pass:visualQualityContract&&renderedContractValue(mobileSvgText,unit.id,field)===String(value).trim()});
      }
    }
  }
  const mobileReadability=JSON.parse(await fs.readFile(path.join(output,"qa","mobile-readability-gate.json"),"utf8").catch(()=>"{}"));
  checks.push({check:"mobile-readability:390",pass:mobileReadability.status==="PASS"&&mobileReadability.modules?.length===spec.aplus_modules.length});
  if(spec.reference_application?.mode==="ON"){
    const trace=JSON.parse(await fs.readFile(path.join(output,"reference","REFERENCE_DECISION_TRACE_V2.json"),"utf8").catch(()=>"{}"));
    checks.push({check:"reference-adapter:plan-changed",pass:spec.reference_application.plan_changed===true});
    checks.push({check:"reference-trace:14-decisions",pass:trace.decisions?.length===14&&trace.decisions.every((decision)=>decision.final_plan_decision==="ACCEPTED")});
  }
  const preview=await fs.readFile(path.join(output,"preview","amazon_pdp_preview.html"),"utf8").catch(()=>"");
  const design=await fs.readFile(path.join(output,"review","design_review_cn.html"),"utf8").catch(()=>"");
  for(const marker of ["Amazon Preview","data-device=\"desktop\"","data-device=\"mobile\"",spec.meta.spec_sha256]) checks.push({check:`preview:${marker}`,pass:preview.includes(marker)});
  for(const marker of ["Design Review","Product Layer","Scene Layer","Graphic Layer",spec.meta.spec_sha256]) checks.push({check:`design:${marker}`,pass:design.includes(marker)});
  for(const marker of ["Selected Reference","Decision Reason","Learned Principle","SwitchBot Adaptation","Why This Layout","What Was Not Copied"]) checks.push({check:`design-trace:${marker}`,pass:design.includes(marker)});
  checks.push({check:"preview:no-fabricated-rating",pass:!/[★☆]/u.test(preview)&&!/>\s*(?:4\.0|4\.5)\s*</.test(preview)});
  for(const forbidden of ["Need Verification","Claim Source","Product Knowledge","Review Draft","理解产品","产生兴趣","素材需求","被阻塞","Seller Central"]) checks.push({check:`consumer-hidden:${forbidden}`,pass:!preview.includes(forbidden)});
}

for(const relative of required.filter(name=>name.endsWith(".xlsx"))){
  let signature="";try{signature=(await fs.readFile(path.join(output,relative))).subarray(0,2).toString("utf8");}catch{}
  checks.push({check:`xlsx:${relative}`,pass:signature==="PK"});
}
for(const relative of ["spec/ASSET_RESOLUTION_PLAN.json","spec/asset_resolution_plan.json","spec/copy_deck.json"]){
  const json=JSON.parse(await fs.readFile(path.join(output,relative),"utf8"));
  checks.push({check:`derived-spec-hash:${relative}`,pass:json.spec_sha256===spec.meta.spec_sha256});
}
const state=JSON.parse(await fs.readFile(path.join(output,"PROJECT_STATE.json"),"utf8"));
checks.push({check:"state:produce-complete",pass:state.produce_status==="complete"});
checks.push({check:"state:qa-pass",pass:state.qa_status==="pass"});
checks.push({check:"state:publish-synced",pass:state.publish_gate===spec.publish_gate.status.toLowerCase()});
if(publishGatePassed(spec)){
  for(const item of spec.product_images) checks.push({check:`final-product:${item.id}`,pass:await exists(path.join(output,"final","product_images",path.basename(item.outputs.jpeg)))});
  for(const module of spec.aplus_modules) checks.push({check:`final-aplus:${module.id}`,pass:await exists(path.join(output,"final","aplus",path.basename(module.outputs.jpeg)))});
  for(const relative of required.filter(name=>name.startsWith("workbooks/")&&name.endsWith(".xlsx"))){
    checks.push({check:`export:${path.basename(relative)}`,pass:await exists(path.join(output,"export",path.basename(relative)))});
  }
}else{
  checks.push({check:"blocked:no-final-directory",pass:!(await exists(path.join(output,"final")))});
  checks.push({check:"blocked:no-export-directory",pass:!(await exists(path.join(output,"export")))});
  checks.push({check:"blocked:marker",pass:await exists(path.join(output,"reports","FINAL_OUTPUT_NOT_GENERATED.md"))});
}
for(const record of spec.asset_resolution_plan.records){
  checks.push({check:`provenance:${record.visual_id}:resolved-semantics`,pass:record.resolved===record.file_resolved});
  checks.push({check:`provenance:${record.visual_id}:unsafe-product-layer`,pass:!["placeholder","external_reference","generated_scene","unknown"].includes(record.source_type)||record.product_layer_allowed===false});
}
const failed=checks.filter(check=>!check.pass);
const report={
  structural_gate:errors.length||failed.length?"Fail":"Pass",
  publish_gate:spec.publish_gate.status,
  story_gate:spec.human_gates.story_approval.status,
  layout_gate:spec.human_gates.layout_approval.status,
  product_images:spec.product_images.length,
  aplus_modules:spec.aplus_modules.length,
  aplus_content_units:spec.aplus_modules.reduce((sum,module)=>sum+module.units.length,0),
  spec_sha256:spec.meta.spec_sha256,
  validation_errors:errors,
  failed_checks:failed,
  checks_passed:checks.length-failed.length,
  checks_total:checks.length,
  note:"Structural Pass, Gate approval and Publish Ready remain independent.",
};
await fs.mkdir(path.join(output,"qa"),{recursive:true});
await fs.writeFile(path.join(output,"qa","validation.json"),`${JSON.stringify(report,null,2)}\n`,"utf8");
console.log(JSON.stringify(report,null,2));
if(report.structural_gate!=="Pass") process.exit(1);
