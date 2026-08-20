#!/usr/bin/env node
import fs from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { loadReferenceLibrary } from "./reference_matcher.mjs";

const skillDir = path.dirname(path.dirname(fileURLToPath(import.meta.url)));
const libraryRoot = path.join(skillDir, "reference-library");

function md(value) {
  return String(value ?? "").replaceAll("|", "\\|").replaceAll("\n", " ");
}

function list(items) {
  return (items || []).map((item) => `- ${item}`).join("\n") || "- Not Available";
}

function referenceMarkdown(reference) {
  const galleryRows = reference.gallery_patterns.map((item) => `| ${item.position} | ${md(item.image_role)} | ${md(item.consumer_question)} | ${md(item.main_message)} | ${md(item.layout_type)} | ${md(item.product_scale)} | ${md(item.text_density)} | ${md(item.content_type.join(" / "))} | ${md(item.why_effective)} |`).join("\n");
  const aplusRows = reference.aplus_patterns.map((item) => `| ${item.position} | ${md(item.module_type)} | ${md(item.story_role)} | ${md(item.layout)} | ${md(item.message)} | ${md(item.visual_density)} | ${md(item.product_presence)} | ${md(item.scene_presence)} | ${md(item.technical_information)} | ${md(item.interaction_type)} | ${md(item.rhythm_relation)} |`).join("\n");
  const grammarRows = Object.entries(reference.visual_patterns).map(([key, value]) => `| ${key.replaceAll("_", " ")} | ${md(value)} |`).join("\n");
  return `# ${reference.brand} ${reference.product} — Reference Analysis\n\n- ASIN: ${reference.asin}\n- Source: ${reference.source_url}\n- Observed: ${reference.observed_on}\n- Category: ${reference.category}\n- Page type: ${reference.page_type.join(" / ")}\n- Complexity: ${reference.complexity}\n\n## Observation Boundary\n\n- Desktop: ${reference.observation.desktop}\n- Mobile: ${reference.observation.mobile}\n${list(reference.observation.limitations)}\n\n## Story Architecture\n\n${reference.story_patterns.join(" → ")}\n\nStrengths:\n\n${list(reference.strengths)}\n\nWeaknesses:\n\n${list(reference.weaknesses)}\n\n## Product Gallery\n\n| # | Image Role | Consumer Question | Main Message | Layout | Product Scale | Text Density | Type | Why Effective |\n|---:|---|---|---|---|---|---|---|---|\n${galleryRows}\n\n## A+ Structure\n\n| # | Module Type | Story Role | Layout | Message | Density | Product | Scene | Technical | Interaction | Rhythm Relation |\n|---:|---|---|---|---|---|---|---|---|---|---|\n${aplusRows}\n\n## Visual Grammar\n\n| Dimension | Observation |\n|---|---|\n${grammarRows}\n\n## USE\n\n${list(reference.use)}\n\n## ADAPT\n\n${list(reference.adapt)}\n\n## AVOID\n\n${list(reference.avoid)}\n\n## Good For\n\n${list(reference.good_for)}\n`;
}

function storyMarkdown(data) {
  return `# Story Pattern Library\n\n> ${data.principle}\n\n${data.patterns.map((pattern) => `## ${pattern.name}\n\n- Pattern ID: \`${pattern.pattern_id}\`\n- Consumer trigger: ${pattern.consumer_trigger}\n- Reference ASINs: ${pattern.reference_asins.join(", ")}\n- Sequence: ${pattern.recommended_sequence.join(" → ")}\n\nUSE:\n\n${list(pattern.use)}\n\nADAPT:\n\n${list(pattern.adapt)}\n\nAVOID:\n\n${list(pattern.avoid)}`).join("\n\n")}\n`;
}

function sequenceMarkdown(title, data, key) {
  return `# ${title}\n\n> ${data.principle}\n\n${data.sequences.map((sequence) => `## ${sequence.sequence_id}\n\n- Best for: ${sequence.best_for.join(" / ")}\n- Reference ASINs: ${sequence.reference_asins.join(", ")}\n- Sequence: ${sequence[key].join(" → ")}\n- Logic / Rhythm: ${sequence.logic || sequence.rhythm}`).join("\n\n")}\n`;
}

