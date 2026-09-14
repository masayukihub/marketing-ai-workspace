import crypto from "node:crypto";
import fs from "node:fs/promises";
import path from "node:path";
import { normalizeCreativeSystem } from "./visual_pipeline.mjs";
import { ASSET_SOURCE_TYPES, assetProvenanceFailures, buildAssetProvenance } from "./asset_provenance.mjs";
import { assertStorySequenceIntegrity } from "./story_sequence_lock.mjs";

export const STAGES = [
  ["understand_product", "理解产品", "これは何？"],
  ["spark_interest", "产生兴趣", "なぜ気になる？"],
  ["understand_advantage", "理解核心优势", "なぜ使いやすい？"],
  ["see_real_scenario", "看到真实场景", "暮らしでどう使う？"],
  ["build_trust", "相信产品", "何を根拠に信じる？"],
  ["check_fit", "判断适不适合自己", "自分の環境に合う？"],
  ["remove_objections", "消除购买顾虑", "買う前の不安は？"],
];

export const PRODUCT_TEMPLATE_SEQUENCE = [
  "P-MAIN-OFFICIAL",
  "P-HERO-SPLIT",
  "P-FEATURE-CENTER",
  "P-LIFESTYLE-FULL",
  "P-TECHNICAL-PROOF",
  "P-COMPARISON",
  "P-PURCHASE-CONFIDENCE",
];

export const APLUS_TEMPLATE_SEQUENCE = [
  "A-HERO",
  "A-50-50-FEATURE",
  "A-THREE-FEATURE-GRID",
  "A-LIFESTYLE",
  "A-TECHNICAL",
  "A-COMPARISON",
  "A-FAQ",
];

const USER_OFFICIAL_ORIGIN = "User Provided Official";
const OFFICIAL_TYPES = new Set([
  "Official White Background",
  "Official PNG",
  "Official Render",
  "Official Lifestyle",
  "Official Installation",
  "Official Detail",
]);

function clone(value) {
  return JSON.parse(JSON.stringify(value));
}

function safeName(value) {
  return String(value || "asset").replace(/[^a-zA-Z0-9._-]+/g, "-").replace(/-+/g, "-").replace(/^-|-$/g, "");
}

function isUrl(value) {
  return /^https?:\/\//i.test(String(value || ""));
}

async function exists(file) {
  try {
    await fs.access(file);
    return true;
  } catch {
    return false;
  }
}

async function sha256File(file) {
  return crypto.createHash("sha256").update(await fs.readFile(file)).digest("hex");
}

function canonicalForHash(spec) {
  const value = clone(spec);
  value.meta.spec_sha256 = "";
  // Publication evidence and calculated gates are derived state. Excluding them
  // keeps the content hash stable when browser QA is attached to the same Spec.
  delete value.quality_evidence;
  delete value.publish_gate;
  return JSON.stringify(value);
}

export function computeSpecHash(spec) {
  return crypto.createHash("sha256").update(canonicalForHash(spec)).digest("hex");
}

function templateIndex(library) {
  return new Map((library.templates || []).map((item) => [item.template_id, item]));
}

function looksLifestyle(value, type = "") {
  return type === "Official Lifestyle" || /(?:lifestyle|scene|install|room|home|weather|party)/i.test(String(value || ""));
}

function sourceMeta(record, data) {
  return {
    source_origin: record.sourceOrigin || record.productSourceOrigin || data.product.mainImageOrigin || data.meta.productAssetOrigin || "Unknown",
    source_asset_type: record.sourceAssetType || record.productSourceType || data.product.mainImageType || "Unknown",
    product_body_ai_generated: record.productBodyAiGenerated ?? data.product.productBodyAiGenerated ?? null,
    ai_generated_elements: record.aiGeneratedElements || [],
    verification_status: record.verificationStatus || record.sourceVerificationStatus || "unverified",
    usage_approved: record.usageApproved === true,
  };
}

export function normalizeRating(value) {
  if (!value || typeof value !== "object" || Array.isArray(value)) {
    return { value: null, count: null, source: null, source_type: null, status: "unavailable" };
  }
  const hasValue = value.value !== null && value.value !== undefined && value.value !== "";
  const hasCount = value.count !== null && value.count !== undefined && value.count !== "";
  const numericValue = hasValue ? Number(value.value) : Number.NaN;
  const numericCount = hasCount ? Number(value.count) : Number.NaN;
  return {
    value: Number.isFinite(numericValue) && numericValue >= 0 && numericValue <= 5 ? numericValue : null,
    count: Number.isInteger(numericCount) && numericCount >= 0 ? numericCount : null,
    source: value.source || null,
    source_type: value.source_type || value.sourceType || null,
    status: String(value.status || "unavailable").toLowerCase(),
  };
}

