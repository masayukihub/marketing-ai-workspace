import crypto from "node:crypto";
import fs from "node:fs/promises";
import path from "node:path";
import { createRequire } from "node:module";
import { REQUIRED_REFERENCE_RENDERERS, rendererCapability } from "./renderer_registry.mjs";

const require = createRequire(import.meta.url);
const sharp = require("sharp");
const FONT = "'Hiragino Sans','Noto Sans JP','Yu Gothic',Arial,sans-serif";
const COLORS = Object.freeze({ ink: "#17212B", muted: "#53636B", accent: "#23A98F", mint: "#DDF3ED", canvas: "#F7FAFA", paper: "#FFFFFF", warm: "#F7F1EB" });

function esc(value) {
  return String(value ?? "").replaceAll("&", "&amp;").replaceAll("<", "&lt;").replaceAll(">", "&gt;").replaceAll('"', "&quot;").replaceAll("'", "&#039;");
}

function normalizeText(value, fallback) {
  const text = String(value || "").trim();
  return text || fallback;
}

function wrap(value, maxChars) {
  const characters = [...String(value || "").trim()];
  const lines = [];
  while (characters.length) lines.push(characters.splice(0, maxChars).join(""));
  return lines.length ? lines : [""];
}

function textBlock(value, { x, y, size, maxChars, maxLines, lineHeight = 1.3, weight = 500, fill = COLORS.ink, anchor = "start", slot }) {
  const lines = wrap(value, maxChars);
  const overflow = lines.length > maxLines ? ` data-line-limit="FAIL:${lines.length}/${maxLines}"` : "";
  return `<g data-slot="${esc(slot || "text")}"${overflow}>${lines.map((line, index) => `<text x="${x}" y="${y + index * size * lineHeight}" text-anchor="${anchor}" font-family="${FONT}" font-size="${size}" font-weight="${weight}" fill="${fill}">${esc(line)}</text>`).join("")}</g>`;
}

function defs() {
  return `<defs><filter id="shadow" x="-20%" y="-20%" width="140%" height="160%"><feDropShadow dx="0" dy="18" stdDeviation="22" flood-color="#0F2A25" flood-opacity=".14"/></filter><linearGradient id="mint" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#F9FCFB"/><stop offset="1" stop-color="#DDF3ED"/></linearGradient></defs>`;
}

function placeholder(x, y, width, height, label = "OFFICIAL PRODUCT ASSET") {
  return `<g data-slot="image" data-fallback="true"><rect x="${x}" y="${y}" width="${width}" height="${height}" rx="34" fill="#E8EFED" stroke="#B8CAC5" stroke-width="4" stroke-dasharray="14 10"/><text x="${x + width / 2}" y="${y + height / 2}" text-anchor="middle" font-family="${FONT}" font-size="24" font-weight="700" fill="#6B7C77">${esc(label)}</text></g>`;
}

function imageSlot(uri, x, y, width, height) {
  return uri
    ? `<g data-slot="image"><image href="${esc(uri)}" x="${x}" y="${y}" width="${width}" height="${height}" preserveAspectRatio="xMidYMid meet" filter="url(#shadow)"/></g>`
    : placeholder(x, y, width, height);
}

async function fileDataUri(outputDir, relativePath) {
  if (!relativePath) return "";
  const file = path.join(outputDir, relativePath);
  try {
    const bytes = await fs.readFile(file);
    const ext = path.extname(file).toLowerCase();
    const mime = ext === ".png" ? "image/png" : ext === ".webp" ? "image/webp" : ext === ".svg" ? "image/svg+xml" : "image/jpeg";
    return `data:${mime};base64,${bytes.toString("base64")}`;
  } catch {
    return "";
  }
}

function claimText(record) {
  const sources = record.claim_sources || record.units?.flatMap((unit) => unit.claim_sources || []) || [];
  const conditions = sources.map((source) => source.conditions).filter(Boolean);
  const condition = normalizeText(conditions[0], "適用条件は本文と商品ページでご確認ください。");
  return /[A-Za-z]{4,}/.test(condition) ? "適用条件は本文と商品ページでご確認ください。" : condition;
}

function leadContent(record) {
  const lead = record.units?.[0] || record;
  return {
    title: normalizeText(record.module_headline || lead.headline || record.headline || record.key_message, "製品情報"),
    body: normalizeText(lead.copy || record.sub_copy || record.role || lead.purpose, "詳しい条件は商品ページでご確認ください。"),
    claim: claimText(record),
  };
}

