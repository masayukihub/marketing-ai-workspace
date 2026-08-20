#!/usr/bin/env node
import fs from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";

const FIELD_CONFIG = [
  ["category", "Category", 20],
  ["product_complexity", "Product Complexity", 8],
  ["primary_usp", "Primary USP", 18],
  ["consumer_tension", "Consumer Tension", 12],
  ["product_type", "Product Type", 18],
  ["story_requirement", "Story Requirement", 10],
  ["technical_complexity", "Technical Complexity", 6],
  ["target_audience", "Target Audience", 8],
];

const PROFILE_KEYS = {
  category: "categories",
  product_complexity: "complexities",
  primary_usp: "primary_usps",
  consumer_tension: "consumer_tensions",
  product_type: "product_types",
  story_requirement: "story_requirements",
  technical_complexity: "technical_complexities",
  target_audience: "target_audiences",
};

export const MINIMUM_MATCH_SCORE = 40;

function array(value) {
  if (Array.isArray(value)) return value.flatMap(array).filter(Boolean);
  if (value === undefined || value === null || value === "") return [];
  return [String(value)];
}

function normalize(value) {
  return String(value || "")
    .normalize("NFKC")
    .toLowerCase()
    .replace(/[→↓/|,;:()[\]{}・、。\/\\_-]+/g, " ")
    .replace(/\s+/g, " ")
    .trim();
}

function tokens(value) {
  return new Set(normalize(value).split(" ").filter((item) => item.length > 1));
}

function pairSimilarity(left, right) {
  const a = normalize(left);
  const b = normalize(right);
  if (!a || !b) return 0;
  if (a === b || a.includes(b) || b.includes(a)) return 1;
  const aTokens = tokens(a);
  const bTokens = tokens(b);
  const overlap = [...aTokens].filter((item) => bTokens.has(item)).length;
  const union = new Set([...aTokens, ...bTokens]).size;
  return union ? overlap / union : 0;
}

function fieldSimilarity(values, profileValues) {
  const left = array(values);
  const right = array(profileValues);
  if (!left.length || !right.length) return { similarity: 0, matched: [], status: "missing_input" };
  const pairs = [];
  for (const input of left) {
    for (const candidate of right) pairs.push({ input, candidate, similarity: pairSimilarity(input, candidate) });
  }
  pairs.sort((a, b) => b.similarity - a.similarity || a.candidate.localeCompare(b.candidate));
  const bestByInput = left.map((input) => pairs.filter((item) => item.input === input)[0]);
  const similarity = bestByInput.reduce((sum, item) => sum + (item?.similarity || 0), 0) / left.length;
  return {
    similarity,
    matched: pairs.filter((item) => item.similarity > 0).slice(0, 3),
    status: similarity > 0 ? "matched" : "no_match",
  };
}

export function buildBriefSignals(brief) {
  const profile = brief.reference_profile || brief.reference_matching || {};
  const heroPoints = array(brief.selling_points)
    .filter((item) => typeof item === "object" && (item.tier === "HERO" || item.priority === 1))
    .flatMap((item) => [item.feature, item.benefit, item.mechanism]);
  const signals = {
    category: array(profile.category || brief.Category || brief.category || brief.product?.category),
    product_complexity: array(profile.product_complexity || brief["Product Complexity"] || brief.product_complexity),
    primary_usp: array(profile.primary_usp || brief["Primary USP"] || brief.primary_usp || [brief.core_value, ...heroPoints]),
    consumer_tension: array(profile.consumer_tension || brief["Consumer Tension"] || brief.consumer_tension || [brief.core_problem, ...(brief.objections || [])]),
    product_type: array(profile.product_type || brief["Product Type"] || brief.product_type || brief.product?.category || brief.category),
    story_requirement: array(profile.story_requirement || brief["Story Requirement"] || brief.story_requirement),
    technical_complexity: array(profile.technical_complexity || brief["Technical Complexity"] || brief.technical_complexity),
    target_audience: array(profile.target_audience || brief["Target Audience"] || brief.target_audience),
  };
  return signals;
}

