import fs from "node:fs/promises";
import path from "node:path";
import { evaluatePublishGate, normalizeCreativeSystem, OFFICIAL_TYPES, produceFinalVisuals, TEMPLATE_NAMES, USER_OFFICIAL_ORIGIN } from "./visual_pipeline.mjs";
import { buildLocalizationReview, buildVisualConsistencyReview, statusChinese } from "./review_checks.mjs";

export const STAGES = [
  ["understand_product", "理解产品", "これは何？"],
  ["spark_interest", "产生兴趣", "なぜ気になる？"],
  ["understand_advantage", "理解核心优势", "なぜ使いやすい？"],
  ["see_real_scenario", "看到真实场景", "暮らしでどう使う？"],
  ["build_trust", "相信产品", "何を根拠に信じる？"],
  ["check_fit", "判断适不适合自己", "自分の環境に合う？"],
  ["remove_objections", "消除购买顾虑", "買う前の不安は？"],
];

const STAGE_IDS = STAGES.map(([id]) => id);
const STATUS_COLORS = {
  Ready: "#DCFCE7",
  "Final Ready": "#DCFCE7",
  "Source Ready": "#DBEAFE",
  "Copy Ready": "#DBEAFE",
  Approved: "#DCFCE7",
  Confirmed: "#DCFCE7",
  "Need Design": "#FEF3C7",
  "Need Cutout": "#FEF3C7",
  "Need Composition": "#FEF3C7",
  "Need Lifestyle Generation": "#FEF3C7",
  "Need Copy": "#FEF3C7",
  "Asset Missing": "#FFEDD5",
  "Need Verification": "#FEF3C7",
  Conflict: "#FEE2E2",
  Blocked: "#FEE2E2",
  Unsupported: "#FEE2E2",
  Prohibited: "#FEE2E2",
  "Not Available": "#F1F5F9",
  "Not Applicable": "#F1F5F9",
};

const PALETTE = [
  ["#F8FAFC", "#0F172A", "#E2E8F0"],
  ["#E8F5F1", "#123D36", "#A7D9CC"],
  ["#EEF2FF", "#243B7A", "#C7D2FE"],
  ["#F3EFE8", "#3D342B", "#DDD0BF"],
  ["#EEF6F8", "#173B45", "#B8D9DF"],
  ["#FFF7E8", "#563B14", "#F1D49F"],
  ["#F8F4F1", "#4B302C", "#E7CBC4"],
];

export function parseArgs(argv) {
  const args = {};
  for (let i = 2; i < argv.length; i += 1) {
    const token = argv[i];
    if (!token.startsWith("--")) continue;
    const key = token.slice(2);
    if (key === "render-workbooks") args.renderWorkbooks = true;
    else args[key] = argv[++i];
  }
  return args;
}

export async function readJson(file) {
  return JSON.parse(await fs.readFile(file, "utf8"));
}

export function validateData(data) {
  const errors = [];
  const warnings = [];
  const required = ["meta", "product", "journey", "strategy", "titles", "bullets", "images", "aplusModules", "comparison", "seo", "faq", "assets", "sources", "missingInformation"];
  for (const key of required) if (data[key] === undefined) errors.push(`Missing top-level field: ${key}`);
  if (data.meta?.market !== "JP") errors.push("meta.market must be JP");
  if (!data.product?.name || !data.product?.brand || !data.product?.category) errors.push("product brand/name/category are required");
  if (!data.product?.mainImage) errors.push("product.mainImage is required");
  const journeyIds = (data.journey || []).map((x) => x.id);
  if (journeyIds.join("|") !== STAGE_IDS.join("|")) errors.push("journey must contain the seven canonical stages in order");
  if (!data.strategy?.coreValue || Array.isArray(data.strategy.coreValue)) errors.push("strategy.coreValue must be one string");
  if (!data.strategy?.heroSellingPoint || Array.isArray(data.strategy.heroSellingPoint)) errors.push("strategy.heroSellingPoint must be one object");
  if ((data.strategy?.coreSellingPoints || []).length > 5) errors.push("coreSellingPoints must not exceed 5");
  if ((data.bullets || []).length !== 5) errors.push("Exactly 5 bullets are required");
  if ((data.images || []).length !== 7) errors.push("Exactly 7 product images are required");
  (data.images || []).forEach((item, index) => {
    if (item.stage !== STAGE_IDS[index]) errors.push(`${item.id || `Image ${index + 1}`} must map to ${STAGE_IDS[index]}`);
    for (const field of ["id", "role", "userQuestion", "keyMessage", "assetRequirement", "claimSource", "risk", "status"]) {
      if (item[field] === undefined || item[field] === "") warnings.push(`${item.id || `Image ${index + 1}`} missing ${field}`);
    }
  });
  const units = (data.aplusModules || []).flatMap((module) => module.units || []);
  if (!(data.aplusModules || []).length) errors.push("At least one A+ module is required");
  if ((data.aplusModules || []).length > 8) warnings.push("A+ has more than 8 modules; verify the page rhythm is not overly long");
  const unitStages = units.map((unit) => unit.stage);
  for (const id of STAGE_IDS) if (!unitStages.includes(id)) errors.push(`A+ does not cover stage ${id}`);
  let lastStage = -1;
  for (const unit of units) {
    const index = STAGE_IDS.indexOf(unit.stage);
    if (index < 0) errors.push(`${unit.id || "A+ unit"} uses an invalid stage`);
    if (index < lastStage) errors.push(`${unit.id || "A+ unit"} reverses the decision journey`);
    lastStage = Math.max(lastStage, index);
    for (const field of ["id", "purpose", "userQuestion", "headline", "asset", "claimSource", "risk", "status"]) {
      if (unit[field] === undefined || unit[field] === "") warnings.push(`${unit.id || "A+ unit"} missing ${field}`);
    }
  }
  (data.aplusModules || []).forEach((module, index) => {
    const rawTemplate = module.templateType || module.templateId;
    if (!rawTemplate) warnings.push(`${module.id || `A+ module ${index + 1}`} missing templateType; the visual system will assign a compatibility template`);
    else if (!TEMPLATE_NAMES[rawTemplate] && !/^[A-J]$/.test(rawTemplate)) warnings.push(`${module.id || `A+ module ${index + 1}`} uses unknown templateType ${rawTemplate}`);
  });
  if ((data.faq || []).length < 8 || (data.faq || []).length > 15) errors.push("FAQ count must be between 8 and 15");
  const usedClaimIds = new Set([
    ...(data.bullets || []).flatMap((x) => x.claimIds || []),
    ...(data.images || []).flatMap((x) => x.claimIds || []),
    ...units.flatMap((x) => x.claimIds || []),
    ...(data.faq || []).flatMap((x) => x.claimIds || []),
  ]);
  const definedClaims = new Set((data.claims || []).map((x) => x.id));
  for (const claimId of usedClaimIds) if (!definedClaims.has(claimId)) errors.push(`Referenced claim not defined: ${claimId}`);
  if (data.meta?.externalPublishReady && (data.claims || []).some((x) => x.status !== "Approved" && x.usedInExternalCopy)) {
    errors.push("externalPublishReady cannot be true while external copy uses non-Approved claims");
  }
  const visualRecords = [...(data.images || []), ...units];
  for (const record of visualRecords) {
    const productAi = record.productBodyAiGenerated ?? data.product?.productBodyAiGenerated;
    const origin = record.sourceOrigin || record.productSourceOrigin || data.product?.mainImageOrigin || data.meta?.productAssetOrigin;
    const sourceType = record.sourceAssetType || record.productSourceType || data.product?.mainImageType;
    if (productAi === true) errors.push(`${record.id}: product body must never be AI-generated or AI-redrawn`);
    if (productAi !== false) warnings.push(`${record.id}: productBodyAiGenerated must be explicitly false before formal publication`);
    if (origin !== USER_OFFICIAL_ORIGIN) warnings.push(`${record.id}: sourceOrigin is not '${USER_OFFICIAL_ORIGIN}'; formal publication will be Blocked`);
    if (!OFFICIAL_TYPES.has(sourceType)) warnings.push(`${record.id}: sourceAssetType must be one of the approved official asset types before formal publication`);
  }
  return { errors, warnings, units };
}

function clone(value) {
  return JSON.parse(JSON.stringify(value));
}

function safeName(value) {
  return String(value || "asset").replace(/[^a-zA-Z0-9._-]+/g, "-").replace(/-+/g, "-").replace(/^-|-$/g, "");
}

function isUrl(value) {
  return /^https?:\/\//i.test(String(value || ""));
}