function copyReviewStatus(data) {
  const records = [
    ...(data.images || []).filter((item) => item.id !== "IMAGE-01"),
    ...(data.aplusModules || []).flatMap((module) => module.units || []),
  ];
  return records.every((item) => ["Reviewed", "Human Approved", "Approved"].includes(item.copyReview?.status));
}

async function createAssetLocalizer(inputFile, outputDir) {
  const inputDir = path.dirname(path.resolve(inputFile));
  const targetDir = path.join(outputDir, "design", "assets");
  await fs.mkdir(targetDir, { recursive: true });
  const localized = new Map();
  const names = new Map();
  let collision = 1;
  return async function localize(source) {
    if (!source || isUrl(source)) return { original: source || "", path: source || "", exists: Boolean(source), sha256: "" };
    const absolute = path.isAbsolute(source) ? source : path.resolve(inputDir, source);
    if (localized.has(absolute)) return localized.get(absolute);
    if (!(await exists(absolute))) {
      const missing = { original: source, path: source, exists: false, sha256: "" };
      localized.set(absolute, missing);
      return missing;
    }
    const parsed = path.parse(absolute);
    let filename = safeName(`${parsed.name}${parsed.ext}`);
    while (names.has(filename) && names.get(filename) !== absolute) filename = safeName(`${parsed.name}-${collision++}${parsed.ext}`);
    names.set(filename, absolute);
    const target = path.join(targetDir, filename);
    await fs.copyFile(absolute, target);
    const result = {
      original: source,
      path: `design/assets/${filename}`,
      exists: true,
      sha256: await sha256File(target),
    };
    localized.set(absolute, result);
    return result;
  };
}

function defaultApproval(gate, gateMode, inputGate) {
  if (inputGate?.status) return clone(inputGate);
  if (gateMode === "internal-test") {
    return {
      status: "Approved — Internal QA",
      approved_by: "Codex internal QA fixture run",
      approved_on: "2026-08-18",
      scope: "Template/render regression only; not a formal business, legal or publication approval",
    };
  }
  return {
    status: "Pending Review",
    approved_by: "",
    approved_on: "",
    scope: gate === "story" ? "Hero, 7-image story, A+ story, final headlines and hierarchy" : "Final templates, layout, product placement and placeholder-scene composition",
  };
}

function layerRules(productPath, scenePath, sceneContainsOfficialProduct) {
  return {
    product_layer: {
      source: productPath,
      rule: "Official product asset only. Never AI-generate, redraw, inpaint or alter the product body, logo, screen, buttons, ports or accessories.",
    },
    scene_layer: {
      source: scenePath,
      contains_official_product: sceneContainsOfficialProduct,
      allowed_origins: ["Official", "Authorized", "AI scene without product", "Placeholder"],
    },
    graphic_layer: {
      renderer: "Programmatic HTML/CSS/SVG",
      contains: ["Japanese headline", "sub copy", "proof labels", "comparison", "technical labels"],
      ai_generated: false,
    },
  };
}

function claimSources(record, data) {
  const byId = new Map((data.claims || []).map((claim) => [claim.id, claim]));
  return (record.claimIds || []).map((id) => {
    const claim = byId.get(id) || {};
    return {
      claim_id: id,
      status: claim.status || "Need Verification",
      source_id: claim.sourceId || "",
      source_url: claim.sourceUrl || "",
      conditions: claim.conditions || "",
    };
  });
}

