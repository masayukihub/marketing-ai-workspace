import crypto from "node:crypto";
import fs from "node:fs/promises";
import path from "node:path";
import { evaluateCreativeReview } from "./creative_review.mjs";

const USER_OFFICIAL_ORIGIN = "User Provided Official";
const OFFICIAL_TYPES = new Set(["Official White Background", "Official PNG", "Official Render", "Official Lifestyle", "Official Installation", "Official Detail"]);
const PRODUCT_FILENAMES = ["image_01.jpg", "image_02.jpg", "image_03.jpg", "image_04.jpg", "image_05.jpg", "image_06.jpg", "image_07.jpg"];
const PRODUCT_LAYOUTS = ["MAIN", "A", "B", "C", "D", "F", "F"];
const TEMPLATE_BY_SEQUENCE = ["SB-A01", "SB-A02", "SB-A03", "SB-A04", "SB-A05", "SB-A07", "SB-A08"];
const LEGACY_TEMPLATE_MAP = { A: "SB-A01", B: "SB-A02", C: "SB-A04", D: "SB-A03", E: "SB-A05", F: "SB-A06", G: "SB-A06", H: "SB-A06", I: "SB-A07", J: "SB-A08" };
const TEMPLATE_NAMES = {
  "SB-A01": "Hero", "SB-A02": "50/50 Feature", "SB-A03": "Three Feature Grid", "SB-A04": "Lifestyle Full Image",
  "SB-A05": "Technical Diagram", "SB-A06": "Ecosystem", "SB-A07": "Comparison / Fit", "SB-A08": "FAQ / Purchase Confidence",
};
const STAGE_COLORS = [
  ["#FFFFFF", "#17212B", "#E8F5F1"], ["#F4FAF8", "#143E37", "#BEE6DC"], ["#F4F8FA", "#173B4C", "#C8E3EC"],
  ["#F7F2EC", "#3D342B", "#DFCDB8"], ["#F1F8F9", "#173B45", "#B8D9DF"], ["#FFF9EE", "#513B18", "#F0D39D"], ["#FAF5F2", "#4B302C", "#E7CBC4"],
];

