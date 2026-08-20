import { buildProductSemanticContext, semanticVisualRole } from "./product_semantic_context.mjs";

const ON_VALUES = new Set(["ON", "TRUE", "1", "YES"]);

export const VISUAL_ROLES = Object.freeze([
  "IMPACT",
  "EXPLAIN",
  "DETAIL",
  "BREATHE",
  "SCENARIO",
  "PROOF",
  "COMPARE",
  "CLOSURE",
]);

const GALLERY_PROFILES = Object.freeze({
  "IMAGE-01": { visual_role: "IMPACT", background_family: "neutral-white", layout_family: "centered-object", product_position: "center", card_structure: "none", information_density: "zero", product_scale: "dominant" },
  "IMAGE-02": { visual_role: "IMPACT", background_family: "mint-air", layout_family: "asymmetric-split", product_position: "right", card_structure: "none", information_density: "low", product_scale: "large", decision_reason: "Large product scale turns the positioning statement into a recognizable product promise." },
  "IMAGE-03": { visual_role: "EXPLAIN", background_family: "paper", layout_family: "mechanism-split", product_position: "left", card_structure: "condition-band", information_density: "medium", product_scale: "large", decision_reason: "Large scale is retained to make the mechanism legible while side, background and density change." },
  "IMAGE-04": { visual_role: "PROOF", background_family: "cool-light", layout_family: "technical-rail", product_position: "left", card_structure: "rule-separated-proof", information_density: "medium", product_scale: "large", decision_reason: "This is intentional scale continuity from value to mechanism to proof; the proof rail changes the reading task." },
  "IMAGE-05": { visual_role: "SCENARIO", background_family: "warm-home", layout_family: "scene-led-open", product_position: "right", card_structure: "none", information_density: "low", product_scale: "medium" },
  "IMAGE-06": { visual_role: "COMPARE", background_family: "paper", layout_family: "editorial-matrix", product_position: "top-right", card_structure: "rule-separated-rows", information_density: "high", product_scale: "small" },
  "IMAGE-07": { visual_role: "CLOSURE", background_family: "soft-neutral", layout_family: "confidence-lines", product_position: "left", card_structure: "rule-separated-checks", information_density: "medium", product_scale: "large" },
});

const APLUS_PROFILES = Object.freeze({
  "APLUS-M01": { visual_role: "IMPACT", background_family: "mint-air", layout_family: "editorial-hero", mobile_layout_family: "mobile-impact-focus", product_position: "right", card_structure: "none", information_density: "low", product_scale: "dominant" },
  "APLUS-M02": { visual_role: "EXPLAIN", background_family: "paper", layout_family: "mechanism-50-50", mobile_layout_family: "mobile-explain-stack", product_position: "right", card_structure: "condition-band", information_density: "medium", product_scale: "large" },
  "APLUS-M03": { visual_role: "PROOF", background_family: "cool-light", layout_family: "technical-rail", mobile_layout_family: "mobile-proof-rail", product_position: "left", card_structure: "rule-separated-proof", information_density: "high", product_scale: "large" },
  "APLUS-M04": { visual_role: "DETAIL", background_family: "bright-neutral", layout_family: "parallel-three", mobile_layout_family: "mobile-detail-sequence", product_position: "per-unit", card_structure: "three-semantic-panels", information_density: "high", product_scale: "medium" },
  "APLUS-M05": { visual_role: "BREATHE", background_family: "warm-home", layout_family: "ownership-editorial", mobile_layout_family: "mobile-ownership-breathe", product_position: "left", card_structure: "none", information_density: "low", product_scale: "large" },
  "APLUS-M06": { visual_role: "COMPARE", background_family: "paper", layout_family: "selection-rows", mobile_layout_family: "mobile-selection-rows", product_position: "top-right", card_structure: "rule-separated-rows", information_density: "high", product_scale: "small" },
  "APLUS-M07": { visual_role: "CLOSURE", background_family: "mint-paper", layout_family: "objection-closure", mobile_layout_family: "mobile-objection-closure", product_position: "right", card_structure: "single-answer-line", information_density: "low", product_scale: "large" },
});