function decideAssetResolution(recordId, meta, productAsset, sceneAsset, sceneContainsOfficialProduct) {
  const productProvenance = buildAssetProvenance({ asset: productAsset, meta, layer: "product" });
  const sceneProvenance = buildAssetProvenance({ asset: sceneAsset, meta, layer: "scene", containsOfficialProduct: sceneContainsOfficialProduct });
  const officialProduct = productProvenance.file_resolved && productProvenance.source_verified;
  const officialScene = sceneProvenance.file_resolved && sceneProvenance.source_verified;
  const missing = [];
  if (!productProvenance.file_resolved) missing.push("official product asset");
  if (!sceneProvenance.file_resolved && recordId !== "IMAGE-01") missing.push("scene/background if template requires it");
  let resolution = "Placeholder — not official or verified";
  if (officialScene) resolution = "Official scene image";
  else if (sceneProvenance.source_type === "generated_scene" && sceneProvenance.scene_layer_allowed) resolution = "Generated scene — Scene Layer only";
  else if (sceneProvenance.source_type === "external_reference") resolution = "External reference — analysis only";
  else if (officialProduct) resolution = "Official white background/render + programmatic composition";
  else if (productProvenance.file_resolved) resolution = `${productProvenance.source_type} asset — verification required`;
  const authorizationStatus = productProvenance.product_layer_allowed
    ? "Product Layer Approved"
    : `${productProvenance.verification_status}; Product Layer Not Approved`;
  return {
    visual_id: recordId,
    official_scene_available: officialScene,
    official_product_available: officialProduct,
    ai_background_needed: !officialScene && recordId !== "IMAGE-01",
    network_reference_needed: false,
    composite_needed: recordId !== "IMAGE-01" && !sceneContainsOfficialProduct,
    scene_contains_official_product: sceneContainsOfficialProduct,
    missing_assets: missing,
    priority_order: ["Official scene", "Official white background/render", "Authorized material", "AI scene without product", "Placeholder"],
    selected_resolution: resolution,
    authorization_status: authorizationStatus,
    product_asset: productAsset.path,
    scene_asset: sceneAsset.path,
    source_type: productProvenance.source_type,
    source_path: productProvenance.source_path,
    verification_status: productProvenance.verification_status,
    product_layer_allowed: productProvenance.product_layer_allowed,
    resolved: productProvenance.resolved,
    file_resolved: productProvenance.file_resolved,
    source_verified: productProvenance.source_verified,
    usage_approved: productProvenance.usage_approved,
    product_provenance: productProvenance,
    scene_provenance: sceneProvenance,
    status: !productProvenance.file_resolved
      ? "Missing Asset"
      : productProvenance.usage_approved && !missing.length
        ? "File Resolved"
        : "File Resolved — Verification Required",
  };
}

function buildPublishGate(spec, library) {
  const visualRecords = [
    ...spec.product_images,
    ...spec.aplus_modules.flatMap((module) => module.units),
  ];
  const templateIds = new Set((library.templates || []).map((template) => template.template_id));
  const productAccuracyFailures = visualRecords.filter((record) => record.product_body_ai_generated !== false || record.source_origin !== USER_OFFICIAL_ORIGIN || !OFFICIAL_TYPES.has(record.source_asset_type));
  const usedClaims = new Set([
    ...spec.bullets.flatMap((item) => item.claimIds || []),
    ...visualRecords.flatMap((item) => item.claim_ids || []),
    ...spec.faq.flatMap((item) => item.claimIds || []),
  ]);
  const claimMap = new Map(spec.claims.map((claim) => [claim.id, claim]));
  const claimFailures = [...usedClaims].filter((id) => claimMap.get(id)?.status !== "Approved");
  const copyPass = spec.copy_review.status === "Pass";
  const layoutFailures = [
    ...spec.product_images.filter((item) => !templateIds.has(item.template_id)),
    ...spec.aplus_modules.filter((item) => !templateIds.has(item.template_id)),
  ];
  const assetFailures = spec.asset_resolution_plan.records.filter((item) => {
    const productFailures = assetProvenanceFailures(item);
    const sceneUnsafe = item.scene_provenance?.file_resolved && !item.scene_provenance?.usage_approved;
    return productFailures.length || sceneUnsafe || (item.missing_assets || []).length;
  });
  const visualConsistencyPass = layoutFailures.length === 0 && spec.product_images.length === 7 && spec.aplus_modules.length >= 5 && spec.aplus_modules.length <= 8;
  const sections = {
    product_accuracy: {
      status: productAccuracyFailures.length ? "Blocked" : "Pass",
      requirement: "Every product body is traced to a user-provided official asset and productBodyAiGenerated=false.",
      failures: productAccuracyFailures.map((item) => item.id),
    },
    claim: {
      status: claimFailures.length || spec.meta.module_availability !== "Confirmed" ? "Blocked" : "Pass",
      requirement: "Every core Claim is Approved for JP/current SKU/current channel and A+ module availability is confirmed.",
      failures: [...claimFailures, ...(spec.meta.module_availability !== "Confirmed" ? ["A+ module availability"] : [])],
    },
    copy: {
      status: copyPass ? "Pass" : "Blocked",
      requirement: "All consumer copy passed Japan Localization Review.",
      failures: copyPass ? [] : [spec.copy_review.status],
    },
    layout: {
      status: layoutFailures.length ? "Blocked" : "Pass",
      requirement: "Every visual unit uses a registered formal template_id.",
      failures: layoutFailures.map((item) => item.id),
    },
    mobile: {
      status: spec.quality_evidence?.mobile?.status === "Pass" ? "Pass" : "Pending Browser QA",
      requirement: "Consumer and review pages are readable at 390px; browser evidence is required.",
      failures: spec.quality_evidence?.mobile?.status === "Pass" ? [] : ["390px browser QA not yet attached at Spec-build time"],
    },
    asset: {
      status: assetFailures.length ? "Blocked" : "Pass",
      requirement: "No fixture, temporary, unlicensed or placeholder asset enters Final.",
      failures: assetFailures.map((item) => item.visual_id),
    },
    visual_consistency: {
      status: visualConsistencyPass ? "Pass" : "Blocked",
      requirement: "SwitchBot Japan Amazon visual grammar and one-template-per-unit constraints pass.",
      failures: visualConsistencyPass ? [] : ["Template sequence or module count mismatch"],
    },
  };
  const reasons = Object.entries(sections).filter(([, section]) => section.status !== "Pass").map(([id, section]) => `${id}: ${section.failures.join(", ")}`);
  return { status: reasons.length ? "BLOCKED" : "PASS", sections, reasons };
}