function layoutMarkdown(data) {
  const rows = data.mappings.map((item) => `| ${item.template_id} | ${item.family} | ${md(item.primitive)} | ${item.primary_role} | ${item.secondary_roles.join(" / ")} | ${md(item.best_when)} | ${md(item.reference_learning)} | ${md(item.boundaries.join("; "))} |`).join("\n");
  return `# Layout Primitive Mapping\n\n> ${data.principle}\n\nVisual Roles: ${data.visual_roles.join(" / ")}\n\n| Template ID | Family | Layout Primitive | Primary Role | Secondary Roles | Best When | Reference Learning | Boundaries |\n|---|---|---|---|---|---|---|---|\n${rows}\n`;
}

function viewerClient() {
  const data = window.__REFERENCE_LIBRARY__;
  let current = data.references[0]?.asin;
  let view = "references";
  const esc = (value) => String(value ?? "").replace(/[&<>"']/g, (character) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", "\"": "&quot;", "'": "&#039;" })[character]);
  const pills = (items) => items.map((item) => `<span class="tag">${esc(item)}</span>`).join("");
  const bullets = (items) => `<ul>${items.map((item) => `<li>${esc(item)}</li>`).join("")}</ul>`;
  function renderReference(references = data.references) {
    const reference = references.find((item) => item.asin === current) || references[0];
    if (!reference) {
      document.querySelector("#app").innerHTML = '<div class="empty">No matching reference.</div>';
      return;
    }
    current = reference.asin;
    document.querySelector("#app").innerHTML = `<div class="workspace"><aside class="rail"><input class="search" aria-label="Search references" placeholder="Search brand, product, ASIN"><div class="ref-list">${references.map((item) => `<button class="ref-button" data-asin="${esc(item.asin)}" aria-label="${esc(`${item.brand} ${item.product} ${item.asin} ${item.category}`)}" aria-current="${item.asin === reference.asin}"><strong>${esc(item.brand)} · ${esc(item.product)} · ${esc(item.asin)}</strong></button>`).join("")}</div></aside><article class="view"><section class="hero"><div class="hero-top">${pills(reference.page_type)}<span class="tag">${esc(reference.complexity)}</span></div><h2>${esc(reference.brand)}<br>${esc(reference.product)}</h2><p>${esc(reference.category)} · <a href="${esc(reference.source_url)}">Amazon source</a> · observed ${esc(reference.observed_on)}</p><p>${esc(reference.observation.mobile)}</p></section><div class="summary-strip"><section class="use"><h3>USE</h3>${bullets(reference.use)}</section><section class="adapt"><h3>ADAPT</h3>${bullets(reference.adapt)}</section><section class="avoid"><h3>AVOID</h3>${bullets(reference.avoid)}</section></div><section class="block"><h3>Visual Grammar</h3><div class="grammar">${Object.entries(reference.visual_patterns).map(([key, value]) => `<div><b>${esc(key.replaceAll("_", " "))}</b><span>${esc(value)}</span></div>`).join("")}</div></section><section class="block"><h3>Product Gallery · ${reference.gallery_patterns.length}</h3><p class="block-note">逐图记录 Consumer Question、角色、密度与有效原因。</p><div class="table-wrap"><table><thead><tr><th>#</th><th>Role / Type</th><th>Consumer Question</th><th>Main Message</th><th>Layout / Scale / Density</th><th>Why Effective</th></tr></thead><tbody>${reference.gallery_patterns.map((item) => `<tr><td class="num">${item.position}</td><td><b>${esc(item.image_role)}</b><br>${esc(item.content_type.join(" / "))}</td><td>${esc(item.consumer_question)}</td><td>${esc(item.main_message)}<br><small>${esc(item.feature)} → ${esc(item.benefit)}</small></td><td>${esc(item.layout_type)}<br>${esc(item.product_scale)} · ${esc(item.text_density)} · ${esc(item.background)}</td><td>${esc(item.why_effective)}</td></tr>`).join("")}</tbody></table></div></section><section class="block"><h3>A+ Structure · ${reference.aplus_patterns.length}</h3><p class="block-note">Major container level. Carousel内各卡片作为Interaction记录，不把卡片数误当成独立Story Module。</p><div class="table-wrap"><table><thead><tr><th>#</th><th>Module / Role</th><th>Message</th><th>Layout / Interaction</th><th>Presence / Density</th><th>Rhythm Relation</th></tr></thead><tbody>${reference.aplus_patterns.map((item) => `<tr><td class="num">${item.position}</td><td><b>${esc(item.module_type)}</b><br>${esc(item.story_role)}</td><td>${esc(item.message)}</td><td>${esc(item.layout)}<br>${esc(item.interaction_type)}</td><td>Visual ${esc(item.visual_density)}<br>Product ${esc(item.product_presence)} · Scene ${esc(item.scene_presence)} · Tech ${esc(item.technical_information)}</td><td>${esc(item.rhythm_relation)}</td></tr>`).join("")}</tbody></table></div></section></article></div>`;
    wireReferences();
  }
  function wireReferences() {
    document.querySelectorAll(".ref-button").forEach((button) => {
      button.onclick = () => { current = button.dataset.asin; renderReference(); };
    });
    const search = document.querySelector(".search");
    if (search) search.oninput = () => {
      const query = search.value.trim().toLowerCase();
      const filtered = data.references.filter((reference) => [reference.asin, reference.brand, reference.product, reference.category, ...reference.page_type].join(" ").toLowerCase().includes(query));
      renderReference(filtered.length ? filtered : data.references);
    };
  }
  function renderStory() {
    document.querySelector("#app").innerHTML = `<section class="block"><h3>Story Pattern Library</h3><p class="block-note">${esc(data.story.principle)}</p></section><div class="library-grid">${data.story.patterns.map((pattern) => `<article class="pattern"><p class="eyebrow">${esc(pattern.pattern_id)}</p><h3>${esc(pattern.name)}</h3><p>${esc(pattern.consumer_trigger)}</p><div class="sequence"><span>Sequence</span><br>${esc(pattern.recommended_sequence.join(" → "))}</div><b>USE</b>${bullets(pattern.use)}<b>ADAPT</b>${bullets(pattern.adapt)}<b>AVOID</b>${bullets(pattern.avoid)}</article>`).join("")}</div>`;
  }
  function renderSequences(kind, title, key) {
    const set = data[kind];
    document.querySelector("#app").innerHTML = `<section class="block"><h3>${esc(title)}</h3><p class="block-note">${esc(set.principle)}</p>${set.sequences.map((sequence) => `<div class="sequence"><p class="eyebrow">${esc(sequence.sequence_id)}</p><b>${esc(sequence.best_for.join(" / "))}</b><p>${esc(sequence[key].join(" → "))}</p><span>${esc(sequence.logic || sequence.rhythm)}</span></div>`).join("")}</section>`;
  }
  function renderLayout() {
    document.querySelector("#app").innerHTML = `<section class="block"><h3>19 Existing Templates → Layout Primitives</h3><p class="block-note">${esc(data.layout.principle)}</p>${data.layout.mappings.map((mapping) => `<div class="mapping"><code>${esc(mapping.template_id)}</code><div class="role">${esc(mapping.primary_role)}</div><div><b>${esc(mapping.primitive)}</b><p>${esc(mapping.best_when)}</p><p>Boundary: ${esc(mapping.boundaries.join(" · "))}</p></div></div>`).join("")}</section>`;
  }
  function render() {
    if (view === "references") renderReference();
    if (view === "story") renderStory();
    if (view === "gallery") renderSequences("gallery", "Gallery Sequence Library", "roles");
    if (view === "aplus") renderSequences("aplus", "A+ Sequence Library", "modules");
    if (view === "layout") renderLayout();
    document.querySelectorAll(".tab").forEach((button) => button.setAttribute("aria-selected", String(button.dataset.view === view)));
  }
  document.querySelectorAll(".tab").forEach((button) => {
    button.onclick = () => { view = button.dataset.view; render(); };
  });
  render();
}

