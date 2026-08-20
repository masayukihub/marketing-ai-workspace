import crypto from "node:crypto";
import fs from "node:fs/promises";
import path from "node:path";
import { refreshSpec, validateSpec } from "./spec_system.mjs";
import { assertRendererCoverage, rendererCapability } from "./renderer_registry.mjs";
import { assertStoryMutationAllowed } from "./story_sequence_lock.mjs";

const clone = (value) => JSON.parse(JSON.stringify(value));
const readJson = async (file) => JSON.parse(await fs.readFile(file, "utf8"));
const hash = (value) => crypto.createHash("sha256").update(JSON.stringify(value)).digest("hex");

function normalizedText(value) {
  return String(value || "").normalize("NFKC").toLowerCase();
}

function words(values) {
  return (Array.isArray(values) ? values : [values])
    .flatMap((value) => normalizedText(value).split(/[^\p{L}\p{N}]+/u))
    .filter((value) => value.length > 1);
}

function patternScore(record, eligibleScores, briefSignals, type) {
  const referenceScore = (record.reference_asins || []).reduce((sum, asin) => sum + (eligibleScores.get(asin) || 0) / 5, 0);
  const bestForFit = (record.best_for || []).reduce((sum, value) => sum + (words(value).some((word) => briefSignals.includes(word)) ? 2 : 0), 0);
  const storyFit = type === "story" && normalizedText(record.name).includes("performance") && briefSignals.includes("performance") ? 3 : 0;
  return referenceScore + bestForFit + storyFit;
}

function choosePattern(records, eligibleScores, briefSignals, type) {
  return records
    .map((record) => ({ record, score: patternScore(record, eligibleScores, briefSignals, type) }))
    .sort((a, b) => b.score - a.score || String(a.record.sequence_id || a.record.pattern_id).localeCompare(String(b.record.sequence_id || b.record.pattern_id)))[0];
}

function roleVisualRoles(role) {
  const value = normalizedText(role);
  if (/official|hero|audience problem|japan fit hero|value hero|category hero|system hero/.test(value)) return ["Hero"];
  if (/mechanism|technology concept|what it does|transformation/.test(value)) return ["Technology", "Feature"];
  if (/performance|proof|failure-point|core proof|measured|observable/.test(value)) return ["Proof", "Technology"];
  if (/scenario|environment|relief|daily fit|human-use|real home|outcome/.test(value)) return ["Scenario", "Feature", "Detail"];
  if (/maintenance|ownership effort|desired-life/.test(value)) return ["Closure", "Comparison", "Scenario"];
  if (/comparison|model|fit and conditions|confidence|support|installation/.test(value)) return ["Comparison", "Closure", "Detail"];
  if (/faq|condition|trust|privacy/.test(value)) return ["Closure", "Detail", "Proof"];
  if (/control|ecosystem|compatibility/.test(value)) return ["Technology", "Detail"];
  return ["Feature", "Detail"];
}

function productTemplateForRole(role, index) {
  const value = normalizedText(role);
  if (index === 0 || /official main/.test(value)) return "P-MAIN-OFFICIAL";
  if (index === 6 || /support and purchase confidence|fit and conditions|desired-life closure/.test(value)) return "P-PURCHASE-CONFIDENCE";
  if (/ecosystem|compatibility/.test(value)) return "P-ECOSYSTEM";
  if (/performance proof|failure-point|core proof|mechanism proof|transformation/.test(value)) return "P-TECHNICAL-PROOF";
  if (/scenario|environment fit|relief|real home|tangible outcome|daily safety/.test(value)) return "P-LIFESTYLE-FULL";
  if (/comparison|ownership effort|installation or ecosystem fit/.test(value)) return "P-COMPARISON";
  if (/mechanism|what it does/.test(value)) return "P-FEATURE-SPLIT";
  if (/hero|problem|audience|core value/.test(value)) return "P-HERO-SPLIT";
  return "P-FEATURE-CENTER";
}