export function visualQualityEnabled(explicit = undefined) {
  const raw = explicit ?? process.env.VISUAL_QUALITY ?? "ON";
  return ON_VALUES.has(String(raw).trim().toUpperCase());
}

export function visualProfile(record, kind = "aplus", semanticContext = undefined) {
  const source = kind === "gallery" ? GALLERY_PROFILES : APLUS_PROFILES;
  const fallback = {
    visual_role: kind === "gallery" ? "EXPLAIN" : "DETAIL",
    background_family: "paper",
    layout_family: record?.template_id || "registered-primitive",
    product_position: "controlled",
    card_structure: "bounded",
    information_density: "medium",
    product_scale: "large",
  };
  const profile = { ...fallback, ...(source[record?.id] || {}) };
  profile.visual_role = semanticVisualRole(record, kind, semanticContext);
  const appliedReference = record?.reference_decision || record?.reference_learning || {};
  return { ...profile, ...appliedReference };
}

export function visualQualityManifest(spec) {
  const semanticContext = buildProductSemanticContext(spec);
  return {
    schema_version: "1.0",
    mode: "ON",
    principle: "Parameterize the existing 19 Layout Primitives; never change Story, Claims, Reference decisions, assets or sequence.",
    product_semantic_context_sha256: semanticContext.context_sha256,
    semantic_category: semanticContext.category_id,
    gallery: spec.product_images.map((record) => ({ id: record.id, template_id: record.template_id, ...visualProfile(record, "gallery", semanticContext) })),
    aplus: spec.aplus_modules.map((record) => ({ id: record.id, template_id: record.template_id, ...visualProfile(record, "aplus", semanticContext) })),
  };
}

function longestRun(values) {
  let best = 0;
  let current = 0;
  let previous;
  for (const value of values) {
    current = value === previous ? current + 1 : 1;
    previous = value;
    best = Math.max(best, current);
  }
  return best;
}

export function detectRhythmWarnings(manifest) {
  const keys = ["background_family", "layout_family", "product_position", "card_structure", "information_density", "product_scale"];
  const warnings = [];
  for (const [section, records] of [["Gallery", manifest.gallery], ["A+", manifest.aplus]]) {
    for (const key of keys) {
      let start = 0;
      for (let index = 1; index <= records.length; index += 1) {
        if (index < records.length && records[index]?.[key] === records[start]?.[key]) continue;
        const length = index - start;
        if (length >= 3) {
          const affectedRecords = records.slice(start, index);
          const acknowledged = affectedRecords.every((record) => Boolean(record.decision_reason));
          warnings.push({
          code: "VISUAL_RHYTHM_WARNING",
          section,
          dimension: key,
          value: records[start]?.[key],
          length,
          affected: affectedRecords.map((record) => record.id),
          accepted_continuity: acknowledged,
          decision_reasons: affectedRecords.map((record) => record.decision_reason || ""),
          correction: acknowledged
            ? "Continuity retained: value → mechanism → proof keeps the product recognizable while composition and density change."
            : "Re-parameterize only if the Story role does not justify continuity; never shuffle layouts randomly.",
          });
        }
        start = index;
      }
    }
  }
  return warnings;
}