export async function prepareAssets(sourceData, inputFile, outputDir) {
  const data = clone(sourceData);
  const inputDir = path.dirname(path.resolve(inputFile));
  const assetDir = path.join(outputDir, "assets");
  await fs.mkdir(assetDir, { recursive: true });
  const copied = new Map();
  const claimedFilenames = new Map();
  let counter = 1;
  async function localize(value) {
    if (!value || isUrl(value)) return value;
    const absolute = path.isAbsolute(value) ? value : path.resolve(inputDir, value);
    if (copied.has(absolute)) return copied.get(absolute);
    try {
      await fs.access(absolute);
    } catch {
      return value;
    }
    const parsed = path.parse(absolute);
    let filename = safeName(`${parsed.name}${parsed.ext}`);
    while (claimedFilenames.has(filename) && claimedFilenames.get(filename) !== absolute) {
      filename = safeName(`${parsed.name}-${counter++}${parsed.ext}`);
    }
    claimedFilenames.set(filename, absolute);
    await fs.copyFile(absolute, path.join(assetDir, filename));
    const relative = `assets/${filename}`;
    copied.set(absolute, relative);
    return relative;
  }
  data.product.mainImage = await localize(data.product.mainImage);
  if (data.product.productSource) data.product.productSource = await localize(data.product.productSource);
  for (const item of data.images || []) {
    if (item.productSource) item.productSource = await localize(item.productSource);
    if (item.sceneSource) item.sceneSource = await localize(item.sceneSource);
    item.visualSrc = await localize(item.visualSrc || item.productSource || data.product.mainImage);
  }
  for (const module of data.aplusModules || []) {
    for (const unit of module.units || []) {
      if (unit.productSource) unit.productSource = await localize(unit.productSource);
      if (unit.sceneSource) unit.sceneSource = await localize(unit.sceneSource);
      unit.visualSrc = await localize(unit.visualSrc || unit.productSource || data.product.mainImage);
    }
  }
  for (const asset of data.assets || []) if (asset.file) asset.file = await localize(asset.file);
  return data;
}

