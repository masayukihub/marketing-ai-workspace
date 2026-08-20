import crypto from "node:crypto";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const moduleDir = path.dirname(fileURLToPath(import.meta.url));
const semanticRoot = path.join(path.dirname(moduleDir), "category-semantics");
const smartLock = JSON.parse(fs.readFileSync(path.join(semanticRoot, "smart-lock.json"), "utf8"));

const GENERIC = Object.freeze({
  schema_version: "1.0",
  category_id: "generic",
  category_name: "Generic Product",
  core_consumer_questions: [],
  trust_dimensions: [],
  compatibility_questions: [],
  installation_questions: [],
  security_questions: [],
  unlock_scenarios: [],
  ownership_questions: [],
  visual_proof_types: [],
  high_risk_claim_types: [],
  forbidden_cross_product_semantics: ["smart lock", "door lock", "スマートロック", "サムターン", "施錠", "解錠", "智能门锁"],
  intent_keywords: {},
});

function hash(value) {
  return crypto.createHash("sha256").update(JSON.stringify(value)).digest("hex");
}

function strings(value, currentPath = "$", out = []) {
  if (typeof value === "string") out.push({ path: currentPath, value });
  else if (Array.isArray(value)) value.forEach((item, index) => strings(item, `${currentPath}[${index}]`, out));
  else if (value && typeof value === "object") Object.entries(value).forEach(([key, item]) => strings(item, `${currentPath}.${key}`, out));
  return out;
}

function productDescriptor(spec) {
  return [spec?.product?.name, spec?.product?.category, spec?.meta?.product_id, spec?.meta?.product_name]
    .filter(Boolean).join(" ").toLowerCase();
}

export function buildProductSemanticContext(spec) {
  const descriptor = productDescriptor(spec);
  const isSmartLock = smartLock.match_terms.some((term) => descriptor.includes(term.toLowerCase()));
  const category = isSmartLock ? smartLock : GENERIC;
  const context = {
    schema_version: "1.0",
    artifact: "PRODUCT_SEMANTIC_CONTEXT",
    product: {
      name: spec?.product?.name || "Not Available",
      category: spec?.product?.category || "Not Available",
      sku: spec?.product?.sku || "Not Available",
    },
    category_id: category.category_id,
    category_name: category.category_name,
    source: isSmartLock ? "category-semantics/smart-lock.json" : "generic fail-closed fallback",
    category_semantics: category,
    quality_priority: ["Semantic Correctness", "Content Completeness", "Product Truth", "Amazon Platform Fidelity", "Brand Fit", "Visual Polish"],
  };
  context.context_sha256 = hash(context);
  return context;
}

function textOf(record) {
  return [record?.id, record?.stage, record?.role, record?.purpose, record?.story_role, record?.user_question, record?.headline, record?.copy, record?.sub_copy, record?.key_message]
    .filter(Boolean).join(" ").toLowerCase();
}

export function semanticIntent(record, context) {
  if (record?.id === "IMAGE-01") return "main_identity";
  const text = textOf(record);
  for (const [intent, keywords] of Object.entries(context?.category_semantics?.intent_keywords || {})) {
    if ((keywords || []).some((keyword) => text.includes(String(keyword).toLowerCase()))) return intent;
  }
  if (/faq|support|closure|objection/.test(text)) return "support_closure";
  if (/comparison|fit|compatib|適合|購入前/.test(text)) return "compatibility_fit";
  if (/scenario|lifestyle|daily|family|帰宅|家族/.test(text)) return "daily_routine";
  if (/technical|proof|trust|condition|mechanism/.test(text)) return "security_trust";
  return "functional_default";
}

export function semanticVisualRole(record, kind, context) {
  const template = record?.template_id || "";
  const intent = semanticIntent(record, context);
  if (template === "P-MAIN-OFFICIAL" || template === "P-HERO-SPLIT" || template === "A-HERO") return "IMPACT";
  if (["P-FEATURE-CENTER", "P-FEATURE-SPLIT", "A-50-50-FEATURE"].includes(template)) return "EXPLAIN";
  if (template === "A-THREE-FEATURE-GRID") return "DETAIL";
  if (["P-LIFESTYLE-FULL", "A-LIFESTYLE"].includes(template)) return intent === "daily_routine" ? "SCENARIO" : "BREATHE";
  if (["P-TECHNICAL-PROOF", "P-ECOSYSTEM", "A-TECHNICAL", "A-ECOSYSTEM", "A-INSTALLATION"].includes(template)) return "PROOF";
  if (["P-COMPARISON", "A-COMPARISON"].includes(template)) return "COMPARE";
  if (["P-PURCHASE-CONFIDENCE", "A-FAQ", "A-BRAND"].includes(template)) return "CLOSURE";
  if (["compatibility_fit", "security_trust", "power_exception", "installation"].includes(intent)) return "PROOF";
  if (["unlock_scenario", "daily_routine"].includes(intent)) return "SCENARIO";
  if (["configuration"].includes(intent)) return "COMPARE";
  if (["support_closure"].includes(intent)) return "CLOSURE";
  return kind === "gallery" ? "EXPLAIN" : "DETAIL";
}

export function scanSemanticContamination(value, context) {
  const forbidden = context?.category_semantics?.forbidden_cross_product_semantics || [];
  const hits = [];
  for (const entry of strings(value)) {
    const lower = entry.value.toLowerCase();
    for (const term of forbidden) {
      if (!term || !lower.includes(String(term).toLowerCase())) continue;
      hits.push({ path: entry.path, term, excerpt: entry.value.slice(0, 220) });
    }
  }
  return {
    code: "CROSS_PRODUCT_SEMANTIC_CONTAMINATION",
    category_id: context?.category_id || "unknown",
    status: hits.length ? "FAIL" : "PASS",
    hit_count: hits.length,
    hits,
  };
}

export function assertSemanticIsolation(value, context) {
  const result = scanSemanticContamination(value, context);
  if (result.status !== "PASS") {
    const sample = result.hits.slice(0, 5).map((hit) => `${hit.path}:${hit.term}`).join(", ");
    throw new Error(`${result.code}: ${sample}`);
  }
  return result;
}
