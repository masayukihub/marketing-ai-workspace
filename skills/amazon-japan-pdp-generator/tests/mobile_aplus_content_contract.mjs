#!/usr/bin/env node
import assert from "node:assert/strict";
import fs from "node:fs/promises";
import path from "node:path";
import { renderVisualQualityMobileAplus } from "../scripts/visual_quality_renderers.mjs";

function decodeXml(value) {
  return String(value || "")
    .replaceAll("&lt;", "<").replaceAll("&gt;", ">").replaceAll("&quot;", '"')
    .replaceAll("&#039;", "'").replaceAll("&amp;", "&");
}

function fieldValue(svg, unitId, field) {
  const unit = unitId.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
  const pattern = new RegExp(`<g[^>]*data-field="${field}"[^>]*data-unit-id="${unit}"[^>]*>([\\s\\S]*?)<\\/g>`);
  const match = svg.match(pattern);
  if (!match) return null;
  return decodeXml([...match[1].matchAll(/<text\b[^>]*>([\s\S]*?)<\/text>/g)].map((item) => item[1]).join(""));
}

function assertTextWithinCards(svg, label) {
  const starts=[...svg.matchAll(/<g class="aplus-unit-contract"[^>]*transform="translate\(0 ([0-9.]+)\)"[^>]*><rect[^>]*height="([0-9.]+)"/g)];
  assert.ok(starts.length>0,`${label} should contain unit cards`);
  starts.forEach((start,index)=>{
    const end=starts[index+1]?.index??svg.length;
    const card=svg.slice(start.index,end);
    const ys=[...card.matchAll(/<text[^>]* y="([0-9.]+)"/g)].map((match)=>Number(match[1]));
    const height=Number(start[2]);
    assert.ok(ys.length>0,`${label} card ${index+1} should contain text`);
    assert.ok(Math.max(...ys)<=height,`${label} card ${index+1} text y ${Math.max(...ys)} exceeds local card height ${height}`);
  });
}

const fixture = {
  id: "APLUS-M05",
  template_id: "A-TECHNICAL",
  module_headline: "購入前に確認したいこと",
  units: [
    { id: "APLUS-U01", headline: "見出し一", copy: "本文一は省略せず表示します。", condition: "条件一も本文の近くに表示します。", annotation: "注記一も可視領域に置きます。" },
    { id: "APLUS-U02", headline: "見出し二", copy: "本文二は長さに応じて高さを広げます。", condition: "", annotation: "注記二" },
    { id: "APLUS-U03", headline: "見出し三", copy: "本文三", condition: "条件三", annotation: "" },
    { id: "APLUS-U04", headline: "見出し四", copy: "本文四", condition: "条件四", annotation: "注記四" },
  ],
};

const fixtureSvg = renderVisualQualityMobileAplus({ module: fixture, prepared: [] });
assertTextWithinCards(fixtureSvg,"fixture");
let fixtureChecks = 0;
for (const unit of fixture.units) {
  for (const [field, value] of [["headline", unit.headline], ["body", unit.copy], ["condition", unit.condition], ["annotation", unit.annotation]]) {
    if (!value) continue;
    assert.equal(fieldValue(fixtureSvg, unit.id, field), value, `${unit.id}.${field} must be visibly rendered without truncation`);
    fixtureChecks += 1;
  }
}

const outputDir = process.argv[2] ? path.resolve(process.argv[2]) : "";
let projectChecks = 0;
if (outputDir) {
  const spec = JSON.parse(await fs.readFile(path.join(outputDir, "spec", "PRODUCT_PAGE_SPEC.json"), "utf8"));
  for (const module of spec.aplus_modules) {
    const svg = await fs.readFile(path.join(outputDir, "design", "aplus", "mobile", `aplus_${String(module.sequence).padStart(2, "0")}.svg`), "utf8");
    assertTextWithinCards(svg,module.id);
    for (const unit of module.units) {
      for (const [field, value] of [["headline", unit.headline], ["body", unit.copy || unit.body], ["condition", unit.condition || unit.conditions || unit.consumer_condition], ["annotation", unit.annotation || unit.technical_annotation || unit.annotation_text]]) {
        if (!String(value || "").trim()) continue;
        assert.equal(fieldValue(svg, unit.id, field), String(value).trim(), `${unit.id}.${field} project render mismatch`);
        projectChecks += 1;
      }
    }
  }
}

console.log(JSON.stringify({ status: "PASS", fixture_checks: fixtureChecks, project_checks: projectChecks, contract: "headline/body/condition/annotation visible and untruncated" }, null, 2));