function aplusTemplateForRole(role) {
  const value = normalizedText(role);
  if (/hero/.test(value)) return "A-HERO";
  if (/core mechanism|primary mechanism|technology concept|transformation mechanism/.test(value)) return "A-50-50-FEATURE";
  if (/performance proof|mechanism proof|measured|technology/.test(value)) return "A-TECHNICAL";
  if (/environment adaptation|daily fit|installation and size/.test(value)) return "A-THREE-FEATURE-GRID";
  if (/maintenance|scenario|relief|human-use|desired-life/.test(value)) return "A-LIFESTYLE";
  if (/control|ecosystem|compatibility/.test(value)) return "A-ECOSYSTEM";
  if (/comparison|model/.test(value)) return "A-COMPARISON";
  if (/faq|condition|trust|privacy|support/.test(value)) return "A-FAQ";
  return "A-50-50-FEATURE";
}

const CONTENT_KEYWORDS = Object.freeze({
  hero: ["define", "system", "value", "compact", "category", "製品", "小型", "価値"],
  mechanism: ["mechanism", "roller", "differentiation", "mechanical", "structure", "仕組み", "構造", "ローラー", "給水", "汚水"],
  performance: ["performance", "proof", "suction", "navigation", "sensor", "mess", "result", "吸引", "センサー", "毛", "食べこぼし", "効果"],
  environment: ["environment", "fit", "dimension", "dining", "carpet", "home", "furniture", "家具", "住まい", "カーペット", "幅", "旋回"],
  maintenance: ["maintenance", "boundary", "station", "closeout", "after", "集じん", "洗浄", "乾燥", "手入れ", "掃除後"],
  comparison: ["comparison", "variant", "water route", "tank", "installation", "sku", "contents", "給排水", "水箱", "設置", "同梱", "セット"],
  closure: ["faq", "condition", "support", "privacy", "sku", "contents", "closure", "同梱", "確認", "条件", "購入前", "正式"],
});

function roleKeywordGroup(role) {
  const value = normalizedText(role);
  if (/hero|audience problem|category/.test(value)) return "hero";
  if (/mechanism|technology|what it does|transformation/.test(value)) return "mechanism";
  if (/performance|proof|failure/.test(value)) return "performance";
  if (/environment|scenario|daily fit|real home|relief/.test(value)) return "environment";
  if (/maintenance|ownership effort/.test(value)) return "maintenance";
  if (/comparison|model|installation|fit and conditions/.test(value)) return "comparison";
  return "closure";
}

function contentScore(record, role) {
  const haystack = normalizedText([record.purpose, record.user_question, record.headline, record.copy, record.role, record.sub_copy, ...(record.claim_ids || [])].filter(Boolean).join(" "));
  const purpose = normalizedText(record.purpose);
  const group = roleKeywordGroup(role);
  return (CONTENT_KEYWORDS[group] || []).reduce((score, keyword) => {
    const normalized = normalizedText(keyword);
    return score + (purpose.includes(normalized) ? 5 : 0) + (haystack.includes(normalized) ? 2 : 0);
  }, 0);
}

function claimProvenance(record, claims) {
  const claimIds = record.claim_ids || record.units?.flatMap((unit) => unit.claim_ids || []) || [];
  const byId = new Map((claims || []).map((claim) => [claim.id, claim]));
  const missing = [...new Set(claimIds)].filter((id) => {
    const claim = byId.get(id);
    const sourceId = claim?.source_id || claim?.sourceId;
    const sourceLocation = claim?.source_url || claim?.sourceUrl || claim?.source_path || claim?.sourcePath || claim?.source;
    return !claim || !sourceId || !sourceLocation;
  });
  return { status: missing.length ? "FAIL" : "PASS", missing };
}

function roleGate(templateId, requiredRoles, primitiveMap) {
  const mapping = primitiveMap.mappings.find((item) => item.template_id === templateId);
  const supported = [mapping?.primary_role, ...(mapping?.secondary_roles || [])].filter(Boolean);
  const pass = requiredRoles.some((role) => supported.includes(role));
  return { status: pass ? "PASS" : "FAIL", supported_roles: supported, required_roles: requiredRoles };
}

function evaluateCandidate(record, templateId, requiredRoles, primitiveMap, claims) {
  const role = roleGate(templateId, requiredRoles, primitiveMap);
  const renderer = rendererCapability(templateId);
  const provenance = claimProvenance(record, claims);
  const gates = {
    A_role_match: role.status,
    B_renderer_availability: renderer.renderer_available ? "PASS" : "FAIL",
    C_mobile_readability: renderer.renderer_available && Boolean(renderer.mobile_layout) ? "PASS" : "FAIL",
    D_claim_provenance: provenance.status,
  };
  return { gates, pass: Object.values(gates).every((value) => value === "PASS"), role, renderer: renderer.implementation, provenance };
}

