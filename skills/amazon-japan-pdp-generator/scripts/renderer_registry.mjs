export const REQUIRED_REFERENCE_RENDERERS = Object.freeze([
  "P-FEATURE-SPLIT",
  "P-ECOSYSTEM",
  "A-50-50-FEATURE",
  "A-INSTALLATION",
  "A-BRAND",
]);

const EXISTING_RENDERERS = Object.freeze([
  "P-MAIN-OFFICIAL",
  "P-HERO-SPLIT",
  "P-FEATURE-CENTER",
  "P-LIFESTYLE-FULL",
  "P-TECHNICAL-PROOF",
  "P-COMPARISON",
  "P-PURCHASE-CONFIDENCE",
  "A-HERO",
  "A-THREE-FEATURE-GRID",
  "A-LIFESTYLE",
  "A-TECHNICAL",
  "A-ECOSYSTEM",
  "A-COMPARISON",
  "A-FAQ",
]);

const SLOT_CONTRACT = Object.freeze({
  title: { required: true, fallback: "key_message / story_role" },
  body: { required: true, fallback: "role / purpose" },
  image: { required: true, fallback: "programmatic neutral placeholder" },
  claim: { required: false, fallback: "claim-free condition text" },
});

const common = Object.freeze({
  renderer_available: true,
  deterministic: true,
  slots: SLOT_CONTRACT,
  safe_fallback: "Preserve consumer text; replace only a missing image with a neutral programmatic placeholder.",
});

export const RENDERER_REGISTRY = Object.freeze({
  ...Object.fromEntries(EXISTING_RENDERERS.map((templateId) => [templateId, {
    ...common,
    implementation: "formal-v4",
    desktop_layout: "Existing deterministic formal renderer.",
    mobile_layout: templateId.startsWith("A-")
      ? "Dedicated 780px single-column A+ renderer selected at <=700px."
      : "Square canvas with mobile-safe center zones.",
  }])),
  "P-FEATURE-SPLIT": {
    ...common,
    implementation: "reference-readiness-v1",
    desktop_layout: "2000x2000 product/mechanism split with title, body and condition band.",
    mobile_layout: "Mobile-safe square: title first, official product center, body and condition remain inside 84% safe area.",
  },
  "P-ECOSYSTEM": {
    ...common,
    implementation: "reference-readiness-v1",
    desktop_layout: "2000x2000 centered official product with at most three verified relationship cards.",
    mobile_layout: "Verified relationships become a top-to-bottom list.",
  },
  "A-50-50-FEATURE": {
    ...common,
    implementation: "reference-readiness-v1",
    desktop_layout: "1464x620 narrative/product columns with one mechanism and one optional condition.",
    mobile_layout: "780px single column: title and body precede image; condition remains adjacent.",
  },
  "A-INSTALLATION": {
    ...common,
    implementation: "reference-readiness-v1",
    desktop_layout: "1464x700 ordered two- or three-step sequence with adjacent conditions.",
    mobile_layout: "780px stacked steps; number, title, body and condition remain adjacent.",
  },
  "A-BRAND": {
    ...common,
    implementation: "reference-readiness-v1",
    desktop_layout: "1464x600 approved brand statement and independent official image zone.",
    mobile_layout: "780px single column: approved brand message first, image second.",
  },
});

export function rendererCapability(templateId) {
  return RENDERER_REGISTRY[templateId] || {
    renderer_available: false,
    deterministic: false,
    implementation: "missing",
    slots: SLOT_CONTRACT,
    desktop_layout: "Not available",
    mobile_layout: "Not available",
    safe_fallback: "Planner must reject this Primitive.",
  };
}

export function assertRendererCoverage(templateIds) {
  const missing = [...new Set(templateIds)].filter((templateId) => !rendererCapability(templateId).renderer_available);
  if (missing.length) throw new Error(`Planner selected Primitive(s) without renderer: ${missing.join(", ")}`);
  return { pass: true, missing };
}
