import { visualProfile } from "./visual_quality_system.mjs";

const FONT = "'Hiragino Sans','Noto Sans JP','Yu Gothic',Arial,sans-serif";
const C = Object.freeze({ ink: "#17212B", muted: "#53636B", accent: "#23A98F", mint: "#DDF3ED", canvas: "#F7FAFA", paper: "#FFFFFF", warm: "#F3ECE3", cool: "#EDF6F6", line: "#CFE0DC" });

function esc(value) {
  return String(value ?? "").replaceAll("&", "&amp;").replaceAll("<", "&lt;").replaceAll(">", "&gt;").replaceAll('"', "&quot;").replaceAll("'", "&#039;");
}

function consumer(value) {
  return String(value || "").replace(/Need Verification|Blocked|Review Draft/g, "").replace(/（条件要確認）|（すべて要照合）|（表示条件確認）|（条件確認）/g, "").trim();
}

function wrap(value, maxChars, maxLines) {
  const clean = consumer(value);
  const characters = [...clean];
  const lines = [];
  while (characters.length && lines.length < maxLines) lines.push(characters.splice(0, maxChars).join(""));
  if (characters.length && lines.length) lines[lines.length - 1] = `${[...lines.at(-1)].slice(0, Math.max(1, maxChars - 1)).join("")}…`;
  return lines.length ? lines : [""];
}

function text(value, x, y, { size = 42, max = 18, lines = 3, weight = 700, fill = C.ink, gap = 1.28, anchor = "start", slot = "text" } = {}) {
  return `<g data-slot="${slot}">${wrap(value, max, lines).map((line, index) => `<text x="${x}" y="${y + index * size * gap}" text-anchor="${anchor}" font-family="${FONT}" font-size="${size}" font-weight="${weight}" fill="${fill}">${esc(line)}</text>`).join("")}</g>`;
}

function defs() {
  return `<defs><filter id="vqShadow" x="-25%" y="-25%" width="150%" height="170%"><feDropShadow dx="0" dy="18" stdDeviation="22" flood-color="#14342E" flood-opacity=".12"/></filter><linearGradient id="vqMint" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#FBFDFC"/><stop offset="1" stop-color="#DDF3ED"/></linearGradient><linearGradient id="vqWarm" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#FAF7F2"/><stop offset="1" stop-color="#EAE0D4"/></linearGradient></defs>`;
}

function image(uri, x, y, width, height, fit = "meet") {
  return uri ? `<g data-slot="image"><image href="${esc(uri)}" x="${x}" y="${y}" width="${width}" height="${height}" preserveAspectRatio="xMidYMid ${fit}" filter="url(#vqShadow)"/></g>` : `<g data-slot="image" data-fallback="true"><rect x="${x}" y="${y}" width="${width}" height="${height}" rx="24" fill="#E9F0EE" stroke="#AFC5C0" stroke-width="3" stroke-dasharray="12 10"/><text x="${x + width / 2}" y="${y + height / 2}" text-anchor="middle" font-family="${FONT}" font-size="20" font-weight="700" fill="#70827D">OFFICIAL PRODUCT ASSET</text></g>`;
}

function lead(record) {
  const unit = record.units?.[0] || record;
  return { title: record.module_headline || unit.headline || record.headline || record.key_message || "", body: unit.copy || record.sub_copy || "", units: record.units || [record] };
}

function displayProofs(item) {
  const internalOnly = /pending|not yet|test|fixture|dummy|placeholder|mechanism|selection-oriented|selling sku|final manual/i;
  const approved = (item.proof_items || [])
    .map((value) => consumer(value))
    .filter((value) => value && !internalOnly.test(value));
  const fallback = [item.key_message, item.sub_copy]
    .map((value) => consumer(value))
    .find((value) => value && !internalOnly.test(value));
  return (approved.length ? approved : fallback ? [fallback] : []).slice(0, 3);
}