function compactCopyDeck(spec) {
  return {
    schema_version: "1.0",
    derived_from: "PRODUCT_PAGE_SPEC.json",
    spec_sha256: spec.meta.spec_sha256,
    title: spec.titles,
    bullets: spec.bullets,
    product_images: spec.product_images.map((item) => ({ id: item.id, headline: item.headline, sub_copy: item.sub_copy, template_id: item.template_id })),
    aplus: spec.aplus_modules.map((module) => ({ id: module.id, template_id: module.template_id, units: module.units.map((unit) => ({ id: unit.id, headline: unit.headline, copy: unit.copy })) })),
    faq: spec.faq,
  };
}

function normalizeStatus(value, fallback = "Need Verification") {
  const status = String(value || fallback);
  return status || fallback;
}

function sellingPointRows(data) {
  const strategy = data.strategy || {};
  return [
    ...(strategy.heroSellingPoint ? [{ ...strategy.heroSellingPoint, tier: "HERO" }] : []),
    ...(strategy.coreSellingPoints || []).map((item) => ({ ...item, tier: "CORE" })),
    ...(strategy.supportingFeatures || []).map((item) => ({ ...item, tier: "SUPPORTING" })),
    ...(strategy.technicalDetails || []).map((item) => ({ ...item, tier: "TECHNICAL" })),
  ];
}

export function buildProductBrief(inputData, inputFile = "") {
  const data = normalizeCreativeSystem(clone(inputData));
  const points = sellingPointRows(data);
  const approvedClaims = (data.claims || []).filter((item) => item.status === "Approved");
  const unverifiedClaims = (data.claims || []).filter((item) => item.status !== "Approved");
  return {
    schema_version: "1.0",
    artifact: "PRODUCT_BRIEF",
    source_input: inputFile ? path.basename(inputFile) : "",
    generated_on: "2026-08-18",
    market: data.meta.market || "JP",
    language: data.meta.language || "ja-JP",
    product: data.product,
    category: data.product.category || "Unknown",
    target_audience: data.strategy?.primaryAudience || "Unknown",
    secondary_audience: data.strategy?.secondaryAudience || "Not Available",
    core_problem: data.strategy?.coreProblem || "Unknown",
    core_value: data.strategy?.coreValue || "Unknown",
    reference_profile: clone(inputData.reference_profile || inputData.referenceProfile || inputData.meta?.reference_profile || inputData.meta?.referenceProfile || {}),
    supporting_values: points.filter((item) => item.tier !== "HERO").map((item) => item.benefit).filter(Boolean),
    selling_points: points,
    features: points.map((item) => item.feature).filter(Boolean),
    benefits: points.map((item) => item.benefit).filter(Boolean),
    use_cases: [...new Set(points.map((item) => item.scenario).filter(Boolean))],
    reasons_to_believe: data.strategy?.reasonsToBelieve || [],
    objections: data.strategy?.objections || [],
    limitations: [
      ...(data.missingInformation || []),
      ...unverifiedClaims.map((item) => ({ claim_id: item.id, status: item.status, risk: item.risk || "" })),
    ],
    compatibility: {
      status: unverifiedClaims.some((item) => /Matter|対応|互換/i.test(`${item.copy} ${item.conditions}`)) ? "Need Verification" : "Not Available",
      evidence: (data.claims || []).filter((item) => /Matter|対応|互換/i.test(`${item.copy} ${item.conditions}`)),
    },
    faq: data.faq || [],
    competitors: data.comparison?.products || [],
    approved_claims: approvedClaims,
    unverified_claims: unverifiedClaims,
    pricing: {
      value: data.product.price || "Not Available",
      status: data.product.priceStatus || "Need Verification",
    },
    source_mapping: data.sources || [],
    fact_checks: {
      status: unverifiedClaims.length ? "Partial" : "Pass",
      approved_claim_count: approvedClaims.length,
      unverified_claim_count: unverifiedClaims.length,
      missing_information_count: (data.missingInformation || []).length,
      rule: "Unverified, blocked and prohibited items remain non-facts and cannot be promoted to consumer Claims.",
    },
    phase_boundary: "KNOW only. No visual plan, A+ layout, AI scene generation or final rendering is authorized by this artifact.",
  };
}

