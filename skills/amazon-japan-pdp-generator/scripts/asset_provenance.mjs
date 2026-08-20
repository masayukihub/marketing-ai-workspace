export const ASSET_SOURCE_TYPES = Object.freeze([
  "official",
  "user_supplied",
  "generated_scene",
  "placeholder",
  "external_reference",
  "unknown",
]);

const USER_OFFICIAL_ORIGIN = "User Provided Official";
const OFFICIAL_TYPES = new Set([
  "Official White Background",
  "Official PNG",
  "Official Render",
  "Official Lifestyle",
  "Official Installation",
  "Official Detail",
]);

function text(value) {
  return String(value || "").normalize("NFKC").toLowerCase();
}

export function classifyAssetSource({ sourcePath = "", sourceOrigin = "", sourceAssetType = "", layer = "product" } = {}) {
  const combined = text([sourcePath, sourceOrigin, sourceAssetType].join(" "));
  if (!sourcePath || /placeholder|dummy|mock(?:up)?|temp(?:orary)?|internal placeholder/.test(combined)) return "placeholder";
  if (/^https?:\/\//i.test(sourcePath) || /external|reference|competitor|network|web download|fixture/.test(combined)) return "external_reference";
  if (layer === "scene" && /generated|ai scene|synthetic|生成/.test(combined)) return "generated_scene";
  if (sourceOrigin === USER_OFFICIAL_ORIGIN && OFFICIAL_TYPES.has(sourceAssetType)) return "official";
  if (/user provided|user supplied|provided by user|用户提供/.test(combined)) return "user_supplied";
  return "unknown";
}

export function buildAssetProvenance({ asset = {}, meta = {}, layer = "product", containsOfficialProduct = false } = {}) {
  const sourcePath = asset.path || asset.original || "";
  const sourceType = classifyAssetSource({
    sourcePath,
    sourceOrigin: meta.source_origin,
    sourceAssetType: meta.source_asset_type,
    layer,
  });
  const fileResolved = Boolean(asset.exists);
  const explicitVerification = text(meta.verification_status);
  const sourceVerified = sourceType === "official"
    && meta.source_origin === USER_OFFICIAL_ORIGIN
    && OFFICIAL_TYPES.has(meta.source_asset_type)
    && ["verified", "approved", "confirmed"].includes(explicitVerification);
  const usageApproved = meta.usage_approved === true;
  const productLayerAllowed = layer === "product"
    && fileResolved
    && sourceVerified
    && usageApproved
    && meta.product_body_ai_generated === false;
  const generatedSceneAllowed = layer === "scene" && sourceType === "generated_scene" && !containsOfficialProduct;
  const sceneLayerAllowed = layer === "scene" && fileResolved && usageApproved && (sourceVerified || generatedSceneAllowed);
  const verificationStatus = sourceVerified ? "verified" : sourceType === "generated_scene" ? "not_applicable" : "unverified";
  return {
    source_type: sourceType,
    source_path: sourcePath,
    verification_status: verificationStatus,
    product_layer_allowed: productLayerAllowed,
    scene_layer_allowed: sceneLayerAllowed,
    resolved: fileResolved,
    file_resolved: fileResolved,
    source_verified: sourceVerified,
    usage_approved: usageApproved,
  };
}

export function assetProvenanceFailures(record) {
  const product = record?.product_provenance || record;
  return [
    ...(!product?.file_resolved ? ["file_not_resolved"] : []),
    ...(!product?.source_verified ? ["source_not_verified"] : []),
    ...(!product?.usage_approved ? ["usage_not_approved"] : []),
    ...(!product?.product_layer_allowed ? ["product_layer_not_allowed"] : []),
  ];
}

export { OFFICIAL_TYPES, USER_OFFICIAL_ORIGIN };