export function renderVisualQualityProduct({ item, productUri = "", sceneUri = "" }) {
  const p = visualProfile(item, "gallery");
  const title = item.headline || item.key_message || "";
  const body = item.sub_copy || "";
  // Internal approval notes remain in the Spec and Design Review, but are not
  // promoted into consumer-facing artwork merely to fill a proof slot.
  const proofs = displayProofs(item);
  const header = `<!-- visual-quality ON ${esc(item.id)} ${p.visual_role} -->`;
  if (item.template_id === "P-HERO-SPLIT") return `${header}<svg xmlns="http://www.w3.org/2000/svg" width="2000" height="2000" viewBox="0 0 2000 2000">${defs()}<rect width="2000" height="2000" fill="url(#vqMint)"/><path d="M1250 0H2000V2000H1050C1210 1530 1195 470 1250 0Z" fill="#FFFFFF" opacity=".8"/><circle cx="1500" cy="780" r="520" fill="#CDEEE5"/>${text(title,120,420,{size:90,max:10,lines:4})}${text(body,126,900,{size:36,max:21,lines:4,weight:500,fill:C.muted,gap:1.48,slot:"body"})}${image(productUri,1040,280,820,1250)}<line x1="120" y1="1500" x2="760" y2="1500" stroke="${C.accent}" stroke-width="8"/>${text(item.key_message || "",120,1580,{size:29,max:22,lines:2,weight:650,slot:"claim"})}</svg>`;
  if (item.template_id === "P-FEATURE-SPLIT") return `${header}<svg xmlns="http://www.w3.org/2000/svg" width="2000" height="2000" viewBox="0 0 2000 2000">${defs()}<rect width="2000" height="2000" fill="${C.paper}"/><rect x="90" y="90" width="850" height="1820" fill="${C.cool}"/>${image(productUri,150,300,730,1250)}<path d="M910 520H1100" stroke="${C.accent}" stroke-width="8"/><circle cx="1125" cy="520" r="18" fill="${C.accent}"/>${text(title,1090,430,{size:82,max:10,lines:4})}${text(body,1095,900,{size:35,max:22,lines:4,weight:500,fill:C.muted,gap:1.45,slot:"body"})}<line x1="1095" y1="1450" x2="1840" y2="1450" stroke="${C.line}" stroke-width="4"/>${text(proofs[0] || item.key_message || "",1095,1550,{size:30,max:24,lines:3,weight:650,slot:"claim"})}</svg>`;
  if (item.template_id === "P-TECHNICAL-PROOF") return `${header}<svg xmlns="http://www.w3.org/2000/svg" width="2000" height="2000" viewBox="0 0 2000 2000">${defs()}<rect width="2000" height="2000" fill="${C.cool}"/>${text(title,110,210,{size:78,max:18,lines:2})}${text(body,114,420,{size:34,max:32,lines:2,weight:500,fill:C.muted,slot:"body"})}<circle cx="620" cy="1170" r="540" fill="#DCEFEA"/>${image(productUri,170,610,900,1040)}<g transform="translate(1210 610)">${(proofs.length ? proofs : [item.key_message]).slice(0,3).map((proof,index)=>`<g transform="translate(0 ${index*330})"><text x="0" y="42" font-family="${FONT}" font-size="24" font-weight="700" fill="${C.accent}">0${index+1}</text><line x1="0" y1="85" x2="650" y2="85" stroke="${C.line}" stroke-width="4"/>${text(proof,0,160,{size:31,max:22,lines:3,weight:650,slot:index===0?"claim":"body"})}</g>`).join("")}</g></svg>`;
  if (item.template_id === "P-LIFESTYLE-FULL") {
    const hasScene = Boolean(sceneUri);
    return `${header}<svg xmlns="http://www.w3.org/2000/svg" width="2000" height="2000" viewBox="0 0 2000 2000">${defs()}<rect width="2000" height="2000" fill="url(#vqWarm)"/>${hasScene ? `<image href="${esc(sceneUri)}" width="2000" height="2000" preserveAspectRatio="xMidYMid slice" opacity=".9"/>` : ""}<path d="M0 0H980V2000H0Z" fill="#FAF7F2" opacity=".92"/>${text(title,120,420,{size:86,max:12,lines:3})}${text(body,126,810,{size:36,max:23,lines:4,weight:500,fill:C.muted,gap:1.5,slot:"body"})}<line x1="120" y1="1280" x2="720" y2="1280" stroke="${C.accent}" stroke-width="8"/>${image(productUri,1040,300,820,1350)}</svg>`;
  }
  if (item.template_id === "P-COMPARISON") return `${header}<svg xmlns="http://www.w3.org/2000/svg" width="2000" height="2000" viewBox="0 0 2000 2000">${defs()}<rect width="2000" height="2000" fill="${C.paper}"/>${text(title,110,210,{size:76,max:14,lines:2})}${text(body,114,455,{size:33,max:31,lines:2,weight:500,fill:C.muted,slot:"body"})}${image(productUri,1490,100,360,390)}<g transform="translate(100 700)">${(proofs.length ? proofs : [item.key_message]).slice(0,3).map((proof,index)=>`<g transform="translate(0 ${index*350})"><text x="0" y="70" font-family="${FONT}" font-size="46" font-weight="700" fill="${C.accent}">0${index+1}</text><line x1="0" y1="115" x2="1800" y2="115" stroke="${C.line}" stroke-width="4"/>${text(proof,190,83,{size:34,max:38,lines:2,weight:650,slot:index===0?"claim":"body"})}</g>`).join("")}</g></svg>`;
  if (item.template_id === "P-PURCHASE-CONFIDENCE") return `${header}<svg xmlns="http://www.w3.org/2000/svg" width="2000" height="2000" viewBox="0 0 2000 2000">${defs()}<rect width="2000" height="2000" fill="${C.canvas}"/><rect x="0" y="0" width="820" height="2000" fill="url(#vqMint)"/>${image(productUri,110,480,650,1180)}${text(title,910,260,{size:76,max:18,lines:2})}${text(body,915,475,{size:33,max:31,lines:3,weight:500,fill:C.muted,slot:"body"})}<g transform="translate(910 760)">${(proofs.length ? proofs : [item.key_message]).slice(0,3).map((proof,index)=>`<g transform="translate(0 ${index*300})"><circle cx="32" cy="42" r="31" fill="${C.accent}"/><path d="M18 43l12 12 23-28" fill="none" stroke="#fff" stroke-width="8" stroke-linecap="round" stroke-linejoin="round"/><line x1="85" y1="90" x2="900" y2="90" stroke="${C.line}" stroke-width="4"/>${text(proof,90,52,{size:31,max:26,lines:3,weight:650,slot:index===0?"claim":"body"})}</g>`).join("")}</g></svg>`;
  return null;
}