function productFeatureSplit(record, productUri, mobile = false) {
  const { title, body, claim } = leadContent(record);
  if (mobile) return `<svg xmlns="http://www.w3.org/2000/svg" width="780" height="780" viewBox="0 0 780 780">${defs()}<rect width="780" height="780" fill="url(#mint)"/>${textBlock(title,{x:46,y:88,size:43,maxChars:14,maxLines:2,weight:750,slot:"title"})}${textBlock(body,{x:46,y:190,size:29,maxChars:24,maxLines:3,lineHeight:1.38,fill:COLORS.muted,slot:"body"})}${imageSlot(productUri,165,300,450,310)}<rect x="46" y="650" width="688" height="84" rx="22" fill="#FFFFFF"/>${textBlock(claim,{x:70,y:690,size:26,maxChars:42,maxLines:2,lineHeight:1.22,fill:COLORS.muted,slot:"claim"})}</svg>`;
  return `<svg xmlns="http://www.w3.org/2000/svg" width="2000" height="2000" viewBox="0 0 2000 2000">${defs()}<rect width="2000" height="2000" fill="url(#mint)"/><rect x="85" y="110" width="875" height="1780" rx="58" fill="#FFFFFF"/>${imageSlot(productUri,150,300,740,1220)}<rect x="1040" y="110" width="875" height="1780" rx="58" fill="#FFFFFF" opacity=".82"/>${textBlock(title,{x:1110,y:420,size:108,maxChars:6,maxLines:3,weight:760,slot:"title"})}${textBlock(body,{x:1110,y:900,size:68,maxChars:10,maxLines:4,lineHeight:1.42,fill:COLORS.muted,slot:"body"})}<rect x="1100" y="1460" width="750" height="300" rx="36" fill="#EAF7F3"/><text x="1160" y="1540" font-family="${FONT}" font-size="30" font-weight="700" fill="${COLORS.accent}">CONDITION</text>${textBlock(claim,{x:1160,y:1625,size:66,maxChars:10,maxLines:3,lineHeight:1.25,fill:COLORS.ink,slot:"claim"})}</svg>`;
}

function productEcosystem(record, productUri, mobile = false) {
  const { title, body, claim } = leadContent(record);
  const relationships = (record.proof_items || []).slice(0, 3);
  const rows = relationships.length ? relationships : [body, claim];
  if (mobile) return `<svg xmlns="http://www.w3.org/2000/svg" width="780" height="920" viewBox="0 0 780 920">${defs()}<rect width="780" height="920" fill="#F1F8F9"/>${textBlock(title,{x:44,y:78,size:41,maxChars:15,maxLines:2,weight:750,slot:"title"})}${imageSlot(productUri,210,180,360,300)}<g data-slot="body">${rows.slice(0,3).map((row,index)=>`<g transform="translate(44 ${520+index*105})"><rect width="692" height="88" rx="20" fill="#FFFFFF"/><circle cx="38" cy="44" r="19" fill="${COLORS.accent}"/><text x="38" y="52" text-anchor="middle" font-family="${FONT}" font-size="20" font-weight="700" fill="#fff">${index+1}</text>${textBlock(row,{x:76,y:37,size:27,maxChars:37,maxLines:2,lineHeight:1.15,slot:index===rows.length-1?"claim":"body"})}</g>`).join("")}</g></svg>`;
  return `<svg xmlns="http://www.w3.org/2000/svg" width="2000" height="2000" viewBox="0 0 2000 2000">${defs()}<rect width="2000" height="2000" fill="#F1F8F9"/>${textBlock(title,{x:1000,y:180,size:100,maxChars:18,maxLines:2,anchor:"middle",weight:760,slot:"title"})}${textBlock(body,{x:1000,y:410,size:66,maxChars:30,maxLines:2,anchor:"middle",fill:COLORS.muted,slot:"body"})}<circle cx="1000" cy="1080" r="430" fill="#DDF3ED"/>${imageSlot(productUri,640,700,720,760)}${rows.slice(0,3).map((row,index)=>{const positions=[[120,760],[1280,780],[650,1590]][index];return `<g transform="translate(${positions[0]} ${positions[1]})"><rect width="600" height="250" rx="38" fill="#FFFFFF" filter="url(#shadow)"/>${textBlock(row,{x:48,y:90,size:54,maxChars:18,maxLines:3,lineHeight:1.25,slot:index===rows.length-1?"claim":"body"})}</g>`;}).join("")}</svg>`;
}

function aplus5050(record, productUri, mobile = false) {
  const { title, body, claim } = leadContent(record);
  const secondary = record.units?.[1];
  if (mobile) return mobileAplus(record, productUri);
  return `<svg xmlns="http://www.w3.org/2000/svg" width="1464" height="620" viewBox="0 0 1464 620">${defs()}<rect width="1464" height="620" fill="#F7FAFA"/><rect x="44" y="44" width="650" height="532" rx="30" fill="#FFFFFF"/>${textBlock(title,{x:82,y:122,size:49,maxChars:18,maxLines:2,weight:760,slot:"title"})}${textBlock(body,{x:82,y:265,size:29,maxChars:34,maxLines:4,lineHeight:1.38,fill:COLORS.muted,slot:"body"})}<rect x="82" y="455" width="574" height="82" rx="20" fill="#EAF7F3"/>${textBlock(secondary?.headline || claim,{x:108,y:496,size:25,maxChars:32,maxLines:2,lineHeight:1.16,slot:"claim"})}<rect x="738" y="44" width="682" height="532" rx="30" fill="#DDF3ED"/>${imageSlot(productUri,800,75,560,470)}</svg>`;
}