export async function loadReferenceLibrary(libraryRoot) {
  const referencesRoot = path.join(libraryRoot, "references");
  const dirs = (await fs.readdir(referencesRoot, { withFileTypes: true }))
    .filter((entry) => entry.isDirectory())
    .map((entry) => entry.name)
    .sort();
  const references = [];
  for (const asin of dirs) {
    const file = path.join(referencesRoot, asin, "reference.json");
    references.push(JSON.parse(await fs.readFile(file, "utf8")));
  }
  return references;
}

function roleStrength(reference, role) {
  const story = (reference.story_patterns || []).map(normalize);
  if (role === "technology") return story.some((item) => item.includes("technology")) ? 2 : 0;
  if (role === "rhythm") {
    const density = normalize(reference.visual_patterns?.information_density);
    const whitespace = normalize(reference.visual_patterns?.whitespace);
    return (density.includes("low") || density.includes("medium") ? 1 : 0) + (whitespace.includes("generous") ? 1 : 0);
  }
  return 0;
}

function overlapsValues(left, right) {
  return array(left).some((a) => array(right).some((b) => pairSimilarity(a, b) > 0));
}

function isRobotVacuum(values) {
  return array(values).some((value) => /robot vacuum|floor[- ]?(?:cleaning|washing) robot|robot cleaner|ロボット掃除機/i.test(normalize(value)));
}

function structuralGates(signals, reference, score, minimumMatchScore = MINIMUM_MATCH_SCORE) {
  const profile = reference.matcher_profile || {};
  const targetRobotVacuum = isRobotVacuum([...signals.category, ...signals.product_type]);
  const referenceRobotVacuum = isRobotVacuum([...(profile.categories || []), ...(profile.product_types || []), reference.category]);
  const sameCategory = targetRobotVacuum
    ? referenceRobotVacuum
    : overlapsValues(signals.category, profile.categories);
  const minimumScore = Number(score) >= minimumMatchScore;
  const productRole = signals.product_type.length > 0 && overlapsValues(signals.product_type, profile.product_types);
  const pageIntent = signals.story_requirement.length > 0 && overlapsValues(signals.story_requirement, profile.story_requirements);
  return {
    same_category_gate: sameCategory ? "PASS" : "FAIL",
    minimum_match_score: minimumScore ? "PASS" : "FAIL",
    product_role_match: productRole ? "PASS" : "FAIL",
    page_intent_match: pageIntent ? "PASS" : "FAIL",
  };
}