export function renderVisualQualityAplus({ module, prepared = [] }) {
  const p = visualProfile(module, "aplus");
  const { title, body, units } = lead(module);
  const product = prepared[0]?.productUri || "";
  const scene = prepared.find((entry) => entry.sceneUri)?.sceneUri || "";
  const rows = units.slice(0,3);
  const header = `<!-- visual-quality ON ${esc(module.id)} ${p.visual_role} -->`;
  if (module.template_id === "A-HERO") return `${header}<svg xmlns="http://www.w3.org/2000/svg" width="1464" height="600" viewBox="0 0 1464 600">${defs()}<rect width="1464" height="600" fill="url(#vqMint)"/><path d="M790 0H1464V600H700C770 440 780 170 790 0Z" fill="#FFFFFF" opacity=".8"/><circle cx="1110" cy="300" r="240" fill="#CDEEE5"/>${text(title,58,155,{size:46,max:12,lines:3})}${text(body,62,360,{size:21,max:25,lines:4,weight:500,fill:C.muted,gap:1.42,slot:"body"})}${image(product,850,55,500,500)}</svg>`;
  if (module.template_id === "A-50-50-FEATURE") return `${header}<svg xmlns="http://www.w3.org/2000/svg" width="1464" height="620" viewBox="0 0 1464 620">${defs()}<rect width="1464" height="620" fill="${C.paper}"/><rect x="0" y="0" width="700" height="620" fill="#FAFCFB"/>${text(title,58,135,{size:47,max:18,lines:2})}${text(body,62,290,{size:23,max:34,lines:4,weight:500,fill:C.muted,gap:1.4,slot:"body"})}<line x1="62" y1="500" x2="620" y2="500" stroke="${C.accent}" stroke-width="5"/>${text(rows[1]?.headline || "",62,550,{size:21,max:28,lines:2,weight:650,slot:"claim"})}<rect x="700" y="0" width="764" height="620" fill="${C.mint}"/>${image(product,790,60,580,500)}</svg>`;
  if (module.template_id === "A-TECHNICAL" || module.template_id === "A-ECOSYSTEM") return `${header}<svg xmlns="http://www.w3.org/2000/svg" width="1464" height="620" viewBox="0 0 1464 620">${defs()}<rect width="1464" height="620" fill="${C.cool}"/>${text(title,54,90,{size:41,max:23,lines:2})}<circle cx="370" cy="390" r="250" fill="#DCEFEA"/>${image(product,85,165,570,395)}<g transform="translate(760 125)">${rows.map((unit,index)=>`<g transform="translate(0 ${index*145})"><text x="0" y="36" font-family="${FONT}" font-size="18" font-weight="700" fill="${C.accent}">0${index+1}</text><line x1="0" y1="60" x2="640" y2="60" stroke="${C.line}" stroke-width="3"/>${text(unit.headline,60,32,{size:22,max:23,lines:1,slot:"title"})}${text(unit.copy,60,78,{size:16,max:35,lines:2,weight:500,fill:C.muted,gap:1.25,slot:index===0?"claim":"body"})}</g>`).join("")}</g></svg>`;
  if (module.template_id === "A-THREE-FEATURE-GRID") return `${header}<svg xmlns="http://www.w3.org/2000/svg" width="1464" height="760" viewBox="0 0 1464 760">${defs()}<rect width="1464" height="760" fill="${C.canvas}"/>${text(title,62,82,{size:38,max:27,lines:1})}<g transform="translate(54 145)">${rows.map((unit,index)=>`<g transform="translate(${index*456} 0)"><rect width="420" height="545" rx="18" fill="${index===1?"#F0F7F5":"#FFFFFF"}"/><rect width="420" height="240" fill="${index===1?"#D7EEE8":"#E8F3F0"}"/>${image(prepared[index]?.sceneUri || prepared[index]?.productUri || product,45,20,330,205)}${text(unit.headline,30,318,{size:25,max:15,lines:2})}${text(unit.copy,30,420,{size:17,max:24,lines:4,weight:500,fill:C.muted,gap:1.38,slot:"body"})}</g>`).join("")}</g></svg>`;
  if (module.template_id === "A-LIFESTYLE") {
    const backdrop = scene ? `<image href="${esc(scene)}" width="1464" height="680" preserveAspectRatio="xMidYMid slice" opacity=".9"/>` : "";
    return `${header}<svg xmlns="http://www.w3.org/2000/svg" width="1464" height="680" viewBox="0 0 1464 680">${defs()}<rect width="1464" height="680" fill="url(#vqWarm)"/>${backdrop}<path d="M760 0H1464V680H680C740 520 750 160 760 0Z" fill="#FAF7F2" opacity=".93"/>${image(product,70,90,600,520)}${text(title,790,150,{size:43,max:13,lines:3})}${text(body,795,355,{size:21,max:28,lines:3,weight:500,fill:C.muted,gap:1.42,slot:"body"})}<line x1="795" y1="500" x2="1330" y2="500" stroke="${C.accent}" stroke-width="5"/>${rows[1] ? `${text(rows[1].headline,795,555,{size:19,max:31,lines:1,weight:700,slot:"title"})}${text(rows[1].copy,795,605,{size:15,max:49,lines:2,weight:500,fill:C.muted,gap:1.25,slot:"claim"})}` : ""}</svg>`;
  }
  if (module.template_id === "A-COMPARISON") return `${header}<svg xmlns="http://www.w3.org/2000/svg" width="1464" height="760" viewBox="0 0 1464 760">${defs()}<rect width="1464" height="760" fill="${C.paper}"/>${text(title,54,88,{size:40,max:26,lines:2})}${image(product,1130,35,240,190)}<g transform="translate(54 230)">${rows.map((unit,index)=>`<g transform="translate(0 ${index*160})"><text x="0" y="54" font-family="${FONT}" font-size="24" font-weight="700" fill="${C.accent}">0${index+1}</text><line x1="0" y1="82" x2="1356" y2="82" stroke="${C.line}" stroke-width="3"/>${text(unit.headline,82,46,{size:22,max:29,lines:1})}${text(unit.copy,82,105,{size:16,max:55,lines:2,weight:500,fill:C.muted,gap:1.25,slot:index===0?"claim":"body"})}</g>`).join("")}</g></svg>`;
  if (module.template_id === "A-FAQ") return `${header}<svg xmlns="http://www.w3.org/2000/svg" width="1464" height="700" viewBox="0 0 1464 700">${defs()}<rect width="1464" height="700" fill="${C.canvas}"/><rect x="0" y="0" width="820" height="700" fill="#FFFFFF"/>${text(title,58,125,{size:44,max:23,lines:2})}<line x1="58" y1="230" x2="690" y2="230" stroke="${C.accent}" stroke-width="5"/>${text(rows[0]?.headline || title,58,315,{size:25,max:25,lines:2,slot:"title"})}${text(rows[0]?.copy || body,58,430,{size:20,max:36,lines:4,weight:500,fill:C.muted,gap:1.4,slot:"body"})}<circle cx="1110" cy="355" r="260" fill="${C.mint}"/>${image(product,890,100,440,510)}</svg>`;
  return null;
}