function aplusInstallation(record, productUri, mobile = false) {
  if (mobile) return mobileAplus(record, productUri);
  const title = leadContent(record).title;
  const units = (record.units || []).slice(0, 3);
  return `<svg xmlns="http://www.w3.org/2000/svg" width="1464" height="700" viewBox="0 0 1464 700">${defs()}<rect width="1464" height="700" fill="#F7FAFA"/>${textBlock(title,{x:56,y:82,size:46,maxChars:26,maxLines:2,weight:760,slot:"title"})}<g data-slot="body">${units.map((unit,index)=>`<g transform="translate(${54+index*470} 165)"><rect width="430" height="470" rx="28" fill="#FFFFFF" filter="url(#shadow)"/><circle cx="55" cy="55" r="29" fill="${COLORS.accent}"/><text x="55" y="65" text-anchor="middle" font-family="${FONT}" font-size="25" font-weight="700" fill="#fff">${index+1}</text>${imageSlot(productUri,110,38,270,185)}${textBlock(unit.headline,{x:32,y:270,size:29,maxChars:17,maxLines:2,weight:700,slot:"title"})}${textBlock(unit.copy,{x:32,y:355,size:22,maxChars:27,maxLines:4,lineHeight:1.28,fill:COLORS.muted,slot:index===units.length-1?"claim":"body"})}</g>`).join("")}</g></svg>`;
}

function aplusBrand(record, productUri, mobile = false) {
  if (mobile) return mobileAplus(record, productUri);
  const { title, body, claim } = leadContent(record);
  return `<svg xmlns="http://www.w3.org/2000/svg" width="1464" height="600" viewBox="0 0 1464 600">${defs()}<rect width="1464" height="600" fill="url(#mint)"/><rect x="48" y="48" width="670" height="504" rx="32" fill="#FFFFFF"/><text x="84" y="104" font-family="${FONT}" font-size="16" font-weight="700" letter-spacing="3" fill="${COLORS.accent}">SWITCHBOT</text>${textBlock(title,{x:84,y:180,size:50,maxChars:18,maxLines:3,weight:760,slot:"title"})}${textBlock(body,{x:84,y:360,size:29,maxChars:35,maxLines:4,lineHeight:1.36,fill:COLORS.muted,slot:"body"})}${textBlock(claim,{x:84,y:518,size:22,maxChars:46,maxLines:2,lineHeight:1.18,fill:COLORS.muted,slot:"claim"})}${imageSlot(productUri,800,70,560,460)}</svg>`;
}

export function mobileAplus(record, productUri = "") {
  const { title, body, claim } = leadContent(record);
  const units = (record.units || []).slice(0, 3);
  const rows = units.length ? units : [{ headline: title, copy: body, claim_sources: record.claim_sources || [] }];
  const cardHeight = 265;
  const height = 780 + rows.length * cardHeight;
  return `<svg xmlns="http://www.w3.org/2000/svg" width="780" height="${height}" viewBox="0 0 780 ${height}">${defs()}<rect width="780" height="${height}" fill="${record.template_id === "A-LIFESTYLE" ? COLORS.warm : COLORS.canvas}"/>${textBlock(title,{x:44,y:76,size:40,maxChars:16,maxLines:3,lineHeight:1.22,weight:760,slot:"title"})}${textBlock(body,{x:44,y:220,size:28,maxChars:25,maxLines:4,lineHeight:1.36,fill:COLORS.muted,slot:"body"})}${imageSlot(productUri,210,370,360,260)}<g transform="translate(0 660)">${rows.map((unit,index)=>`<g transform="translate(44 ${index*cardHeight})"><rect width="692" height="225" rx="26" fill="#FFFFFF"/><circle cx="43" cy="45" r="22" fill="${COLORS.accent}"/><text x="43" y="54" text-anchor="middle" font-family="${FONT}" font-size="21" font-weight="700" fill="#FFFFFF">${index+1}</text>${textBlock(normalizeText(unit.headline, unit.purpose || "確認ポイント"),{x:84,y:50,size:30,maxChars:20,maxLines:2,lineHeight:1.2,weight:700,slot:"title"})}${textBlock(normalizeText(unit.copy, "詳しい条件は商品ページでご確認ください。"),{x:34,y:130,size:27,maxChars:25,maxLines:4,lineHeight:1.28,fill:COLORS.muted,slot:"body"})}</g>`).join("")}</g><g data-slot="claim"><rect x="44" y="${height-95}" width="692" height="60" rx="18" fill="#EAF7F3"/>${textBlock(claim,{x:68,y:height-58,size:28,maxChars:43,maxLines:2,lineHeight:1.15,fill:COLORS.muted,slot:"claim"})}</g></svg>`;
}

