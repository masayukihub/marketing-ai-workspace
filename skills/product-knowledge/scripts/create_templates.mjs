import fs from "node:fs/promises";
import path from "node:path";

let SpreadsheetFile;
let Workbook;

const skillDir = path.resolve(process.argv[2] || ".");
const referenceDir = path.join(skillDir, "references");
const previewDir = process.argv[3] ? path.resolve(process.argv[3]) : null;

const isoDateColumns = new Set([
  "launch_date_jp", "last_verified_date", "valid_from", "valid_to",
  "start_date", "end_date", "collected_date", "planned_date",
  "actual_date", "discontinued_date",
]);

const enums = {
  market: ["JP", "Global", "US", "EU", "Unknown"],
  status: ["planned", "active", "discontinued", "unknown"],
  release_status: ["released", "beta", "announced", "firmware_required", "region_limited", "unsupported", "unknown"],
  review_status: ["draft", "pending_verification", "verified", "approved", "rejected", "expired", "conflict"],
  price_type: ["MSRP", "Regular Price", "Sale Price", "Launch Price", "Bundle Price", "Coupon Price", "Historical Price"],
  currency: ["JPY", "USD", "EUR", "CNY", "Unknown"],
  relationship_type: ["works_with", "requires", "optional", "incompatible", "controls", "bridges", "replaces", "bundle_with"],
  support_status: ["released", "beta", "announced", "firmware_required", "region_limited", "unsupported", "unknown"],
  alias_type: ["official", "short_name", "former_name", "internal_name", "model_name", "typo", "competitor_confusion"],
  usage_status: ["current", "historical", "avoid", "ambiguous"],
  threat_level: ["Low", "Medium", "High", "Critical", "Unverified"],
  tax_included: ["yes", "no", "unknown"],
  completeness: ["skeleton", "partial", "verified"],
};

const products = [
  ["hub_3", "SwitchBot Hub 3", "", "", "Hub 3", "Hub", "", "", "", "JP", "unknown", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "SRC-004", "2026-07-30", "", "Status, official JP name, and model need product-owner verification."],
  ["lock_ultra", "SwitchBot Lock Ultra", "", "", "Lock Ultra", "Lock", "", "", "", "JP", "unknown", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "SRC-002", "2026-07-30", "", "Do not attribute Keypad Vision Pro biometric functions to the lock body."],
  ["keypad_vision_pro", "SwitchBot Keypad Vision Pro", "", "", "Keypad Vision Pro", "Keypad", "", "", "", "JP", "unknown", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "SRC-003", "2026-07-30", "", "Current official naming requires confirmation; Keypad Vision is retained as an ambiguous/former alias."],
  ["ai_mindclip", "SwitchBot AI MindClip", "", "", "AI MindClip", "AI", "", "", "", "JP", "unknown", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "SRC-005", "2026-07-30", "", "Recording, privacy, subscription, OpenAPI, and release status require approval."],
  ["video_doorbell", "SwitchBot Video Doorbell", "", "", "Video Doorbell", "Security", "", "", "", "JP", "unknown", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "SRC-006", "2026-07-30", "", "Exact official JP name requires confirmation."],
  ["battery_circulator_fan", "SwitchBot Battery Circulator Fan", "", "", "Battery Circulator Fan", "Comfort", "", "", "", "JP", "unknown", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "SRC-000", "2026-07-30", "", "Structure created from requested scope; source content pending."],
  ["circulator_fan_2_pro", "SwitchBot Circulator Fan 2 Pro", "", "", "Circulator Fan 2 Pro", "Comfort", "", "", "", "JP", "unknown", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "SRC-007", "2026-07-30", "", "Exact official English and JP names require confirmation."],
  ["curtain_3", "SwitchBot Curtain 3", "", "", "Curtain 3", "Curtain", "", "", "", "JP", "unknown", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "SRC-008", "2026-07-30", "", "Rail compatibility conditions pending."],
  ["k10_pro_combo", "SwitchBot K10+ Pro Combo", "", "", "K10+ Pro Combo", "Robot Vacuum", "", "", "", "JP", "unknown", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "SRC-009", "2026-07-30", "", "Bundle capability ownership must remain explicit."],
  ["k11_plus", "SwitchBot K11+", "", "", "K11+", "Robot Vacuum", "", "", "", "JP", "unknown", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "SRC-001", "2026-07-30", "", "Do not merge with K11+ Pro."],
  ["s10", "SwitchBot S10", "", "", "S10", "Robot Vacuum", "", "", "", "JP", "unknown", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "SRC-018", "2026-07-30", "", "Historical source; current status pending."],
  ["s20", "SwitchBot S20", "", "", "S20", "Robot Vacuum", "", "", "", "JP", "unknown", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "SRC-001", "2026-07-30", "", "Do not merge S20, S20 Pro, and S20 Mini."],
  ["daily_station", "SwitchBot Daily Station", "", "", "Daily Station", "", "", "", "", "JP", "unknown", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "SRC-017", "2026-07-30", "", "Only draft product-story source registered."],
  ["weather_station", "SwitchBot Weather Station", "", "", "Weather Station", "", "", "", "", "JP", "unknown", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "SRC-016", "2026-07-30", "", "Specification sheet registered for later import."],
  ["ai_art_canvas", "SwitchBot AI Art Canvas", "", "", "AI Art Canvas", "AI Art", "", "", "", "JP", "unknown", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "SRC-000", "2026-07-30", "", "Potential naming conflict with AI Art Frame in SRC-010."],
  ["relay_switch_1", "SwitchBot Relay Switch 1", "", "", "Relay Switch 1", "Relay Switch", "", "", "", "JP", "unknown", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "SRC-015", "2026-07-30", "", "JP compliance and 1 versus 1PM distinction pending."],
  ["kata_friends", "SwitchBot KATA Friends", "", "", "KATA Friends", "KATA", "", "", "", "JP", "unknown", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "SRC-011", "2026-07-30", "", "AI scope, privacy, safety, language, and availability pending."],
  ["homerunpet_series", "homerunPET Series", "", "", "homerunPET", "Pet Smart Home", "", "", "", "JP", "unknown", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "SRC-013", "2026-07-30", "", "Umbrella entity; expand only from uniquely verified JP standard-name rows."],
];