export function buildSellingPointMatrix(inputData, productBrief = null) {
  const data = normalizeCreativeSystem(clone(inputData));
  const brief = productBrief || buildProductBrief(inputData);
  const claims = new Map((data.claims || []).map((item) => [item.id, item]));
  const records = sellingPointRows(data).map((item, index) => {
    const claimRecords = (item.claimIds || []).map((id) => claims.get(id)).filter(Boolean);
    const blocked = claimRecords.some((claim) => claim.status !== "Approved");
    return {
      id: `SP-${String(index + 1).padStart(2, "0")}`,
      tier: item.tier,
      priority: item.priority || index + 1,
      feature: item.feature || "",
      benefit: item.benefit || "",
      user_problem: item.userProblem || brief.core_problem,
      scenario: item.scenario || "",
      mechanism: item.mechanism || "",
      proof: item.proof || "",
      claim_ids: item.claimIds || [],
      claim_source: item.source || claimRecords.map((claim) => claim.sourceId).filter(Boolean).join("; "),
      recommended_placement: item.placement || "Pending Planning",
      asset_needed: item.assetNeeded || "Not Available",
      status: blocked ? "Needs Claim Review" : normalizeStatus(item.status),
    };
  });
  return {
    schema_version: "1.0",
    artifact: "SELLING_POINT_MATRIX",
    derived_from: "PRODUCT_BRIEF.json",
    product: brief.product?.name || brief.product?.productName || "Unknown",
    market: brief.market,
    hierarchy: ["HERO", "CORE", "SUPPORTING", "TECHNICAL"],
    records,
    planning_rules: {
      consumer_decision_order: STAGES.map(([id, label_cn, question_ja]) => ({ id, label_cn, question_ja })),
      one_asset_per_feature: false,
      module_count_expansion_forbidden: true,
      unapproved_claim_policy: "Keep status and source; do not use as an approved external Claim.",
    },
  };
}

export async function writePlanningBundle(productBrief, sellingMatrix, outputDir) {
  const specDir = path.join(outputDir, "spec");
  await fs.mkdir(specDir, { recursive: true });
  await fs.writeFile(path.join(specDir, "PRODUCT_BRIEF.json"), `${JSON.stringify(productBrief, null, 2)}\n`, "utf8");
  await fs.writeFile(path.join(specDir, "SELLING_POINT_MATRIX.json"), `${JSON.stringify(sellingMatrix, null, 2)}\n`, "utf8");
}

export function refreshSpec(spec, library) {
  spec.publish_gate = buildPublishGate(spec, library);
  spec.meta.spec_sha256 = computeSpecHash(spec);
  return spec;
}