export async function renderReferencePrimitive({ templateId, record, outputDir, viewport = "desktop" }) {
  const capability = rendererCapability(templateId);
  if (!capability.renderer_available) throw new Error(`Renderer unavailable: ${templateId}`);
  const lead = record.units?.[0] || record;
  const productUri = await fileDataUri(outputDir, lead.layers?.product_layer?.source || record.layers?.product_layer?.source || "");
  const mobile = viewport === "mobile";
  let svg;
  if (templateId === "P-FEATURE-SPLIT") svg = productFeatureSplit(record, productUri, mobile);
  else if (templateId === "P-ECOSYSTEM") svg = productEcosystem(record, productUri, mobile);
  else if (templateId === "A-50-50-FEATURE") svg = aplus5050(record, productUri, mobile);
  else if (templateId === "A-INSTALLATION") svg = aplusInstallation(record, productUri, mobile);
  else if (templateId === "A-BRAND") svg = aplusBrand(record, productUri, mobile);
  else if (mobile && templateId.startsWith("A-")) svg = mobileAplus(record, productUri);
  else throw new Error(`Reference renderer is not responsible for ${templateId} ${viewport}`);
  return { svg: `<!-- renderer ${templateId} ${viewport} -->\n${svg}`, fallback_used: !productUri };
}

export async function writeReferenceRenderedAsset({ templateId, record, outputDir, svgPath, jpegPath, viewport = "desktop", metadata = "" }) {
  const { svg, fallback_used } = await renderReferencePrimitive({ templateId, record, outputDir, viewport });
  const absoluteSvg = path.join(outputDir, svgPath);
  const absoluteJpeg = path.join(outputDir, jpegPath);
  await fs.mkdir(path.dirname(absoluteSvg), { recursive: true });
  await fs.mkdir(path.dirname(absoluteJpeg), { recursive: true });
  await fs.writeFile(absoluteSvg, svg, "utf8");
  let pipeline = sharp(Buffer.from(svg)).jpeg({ quality: 93, chromaSubsampling: "4:4:4" });
  if (metadata) pipeline = pipeline.withMetadata({ exif: { IFD0: { ImageDescription: metadata } } });
  await pipeline.toFile(absoluteJpeg);
  return { template_id: templateId, viewport, svg: svgPath, jpeg: jpegPath, sha256: crypto.createHash("sha256").update(svg).digest("hex"), fallback_used };
}

export async function buildReferenceRendererSnapshots(outputDir) {
  const baseProduct = { headline: "仕組みを、ひと目で。", sub_copy: "製品の役割と条件を、読みやすい順序で説明します。", key_message: "一つの購入判断に集中", proof_items: ["確認済みの関係", "条件を明記"], claim_sources: [{ conditions: "適用条件は本文の近くに表示" }], layers: { product_layer: { source: "" } } };
  const baseAplus = { module_headline: "仕組みから、使い方まで。", units: [
    { headline: "確認ポイント1", copy: "最初の判断材料を短く説明します。", claim_sources: [{ conditions: "条件1" }], layers: { product_layer: { source: "" } } },
    { headline: "確認ポイント2", copy: "次の判断材料を短く説明します。", claim_sources: [{ conditions: "条件2" }], layers: { product_layer: { source: "" } } },
    { headline: "確認ポイント3", copy: "購入前の条件を明確にします。", claim_sources: [{ conditions: "条件3" }], layers: { product_layer: { source: "" } } },
  ] };
  const records = { "P-FEATURE-SPLIT": baseProduct, "P-ECOSYSTEM": baseProduct, "A-50-50-FEATURE": { ...baseAplus, template_id: "A-50-50-FEATURE" }, "A-INSTALLATION": { ...baseAplus, template_id: "A-INSTALLATION" }, "A-BRAND": { ...baseAplus, template_id: "A-BRAND" } };
  const snapshots = [];
  for (const templateId of REQUIRED_REFERENCE_RENDERERS) {
    for (const viewport of ["desktop", "mobile"]) {
      const { svg, fallback_used } = await renderReferencePrimitive({ templateId, record: records[templateId], outputDir, viewport });
      snapshots.push({ template_id: templateId, viewport, sha256: crypto.createHash("sha256").update(svg).digest("hex"), fallback_used, slots: ["title", "body", "image", "claim"].filter((slot) => svg.includes(`data-slot="${slot}"`)) });
    }
  }
  return snapshots;
}