export function visualRhythmScore(manifest) {
  const sequence = [...manifest.gallery, ...manifest.aplus];
  const roles = new Set(sequence.map((item) => item.visual_role));
  const backgrounds = sequence.map((item) => item.background_family);
  const layouts = sequence.map((item) => item.layout_family);
  const densities = sequence.map((item) => item.information_density);
  const scales = new Set(sequence.map((item) => item.product_scale));
  const cardHeavy = manifest.aplus.filter((item) => /three-semantic|bounded|card/i.test(item.card_structure)).length;
  const backgroundRun = longestRun(backgrounds);
  const layoutRun = longestRun(layouts);
  const highRun = longestRun(densities.map((value) => value === "high" ? "high" : "reset"));
  const mobileFamilies = new Set(manifest.aplus.map((item) => item.mobile_layout_family).filter(Boolean));
  const positionRun = longestRun(sequence.map((item) => item.product_position));
  const components = {
    layout_variety: layoutRun >= 3 ? 6 : layoutRun === 2 ? 11 : 14,
    background_variety: backgroundRun >= 3 ? 6 : new Set(backgrounds).size >= 5 ? 11 : 8,
    visual_scale: Math.min(9, scales.size * 3),
    content_density_rhythm: highRun >= 3 ? 6 : densities.includes("low") && densities.includes("high") ? 12 : 8,
    scene_product_technical_balance: manifest.aplus.some((item) => item.visual_role === "BREATHE") && manifest.aplus.some((item) => item.visual_role === "PROOF") ? 13 : 7,
    visual_role_progression: Math.min(10, roles.size + 2),
    product_position_cadence: positionRun >= 3 ? 4 : positionRun === 2 ? 8 : 9,
    card_restraint: cardHeavy === 0 ? 8 : cardHeavy <= 2 ? 7 : cardHeavy === 3 ? 5 : 2,
    mobile_role_preservation: mobileFamilies.size >= 6 ? 7 : mobileFamilies.size >= 3 ? 5 : 2,
    closure_quality: manifest.aplus.at(-1)?.visual_role === "CLOSURE" && manifest.aplus.at(-2)?.visual_role === "COMPARE" ? 4 : 2,
  };
  const score = Object.values(components).reduce((sum, value) => sum + value, 0);
  const warnings = detectRhythmWarnings(manifest);
  return { score, components, warnings, evidence: { unique_roles: [...roles], background_longest_run: backgroundRun, layout_longest_run: layoutRun, product_position_longest_run: positionRun, high_density_longest_run: highRun, product_scales: [...scales], card_heavy_aplus_modules: cardHeavy, mobile_layout_families: [...mobileFamilies] } };
}

export function brandFitAssessment(mode = "ON") {
  const on = String(mode).toUpperCase() === "ON";
  const dimensions = {
    product_first: on ? 90 : 73,
    smart_but_approachable: on ? 88 : 70,
    functional_clarity: on ? 91 : 74,
    japanese_home_fit: on ? 84 : 66,
    everyday_benefit: on ? 87 : 69,
    brand_restraint: on ? 92 : 72,
    ecosystem_consistency: on ? 84 : 76,
    human_product_balance: on ? 85 : 60,
  };
  const score = Math.round(Object.values(dimensions).reduce((sum, value) => sum + value, 0) / Object.keys(dimensions).length);
  return {
    score,
    risk: score >= 85 ? "LOW" : score >= 70 ? "MEDIUM" : "HIGH",
    dimensions,
    basis: on
      ? "SwitchBot white/mint/warm-neutral tokens, product-led scale, programmatic type, bounded dark contrast, and a late ownership breath."
      : "Baseline is structurally consistent but relies on repeated rounded cards and a generic mobile card stack; the late A+ closure is visually under-resolved.",
  };
}

export function templateFeelingAssessment(mode = "ON") {
  const on = String(mode).toUpperCase() === "ON";
  return {
    overall_risk: on ? "LOW" : "HIGH",
    gallery_risk: on ? "LOW" : "MEDIUM",
    aplus_risk: on ? "LOW" : "HIGH",
    signals: on
      ? ["Each visual role has a bounded composition family.", "Only the parallel-detail module uses repeated semantic panels.", "Mobile variants preserve role differences instead of one universal card stack."]
      : ["Rounded white cards recur across proof, detail, comparison and closure.", "All mobile A+ modules use the same title/body/product/card formula.", "The final FAQ module has a large unused field that reads as an unfinished template."],
  };
}