export function validateSpec(spec, library) {
  const errors = [];
  const templateIds = new Set((library.templates || []).map((template) => template.template_id));
  if (spec.schema_version !== "4.0") errors.push("schema_version must be 4.0");
  if (spec.product_images.length !== 7) errors.push("Exactly 7 product images are required");
  if (spec.bullets.length !== 5) errors.push("Exactly 5 bullets are required");
  if (spec.aplus_modules.length < 5 || spec.aplus_modules.length > 8) errors.push("A+ must use 5-8 modules");
  spec.product_images.forEach((item, index) => {
    if (item.stage !== STAGES[index][0]) errors.push(`${item.id} stage order is invalid`);
    if (!templateIds.has(item.template_id)) errors.push(`${item.id} uses unknown template_id ${item.template_id}`);
  });
  spec.aplus_modules.forEach((module) => {
    if (!templateIds.has(module.template_id)) errors.push(`${module.id} uses unknown template_id ${module.template_id}`);
  });
  for (const record of spec.asset_resolution_plan?.records || []) {
    if (!ASSET_SOURCE_TYPES.includes(record.source_type)) errors.push(`${record.visual_id} uses invalid asset source_type ${record.source_type}`);
    if (["placeholder", "external_reference", "generated_scene", "unknown"].includes(record.source_type) && record.product_layer_allowed) {
      errors.push(`${record.visual_id} unsafe provenance: ${record.source_type} cannot be allowed in Product Layer`);
    }
    if (record.resolved !== record.file_resolved) errors.push(`${record.visual_id} resolved must mean file_resolved only`);
  }
  try {
    assertStorySequenceIntegrity(spec);
  } catch (error) {
    errors.push(error.message);
  }
  if (spec.meta.spec_sha256 !== computeSpecHash(spec)) errors.push("Spec SHA-256 does not match canonical content");
  return errors;
}