const productHeaders = [
  "product_id", "official_name_en", "official_name_ja", "official_name_zh", "short_name",
  "product_series", "category", "subcategory", "model_number", "market", "status",
  "launch_date_jp", "one_sentence_positioning", "primary_target", "primary_use_case",
  "core_benefit", "key_feature_1", "key_feature_2", "key_feature_3", "differentiation",
  "ecosystem_role", "required_hub", "matter_support", "app_support", "voice_assistant",
  "source_id", "last_verified_date", "data_owner", "notes",
];

const configs = [
  {
    file: "product_master.xlsx",
    headers: productHeaders,
    rows: products,
    required: ["product_id", "official_name_en", "market", "status", "source_id", "last_verified_date"],
    descriptions: {
      product_id: "Stable lowercase identifier.", official_name_en: "Formal English name.",
      market: "Applicable market.", status: "Lifecycle state; use unknown rather than guessing.",
      source_id: "Source Registry reference.", last_verified_date: "Date the row was last checked.",
      notes: "Limitations, naming conflicts, and review needs.",
    },
  },
  {
    file: "product_specs.xlsx",
    headers: ["product_id", "spec_category", "spec_name", "spec_value", "unit", "conditions", "market", "firmware_version", "source_id", "source_revision_id", "review_status", "last_verified_date", "notes"],
    rows: [
      ["lock_ultra", "acoustic", "night_mode_noise", 20, "dB", "Night mode; test method, distance, environment, and tolerance pending.", "JP", "", "SRC-001", "1188", "pending_verification", "2026-07-30", "Do not publish until conditions are approved."],
      ["lock_ultra", "power", "main_battery_life", 12, "months", "Internal source statement; usage frequency, temperature, lock type, and test protocol pending.", "JP", "", "SRC-001", "1188", "pending_verification", "2026-07-30", "Not an approved external claim."],
      ["hub_3", "matter", "bridge_device_quantity", 30, "devices", "Internal source statement; supported device categories, platform, firmware, and region pending.", "JP", "", "SRC-001", "1188", "pending_verification", "2026-07-30", "Not an approved universal capacity claim."],
    ],
    required: ["product_id", "spec_category", "spec_name", "spec_value", "market", "source_id", "review_status", "last_verified_date"],
  },
  {
    file: "pricing.xlsx",
    headers: ["product_id", "channel", "market", "price_type", "regular_price", "sale_price", "currency", "discount_amount", "discount_rate", "campaign_name", "start_date", "end_date", "tax_included", "source_id", "source_revision_id", "review_status", "last_verified_date", "notes"],
    rows: [],
    required: ["product_id", "channel", "market", "price_type", "currency", "tax_included", "source_id", "review_status", "last_verified_date"],
    descriptions: { notes: "Initial release deliberately contains no current price assertions." },
  },
  {
    file: "competitor.xlsx",
    headers: ["our_product_id", "competitor_brand", "competitor_product", "competitor_model", "market", "category", "positioning", "regular_price", "currency", "key_features", "strengths", "weaknesses", "difference_vs_switchbot", "threat_level", "source_url", "source_id", "collected_date", "last_verified_date", "notes"],
    rows: [],
    required: ["our_product_id", "competitor_brand", "competitor_product", "market", "source_url", "source_id", "collected_date", "last_verified_date"],
  },
  {
    file: "product_positioning.xlsx",
    headers: ["product_id", "audience", "scenario", "communication_goal", "primary_message", "supporting_message", "proof_point", "recommended_expression_ja", "avoid_expression", "channel", "source_id", "review_status", "last_verified_date", "notes"],
    rows: [],
    required: ["product_id", "audience", "scenario", "channel", "source_id", "review_status", "last_verified_date"],
  },
  {
    file: "compatibility.xlsx",
    headers: ["source_product_id", "target_product_or_platform", "target_product_id", "relationship_type", "support_status", "requirements", "limitations", "firmware_requirement", "region", "source_id", "source_revision_id", "review_status", "last_verified_date", "notes"],
    rows: [
      ["lock_ultra", "SwitchBot Keypad Vision Pro", "keypad_vision_pro", "works_with", "unknown", "Compatible-lock confirmation required.", "Face recognition belongs to the keypad accessory.", "", "JP", "SRC-003", "2033", "pending_verification", "2026-07-30", ""],
      ["keypad_vision_pro", "SwitchBot Lock Ultra", "lock_ultra", "requires", "unknown", "Compatible lock required.", "Current JP naming and firmware require confirmation.", "", "JP", "SRC-003", "2033", "pending_verification", "2026-07-30", ""],
      ["hub_3", "Matter ecosystem", "", "bridges", "unknown", "Supported device categories, platform, and firmware required.", "Not universal compatibility.", "", "JP", "SRC-004", "5836", "pending_verification", "2026-07-30", ""],
    ],
    required: ["source_product_id", "target_product_or_platform", "relationship_type", "support_status", "region", "source_id", "review_status", "last_verified_date"],
  },
  {
    file: "product_aliases.xlsx",
    headers: ["alias", "product_id", "alias_type", "language", "valid_from", "valid_to", "usage_status", "source_id", "last_verified_date", "notes"],
    rows: [
      ["SwitchBot Hub 3", "hub_3", "official", "en", "", "", "current", "SRC-004", "2026-07-30", ""],
      ["Hub 3", "hub_3", "short_name", "en", "", "", "current", "SRC-000", "2026-07-30", ""],
      ["Hub3", "hub_3", "short_name", "en", "", "", "current", "SRC-000", "2026-07-30", ""],
      ["ハブ3", "hub_3", "short_name", "ja", "", "", "current", "SRC-000", "2026-07-30", ""],
      ["SwitchBot Lock Ultra", "lock_ultra", "official", "en", "", "", "current", "SRC-002", "2026-07-30", ""],
      ["Lock Ultra", "lock_ultra", "short_name", "en", "", "", "current", "SRC-000", "2026-07-30", ""],
      ["SwitchBot Keypad Vision Pro", "keypad_vision_pro", "official", "en", "", "", "current", "SRC-003", "2026-07-30", ""],
      ["Keypad Vision Pro", "keypad_vision_pro", "short_name", "en", "", "", "current", "SRC-000", "2026-07-30", ""],
      ["Keypad Vision", "keypad_vision_pro", "former_name", "en", "", "", "ambiguous", "SRC-001", "2026-07-30", "Confirm current official naming before external use."],
      ["SwitchBot AI MindClip", "ai_mindclip", "official", "en", "", "", "current", "SRC-005", "2026-07-30", ""],
      ["AI MindClip", "ai_mindclip", "short_name", "en", "", "", "current", "SRC-000", "2026-07-30", ""],
      ["MindClip", "ai_mindclip", "short_name", "en", "", "", "current", "SRC-000", "2026-07-30", ""],
      ["AI マインドクリップ", "ai_mindclip", "short_name", "ja", "", "", "current", "SRC-000", "2026-07-30", ""],
      ["SwitchBot Video Doorbell", "video_doorbell", "official", "en", "", "", "current", "SRC-000", "2026-07-30", ""],
      ["Video Doorbell", "video_doorbell", "short_name", "en", "", "", "current", "SRC-000", "2026-07-30", ""],
      ["SwitchBot Battery Circulator Fan", "battery_circulator_fan", "official", "en", "", "", "current", "SRC-000", "2026-07-30", ""],
      ["Battery Circulator Fan", "battery_circulator_fan", "short_name", "en", "", "", "current", "SRC-000", "2026-07-30", ""],
      ["SwitchBot Circulator Fan 2 Pro", "circulator_fan_2_pro", "official", "en", "", "", "current", "SRC-000", "2026-07-30", ""],
      ["Circulator Fan 2 Pro", "circulator_fan_2_pro", "short_name", "en", "", "", "current", "SRC-000", "2026-07-30", ""],
      ["SwitchBot Curtain 3", "curtain_3", "official", "en", "", "", "current", "SRC-008", "2026-07-30", ""],
      ["Curtain 3", "curtain_3", "short_name", "en", "", "", "current", "SRC-000", "2026-07-30", ""],
      ["SwitchBot K10+ Pro Combo", "k10_pro_combo", "official", "en", "", "", "current", "SRC-009", "2026-07-30", ""],
      ["K10+ Pro Combo", "k10_pro_combo", "short_name", "en", "", "", "current", "SRC-000", "2026-07-30", ""],
      ["SwitchBot K11+", "k11_plus", "official", "en", "", "", "current", "SRC-001", "2026-07-30", ""],
      ["K11+", "k11_plus", "short_name", "en", "", "", "current", "SRC-000", "2026-07-30", ""],
      ["SwitchBot S10", "s10", "official", "en", "", "", "current", "SRC-018", "2026-07-30", ""],
      ["S10", "s10", "short_name", "en", "", "", "current", "SRC-000", "2026-07-30", ""],
      ["SwitchBot S20", "s20", "official", "en", "", "", "current", "SRC-001", "2026-07-30", ""],
      ["S20", "s20", "short_name", "en", "", "", "current", "SRC-000", "2026-07-30", ""],
      ["SwitchBot Daily Station", "daily_station", "official", "en", "", "", "current", "SRC-000", "2026-07-30", ""],
      ["Daily Station", "daily_station", "short_name", "en", "", "", "current", "SRC-000", "2026-07-30", ""],
      ["SwitchBot Weather Station", "weather_station", "official", "en", "", "", "current", "SRC-000", "2026-07-30", ""],
      ["Weather Station", "weather_station", "short_name", "en", "", "", "current", "SRC-000", "2026-07-30", ""],
      ["SwitchBot AI Art Canvas", "ai_art_canvas", "official", "en", "", "", "current", "SRC-000", "2026-07-30", ""],
      ["AI Art Canvas", "ai_art_canvas", "short_name", "en", "", "", "current", "SRC-000", "2026-07-30", ""],
      ["AI Art Frame", "ai_art_canvas", "competitor_confusion", "en", "", "", "ambiguous", "SRC-010", "2026-07-30", "Do not silently treat Frame and Canvas as identical."],
      ["SwitchBot Relay Switch 1", "relay_switch_1", "official", "en", "", "", "current", "SRC-000", "2026-07-30", ""],
      ["Relay Switch 1", "relay_switch_1", "short_name", "en", "", "", "current", "SRC-000", "2026-07-30", ""],
      ["SwitchBot KATA Friends", "kata_friends", "official", "en", "", "", "current", "SRC-011", "2026-07-30", ""],
      ["KATA Friends", "kata_friends", "short_name", "en", "", "", "current", "SRC-000", "2026-07-30", ""],
      ["KATAフレンズ", "kata_friends", "short_name", "ja", "", "", "current", "SRC-000", "2026-07-30", ""],
      ["homerunPET", "homerunpet_series", "official", "en", "", "", "current", "SRC-013", "2026-07-30", "Series umbrella only."],
      ["homerunPET Series", "homerunpet_series", "short_name", "en", "", "", "current", "SRC-000", "2026-07-30", "Series umbrella only."],
    ],
    required: ["alias", "product_id", "alias_type", "language", "usage_status", "source_id", "last_verified_date"],
  },
  {
    file: "launch_calendar.xlsx",
    headers: ["product_id", "market", "launch_stage", "planned_date", "actual_date", "channel", "source_id", "review_status", "last_verified_date", "notes"],
    rows: products.map((row) => [row[0], "JP", "unknown", "", "", "", row[25], "pending_verification", "2026-07-30", "No launch-date assertion in initial release."]),
    required: ["product_id", "market", "launch_stage", "source_id", "review_status", "last_verified_date"],
  },
  {
    file: "discontinued_products.xlsx",
    headers: ["product_id", "market", "discontinued_date", "replacement_product_id", "source_id", "review_status", "last_verified_date", "notes"],
    rows: [],
    required: ["product_id", "market", "discontinued_date", "source_id", "review_status", "last_verified_date"],
  },
  {
    file: "product_facts.xlsx",
    headers: ["fact_id", "subject_product_id", "capability_owner_product_id", "required_product_id", "fact_type", "fact_name", "fact_value", "unit", "conditions", "release_status", "market", "firmware_requirement", "valid_from", "valid_to", "source_id", "source_revision_id", "review_status", "last_verified_date", "data_owner", "notes"],
    rows: [
      ["FCT-001", "hub_3", "hub_3", "", "feature", "infrared_device_control", "Controls supported infrared appliances", "", "Supported appliance types and code library require current confirmation.", "unknown", "JP", "", "", "", "SRC-004", "5836", "pending_verification", "2026-07-30", "", ""],
      ["FCT-002", "hub_3", "hub_3", "", "feature", "matter_bridge", "Bridges supported SwitchBot and infrared devices to supported Matter ecosystems", "", "Supported categories, quantity, platform, firmware, and region require confirmation.", "unknown", "JP", "", "", "", "SRC-004", "5836", "pending_verification", "2026-07-30", "", ""],
      ["FCT-003", "hub_3", "hub_3", "", "feature", "matter_device_control", "Controls supported Matter devices through physical controls", "", "Supported platform and device categories require confirmation.", "unknown", "JP", "", "", "", "SRC-004", "5836", "pending_verification", "2026-07-30", "", ""],
      ["FCT-004", "lock_ultra", "keypad_vision_pro", "keypad_vision_pro", "feature", "face_recognition_unlock", "Available through the compatible Keypad Vision Pro accessory", "", "Requires compatible lock, current JP naming, support status, and firmware confirmation.", "unknown", "JP", "", "", "", "SRC-003", "2033", "pending_verification", "2026-07-30", "", "Canonical attribution resolves the source-level bundle wording."],
      ["FCT-005", "lock_ultra", "lock_ultra", "", "design", "power_backup_design", "Three-stage power backup design described internally", "", "Battery composition, duration, temperature, use frequency, and emergency behavior require confirmation.", "unknown", "JP", "", "", "", "SRC-001", "1188", "pending_verification", "2026-07-30", "", ""],
      ["FCT-006", "keypad_vision_pro", "keypad_vision_pro", "lock_ultra", "feature", "three_dimensional_face_recognition", "3D face-recognition unlocking for compatible lock products", "", "Compatible models, environment, enrollment, speed, accuracy, and firmware require confirmation.", "unknown", "JP", "", "", "", "SRC-003", "2033", "pending_verification", "2026-07-30", "", ""],
    ],
    required: ["fact_id", "subject_product_id", "capability_owner_product_id", "fact_type", "fact_name", "fact_value", "release_status", "market", "source_id", "source_revision_id", "review_status", "last_verified_date"],
  },
];

