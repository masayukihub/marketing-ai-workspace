import crypto from "node:crypto";
import fs from "node:fs/promises";
import path from "node:path";
import { REQUIRED_REFERENCE_RENDERERS, assertRendererCoverage } from "./renderer_registry.mjs";
import { renderReferencePrimitive } from "./reference_renderers.mjs";
import { runMobileReadabilityGate } from "./mobile_readability_gate.mjs";
import { visualProfile, visualQualityEnabled, visualQualityManifest } from "./visual_quality_system.mjs";
import { renderVisualQualityAplus, renderVisualQualityMobileAplus, renderVisualQualityProduct } from "./visual_quality_renderers.mjs";

function esc(value) {
  return String(value ?? "").replaceAll("&", "&amp;").replaceAll("<", "&lt;").replaceAll(">", "&gt;").replaceAll('"', "&quot;").replaceAll("'", "&#039;");
}

function chars(value) {
  return [...String(value || "").trim()];
}

function consumerText(value) {
  return String(value || "")
    .replace(/正確な同梱内容はSKUとAmazon登録内容を最終確認/g, "同梱物は商品ページでご確認ください")
    .replace(/本体、設置部材、センサー搭載ケーブル、電源関連部材をSKU別に確認/g, "同梱物は商品ページでご確認ください")
    .replace(/最新サポート情報への確認導線を用意/g, "最新の対応条件は商品ページをご確認ください")
    .replace(/（条件要確認）|（すべて要照合）|（表示条件確認）|（条件確認）/g, "")
    .replace(/Need Verification|Blocked|Review Draft|公開前検証が必要|最終確認|確認導線を用意/g, "")
    .trim();
}

function lines(value, max = 18, limit = 3) {
  const clean = consumerText(value);
  const semantic = clean.match(/[^、。！？]+[、。！？]?/g) || [clean];
  const result = [];
  let current = "";
  for (const segment of semantic) {
    if (chars(current + segment).length <= max) {
      current += segment;
      continue;
    }
    if (current) result.push(current);
    const remaining = chars(segment);
    while (remaining.length > max && result.length < limit) result.push(remaining.splice(0, max).join(""));
    current = remaining.join("");
    if (result.length >= limit) break;
  }
  if (current && result.length < limit) result.push(current);
  const consumed = result.join("");
  if (chars(consumed).length < chars(clean).length && result.length) result[result.length - 1] = `${chars(result.at(-1)).slice(0, Math.max(1, max - 1)).join("")}…`;
  if (result.length > 1 && chars(result.at(-1)).length < 4) {
    const previous = chars(result.at(-2));
    const tail = chars(result.at(-1));
    while (tail.length < 4 && previous.length > 6) tail.unshift(previous.pop());
    result[result.length - 2] = previous.join("");
    result[result.length - 1] = tail.join("");
  }
  return result;
}

function svgText(value, x, y, options = {}) {
  const { max = 18, limit = 3, size = 58, weight = 700, fill = "#17212B", gap = 1.28, anchor = "start" } = options;
  return lines(value, max, limit).map((line, index) => `<text x="${x}" y="${y + index * size * gap}" text-anchor="${anchor}" font-family="'Hiragino Sans','Noto Sans JP','Yu Gothic',Arial,sans-serif" font-size="${size}" font-weight="${weight}" fill="${fill}">${esc(line)}</text>`).join("\n");
}

async function exists(file) {
  try {
    await fs.access(file);
    return true;
  } catch {
    return false;
  }
}

function mime(bytes, filename) {
  if (bytes[0] === 0xff && bytes[1] === 0xd8) return "image/jpeg";
  if (bytes[0] === 0x89 && bytes[1] === 0x50 && bytes[2] === 0x4e && bytes[3] === 0x47) return "image/png";
  if (bytes.subarray(0, 4).toString("ascii") === "RIFF" && bytes.subarray(8, 12).toString("ascii") === "WEBP") return "image/webp";
  if (/\.svg$/i.test(filename)) return "image/svg+xml";
  return "application/octet-stream";
}