function wrapAll(value, maxChars) {
  const characters = [...String(value || "").trim()];
  const lines = [];
  while (characters.length) lines.push(characters.splice(0, maxChars).join(""));
  return lines.length ? lines : [""];
}

function fullText(value, x, y, { size, max, weight = 500, fill = C.ink, gap = 1.28, field, unitId } = {}) {
  const lines = wrapAll(value, max);
  return {
    height: lines.length * size * gap,
    svg: `<g data-slot="${field}" data-field="${field}" data-unit-id="${esc(unitId)}">${lines.map((line, index) => `<text x="${x}" y="${y + index * size * gap}" font-family="${FONT}" font-size="${size}" font-weight="${weight}" fill="${fill}">${esc(line)}</text>`).join("")}</g>`,
  };
}

function unitContract(unit) {
  return {
    id: unit.id || "APLUS-UNIT",
    headline: String(unit.headline || "").trim(),
    body: String(unit.copy || unit.body || "").trim(),
    condition: String(unit.condition || unit.conditions || unit.consumer_condition || "").trim(),
    annotation: String(unit.annotation || unit.technical_annotation || unit.annotation_text || "").trim(),
  };
}

function mobileUnitCard(unit, index, y) {
  const content = unitContract(unit);
  // Coordinates inside this group are local. Adding the group translation to
  // text y-values clips text after rasterization while leaving SVG nodes in
  // the DOM, which is a false positive for content-presence checks.
  let cursor = 64;
  const blocks = [];
  const title = fullText(content.headline, 118, cursor, { size: 30, max: 20, weight: 700, field: "headline", unitId: content.id });
  blocks.push(title.svg);
  cursor += title.height + 24;
  const body = fullText(content.body, 72, cursor, { size: 27, max: 25, weight: 500, fill: C.muted, field: "body", unitId: content.id });
  blocks.push(body.svg);
  cursor += body.height + 20;
  if (content.condition) {
    const condition = fullText(content.condition, 72, cursor, { size: 23, max: 28, weight: 600, fill: "#355E55", field: "condition", unitId: content.id });
    blocks.push(condition.svg);
    cursor += condition.height + 16;
  }
  if (content.annotation) {
    const annotation = fullText(content.annotation, 72, cursor, { size: 23, max: 28, weight: 500, fill: C.muted, field: "annotation", unitId: content.id });
    blocks.push(annotation.svg);
    cursor += annotation.height + 16;
  }
  const height = Math.max(250, Math.ceil(cursor + 26));
  const svg = `<g class="aplus-unit-contract" data-unit-id="${esc(content.id)}" transform="translate(0 ${y})"><rect x="44" y="0" width="692" height="${height}" rx="22" fill="#FFFFFF"/><circle cx="82" cy="53" r="22" fill="${C.accent}"/><text x="82" y="61" text-anchor="middle" font-family="${FONT}" font-size="20" font-weight="700" fill="#FFFFFF">${index + 1}</text>${blocks.join("")}</g>`;
  return { svg, height };
}