function esc(value) { return String(value ?? "").replaceAll("&", "&amp;").replaceAll("<", "&lt;").replaceAll(">", "&gt;").replaceAll('"', "&quot;").replaceAll("'", "&#039;"); }
function isUrl(value) { return /^https?:\/\//i.test(String(value || "")); }
function chars(value) { return [...String(value || "").trim()]; }
function compact(value, max) { const input = chars(value); return input.length <= max ? input.join("") : `${input.slice(0, Math.max(1, max - 1)).join("")}…`; }
function splitProof(value) { return String(value || "").split(/\s*(?:\/|｜|\||;|；|、)\s*/).map((x) => x.trim()).filter(Boolean).slice(0, 4); }

function textLines(value, max = 18, limit = 3) {
  const segments = String(value || "").trim().split(/\r?\n/); const lines = []; let overflow = false;
  for (let segmentIndex = 0; segmentIndex < segments.length; segmentIndex += 1) {
    const input = chars(segments[segmentIndex]);
    while (input.length && lines.length < limit) lines.push(input.splice(0, max).join(""));
    if (input.length || (segmentIndex < segments.length - 1 && lines.length >= limit)) { overflow = true; break; }
  }
  if (overflow && lines.length) lines[lines.length - 1] = `${chars(lines.at(-1)).slice(0, Math.max(1, max - 1)).join("")}…`;
  if (segments.length === 1 && lines.length > 1 && chars(lines.at(-1)).length < 4) {
    const previous = chars(lines.at(-2)); const tail = chars(lines.at(-1));
    while (tail.length < 4 && previous.length > 6) tail.unshift(previous.pop());
    lines[lines.length - 2] = previous.join(""); lines[lines.length - 1] = tail.join("");
  }
  return lines;
}

function svgText(value, x, y, options = {}) {
  const { max = 18, limit = 3, size = 58, weight = 700, fill = "#17212B", gap = 1.28, anchor = "start", opacity = 1 } = options;
  return textLines(value, max, limit).map((line, index) => `<text x="${x}" y="${y + index * size * gap}" text-anchor="${anchor}" font-family="'Hiragino Sans','Noto Sans JP','Yu Gothic',Arial,sans-serif" font-size="${size}" font-weight="${weight}" fill="${fill}" opacity="${opacity}">${esc(line)}</text>`).join("\n");
}

function scoreCopy(text, claimIds = [], approvedClaims = new Set(), option = "A") {
  const length = chars(text).length; const japanese = /[ぁ-んァ-ヶ一-龠々]/u.test(text);
  const internal = /Need Verification|Claim|Source|待确认|素材|风险|要確認|確認中|未確認|Seller Central|Amazon登録/i.test(text);
  const naturalness = japanese && !internal ? 5 : japanese ? 3 : 1;
  const amazonReadability = length <= 15 ? 5 : length <= 20 ? 4 : length <= 26 ? 3 : 1;
  const claimAccuracy = claimIds.some((id) => !approvedClaims.has(id)) ? 2 : 5;
  const mobileLength = length <= 18 ? 5 : length <= 24 ? 3 : 1;
  return { naturalness, amazonReadability, claimAccuracy, mobileLength, total: naturalness + amazonReadability + claimAccuracy + mobileLength + (option === "A" ? 2 : 0) };
}

function japaneseCandidate(value) {
  const text = String(value || "").trim();
  return /[ぁ-んァ-ヶ一-龠々]/u.test(text) && !/[\u4e00-\u9fff]{4,}.*[的了]/u.test(text) ? text : "";
}

function ensureCopyReview(record, approvedClaims, bodyKey = "subcopy") {
  const current = String(record.headline || "").trim();
  if (!current) { record.copyReview = { options: [], selected: "", status: "Not Applicable", reason: "主图不放营销文案" }; return; }
  const authored = Array.isArray(record.copyOptions) ? record.copyOptions : [];
  const functional = japaneseCandidate(record.functionalHeadline || record.keyMessage || record.userQuestion);
  const lifestyle = japaneseCandidate(record.lifestyleHeadline || String(record[bodyKey] || "").split(/[。！？]/)[0]);
  const seeds = [
    { id: "A", approach: "最推荐 / Benefit", text: authored.find((x) => x.id === "A")?.text || current },
    { id: "B", approach: "功能型", text: authored.find((x) => x.id === "B")?.text || functional || compact(current.replace(/[。、]/g, ""), 18) },
    { id: "C", approach: "生活场景型", text: authored.find((x) => x.id === "C")?.text || lifestyle || compact(current, 15) },
  ];
  const options = seeds.map((option) => ({ ...option, scores: scoreCopy(option.text, record.claimIds || [], approvedClaims, option.id) }));
  const selected = authored.length ? (record.copySelected || "A") : options.slice().sort((a, b) => b.scores.total - a.scores.total || a.id.localeCompare(b.id))[0].id;
  const final = options.find((x) => x.id === selected) || options[0];
  record.originalHeadline = current;
  record.copyReview = { options, selected: final.id, selectedText: final.text, status: authored.length >= 3 ? "Reviewed" : "Auto Draft — Needs Japanese Copy Review", reason: `自然度・Amazon可読性・Claim正確性・モバイル長を採点。${final.id}を採用。` };
  record.headline = final.text;
}

function normalizeTemplate(module, index) {
  const raw = String(module.templateType || module.templateId || "").trim();
  const canonical = TEMPLATE_NAMES[raw] ? raw : LEGACY_TEMPLATE_MAP[raw] || TEMPLATE_BY_SEQUENCE[index] || "SB-A02";
  module.templateType = canonical; module.templateId = canonical; module.templateName = TEMPLATE_NAMES[canonical]; return canonical;
}

function normalizeRating(value) {
  if (!value || typeof value !== "object" || Array.isArray(value)) return { value: null, count: null, source: null, source_type: null, status: "unavailable" };
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

export function normalizeCreativeSystem(data) {
  const approvedClaims = new Set((data.claims || []).filter((x) => x.status === "Approved").map((x) => x.id));
  data.product.rating = normalizeRating(data.product.rating);
  data.meta.visualWorkflowVersion = "3.0";
  data.meta.visualWorkflow = ["Page Role", "Information Structure", "Wireframe", "Japanese Copy Review", "Asset Selection", "Product Composite", "Scene Completion", "Round 1", "Visual Review", "Round 2", "Final QA"];
  (data.images || []).forEach((item, index) => {
    item.pageRole = item.pageRole || item.role;
    item.layoutId = index === 0 ? "MAIN" : (String(item.layoutId || "").toUpperCase() || PRODUCT_LAYOUTS[index]);
    if (!["MAIN", "A", "B", "C", "D", "E", "F"].includes(item.layoutId)) item.layoutId = PRODUCT_LAYOUTS[index];
    ensureCopyReview(item, approvedClaims, "subcopy");
    item.informationHierarchy = { level1: item.headline || "", level2: item.subcopy || "", level3: Array.isArray(item.proofItems) ? item.proofItems.slice(0, 4) : splitProof(item.supportingData) };
    item.layerPlan = {
      product: { source: item.productSource || item.visualSrc || data.product.mainImage, rule: "官方产品素材，仅合成，不重画" },
      scene: { source: item.sceneSource || "", aiAllowed: ["scene", "people", "background", "lighting", "props", "composition expansion"] },
      graphic: { elements: item.graphicElements || ["headline", "subcopy", ...(item.informationHierarchy.level3.length ? ["proof"] : [])], editable: true },
    };
    item.wireframe = { layoutId: item.layoutId, visualFocus: index === 0 ? "产品准确性" : "产品本体", maxInformationLevels: 3, mobileRule: "390px 下 Headline 仍可在 5 秒内读取" };
  });
  (data.aplusModules || []).forEach((module, index) => {
    normalizeTemplate(module, index); module.storyRole = module.storyRole || module.purpose; module.units = module.units || [];
    module.units.forEach((unit) => {
      ensureCopyReview(unit, approvedClaims, "copy");
      unit.informationHierarchy = { level1: unit.headline || "", level2: unit.copy || "", level3: Array.isArray(unit.proofItems) ? unit.proofItems.slice(0, 4) : [] };
      unit.layerPlan = {
        product: { source: unit.productSource || unit.visualSrc || data.product.mainImage, rule: "官方产品素材，仅合成，不重画" },
        scene: { source: unit.sceneSource || "", aiAllowed: ["scene", "people", "background", "lighting", "props", "composition expansion"] },
        graphic: { elements: ["headline", "supporting copy", ...(unit.informationHierarchy.level3.length ? ["proof"] : [])], editable: true },
      };
    });
    module.wireframe = { templateType: module.templateType, storyRole: module.storyRole, unitCount: module.units.length, mobileRule: module.mobileConsideration || "Headline优先，卡片纵向堆叠" };
  });
  return data;
}

async function sha256(file) { return crypto.createHash("sha256").update(await fs.readFile(file)).digest("hex"); }
async function exists(file) { try { await fs.access(file); return true; } catch { return false; } }
function mimeFromBytes(bytes, sourcePath) {
  if (bytes[0] === 0xff && bytes[1] === 0xd8) return "image/jpeg";
  if (bytes[0] === 0x89 && bytes[1] === 0x50 && bytes[2] === 0x4e && bytes[3] === 0x47) return "image/png";
  if (bytes.subarray(0, 4).toString("ascii") === "RIFF" && bytes.subarray(8, 12).toString("ascii") === "WEBP") return "image/webp";
  if (/\.svg$/i.test(sourcePath)) return "image/svg+xml"; return "application/octet-stream";
}
async function dataUri(file) { const bytes = await fs.readFile(file); return `data:${mimeFromBytes(bytes, file)};base64,${bytes.toString("base64")}`; }
function localPath(value, outputDir) { if (!value || isUrl(value)) return null; return path.isAbsolute(value) ? value : path.join(outputDir, value); }

function resolveSources(record, data, outputDir) {
  const visual = String(record.visualSrc || "");
  const looksLifestyle = record.sourceAssetType === "Official Lifestyle" || /(?:lifestyle|scene|install|room|home|weather|party)/i.test(visual);
  const productValue = record.productSource || (looksLifestyle ? (data.product.productSource || data.product.mainImage) : null) || data.product.productSource || data.product.mainImage || visual;
  const sceneValue = record.sceneSource || (looksLifestyle ? visual : (record.productSource && visual && visual !== record.productSource ? visual : null));
  return { productValue, productAbsolute: localPath(productValue, outputDir), sceneValue, sceneAbsolute: localPath(sceneValue, outputDir) };
}

function sourceMetadata(record, data) {
  return { origin: record.sourceOrigin || record.productSourceOrigin || data.product.mainImageOrigin || data.meta.productAssetOrigin || "Legacy Unverified", type: record.sourceAssetType || record.productSourceType || data.product.mainImageType || "Legacy Unverified", productBodyAiGenerated: record.productBodyAiGenerated ?? data.product.productBodyAiGenerated ?? null, aiGeneratedElements: record.aiGeneratedElements || [] };
}
function claimReady(record, data) { const byId = new Map((data.claims || []).map((claim) => [claim.id, claim])); return (record.claimIds || []).every((id) => byId.get(id)?.status === "Approved"); }
export function publicationStatus(record, meta, sourceExists, claimsApproved, designPassed) {
  if (!sourceExists || meta.productBodyAiGenerated !== false) return "Blocked";
  if (meta.origin !== USER_OFFICIAL_ORIGIN || !OFFICIAL_TYPES.has(meta.type)) return "Blocked";
  if (!claimsApproved || ["Need Verification", "Conflict", "Unsupported", "Prohibited"].includes(record.status)) return "Need Verification";
  if (["Asset Missing", "Blocked"].includes(record.status)) return "Blocked";
  return designPassed ? "Final Ready" : "Need Verification";
}

function round1Audit(record, kind = "image") {
  const issues = []; const h = chars(record.headline).length; const body = chars(kind === "image" ? record.subcopy : record.copy).length;
  if (h > 15) issues.push(`Headline ${h}字：超过15字优先线，Round 2优化换行与字号`);
  if (body > (kind === "image" ? 48 : 80)) issues.push(`Supporting Copy ${body}字：移动端密度偏高`);
  if (record.copyReview?.status?.startsWith("Auto Draft")) issues.push("三案由旧输入兼容生成，需日文编辑复核");
  if (!record.layoutId && kind === "image") issues.push("缺少明确Layout ID");
  return issues.length ? issues : ["文案与版式元数据未发现问题；尚未查看实际成图"];
}

export function finalAudit(record, kind = "image", templateType = "") {
  const issues = []; const h = chars(record.headline).length; const body = chars(kind === "image" ? record.subcopy : record.copy).length;
  if (h > 28) issues.push("Headline仍过长"); if (body > (kind === "image" ? 100 : 150)) issues.push("Supporting Copy仍过长");
  if ((record.informationHierarchy?.level3 || []).length > 4) issues.push("Level 3超过4项");
  if (kind === "image" && !["MAIN", "A", "B", "C", "D", "E", "F"].includes(record.layoutId)) issues.push("Layout无效");
  if (kind === "image") {
    const capacity = {
      A: { headline: 21, body: 52 }, B: { headline: 34, body: 68 }, C: { headline: 42, body: 78 },
      D: { headline: 30, body: 60 }, E: { headline: 30, body: 60 }, F: { headline: 30, body: 60 },
    }[record.layoutId];
    if (capacity && h > capacity.headline) issues.push(`Headline超过Layout ${record.layoutId}安全容量`);
    if (capacity && body > capacity.body) issues.push(`Supporting Copy超过Layout ${record.layoutId}安全容量`);
    if (record.layoutId === "B") {
      const proof = record.informationHierarchy?.level3 || [];
      const callouts = proof.length >= 2 ? proof.slice(0, 2) : [proof[0] || "対象操作は設定により異なる", record.keyMessage || "よく使う操作へアクセス"];
      if (callouts.some((value) => chars(value).length > 33)) issues.push("Callout超过三行安全容量");
    }
    if (["D", "E", "F"].includes(record.layoutId) && (record.informationHierarchy?.level3 || []).slice(0, 3).some((value) => chars(value).length > 52)) issues.push("规格卡超过四行安全容量");
  } else {
    const capacity = {
      "SB-A01": { headline: 51, body: 96 }, "SB-A02": { headline: 39, body: 115 },
      "SB-A03": { headline: 26, body: 66 }, "SB-A04": { headline: 48, body: 93 },
      "SB-A05": { headline: 39, body: 115 }, "SB-A06": { headline: 39, body: 115 },
      "SB-A07": { headline: 28, body: 55 }, "SB-A08": { headline: 28, body: 55 },
    }[templateType];
    if (capacity && h > capacity.headline) issues.push(`Headline超过${templateType}安全容量`);
    if (capacity && body > capacity.body) issues.push(`Supporting Copy超过${templateType}安全容量`);
  }
  if (record.productBodyAiGenerated === true) issues.push("产品本体由AI生成");
  return { status: issues.length ? "Reject" : "Pass", scope: "CONTENT_AND_LAYOUT_METADATA_ONLY", issues, intendedMessage: compact(record.headline || record.keyMessage || record.purpose, 28), fiveSecondMessage: null };
}

function defs() { return `<defs><filter id="shadow"><feDropShadow dx="0" dy="24" stdDeviation="28" flood-opacity=".16"/></filter><linearGradient id="darkFade" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="#0A1717" stop-opacity=".76"/><stop offset=".62" stop-color="#0A1717" stop-opacity=".10"/><stop offset="1" stop-color="#0A1717" stop-opacity="0"/></linearGradient><linearGradient id="mint" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#F7FCFA"/><stop offset="1" stop-color="#CBE9E1"/></linearGradient></defs>`; }
function proofPills(items, x, y, width, fill, ink, max = 3) {
  return items.slice(0, max).map((item, index) => `<g transform="translate(${x} ${y + index * 92})"><rect width="${width}" height="70" rx="35" fill="${fill}"/><circle cx="38" cy="35" r="14" fill="#23B69A"/><path d="M31 35l5 5 10-12" fill="none" stroke="#fff" stroke-width="5" stroke-linecap="round" stroke-linejoin="round"/>${svgText(compact(item, 24), 72, 45, { max: 24, limit: 1, size: 28, weight: 600, fill: ink })}</g>`).join("");
}

function productWireframeSvg(item, index) {
  const layout = item.layoutId;
  const header = `<rect width="2000" height="2000" fill="#F5F6F7"/><text x="90" y="100" font-family="Arial" font-size="34" font-weight="700" fill="#374151">${esc(item.id)} · LAYOUT ${layout}</text>`;
  const copy = `<rect x="100" y="230" width="650" height="250" rx="22" fill="#D1D5DB"/><text x="130" y="310" font-family="Arial" font-size="28" fill="#4B5563">LEVEL 1 / HEADLINE</text><rect x="100" y="520" width="650" height="170" rx="22" fill="#E5E7EB"/><text x="130" y="600" font-family="Arial" font-size="26" fill="#6B7280">LEVEL 2 / BENEFIT</text>`;
  if (index === 0) return `<svg xmlns="http://www.w3.org/2000/svg" width="2000" height="2000">${header}<rect x="360" y="250" width="1280" height="1500" rx="36" fill="#D1D5DB"/><text x="1000" y="1030" text-anchor="middle" font-family="Arial" font-size="42" fill="#4B5563">OFFICIAL PRODUCT / WHITE</text></svg>`;
  if (layout === "B") return `<svg xmlns="http://www.w3.org/2000/svg" width="2000" height="2000">${header}<rect x="700" y="270" width="600" height="1030" rx="30" fill="#C7CDD3"/><text x="1000" y="820" text-anchor="middle" font-family="Arial" font-size="36" fill="#4B5563">PRODUCT</text><rect x="90" y="520" width="460" height="330" rx="24" fill="#E5E7EB"/><rect x="1450" y="520" width="460" height="330" rx="24" fill="#E5E7EB"/><rect x="300" y="1450" width="1400" height="260" rx="24" fill="#D1D5DB"/></svg>`;
  if (layout === "C") return `<svg xmlns="http://www.w3.org/2000/svg" width="2000" height="2000">${header}<rect x="70" y="170" width="1860" height="1660" rx="30" fill="#C7CDD3"/><text x="1000" y="850" text-anchor="middle" font-family="Arial" font-size="46" fill="#4B5563">LIFESTYLE SCENE</text><rect x="110" y="1130" width="820" height="520" rx="30" fill="#F3F4F6"/><rect x="1480" y="1280" width="350" height="350" rx="175" fill="#E5E7EB"/></svg>`;
  if (["D", "E", "F"].includes(layout)) return `<svg xmlns="http://www.w3.org/2000/svg" width="2000" height="2000">${header}${copy}<rect x="850" y="250" width="900" height="760" rx="30" fill="#C7CDD3"/><text x="1300" y="660" text-anchor="middle" font-family="Arial" font-size="40" fill="#4B5563">OFFICIAL PRODUCT</text><rect x="100" y="1180" width="520" height="390" rx="28" fill="#E5E7EB"/><rect x="740" y="1180" width="520" height="390" rx="28" fill="#E5E7EB"/><rect x="1380" y="1180" width="520" height="390" rx="28" fill="#E5E7EB"/></svg>`;
  return `<svg xmlns="http://www.w3.org/2000/svg" width="2000" height="2000">${header}${copy}<rect x="860" y="210" width="1040" height="1320" rx="34" fill="#C7CDD3"/><text x="1380" y="900" text-anchor="middle" font-family="Arial" font-size="42" fill="#4B5563">PRODUCT / LIFESTYLE</text><rect x="100" y="1510" width="650" height="220" rx="28" fill="#D1D5DB"/></svg>`;
}

function productSvg(item, productUri, sceneUri, index, round = 2) {
  const [background, ink, accent] = STAGE_COLORS[index] || STAGE_COLORS[0];
  const h = item.headline || item.keyMessage || ""; const sub = item.subcopy || ""; const proofs = item.informationHierarchy?.level3 || [];
  const scale = round === 1 ? 0.88 : 1;
  if (index === 0) return null;
  if (item.layoutId === "A") return `<svg xmlns="http://www.w3.org/2000/svg" width="2000" height="2000" viewBox="0 0 2000 2000">${defs()}<rect width="2000" height="2000" fill="url(#mint)"/><circle cx="1580" cy="350" r="450" fill="#A9DDD2" opacity=".55"/><rect width="790" height="2000" fill="#FFFFFF" opacity=".88"/><text x="120" y="250" font-family="Arial" font-size="25" font-weight="700" fill="#23A78E" letter-spacing="3">SWITCHBOT</text>${svgText(h, 118, 500, { max: 7, limit: 3, size: 82, fill: ink })}${svgText(sub, 124, 870, { max: 13, limit: 4, size: 36, weight: 500, fill: ink, gap: 1.5 })}${proofPills(proofs, 120, 1250, 600, "#E8F5F1", ink, 2)}<image href="${esc(productUri)}" x="${900 + (1 - scale) * 450}" y="${280 + (1 - scale) * 500}" width="${900 * scale}" height="${1220 * scale}" preserveAspectRatio="xMidYMid meet" filter="url(#shadow)"/><rect x="910" y="1590" width="850" height="10" rx="5" fill="#23B69A" opacity=".7"/></svg>`;
  if (item.layoutId === "B") {
    const callouts = proofs.length >= 2 ? proofs.slice(0, 2) : [proofs[0] || "対象操作は設定により異なる", item.keyMessage || "よく使う操作へアクセス"];
    return `<svg xmlns="http://www.w3.org/2000/svg" width="2000" height="2000" viewBox="0 0 2000 2000">${defs()}<rect width="2000" height="2000" fill="${background}"/><circle cx="1000" cy="990" r="680" fill="${accent}" opacity=".34"/>${svgText(h, 1000, 250, { max: 17, limit: 2, size: 78, fill: ink, anchor: "middle" })}<image href="${esc(productUri)}" x="650" y="460" width="700" height="970" preserveAspectRatio="xMidYMid meet" filter="url(#shadow)"/><path d="M720 760 C560 760 520 720 430 650" fill="none" stroke="#23A98F" stroke-width="8"/><path d="M1280 900 C1450 900 1510 850 1580 780" fill="none" stroke="#23A98F" stroke-width="8"/><g transform="translate(90 520)"><rect width="510" height="270" rx="32" fill="#fff" filter="url(#shadow)"/><text x="42" y="62" font-family="Arial" font-size="21" font-weight="700" fill="#23A98F">POINT 01</text>${svgText(callouts[0] || "操作をひとつに", 42, 132, { max: 11, limit: 3, size: 30, fill: ink })}</g><g transform="translate(1400 650)"><rect width="510" height="270" rx="32" fill="#fff" filter="url(#shadow)"/><text x="42" y="62" font-family="Arial" font-size="21" font-weight="700" fill="#23A98F">POINT 02</text>${svgText(callouts[1] || compact(sub, 20), 42, 132, { max: 11, limit: 3, size: 30, fill: ink })}</g><rect x="210" y="1570" width="1580" height="220" rx="34" fill="#FFFFFF" opacity=".88"/>${svgText(sub, 1000, 1660, { max: 34, limit: 2, size: 36, weight: 500, fill: ink, anchor: "middle" })}</svg>`;
  }
  if (item.layoutId === "C") {
    const backgroundUri = sceneUri || productUri;
    return `<svg xmlns="http://www.w3.org/2000/svg" width="2000" height="2000" viewBox="0 0 2000 2000">${defs()}<image href="${esc(backgroundUri)}" width="2000" height="2000" preserveAspectRatio="xMidYMid slice"/><rect width="2000" height="2000" fill="url(#darkFade)"/><rect x="90" y="980" width="840" height="750" rx="42" fill="#0F2321" opacity=".72"/>${svgText(h, 150, 1160, { max: 14, limit: 3, size: 80, fill: "#FFFFFF" })}${svgText(sub, 156, 1480, { max: 26, limit: 3, size: 36, weight: 500, fill: "#FFFFFF", gap: 1.5 })}<circle cx="1650" cy="1570" r="265" fill="#FFFFFF" opacity=".92" filter="url(#shadow)"/><image href="${esc(productUri)}" x="1450" y="1350" width="400" height="440" preserveAspectRatio="xMidYMid meet"/></svg>`;
  }
  const cards = (proofs.length ? proofs : [compact(item.keyMessage, 22), compact(sub, 22), "購入前に条件を確認"]).filter(Boolean).slice(0, 3);
  const cardDisplay = (value) => /要照合/.test(value) ? `${String(value).replace(/[（(].*?[）)]/g, "").trim()}\n要照合` : value;
  return `<svg xmlns="http://www.w3.org/2000/svg" width="2000" height="2000" viewBox="0 0 2000 2000">${defs()}<rect width="2000" height="2000" fill="${background}"/><rect x="80" y="90" width="1840" height="1820" rx="54" fill="#FFFFFF" opacity=".82"/>${svgText(h, 120, 300, { max: 10, limit: 3, size: 68, fill: ink })}${svgText(sub, 124, 570, { max: 20, limit: 3, size: 32, weight: 500, fill: ink, gap: 1.5 })}<image href="${esc(productUri)}" x="1030" y="180" width="760" height="820" preserveAspectRatio="xMidYMid meet" filter="url(#shadow)"/>${cards.slice(0, 3).map((card, i) => `<g transform="translate(${120 + i * 595} 1180)"><rect width="520" height="420" rx="38" fill="${i === 0 ? accent : "#F6F8F8"}" opacity="${i === 0 ? .64 : 1}"/><circle cx="64" cy="66" r="28" fill="#23A98F"/><text x="64" y="76" text-anchor="middle" font-family="Arial" font-size="26" font-weight="700" fill="#fff">${i + 1}</text>${svgText(cardDisplay(card), 52, 170, { max: 13, limit: 4, size: 30, weight: 650, fill: ink })}</g>`).join("")}</svg>`;
}

function moduleWireframeSvg(module, index) {
  const units = module.units || []; const count = Math.max(1, Math.min(4, units.length)); const slot = 1324 / count;
  const cards = Array.from({ length: count }, (_, i) => `<rect x="${70 + i * slot}" y="230" width="${Math.floor(slot - 20)}" height="430" rx="20" fill="${i % 2 ? "#D1D5DB" : "#E5E7EB"}"/><text x="${70 + i * slot + (slot - 20) / 2}" y="470" text-anchor="middle" font-family="Arial" font-size="24" fill="#4B5563">UNIT ${i + 1}</text>`).join("");
  return `<svg xmlns="http://www.w3.org/2000/svg" width="1464" height="760"><rect width="1464" height="760" fill="#F5F6F7"/><text x="60" y="70" font-family="Arial" font-size="30" font-weight="700" fill="#374151">A+ ${String(index + 1).padStart(2, "0")} · ${esc(module.templateType)}</text><rect x="60" y="105" width="600" height="80" rx="16" fill="#D1D5DB"/><text x="85" y="155" font-family="Arial" font-size="24" fill="#4B5563">MODULE HEADLINE / STORY ROLE</text>${cards}<text x="732" y="720" text-anchor="middle" font-family="Arial" font-size="20" fill="#6B7280">${esc(module.templateName)} · ${units.length} content unit(s)</text></svg>`;
}

function moduleDimensions(template) {
  if (template === "SB-A01") return [1464, 600]; if (template === "SB-A03") return [1464, 760]; if (template === "SB-A04") return [1464, 680]; if (template === "SB-A07") return [1464, 760]; if (template === "SB-A08") return [1464, 700]; return [1464, 620];
}

function moduleSvg(module, preparedUnits, index) {
  const template = module.templateType; const [width, height] = moduleDimensions(template); const units = preparedUnits; const lead = units[0];
  const [bg, ink, accent] = STAGE_COLORS[index % STAGE_COLORS.length]; const product = lead?.productUri || "";
  const scene = units.find((x) => x.sceneUri)?.sceneUri || lead?.sceneUri || ""; const h = lead?.record.headline || module.purpose || ""; const copy = lead?.record.copy || "";
  if (template === "SB-A01") return `<svg xmlns="http://www.w3.org/2000/svg" width="${width}" height="${height}" viewBox="0 0 ${width} ${height}">${defs()}<rect width="${width}" height="${height}" fill="url(#mint)"/>${scene ? `<image href="${esc(scene)}" width="${width}" height="${height}" preserveAspectRatio="xMidYMid slice"/><rect width="${width}" height="${height}" fill="url(#darkFade)"/>` : ""}<rect width="620" height="${height}" fill="#FFFFFF" opacity="${scene ? .90 : .76}"/><text x="62" y="86" font-family="Arial" font-size="17" font-weight="700" fill="#23A98F" letter-spacing="2">SWITCHBOT</text>${svgText(h, 60, 205, { max: 17, limit: 3, size: 50, fill: ink })}${svgText(copy, 64, 410, { max: 32, limit: 3, size: 23, weight: 500, fill: ink, gap: 1.5 })}<image href="${esc(product)}" x="820" y="45" width="540" height="510" preserveAspectRatio="xMidYMid meet" filter="url(#shadow)"/></svg>`;
  if (template === "SB-A04") return `<svg xmlns="http://www.w3.org/2000/svg" width="${width}" height="${height}" viewBox="0 0 ${width} ${height}">${defs()}<image href="${esc(scene || product)}" width="${width}" height="${height}" preserveAspectRatio="xMidYMid slice"/><rect width="${width}" height="${height}" fill="url(#darkFade)"/><rect x="50" y="120" width="570" height="430" rx="28" fill="#102321" opacity=".66"/>${svgText(h, 90, 230, { max: 16, limit: 3, size: 46, fill: "#fff" })}${svgText(copy, 94, 430, { max: 31, limit: 3, size: 22, weight: 500, fill: "#fff", gap: 1.45 })}</svg>`;
  if (template === "SB-A03") {
    const count = Math.max(1, Math.min(3, units.length));
    return `<svg xmlns="http://www.w3.org/2000/svg" width="${width}" height="${height}" viewBox="0 0 ${width} ${height}">${defs()}<rect width="${width}" height="${height}" fill="#F7FAFA"/>${svgText(module.moduleHeadline || "毎日の操作を、もっとシンプルに。", 732, 86, { max: 25, limit: 1, size: 38, fill: ink, anchor: "middle" })}${units.slice(0, count).map((entry, i) => `<g transform="translate(${70 + i * 462} 160)"><rect width="414" height="520" rx="30" fill="#FFFFFF" filter="url(#shadow)"/><rect width="414" height="255" rx="30" fill="${accent}" opacity=".35"/><image href="${esc(entry.sceneUri || entry.productUri)}" x="25" y="20" width="364" height="220" preserveAspectRatio="xMidYMid meet"/>${svgText(entry.record.headline, 30, 330, { max: 13, limit: 2, size: 25, fill: ink })}${svgText(entry.record.copy, 30, 420, { max: 22, limit: 3, size: 16, weight: 500, fill: ink, gap: 1.45 })}</g>`).join("")}</svg>`;
  }
  if (["SB-A07", "SB-A08"].includes(template)) {
    const count = Math.max(1, Math.min(3, units.length));
    return `<svg xmlns="http://www.w3.org/2000/svg" width="${width}" height="${height}" viewBox="0 0 ${width} ${height}">${defs()}<rect width="${width}" height="${height}" fill="${bg}"/>${svgText(h, 68, 105, { max: 25, limit: 2, size: 42, fill: ink })}<image href="${esc(product)}" x="1040" y="35" width="350" height="245" preserveAspectRatio="xMidYMid meet"/>${units.slice(0, count).map((entry, i) => `<g transform="translate(70 ${220 + i * 165})"><rect width="1324" height="135" rx="24" fill="#FFFFFF"/><circle cx="64" cy="67" r="27" fill="#23A98F"/><text x="64" y="76" text-anchor="middle" font-family="Arial" font-size="23" font-weight="700" fill="#fff">${i + 1}</text>${svgText(entry.record.headline, 118, 55, { max: 28, limit: 1, size: 25, fill: ink })}${svgText(entry.record.copy, 118, 98, { max: 55, limit: 1, size: 17, weight: 500, fill: ink })}</g>`).join("")}</svg>`;
  }
  const secondary = units[1];
  return `<svg xmlns="http://www.w3.org/2000/svg" width="${width}" height="${height}" viewBox="0 0 ${width} ${height}">${defs()}<rect width="${width}" height="${height}" fill="${bg}"/><rect width="650" height="${height}" fill="#FFFFFF"/>${svgText(h, 62, 165, { max: 13, limit: 3, size: 44, fill: ink })}${svgText(copy, 66, 395, { max: 23, limit: 5, size: 22, weight: 500, fill: ink, gap: 1.42 })}<rect x="720" y="45" width="680" height="${height - 90}" rx="30" fill="${accent}" opacity=".38"/><image href="${esc(scene || product)}" x="750" y="70" width="620" height="${height - 140}" preserveAspectRatio="xMidYMid meet" filter="url(#shadow)"/>${secondary ? `<rect x="760" y="${height - 168}" width="580" height="105" rx="22" fill="#FFFFFF" opacity=".94"/>${svgText(secondary.record.headline, 1050, height - 105, { max: 23, limit: 1, size: 21, fill: ink, anchor: "middle" })}` : ""}</svg>`;
}

async function renderMain(sharp, sourceFile, outputFile) {
  const product = await sharp(sourceFile).rotate().resize(1660, 1660, { fit: "contain", background: { r: 255, g: 255, b: 255, alpha: 0 } }).png().toBuffer();
  await sharp({ create: { width: 2000, height: 2000, channels: 3, background: "#FFFFFF" } }).composite([{ input: product, gravity: "center" }]).jpeg({ quality: 94, chromaSubsampling: "4:4:4" }).toFile(outputFile);
}
async function renderSvg(sharp, svg, outputFile) { await sharp(Buffer.from(svg)).jpeg({ quality: 93, chromaSubsampling: "4:4:4" }).toFile(outputFile); }
async function sourceEntry(sharp, sourceFile) { if (!sourceFile || !(await exists(sourceFile))) return { exists: false }; const metadata = await sharp(sourceFile).metadata(); return { exists: true, sha256: await sha256(sourceFile), width: metadata.width, height: metadata.height, format: metadata.format }; }
async function writeSvg(file, svg) { await fs.mkdir(path.dirname(file), { recursive: true }); await fs.writeFile(file, svg, "utf8"); }
async function copySource(source, sourcesDir, inventory, id, layer) {
  if (!source || !(await exists(source))) return; const filename = `${id.toLowerCase().replace(/[^a-z0-9]+/g, "-")}-${layer}${path.extname(source) || ".img"}`; const target = path.join(sourcesDir, filename);
  if (!(await exists(target))) await fs.copyFile(source, target); inventory.push({ id, layer, source, editableCopy: `design/sources/${filename}`, sha256: await sha256(source) });
}

export async function produceFinalVisuals(data, outputDir) {
  normalizeCreativeSystem(data);
  const { default: sharp } = await import("sharp");
  const productDir = path.join(outputDir, "design", "product_images"); const aplusDir = path.join(outputDir, "design", "aplus");
  const sourcesDir = path.join(outputDir, "design", "sources"); const editableDir = path.join(outputDir, "design", "editable");
  await Promise.all([productDir, aplusDir, sourcesDir, editableDir].map((dir) => fs.mkdir(dir, { recursive: true })));
  const manifest = { schemaVersion: "3.0", visualWorkflow: data.meta.visualWorkflow, formalAssetRule: "Product body must come from user-provided official asset; AI product generation or redraw is prohibited.", userOfficialOrigin: USER_OFFICIAL_ORIGIN, allowedOfficialTypes: [...OFFICIAL_TYPES], productImages: [], aplusModules: [], sources: [] };

  for (let index = 0; index < data.images.length; index += 1) {
    const item = data.images[index]; const source = resolveSources(item, data, outputDir); const sourceInfo = await sourceEntry(sharp, source.productAbsolute); const sceneInfo = await sourceEntry(sharp, source.sceneAbsolute); const meta = sourceMetadata(item, data);
    item.sourceOrigin = meta.origin; item.sourceAssetType = meta.type; item.productBodyAiGenerated = meta.productBodyAiGenerated; item.aiGeneratedElements = meta.aiGeneratedElements;
    item.wireframePath = `design/editable/wireframes/product_images/${PRODUCT_FILENAMES[index].replace(".jpg", "_wireframe.svg")}`;
    await writeSvg(path.join(outputDir, item.wireframePath), productWireframeSvg(item, index));
    const outputFile = path.join(productDir, PRODUCT_FILENAMES[index]); const round1File = path.join(editableDir, "round_01", "product_images", PRODUCT_FILENAMES[index]);
    const editableSvgFile = path.join(editableDir, "final", "product_images", PRODUCT_FILENAMES[index].replace(".jpg", ".svg")); await fs.mkdir(path.dirname(round1File), { recursive: true });
    let rendered = false; let finalSvg = "";
    if (sourceInfo.exists) {
      if (index === 0) {
        await renderMain(sharp, source.productAbsolute, round1File); await renderMain(sharp, source.productAbsolute, outputFile);
        finalSvg = `<svg xmlns="http://www.w3.org/2000/svg" width="2000" height="2000"><rect width="2000" height="2000" fill="#fff"/><text x="1000" y="100" text-anchor="middle" font-family="Arial" font-size="20" fill="#9CA3AF">EDITABLE MAIN IMAGE — replace linked official product source if needed</text></svg>`;
      } else {
        const productUri = await dataUri(source.productAbsolute); const sceneUri = sceneInfo.exists ? await dataUri(source.sceneAbsolute) : null;
        await renderSvg(sharp, productSvg(item, productUri, sceneUri, index, 1), round1File); finalSvg = productSvg(item, productUri, sceneUri, index, 2); await renderSvg(sharp, finalSvg, outputFile);
      }
      rendered = true;
    } else {
      finalSvg = `<svg xmlns="http://www.w3.org/2000/svg" width="2000" height="2000"><rect width="2000" height="2000" fill="#F3F4F6"/><text x="1000" y="1000" text-anchor="middle" font-family="Arial" font-size="54" fill="#6B7280">Official product asset required</text></svg>`;
      await renderSvg(sharp, finalSvg, round1File); await renderSvg(sharp, finalSvg, outputFile);
    }
    await writeSvg(editableSvgFile, finalSvg);
    item.round1Path = path.relative(outputDir, round1File); item.editablePath = path.relative(outputDir, editableSvgFile); item.round1Review = round1Audit(item, "image"); item.round2Qa = finalAudit(item, "image");
    if (item.round2Qa.status !== "Pass") throw new Error(`${item.id} rejected after Round 2: ${item.round2Qa.issues.join("; ")}`);
    item.finalPath = `design/product_images/${PRODUCT_FILENAMES[index]}`; item.mockupPath = item.finalPath;
    item.outputSha256 = await sha256(outputFile);
    item.creativeReviewResult = evaluateCreativeReview(item.creativeReview, { id: item.id, path: item.finalPath, sha256: item.outputSha256 });
    item.designQaStatus = item.creativeReviewResult.status;
    item.visualProductionStatus = publicationStatus(item, meta, sourceInfo.exists, claimReady(item, data), item.designQaStatus === "Pass");
    await copySource(source.productAbsolute, sourcesDir, manifest.sources, item.id, "product"); await copySource(source.sceneAbsolute, sourcesDir, manifest.sources, item.id, "scene");
    manifest.productImages.push({ id: item.id, layoutId: item.layoutId, wireframePath: item.wireframePath, round1Path: item.round1Path, editablePath: item.editablePath, finalPath: item.finalPath, productSourcePath: source.productValue, sceneSourcePath: source.sceneValue, sourceOrigin: meta.origin, sourceAssetType: meta.type, productSource: sourceInfo, sceneSource: sceneInfo, productBodyAiGenerated: meta.productBodyAiGenerated, aiGeneratedElements: meta.aiGeneratedElements, operations: ["wireframe", "official product decode", sceneInfo.exists ? "separate scene/background decode" : "brand background construction", "Round 1 composition", "content/layout metadata audit", "Round 2 controlled SVG composition", "programmatic Japanese typography", "JPEG export"], round1Review: item.round1Review, round2Qa: item.round2Qa, creativeReview: item.creativeReviewResult, output: await sourceEntry(sharp, outputFile), visualProductionStatus: item.visualProductionStatus, rendered });
  }

  for (let index = 0; index < data.aplusModules.length; index += 1) {
    const module = data.aplusModules[index]; const preparedUnits = []; const metas = [];
    for (const unit of module.units || []) {
      const source = resolveSources(unit, data, outputDir); const sourceInfo = await sourceEntry(sharp, source.productAbsolute); const sceneInfo = await sourceEntry(sharp, source.sceneAbsolute); const meta = sourceMetadata(unit, data);
      unit.sourceOrigin = meta.origin; unit.sourceAssetType = meta.type; unit.productBodyAiGenerated = meta.productBodyAiGenerated; unit.aiGeneratedElements = meta.aiGeneratedElements;
      unit.round1Review = round1Audit(unit, "aplus"); unit.round2Qa = finalAudit(unit, "aplus", module.templateType);
      if (unit.round2Qa.status !== "Pass") throw new Error(`${unit.id} rejected after Round 2: ${unit.round2Qa.issues.join("; ")}`);
      preparedUnits.push({ record: unit, productUri: sourceInfo.exists ? await dataUri(source.productAbsolute) : "", sceneUri: sceneInfo.exists ? await dataUri(source.sceneAbsolute) : "", source, sourceInfo, sceneInfo, meta }); metas.push(meta);
      await copySource(source.productAbsolute, sourcesDir, manifest.sources, unit.id, "product"); await copySource(source.sceneAbsolute, sourcesDir, manifest.sources, unit.id, "scene");
    }
    const filename = `aplus_${String(index + 1).padStart(2, "0")}.jpg`; module.wireframePath = `design/editable/wireframes/aplus/${filename.replace(".jpg", "_wireframe.svg")}`;
    await writeSvg(path.join(outputDir, module.wireframePath), moduleWireframeSvg(module, index));
    if (["SB-A02", "SB-A05", "SB-A06"].includes(module.templateType) && preparedUnits[1] && chars(preparedUnits[1].record.headline).length > 23) throw new Error(`${module.id} rejected after Round 2: secondary headline exceeds 50/50 safe area`);
    if (module.templateType === "SB-A03" && chars(module.moduleHeadline || "").length > 25) throw new Error(`${module.id} rejected after Round 2: module headline exceeds grid safe area`);
    const round1File = path.join(editableDir, "round_01", "aplus", filename); const editableSvgFile = path.join(editableDir, "final", "aplus", filename.replace(".jpg", ".svg")); const outputFile = path.join(aplusDir, filename);
    await fs.mkdir(path.dirname(round1File), { recursive: true }); const composedSvg = moduleSvg(module, preparedUnits, index); await renderSvg(sharp, composedSvg, round1File); await renderSvg(sharp, composedSvg, outputFile); await writeSvg(editableSvgFile, composedSvg);
    module.round1Path = path.relative(outputDir, round1File); module.editablePath = path.relative(outputDir, editableSvgFile); module.finalPath = `design/aplus/${filename}`; module.mockupPath = module.finalPath;
    module.round1Review = preparedUnits.flatMap((x) => x.record.round1Review); module.round2Qa = { status: preparedUnits.every((x) => x.record.round2Qa.status === "Pass") ? "Pass" : "Reject", scope: "CONTENT_AND_LAYOUT_METADATA_ONLY", issues: preparedUnits.flatMap((x) => x.record.round2Qa.issues), intendedMessage: compact(module.purpose, 28), fiveSecondMessage: null };
    module.outputSha256 = await sha256(outputFile);
    module.creativeReviewResult = evaluateCreativeReview(module.creativeReview, { id: module.id, path: module.finalPath, sha256: module.outputSha256 });
    module.designQaStatus = module.creativeReviewResult.status;
    const allSources = preparedUnits.length > 0 && preparedUnits.every((x) => x.sourceInfo.exists); const allClaims = (module.units || []).every((x) => claimReady(x, data));
    const allOfficial = metas.length > 0 && metas.every((meta) => meta.origin === USER_OFFICIAL_ORIGIN && OFFICIAL_TYPES.has(meta.type) && meta.productBodyAiGenerated === false);
    module.visualProductionStatus = !allSources || module.round2Qa.status !== "Pass" ? "Blocked" : !allOfficial ? "Blocked" : !allClaims || module.moduleAvailability !== "Confirmed" || module.designQaStatus !== "Pass" ? "Need Verification" : "Final Ready";
    for (const unit of module.units || []) { unit.moduleFinalPath = module.finalPath; unit.visualProductionStatus = module.visualProductionStatus; }
    manifest.aplusModules.push({ id: module.id, templateType: module.templateType, visualUnits: module.units.length, wireframePath: module.wireframePath, round1Path: module.round1Path, editablePath: module.editablePath, finalPath: module.finalPath, round1Review: module.round1Review, round2Qa: module.round2Qa, creativeReview: module.creativeReviewResult, operations: ["module wireframe", "official product/scene source assembly", "Round 1 module composition", "content/layout metadata audit", "Round 2 controlled SVG composition", "programmatic Japanese typography", "JPEG export"], output: await sourceEntry(sharp, outputFile), visualProductionStatus: module.visualProductionStatus });
  }
  await fs.writeFile(path.join(sourcesDir, "source_inventory.json"), JSON.stringify(manifest.sources, null, 2), "utf8");
  await fs.writeFile(path.join(outputDir, "visual_production_manifest.json"), JSON.stringify(manifest, null, 2), "utf8"); return manifest;
}

export function evaluatePublishGate(data) {
  const reasons = []; const units = (data.aplusModules || []).flatMap((module) => module.units || []); const visuals = [...(data.images || []), ...units];
  if (!data.meta.externalPublishReady) reasons.push("meta.externalPublishReady is false");
  if (data.meta.moduleAvailability !== "Confirmed" || (data.aplusModules || []).some((module) => module.moduleAvailability !== "Confirmed")) reasons.push("Amazon A+ module availability is not Confirmed");
  const nonApprovedClaims = (data.claims || []).filter((claim) => claim.usedInExternalCopy && claim.status !== "Approved"); if (nonApprovedClaims.length) reasons.push(`${nonApprovedClaims.length} external Claim(s) are not Approved`);
  const nonFinal = [...(data.images || []), ...(data.aplusModules || [])].filter((record) => record.visualProductionStatus !== "Final Ready"); if (nonFinal.length) reasons.push(`${nonFinal.length} final visual(s) are not Final Ready`);
  const unreviewed = [...(data.images || []), ...(data.aplusModules || [])].filter((record) =>
    evaluateCreativeReview(record.creativeReview, { id: record.id, path: record.finalPath, sha256: record.outputSha256 }).status !== "Pass");
  if (unreviewed.length) reasons.push(`${unreviewed.length} visual(s) need a current creative review of the exported image`);
  const prohibitedAi = visuals.filter((record) => record.productBodyAiGenerated !== false); if (prohibitedAi.length) reasons.push(`${prohibitedAi.length} visual unit(s) do not explicitly prove productBodyAiGenerated=false`);
  const nonUserOfficial = visuals.filter((record) => record.sourceOrigin !== USER_OFFICIAL_ORIGIN || !OFFICIAL_TYPES.has(record.sourceAssetType)); if (nonUserOfficial.length) reasons.push(`${nonUserOfficial.length} visual unit(s) are not traced to user-provided official product assets`);
  if (data.meta.japanLocalizationStatus !== "Natural") reasons.push("Japanese consumer copy has unresolved localization or Claim review issues"); if (data.meta.visualConsistencyStatus !== "Pass") reasons.push("Visual consistency review is not Pass");
  const gate = reasons.length ? "Blocked" : "Ready"; data.meta.effectivePublishGate = gate; data.meta.publishGateReasons = reasons; return { gate, reasons };
}

export { OFFICIAL_TYPES, PRODUCT_FILENAMES, PRODUCT_LAYOUTS, TEMPLATE_NAMES, USER_OFFICIAL_ORIGIN };