function setTemplate(record, templateId, templateById) {
  record.template_id = templateId;
  record.template_snapshot = clone(templateById.get(templateId));
}

function enrichGalleryFromUnit(image, unit) {
  if (!unit) return image;
  return {
    ...image,
    user_question: unit.user_question || image.user_question,
    headline: unit.headline || image.headline,
    sub_copy: unit.copy || image.sub_copy,
    key_message: unit.copy || image.key_message,
    claim_ids: clone(unit.claim_ids || image.claim_ids || []),
    claim_sources: clone(unit.claim_sources || image.claim_sources || []),
    claim_source: unit.claim_source || image.claim_source,
    risk: unit.risk || image.risk,
    layers: clone(unit.layers || image.layers),
    asset_resolution: clone(unit.asset_resolution || image.asset_resolution),
    source_origin: unit.source_origin || image.source_origin,
    source_asset_type: unit.source_asset_type || image.source_asset_type,
    product_body_ai_generated: unit.product_body_ai_generated ?? image.product_body_ai_generated,
  };
}

function selectBestUnit(units, role) {
  return units.map((unit, index) => ({ unit, index, score: contentScore(unit, role) }))
    .sort((a, b) => b.score - a.score || a.index - b.index)[0]?.unit;
}

function allocateCapacities(total, count) {
  if (total === 16 && count === 7) return [2, 2, 3, 3, 2, 3, 1];
  const capacities = Array.from({ length: count }, () => 1);
  let remaining = Math.max(0, total - count);
  const order = [2, 3, 4, 5, 1, 6, 0];
  while (remaining > 0) {
    for (const index of order) {
      if (remaining <= 0) break;
      capacities[index % count] += 1;
      remaining -= 1;
    }
  }
  return capacities;
}

function sevenModuleRoles(modules) {
  const result = [...modules];
  while (result.length > 7) {
    const removable = result.findIndex((role, index) => index > 0 && index < result.length - 2 && /control|ecosystem|compatibility/i.test(role));
    result.splice(removable >= 0 ? removable : result.length - 3, 1);
  }
  return result;
}

function normalizedPlan(spec) {
  return { strategy: spec.strategy, journey: spec.journey, product_images: spec.product_images, aplus_modules: spec.aplus_modules };
}