export function renderVisualQualityMobileAplus({ module, prepared = [] }) {
  const p = visualProfile(module, "aplus");
  const { title, units } = lead(module);
  const product = prepared[0]?.productUri || "";
  const scene = prepared.find((entry) => entry.sceneUri)?.sceneUri || "";
  const rows = units.length ? units : [{ id: `${module.id}-LEAD`, headline: title, copy: "" }];
  const topHeight = p.visual_role === "SCENARIO" || p.visual_role === "BREATHE" ? 520 : 500;
  let cursor = topHeight;
  const cards = rows.map((unit, index) => {
    const card = mobileUnitCard(unit, index, cursor);
    cursor += card.height + 18;
    return card.svg;
  });
  const baseHeight = cursor + 36;
  const header = `<!-- visual-quality ON mobile ${esc(module.id)} ${p.visual_role} -->`;
  const background = p.visual_role === "SCENARIO" || p.visual_role === "BREATHE" ? "url(#vqWarm)" : p.visual_role === "PROOF" ? C.cool : p.visual_role === "IMPACT" ? "url(#vqMint)" : p.visual_role === "COMPARE" ? C.paper : C.canvas;
  const topVisual = p.visual_role === "SCENARIO" || p.visual_role === "BREATHE"
    ? `${scene ? `<image href="${esc(scene)}" x="0" y="0" width="780" height="${topHeight}" preserveAspectRatio="xMidYMid slice" opacity=".82"/>` : ""}<rect x="28" y="28" width="430" height="330" rx="18" fill="#FAF7F2" opacity=".93"/>${image(product,445,70,275,350)}`
    : `${p.visual_role === "PROOF" ? `<circle cx="560" cy="260" r="190" fill="#DCEFEA"/>` : ""}${image(product,440,95,280,335)}`;
  return `${header}<svg xmlns="http://www.w3.org/2000/svg" width="780" height="${baseHeight}" viewBox="0 0 780 ${baseHeight}">${defs()}<rect width="780" height="${baseHeight}" fill="${background}"/>${topVisual}${text(title,44,90,{size:42,max:16,lines:3,slot:"module-title"})}<line x1="44" y1="430" x2="650" y2="430" stroke="${C.accent}" stroke-width="5"/>${cards.join("")}</svg>`;
}