export function matchReferences(brief, references) {
  const signals = buildBriefSignals(brief);
  const missing_fields = FIELD_CONFIG.filter(([key]) => signals[key].length === 0).map(([, label]) => label);
  const available_signal_weight = FIELD_CONFIG.filter(([key]) => signals[key].length > 0).reduce((sum, [, , weight]) => sum + weight, 0);
  const ranked = references.map((reference) => {
    const field_scores = {};
    let score = 0;
    let availableWeight = 0;
    for (const [key, label, weight] of FIELD_CONFIG) {
      const result = fieldSimilarity(signals[key], reference.matcher_profile?.[PROFILE_KEYS[key]] || []);
      const points = result.similarity * weight;
      field_scores[key] = { label, weight, points: Number(points.toFixed(2)), ...result };
      if (signals[key].length) availableWeight += weight;
      score += points;
    }
    const normalizedScore = availableWeight ? (score / availableWeight) * 100 : 0;
    return {
      rank: 0,
      asin: reference.asin,
      brand: reference.brand,
      product: reference.product,
      score: Number(normalizedScore.toFixed(1)),
      score_basis: `${availableWeight}/100 input weight available`,
      field_scores,
      why_selected: (reference.good_for || []).slice(0, 2),
      borrow: (reference.use || []).slice(0, 3),
      do_not_borrow: [...(reference.avoid || []).slice(0, 2), ...(reference.adapt || []).slice(0, 1)],
      story_patterns: reference.story_patterns || [],
    };
  }).sort((a, b) => b.score - a.score || a.asin.localeCompare(b.asin));
  ranked.forEach((item, index) => {
    item.rank = index + 1;
    const reference = references.find((candidate) => candidate.asin === item.asin);
    item.gates = structuralGates(signals, reference, item.score);
    item.structural_eligible = Object.values(item.gates).every((status) => status === "PASS");
    item.structural_decision = item.structural_eligible ? "ELIGIBLE" : "EXCLUDED";
    item.allowed_influence = item.structural_eligible
      ? ["Gallery Structure", "A+ Structure", "Module Order", "Problem Expression Inspiration", "Visual Inspiration"]
      : ["Problem Expression Inspiration", "Visual Inspiration"];
  });
  const sufficient = available_signal_weight >= 40;
  const top3 = sufficient ? ranked.slice(0, 3) : [];
  const structuralReferences = top3.filter((item) => item.structural_eligible);
  const inspirationOnlyReferences = top3.filter((item) => !item.structural_eligible);
  const topReferenceRecords = top3.map((item) => references.find((reference) => reference.asin === item.asin));
  const structuralRecords = structuralReferences.map((item) => references.find((reference) => reference.asin === item.asin));
  const technology = [...(structuralRecords.length ? structuralRecords : topReferenceRecords)].sort((a, b) => roleStrength(b, "technology") - roleStrength(a, "technology"))[0];
  const rhythm = [...topReferenceRecords].sort((a, b) => roleStrength(b, "rhythm") - roleStrength(a, "rhythm"))[0];
  const status = !sufficient ? "blocked_insufficient_brief" : structuralReferences.length ? "complete" : "blocked_no_structural_reference";
  return {
    schema_version: "2.0",
    artifact: "REFERENCE_SELECTION",
    generated_on: "2026-08-18",
    status,
    is_human_gate: false,
    principle: "Reference is a decision aid, not a source of competitor copy, imagery, trade dress or complete layouts.",
    brief_signals: signals,
    available_signal_weight,
    minimum_signal_weight: 40,
    minimum_match_score: MINIMUM_MATCH_SCORE,
    missing_fields,
    top_references: top3,
    structural_references: structuralReferences,
    inspiration_only_references: inspirationOnlyReferences,
    matcher_gates: ["Same Category", "Minimum Match Score", "Product Role Match", "Page Intent Match"],
    reference_strategy: {
      structure: structuralReferences[0] ? `${structuralReferences[0].brand} / ${structuralReferences[0].asin}` : "Not Available",
      technology_explanation: technology ? `${technology.brand} / ${technology.asin}` : "Not Available",
      visual_rhythm: rhythm ? `${rhythm.brand} / ${rhythm.asin}` : "Not Available",
      brand: "SwitchBot",
    },
    final_combination_strategy: [
      structuralReferences[0] ? `Use ${structuralReferences[0].brand} only for the dominant story architecture.` : "No structurally eligible reference available.",
      technology ? `Use ${technology.brand} only for technology-explanation discipline.` : "No technology reference available.",
      rhythm ? `Use ${rhythm.brand} only for density, whitespace and scene/technical rhythm.` : "No rhythm reference available.",
      "Use SwitchBot product truth, claims, official product assets, brand system and programmatic Japanese copy for every production output."
    ]
  };
}

function esc(value) {
  return String(value ?? "").replaceAll("|", "\\|").replaceAll("\n", " ");
}

