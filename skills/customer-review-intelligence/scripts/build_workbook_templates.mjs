import fs from "node:fs/promises";
import path from "node:path";
import { SpreadsheetFile, Workbook } from "@oai/artifact-tool";

const skillDir = path.resolve(path.dirname(new URL(import.meta.url).pathname), "..");
const workspace = globalThis.CRI_WORKSPACE || process.argv?.[2];
const productKnowledgeDir = globalThis.CRI_PRODUCT_KNOWLEDGE_DIR || process.argv?.[3];
const outputSkillDir = globalThis.CRI_OUTPUT_SKILL_DIR || process.argv?.[4] || skillDir;
const productEntityOutputPath = globalThis.CRI_PRODUCT_ENTITY_OUTPUT_PATH || process.argv?.[5] || path.join(productKnowledgeDir, "references", "product_entities.xlsx");
if (!workspace || !productKnowledgeDir) {
  throw new Error("Usage: node build_workbook_templates.mjs <workspace> <product-knowledge-dir>");
}

const previewRoot = path.join(workspace, "outputs", "template-previews");
await fs.mkdir(previewRoot, { recursive: true });

const colors = {
  brand: "#E53935",
  navy: "#172033",
  light: "#F4F6F9",
  line: "#DCE2EA",
  white: "#FFFFFF",
  input: "#FFF8D8",
};

function columnName(index) {
  let value = index + 1;
  let result = "";
  while (value) {
    value -= 1;
    result = String.fromCharCode(65 + (value % 26)) + result;
    value = Math.floor(value / 26);
  }
  return result;
}

function styleSheet(sheet, headers, rowCount = 200) {
  const end = columnName(headers.length - 1);
  sheet.showGridLines = false;
  sheet.freezePanes.freezeRows(1);
  const header = sheet.getRange(`A1:${end}1`);
  header.format = {
    fill: colors.navy,
    font: { bold: true, color: colors.white },
    wrapText: true,
    verticalAlignment: "center",
    borders: { preset: "outside", style: "thin", color: colors.line },
  };
  header.format.rowHeight = 34;
  const body = sheet.getRange(`A2:${end}${rowCount}`);
  body.format = {
    verticalAlignment: "top",
    borders: { preset: "inside", style: "thin", color: "#EEF1F5" },
  };
  sheet.getRange(`A1:${end}${Math.max(2, rowCount)}`).format.autofitColumns();
  for (let col = 0; col < headers.length; col += 1) {
    const key = headers[col];
    const width = /requirement|purpose|limitations/i.test(key) ? 38 : /body|notes|basis|url|path|expression|evidence/i.test(key) ? 28 : /date|_at/i.test(key) ? 14 : 16;
    sheet.getRange(`${columnName(col)}:${columnName(col)}`).format.columnWidth = width;
  }
}

async function saveAndRender(workbook, outputPath) {
  const fileName = path.basename(outputPath, ".xlsx");
  const previewDir = path.join(previewRoot, fileName);
  await fs.mkdir(previewDir, { recursive: true });
  for (const sheet of workbook.worksheets.items) {
    const preview = await workbook.render({ sheetName: sheet.name, autoCrop: "all", scale: 1, format: "png" });
    await fs.writeFile(path.join(previewDir, `${sheet.name.replaceAll("/", "-")}.png`), new Uint8Array(await preview.arrayBuffer()));
  }
  const exported = await SpreadsheetFile.exportXlsx(workbook);
  await exported.save(outputPath);
}

function createTableWorkbook(sheetName, headers, rows, tableName) {
  const workbook = Workbook.create();
  const sheet = workbook.worksheets.add(sheetName);
  const matrix = [headers, ...(rows.length ? rows : [headers.map(() => null)])];
  sheet.getRangeByIndexes(0, 0, matrix.length, headers.length).values = matrix;
  styleSheet(sheet, headers, Math.max(50, matrix.length));
  const end = columnName(headers.length - 1);
  const table = sheet.tables.add(`A1:${end}${matrix.length}`, true, tableName);
  table.style = "TableStyleMedium2";
  table.showFilterButton = true;
  return { workbook, sheet };
}