function htmlPayload(references, story, gallery, aplus, layout) {
  const payload = JSON.stringify({ references, story, gallery, aplus, layout }).replaceAll("</script", "<\\/script");
  return `<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <meta name="color-scheme" content="light">
  <title>Amazon Japan PDP Reference Library</title>
  <style>
    /* Hallmark · pre-emit critique: P5 H5 E5 S5 R5 V4 · macrostructure: Knowledge-workbench · theme: studied-DNA (source: six Amazon Japan references, principles only) · genre: modern-minimal utility · tone: analytical, restrained · anchor: mint · contrast: pass (40–41) · nav: N5 · footer: Ft1 · slop: pass (42–45) · honest: pass (46) · chrome: pass (47) · tokens: pass (48) · responsive: pass (49) · icons: pass (30) · mobile: pass (34,49,50–57) */
    :root{
      --color-ink:#17212b;--color-muted:#59666f;--color-paper:#f3f5f2;--color-surface:#ffffff;--color-line:#d9dfdb;--color-accent:#13a88a;--color-accent-deep:#08745f;--color-accent-ink:#10261f;--color-warning:#8a5a18;--color-danger:#8e332c;--color-panel-muted:#eef2ef;--color-panel-ink:#435059;--color-hover:#e5ebe7;--color-hero-muted:#cbd4d2;--color-hero-link:#86e7d2;--color-sticky:rgba(243,245,242,.92);--color-surface-translucent:rgba(255,255,255,.65);--color-tag-border:rgba(255,255,255,.2);--color-focus-shadow:rgba(19,168,138,.12);--color-shadow:rgba(23,33,43,.08);--color-transparent:transparent;--space-3xs:4px;--space-2xs:8px;--space-xs:12px;--space-sm:16px;--space-md:20px;--space-lg:24px;--space-xl:32px;--space-2xl:40px;--space-3xl:48px;--space-4xl:64px;--radius-sm:4px;--radius-md:12px;--radius-lg:14px;--radius-xl:18px;--radius-pill:999px;--shadow-elevated:0 14px 42px var(--color-shadow);--layout-max:1460px;--font-body:"Hiragino Sans","Yu Gothic UI","Noto Sans JP","PingFang SC",sans-serif;--font-display:"Avenir Next","Hiragino Kaku Gothic ProN","Yu Gothic UI",sans-serif
    }
    *{box-sizing:border-box}html{background:var(--color-paper);color:var(--color-ink);font-family:var(--font-body);overflow-x:clip}body{margin:0;min-width:0;overflow-x:clip}button,input{font:inherit}button{color:inherit;outline:2px solid var(--color-transparent);outline-offset:1px}button:focus-visible{outline-color:var(--color-accent-deep)}button:active{background:var(--color-line)}button:disabled{opacity:.55;cursor:not-allowed;background:var(--color-panel-muted);color:var(--color-muted)}.shell{max-width:var(--layout-max);margin:auto;padding:var(--space-lg)}.mast{display:grid;grid-template-columns:minmax(0,1fr) auto;gap:var(--space-md);align-items:end;padding:var(--space-xl) var(--space-3xs) var(--space-lg);border-bottom:1px solid var(--color-line)}.eyebrow{margin:0 0 var(--space-2xs);color:var(--color-accent-deep);font-size:12px;font-weight:800;letter-spacing:.12em;text-transform:uppercase}.mast h1{margin:0;max-width:18ch;min-width:0;overflow-wrap:anywhere;font-family:var(--font-display);font-size:clamp(32px,5vw,64px);line-height:1;letter-spacing:-.045em}.mast p{max-width:68ch;margin:var(--space-sm) 0 0;color:var(--color-muted);line-height:1.7}.count{display:flex;gap:var(--space-sm);align-items:center}.count b{display:block;font-family:var(--font-display);font-size:28px}.count span{font-size:12px;color:var(--color-muted)}.tabs{display:flex;gap:var(--space-2xs);align-items:center;padding:var(--space-sm) 0;position:sticky;top:0;z-index:5;background:var(--color-sticky);backdrop-filter:blur(16px);overflow-x:auto}.tab{border:0;background:var(--color-transparent);border-radius:var(--radius-pill);padding:var(--space-xs) var(--space-sm);white-space:nowrap;cursor:pointer;line-height:1}.tab:hover{background:var(--color-hover)}.tab:active{background:var(--color-line)}.tab[aria-selected="true"]{background:var(--color-ink);color:var(--color-surface)}.workspace{display:grid;grid-template-columns:300px minmax(0,1fr);gap:var(--space-xl);align-items:start}.rail{position:sticky;top:72px;max-height:calc(100vh - 96px);overflow:auto;padding-right:var(--space-3xs)}.search{width:100%;min-height:44px;border:1px solid var(--color-line);border-radius:var(--radius-md);background:var(--color-surface);padding:var(--space-xs) var(--space-sm);outline:2px solid var(--color-transparent);outline-offset:1px}.search:hover{border-color:var(--color-accent)}.search:focus-visible{border-color:var(--color-accent);outline-color:var(--color-accent-deep);box-shadow:0 0 0 3px var(--color-focus-shadow)}.search:active{background:var(--color-panel-muted)}.search:disabled{opacity:.55;cursor:not-allowed;background:var(--color-panel-muted);color:var(--color-muted)}.ref-list{display:grid;gap:var(--space-2xs);margin-top:var(--space-xs)}.ref-button{width:100%;border:1px solid var(--color-transparent);background:var(--color-transparent);border-radius:var(--radius-lg);padding:var(--space-xs);text-align:left;cursor:pointer}.ref-button:hover,.ref-button:focus-visible{border-color:var(--color-line);background:var(--color-surface-translucent)}.ref-button:active{background:var(--color-hover)}.ref-button[aria-current="true"]{background:var(--color-surface);border-color:var(--color-line);box-shadow:var(--shadow-elevated)}.ref-button strong,.ref-button small{display:block;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}.ref-button small{margin-top:var(--space-3xs);color:var(--color-muted)}.view{min-width:0}.hero{padding:var(--space-xl);border-radius:var(--radius-xl);background:var(--color-ink);color:var(--color-surface);box-shadow:var(--shadow-elevated)}.hero-top{display:flex;flex-wrap:wrap;gap:var(--space-2xs);align-items:center}.tag{display:inline-flex;border:1px solid var(--color-tag-border);border-radius:var(--radius-pill);padding:var(--space-3xs) var(--space-2xs);font-size:12px}.hero h2{min-width:0;overflow-wrap:anywhere;font-family:var(--font-display);font-size:clamp(28px,4vw,52px);line-height:1.05;letter-spacing:-.035em;margin:var(--space-sm) 0 var(--space-2xs)}.hero a{color:var(--color-hero-link);outline:2px solid var(--color-transparent);outline-offset:1px}.hero a:hover{text-decoration-thickness:2px}.hero a:focus-visible{outline-color:var(--color-hero-link)}.hero a:active{color:var(--color-surface)}.hero p{max-width:72ch;color:var(--color-hero-muted);line-height:1.65}.summary-strip{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:1px;margin:var(--space-sm) 0;background:var(--color-line);border:1px solid var(--color-line);border-radius:var(--radius-xl);overflow:hidden}.summary-strip section{background:var(--color-surface);padding:var(--space-md)}.summary-strip h3{margin:0 0 var(--space-xs);font-size:13px;letter-spacing:.08em}.summary-strip ul{margin:0;padding-left:var(--space-md);color:var(--color-muted);line-height:1.6}.summary-strip .use h3{color:var(--color-accent-deep)}.summary-strip .adapt h3{color:var(--color-warning)}.summary-strip .avoid h3{color:var(--color-danger)}.block{margin:var(--space-sm) 0;padding:var(--space-lg);border:1px solid var(--color-line);border-radius:var(--radius-xl);background:var(--color-surface)}.block h3{margin:0 0 var(--space-sm);font-family:var(--font-display);font-size:24px;letter-spacing:-.02em}.block-note{max-width:72ch;color:var(--color-muted);line-height:1.65}.grammar{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:0 var(--space-lg)}.grammar div{padding:var(--space-xs) 0;border-bottom:1px solid var(--color-line)}.grammar b{display:block;font-size:12px;text-transform:uppercase;letter-spacing:.08em;color:var(--color-accent-deep)}.grammar span{display:block;margin-top:var(--space-2xs);line-height:1.55;color:var(--color-muted)}.table-wrap{overflow:auto;border:1px solid var(--color-line);border-radius:var(--radius-lg)}table{border-collapse:collapse;width:100%;min-width:900px;font-size:13px}th,td{padding:var(--space-xs);border-bottom:1px solid var(--color-line);vertical-align:top;text-align:left;line-height:1.5}th{position:sticky;top:0;background:var(--color-panel-muted);color:var(--color-panel-ink);font-size:11px;text-transform:uppercase;letter-spacing:.06em}tr:last-child td{border-bottom:0}.num{font-variant-numeric:tabular-nums;color:var(--color-accent-deep);font-weight:800}.library-grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:var(--space-sm)}.pattern{border-top:4px solid var(--color-accent);border-radius:var(--radius-sm) var(--radius-sm) var(--radius-xl) var(--radius-xl);background:var(--color-surface);padding:var(--space-lg);box-shadow:var(--shadow-elevated)}.pattern h3{margin:0;font-family:var(--font-display)}.pattern p{max-width:72ch;color:var(--color-muted);line-height:1.6}.sequence{padding:var(--space-xs) 0;border-top:1px solid var(--color-line);line-height:1.6}.sequence span{color:var(--color-accent-deep);font-weight:700}.mapping{display:grid;grid-template-columns:180px 120px minmax(0,1fr);gap:var(--space-xs);padding:var(--space-sm) 0;border-top:1px solid var(--color-line);align-items:start}.mapping code{font-weight:800}.mapping .role{color:var(--color-accent-deep);font-weight:800}.mapping p{max-width:72ch;margin:0;color:var(--color-muted);line-height:1.55}.empty{padding:var(--space-2xl);text-align:center;color:var(--color-muted)}footer{padding:var(--space-2xl) 0;color:var(--color-muted);font-size:12px}.hidden{display:none!important}
    @media(max-width:900px){.shell{padding:var(--space-sm)}.mast{grid-template-columns:1fr}.count{justify-content:flex-start}.workspace{grid-template-columns:1fr}.rail{position:static;max-height:none}.ref-list{grid-template-columns:repeat(3,minmax(210px,1fr));overflow:auto;padding-bottom:var(--space-2xs)}.summary-strip{grid-template-columns:1fr}.library-grid{grid-template-columns:1fr}.grammar{grid-template-columns:1fr}}
    @media(max-width:540px){.shell{padding:var(--space-2xs)}.mast{padding:var(--space-lg) var(--space-3xs) var(--space-xl)}.mast h1{font-size:36px}.count{gap:var(--space-xs)}.count b{font-size:24px}.hero,.block,.pattern{padding:var(--space-sm)}.ref-list{grid-template-columns:repeat(6,225px)}.mapping{grid-template-columns:1fr;gap:var(--space-3xs)}.tabs{top:0}.summary-strip section{padding:var(--space-sm)}}
  </style>
</head>
<body>
  <div class="shell">
    <header class="mast">
      <div><p class="eyebrow">SwitchBot · Amazon Japan PDP Generator V4</p><h1>Reference Library</h1><p>把优秀页面转成可检索的故事结构、信息密度与视觉节奏知识。Reference 是设计决策输入，不是竞品素材库。</p></div>
      <div class="count"><div><b>${references.length}</b><span>Live references</span></div><div><b>${layout.mappings.length}</b><span>Existing primitives</span></div><div><b>${story.patterns.length}</b><span>Story patterns</span></div></div>
    </header>
    <nav class="tabs" aria-label="Library views"><button class="tab" data-view="references" aria-selected="true">References</button><button class="tab" data-view="story" aria-selected="false">Story Patterns</button><button class="tab" data-view="gallery" aria-selected="false">Gallery Sequences</button><button class="tab" data-view="aplus" aria-selected="false">A+ Sequences</button><button class="tab" data-view="layout" aria-selected="false">Layout Mapping</button></nav>
    <main id="app"></main>
    <footer>Observed 2026-08-18 · Desktop 1440×1000 + real browser 390×844 viewport · Competitor images and copy are not embedded.</footer>
  </div>
  <script>window.__REFERENCE_LIBRARY__=${payload};</script>
  <script>(${viewerClient.toString()})();</script>
</body>
</html>`;
}