if (process.argv.includes("--emit-json")) {
  console.log(JSON.stringify({ configs, enums, isoDateColumns: [...isoDateColumns] }));
  process.exit(0);
}

({ SpreadsheetFile, Workbook } = await import("@oai/artifact-tool"));

function typedRows(headers, rows) {
  return rows.map((row) => row.map((value, index) => {
    if (!value || !isoDateColumns.has(headers[index])) return value;
    if (value instanceof Date) return value;
    if (/^\d{4}-\d{2}-\d{2}$/.test(String(value))) return new Date(`${value}T00:00:00Z`);
    return value;
  }));
}

function makeDictionary(headers, required, descriptions = {}) {
  return headers.map((field) => [
    field,
    required.includes(field) ? "yes" : "no",
    enums[field] ? enums[field].join(" | ") : "",
    descriptions[field] || "",
  ]);
}

async function createWorkbook(config, index) {
  const workbook = Workbook.create();
  const dataSheet = workbook.worksheets.add("Data");
  const dictionarySheet = workbook.worksheets.add("Data Dictionary");
  const enumSheet = workbook.worksheets.add("Enums");
  dataSheet.showGridLines = false;
  dictionarySheet.showGridLines = false;
  enumSheet.showGridLines = false;

  const headers = config.headers;
  const dataRows = typedRows(headers, config.rows);
  dataSheet.getRangeByIndexes(0, 0, 1, headers.length).values = [headers];
  if (dataRows.length) {
    dataSheet.getRangeByIndexes(1, 0, dataRows.length, headers.length).values = dataRows;
  }
  const usedRows = Math.max(dataRows.length + 1, 2);
  dataSheet.getRangeByIndexes(0, 0, 1, headers.length).format = {
    fill: "#173F5F",
    font: { bold: true, color: "#FFFFFF" },
    wrapText: true,
    verticalAlignment: "center",
  };
  dataSheet.getRangeByIndexes(0, 0, usedRows, headers.length).format.borders = {
    preset: "inside",
    style: "thin",
    color: "#D9E2F3",
  };
  dataSheet.getRangeByIndexes(0, 0, usedRows, headers.length).format.autofitColumns();
  dataSheet.getRangeByIndexes(0, 0, 1, headers.length).format.rowHeight = 34;
  for (let c = 0; c < headers.length; c++) {
    const field = headers[c];
    const columnRange = dataSheet.getRangeByIndexes(1, c, Math.max(dataRows.length, 1), 1);
    if (isoDateColumns.has(field)) columnRange.setNumberFormat("yyyy-mm-dd");
    if (field.includes("price") || field === "discount_amount") columnRange.setNumberFormat("#,##0");
    if (field === "discount_rate") columnRange.setNumberFormat("0.0%");
    if (enums[field]) {
      columnRange.dataValidation = { rule: { type: "list", values: enums[field] } };
    }
  }
  dataSheet.freezePanes.freezeRows(1);
  if (dataRows.length) {
    dataSheet.tables.add(dataSheet.getRangeByIndexes(0, 0, dataRows.length + 1, headers.length), true, `DataTable${index}`);
  }

  const dictionary = [["Field", "Required", "Allowed values", "Description"], ...makeDictionary(headers, config.required || [], config.descriptions || {})];
  dictionarySheet.getRangeByIndexes(0, 0, dictionary.length, 4).values = dictionary;
  dictionarySheet.getRange("A1:D1").format = { fill: "#20639B", font: { bold: true, color: "#FFFFFF" } };
  dictionarySheet.getRangeByIndexes(0, 0, dictionary.length, 4).format.autofitColumns();
  dictionarySheet.getRange("D1:D200").format.wrapText = true;
  dictionarySheet.freezePanes.freezeRows(1);

  const enumRows = [["Field", "Allowed Value"]];
  for (const [field, values] of Object.entries(enums)) for (const value of values) enumRows.push([field, value]);
  enumSheet.getRangeByIndexes(0, 0, enumRows.length, 2).values = enumRows;
  enumSheet.getRange("A1:B1").format = { fill: "#3CAEA3", font: { bold: true, color: "#FFFFFF" } };
  enumSheet.getRangeByIndexes(0, 0, enumRows.length, 2).format.autofitColumns();
  enumSheet.freezePanes.freezeRows(1);

  const output = await SpreadsheetFile.exportXlsx(workbook);
  await output.save(path.join(referenceDir, config.file));
  if (previewDir) {
    await fs.mkdir(previewDir, { recursive: true });
    const preview = await workbook.render({ sheetName: "Data", autoCrop: "all", scale: 1, format: "png" });
    await fs.writeFile(path.join(previewDir, `${config.file}.png`), new Uint8Array(await preview.arrayBuffer()));
  }
}

await fs.mkdir(referenceDir, { recursive: true });
for (let index = 0; index < configs.length; index++) {
  await createWorkbook(configs[index], index + 1);
}
console.log(JSON.stringify({ ok: true, workbooks: configs.map((config) => config.file) }, null, 2));
