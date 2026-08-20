import fs from "node:fs/promises";
import path from "node:path";
import { SpreadsheetFile, Workbook } from "@oai/artifact-tool";

const workspace = path.resolve(process.argv[2]);
const output = path.resolve(process.argv[3] || path.join(workspace, "outputs", "cleaned_data.xlsx"));
const previewRoot = path.join(workspace, "outputs", "workbook-previews");
await fs.mkdir(previewRoot, { recursive: true });

function parseCsv(text) {
  const rows = []; let row = [], cell = "", quoted = false;
  for (let i = 0; i < text.length; i++) {
    const c = text[i];
    if (quoted) {
      if (c === '"' && text[i + 1] === '"') { cell += '"'; i++; }
      else if (c === '"') quoted = false; else cell += c;
    } else if (c === '"') quoted = true;
    else if (c === ',') { row.push(cell); cell = ""; }
    else if (c === '\n') { row.push(cell.replace(/\r$/, "")); rows.push(row); row = []; cell = ""; }
    else cell += c;
  }
  if (cell || row.length) { row.push(cell); rows.push(row); }
  if (rows[0]?.[0]?.charCodeAt(0) === 0xFEFF) rows[0][0] = rows[0][0].slice(1);
  return rows.filter(r => r.some(v => v !== ""));
}

function colName(n) { let s = ""; for (n++; n; n = Math.floor((n - 1) / 26)) s = String.fromCharCode(65 + ((n - 1) % 26)) + s; return s; }
function addSheet(wb, name, matrix) {
  const sheet = wb.worksheets.add(name); const cols = Math.max(...matrix.map(r => r.length));
  const padded = matrix.map(r => [...r, ...Array(cols - r.length).fill("")]);
  sheet.getRangeByIndexes(0, 0, padded.length, cols).values = padded;
  sheet.showGridLines = false; sheet.freezePanes.freezeRows(1);
  sheet.getRangeByIndexes(0, 0, 1, cols).format = { fill: "#172033", font: { bold: true, color: "#FFFFFF" }, wrapText: true };
  sheet.getRangeByIndexes(0, 0, padded.length, cols).format.autofitColumns();
  for (let c = 0; c < cols; c++) {
    const h = String(padded[0][c] || "");
    const width = /review_body|evidence|data_gap|coverage_note|success_metric|action|problem/i.test(h) ? 34 : /url|notes|title|motivation|scenario|expectation/i.test(h) ? 26 : 16;
    sheet.getRange(`${colName(c)}:${colName(c)}`).format.columnWidth = width;
  }
  if (padded.length > 1) { const table = sheet.tables.add(`A1:${colName(cols - 1)}${padded.length}`, true, `${name.replace(/[^A-Za-z0-9]/g, "")}Table`); table.style = "TableStyleMedium2"; table.showFilterButton = true; }
  return sheet;
}

const wb = Workbook.create();
for (const [name, relative] of [
  ["Product Summary", "outputs/product_summary.csv"], ["Unified Channels", "outputs/unified_channel_statistics.csv"], ["Channel Comparison", "outputs/channel_comparison.csv"],
  ["Trend", "outputs/trend_analysis.csv"], ["Risk Queue", "outputs/risk_queue.csv"], ["Action Plan", "outputs/action_plan.csv"],
]) {
  let matrix = parseCsv(await fs.readFile(path.join(workspace, relative), "utf8"));
  if (name === "Risk Queue") {
    const fields = ["review_id","source","variant_id","rating","review_date","sentiment","primary_topic","severity","review_title","review_body","expectation_gap","return_intent","installation_related","app_related","hardware_related","responsibility_owner","review_url"];
    const positions = new Map(matrix[0].map((h,i)=>[h,i]));
    matrix = [fields, ...matrix.slice(1).map(r => fields.map(h => r[positions.get(h)] ?? ""))];
  }
  addSheet(wb, name, matrix);
}

const reviews = parseCsv(await fs.readFile(path.join(workspace, "normalized/reviews.csv"), "utf8"));
const keep = ["review_id","source","record_type","relationship_type","voc_eligibility","product_id","variant_id","bundle_id","asin","sku","jan","mapping_status","review_url","rating","review_title","review_body","review_date","verified_purchase","variant_text","review_status","coverage_status","duplicate_type","sentiment","primary_topic","secondary_topics","purchase_motivation","usage_scenario","expectation_gap","severity","return_intent","installation_related","app_related","hardware_related","analysis_confidence","manual_review_required","responsibility_owner","notes"];
const pos = new Map(reviews[0].map((h,i)=>[h,i]));
addSheet(wb, "Reviews", [keep, ...reviews.slice(1).map(r => keep.map(h => r[pos.get(h)] ?? ""))]);

for (const sheet of wb.worksheets.items) {
  const img = await wb.render({ sheetName: sheet.name, range: sheet.name === "Reviews" ? "A1:K30" : undefined, autoCrop: "all", scale: 0.8, format: "png" });
  await fs.writeFile(path.join(previewRoot, `${sheet.name.replaceAll("/", "-")}.png`), new Uint8Array(await img.arrayBuffer()));
}
const errors = await wb.inspect({ kind: "match", searchTerm: "#REF!|#DIV/0!|#VALUE!|#NAME\\?|#N/A", options: { useRegex: true, maxResults: 100 }, summary: "formula errors" });
await fs.writeFile(path.join(previewRoot, "formula-errors.json"), JSON.stringify(errors, null, 2));
const exported = await SpreadsheetFile.exportXlsx(wb); await exported.save(output);
console.log(JSON.stringify({ output, sheets: wb.worksheets.items.map(s => s.name) }));