export function renderSelectionMarkdown(selection, briefFile = "PRODUCT_BRIEF.json") {
  const signalRows = FIELD_CONFIG.map(([key, label]) => `| ${label} | ${esc(selection.brief_signals[key].join(" / ") || "Not Available")} |`).join("\n");
  const topSections = selection.top_references.map((item) => `### ${item.rank}. ${item.brand} — ${item.product} (${item.asin})\n\nScore: **${item.score}/100** (${item.score_basis})\n\nStructural decision: **${item.structural_decision}**\n\nGates: ${Object.entries(item.gates || {}).map(([name, status]) => `${name}=${status}`).join(", ")}\n\nAllowed influence: ${(item.allowed_influence || []).join(" / ")}\n\nWhy selected:\n${item.why_selected.map((line) => `- ${line}`).join("\n") || "- Not Available"}\n\nBorrow:\n${item.borrow.map((line) => `- ${line}`).join("\n") || "- Not Available"}\n\nDo not borrow:\n${item.do_not_borrow.map((line) => `- ${line}`).join("\n") || "- Not Available"}`).join("\n\n");
  return `# REFERENCE_SELECTION\n\nSource: \`${briefFile}\`\n\nStatus: ${selection.status}. This is not a human gate.\n\n> Reference does not equal copy. Competitor copy, images, trade dress and complete layouts are prohibited.\n\n## Input Signals\n\n| Matching field | Value |\n|---|---|\n${signalRows}\n\nAvailable signal weight: ${selection.available_signal_weight}/100; minimum: ${selection.minimum_signal_weight}/100. Structural minimum match score: ${selection.minimum_match_score}/100.\n\nMissing explicit fields: ${selection.missing_fields.length ? selection.missing_fields.join(", ") : "None"}. Missing fields receive no score; the matcher does not invent them.\n\n## Ranked References\n\n${topSections || "Reference selection is blocked until the Brief provides enough matching signal; Top 3 was not forced."}\n\n## Structural / Inspiration Separation\n\n- Structural references: ${selection.structural_references.map((item) => `${item.brand} ${item.asin}`).join(" / ") || "None"}\n- Inspiration only: ${selection.inspiration_only_references.map((item) => `${item.brand} ${item.asin}`).join(" / ") || "None"}\n\n## Reference Strategy\n\n| Decision layer | Reference |\n|---|---|\n| Structure | ${selection.reference_strategy.structure} |\n| Technology Explanation | ${selection.reference_strategy.technology_explanation} |\n| Visual Rhythm | ${selection.reference_strategy.visual_rhythm} |\n| Brand | ${selection.reference_strategy.brand} |\n\n## Final Combination Strategy\n\n${selection.final_combination_strategy.map((line) => `- ${line}`).join("\n")}\n`;
}

export async function writeReferenceSelection(brief, outputDir, libraryRoot, briefFile = "PRODUCT_BRIEF.json") {
  const references = await loadReferenceLibrary(libraryRoot);
  const selection = matchReferences(brief, references);
  const targetDir = path.join(outputDir, "reference");
  await fs.mkdir(targetDir, { recursive: true });
  await fs.writeFile(path.join(targetDir, "REFERENCE_SELECTION.json"), `${JSON.stringify(selection, null, 2)}\n`, "utf8");
  await fs.writeFile(path.join(targetDir, "REFERENCE_SELECTION.md"), renderSelectionMarkdown(selection, briefFile), "utf8");
  return selection;
}

function parseArgs(argv) {
  const args = {};
  for (let index = 2; index < argv.length; index += 1) {
    const item = argv[index];
    if (!item.startsWith("--")) continue;
    const key = item.slice(2);
    const value = argv[index + 1];
    args[key] = value && !value.startsWith("--") ? argv[++index] : true;
  }
  return args;
}

if (process.argv[1] && path.resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  const args = parseArgs(process.argv);
  if (!args.brief || !args.output) {
    console.error("Usage: node scripts/reference_matcher.mjs --brief <PRODUCT_BRIEF.json> --output <dir> [--library <reference-library>]");
    process.exit(2);
  }
  const skillDir = path.dirname(path.dirname(fileURLToPath(import.meta.url)));
  const libraryRoot = path.resolve(args.library || path.join(skillDir, "reference-library"));
  const briefFile = path.resolve(args.brief);
  const brief = JSON.parse(await fs.readFile(briefFile, "utf8"));
  const selection = await writeReferenceSelection(brief, path.resolve(args.output), libraryRoot, args.brief);
  console.log(JSON.stringify({ status: "complete", top_references: selection.top_references.map(({ rank, asin, brand, score }) => ({ rank, asin, brand, score })), output: path.join(path.resolve(args.output), "reference", "REFERENCE_SELECTION.md") }, null, 2));
}