export async function buildProductPageSpec(inputData, inputFile, outputDir, library, gateMode = "pending") {
  const data = normalizeCreativeSystem(clone(inputData));
  const byTemplate = templateIndex(library);
  const localize = await createAssetLocalizer(inputFile, outputDir);
  const productMain = await localize(data.product.mainImage);
  const assetRecords = [];
  const productImages = [];

  for (let index = 0; index < data.images.length; index += 1) {
    const record = data.images[index];
    const meta = sourceMeta(record, data);
    const visual = record.visualSrc || record.productSource || data.product.mainImage;
    const lifestyle = looksLifestyle(visual, meta.source_asset_type) || record.stage === "see_real_scenario";
    const productRaw = record.productSource || data.product.mainImage;
    const sceneRaw = record.sceneSource || (lifestyle ? visual : "");
    const productAsset = await localize(productRaw);
    const sceneAsset = sceneRaw ? await localize(sceneRaw) : { original: "", path: "", exists: false, sha256: "" };
    const sceneContainsOfficialProduct = lifestyle && sceneAsset.exists;
    const resolution = decideAssetResolution(record.id, meta, productAsset, sceneAsset, sceneContainsOfficialProduct);
    assetRecords.push(resolution);
    productImages.push({
      id: record.id,
      ...(Object.hasOwn(record, "visual_type") ? { visual_type: record.visual_type } : {}),
      sequence: index + 1,
      stage: record.stage,
      stage_label_cn: STAGES[index][1],
      user_question: record.userQuestion || STAGES[index][2],
      role: record.pageRole || record.role,
      key_message: record.keyMessage,
      headline: record.headline || "",
      sub_copy: record.subcopy || "",
      supporting_data: record.supportingData || "",
      proof_items: record.informationHierarchy?.level3 || [],
      template_id: PRODUCT_TEMPLATE_SEQUENCE[index],
      template_snapshot: byTemplate.get(PRODUCT_TEMPLATE_SEQUENCE[index]),
      copy_review: record.copyReview,
      claim_ids: record.claimIds || [],
      claim_sources: claimSources(record, data),
      claim_source: record.claimSource || "",
      risk: record.risk || "",
      source_origin: meta.source_origin,
      source_asset_type: meta.source_asset_type,
      product_body_ai_generated: meta.product_body_ai_generated,
      ai_generated_elements: meta.ai_generated_elements,
      layers: layerRules(productAsset.path || productMain.path, sceneAsset.path, sceneContainsOfficialProduct),
      asset_resolution: resolution,
      status: record.status,
      outputs: {
        jpeg: `design/product_images/image_${String(index + 1).padStart(2, "0")}.jpg`,
        svg: `design/svg/product_images/image_${String(index + 1).padStart(2, "0")}.svg`,
        wireframe_svg: `design/svg/wireframes/product_images/image_${String(index + 1).padStart(2, "0")}.svg`,
      },
    });
  }

  const aplusModules = [];
  for (let index = 0; index < data.aplusModules.length; index += 1) {
    const module = data.aplusModules[index];
    const templateId = APLUS_TEMPLATE_SEQUENCE[index] || "A-50-50-FEATURE";
    const units = [];
    for (const unit of module.units || []) {
      const meta = sourceMeta(unit, data);
      const visual = unit.visualSrc || unit.productSource || data.product.mainImage;
      const lifestyle = looksLifestyle(visual, meta.source_asset_type) || unit.stage === "see_real_scenario";
      const productRaw = unit.productSource || data.product.mainImage;
      const sceneRaw = unit.sceneSource || (lifestyle ? visual : "");
      const productAsset = await localize(productRaw);
      const sceneAsset = sceneRaw ? await localize(sceneRaw) : { original: "", path: "", exists: false, sha256: "" };
      const sceneContainsOfficialProduct = lifestyle && sceneAsset.exists;
      const resolution = decideAssetResolution(unit.id, meta, productAsset, sceneAsset, sceneContainsOfficialProduct);
      assetRecords.push(resolution);
      units.push({
        id: unit.id,
        ...(Object.hasOwn(unit, "visual_type") ? { visual_type: unit.visual_type } : {}),
        stage: unit.stage,
        purpose: unit.purpose,
        user_question: unit.userQuestion,
        headline: unit.headline,
        copy: unit.copy || "",
        visual: unit.visual || "",
        asset_requirement: unit.asset || "",
        copy_review: unit.copyReview,
        claim_ids: unit.claimIds || [],
        claim_sources: claimSources(unit, data),
        claim_source: unit.claimSource || "",
        risk: unit.risk || "",
        source_origin: meta.source_origin,
        source_asset_type: meta.source_asset_type,
        product_body_ai_generated: meta.product_body_ai_generated,
        ai_generated_elements: meta.ai_generated_elements,
        layers: layerRules(productAsset.path || productMain.path, sceneAsset.path, sceneContainsOfficialProduct),
        asset_resolution: resolution,
        status: unit.status,
      });
    }
    aplusModules.push({
      id: module.id,
      ...(Object.hasOwn(module, "visual_type") ? { visual_type: module.visual_type } : {}),
      sequence: index + 1,
      template_id: templateId,
      template_snapshot: byTemplate.get(templateId),
      story_role: module.storyRole || module.purpose,
      module_headline: module.moduleHeadline || units[0]?.headline || module.purpose,
      module_availability: module.moduleAvailability || data.meta.moduleAvailability || "Need Verification",
      units,
      outputs: {
        jpeg: `design/aplus/aplus_${String(index + 1).padStart(2, "0")}.jpg`,
        svg: `design/svg/aplus/aplus_${String(index + 1).padStart(2, "0")}.svg`,
        wireframe_svg: `design/svg/wireframes/aplus/aplus_${String(index + 1).padStart(2, "0")}.svg`,
      },
    });
  }

  const storyApproval = defaultApproval("story", gateMode, inputData.human_gates?.story_approval);
  const layoutApproval = defaultApproval("layout", gateMode, inputData.human_gates?.layout_approval);
  const spec = {
    schema_version: "4.0",
    system: "amazon-japan-pdp-generator",
    production_model: "Spec-driven + Template-driven",
    meta: {
      spec_sha256: "",
      generated_on: "2026-08-18",
      market: data.meta.market,
      language: data.meta.language || "ja-JP",
      source_input: path.basename(inputFile),
      external_publish_ready: Boolean(data.meta.externalPublishReady),
      module_availability: data.meta.moduleAvailability || "Need Verification",
      asset_origin_boundary: data.meta.productAssetOrigin || data.product.mainImageOrigin || "Unknown",
      gate_mode: gateMode,
      render_policy: "Final high-fidelity render requires Layout Approval. Internal QA approval is not publication approval.",
    },
    upstream: {
      product_brief: "spec/PRODUCT_BRIEF.json",
      selling_point_matrix: "spec/SELLING_POINT_MATRIX.json",
      rule: "These upstream planning artifacts may be rebuilt in KNOW/PLAN. Every page/design/export artifact below is rendered only from this PRODUCT_PAGE_SPEC.",
    },
    template_library: {
      library_version: library.library_version,
      schema_version: library.schema_version,
      registered_template_count: (library.templates || []).length,
      source_policy: library.source_policy,
      brand_tokens: library.brand_tokens,
      historical_references: library.historical_references,
      registry_path: "templates/template_library.json",
    },
    product: {
      ...data.product,
      main_asset: productMain.path,
      main_asset_sha256: productMain.sha256,
      rating: normalizeRating(data.product.rating),
    },
    journey: data.journey,
    strategy: data.strategy,
    titles: data.titles,
    bullets: data.bullets,
    product_images: productImages,
    aplus_modules: aplusModules,
    comparison: data.comparison,
    seo: data.seo,
    faq: data.faq,
    claims: data.claims || [],
    sources: data.sources || [],
    missing_information: data.missingInformation || [],
    asset_resolution_plan: {
      schema_version: "2.0",
      priority_order: ["Official scene", "Official white background/render", "Authorized material", "AI scene without product", "Placeholder"],
      records: assetRecords,
    },
    copy_review: {
      status: copyReviewStatus(data) ? "Pass" : "Needs Japan Localization Review",
      scope: "Title, Bullet, product-image headlines, A+ headlines/copy and FAQ",
      note: "Programmatic typesetting does not replace human Japan localization approval.",
    },
    human_gates: {
      story_approval: storyApproval,
      layout_approval: layoutApproval,
      final_render_authorized: String(layoutApproval.status).startsWith("Approved"),
    },
    quality_evidence: {
      mobile: {
        status: "Pending Browser QA",
        viewport: "390x844",
        evidence_file: "qa/browser-qa.json",
      },
    },
    output_contract: {
      product_brief: "spec/PRODUCT_BRIEF.json",
      selling_point_matrix: "spec/SELLING_POINT_MATRIX.json",
      spec: "spec/PRODUCT_PAGE_SPEC.json",
      asset_resolution: "spec/ASSET_RESOLUTION_PLAN.json",
      copy_deck: "spec/copy_deck.json",
      product_understanding: "review/product_understanding_cn.html",
      story_review: "review/story_review.html",
      layout_review: "review/layout_review.html",
      design_review: "review/design_review_cn.html",
      amazon_preview: "preview/amazon_pdp_preview.html",
      workbooks: "workbooks/*.xlsx",
      export_workbooks: "export/*.xlsx",
      product_images: "design/product_images/*.jpg",
      aplus: "design/aplus/*.jpg",
      editable_svg: "design/svg/**/*.svg",
      final_product_images: "final/product_images/*.jpg",
      final_aplus: "final/aplus/*.jpg",
      final_comparison: "final/comparison/*",
      final_editable: "final/editable/**/*.svg",
      reports: "reports/*",
    },
  };
  return refreshSpec(spec, library);
}