export async function adaptReferencePlan({ baselineSpec, brief, selection, templateLibrary, referenceLibraryRoot }) {
  if (selection.status !== "complete" || !(selection.structural_references || []).length) throw new Error("Reference Decision Adapter blocked: no structurally eligible Reference.");
  assertStoryMutationAllowed(baselineSpec, "REORDER");
  const [galleryLibrary, aplusLibrary, storyLibrary, primitiveMap] = await Promise.all([
    readJson(path.join(referenceLibraryRoot, "patterns", "gallery_sequence_library.json")),
    readJson(path.join(referenceLibraryRoot, "patterns", "aplus_sequence_library.json")),
    readJson(path.join(referenceLibraryRoot, "patterns", "story_pattern_library.json")),
    readJson(path.join(referenceLibraryRoot, "layout", "layout_primitive_mapping.json")),
  ]);
  const eligibleScores = new Map(selection.structural_references.map((candidate) => [candidate.asin, candidate.score]));
  const briefSignals = words(Object.values(brief.reference_profile || brief.reference_matching || {}).flat());
  const story = choosePattern(storyLibrary.patterns, eligibleScores, briefSignals, "story");
  const gallery = choosePattern(galleryLibrary.sequences, eligibleScores, briefSignals, "gallery");
  const aplus = choosePattern(aplusLibrary.sequences, eligibleScores, briefSignals, "aplus");
  const spec = clone(baselineSpec);
  const baselineHash = hash(normalizedPlan(baselineSpec));
  const templateById = new Map(templateLibrary.templates.map((template) => [template.template_id, template]));
  const allUnits = baselineSpec.aplus_modules.flatMap((module) => module.units || []).map(clone);
  const traces = [];
  const referenceSources = selection.structural_references.map(({ asin, brand, score }) => ({ asin, brand, score }));

  const galleryRoles = gallery.record.roles;
  spec.product_images = baselineSpec.product_images.map((original, index) => {
    const role = galleryRoles[index] || original.role;
    const templateId = productTemplateForRole(role, index);
    let record = clone(original);
    if (index > 1 && index < 6) record = enrichGalleryFromUnit(record, selectBestUnit(allUnits, role));
    record.role = role;
    setTemplate(record, templateId, templateById);
    const evaluation = evaluateCandidate(record, templateId, roleVisualRoles(role), primitiveMap, spec.claims);
    const trace = {
      visual_id: record.id,
      family: "Gallery",
      consumer_question: record.user_question,
      story_role: role,
      reference_source: referenceSources,
      selected_reference_pattern: gallery.record.sequence_id,
      reference_role: role,
      learned_principle: gallery.record.logic,
      switchbot_adaptation: "Reordered only source-backed SwitchBot copy, Claims and official product layers for this decision role.",
      primitive: templateId,
      why_layout_was_chosen: `${templateId} supports ${roleVisualRoles(role).join(" / ")} while preserving the registered Primitive boundary.`,
      decision_reason: `Answer ${record.user_question || "the next consumer question"} with the ${role} role using a renderer-backed SwitchBot Primitive.`,
      intentionally_not_copied: "Competitor copy, images, logos, UI, trade dress and complete layout were not copied.",
      ...evaluation,
      final_plan_decision: evaluation.pass ? "ACCEPTED" : "REJECTED",
    };
    traces.push(trace);
    if (!evaluation.pass) throw new Error(`Reference Decision Adapter rejected ${record.id}: ${JSON.stringify(evaluation.gates)}`);
    record.reference_decision = clone(trace);
    return record;
  });

  const targetRoles = sevenModuleRoles(aplus.record.modules);
  const capacities = allocateCapacities(allUnits.length, targetRoles.length);
  const unused = allUnits.map((unit, index) => ({ unit, index }));
  const assignments = new Map();
  const allocationOrder = targetRoles.map((role, index) => ({ role, index, group: roleKeywordGroup(role) })).sort((a, b) => {
    const priority = { closure: 0, maintenance: 1, mechanism: 2, hero: 3, performance: 4, comparison: 5, environment: 6 };
    return (priority[a.group] ?? 9) - (priority[b.group] ?? 9) || a.index - b.index;
  });
  for (const target of allocationOrder) {
    const ranked = unused.map((entry) => ({ ...entry, score: contentScore(entry.unit, target.role) })).sort((a, b) => b.score - a.score || a.index - b.index);
    const selected = ranked.slice(0, capacities[target.index]);
    const selectedIndexes = new Set(selected.map((entry) => entry.index));
    assignments.set(target.index, selected.sort((a, b) => a.index - b.index).map((entry) => clone(entry.unit)));
    for (let cursor = unused.length - 1; cursor >= 0; cursor -= 1) if (selectedIndexes.has(unused[cursor].index)) unused.splice(cursor, 1);
  }
  spec.aplus_modules = targetRoles.map((role, index) => {
    const units = assignments.get(index) || [];
    const originalSlot = baselineSpec.aplus_modules[index];
    const templateId = aplusTemplateForRole(role);
    const module = {
      ...clone(originalSlot),
      id: originalSlot.id,
      sequence: index + 1,
      story_role: role,
      module_headline: units[0]?.headline || originalSlot.module_headline,
      units,
      outputs: clone(originalSlot.outputs),
    };
    setTemplate(module, templateId, templateById);
    const evaluation = evaluateCandidate(module, templateId, roleVisualRoles(role), primitiveMap, spec.claims);
    const trace = {
      visual_id: module.id,
      unit_ids: units.map((unit) => unit.id),
      family: "A+",
      consumer_question: units.map((unit) => unit.user_question).filter(Boolean).join(" / "),
      story_role: role,
      reference_source: referenceSources,
      selected_reference_pattern: aplus.record.sequence_id,
      reference_role: role,
      learned_principle: aplus.record.rhythm,
      switchbot_adaptation: "Grouped existing source-backed SwitchBot units around one consumer decision; module and unit counts remain fixed.",
      primitive: templateId,
      why_layout_was_chosen: `${templateId} supports ${roleVisualRoles(role).join(" / ")} and has deterministic Desktop/Mobile renderers.`,
      decision_reason: `Continue the A+ purchase story with ${role} while keeping the approved unit count and renderer constraints.`,
      intentionally_not_copied: "Competitor module copy, imagery, exact order, UI and complete layout were not copied.",
      ...evaluation,
      final_plan_decision: evaluation.pass ? "ACCEPTED" : "REJECTED",
    };
    traces.push(trace);
    if (!evaluation.pass) throw new Error(`Reference Decision Adapter rejected ${module.id}: ${JSON.stringify(evaluation.gates)}`);
    module.reference_decision = clone(trace);
    module.units = module.units.map((unit) => ({ ...unit, reference_decision: clone(trace) }));
    return module;
  });

  assertRendererCoverage([...spec.product_images.map((item) => item.template_id), ...spec.aplus_modules.map((module) => module.template_id)]);
  spec.reference_application = {
    mode: "ON",
    adapter: "Reference Decision Adapter V2",
    selected_story_pattern: story.record.pattern_id,
    selected_gallery_sequence: gallery.record.sequence_id,
    selected_aplus_sequence: aplus.record.sequence_id,
    structural_references: referenceSources,
    inspiration_only_references: (selection.inspiration_only_references || []).map(({ asin, brand, score }) => ({ asin, brand, score })),
    gates_required: ["Role Match", "Renderer Availability", "Mobile Readability", "Claim Provenance"],
    plan_changed: false,
  };
  spec.reference_application.plan_changed = baselineHash !== hash(normalizedPlan(spec));
  if (!spec.reference_application.plan_changed) throw new Error("Reference Decision Adapter under-utilization: PLAN did not change.");
  refreshSpec(spec, templateLibrary);
  const errors = validateSpec(spec, templateLibrary);
  if (errors.length) throw new Error(`Adapted Spec invalid: ${errors.join("; ")}`);
  return { spec, traces, patterns: { story, gallery, aplus } };
}