const references = await loadReferenceLibrary(libraryRoot);
const story = JSON.parse(await fs.readFile(path.join(libraryRoot, "patterns", "story_pattern_library.json"), "utf8"));
const gallery = JSON.parse(await fs.readFile(path.join(libraryRoot, "patterns", "gallery_sequence_library.json"), "utf8"));
const aplus = JSON.parse(await fs.readFile(path.join(libraryRoot, "patterns", "aplus_sequence_library.json"), "utf8"));
const layout = JSON.parse(await fs.readFile(path.join(libraryRoot, "layout", "layout_primitive_mapping.json"), "utf8"));

for (const reference of references) {
  await fs.writeFile(path.join(libraryRoot, "references", reference.asin, "analysis.md"), referenceMarkdown(reference), "utf8");
}
await fs.writeFile(path.join(libraryRoot, "patterns", "story_pattern_library.md"), storyMarkdown(story), "utf8");
await fs.writeFile(path.join(libraryRoot, "patterns", "gallery_sequence_library.md"), sequenceMarkdown("Gallery Sequence Library", gallery, "roles"), "utf8");
await fs.writeFile(path.join(libraryRoot, "patterns", "aplus_sequence_library.md"), sequenceMarkdown("A+ Sequence Library", aplus, "modules"), "utf8");
await fs.writeFile(path.join(libraryRoot, "layout", "layout_primitive_mapping.md"), layoutMarkdown(layout), "utf8");
await fs.writeFile(path.join(libraryRoot, "index.json"), `${JSON.stringify({ schema_version: "1.0", observed_on: "2026-08-18", references: references.map((reference) => ({ asin: reference.asin, brand: reference.brand, product: reference.product, category: reference.category, page_type: reference.page_type, complexity: reference.complexity, json: `references/${reference.asin}/reference.json`, analysis: `references/${reference.asin}/analysis.md` })), patterns: ["patterns/story_pattern_library.json", "patterns/gallery_sequence_library.json", "patterns/aplus_sequence_library.json"], layout_mapping: "layout/layout_primitive_mapping.json", viewer: "viewer/reference_library.html" }, null, 2)}\n`, "utf8");
await fs.mkdir(path.join(libraryRoot, "viewer"), { recursive: true });
await fs.writeFile(path.join(libraryRoot, "viewer", "reference_library.html"), htmlPayload(references, story, gallery, aplus, layout), "utf8");
console.log(JSON.stringify({ status: "complete", references: references.length, gallery_items: references.reduce((sum, reference) => sum + reference.gallery_patterns.length, 0), aplus_modules: references.reduce((sum, reference) => sum + reference.aplus_patterns.length, 0), layout_mappings: layout.mappings.length, viewer: path.join(libraryRoot, "viewer", "reference_library.html") }, null, 2));