const reviewHeaders = [
  "review_id", "version_id", "batch_id", "source", "source_review_id", "source_id",
  "record_type", "relationship_type", "voc_eligibility", "product_id", "variant_id",
  "bundle_id", "asin", "sku", "jan", "model_number", "mapping_status", "mapping_basis",
  "channel_product_name", "channel_product_url", "source_url", "review_url", "rating", "review_title",
  "review_body", "review_date", "collected_at", "reviewer_display_name",
  "verified_purchase", "helpful_votes", "variant_text", "language", "review_status",
  "coverage_status", "original_review_hash", "duplicate_type", "duplicate_group_id",
  "canonical_review_id", "raw_file_path", "last_checked_at", "sentiment",
  "sentiment_score", "primary_topic", "secondary_topics", "issue_category",
  "issue_subcategory", "purchase_motivation", "usage_scenario", "praised_feature",
  "complained_feature", "expectation_gap", "severity", "return_intent",
  "support_contacted", "firmware_related", "installation_related", "app_related",
  "hardware_related", "logistics_related", "analysis_confidence",
  "classification_basis", "manual_review_required", "responsibility_owner", "notes",
];

{
  const workbook = Workbook.create();
  const instructions = workbook.worksheets.add("Instructions");
  instructions.getRange("A1:F1").merge();
  instructions.getRange("A1").values = [["Customer Review Intelligence Database"]];
  instructions.getRange("A1:F1").format = { fill: colors.brand, font: { bold: true, color: colors.white, size: 16 } };
  instructions.getRange("A3:B9").values = [
    ["Rule", "Requirement"],
    ["Source preservation", "Never overwrite raw evidence or prior versions."],
    ["Product mapping", "Only Confirmed mappings enter formal product totals."],
    ["Missing data", "Keep Blocked, Partial, Zero Confirmed, and Not Configured distinct."],
    ["Reviewer identity", "Do not expose reviewer names in analytical reports."],
    ["Deletion", "Only after a complete successful recheck of the same scope."],
    ["Natural VOC", "Exclude paid, owned, PR, and syndicated content."],
  ];
  styleSheet(instructions, ["Rule", "Requirement"], 9);
  instructions.getRange("B:B").format.columnWidth = 68;
  instructions.getRange("A3:B9").format.wrapText = true;
  for (const name of ["Reviews", "Versions"]) {
    const sheet = workbook.worksheets.add(name);
    sheet.getRangeByIndexes(0, 0, 2, reviewHeaders.length).values = [reviewHeaders, reviewHeaders.map(() => null)];
    styleSheet(sheet, reviewHeaders, 200);
    const table = sheet.tables.add(`A1:${columnName(reviewHeaders.length - 1)}2`, true, `${name}Table`);
    table.style = "TableStyleMedium2";
  }
  const dictionary = workbook.worksheets.add("Field Dictionary");
  dictionary.getRange("A1:C2").values = [
    ["Field", "Purpose", "Required"],
    ["review_id", "Stable review identity; platform ID preferred.", "Yes"],
  ];
  for (const field of reviewHeaders.slice(1)) {
    dictionary.tables.items.length;
    dictionary.getRangeByIndexes(dictionary.getUsedRange().rowCount, 0, 1, 3).values = [[field, "See skill data contract.", "Conditional"]];
  }
  styleSheet(dictionary, ["Field", "Purpose", "Required"], reviewHeaders.length + 2);
  dictionary.getRange("B:B").format.columnWidth = 38;
  dictionary.getRange("C:C").format.columnWidth = 14;
  await fs.mkdir(path.join(outputSkillDir, "references"), { recursive: true });
  await saveAndRender(workbook, path.join(outputSkillDir, "references", "review_database.xlsx"));
}

{
  const workbook = Workbook.create();
  const sheets = [
    ["Overview", ["metric", "value", "definition"], []],
    ["Positive Drivers", ["rank", "driver", "review_count", "share", "representative_expression", "source_urls"], []],
    ["Negative Drivers", ["rank", "issue", "review_count", "share", "severity", "trend", "source_urls"], []],
    ["Channel Comparison", ["metric", "amazon", "rakuten", "yahoo", "official_store", "comparability_note"], []],
    ["Trend", ["period_start", "period_end", "product_id", "topic", "review_count", "negative_count", "coverage_status", "note"], []],
  ];
  for (const [name, headers, rows] of sheets) {
    const sheet = workbook.worksheets.add(name);
    sheet.getRangeByIndexes(0, 0, 2, headers.length).values = [headers, headers.map(() => null)];
    styleSheet(sheet, headers, 50);
    const table = sheet.tables.add(`A1:${columnName(headers.length - 1)}2`, true, `${name.replaceAll(" ", "")}Table`);
    table.style = "TableStyleMedium2";
  }
  await saveAndRender(workbook, path.join(outputSkillDir, "references", "product_review_summary.xlsx"));
}