export function referenceTraceMarkdown({ traces, selection, patterns }) {
  const matcherRows = (selection.top_references || []).map((item) => `| ${item.brand} ${item.asin} | ${item.score} | ${item.gates.same_category_gate} | ${item.gates.minimum_match_score} | ${item.gates.product_role_match} | ${item.gates.page_intent_match} | ${item.structural_decision} | ${(item.allowed_influence || []).join(" / ")} |`).join("\n");
  const decisionRows = traces.map((item) => `| ${item.visual_id} | ${item.reference_source.map((source) => `${source.brand} ${source.asin}`).join(" + ")} | ${item.selected_reference_pattern} | ${item.primitive} | ${item.gates.A_role_match} | ${item.gates.B_renderer_availability} | ${item.gates.C_mobile_readability} | ${item.gates.D_claim_provenance} | ${item.final_plan_decision} |`).join("\n");
  const details = traces.map((item) => `### ${item.visual_id}\n\n- Consumer Question: ${item.consumer_question || "Not Available"}\n- Story Role: ${item.story_role}\n- Reference Source: ${item.reference_source.map((source) => `${source.brand} ${source.asin}`).join(" + ")}\n- Learned Principle: ${item.learned_principle}\n- SwitchBot Adaptation: ${item.switchbot_adaptation}\n- Layout Decision: ${item.primitive} — ${item.why_layout_was_chosen}\n- Intentionally Not Copied: ${item.intentionally_not_copied}\n- Final Decision: ${item.final_plan_decision}`).join("\n\n");
  return `# REFERENCE_DECISION_TRACE_V2\n\n## Matcher Threshold\n\n| Reference | Score | Same Category | Min Score | Product Role | Page Intent | Structural Decision | Allowed Influence |\n|---|---:|---|---|---|---|---|---|\n${matcherRows}\n\n## Selected Patterns\n\n- Story: \`${patterns.story.record.pattern_id}\`\n- Gallery: \`${patterns.gallery.record.sequence_id}\`\n- A+: \`${patterns.aplus.record.sequence_id}\`\n\n## Reference → Pattern → Primitive → Gate → Final Plan\n\n| Visual | Structural Reference | Pattern | Primitive | Gate A Role | Gate B Renderer | Gate C Mobile | Gate D Claim | Decision |\n|---|---|---|---|---|---|---|---|---|\n${decisionRows}\n\n## Decision Detail\n\n${details}\n\n## Non-copy Boundary\n\nCompetitor copy, images, trade dress, UI, logos and complete layouts were not used. Only decision order, explanation discipline and rhythm principles entered PLAN.\n`;
}