export async function writeSpecBundle(spec, outputDir, options = {}) {
  const { derived = true } = options;
  const specDir = path.join(outputDir, "spec");
  await fs.mkdir(specDir, { recursive: true });
  await fs.writeFile(path.join(specDir, "PRODUCT_PAGE_SPEC.json"), `${JSON.stringify(spec, null, 2)}\n`, "utf8");
  if (!derived) return;
  const assetResolution = `${JSON.stringify({
    ...spec.asset_resolution_plan,
    derived_from: "PRODUCT_PAGE_SPEC.json",
    spec_sha256: spec.meta.spec_sha256,
  }, null, 2)}\n`;
  await fs.writeFile(path.join(specDir, "ASSET_RESOLUTION_PLAN.json"), assetResolution, "utf8");
  // Compatibility alias for V3/V4-beta consumers. Canonical path is uppercase.
  await fs.writeFile(path.join(specDir, "asset_resolution_plan.json"), assetResolution, "utf8");
  await fs.writeFile(path.join(specDir, "copy_deck.json"), `${JSON.stringify(compactCopyDeck(spec), null, 2)}\n`, "utf8");
}

export async function readSpec(specFile) {
  return JSON.parse(await fs.readFile(specFile, "utf8"));
}

export async function readTemplateLibrary(skillDir) {
  return JSON.parse(await fs.readFile(path.join(skillDir, "templates", "template_library.json"), "utf8"));
}

export function parseArgs(argv) {
  const args = {};
  const booleans = new Set(["render-workbooks", "verify-workbooks", "resume", "rerender", "force", "from-spec-only"]);
  for (let index = 2; index < argv.length; index += 1) {
    const token = argv[index];
    if (!token.startsWith("--")) continue;
    const key = token.slice(2);
    if (booleans.has(key)) args[key] = true;
    else args[key] = argv[++index];
  }
  return args;
}

export { OFFICIAL_TYPES, USER_OFFICIAL_ORIGIN };