const taxonomyRows = [
  ["Product Quality", "故障・初期不良", "Negative", "Quality Assurance"],
  ["Installation", "設置・取付", "Mixed", "Product"],
  ["Setup", "初期設定", "Mixed", "Product"],
  ["App", "アプリ体験", "Mixed", "App"],
  ["Connectivity", "接続・オフライン", "Negative", "Firmware"],
  ["Automation", "自動化", "Mixed", "Product"],
  ["Compatibility", "互換性・対応範囲", "Mixed", "Product"],
  ["Performance", "速度・認識・精度", "Mixed", "Product"],
  ["Reliability", "安定性・再発", "Negative", "Quality Assurance"],
  ["Battery", "電池・充電", "Mixed", "Hardware"],
  ["Noise", "騒音", "Mixed", "Hardware"],
  ["Design", "外観・質感", "Mixed", "Product"],
  ["Size", "寸法・設置空間", "Mixed", "Product"],
  ["Ease of Use", "使いやすさ", "Mixed", "Product"],
  ["Security", "施錠・解錠・防犯", "Negative", "Product"],
  ["Privacy", "個人情報・録画", "Negative", "Product"],
  ["AI Function", "AI認識・要約", "Mixed", "Product"],
  ["Firmware", "更新・不具合", "Mixed", "Firmware"],
  ["Customer Support", "問い合わせ対応", "Mixed", "Customer Support"],
  ["Delivery", "配送", "Mixed", "Logistics"],
  ["Packaging", "梱包", "Mixed", "Logistics"],
  ["Price", "価格", "Mixed", "EC"],
  ["Value for Money", "コストパフォーマンス", "Positive", "Marketing"],
  ["Instructions", "説明書・FAQ", "Mixed", "Marketing"],
  ["Accessories", "付属品・別売", "Mixed", "Product"],
  ["Subscription", "月額・課金", "Mixed", "Product"],
  ["Return / Refund", "返品・返金", "Negative", "Customer Support"],
  ["Expectation Gap", "期待との差", "Negative", "Marketing"],
  ["Positive Experience", "満足・生活改善", "Positive", "Marketing"],
  ["Other", "未分類", "Neutral", "Product"],
];
{
  const { workbook, sheet } = createTableWorkbook("Taxonomy", ["primary_topic", "example_subcategory", "typical_sentiment", "default_owner"], taxonomyRows, "TaxonomyTable");
  sheet.getRange(`A2:D${taxonomyRows.length + 1}`).format.wrapText = true;
  await saveAndRender(workbook, path.join(outputSkillDir, "references", "issue_taxonomy.xlsx"));
}

const keywordRows = [
  ["接続できない", "Connectivity", "Negative", "接続不可", "All"],
  ["反応が遅い", "Performance", "Negative", "反応速度", "All"],
  ["設定が難しい", "Setup", "Negative", "設定障壁", "All"],
  ["便利", "Positive Experience", "Positive", "利便性", "All"],
  ["買ってよかった", "Positive Experience", "Positive", "購入満足", "All"],
  ["期待外れ", "Expectation Gap", "Negative", "期待差", "All"],
  ["すぐ壊れた", "Product Quality", "Negative", "短期故障", "All"],
  ["コスパが良い", "Value for Money", "Positive", "価格価値", "All"],
  ["説明書がわかりにくい", "Instructions", "Negative", "説明不足", "All"],
  ["アプリが使いにくい", "App", "Negative", "アプリUX", "All"],
];
{
  const { workbook } = createTableWorkbook("Keywords", ["keyword", "normalized_topic", "sentiment_hint", "context", "product_category"], keywordRows, "KeywordTable");
  await saveAndRender(workbook, path.join(outputSkillDir, "references", "keyword_dictionary.xlsx"));
}

