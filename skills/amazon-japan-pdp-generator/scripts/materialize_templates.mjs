#!/usr/bin/env node
import fs from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";

const skillDir = path.dirname(path.dirname(fileURLToPath(import.meta.url)));
const registry = JSON.parse(await fs.readFile(path.join(skillDir, "templates", "template_library.json"), "utf8"));
const { default: sharp } = await import("sharp");

function slug(id) {
  return id.toLowerCase().replace(/^p-/, "product-").replace(/^a-/, "aplus-").replaceAll("-", "_");
}

function dimensions(template) {
  const parts = String(template.svg.view_box).split(/\s+/).map(Number);
  return { width: parts[2] || 1464, height: parts[3] || 620 };
}

function svg(template) {
  const { width, height } = dimensions(template);
  const product = template.product_area ? `<rect x="${Math.round(width * .53)}" y="${Math.round(height * .18)}" width="${Math.round(width * .39)}" height="${Math.round(height * .64)}" rx="${Math.round(width * .02)}" fill="#DDF3ED"/><text x="${Math.round(width * .725)}" y="${Math.round(height * .51)}" text-anchor="middle" font-family="Arial" font-size="${Math.round(width * .025)}" font-weight="700" fill="#34665C">PRODUCT / SCENE</text>` : "";
  const text = template.text_area !== null ? `<rect x="${Math.round(width * .06)}" y="${Math.round(height * .22)}" width="${Math.round(width * .4)}" height="${Math.round(height * .48)}" rx="${Math.round(width * .018)}" fill="#FFFFFF"/><text x="${Math.round(width * .09)}" y="${Math.round(height * .38)}" font-family="Arial" font-size="${Math.round(width * .03)}" font-weight="700" fill="#17212B">${template.name}</text><text x="${Math.round(width * .09)}" y="${Math.round(height * .49)}" font-family="Arial" font-size="${Math.round(width * .016)}" fill="#607078">PROGRAMMATIC TEXT AREA</text>` : "";
  return `<svg xmlns="http://www.w3.org/2000/svg" width="${width}" height="${height}" viewBox="0 0 ${width} ${height}"><rect width="${width}" height="${height}" fill="#F7FAFA"/><rect x="${Math.round(width * .035)}" y="${Math.round(height * .07)}" width="${Math.round(width * .93)}" height="${Math.round(height * .86)}" rx="${Math.round(width * .018)}" fill="none" stroke="#23A98F" stroke-width="4" stroke-dasharray="14 10"/>${text}${product}<text x="${Math.round(width * .05)}" y="${Math.round(height * .94)}" font-family="Arial" font-size="${Math.round(width * .013)}" fill="#087A66">${template.template_id} · SAFE AREA · 390PX RULE</text></svg>`;
}

let count = 0;
for (const template of registry.templates) {
  const dir = path.join(skillDir, "templates", "amazon", slug(template.template_id));
  await fs.mkdir(dir, { recursive: true });
  const markup = svg(template);
  const css = `:root{--accent:#23A98F;--ink:#17212B;--canvas:#F7FAFA}*{box-sizing:border-box}.template{display:grid;min-height:100%;background:var(--canvas);font-family:"Hiragino Sans","Noto Sans JP",sans-serif}.graphic-layer{position:relative}.product-layer,.scene-layer{object-fit:contain}.consumer-copy{color:var(--ink)}@media(max-width:390px){.template{grid-template-columns:1fr}.consumer-copy{font-size:max(16px,4.1vw)}}\n`;
  const html = `<!doctype html><html lang="ja"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><link rel="stylesheet" href="template.css"><title>${template.name}</title></head><body><main class="template ${template.html.class}"><section class="graphic-layer"><div class="consumer-copy">{{headline}}<br>{{sub_copy}}</div><img class="scene-layer" src="{{scene_layer}}" alt=""><img class="product-layer" src="{{official_product_layer}}" alt=""></section></main></body></html>\n`;
  const readme = `# ${template.name}\n\n- Template ID: \`${template.template_id}\`\n- Family: \`${template.family}\`\n- Grid: \`${JSON.stringify(template.grid)}\`\n- Product area: \`${JSON.stringify(template.product_area)}\`\n- Text area: \`${JSON.stringify(template.text_area)}\`\n- Safe area: \`${JSON.stringify(template.safe_area)}\`\n- Font size: \`${JSON.stringify(template.font_size)}\`\n- Headline length: \`${JSON.stringify(template.headline_length)}\`\n- Sub copy length: \`${JSON.stringify(template.sub_copy_length)}\`\n- Desktop: ${template.desktop_rules.join("; ")}\n- Mobile: ${template.mobile_rules.join("; ")}\n- Historical reference: ${template.historical_reference.join(", ")}\n\nProduct Layer must use a user-provided official product asset. AI/stock may only supply a product-free Scene Layer. Japanese copy, UI, tables and diagram text stay in the programmatic Graphic Layer.\n`;
  await fs.writeFile(path.join(dir, "template.json"), `${JSON.stringify({ ...template, library_version: registry.library_version, source_policy: registry.source_policy }, null, 2)}\n`, "utf8");
  await fs.writeFile(path.join(dir, "template.html"), html, "utf8");
  await fs.writeFile(path.join(dir, "template.css"), css, "utf8");
  await fs.writeFile(path.join(dir, "template.svg"), markup, "utf8");
  await fs.writeFile(path.join(dir, "README.md"), readme, "utf8");
  await sharp(Buffer.from(markup)).resize({ width: 1000 }).jpeg({ quality: 90 }).toFile(path.join(dir, "preview.jpg"));
  count += 1;
}

console.log(JSON.stringify({ materialized_templates: count, root: "templates/amazon" }, null, 2));