async function dataUri(outputDir, relativePath) {
  if (!relativePath) return "";
  if (/^https?:\/\//i.test(relativePath)) return relativePath;
  const file = path.join(outputDir, relativePath);
  if (!(await exists(file))) return "";
  const bytes = await fs.readFile(file);
  return `data:${mime(bytes, relativePath)};base64,${bytes.toString("base64")}`;
}

async function sha256File(file) {
  return crypto.createHash("sha256").update(await fs.readFile(file)).digest("hex");
}

function defs() {
  return `<defs>
    <filter id="shadow" x="-20%" y="-20%" width="140%" height="160%"><feDropShadow dx="0" dy="24" stdDeviation="28" flood-color="#0F2A25" flood-opacity=".16"/></filter>
    <linearGradient id="mint" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#F8FCFB"/><stop offset="1" stop-color="#DDF3ED"/></linearGradient>
    <linearGradient id="sceneFade" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="#102321" stop-opacity=".82"/><stop offset=".62" stop-color="#102321" stop-opacity=".18"/><stop offset="1" stop-color="#102321" stop-opacity="0"/></linearGradient>
  </defs>`;
}

function productTemplateSvg(item, productUri, sceneUri, spec) {
  const id = item.template_id;
  const headline = item.headline || item.key_message || "";
  const sub = item.sub_copy || "";
  const proofs = (item.proof_items || []).slice(0, 3);
  if (id === "P-HERO-SPLIT") {
    return `<svg xmlns="http://www.w3.org/2000/svg" width="2000" height="2000" viewBox="0 0 2000 2000">${defs()}<rect width="2000" height="2000" fill="url(#mint)"/><rect x="1040" y="110" width="850" height="1780" rx="64" fill="#FFFFFF" opacity=".78"/><circle cx="1470" cy="690" r="510" fill="#BFE9DE" opacity=".62"/><text x="120" y="176" font-family="Arial" font-size="24" font-weight="700" fill="#23A98F" letter-spacing="4">SWITCHBOT</text>${svgText(headline, 120, 500, {max:9,limit:4,size:86})}${svgText(sub, 126, 930, {max:20,limit:4,size:36,weight:500,fill:"#42535B",gap:1.48})}<image href="${esc(productUri)}" x="1030" y="330" width="850" height="1250" preserveAspectRatio="xMidYMid meet" filter="url(#shadow)"/><rect x="1180" y="1590" width="600" height="150" rx="34" fill="#FFFFFF" opacity=".92"/>${svgText(item.key_message, 1480, 1676, {max:18,limit:2,size:27,weight:650,anchor:"middle"})}</svg>`;
  }
  if (id === "P-FEATURE-CENTER") {
    const cards = proofs.length ? proofs.slice(0, 2) : [item.key_message, item.role].filter(Boolean).slice(0, 2);
    return `<svg xmlns="http://www.w3.org/2000/svg" width="2000" height="2000" viewBox="0 0 2000 2000">${defs()}<rect width="2000" height="2000" fill="#F4F8FA"/>${svgText(headline, 1000, 210, {max:20,limit:2,size:86,anchor:"middle"})}${svgText(sub, 1000, 430, {max:34,limit:2,size:35,weight:500,fill:"#56666E",anchor:"middle"})}<circle cx="1000" cy="1050" r="560" fill="#D8EEE9"/><image href="${esc(productUri)}" x="510" y="540" width="980" height="980" preserveAspectRatio="xMidYMid meet" filter="url(#shadow)"/>${cards.map((card,index)=>`<g transform="translate(${index ? 1210 : 90} 1250)"><rect width="700" height="270" rx="40" fill="#FFFFFF" filter="url(#shadow)"/><circle cx="70" cy="72" r="28" fill="#23A98F"/><text x="70" y="82" text-anchor="middle" font-family="Arial" font-size="24" font-weight="700" fill="#fff">${index+1}</text>${svgText(card, 44, 150, {max:20,limit:3,size:31,weight:650})}</g>`).join("")}</svg>`;
  }
  if (id === "P-LIFESTYLE-FULL") {
    const background = sceneUri || productUri;
    return `<svg xmlns="http://www.w3.org/2000/svg" width="2000" height="2000" viewBox="0 0 2000 2000">${defs()}<rect width="2000" height="2000" fill="#EEE7DE"/><image href="${esc(background)}" width="2000" height="2000" preserveAspectRatio="xMidYMid slice"/><rect width="2000" height="2000" fill="url(#sceneFade)"/><rect x="90" y="1080" width="860" height="700" rx="54" fill="#102321" opacity=".58"/>${svgText(headline, 150, 1260, {max:16,limit:3,size:84,fill:"#FFFFFF"})}${svgText(sub, 156, 1570, {max:26,limit:4,size:36,weight:500,fill:"#FFFFFF",gap:1.45})}</svg>`;
  }
  if (id === "P-TECHNICAL-PROOF") {
    const claimsApproved = (item.claim_sources || []).every(claim => claim.status === "Approved");
    const cards = claimsApproved && proofs.length ? proofs : ["対応条件は商品ページでご確認ください"];
    return `<svg xmlns="http://www.w3.org/2000/svg" width="2000" height="2000" viewBox="0 0 2000 2000">${defs()}<rect width="2000" height="2000" fill="#F1F8F9"/>${svgText(headline, 110, 210, {max:18,limit:2,size:78})}${svgText(sub, 114, 410, {max:32,limit:2,size:34,weight:500,fill:"#56666E"})}<rect x="90" y="540" width="1080" height="1330" rx="60" fill="#FFFFFF"/><image href="${esc(productUri)}" x="160" y="650" width="930" height="1040" preserveAspectRatio="xMidYMid meet" filter="url(#shadow)"/>${cards.slice(0,3).map((card,index)=>`<g transform="translate(1230 ${520+index*390})"><rect width="660" height="330" rx="40" fill="#FFFFFF" filter="url(#shadow)"/><rect width="18" height="330" rx="9" fill="#23A98F"/><text x="60" y="72" font-family="Arial" font-size="21" font-weight="700" fill="#23A98F">PROOF ${String(index+1).padStart(2,"0")}</text>${svgText(card, 60, 145, {max:22,limit:4,size:30,weight:650})}</g>`).join("")}</svg>`;
  }
  if (id === "P-COMPARISON") {
    const rows = (item.proof_items || []).slice(0, 4).map((proof,index)=>({criteria:["本体サイズ","重量","ネットワーク","対応環境"][index]||`確認項目 ${index+1}`,value:String(proof).replace(/（すべて要照合）|要確認|Need Verification|Blocked/g,"").trim()})).filter(row=>row.value);
    return `<svg xmlns="http://www.w3.org/2000/svg" width="2000" height="2000" viewBox="0 0 2000 2000">${defs()}<rect width="2000" height="2000" fill="#FFF9EE"/>${svgText(headline, 110, 200, {max:19,limit:2,size:76})}${svgText(sub, 114, 390, {max:30,limit:2,size:33,weight:500,fill:"#665A45"})}<image href="${esc(productUri)}" x="1440" y="90" width="430" height="420" preserveAspectRatio="xMidYMid meet"/><g transform="translate(100 610)"><rect width="1800" height="1180" rx="50" fill="#FFFFFF"/>${rows.map((row,index)=>`<g transform="translate(50 ${80+index*300})"><rect width="1700" height="250" rx="28" fill="${index%2?"#F8FAFA":"#EDF7F4"}"/><circle cx="75" cy="125" r="34" fill="#23A98F"/><path d="M57 126l14 14 28-35" fill="none" stroke="#fff" stroke-width="9" stroke-linecap="round" stroke-linejoin="round"/>${svgText(row.criteria,140,105,{max:18,limit:1,size:30,weight:700})}${svgText(row.value,620,145,{max:28,limit:2,size:31,weight:600})}</g>`).join("")}</g></svg>`;
  }
  if (id === "P-PURCHASE-CONFIDENCE") {
    const checks = proofs.length ? proofs : [item.key_message, item.asset_resolution?.missing_assets?.join(" / "), item.risk].filter(Boolean).slice(0,3);
    return `<svg xmlns="http://www.w3.org/2000/svg" width="2000" height="2000" viewBox="0 0 2000 2000">${defs()}<rect width="2000" height="2000" fill="#FAF5F2"/>${svgText(headline, 100, 210, {max:18,limit:2,size:76})}${svgText(sub, 104, 410, {max:31,limit:2,size:33,weight:500,fill:"#675A55"})}<image href="${esc(productUri)}" x="90" y="570" width="760" height="1130" preserveAspectRatio="xMidYMid meet" filter="url(#shadow)"/>${checks.slice(0,3).map((check,index)=>`<g transform="translate(900 ${560+index*390})"><rect width="990" height="330" rx="42" fill="#FFFFFF"/><circle cx="78" cy="78" r="34" fill="#23A98F"/><path d="M60 79l13 13 25-31" fill="none" stroke="#fff" stroke-width="9" stroke-linecap="round" stroke-linejoin="round"/>${svgText(check, 140, 112, {max:26,limit:4,size:31,weight:650})}</g>`).join("")}</svg>`;
  }
  return `<svg xmlns="http://www.w3.org/2000/svg" width="2000" height="2000"><rect width="2000" height="2000" fill="#fff"/><image href="${esc(productUri)}" x="170" y="170" width="1660" height="1660" preserveAspectRatio="xMidYMid meet"/></svg>`;
}

function wireframeSvg(record, isAplus = false) {
  const template = record.template_snapshot || {};
  const width = isAplus ? 1464 : 2000;
  const height = isAplus ? Number(String(template.svg?.view_box || "0 0 1464 620").split(" ").at(-1)) || 620 : 2000;
  return `<svg xmlns="http://www.w3.org/2000/svg" width="${width}" height="${height}" viewBox="0 0 ${width} ${height}"><rect width="${width}" height="${height}" fill="#F4F6F7"/><rect x="${width*.05}" y="${height*.1}" width="${width*.42}" height="${height*.34}" rx="24" fill="#DDE2E4"/><text x="${width*.08}" y="${height*.22}" font-family="Arial" font-size="${isAplus?28:44}" font-weight="700" fill="#53636B">TEXT AREA</text><rect x="${width*.52}" y="${height*.12}" width="${width*.42}" height="${height*.72}" rx="28" fill="#C7DEDA"/><text x="${width*.73}" y="${height*.5}" text-anchor="middle" font-family="Arial" font-size="${isAplus?28:44}" font-weight="700" fill="#3D625B">PRODUCT / SCENE AREA</text><rect x="${width*.04}" y="${height*.05}" width="${width*.92}" height="${height*.9}" rx="20" fill="none" stroke="#23A98F" stroke-width="4" stroke-dasharray="16 12"/><text x="${width*.05}" y="${height*.95}" font-family="Arial" font-size="${isAplus?18:28}" fill="#4B5E65">${esc(record.template_id)} · safe area · ${esc(template.mobile_rules?.[0] || "390px rule")}</text></svg>`;
}

function moduleSvg(module, prepared, spec) {
  const id = module.template_id;
  const lead = prepared[0] || {};
  const headline = module.module_headline || lead.unit?.headline || module.story_role;
  const copy = lead.unit?.copy || "";
  const product = lead.productUri || "";
  const scene = prepared.find((entry) => entry.sceneUri)?.sceneUri || "";
  const unitRows = prepared.slice(0, 3);
  if (id === "A-HERO") return `<svg xmlns="http://www.w3.org/2000/svg" width="1464" height="600" viewBox="0 0 1464 600">${defs()}<rect width="1464" height="600" fill="url(#mint)"/>${scene?`<image href="${esc(scene)}" width="1464" height="600" preserveAspectRatio="xMidYMid slice"/><rect width="1464" height="600" fill="url(#sceneFade)"/>`:""}<rect x="0" y="0" width="650" height="600" fill="#FFFFFF" opacity=".92"/><text x="58" y="74" font-family="Arial" font-size="16" font-weight="700" fill="#23A98F" letter-spacing="3">SWITCHBOT</text>${svgText(headline,58,165,{max:11,limit:4,size:43})}${svgText(copy,62,400,{max:23,limit:4,size:20,weight:500,fill:"#53636B",gap:1.45})}<image href="${esc(product)}" x="820" y="45" width="540" height="510" preserveAspectRatio="xMidYMid meet" filter="url(#shadow)"/></svg>`;
  if (id === "A-THREE-FEATURE-GRID") return `<svg xmlns="http://www.w3.org/2000/svg" width="1464" height="760" viewBox="0 0 1464 760">${defs()}<rect width="1464" height="760" fill="#F7FAFA"/>${svgText(headline,732,76,{max:24,limit:1,size:38,anchor:"middle"})}${unitRows.map((entry,index)=>`<g transform="translate(${62+index*468} 145)"><rect width="430" height="550" rx="30" fill="#FFFFFF" filter="url(#shadow)"/><rect width="430" height="260" rx="30" fill="#DDF3ED"/><image href="${esc(entry.sceneUri||entry.productUri)}" x="30" y="18" width="370" height="225" preserveAspectRatio="xMidYMid meet"/>${svgText(entry.unit.headline,32,332,{max:14,limit:2,size:26})}${svgText(entry.unit.copy,32,430,{max:23,limit:4,size:17,weight:500,fill:"#53636B",gap:1.42})}</g>`).join("")}</svg>`;
  if (id === "A-LIFESTYLE") return `<svg xmlns="http://www.w3.org/2000/svg" width="1464" height="680" viewBox="0 0 1464 680">${defs()}<rect width="1464" height="680" fill="#EEE7DE"/><image href="${esc(scene||product)}" width="1464" height="680" preserveAspectRatio="xMidYMid slice"/><rect width="1464" height="680" fill="url(#sceneFade)"/><rect x="48" y="115" width="580" height="460" rx="30" fill="#102321" opacity=".58"/>${svgText(headline,84,225,{max:17,limit:3,size:45,fill:"#FFFFFF"})}${svgText(copy,88,440,{max:31,limit:4,size:22,weight:500,fill:"#FFFFFF",gap:1.45})}</svg>`;
  if (id === "A-TECHNICAL" || id === "A-ECOSYSTEM") {
    return `<svg xmlns="http://www.w3.org/2000/svg" width="1464" height="620" viewBox="0 0 1464 620">${defs()}<rect width="1464" height="620" fill="#F1F8F9"/>${svgText(headline,54,92,{max:22,limit:2,size:41})}<image href="${esc(product)}" x="80" y="170" width="610" height="390" preserveAspectRatio="xMidYMid meet" filter="url(#shadow)"/>${unitRows.map((entry,index)=>`<g transform="translate(760 ${100+index*160})"><rect width="640" height="135" rx="24" fill="#FFFFFF"/><circle cx="55" cy="66" r="25" fill="#23A98F"/><text x="55" y="75" text-anchor="middle" font-family="Arial" font-size="22" font-weight="700" fill="#FFFFFF">${index+1}</text>${svgText(entry.unit.headline,100,48,{max:24,limit:1,size:22})}${svgText(entry.unit.copy,100,82,{max:30,limit:2,size:15,weight:500,fill:"#53636B",gap:1.25})}</g>`).join("")}</svg>`;
  }
  if (id === "A-COMPARISON") {
    return `<svg xmlns="http://www.w3.org/2000/svg" width="1464" height="760" viewBox="0 0 1464 760">${defs()}<rect width="1464" height="760" fill="#FFF9EE"/>${svgText(headline,54,86,{max:24,limit:2,size:40})}<image href="${esc(product)}" x="1090" y="30" width="300" height="220" preserveAspectRatio="xMidYMid meet"/><g transform="translate(54 220)">${unitRows.map((entry,index)=>`<g transform="translate(0 ${index*160})"><rect width="1356" height="140" rx="22" fill="${index%2?"#FFFFFF":"#F2F8F6"}"/><circle cx="56" cy="70" r="26" fill="#23A98F"/><path d="M43 71l11 11 22-28" fill="none" stroke="#fff" stroke-width="7" stroke-linecap="round" stroke-linejoin="round"/>${svgText(entry.unit.headline,105,56,{max:24,limit:1,size:22})}${svgText(entry.unit.copy,105,98,{max:45,limit:1,size:16,weight:500,fill:"#53636B"})}</g>`).join("")}</g></svg>`;
  }
  if (id === "A-FAQ") return `<svg xmlns="http://www.w3.org/2000/svg" width="1464" height="700" viewBox="0 0 1464 700">${defs()}<rect width="1464" height="700" fill="#FAF5F2"/>${svgText(headline,54,88,{max:24,limit:2,size:40})}<image href="${esc(product)}" x="1100" y="30" width="270" height="200" preserveAspectRatio="xMidYMid meet"/>${unitRows.map((entry,index)=>`<g transform="translate(54 ${210+index*150})"><rect width="1356" height="125" rx="24" fill="#FFFFFF"/><circle cx="55" cy="62" r="25" fill="#23A98F"/><text x="55" y="71" text-anchor="middle" font-family="Arial" font-size="21" font-weight="700" fill="#fff">${index+1}</text>${svgText(entry.unit.headline,100,42,{max:28,limit:1,size:22})}${svgText(entry.unit.copy,100,79,{max:42,limit:2,size:15,weight:500,fill:"#53636B",gap:1.25})}</g>`).join("")}</svg>`;
  return `<svg xmlns="http://www.w3.org/2000/svg" width="1464" height="620" viewBox="0 0 1464 620">${defs()}<rect width="1464" height="620" fill="#F7FAFA"/><rect width="650" height="620" fill="#FFFFFF"/>${svgText(headline,54,155,{max:14,limit:3,size:43})}${svgText(copy,58,390,{max:25,limit:5,size:21,weight:500,fill:"#53636B",gap:1.42})}<rect x="720" y="45" width="680" height="530" rx="32" fill="#DDF3ED"/><image href="${esc(scene||product)}" x="760" y="70" width="600" height="480" preserveAspectRatio="xMidYMid meet" filter="url(#shadow)"/></svg>`;
}

async function writeSvg(file, svg) {
  await fs.mkdir(path.dirname(file), { recursive: true });
  await fs.writeFile(file, svg, "utf8");
}

async function renderSvgToJpeg(sharp, svg, target, specHash) {
  await fs.mkdir(path.dirname(target), { recursive: true });
  await sharp(Buffer.from(svg)).jpeg({ quality: 93, chromaSubsampling: "4:4:4" }).withMetadata({ exif: { IFD0: { ImageDescription: `Rendered from PRODUCT_PAGE_SPEC ${specHash}` } } }).toFile(target);
}

async function renderMainToJpeg(sharp, source, target, specHash) {
  const product = await sharp(source).rotate().resize(1660, 1660, { fit: "contain", background: { r:255,g:255,b:255,alpha:0 } }).png().toBuffer();
  await fs.mkdir(path.dirname(target), { recursive: true });
  await sharp({ create: { width: 2000, height: 2000, channels: 3, background: "#FFFFFF" } }).composite([{ input: product, gravity: "center" }]).jpeg({quality:94,chromaSubsampling:"4:4:4"}).withMetadata({ exif: { IFD0: { ImageDescription: `Rendered from PRODUCT_PAGE_SPEC ${specHash}` } } }).toFile(target);
}

function htmlShell(title, body, styles = "", script = "") {
  return `<!doctype html><html lang="ja"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><link rel="icon" href="data:,"><title>${esc(title)}</title><style>${baseCss()}${reviewSafetyCss()}${styles}</style></head><body>${body}${script?`<script>${script}</script>`:""}</body></html>`;
}

function reviewSafetyCss() {
  return `html{scroll-behavior:smooth;scroll-padding-top:68px}.card,[id]{scroll-margin-top:68px}.card{min-width:0;overflow-wrap:anywhere}.grid>*{min-width:0}.final-img{max-width:100%;height:auto}.trace-grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:8px 14px;margin:14px 0}.trace-grid div{padding:8px 0;border-bottom:1px dashed var(--line);min-width:0}.trace-grid dt{color:var(--muted);font-size:11px;font-weight:700}.trace-grid dd{margin:3px 0 0;overflow-wrap:anywhere}.unit-traces{margin-top:22px;border-top:1px solid var(--line);padding-top:20px}.unit-traces .trace-grid{padding:14px;background:#f8faf9;border-radius:12px}@media(max-width:700px){html{scroll-padding-top:50px}.top{width:100%;max-width:100vw;box-sizing:border-box;padding:7px 10px;gap:10px;flex-wrap:nowrap;overflow-x:auto;white-space:nowrap}.top a,.top button{flex:0 0 auto}.top .hash{display:none}.wrap{padding:12px}.card{padding:16px}.card,[id]{scroll-margin-top:50px}.grid{grid-template-columns:minmax(0,1fr)!important}.trace-grid{grid-template-columns:minmax(0,1fr)}}`;
}

function baseCss() {
  return `:root{--ink:#17212b;--muted:#607078;--accent:#23a98f;--mint:#ddf3ed;--line:#dfe6e5;--paper:#fff;--canvas:#f5f7f7}*{box-sizing:border-box}body{margin:0;font-family:"Hiragino Sans","Noto Sans JP","Yu Gothic",Arial,sans-serif;color:var(--ink);background:var(--canvas)}a{color:#087a66}.top{position:sticky;top:0;z-index:10;background:#101820;color:#fff;padding:12px 22px;display:flex;align-items:center;gap:18px;flex-wrap:wrap}.top a{color:#c9fff3;text-decoration:none}.top .hash{margin-left:auto;font:12px ui-monospace,monospace;color:#a8bab7}.wrap{max-width:1440px;margin:auto;padding:28px}.card{background:#fff;border:1px solid var(--line);border-radius:18px;padding:22px;margin-bottom:18px;box-shadow:0 6px 20px rgba(22,42,38,.05)}h1{font-size:32px;margin:0 0 10px}h2{font-size:24px;margin:0 0 14px}h3{font-size:18px;margin:0 0 10px}.muted{color:var(--muted)}.status{display:inline-flex;padding:5px 10px;border-radius:999px;background:#fff2c9;color:#735b0a;font-weight:700;font-size:12px}.status.pass{background:#dcf7ed;color:#0d6b57}.status.block{background:#fee4e2;color:#9f2f27}.grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:18px}.spec-table{width:100%;border-collapse:collapse;font-size:13px}.spec-table th,.spec-table td{padding:10px;border-bottom:1px solid var(--line);vertical-align:top;text-align:left}.preview-frame{background:#edf1f1;padding:20px;border-radius:16px}.unit-mock{aspect-ratio:1;background:linear-gradient(135deg,#f8fcfb,#ddf3ed);position:relative;overflow:hidden;border-radius:10px;border:1px solid #dce7e4}.unit-mock img{position:absolute;right:5%;bottom:5%;width:54%;height:74%;object-fit:contain}.unit-mock .placeholder{position:absolute;inset:0;background:linear-gradient(135deg,#ece4d9,#d9ece6);opacity:.58}.unit-mock .copy{position:absolute;left:6%;top:10%;width:46%;z-index:2}.unit-mock .copy b{display:block;font-size:clamp(18px,2.2vw,34px);line-height:1.25}.unit-mock .copy span{display:block;margin-top:12px;font-size:clamp(11px,1.15vw,17px);line-height:1.55}.layer{display:inline-block;padding:4px 8px;margin:2px;border:1px solid var(--line);border-radius:7px;background:#f8faf9;font-size:11px}.final-img{width:100%;height:auto;display:block;border-radius:10px;border:1px solid var(--line);background:#fff}@media(max-width:700px){.wrap{padding:14px}.grid{grid-template-columns:1fr}.top .hash{width:100%;margin-left:0;overflow:hidden;text-overflow:ellipsis}.unit-mock .copy{width:50%}.spec-table{font-size:11px}.spec-table th,.spec-table td{padding:7px}h1{font-size:26px}}`;
}

function reviewNav(spec) {
  return `<nav class="top"><strong>SwitchBot PDP v4</strong><a href="../review/story_review.html">Story Approval</a><a href="../review/layout_review.html">Layout Approval</a><a href="../preview/amazon_pdp_preview.html">Amazon Preview</a><a href="../review/design_review_cn.html">Design Review</a><a href="#gallery-review">Gallery</a><a href="#aplus-review">A+</a><a href="#qa-review">QA</a><span class="hash">Spec ${esc(spec.meta.spec_sha256)}</span></nav>`;
}

function gateClass(status) {
  const normalized = String(status || "").toUpperCase();
  return String(status).startsWith("Approved") || normalized === "PASS" ? "pass" : normalized === "BLOCKED" ? "block" : "";
}

export function ratingDisplayModel(product = {}) {
  const rating = product.rating || {};
  const status = String(rating.status || "").toLowerCase();
  const value = Number(rating.value);
  const count = Number(rating.count);
  const sourceText = typeof rating.source === "object" ? JSON.stringify(rating.source) : String(rating.source || "");
  const sourceType = String(rating.source_type || rating.sourceType || "").toLowerCase();
  const sourceAllowed = ["amazon_api", "amazon_verified_snapshot", "approved_marketplace_snapshot"].includes(sourceType)
    && Boolean(sourceText)
    && !/placeholder|fixture|dummy|mock|test/i.test(sourceText);
  const confirmed = ["confirmed", "approved", "verified"].includes(status);
  if (!confirmed || !sourceAllowed || !Number.isFinite(value) || value < 0 || value > 5 || !Number.isInteger(count) || count < 0) {
    return { available: false, text: "—", value: null, count: null };
  }
  return { available: true, text: `${value.toFixed(1)}／5（${count.toLocaleString("ja-JP")}件）`, value, count };
}

function referenceSourceLabel(decision) {
  const sources = decision?.reference_source || [];
  return sources.length ? sources.map((item) => `${item.brand || "Reference"} ${item.asin || ""}`.trim()).join(" / ") : "REFERENCE=OFF / Not Applicable";
}

function decisionTraceGrid({ id, consumerQuestion, storyRole, mainMessage, templateId, status, decision }) {
  const rows = [
    ["ID", id], ["Consumer Question", consumerQuestion], ["Story Role", storyRole], ["Main Message", mainMessage],
    ["Selected Reference", referenceSourceLabel(decision)], ["Reference Role", decision?.reference_role || decision?.story_role || "Not Applicable"],
    ["Decision Reason", decision?.decision_reason || "V4 default decision logic; Reference not applied."], ["Learned Principle", decision?.learned_principle || "Not Applicable"],
    ["SwitchBot Adaptation", decision?.switchbot_adaptation || "SwitchBot Product Truth, Claims and registered Primitive remain authoritative."],
    ["Layout Primitive", templateId], ["Why This Layout", decision?.why_layout_was_chosen || "Selected by the registered V4 role-to-Primitive mapping."],
    ["What Was Not Copied", decision?.intentionally_not_copied || "Competitor copy, images, UI, trade dress and complete layouts were not used."],
    ["Status", decision?.final_plan_decision || status || "Pending"],
  ];
  return `<dl class="trace-grid">${rows.map(([label, value]) => `<div><dt>${esc(label)}</dt><dd>${esc(value || "—")}</dd></div>`).join("")}</dl>`;
}

function buildStoryReview(spec) {
  const hero = spec.strategy.coreValue;
  const hierarchy = [spec.strategy.heroSellingPoint, ...(spec.strategy.coreSellingPoints || []), ...(spec.strategy.supportingFeatures || [])].filter(Boolean);
  const body = `${reviewNav(spec)}<main class="wrap"><section class="card"><span class="status ${gateClass(spec.human_gates.story_approval.status)}">${esc(spec.human_gates.story_approval.status)}</span><h1>Gate 1 · Story Approval</h1><p class="muted">正式视觉生成前，确认 Hero Value、7图结构、A+ Story、最终日文标题和卖点层级。Internal QA approval 不等于正式发布批准。</p></section><section class="card"><h2>Hero Value</h2><p style="font-size:28px;font-weight:750">${esc(hero)}</p></section><section class="card"><h2>7图结构</h2><table class="spec-table"><thead><tr><th>#</th><th>决策阶段</th><th>用户问题</th><th>最终日文 Headline</th><th>Template</th></tr></thead><tbody>${spec.product_images.map(item=>`<tr><td>${item.sequence}</td><td>${esc(item.stage_label_cn)}</td><td>${esc(item.user_question)}</td><td>${esc(item.headline||"主图无文案")}</td><td>${esc(item.template_id)}</td></tr>`).join("")}</tbody></table></section><section class="card"><h2>A+ Story</h2><table class="spec-table"><thead><tr><th>#</th><th>Story Role</th><th>Template</th><th>内容单元</th><th>Lead Headline</th></tr></thead><tbody>${spec.aplus_modules.map(module=>`<tr><td>${module.sequence}</td><td>${esc(module.story_role)}</td><td>${esc(module.template_id)}</td><td>${module.units.length}</td><td>${esc(module.module_headline)}</td></tr>`).join("")}</tbody></table></section><section class="card"><h2>Selling Point Hierarchy</h2><table class="spec-table"><thead><tr><th>Level</th><th>Feature</th><th>Benefit</th><th>Proof/Source</th><th>Status</th></tr></thead><tbody>${hierarchy.map(point=>`<tr><td>${esc(point.level)}</td><td>${esc(point.feature)}</td><td>${esc(point.benefit)}</td><td>${esc(point.proof||point.source)}</td><td>${esc(point.status)}</td></tr>`).join("")}</tbody></table></section></main>`;
  return htmlShell("Story Approval", body);
}

function layoutMock(item, outputDirPrefix = "../") {
  const product = `${outputDirPrefix}${item.layers.product_layer.source}`;
  return `<div class="unit-mock"><div class="placeholder"></div><img src="${esc(product)}" alt=""><div class="copy"><b>${esc(item.headline || item.key_message || "Product Main")}</b><span>${esc(item.sub_copy || "")}</span></div></div>`;
}

function buildLayoutReview(spec) {
  const body = `${reviewNav(spec)}<main class="wrap"><section class="card"><span class="status ${gateClass(spec.human_gates.layout_approval.status)}">${esc(spec.human_gates.layout_approval.status)}</span><h1>Gate 2 · Layout Approval</h1><p class="muted">真实产品图 + Placeholder 场景 + 最终文案 + 最终 Template/Layout。只有 Gate 2 通过后，渲染器才允许生产高保真 JPEG。</p></section><h2>7 Product Images</h2><section class="grid">${spec.product_images.map(item=>`<article class="card">${layoutMock(item)}<h3>${esc(item.id)} · ${esc(item.template_id)}</h3><p>${esc(item.role)}</p><p class="muted">Grid: ${esc(JSON.stringify(item.template_snapshot.grid))}<br>Mobile: ${esc((item.template_snapshot.mobile_rules||[]).join(" / "))}</p></article>`).join("")}</section><h2>A+ Modules</h2><section class="grid">${spec.aplus_modules.map(module=>`<article class="card">${layoutMock({...module,headline:module.module_headline,sub_copy:module.units[0]?.copy||"",layers:module.units[0]?.layers||{product_layer:{source:spec.product.main_asset}}})}<h3>${esc(module.id)} · ${esc(module.template_id)}</h3><p>${esc(module.story_role)}</p><p class="muted">Grid: ${esc(JSON.stringify(module.template_snapshot.grid))}<br>Mobile: ${esc((module.template_snapshot.mobile_rules||[]).join(" / "))}</p></article>`).join("")}</section></main>`;
  return htmlShell("Layout Approval", body);
}

function productStatus(item) {
  return item.asset_resolution?.product_layer_allowed === true && item.product_body_ai_generated === false ? "Product Layer Ready" : "Blocked for Final Launch";
}

function buildDesignReview(spec) {
  const visualQuality = visualQualityEnabled();
  const records = [
    ...spec.product_images.map(item=>({kind:"商品图",id:item.id,template:item.template_id,headline:item.headline,role:item.role,final:item.outputs.jpeg,item,units:[item]})),
    ...spec.aplus_modules.map(module=>({kind:"A+",id:module.id,template:module.template_id,headline:module.module_headline,role:module.story_role,final:module.outputs.jpeg,item:module,units:module.units})),
  ];
  const body = `${reviewNav(spec)}<main class="wrap"><section class="card"><h1>Design Review · 中文生产审阅</h1><p class="muted">消费者文案、模板、素材、Claim、Reference 决策与状态全部来自同一份 PRODUCT_PAGE_SPEC。Flattened JPEG 不是唯一源文件。</p><p><strong>Visual Quality：</strong>${visualQuality?"ON · 只参数化现有 Primitive，不改变 Story/Claim/Reference/Asset":"OFF · Production Baseline"}</p><span class="status ${gateClass(spec.publish_gate.status)}">Publish Gate ${esc(spec.publish_gate.status)}</span></section>${records.map(record=>{const lead=record.units[0];const claims=record.units.flatMap(unit=>unit.claim_sources||[]);const decision=record.item.reference_decision||lead.reference_decision;const kind=record.kind==="A+"?"aplus":"gallery";const profile=visualQuality?visualProfile(record.item,kind):null;const profileHtml=profile?`<section class="unit-traces"><h3>Visual Quality Parameters</h3><div class="trace-grid"><div><dt>Visual Role</dt><dd>${esc(profile.visual_role)}</dd></div><div><dt>Background</dt><dd>${esc(profile.background_family)}</dd></div><div><dt>Layout Family</dt><dd>${esc(profile.layout_family)}</dd></div><div><dt>Product Scale</dt><dd>${esc(profile.product_scale)}</dd></div><div><dt>Card Structure</dt><dd>${esc(profile.card_structure)}</dd></div><div><dt>Density</dt><dd>${esc(profile.information_density)}</dd></div>${profile.learned_principle?`<div><dt>Reference Principle</dt><dd>${esc(profile.learned_principle)}</dd></div><div><dt>Not Copied</dt><dd>${esc(profile.intentionally_not_copied)}</dd></div>`:""}</div></section>`:"";const trace=decisionTraceGrid({id:record.id,consumerQuestion:lead.user_question,storyRole:record.role,mainMessage:record.headline||lead.copy||lead.key_message,templateId:record.template,status:record.item.status||lead.status,decision});const unitTraces=record.kind==="A+"?`<section class="unit-traces"><h3>A+ Content Unit Decision Trace</h3>${record.units.map(unit=>decisionTraceGrid({id:unit.id,consumerQuestion:unit.user_question,storyRole:record.role,mainMessage:unit.headline||unit.copy,templateId:record.template,status:unit.status,decision:unit.reference_decision||decision})).join("")}</section>`:"";return `<article class="card"><div class="grid"><div><img class="final-img" src="../${esc(record.final)}" alt="${esc(record.id)}"></div><div><h2>${esc(record.id)} · ${esc(record.template)}</h2>${trace}<p><strong>素材需求：</strong>${esc(lead.asset_requirement||lead.asset_resolution?.selected_resolution||"")}</p><p><strong>Product Layer：</strong>${esc(lead.layers?.product_layer?.source||"")} <span class="layer">禁止AI产品</span></p><p><strong>Scene Layer：</strong>${esc(lead.layers?.scene_layer?.source||"Placeholder / programmatic background")} <span class="layer">AI仅可无产品场景</span></p><p><strong>Graphic Layer：</strong>HTML/CSS/SVG 程序化排版 <span class="layer">日文/比较表/UI禁止AI生成</span></p><p><strong>Claim来源：</strong>${claims.length?claims.map(c=>`${esc(c.claim_id)} · ${esc(c.status)} · ${esc(c.source_id)}`).join("<br>"):"无"}</p><p><strong>素材解析：</strong>${esc(lead.asset_resolution?.selected_resolution||"")} / ${esc(lead.asset_resolution?.authorization_status||"")}</p><p><strong>完成状态：</strong><span class="status ${productStatus(lead).startsWith("Blocked")?"block":"pass"}">${esc(productStatus(lead))}</span></p><p class="muted">Safe Area: ${esc(JSON.stringify(record.item.template_snapshot.safe_area))}<br>Headline: ${esc(JSON.stringify(record.item.template_snapshot.headline_length))}<br>Mobile: ${esc((record.item.template_snapshot.mobile_rules||[]).join(" / "))}</p></div></div>${profileHtml}${unitTraces}</article>`}).join("")}</main>`;
  const firstGalleryHeading = `<h2>${esc(spec.product_images[0]?.id)} ·`;
  const firstAplusHeading = `<h2>${esc(spec.aplus_modules[0]?.id)} ·`;
  return htmlShell("Design Review CN", body)
    .replace('<section class="card"><h1>Design Review', '<section id="qa-review" class="card"><h1>Design Review')
    .replace(firstGalleryHeading, `<span id="gallery-review" aria-hidden="true"></span>${firstGalleryHeading}`)
    .replace(firstAplusHeading, `<span id="aplus-review" aria-hidden="true"></span>${firstAplusHeading}`);
}

function buildAmazonPreview(spec) {
  const title = spec.titles[spec.titles.recommendedKey] || spec.titles.main;
  const images = spec.product_images;
  const fitUnits = spec.aplus_modules.find(module=>module.template_id==="A-COMPARISON")?.units || [];
  const rating = ratingDisplayModel(spec.product);
  const body = `<nav class="top"><strong>Amazon Preview</strong><button data-device="desktop">Desktop</button><button data-device="mobile">390px</button><a href="../review/design_review_cn.html">Design Review</a><span class="hash">Spec ${esc(spec.meta.spec_sha256)}</span></nav><main class="amazon" id="amazonRoot"><section class="pdp"><div class="gallery"><div class="thumbs">${images.map((item,index)=>`<button class="thumb ${index===0?"active":""}" data-src="../${esc(item.outputs.jpeg)}"><img src="../${esc(item.outputs.jpeg)}" alt=""></button>`).join("")}</div><div class="main-image"><img id="mainProductImage" src="../${esc(images[0].outputs.jpeg)}" alt="${esc(spec.product.name)}"></div></div><div class="detail"><p class="brand">SwitchBot</p><h1>${esc(title)}</h1><p class="rating ${rating.available?"":"rating-unavailable"}"><span data-rating-status="${rating.available?"confirmed":"unavailable"}">${esc(rating.text)}</span> <a href="#aplus">商品説明を見る</a></p><div class="price">価格はAmazon.co.jpでご確認ください</div><ul>${spec.bullets.map(item=>`<li><b>【${esc(item.headline)}】</b>${esc(item.body)}</li>`).join("")}</ul><div class="buy"><b>バリエーション</b><span>${esc(spec.product.variationPlaceholder||"1個")}</span><button>カートに入れる</button></div></div></section><section class="aplus" id="aplus"><h2>商品の説明</h2>${spec.aplus_modules.map(module=>`<picture><source media="(max-width:700px)" srcset="../design/aplus/mobile/aplus_${String(module.sequence).padStart(2,"0")}.jpg"><img src="../${esc(module.outputs.jpeg)}" alt="${esc(module.module_headline)}"></picture>`).join("")}</section><section class="consumer-card"><h2>ご購入前のチェックポイント</h2><div class="comparison">${fitUnits.map(unit=>`<div><b>${esc(unit.headline)}</b><span>${esc(unit.copy)}</span></div>`).join("")}</div></section><section class="consumer-card"><h2>よくある質問</h2>${spec.faq.map(item=>`<details><summary>${esc(item.question)}</summary><p>${esc(item.answer)}</p></details>`).join("")}</section></main>`;
  const styles = `.top button{border:1px solid #56706b;background:#22322f;color:#fff;padding:7px 10px;border-radius:7px}.amazon{max-width:1460px;margin:auto;background:#fff;padding:28px}.pdp{display:grid;grid-template-columns:minmax(0,1.12fr) minmax(420px,.88fr);gap:34px}.gallery{display:grid;grid-template-columns:72px 1fr;gap:14px}.thumbs{display:flex;flex-direction:column;gap:9px}.thumb{padding:0;background:#fff;border:1px solid #bbc4c2;border-radius:7px;overflow:hidden}.thumb.active{border:3px solid #23a98f}.thumb img{display:block;width:100%;aspect-ratio:1;object-fit:cover}.main-image img{display:block;width:100%;max-height:720px;object-fit:contain}.detail h1{font-size:26px;line-height:1.45;font-weight:500}.brand{color:#087a66}.rating{color:#8a5a00}.rating-unavailable{color:var(--muted)}.price{font-size:18px;border-top:1px solid #ddd;border-bottom:1px solid #ddd;padding:16px 0;margin:14px 0}.detail li{margin:10px 0;line-height:1.65}.buy{border:1px solid #d4d9d8;border-radius:12px;padding:18px;display:grid;gap:12px}.buy span{border:2px solid #23a98f;padding:10px;border-radius:8px}.buy button{border:0;border-radius:999px;background:#ffd814;padding:13px;font-size:16px}.aplus{max-width:1464px;margin:50px auto}.aplus picture,.aplus img{display:block;width:100%;margin:0 0 20px}.consumer-card{max-width:970px;margin:40px auto;border-top:1px solid #ddd;padding-top:24px}.comparison>div{display:grid;grid-template-columns:1fr 2fr;padding:12px;border-bottom:1px solid #e4e8e7}.consumer-card details{padding:12px;border-bottom:1px solid #e4e8e7}.consumer-card summary{font-weight:700}.amazon.mobile{max-width:390px;padding:12px}.amazon.mobile .pdp{grid-template-columns:1fr}.amazon.mobile .gallery{grid-template-columns:1fr}.amazon.mobile .thumbs{order:2;flex-direction:row;overflow:auto}.amazon.mobile .thumb{min-width:52px}.amazon.mobile .detail h1{font-size:19px}.amazon.mobile .aplus{margin-top:25px}.amazon.mobile .comparison>div{grid-template-columns:1fr}.amazon.mobile .consumer-card{margin:28px auto}@media(max-width:700px){.amazon{padding:12px}.pdp{grid-template-columns:1fr}.gallery{grid-template-columns:1fr}.thumbs{order:2;flex-direction:row;overflow:auto}.thumb{min-width:52px}.detail h1{font-size:19px}}`;
  const script = `document.querySelectorAll('.thumb').forEach(b=>b.addEventListener('click',()=>{document.querySelectorAll('.thumb').forEach(x=>x.classList.remove('active'));b.classList.add('active');document.getElementById('mainProductImage').src=b.dataset.src}));document.querySelectorAll('[data-device]').forEach(b=>b.addEventListener('click',()=>document.getElementById('amazonRoot').classList.toggle('mobile',b.dataset.device==='mobile')));`;
  return htmlShell("Amazon Japan PDP Preview", body, styles, script);
}

function markdownTable(headers, rows) {
  const clean = value => String(value ?? "").replaceAll("|", "\\|").replaceAll("\n", "<br>");
  return [`| ${headers.map(clean).join(" | ")} |`,`| ${headers.map(()=>"---").join(" | ")} |`,...rows.map(row=>`| ${row.map(clean).join(" | ")} |`)].join("\n");
}

export async function writeStoryReview(spec, outputDir) {
  const reviewDir = path.join(outputDir, "review");
  await fs.mkdir(reviewDir, { recursive: true });
  await fs.writeFile(path.join(reviewDir, "story_review.html"), buildStoryReview(spec), "utf8");
}

export async function writeLayoutReview(spec, outputDir) {
  const reviewDir = path.join(outputDir, "review");
  await fs.mkdir(reviewDir, { recursive: true });
  await fs.writeFile(path.join(reviewDir, "layout_review.html"), buildLayoutReview(spec), "utf8");
}

async function writeReviewPages(spec, outputDir) {
  await writeStoryReview(spec, outputDir);
  await writeLayoutReview(spec, outputDir);
}

async function writeFinalPages(spec, outputDir) {
  const reviewDir = path.join(outputDir, "review");
  const previewDir = path.join(outputDir, "preview");
  await Promise.all([reviewDir,previewDir].map(dir=>fs.mkdir(dir,{recursive:true})));
  await fs.writeFile(path.join(reviewDir, "design_review_cn.html"), buildDesignReview(spec), "utf8");
  await fs.writeFile(path.join(previewDir, "amazon_pdp_preview.html"), buildAmazonPreview(spec), "utf8");
  await fs.writeFile(path.join(previewDir, "mobile_preview.html"), buildAmazonPreview(spec).replace('class="amazon" id="amazonRoot"', 'class="amazon mobile" id="amazonRoot"'), "utf8");
}

async function writeReports(spec, outputDir, manifest) {
  const reports = path.join(outputDir, "reports");
  await fs.mkdir(reports, {recursive:true});
  const gateRows = Object.entries(spec.publish_gate.sections).map(([id,section])=>[id,section.status,section.requirement,section.failures.join("; ")]);
  await fs.writeFile(path.join(reports,"publish_gate.md"),`# Publish Gate\n\n- Status: **${spec.publish_gate.status}**\n- Spec SHA-256: \`${spec.meta.spec_sha256}\`\n- Structural completeness does not override publication approval.\n\n${markdownTable(["Gate","Status","Requirement","Failures"],gateRows)}\n`,"utf8");
  const assetRows = spec.asset_resolution_plan.records.map(item=>[item.visual_id,item.selected_resolution,item.source_type,item.source_path,item.file_resolved,item.source_verified,item.usage_approved,item.product_layer_allowed,item.scene_provenance?.source_type,item.authorization_status,item.status]);
  await fs.writeFile(path.join(reports,"asset_resolution_report.md"),`# Asset Resolver\n\nResolved means file path found only; it never implies Official, Verified or Approved.\n\n${markdownTable(["Visual","Resolution","Source Type","Source Path","File Resolved","Source Verified","Usage Approved","Product Layer Allowed","Scene Source Type","Authorization","Status"],assetRows)}\n`,"utf8");
  const copyRows = [...spec.product_images.filter(item=>item.id!=="IMAGE-01").map(item=>[item.id,item.headline,item.copy_review?.status,item.template_id]),...spec.aplus_modules.flatMap(module=>module.units.map(unit=>[unit.id,unit.headline,unit.copy_review?.status,module.template_id]))];
  await fs.writeFile(path.join(reports,"japan_localization_review.md"),`# Japan Localization Review\n\n- Status: **${spec.copy_review.status}**\n- Programmatic typography never converts an Auto Draft into a human-approved Japanese final.\n\n${markdownTable(["ID","Final Japanese Headline","Review Status","Template"],copyRows)}\n`,"utf8");
  const layoutRows=[...spec.product_images.map(item=>[item.id,item.template_id,item.template_snapshot.name,item.template_snapshot.mobile_rules.join(" / ")]),...spec.aplus_modules.map(item=>[item.id,item.template_id,item.template_snapshot.name,item.template_snapshot.mobile_rules.join(" / ")])];
  const registeredTemplateCount = spec.template_library?.registered_template_count || "see templates/template_library.json";
  await fs.writeFile(path.join(reports,"visual_consistency_report.md"),`# Visual Consistency\n\n- Registered templates: ${registeredTemplateCount}.\n- Used visual modules: 7 product / ${spec.aplus_modules.length} A+; no module count increase.\n- Every unit references one formal template_id.\n\n${markdownTable(["Visual","Template ID","Name","390px Rule"],layoutRows)}\n`,"utf8");
  const title=spec.titles[spec.titles.recommendedKey]||spec.titles.main;
  await fs.writeFile(path.join(reports,"final_copy_ja.md"),`# 商品タイトル\n\n${title}\n\n# 商品仕様・説明\n\n${spec.bullets.map(item=>`- 【${item.headline}】${item.body}`).join("\n")}\n`,"utf8");
  await fs.writeFile(path.join(reports,"source_register.md"),`# Source Register\n\n${markdownTable(["ID","Title","Type","URL / Path","Market","Last Verified","Status"],spec.sources.map(source=>[source.id,source.title,source.type,source.url||source.path,source.market,source.lastVerified,source.status]))}\n`,"utf8");
  await fs.writeFile(path.join(reports,"visual_production_manifest.json"),`${JSON.stringify(manifest,null,2)}\n`,"utf8");
  if (manifest.visual_quality) await fs.writeFile(path.join(reports,"VISUAL_QUALITY_MANIFEST.json"),`${JSON.stringify(manifest.visual_quality,null,2)}\n`,"utf8");
}

export async function renderFromSpec(spec, outputDir, selection = null) {
  await writeReviewPages(spec, outputDir);
  if (!spec.human_gates.final_render_authorized) {
    return { status: "Stopped at Layout Approval", rendered: false, reason: spec.human_gates.layout_approval.status };
  }
  const { default: sharp } = await import("sharp");
  assertRendererCoverage([...spec.product_images.map((item) => item.template_id), ...spec.aplus_modules.map((module) => module.template_id)]);
  const selectedProductIds = selection ? new Set(selection.product_ids || []) : null;
  const selectedAplusIds = selection ? new Set(selection.aplus_ids || []) : null;
  const visualQuality = visualQualityEnabled();
  const qualityManifest = visualQuality ? visualQualityManifest(spec) : null;
  const manifest = { schema_version:"4.0",derived_from:"spec/PRODUCT_PAGE_SPEC.json",spec_sha256:spec.meta.spec_sha256,visual_quality_mode:visualQuality?"ON":"OFF",visual_quality:qualityManifest,product_images:[],aplus_modules:[],layer_policy:spec.template_library.source_policy };
  for (const item of spec.product_images) {
    const productPath = item.layers.product_layer.source;
    const scenePath = item.layers.scene_layer.source;
    const productUri = await dataUri(outputDir, productPath);
    const sceneUri = await dataUri(outputDir, scenePath);
    const referenceRender = REQUIRED_REFERENCE_RENDERERS.includes(item.template_id)
      ? await renderReferencePrimitive({ templateId: item.template_id, record: item, outputDir, viewport: "desktop" })
      : null;
    const visualQualitySvg = visualQuality && item.template_id !== "P-MAIN-OFFICIAL" ? renderVisualQualityProduct({item,productUri,sceneUri}) : null;
    const rawSvg = visualQualitySvg || referenceRender?.svg || (item.template_id === "P-MAIN-OFFICIAL" ? `<svg xmlns="http://www.w3.org/2000/svg" width="2000" height="2000"><rect width="2000" height="2000" fill="#fff"/><image href="${esc(productUri)}" x="170" y="170" width="1660" height="1660" preserveAspectRatio="xMidYMid meet"/></svg>` : productTemplateSvg(item,productUri,sceneUri,spec));
    const svg = `<!-- PRODUCT_PAGE_SPEC ${spec.meta.spec_sha256} -->\n${rawSvg}`;
    const svgFile=path.join(outputDir,item.outputs.svg);const wireframeFile=path.join(outputDir,item.outputs.wireframe_svg);const jpegFile=path.join(outputDir,item.outputs.jpeg);
    if (selectedProductIds && !selectedProductIds.has(item.id) && await exists(jpegFile)) {
      manifest.product_images.push({id:item.id,template_id:item.template_id,product_layer:productPath,scene_layer:scenePath,graphic_layer:"programmatic SVG",svg:item.outputs.svg,jpeg:item.outputs.jpeg,jpeg_sha256:await sha256File(jpegFile),product_body_ai_generated:item.product_body_ai_generated,source_origin:item.source_origin,publication_status:productStatus(item),incremental_status:"Reused unchanged render"});
      continue;
    }
    await writeSvg(svgFile,svg);await writeSvg(wireframeFile,`<!-- PRODUCT_PAGE_SPEC ${spec.meta.spec_sha256} -->\n${wireframeSvg(item,false)}`);
    if(item.template_id==="P-MAIN-OFFICIAL"&&await exists(path.join(outputDir,productPath))) await renderMainToJpeg(sharp,path.join(outputDir,productPath),jpegFile,spec.meta.spec_sha256); else await renderSvgToJpeg(sharp,svg,jpegFile,spec.meta.spec_sha256);
    manifest.product_images.push({id:item.id,template_id:item.template_id,product_layer:productPath,scene_layer:scenePath,graphic_layer:"programmatic SVG",svg:item.outputs.svg,jpeg:item.outputs.jpeg,jpeg_sha256:await sha256File(jpegFile),product_body_ai_generated:item.product_body_ai_generated,source_origin:item.source_origin,publication_status:productStatus(item)});
  }
  for(const module of spec.aplus_modules){
    const prepared=[];
    for(const unit of module.units){prepared.push({unit,productUri:await dataUri(outputDir,unit.layers.product_layer.source),sceneUri:await dataUri(outputDir,unit.layers.scene_layer.source)});}
    const referenceRender = REQUIRED_REFERENCE_RENDERERS.includes(module.template_id)
      ? await renderReferencePrimitive({ templateId: module.template_id, record: module, outputDir, viewport: "desktop" })
      : null;
    const visualQualitySvg = visualQuality ? renderVisualQualityAplus({module,prepared}) : null;
    const svg=`<!-- PRODUCT_PAGE_SPEC ${spec.meta.spec_sha256} -->\n${visualQualitySvg || referenceRender?.svg || moduleSvg(module,prepared,spec)}`;const svgFile=path.join(outputDir,module.outputs.svg);const wireframeFile=path.join(outputDir,module.outputs.wireframe_svg);const jpegFile=path.join(outputDir,module.outputs.jpeg);
    const mobileSvgRelative=`design/aplus/mobile/aplus_${String(module.sequence).padStart(2,"0")}.svg`;
    const mobileJpegRelative=`design/aplus/mobile/aplus_${String(module.sequence).padStart(2,"0")}.jpg`;
    const mobileSvgRaw = visualQuality ? renderVisualQualityMobileAplus({module,prepared}) : (await renderReferencePrimitive({templateId:module.template_id,record:module,outputDir,viewport:"mobile"})).svg;
    const mobileSvg=`<!-- PRODUCT_PAGE_SPEC ${spec.meta.spec_sha256} -->\n${mobileSvgRaw}`;
    await writeSvg(path.join(outputDir,mobileSvgRelative),mobileSvg);
    await renderSvgToJpeg(sharp,mobileSvg,path.join(outputDir,mobileJpegRelative),spec.meta.spec_sha256);
    if (selectedAplusIds && !selectedAplusIds.has(module.id) && await exists(jpegFile)) {
      manifest.aplus_modules.push({id:module.id,template_id:module.template_id,units:module.units.length,svg:module.outputs.svg,jpeg:module.outputs.jpeg,jpeg_sha256:await sha256File(jpegFile),mobile_svg:mobileSvgRelative,mobile_jpeg:mobileJpegRelative,mobile_jpeg_sha256:await sha256File(path.join(outputDir,mobileJpegRelative)),product_layers:module.units.map(unit=>unit.layers.product_layer.source),scene_layers:module.units.map(unit=>unit.layers.scene_layer.source),graphic_layer:"programmatic SVG",publication_status:module.units.every(unit=>productStatus(unit)==="Product Layer Ready")?"Product Layer Ready":"Blocked for Final Launch",incremental_status:"Reused unchanged desktop render"});
      continue;
    }
    await writeSvg(svgFile,svg);await writeSvg(wireframeFile,`<!-- PRODUCT_PAGE_SPEC ${spec.meta.spec_sha256} -->\n${wireframeSvg(module,true)}`);await renderSvgToJpeg(sharp,svg,jpegFile,spec.meta.spec_sha256);
    manifest.aplus_modules.push({id:module.id,template_id:module.template_id,units:module.units.length,svg:module.outputs.svg,jpeg:module.outputs.jpeg,jpeg_sha256:await sha256File(jpegFile),mobile_svg:mobileSvgRelative,mobile_jpeg:mobileJpegRelative,mobile_jpeg_sha256:await sha256File(path.join(outputDir,mobileJpegRelative)),product_layers:module.units.map(unit=>unit.layers.product_layer.source),scene_layers:module.units.map(unit=>unit.layers.scene_layer.source),graphic_layer:"programmatic SVG",publication_status:module.units.every(unit=>productStatus(unit)==="Product Layer Ready")?"Product Layer Ready":"Blocked for Final Launch"});
  }
  const mobileReadability=await runMobileReadabilityGate(spec,outputDir);
  await fs.mkdir(path.join(outputDir,"qa"),{recursive:true});
  await fs.writeFile(path.join(outputDir,"qa","mobile-readability-gate.json"),`${JSON.stringify(mobileReadability,null,2)}\n`,"utf8");
  await writeFinalPages(spec,outputDir);await writeReports(spec,outputDir,manifest);
  return {status:mobileReadability.status==="PASS"?"Rendered":"Blocked by Mobile Readability Gate",rendered:true,product_images:spec.product_images.length,aplus_modules:spec.aplus_modules.length,mobile_readability:mobileReadability.status,spec_sha256:spec.meta.spec_sha256};
}