const sourceRows = [
  ["amazon_jp", "Amazon Japan", "EC", "amazon.co.jp", "public_http_or_browser", "Enabled", "Review pages may require login or block automation."],
  ["rakuten", "楽天市場", "EC", "review.rakuten.co.jp", "public_http_or_browser", "Enabled", "Paginate until time window ends."],
  ["yahoo_shopping", "Yahoo!ショッピング", "EC", "shopping.yahoo.co.jp", "public_http_or_browser", "Enabled", "Verify more/pagination controls."],
  ["switchbot_official", "SwitchBot 日本公式サイト", "EC", "switchbot.jp", "public_http_or_browser", "Enabled", "Review widget pagination required."],
  ["kakaku", "価格.com", "Competitor", "kakaku.com", "public_http_or_browser", "Disabled", "Enable per project."],
  ["youtube", "YouTube", "KOL", "youtube.com", "browser_or_user_export", "Disabled", "Video metrics are not product VOC."],
  ["x", "X", "SNS", "x.com", "browser_or_user_export", "Disabled", "Exclude PR, official, giveaway, and repost noise."],
  ["blog", "Blog / Media", "PR", "", "public_http_or_user_links", "Disabled", "Separate placement, review, and syndication."],
];
{
  const { workbook, sheet } = createTableWorkbook("Sources", ["source_id", "source_name", "module", "domain", "collection_method", "status", "limitations"], sourceRows, "SourceTable");
  sheet.getRange("E:E").format.columnWidth = 26;
  sheet.getRange("G:G").format.columnWidth = 46;
  sheet.getRange(`A2:G${sourceRows.length + 1}`).format.wrapText = true;
  await saveAndRender(workbook, path.join(outputSkillDir, "references", "source_registry.xlsx"));
}

const productIndex = JSON.parse(await fs.readFile(path.join(productKnowledgeDir, "outputs", "product_index.json"), "utf8"));
const sourceIds = {
  hub_3: "SRC-004", lock_ultra: "SRC-002", keypad_vision_pro: "SRC-003",
  ai_mindclip: "SRC-005", video_doorbell: "SRC-006", battery_circulator_fan: "SRC-000",
  circulator_fan_2_pro: "SRC-007", curtain_3: "SRC-008", k10_pro_combo: "SRC-009",
  k11_plus: "SRC-001", s10: "SRC-018", s20: "SRC-001", daily_station: "SRC-017",
  weather_station: "SRC-016", ai_art_canvas: "SRC-000", relay_switch_1: "SRC-015",
  kata_friends: "SRC-011", homerunpet_series: "SRC-013",
};
const entityHeaders = [
  "entity_id", "product_id", "entity_type", "variant_id", "bundle_id",
  "official_name", "asin", "sku", "jan", "model_number", "market",
  "valid_from", "valid_to", "source_id", "review_status", "last_verified_date", "notes",
];
const entityRows = productIndex.products.map((product) => [
  `product:${product.product_id}`, product.product_id, "product", "", "",
  product.official_name?.en || product.product_id, "", "", "", product.model_number || "",
  product.market || "JP", "", "", sourceIds[product.product_id] || "SRC-000",
  "pending_verification", product.last_verified_date || "2026-07-30",
  "Product-level entity only. Add variant or bundle rows only with verified identifiers.",
]);
entityRows.push(
  ["variant:lock-ultra:black-jp", "lock_ultra", "variant", "lock_ultra_black_jp", "", "SwitchBot Lock Ultra Black (JP)", "", "810150543469JP", "0810150543469", "W5600004", "JP", "2025-04-25", "", "SRC-002", "verified", "2026-07-31", "Verified from SwitchBot Japan public product JSON and Japanese retail listings."],
  ["variant:lock-ultra:silver-jp", "lock_ultra", "variant", "lock_ultra_silver_jp", "", "SwitchBot Lock Ultra Silver (JP)", "", "810150543513JP", "0810150543513", "W5600000-S", "JP", "2025-04-29", "", "SRC-002", "verified", "2026-07-31", "Verified from SwitchBot Japan public product JSON and Japanese retail listings."],
  ["variant:hub-3:jp", "hub_3", "variant", "hub_3_jp", "", "SwitchBot Hub 3 (JP)", "", "", "0810150543353", "W7202101", "JP", "2025-05-01", "", "SRC-004", "verified", "2026-07-31", "Verified from Rakuten public product metadata and Japanese retail listings."],
);
{
  const { workbook, sheet } = createTableWorkbook("Data", entityHeaders, entityRows, "ProductEntitiesTable");
  sheet.getRange(`G2:J${entityRows.length + 1}`).format.numberFormat = "@";
  sheet.getRangeByIndexes(1, 6, entityRows.length, 4).values = entityRows.map((row) => row.slice(6, 10));
  sheet.getRange("C2:C200").dataValidation = { rule: { type: "list", values: ["product", "variant", "bundle"] } };
  sheet.getRange("O2:O200").dataValidation = { rule: { type: "list", values: ["draft", "pending_verification", "verified", "approved", "rejected", "expired", "conflict"] } };
  sheet.getRange("Q:Q").format.columnWidth = 52;
  await saveAndRender(workbook, productEntityOutputPath);
}

console.log(JSON.stringify({ ok: true, previewRoot }, null, 2));
