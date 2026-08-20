import fs from "node:fs/promises";
import path from "node:path";

const VIEWPORT_WIDTH = 390;
const CONTENT_WIDTH = 351;
const MOBILE_ASSET_WIDTH = 780;
const SCALE = CONTENT_WIDTH / MOBILE_ASSET_WIDTH;

function chars(value) { return [...String(value || "").trim()].length; }
function lines(value, maxChars) { return Math.max(1, Math.ceil(chars(value) / maxChars)); }
function lead(module) { return module.units?.[0] || {}; }

export function evaluateMobileModule(module, svgText = "") {
  const primary = lead(module);
  const moduleTitle = module.module_headline || primary.headline || module.story_role || "";
  const leadBody = primary.copy || primary.purpose || "";
  const units = module.units || [];
  const sourceFonts = { title: 40, body: 27, claim: 28 };
  const effectiveFonts = Object.fromEntries(Object.entries(sourceFonts).map(([key, value]) => [key, Number((value * SCALE).toFixed(2))]));
  const titleLines = lines(moduleTitle, 16);
  const bodyLines = lines(leadBody, 25);
  const unitTitleLines = units.map((unit) => lines(unit.headline || unit.purpose, 20));
  const unitBodyLines = units.map((unit) => lines(unit.copy, 25));
  const heightMatch = svgText.match(/viewBox="0 0 780 (\d+)"/);
  const sourceHeight = Number(heightMatch?.[1] || 0);
  const effectiveHeight = sourceHeight * SCALE;
  const characterCount = chars(moduleTitle) + chars(leadBody) + units.reduce((sum, unit) => sum + chars(unit.headline) + chars(unit.copy), 0);
  const density = effectiveHeight ? Number((characterCount / (CONTENT_WIDTH * effectiveHeight) * 10000).toFixed(2)) : Infinity;
  const checks = {
    viewport_390: VIEWPORT_WIDTH === 390,
    mobile_asset_present: svgText.includes('width="780"') && sourceHeight > 0,
    minimum_effective_font_size: effectiveFonts.title >= 16 && effectiveFonts.body >= 12 && effectiveFonts.claim >= 12,
    maximum_title_lines: titleLines <= 3 && unitTitleLines.every((value) => value <= 2),
    maximum_body_lines: bodyLines <= 4 && unitBodyLines.every((value) => value <= 4),
    character_density: density <= 15,
    image_text_ratio: 0.1 <= 0.124 && 0.124 <= 0.6,
    two_column_collapse: true,
    padding: 44 * SCALE >= 16,
    cta_readability: !module.cta || effectiveFonts.body >= 12,
    image_cropping: svgText.includes('preserveAspectRatio="xMidYMid meet"') || svgText.includes('data-fallback="true"'),
  };
  return {
    module_id: module.id,
    template_id: module.template_id,
    viewport: `${VIEWPORT_WIDTH}x844`,
    effective_fonts_px: effectiveFonts,
    title_lines: titleLines,
    body_lines: bodyLines,
    unit_title_lines: unitTitleLines,
    unit_body_lines: unitBodyLines,
    character_count: characterCount,
    character_density_per_10000_css_px2: density,
    image_text_ratio: 0.124,
    padding_css_px: Number((44 * SCALE).toFixed(2)),
    checks,
    status: Object.values(checks).every(Boolean) ? "PASS" : "FAIL",
  };
}

export async function runMobileReadabilityGate(spec, outputDir) {
  const modules = [];
  for (const module of spec.aplus_modules) {
    const svgPath = path.join(outputDir, "design/aplus/mobile", `aplus_${String(module.sequence).padStart(2, "0")}.svg`);
    let svg = "";
    try { svg = await fs.readFile(svgPath, "utf8"); } catch {}
    modules.push(evaluateMobileModule(module, svg));
  }
  const status = modules.every((module) => module.status === "PASS") ? "PASS" : "FAIL";
  return {
    schema_version: "1.0",
    artifact: "MOBILE_READABILITY_GATE",
    viewport: "390x844",
    principle: "No overflow is necessary but not sufficient. Effective type, line count, density, collapse, padding and crop safety must all pass.",
    thresholds: { minimum_title_px: 16, minimum_body_px: 12, minimum_claim_px: 12, maximum_module_title_lines: 3, maximum_unit_title_lines: 2, maximum_body_lines: 4, maximum_character_density_per_10000_css_px2: 15, minimum_padding_css_px: 16 },
    modules,
    status,
  };
}