function esc(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

function xml(value) {
  return esc(value);
}

function lines(value, max = 20, limit = 3) {
  const text = String(value || "").trim();
  if (!text) return [];
  const chars = [...text];
  const result = [];
  while (chars.length && result.length < limit) result.push(chars.splice(0, max).join(""));
  if (chars.length && result.length) result[result.length - 1] = `${result[result.length - 1].slice(0, Math.max(0, max - 1))}…`;
  return result;
}

function textSvg(text, x, y, opts = {}) {
  const { max = 20, limit = 3, size = 48, weight = 700, fill = "#0F172A", gap = 1.22, anchor = "start" } = opts;
  return lines(text, max, limit).map((line, index) => `<text x="${x}" y="${y + index * size * gap}" text-anchor="${anchor}" font-family="'Noto Sans JP','Hiragino Sans',Arial,sans-serif" font-size="${size}" font-weight="${weight}" fill="${fill}">${xml(line)}</text>`).join("\n");
}

async function svgAssetHref(assetPath, outputDir) {
  if (!assetPath || isUrl(assetPath)) return assetPath || "";
  try {
    const bytes = await fs.readFile(path.join(outputDir, assetPath));
    let mime = "application/octet-stream";
    if (bytes[0] === 0xff && bytes[1] === 0xd8) mime = "image/jpeg";
    else if (bytes[0] === 0x89 && bytes[1] === 0x50 && bytes[2] === 0x4e && bytes[3] === 0x47) mime = "image/png";
    else if (bytes.subarray(0, 4).toString("ascii") === "RIFF" && bytes.subarray(8, 12).toString("ascii") === "WEBP") mime = "image/webp";
    else if (/\.svg$/i.test(assetPath)) mime = "image/svg+xml";
    return `data:${mime};base64,${bytes.toString("base64")}`;
  } catch {
    return assetPath;
  }
}

function stageMeta(stage) {
  const index = Math.max(0, STAGE_IDS.indexOf(stage));
  return { index, label: STAGES[index]?.[1] || stage, colors: PALETTE[index] || PALETTE[0] };
}

function productSvg(item, product, embeddedSrc) {
  const { index, label, colors } = stageMeta(item.stage);
  const [bg, ink, accent] = colors;
  const src = embeddedSrc;
  const isMain = index === 0;
  if (isMain) {
    return `<svg xmlns="http://www.w3.org/2000/svg" width="1600" height="1600" viewBox="0 0 1600 1600"><rect width="1600" height="1600" fill="#fff"/><image href="${xml(src)}" x="90" y="90" width="1420" height="1420" preserveAspectRatio="xMidYMid meet"/></svg>`;
  }
  const lifestyle = item.stage === "see_real_scenario";
  const proof = item.stage === "build_trust";
  return `<svg xmlns="http://www.w3.org/2000/svg" width="1600" height="1600" viewBox="0 0 1600 1600">
    <defs><linearGradient id="shade" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#000" stop-opacity="0"/><stop offset="1" stop-color="#000" stop-opacity=".7"/></linearGradient><filter id="shadow"><feDropShadow dx="0" dy="22" stdDeviation="25" flood-opacity=".18"/></filter></defs>
    <rect width="1600" height="1600" fill="${bg}"/>
    ${lifestyle ? `<image href="${xml(src)}" width="1600" height="1600" preserveAspectRatio="xMidYMid slice"/><rect width="1600" height="1600" fill="url(#shade)"/>` : `<circle cx="1230" cy="330" r="310" fill="${accent}" opacity=".6"/><image href="${xml(src)}" x="690" y="250" width="760" height="890" preserveAspectRatio="xMidYMid meet" filter="url(#shadow)"/>`}
    <rect x="94" y="84" width="270" height="54" rx="27" fill="${lifestyle ? "#FFFFFF" : ink}" opacity=".94"/><text x="229" y="120" text-anchor="middle" font-family="'Noto Sans JP',Arial,sans-serif" font-size="24" font-weight="700" fill="${lifestyle ? ink : "#FFFFFF"}">${xml(`STEP ${index + 1} · ${label}`)}</text>
    ${textSvg(item.headline || item.keyMessage, 100, lifestyle ? 1120 : 310, { max: 17, limit: 3, size: 74, fill: lifestyle ? "#FFFFFF" : ink })}
    ${textSvg(item.subcopy, 104, lifestyle ? 1410 : 610, { max: 30, limit: 3, size: 34, weight: 500, fill: lifestyle ? "#FFFFFF" : ink, gap: 1.45 })}
    ${proof ? `<g transform="translate(110 920)"><rect width="500" height="190" rx="28" fill="#FFFFFF" opacity=".92"/><text x="36" y="60" font-family="Arial,sans-serif" font-size="24" font-weight="700" fill="${ink}">PROOF / CONDITIONS</text>${textSvg(item.supportingData || "Source condition required", 36, 118, { max: 24, limit: 2, size: 29, weight: 600, fill: ink })}</g>` : ""}
  </svg>`;
}

function parseRatio(value) {
  const match = String(value || "970:300").match(/(\d+)\s*[:x×]\s*(\d+)/);
  if (!match) return [970, 420];
  const width = 970;
  const height = Math.max(240, Math.min(700, Math.round(width * Number(match[2]) / Number(match[1]))));
  return [width, height];
}

function aplusSvg(unit, module, product, embeddedSrc) {
  const [width, height] = parseRatio(module.imageRatio);
  const { colors, label } = stageMeta(unit.stage);
  const [bg, ink, accent] = colors;
  const src = embeddedSrc;
  const imageX = Math.round(width * 0.56);
  const imageW = width - imageX;
  const darkOverlay = unit.stage === "see_real_scenario";
  const fontSize = height > 500 ? 42 : 34;
  return `<svg xmlns="http://www.w3.org/2000/svg" width="${width}" height="${height}" viewBox="0 0 ${width} ${height}">
    <defs><linearGradient id="fade" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="#000" stop-opacity=".72"/><stop offset="1" stop-color="#000" stop-opacity=".06"/></linearGradient></defs>
    <rect width="${width}" height="${height}" fill="${bg}"/>
    ${darkOverlay ? `<image href="${xml(src)}" width="${width}" height="${height}" preserveAspectRatio="xMidYMid slice"/><rect width="${width}" height="${height}" fill="url(#fade)"/>` : `<rect x="${imageX - 28}" y="0" width="${imageW + 28}" height="${height}" fill="${accent}" opacity=".42"/><image href="${xml(src)}" x="${imageX}" y="20" width="${imageW - 20}" height="${height - 40}" preserveAspectRatio="xMidYMid meet"/>`}
    <rect x="40" y="32" width="190" height="34" rx="17" fill="${darkOverlay ? "#FFFFFF" : ink}" opacity=".94"/><text x="135" y="55" text-anchor="middle" font-family="Arial,sans-serif" font-size="15" font-weight="700" fill="${darkOverlay ? ink : "#FFFFFF"}">${xml(label)}</text>
    ${textSvg(unit.headline, 42, Math.max(118, height * .34), { max: height > 500 ? 18 : 22, limit: 3, size: fontSize, fill: darkOverlay ? "#FFFFFF" : ink })}
    ${textSvg(unit.copy, 44, Math.max(232, height * .62), { max: 33, limit: height > 500 ? 4 : 2, size: height > 500 ? 24 : 19, weight: 500, fill: darkOverlay ? "#FFFFFF" : ink, gap: 1.45 })}
  </svg>`;
}

export async function generateMockups(data, outputDir) {
  return produceFinalVisuals(data, outputDir);
}

function markdownTable(headers, rows) {
  const clean = (value) => String(value ?? "").replaceAll("|", "\\|").replaceAll("\n", "<br>");
  return [`| ${headers.map(clean).join(" | ")} |`, `| ${headers.map(() => "---").join(" | ")} |`, ...rows.map((row) => `| ${row.map(clean).join(" | ")} |`)].join("\n");
}

export async function writeMarkdown(data, outputDir) {
  const title = data.titles[data.titles.recommendedKey] || data.titles.main;
  const units = data.aplusModules.flatMap((x) => x.units || []);
  const localization = buildLocalizationReview(data);
  const visual = buildVisualConsistencyReview(data);
  const { gate: publishGate, reasons } = evaluatePublishGate(data);
  const summary = `# 执行摘要\n\n## 结论\n\n- 已生成 7 张 Round 2 JPEG 商品图、${data.aplusModules.length} 张 Round 2 A+ 模块图（内部包含 ${units.length} 个内容单元）和 5 条 Bullet。A+ 数量由购买故事决定，不再以“至少15张横幅”为目标。\n- 每张正式视觉都保留 Wireframe、Round 1、Round 2 可编辑 SVG 与自动 QA。\n- 决策顺序：${STAGES.map((x) => x[1]).join(" → ")}。\n- Publish Gate：**${publishGate}**。${publishGate === "Ready" ? "已满足本次输入声明的外发门槛。" : "当前仅供内部审阅，不得直接上线。"}\n- 产品本体硬规则：必须来自用户提供的官方素材，且 \`productBodyAiGenerated=false\`；AI 仅可用于场景、人物、背景、灯光、道具与构图扩展。\n- 核心价值：${data.strategy.coreValue}\n- 推荐标题：${title}\n\n## 发布阻塞原因\n\n${reasons.map((reason) => `- ${reason}`).join("\n") || "- 无"}\n\n## 页面策略\n\n- 搜索意图：${data.strategy.searchIntent}\n- 主要受众：${data.strategy.primaryAudience}\n- 核心问题：${data.strategy.coreProblem}\n- 信任理由：${(data.strategy.reasonsToBelieve || []).join("；")}\n- 购买顾虑：${(data.strategy.objections || []).join("；")}\n\n## 最高优先级缺口\n\n${(data.missingInformation || []).map((x) => `- [${statusChinese(x.status)}] ${x.item}: ${x.impact}`).join("\n") || "- 无"}\n`;
  await fs.writeFile(path.join(outputDir, "executive_summary_cn.md"), summary, "utf8");
  await fs.writeFile(path.join(outputDir, "executive_summary.md"), summary, "utf8");

  const titleMd = `# Amazon Japan Title\n\n- Final Recommendation: ${title}\n- Status: ${data.titles.status}\n- Character Count: ${[...title].length}\n- Main Version: ${data.titles.main}\n- SEO Version: ${data.titles.seo}\n- Concise Version: ${data.titles.concise}\n- Main Keywords: ${(data.titles.mainKeywords || []).join("、")}\n- Keyword Logic: ${data.titles.keywordLogic}\n- Risk Check: ${data.titles.riskCheck}\n`;
  await fs.writeFile(path.join(outputDir, "amazon_title.md"), titleMd, "utf8");

  const consumerBullets = data.bullets.map((item) => `- 【${item.headline}】${item.body}`).join("\n");
  const finalCopyJa = `# 商品タイトル\n\n${title}\n\n# 商品仕様・説明\n\n${consumerBullets}\n`;
  await fs.writeFile(path.join(outputDir, "final_copy_ja.md"), finalCopyJa, "utf8");
  await fs.writeFile(path.join(outputDir, "final_copy.md"), `# Final Copy\n\nPublish Gate: **${publishGate}**\n\n> 正式发布前必须查看 executive_summary_cn.md、claim_check.md 与 visual_production_manifest.json。\n\n${finalCopyJa}`, "utf8");

  const faqJa = `# よくある質問\n\n${data.faq.map((item) => `## ${item.question}\n\n${item.answer}\n`).join("\n")}`;
  await fs.writeFile(path.join(outputDir, "faq_ja.md"), faqJa, "utf8");
  await fs.writeFile(path.join(outputDir, "faq.md"), faqJa, "utf8");

  const claimRows = (data.claims || []).map((x) => [x.id, x.copy, x.status, x.sourceId, x.sourceUrl, x.conditions, x.risk, x.usedInExternalCopy ? "Yes" : "No"]);
  await fs.writeFile(path.join(outputDir, "claim_check.md"), `# Claim Safety Check\n\nPublish Gate: **${publishGate}**\n\n${markdownTable(["Claim ID", "Copy", "Status", "Source ID", "Source URL", "Conditions", "Risk", "External Copy"], claimRows)}\n`, "utf8");
  await fs.writeFile(path.join(outputDir, "missing_information_checklist.md"), `# Missing Information Checklist\n\n${markdownTable(["Item", "Why Needed", "Impact", "Owner", "Status"], (data.missingInformation || []).map((x) => [x.item, x.whyNeeded, x.impact, x.owner, x.status]))}\n`, "utf8");
  await fs.writeFile(path.join(outputDir, "source_register.md"), `# Source Register\n\n${markdownTable(["Source ID", "Title", "Type", "URL / Path", "Market", "Last Verified", "Status", "Notes"], (data.sources || []).map((x) => [x.id, x.title, x.type, x.url || x.path, x.market, x.lastVerified, x.status, x.notes]))}\n`, "utf8");
  await fs.writeFile(path.join(outputDir, "visual_consistency_report.md"), visual.markdown, "utf8");
  await fs.writeFile(path.join(outputDir, "japan_localization_review.md"), localization.markdown, "utf8");
  const reportsDir = path.join(outputDir, "reports");
  await fs.mkdir(reportsDir, { recursive: true });
  const reviewRecords = [
    ...(data.images || []).map((x) => ({ id: x.id, placement: "商品图", review: x.copyReview })),
    ...units.map((x) => ({ id: x.id, placement: "A+ 内容单元", review: x.copyReview })),
  ];
  const copyRows = reviewRecords.flatMap((record) => (record.review?.options || []).map((option) => [record.id, record.placement, option.id, option.approach, option.text, option.scores?.naturalness, option.scores?.amazonReadability, option.scores?.claimAccuracy, option.scores?.mobileLength, option.scores?.total, option.id === record.review?.selected ? "Final" : "Candidate", record.review?.status]));
  const copyReport = `# Japanese Copy Review\n\n## 结论\n\n- 所有带文案的商品图与 A+ 内容单元均先生成 A / B / C 三案，再按日本自然度、Amazon 可读性、Claim 准确性与手机端长度评分。\n- 自动兼容生成的候选仍保留 \`Needs Japanese Copy Review\`，不得冒充人工日文终审。\n- Claim 分数不等于自然度分数；未批准 Claim 会单独阻塞发布。\n\n${markdownTable(["ID", "位置", "Option", "方向", "日文", "自然度", "Amazon可读性", "Claim准确性", "手机长度", "总分", "选择", "审阅状态"], copyRows)}\n`;
  await fs.writeFile(path.join(reportsDir, "japanese_copy_review.md"), copyReport, "utf8");
  const qaRows = [
    ...(data.images || []).map((x) => [x.id, x.userQuestion, `Layout ${x.layoutId}`, x.round1Review, x.round2Qa?.status, x.round2Qa?.fiveSecondMessage, x.mobileSafeArea || x.wireframe?.mobileRule, x.productBodyAiGenerated === false ? "产品本体非AI" : "产品来源门槛未通过", x.visualProductionStatus]),
    ...(data.aplusModules || []).map((x) => [x.id, x.storyRole || x.purpose, x.templateType, x.round1Review, x.round2Qa?.status, x.round2Qa?.fiveSecondMessage, x.mobileConsideration, (x.units || []).every((u) => u.productBodyAiGenerated === false) ? "产品本体非AI" : "产品来源门槛未通过", x.visualProductionStatus]),
  ];
  const qaReport = `# Visual QA\n\n## 结论\n\n- 自动拒绝条件：文案超载、无固定版式、超过3层信息、产品本体AI状态不合格、Round 2仍不满足5秒理解与移动端密度。\n- Final 目录只收录 Round 2 通过 Design QA 的 JPEG；发布状态仍由独立 Claim / 素材门槛决定。\n\n${markdownTable(["Visual", "购买问题 / 作用", "Layout / Template", "Round 1审阅", "Round 2", "5秒信息", "Mobile", "产品", "制作状态"], qaRows)}\n`;
  await fs.writeFile(path.join(reportsDir, "visual_qa.md"), qaReport, "utf8");
  const mappingRows = (data.aplusModules || []).map((module, index) => [index + 1, module.id, module.templateType, module.templateName, module.storyRole || module.purpose, (module.units || []).length, module.wireframePath, module.finalPath, module.moduleAvailability]);
  const templateReport = `# Amazon Template Mapping\n\n## A+ Story Rhythm\n\n${(data.aplusModules || []).map((module) => `${module.templateType} ${module.templateName}`).join(" → ")}\n\n${markdownTable(["顺序", "Module", "Template Type", "模板名", "购买职责", "内容单元", "Wireframe", "Final", "Amazon可用性"], mappingRows)}\n\n## 说明\n\n- 设计基线来自当前可访问的 SwitchBot Japan Amazon A+ 页面和 Amazon 官方 A+ 指南；模板结构不是产品 Claim 来源。\n- Seller Central 实际可用模块、账号资格与目标 ASIN 仍以发布当天的 Builder 为准。\n`;
  await fs.writeFile(path.join(reportsDir, "amazon_template_mapping.md"), templateReport, "utf8");
  const comparison = `# Hub 3 升级前后对比\n\n${markdownTable(["项目", "升级前", "升级后"], [
    ["产品本体来源", "原则性要求，生成器未做硬校验", "必须是 User Provided Official + 官方素材类型，否则 Blocked"],
    ["AI 产品本体", "没有机器可读的发布门槛", "productBodyAiGenerated 必须明确为 false；true 直接结构校验失败"],
    ["视觉产物", "每个内容单元一张横幅", "7 张商品图 + 按故事组合的 A+ 模块 JPEG，并记录 SHA-256"],
    ["主图", "SVG 中嵌入原图", "白底、居中、留白、等比缩放后重新合成输出"],
    ["消费者预览", "混入 Decision Journey、状态、SEO 与内部说明", "只显示日语消费者内容，模拟日亚首屏至 A+ / 比较 / FAQ"],
    ["设计审阅", "中英混合", "中文字段、中文状态、素材来源、产品 AI、Claim 和完成状态并列"],
    ["A+ 逻辑", "16个同规格Banner", "以 SB-A01—SB-A08 组合大图 / 双栏 / 网格 / 场景 / Proof / Comparison / FAQ 节奏"],
    ["设计过程", "直接合成 Final", "Composition Sheet → Wireframe → Round 1 → Visual Review → Round 2 → Final"],
    ["新增验收", "结构与浏览器检查", "增加自动拒绝、5秒理解、信息层级、移动端、产品来源与两轮QA"],
  ])}\n`;
  await fs.writeFile(path.join(outputDir, "upgrade_comparison.md"), comparison, "utf8");
}

function cellValue(value) {
  if (value === null || value === undefined) return "";
  if (Array.isArray(value)) return value.join(", ");
  if (typeof value === "object") return JSON.stringify(value);
  return value;
}

function colLetter(index) {
  let value = index + 1;
  let output = "";
  while (value) {
    value -= 1;
    output = String.fromCharCode(65 + (value % 26)) + output;
    value = Math.floor(value / 26);
  }
  return output;
}

async function createWorkbook(outputDir, spec, renderWorkbooks) {
  const { SpreadsheetFile, Workbook } = await import("@oai/artifact-tool");
  const workbook = Workbook.create();
  const sheet = workbook.worksheets.add(spec.sheetName);
  sheet.showGridLines = false;
  const cols = spec.columns;
  const rows = spec.rows.map((row) => row.map(cellValue));
  const lastCol = colLetter(cols.length - 1);
  sheet.getRange(`A1:${lastCol}1`).merge();
  sheet.getRange("A1").values = [[spec.title]];
  sheet.getRange(`A2:${lastCol}2`).merge();
  sheet.getRange("A2").values = [[spec.note || "Source-backed internal working file. Unknown values remain explicit."]];
  sheet.getRange(`A4:${lastCol}4`).values = [cols.map((x) => x.label)];
  if (rows.length) sheet.getRangeByIndexes(4, 0, rows.length, cols.length).values = rows;
  sheet.getRange(`A1:${lastCol}1`).format = { fill: "#0F766E", font: { bold: true, color: "#FFFFFF", size: 16 }, verticalAlignment: "center" };
  sheet.getRange(`A2:${lastCol}2`).format = { fill: "#E8F5F1", font: { color: "#315B54", italic: true, size: 10 }, wrapText: true };
  sheet.getRange(`A4:${lastCol}4`).format = { fill: "#163C35", font: { bold: true, color: "#FFFFFF" }, wrapText: true, verticalAlignment: "center" };
  sheet.getRange(`A1:${lastCol}${Math.max(5, rows.length + 4)}`).format.font = { name: "Arial", size: 10 };
  if (rows.length) {
    const body = sheet.getRange(`A5:${lastCol}${rows.length + 4}`);
    body.format = { wrapText: true, verticalAlignment: "top", borders: { preset: "insideHorizontal", style: "thin", color: "#E2E8F0" } };
    const table = sheet.tables.add(`A4:${lastCol}${rows.length + 4}`, true, `${safeName(spec.sheetName).replaceAll("-", "")}Table`);
    table.style = "TableStyleMedium2";
    const statusIndex = cols.findIndex((x) => /status/i.test(x.key));
    if (statusIndex >= 0) {
      for (let row = 0; row < rows.length; row += 1) {
        const status = String(rows[row][statusIndex] || "");
        const fill = STATUS_COLORS[status];
        if (fill) sheet.getCell(row + 4, statusIndex).format.fill = fill;
      }
    }
  }
  for (let index = 0; index < cols.length; index += 1) sheet.getRange(`${colLetter(index)}:${colLetter(index)}`).format.columnWidth = cols[index].width || 18;
  sheet.getRange("1:1").format.rowHeight = 28;
  sheet.getRange("2:2").format.rowHeight = 34;
  sheet.getRange("4:4").format.rowHeight = 34;
  sheet.freezePanes.freezeRows(4);
  const outputFile = path.join(outputDir, spec.filename);
  const blob = await SpreadsheetFile.exportXlsx(workbook);
  await blob.save(outputFile);
  const inspection = await workbook.inspect({ kind: "sheet,table,match", searchTerm: "#REF!|#DIV/0!|#VALUE!|#NAME\\?|#N/A", options: { useRegex: true, maxResults: 50 }, maxChars: 4000, tableMaxRows: 8, tableMaxCols: 12 });
  await fs.unlink(`${outputFile}.inspect.ndjson`).catch((error) => {
    if (error?.code !== "ENOENT") throw error;
  });
  if (renderWorkbooks) {
    const previewDir = path.join(outputDir, "qa", "workbook-previews");
    await fs.mkdir(previewDir, { recursive: true });
    const preview = await workbook.render({ sheetName: spec.sheetName, autoCrop: "all", scale: 1, format: "png" });
    await fs.writeFile(path.join(previewDir, spec.filename.replace(/\.xlsx$/i, ".png")), new Uint8Array(await preview.arrayBuffer()));
  }
  return { file: spec.filename, inspection: inspection.ndjson };
}

export async function writeCompositionWorkbook(data, outputDir, renderWorkbooks = false) {
  normalizeCreativeSystem(data);
  const rows = [
    ...(data.images || []).map((item, index) => [
      item.id, "Product Image", item.pageRole || item.role, item.layoutId, item.headline, item.subcopy,
      item.productSource || item.visualSrc || data.product.mainImage, item.sceneSource || "",
      (item.aiGeneratedElements || []).length ? "Yes" : "No", item.aiGeneratedElements,
      item.layerPlan?.graphic?.elements || [], item.designPriority || (index === 0 ? "SKU accuracy" : "Conversion clarity"),
      `Layout ${item.layoutId} planned`, item.copyReview?.status, item.claimSource, item.risk, item.status,
    ]),
    ...(data.aplusModules || []).map((module) => [
      module.id, "A+ Module", module.storyRole || module.purpose, module.templateType,
      module.units?.[0]?.headline || module.purpose, module.units?.map((x) => x.copy).filter(Boolean).join(" | "),
      module.units?.map((x) => x.productSource || x.visualSrc || data.product.mainImage).filter(Boolean),
      module.units?.map((x) => x.sceneSource).filter(Boolean),
      module.units?.some((x) => (x.aiGeneratedElements || []).length) ? "Yes" : "No",
      module.units?.flatMap((x) => x.aiGeneratedElements || []), ["module headline", "supporting copy", "proof / card structure"],
      `Story sequence ${module.sequence || ""}`, `${module.templateType} planned`,
      module.units?.every((x) => x.copyReview?.status === "Reviewed") ? "Reviewed" : "Needs Japanese Copy Review",
      module.units?.map((x) => x.claimSource).filter(Boolean), module.units?.map((x) => x.risk).filter(Boolean), module.moduleAvailability,
    ]),
  ];
  const spec = {
    filename: "visual_composition_plan.xlsx",
    sheetName: "Composition Plan",
    title: "Amazon Japan Visual Composition Plan — Approved Before Rendering",
    note: "Workflow gate: Page Role → Information Structure → Wireframe → Japanese Copy Review → Asset Selection → Product Composite → Scene Completion → Round 1 → Review → Round 2. Product body must use user-provided official assets.",
    columns: [
      ["visualId", 17], ["type", 16], ["role", 24], ["layout", 17], ["headline", 24], ["subCopy", 30],
      ["productAsset", 28], ["sceneAsset", 28], ["aiNeeded", 12], ["allowedAiElements", 24], ["graphicElements", 24],
      ["priority", 20], ["wireframeGate", 20], ["copyReview", 22], ["claimSource", 24], ["risk", 28], ["status", 18],
    ].map(([key, width]) => ({ key, label: key.replace(/([A-Z])/g, " $1").replace(/^./, (c) => c.toUpperCase()), width })),
    rows,
  };
  return createWorkbook(outputDir, spec, renderWorkbooks);
}

export async function writeWorkbooks(data, outputDir, renderWorkbooks = false) {
  const sellingPoints = [data.strategy.heroSellingPoint, ...(data.strategy.coreSellingPoints || []), ...(data.strategy.supportingFeatures || []), ...(data.strategy.technicalDetails || [])].filter(Boolean);
  const productImageRows = data.images.map((x) => [x.id, x.stage, x.pageRole || x.role, x.userQuestion, x.keyMessage, x.layoutId, x.headline, x.subcopy, x.informationHierarchy?.level3, x.copyReview?.selected, x.copyReview?.status, x.visualDirection, x.productPlacement, x.scene, x.assetRequirement, x.designPriority, x.avoid, x.claimIds, x.claimSource, x.risk, x.status, x.visualProductionStatus, x.designQaStatus, x.sourceOrigin, x.sourceAssetType, x.productBodyAiGenerated, x.aiGeneratedElements, x.canvas, x.productSize, x.mobileSafeArea, x.wireframePath, x.round1Path, x.editablePath, x.finalPath]);
  const aplusRows = data.aplusModules.flatMap((module) => (module.units || []).map((unit) => [module.id, module.sequence, module.templateType, module.templateName, module.moduleAvailability, module.storyRole || module.purpose, module.desktopLayout, module.mobileConsideration, module.imageRatio, module.copyLength, module.wireframePath, module.round1Path, module.editablePath, module.finalPath, module.designQaStatus, unit.id, unit.stage, unit.purpose, unit.userQuestion, unit.headline, unit.copy, unit.copyReview?.selected, unit.copyReview?.status, unit.visual, unit.asset, unit.claimIds, unit.claimSource, unit.risk, unit.status, unit.visualProductionStatus, unit.sourceOrigin, unit.sourceAssetType, unit.productBodyAiGenerated, unit.aiGeneratedElements]));
  const comparisonHeaders = ["Criteria", ...(data.comparison.products || []).map((x) => x.name), "Source", "Status"];
  const comparisonRows = (data.comparison.rows || []).map((row) => [row.criteria, ...(data.comparison.products || []).map((x) => row.values?.[x.id] || ""), row.source, row.status]);
  const specs = [
    {
      filename: "selling_point_matrix.xlsx", sheetName: "Selling Points", title: "Amazon Japan Selling Point Matrix",
      columns: ["priority", "level", "feature", "mechanism", "benefit", "userProblem", "scenario", "proof", "placement", "assetNeeded", "claimIds", "source", "status"].map((key) => ({ key, label: key.replace(/([A-Z])/g, " $1").replace(/^./, (c) => c.toUpperCase()), width: ["feature", "benefit", "userProblem", "scenario", "proof", "placement", "assetNeeded", "source"].includes(key) ? 24 : 14 })),
      rows: sellingPoints.map((x) => [x.priority, x.level, x.feature, x.mechanism, x.benefit, x.userProblem, x.scenario, x.proof, x.placement, x.assetNeeded, x.claimIds, x.source, x.status]),
    },
    {
      filename: "product_image_brief.xlsx", sheetName: "Product Images", title: "7-Image Decision Journey Brief",
      columns: ["imageId", "stage", "pageRole", "userQuestion", "keyMessage", "layoutId", "japaneseHeadline", "japaneseSubCopy", "proofItems", "selectedCopy", "copyReviewStatus", "visualDirection", "productPlacement", "scene", "assetRequirement", "designPriority", "avoid", "claimIds", "claimSource", "risk", "status", "visualProductionStatus", "designQaStatus", "sourceOrigin", "sourceAssetType", "productBodyAiGenerated", "aiGeneratedElements", "canvas", "productSize", "mobileSafeArea", "wireframe", "round1", "editableSvg", "finalJpeg"].map((key) => ({ key, label: key.replace(/([A-Z])/g, " $1").replace(/^./, (c) => c.toUpperCase()), width: ["stage", "imageId", "status", "layoutId", "designQaStatus"].includes(key) ? 17 : 22 })),
      rows: productImageRows,
    },
    {
      filename: "aplus_content_plan.xlsx", sheetName: "A+ Plan", title: "A+ Module Structure and Visual Unit Plan",
      columns: ["module", "sequence", "templateType", "templateName", "moduleAvailability", "storyRole", "desktopLayout", "mobileConsideration", "imageRatio", "copyLength", "wireframe", "round1", "editableSvg", "moduleFinalJpeg", "designQaStatus", "unitId", "stage", "unitPurpose", "userQuestion", "headline", "copy", "selectedCopy", "copyReviewStatus", "visual", "asset", "claimIds", "claimSource", "risk", "status", "visualProductionStatus", "sourceOrigin", "sourceAssetType", "productBodyAiGenerated", "aiGeneratedElements"].map((key) => ({ key, label: key.replace(/([A-Z])/g, " $1").replace(/^./, (c) => c.toUpperCase()), width: ["copy", "visual", "asset", "claimSource", "risk"].includes(key) ? 28 : 18 })),
      rows: aplusRows,
    },
    {
      filename: "comparison_chart.xlsx", sheetName: "Comparison", title: "Product Family Comparison",
      columns: comparisonHeaders.map((label, index) => ({ key: index === comparisonHeaders.length - 1 ? "status" : `c${index}`, label, width: index === 0 ? 24 : 20 })), rows: comparisonRows,
    },
    {
      filename: "amazon_seo_keywords.xlsx", sheetName: "SEO Keywords", title: "Amazon Japan SEO Keyword Plan",
      columns: ["category", "keyword", "priority", "searchIntent", "placement", "reason", "avoidReason", "source", "status"].map((key) => ({ key, label: key.replace(/([A-Z])/g, " $1").replace(/^./, (c) => c.toUpperCase()), width: ["keyword", "searchIntent", "reason", "avoidReason", "source"].includes(key) ? 26 : 16 })),
      rows: data.seo.map((x) => [x.category, x.keyword, x.priority, x.searchIntent, x.placement, x.reason, x.avoidReason, x.source, x.status]),
    },
    {
      filename: "asset_requirements.xlsx", sheetName: "Assets", title: "Design Asset Requirements",
      columns: ["assetId", "placement", "decisionStage", "description", "canvas", "sourceType", "sourceFile", "sourceUrl", "owner", "due", "retouch", "rights", "risk", "status"].map((key) => ({ key, label: key.replace(/([A-Z])/g, " $1").replace(/^./, (c) => c.toUpperCase()), width: ["description", "sourceFile", "sourceUrl", "retouch", "rights", "risk"].includes(key) ? 28 : 16 })),
      rows: data.assets.map((x) => [x.id, x.placement, x.stage, x.description, x.canvas, x.sourceType, x.file, x.url, x.owner, x.due, x.retouch, x.rights, x.risk, x.status]),
    },
    {
      filename: "asset_gap_analysis.xlsx", sheetName: "Asset Gaps", title: "Official Product Asset Gap Analysis",
      note: "Formal launch assets require user-provided official product sources. AI may only create scene, people, background, lighting, props, or composition expansion.",
      columns: ["visualId", "placement", "decisionStage", "requiredOfficialAsset", "currentSource", "sourceOrigin", "sourceAssetType", "productBodyAiGenerated", "allowedAiElements", "requiredOperation", "claimSource", "gap", "owner", "visualProductionStatus", "finalJpeg"].map((key) => ({ key, label: key.replace(/([A-Z])/g, " $1").replace(/^./, (c) => c.toUpperCase()), width: ["requiredOfficialAsset", "currentSource", "allowedAiElements", "requiredOperation", "claimSource", "gap"].includes(key) ? 28 : 18 })),
      rows: [...data.images, ...data.aplusModules.flatMap((module) => module.units || [])].map((x) => [x.id, x.id.startsWith("IMAGE") ? "Product Image" : "A+ Content Unit", x.stage, x.assetRequirement || x.asset, x.productSource || x.visualSrc || data.product.mainImage, x.sourceOrigin, x.sourceAssetType, x.productBodyAiGenerated, x.aiGeneratedElements, x.retouchRequirement || "Wireframe → official product composite → scene/background → programmatic Japanese copy → Round 1 review → Round 2 final", x.claimSource, x.visualProductionStatus === "Final Ready" ? "None" : `Requires resolution before formal launch: ${x.visualProductionStatus}`, x.owner || "Design / PMM", x.visualProductionStatus, x.finalPath || x.moduleFinalPath]),
    },
  ];
  const inspections = [];
  for (const spec of specs) inspections.push(await createWorkbook(outputDir, spec, renderWorkbooks));
  await fs.mkdir(path.join(outputDir, "qa"), { recursive: true });
  await fs.writeFile(path.join(outputDir, "qa", "workbook-inspection.json"), JSON.stringify(inspections, null, 2), "utf8");
}

function badge(status, translated = true) {
  const key = String(status || "Unknown").toLowerCase().replace(/[^a-z]+/g, "-");
  return `<span class="badge badge-${esc(key)}">${esc(translated ? statusChinese(status) : status || "Unknown")}</span>`;
}

function detailGrid(entries) {
  return `<dl class="detail-grid">${entries.map(([label, value]) => `<div><dt>${esc(label)}</dt><dd>${esc(Array.isArray(value) ? value.join("、") : value === false ? "否" : value === true ? "是" : value || "—")}</dd></div>`).join("")}</dl>`;
}

function copyOptionsHtml(review) {
  if (!(review?.options || []).length) return `<p class="muted">主图不放营销文案</p>`;
  return `<div class="copy-options">${review.options.map((option) => `<div class="copy-option ${option.id === review.selected ? "selected" : ""}"><div><strong>Option ${esc(option.id)}</strong><span>${esc(option.approach)}</span></div><p>${esc(option.text)}</p><small>自然度 ${esc(option.scores?.naturalness)} · 可读性 ${esc(option.scores?.amazonReadability)} · Claim ${esc(option.scores?.claimAccuracy)} · Mobile ${esc(option.scores?.mobileLength)} · Total ${esc(option.scores?.total)}</small></div>`).join("")}</div>`;
}

function visualPair(finalPath, wireframePath, label = "Final") {
  return `<div class="visual-pair"><figure><figcaption>Wireframe</figcaption><img src="${esc(wireframePath)}" alt="Wireframe"/></figure><figure><figcaption>${esc(label)}</figcaption><img src="${esc(finalPath)}" alt="${esc(label)}"/></figure></div>`;
}

function consumerSafe(value, fallback = "詳細は商品仕様をご確認ください。") {
  const text = String(value ?? "").replaceAll("（公開前検証が必要）", "").trim();
  const internal = /Need Verification|Claim|Source|Product Knowledge|Placeholder|Prototype|Review Draft|待确认|被阻塞|素材|风险|要確認|条件確認|確認中|未確認|最終確認|Seller Central|Amazon登録|公式ページには|公式ページでは|外部公開/;
  return internal.test(text) ? fallback : text;
}

function legacyRatingHtml(product = {}) {
  const rating = product.rating || {};
  const status = String(rating.status || "").toLowerCase();
  const value = Number(rating.value);
  const count = Number(rating.count);
  const sourceText = typeof rating.source === "object" ? JSON.stringify(rating.source) : String(rating.source || "");
  const sourceType = String(rating.source_type || rating.sourceType || "").toLowerCase();
  const valid = ["confirmed", "approved", "verified"].includes(status)
    && ["amazon_api", "amazon_verified_snapshot", "approved_marketplace_snapshot"].includes(sourceType)
    && Boolean(sourceText)
    && !/placeholder|fixture|dummy|mock|test/i.test(sourceText)
    && Number.isFinite(value) && value >= 0 && value <= 5
    && Number.isInteger(count) && count >= 0;
  return valid
    ? `<span data-rating-status="confirmed">${esc(`${value.toFixed(1)}／5（${count.toLocaleString("ja-JP")}件）`)}</span>`
    : `<span data-rating-status="unavailable">—</span>`;
}

export function buildHtml(data) {
  const title = data.titles[data.titles.recommendedKey] || data.titles.main;
  const publishGate = data.meta.effectivePublishGate || "Blocked";
  const units = data.aplusModules.flatMap((module) => module.units || []);
  const thumbs = data.images.map((item, index) => `<button class="thumb ${index === 0 ? "active" : ""}" data-src="${esc(item.finalPath)}" aria-label="商品画像 ${index + 1}"><img src="${esc(item.finalPath)}" alt="${esc(data.product.name)} 商品画像 ${index + 1}"/></button>`).join("");
  const bullets = data.bullets.map((item) => `<li><strong>【${esc(consumerSafe(item.headline))}】</strong>${esc(consumerSafe(item.body))}</li>`).join("");
  const aplus = data.aplusModules.map((module) => `<section class="consumer-module"><img src="${esc(module.finalPath)}" alt="${esc(consumerSafe(module.units?.[0]?.headline || module.purpose))}"/></section>`).join("");
  const comparisonHead = (data.comparison.products || []).map((product) => `<th>${esc(consumerSafe(product.name))}</th>`).join("");
  const comparisonBody = (data.comparison.rows || []).map((row) => `<tr><th>${esc(consumerSafe(row.criteria))}</th>${(data.comparison.products || []).map((product) => `<td>${esc(consumerSafe(row.values?.[product.id] || "—", "—"))}</td>`).join("")}</tr>`).join("");
  const faq = data.faq.map((item) => `<details><summary>${esc(consumerSafe(item.question))}</summary><p>${esc(consumerSafe(item.answer))}</p></details>`).join("");
  const reviewImages = data.images.map((item, index) => `<article class="review-row"><div class="review-preview">${visualPair(item.finalPath, item.wireframePath, "Round 2 Final")}</div><div><div class="review-title"><div><p class="eyebrow">${esc(item.id)} · ${esc(STAGES[index][1])} · Layout ${esc(item.layoutId)}</p><h3>${esc(item.headline || item.keyMessage || "Amazon 主图")}</h3></div>${badge(item.visualProductionStatus)}</div>${copyOptionsHtml(item.copyReview)}${detailGrid([["设计目标", item.pageRole || item.role], ["用户问题", item.userQuestion], ["对应卖点", item.keyMessage], ["信息层级", `L1 ${item.informationHierarchy?.level1 || "—"} / L2 ${item.informationHierarchy?.level2 || "—"} / L3 ${(item.informationHierarchy?.level3 || []).join("、") || "—"}`], ["素材需求", item.assetRequirement], ["产品源文件", item.productSource || item.visualSrc], ["场景素材", item.sceneSource || "无 / 程序化背景"], ["来源归属", item.sourceOrigin], ["官方素材类型", item.sourceAssetType], ["产品本体是否由 AI 生成", item.productBodyAiGenerated], ["AI 生成内容", item.aiGeneratedElements], ["Claim 来源", item.claimSource], ["风险", item.risk], ["Round 1 修正", item.round1Review], ["Round 2 QA", item.round2Qa?.status], ["Mobile", item.mobileSafeArea || item.wireframe?.mobileRule], ["可编辑 SVG", item.editablePath], ["最终 JPEG", item.finalPath], ["内容状态", statusChinese(item.status)], ["制作状态", statusChinese(item.visualProductionStatus)]])}</div></article>`).join("");
  const reviewAplus = data.aplusModules.map((module) => `<section class="review-module"><header><div><p class="eyebrow">${esc(module.id)} · ${esc(module.templateType)}</p><h3>${esc(module.templateName || module.moduleType)}</h3><p>${esc(module.storyRole || module.purpose)}</p></div>${badge(module.visualProductionStatus)}</header>${visualPair(module.finalPath, module.wireframePath, "Round 2 Module")}${detailGrid([["Amazon模板", module.templateType], ["故事职责", module.storyRole || module.purpose], ["桌面布局", module.desktopLayout], ["移动端要求", module.mobileConsideration], ["文案长度", module.copyLength], ["Round 1 修正", module.round1Review], ["Round 2 QA", module.round2Qa?.status], ["可编辑 SVG", module.editablePath], ["最终 JPEG", module.finalPath], ["Module 可用性", statusChinese(module.moduleAvailability)]])}<div class="review-unit-grid">${(module.units || []).map((unit) => `<article><div><div class="review-title"><strong>${esc(unit.id)} · ${esc(stageMeta(unit.stage).label)}</strong>${badge(unit.status)}</div>${copyOptionsHtml(unit.copyReview)}${detailGrid([["设计作用", unit.purpose], ["用户问题", unit.userQuestion], ["最终日文Headline", unit.headline], ["最终日文Sub Copy", unit.copy], ["素材需求", unit.asset], ["产品源文件", unit.productSource || unit.visualSrc], ["场景素材", unit.sceneSource || "无 / 模块背景"], ["来源归属", unit.sourceOrigin], ["官方素材类型", unit.sourceAssetType], ["产品本体是否由 AI 生成", unit.productBodyAiGenerated], ["AI 生成内容", unit.aiGeneratedElements], ["Claim 来源", unit.claimSource], ["风险", unit.risk], ["内容状态", statusChinese(unit.status)]])}</div></article>`).join("")}</div></section>`).join("");
  const claimReview = (data.claims || []).map((claim) => `<tr><td>${esc(claim.id)}</td><td>${esc(claim.copy)}</td><td>${badge(claim.status)}</td><td>${esc(claim.sourceId)}</td><td>${claim.sourceUrl ? `<a href="${esc(claim.sourceUrl)}">查看来源</a>` : "—"}</td><td>${esc(claim.conditions)}</td><td>${esc(claim.risk)}</td></tr>`).join("");
  const assetReview = data.assets.map((asset) => `<tr><td>${esc(asset.id)}</td><td>${esc(asset.placement)}</td><td>${esc(asset.description)}</td><td>${esc(asset.sourceType)}</td><td>${esc(asset.rights)}</td><td>${esc(asset.risk)}</td><td>${badge(asset.status)}</td></tr>`).join("");
  const sourceReview = data.sources.map((source) => `<tr><td>${esc(source.id)}</td><td>${esc(source.title)}</td><td>${esc(source.type)}</td><td>${source.url ? `<a href="${esc(source.url)}">打开</a>` : esc(source.path || "—")}</td><td>${esc(source.lastVerified)}</td><td>${badge(source.status)}</td></tr>`).join("");
  return `<!doctype html><html lang="ja"><head><meta charset="utf-8"/><meta name="viewport" content="width=device-width,initial-scale=1"/><link rel="icon" href="data:,"/><title>${esc(data.product.name)} — Amazon Japan PDP</title>
<style>
:root{--ink:#18212a;--muted:#606b75;--line:#d8dde3;--bg:#eef1f3;--teal:#087f76;--orange:#ff9900;--amazon:#131921;--shadow:0 18px 50px rgba(18,28,38,.13)}*{box-sizing:border-box}html{scroll-behavior:smooth}body{margin:0;background:var(--bg);color:var(--ink);font-family:-apple-system,BlinkMacSystemFont,"Hiragino Kaku Gothic ProN","Yu Gothic",Meiryo,sans-serif;line-height:1.55}button{font:inherit}.hidden{display:none!important}.muted{color:var(--muted)}.appbar{position:sticky;top:0;z-index:50;display:flex;align-items:center;gap:18px;padding:12px 22px;background:var(--amazon);color:#fff;box-shadow:0 3px 16px #0003}.brand{font-weight:800;white-space:nowrap}.brand small{display:block;color:#aab6c2;font-size:11px;font-weight:500}.switch{display:flex;padding:3px;background:#27313a;border-radius:10px}.switch button{border:0;background:transparent;color:#d4dbe1;padding:8px 12px;border-radius:7px;cursor:pointer}.switch button.active{background:#fff;color:#17212b}.gate{margin-left:auto}.nav{position:sticky;top:70px;z-index:40;display:flex;gap:22px;padding:10px 24px;background:#fff;border-bottom:1px solid var(--line);overflow:auto;white-space:nowrap}.nav a{color:#31404c;text-decoration:none;font-size:13px}.preview-shell{max-width:1440px;margin:22px auto;background:#fff;box-shadow:var(--shadow);transition:.25s}.pdp-fold{display:grid;grid-template-columns:minmax(0,1.07fr) minmax(390px,.93fr);gap:26px;padding:32px}.gallery{display:grid;grid-template-columns:74px 1fr;gap:18px}.thumbs{display:flex;flex-direction:column;gap:10px}.thumb{width:70px;height:70px;padding:3px;border:1px solid var(--line);border-radius:7px;background:#fff;cursor:pointer;overflow:hidden}.thumb.active{border:3px solid var(--orange)}.thumb img{width:100%;height:100%;object-fit:cover}.hero-image{aspect-ratio:1;display:grid;place-items:center;border:1px solid #edf0f2;background:#fff;overflow:hidden}.hero-image img{width:100%;height:100%;object-fit:contain}.product-copy h1{margin:0 0 12px;font-size:25px;line-height:1.38;font-weight:500}.rating{display:flex;gap:12px;padding:8px 0;border-bottom:1px solid var(--line);font-size:13px}.stars{color:#f59e0b}.price{margin:16px 0;color:#b12704;font-size:30px}.price small{display:block;color:var(--muted);font-size:12px}.bullets{padding-left:20px}.bullets li{margin:10px 0}.variation,.delivery,.buybox{margin-top:14px;padding:13px;border:1px solid var(--line);border-radius:8px}.buybox button{width:100%;padding:11px;border:0;border-radius:20px;background:#ffd814}.section{padding:52px 42px;border-top:1px solid #edf0f2}.section h2{margin:0 0 24px;font-size:27px}.consumer-aplus{background:#f4f4f4}.consumer-module{max-width:1240px;margin:0 auto 34px;background:#fff}.consumer-module img{display:block;width:100%;height:auto}.comparison-wrap{overflow:auto}.comparison,.review-table{width:100%;border-collapse:collapse}.comparison{min-width:680px}.comparison th,.comparison td{padding:14px;border:1px solid var(--line);text-align:center}.comparison th:first-child{text-align:left;background:#f5f7f8}.faq-list details{padding:16px 0;border-top:1px solid var(--line)}.faq-list summary{font-weight:700;cursor:pointer}.preview-shell.mobile{width:390px;max-width:calc(100vw - 24px)!important}.preview-shell.mobile .pdp-fold{grid-template-columns:1fr;padding:14px}.preview-shell.mobile .gallery{grid-template-columns:54px 1fr}.preview-shell.mobile .thumb{width:50px;height:50px}.preview-shell.mobile .product-copy{padding:8px 6px 20px}.preview-shell.mobile .product-copy h1{font-size:18px}.preview-shell.mobile .section{padding:32px 14px}.preview-shell.mobile .comparison{font-size:12px}.review-shell{max-width:1500px;margin:22px auto;padding:28px;background:#fff;box-shadow:var(--shadow)}.review-hero{display:flex;justify-content:space-between;gap:24px;padding:10px 0 28px;border-bottom:1px solid var(--line)}.review-hero h1{margin:0}.review-summary{display:flex;gap:12px;flex-wrap:wrap}.review-summary div{min-width:126px;padding:12px;border-radius:10px;background:#f3f6f7}.review-summary strong{display:block;font-size:21px}.review-section{padding:40px 0;border-bottom:1px solid var(--line)}.review-row{display:grid;grid-template-columns:minmax(380px,46%) 1fr;gap:28px;padding:28px 0;border-top:1px solid var(--line)}.visual-pair{display:grid;grid-template-columns:1fr 1fr;gap:12px;margin:16px 0}.visual-pair figure{margin:0}.visual-pair figcaption{padding:6px 9px;background:#eef2f3;color:#40515d;font-size:11px;font-weight:800}.visual-pair img{display:block;width:100%;border:1px solid var(--line)}.review-title,.review-module>header{display:flex;align-items:start;justify-content:space-between;gap:18px}.review-title h3{margin:0}.eyebrow{margin:0 0 6px;color:var(--teal);font-size:12px;font-weight:800;letter-spacing:.05em}.detail-grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:8px 18px}.detail-grid div{padding:9px 0;border-bottom:1px dashed #d7dde1}.detail-grid dt{color:var(--muted);font-size:11px;font-weight:700}.detail-grid dd{margin:2px 0 0}.copy-options{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:8px;margin:14px 0}.copy-option{padding:10px;border:1px solid var(--line);border-radius:9px;background:#fafbfb}.copy-option.selected{border:2px solid var(--teal);background:#edf9f6}.copy-option div{display:flex;justify-content:space-between;gap:6px}.copy-option span,.copy-option small{color:var(--muted);font-size:10px}.copy-option p{margin:8px 0;font-size:13px}.review-module{padding:32px 0;border-top:1px solid var(--line)}.review-unit-grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:18px;margin-top:20px}.review-unit-grid article{overflow:hidden;border:1px solid var(--line);border-radius:12px}.review-unit-grid article>div{padding:16px}.review-table th,.review-table td{padding:10px;border-bottom:1px solid var(--line);text-align:left;vertical-align:top}.badge{display:inline-flex;padding:3px 8px;border-radius:999px;background:#edf0f2;color:#42505d;font-size:10px;font-weight:800;white-space:nowrap}.badge-ready,.badge-final-ready,.badge-approved,.badge-confirmed,.badge-pass,.badge-reviewed{background:#dcfce7;color:#166534}.badge-copy-ready,.badge-source-ready{background:#dbeafe;color:#1d4ed8}.badge-need-design,.badge-need-verification,.badge-need-cutout,.badge-need-composition,.badge-need-lifestyle-generation,.badge-need-copy{background:#fef3c7;color:#92400e}.badge-asset-missing{background:#ffedd5;color:#9a3412}.badge-blocked,.badge-conflict,.badge-unsupported,.badge-prohibited,.badge-reject{background:#fee2e2;color:#991b1b}@media(max-width:900px){.appbar{flex-wrap:wrap}.gate{margin-left:0}.nav{top:118px}.preview-shell,.review-shell{margin:0}.review-shell{padding:16px}.pdp-fold{grid-template-columns:1fr}.review-hero{display:block}.review-row,.review-unit-grid,.detail-grid,.visual-pair,.copy-options{grid-template-columns:1fr}}
html{scroll-padding-top:110px}.review-section,[id]{scroll-margin-top:110px}@media(max-width:900px){html{scroll-padding-top:82px}.appbar{padding:7px 10px;gap:8px;flex-wrap:nowrap;overflow-x:auto}.brand,.gate{flex:0 0 auto}.nav{top:48px;padding:7px 10px;gap:14px}.review-section,[id]{scroll-margin-top:82px}}
</style></head><body>
<header class="appbar"><div class="brand">Amazon Japan PDP<small>${esc(data.product.name)}</small></div><div class="switch"><button class="active" data-mode="amazon">Amazon Preview</button><button data-mode="review">Design Review</button></div><div class="switch"><button class="active" data-device="desktop">Desktop</button><button data-device="mobile">Mobile</button></div><div id="gateStatus" class="gate hidden">发布门槛 ${badge(publishGate)}</div></header>
<nav class="nav"><a href="#product-images">商品画像</a><a href="#aplus">商品の説明</a><a href="#comparison">商品比較</a><a href="#faq">よくある質問</a></nav>
<main id="amazonView"><div id="previewShell" class="preview-shell"><section id="product-images" class="pdp-fold"><div class="gallery"><div class="thumbs">${thumbs}</div><div class="hero-image"><img id="mainImage" src="${esc(data.images[0].finalPath)}" alt="${esc(data.product.name)}"/></div></div><div class="product-copy"><h1>${esc(consumerSafe(title))}</h1><div class="rating">${legacyRatingHtml(data.product)}<span>カスタマーレビュー</span><span>${esc(data.product.sku)}</span></div><div class="price">${esc(consumerSafe(data.product.price || "価格情報をご確認ください"))}<small>税込価格・販売条件は商品ページをご確認ください</small></div><ul class="bullets">${bullets}</ul><div class="variation"><strong>バリエーション</strong><br/>${esc(consumerSafe(data.product.variationPlaceholder || "選択肢をご確認ください"))}</div><div class="delivery">お届け先を選択して、配送予定日をご確認ください。</div><div class="buybox"><button>カートに入れる</button></div></div></section><section id="aplus" class="section consumer-aplus"><h2>商品の説明</h2>${aplus}</section><section id="comparison" class="section"><h2>${esc(consumerSafe(data.comparison.title || "商品比較"))}</h2><div class="comparison-wrap"><table class="comparison"><thead><tr><th>比較項目</th>${comparisonHead}</tr></thead><tbody>${comparisonBody}</tbody></table></div></section><section id="faq" class="section"><h2>よくある質問</h2><div class="faq-list">${faq}</div></section></div></main>
<main id="reviewView" class="hidden"><div class="review-shell"><section class="review-hero"><div><p class="eyebrow">设计审阅</p><h1>${esc(data.product.name)}</h1><p>运营、设计与审核使用同一个 PDP 数据源。先看 Wireframe，再看 Round 2；消费者端文案与内部来源、风险、状态严格分离。</p></div><div class="review-summary"><div><span>商品图</span><strong>7</strong></div><div><span>A+ 模块图</span><strong>${data.aplusModules.length}</strong></div><div><span>A+ 内容单元</span><strong>${units.length}</strong></div><div><span>发布门槛</span><strong>${statusChinese(publishGate)}</strong></div></div></section><section class="review-section"><h2>商品图：Wireframe → Round 2</h2>${reviewImages}</section><section class="review-section"><h2>A+：故事模块、素材与两轮设计</h2>${reviewAplus}</section><section id="claim-review" class="review-section"><h2>Claim 审查</h2><div class="comparison-wrap"><table class="review-table"><thead><tr><th>ID</th><th>文案</th><th>状态</th><th>来源 ID</th><th>链接</th><th>适用条件</th><th>风险</th></tr></thead><tbody>${claimReview}</tbody></table></div></section><section class="review-section"><h2>素材审查</h2><div class="comparison-wrap"><table class="review-table"><thead><tr><th>ID</th><th>位置</th><th>说明</th><th>来源类型</th><th>权利</th><th>风险</th><th>状态</th></tr></thead><tbody>${assetReview}</tbody></table></div></section><section class="review-section"><h2>来源登记</h2><div class="comparison-wrap"><table class="review-table"><thead><tr><th>ID</th><th>标题</th><th>类型</th><th>URL / 路径</th><th>确认日期</th><th>状态</th></tr></thead><tbody>${sourceReview}</tbody></table></div></section></div></main>
<script>const modeButtons=document.querySelectorAll('[data-mode]');const deviceButtons=document.querySelectorAll('[data-device]');const amazon=document.getElementById('amazonView');const review=document.getElementById('reviewView');const shell=document.getElementById('previewShell');const gateStatus=document.getElementById('gateStatus');modeButtons.forEach(btn=>btn.addEventListener('click',()=>{modeButtons.forEach(x=>x.classList.remove('active'));btn.classList.add('active');const showAmazon=btn.dataset.mode==='amazon';amazon.classList.toggle('hidden',!showAmazon);review.classList.toggle('hidden',showAmazon);gateStatus.classList.toggle('hidden',showAmazon);deviceButtons.forEach(x=>x.disabled=!showAmazon)}));deviceButtons.forEach(btn=>btn.addEventListener('click',()=>{deviceButtons.forEach(x=>x.classList.remove('active'));btn.classList.add('active');shell.classList.toggle('mobile',btn.dataset.device==='mobile')}));document.querySelectorAll('.thumb').forEach(btn=>btn.addEventListener('click',()=>{document.querySelectorAll('.thumb').forEach(x=>x.classList.remove('active'));btn.classList.add('active');document.getElementById('mainImage').src=btn.dataset.src}));</script></body></html>`;
}

export async function writeHtmlAndData(data, outputDir) {
  await fs.writeFile(path.join(outputDir, "pdp-data.json"), JSON.stringify(data, null, 2), "utf8");
  const html = buildHtml(data);
  await fs.writeFile(path.join(outputDir, "amazon_pdp_preview.html"), html, "utf8");
  const reviewHtml = html.replace("</body>", `<script>window.addEventListener('DOMContentLoaded',()=>document.querySelector('[data-mode="review"]')?.click());</script></body>`);
  await fs.writeFile(path.join(outputDir, "design_review_cn.html"), reviewHtml, "utf8");
}

export async function fileExists(file) {
  try { await fs.access(file); return true; } catch { return false; }
}
