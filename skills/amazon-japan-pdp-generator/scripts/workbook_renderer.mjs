import fs from "node:fs/promises";
import path from "node:path";
import { SpreadsheetFile, Workbook } from "@oai/artifact-tool";

function value(input) {
  if (input === null || input === undefined) return "";
  if (Array.isArray(input)) return input.join(" | ");
  if (typeof input === "object") return JSON.stringify(input);
  return input;
}

function colLetter(index) {
  let number = index + 1;
  let output = "";
  while (number > 0) {
    number -= 1;
    output = String.fromCharCode(65 + (number % 26)) + output;
    number = Math.floor(number / 26);
  }
  return output;
}

function tableName(filename) {
  return filename.replace(/\.xlsx$/i, "").replace(/[^A-Za-z0-9]/g, "").slice(0, 50) + "Table";
}

function statusColor(status) {
  if (/^(Pass|Ready|Approved|Confirmed|Resolved)/i.test(status)) return "#DCFCE7";
  if (/Blocked|Missing|Conflict|Prohibited|Fixture/i.test(status)) return "#FEE2E2";
  if (/Need|Pending|Review|Unknown/i.test(status)) return "#FEF3C7";
  return "";
}

async function makeWorkbook(spec, definition, outputDir, previewDir) {
  const workbook = Workbook.create();
  const sheet = workbook.worksheets.add(definition.sheet);
  sheet.showGridLines = false;
  const columns = definition.columns;
  const rows = definition.rows.map(row => row.map(value));
  const lastCol = colLetter(columns.length - 1);
  const lastRow = Math.max(5, rows.length + 5);
  sheet.getRange(`A1:${lastCol}1`).merge();
  sheet.getRange("A1").values = [[definition.title]];
  sheet.getRange(`A2:${lastCol}2`).merge();
  sheet.getRange("A2").values = [[`Derived from PRODUCT_PAGE_SPEC.json · Spec SHA-256 ${spec.meta.spec_sha256}`]];
  sheet.getRange(`A3:${lastCol}3`).merge();
  sheet.getRange("A3").values = [[definition.note]];
  sheet.getRange(`A5:${lastCol}5`).values = [columns.map(column => column.label)];
  if (rows.length) sheet.getRangeByIndexes(5, 0, rows.length, columns.length).values = rows;
  sheet.getRange(`A1:${lastCol}1`).format = { fill: "#143E37", font: { name: "Arial", size: 16, bold: true, color: "#FFFFFF" }, verticalAlignment: "center" };
  sheet.getRange(`A2:${lastCol}2`).format = { fill: "#DDF3ED", font: { name: "Arial", size: 10, color: "#315B54" }, wrapText: true };
  sheet.getRange(`A3:${lastCol}3`).format = { fill: "#F6FAF9", font: { name: "Arial", size: 10, italic: true, color: "#5B6B68" }, wrapText: true };
  sheet.getRange(`A5:${lastCol}5`).format = { fill: "#23A98F", font: { name: "Arial", size: 10, bold: true, color: "#FFFFFF" }, wrapText: true, verticalAlignment: "center" };
  sheet.getRange(`A6:${lastCol}${lastRow}`).format.font = { name: "Arial", size: 9 };
  if (rows.length) {
    const body = sheet.getRange(`A6:${lastCol}${rows.length + 5}`);
    body.format = { wrapText: true, verticalAlignment: "top", borders: { preset: "insideHorizontal", style: "thin", color: "#E2E8F0" } };
    const table = sheet.tables.add(`A5:${lastCol}${rows.length + 5}`, true, tableName(definition.filename));
    table.style = "TableStyleMedium4";
    const statusIndexes = columns.map((column,index)=>/status|gate/i.test(column.key)?index:-1).filter(index=>index>=0);
    for (let rowIndex = 0; rowIndex < rows.length; rowIndex += 1) {
      for (const statusIndex of statusIndexes) {
        const fill = statusColor(String(rows[rowIndex][statusIndex] || ""));
        if (fill) sheet.getCell(rowIndex + 5, statusIndex).format.fill = fill;
      }
    }
  }
  for (let index = 0; index < columns.length; index += 1) sheet.getRange(`${colLetter(index)}:${colLetter(index)}`).format.columnWidth = columns[index].width || 18;
  sheet.getRange("1:1").format.rowHeight = 30;
  sheet.getRange("2:2").format.rowHeight = 32;
  sheet.getRange("3:3").format.rowHeight = 38;
  sheet.getRange("5:5").format.rowHeight = 35;
  sheet.freezePanes.freezeRows(5);
  const outputFile = path.join(outputDir, definition.filename);
  const blob = await SpreadsheetFile.exportXlsx(workbook);
  await blob.save(outputFile);
  const inspection = await workbook.inspect({
    kind: "sheet,table,match",
    searchTerm: "#REF!|#DIV/0!|#VALUE!|#NAME\\?|#N/A",
    options: { useRegex: true, maxResults: 100 },
    maxChars: 5000,
    tableMaxRows: 8,
    tableMaxCols: 12,
  });
  const preview = await workbook.render({ sheetName: definition.sheet, autoCrop: "all", scale: 1, format: "png" });
  await fs.writeFile(path.join(previewDir, definition.filename.replace(/\.xlsx$/i, ".png")), new Uint8Array(await preview.arrayBuffer()));
  return { file: definition.filename, inspection: inspection.ndjson };
}

function columns(keys, wide = []) {
  return keys.map(key => ({ key, label: key.replace(/_/g, " ").replace(/^./, char => char.toUpperCase()), width: wide.includes(key) ? 28 : 16 }));
}

function definitions(spec) {
  const sellingPoints = [spec.strategy.heroSellingPoint, ...(spec.strategy.coreSellingPoints || []), ...(spec.strategy.supportingFeatures || []), ...(spec.strategy.technicalDetails || [])].filter(Boolean);
  const compositionRows = [
    ...spec.product_images.map(item => [item.id,"Product Image",item.stage_label_cn,item.role,item.template_id,item.headline,item.sub_copy,item.layers.product_layer.source,item.layers.scene_layer.source,item.asset_resolution.selected_resolution,item.claim_source,item.risk,item.status,spec.human_gates.layout_approval.status,spec.publish_gate.status]),
    ...spec.aplus_modules.map(module => [module.id,"A+ Module",module.units.map(unit=>unit.stage).join(" → "),module.story_role,module.template_id,module.module_headline,module.units.map(unit=>unit.copy).join(" | "),module.units.map(unit=>unit.layers.product_layer.source),module.units.map(unit=>unit.layers.scene_layer.source),module.units.map(unit=>unit.asset_resolution.selected_resolution),module.units.map(unit=>unit.claim_source),module.units.map(unit=>unit.risk),module.module_availability,spec.human_gates.layout_approval.status,spec.publish_gate.status]),
  ];
  const imageRows = spec.product_images.map(item => [item.id,item.sequence,item.stage,item.user_question,item.role,item.key_message,item.template_id,item.headline,item.sub_copy,item.copy_review?.selected,item.copy_review?.status,item.proof_items,item.layers.product_layer.source,item.layers.scene_layer.source,item.source_origin,item.source_asset_type,item.product_body_ai_generated,item.asset_resolution.selected_resolution,item.claim_ids,item.claim_source,item.risk,item.status,item.outputs.svg,item.outputs.jpeg]);
  const aplusRows = spec.aplus_modules.flatMap(module => module.units.map(unit => [module.id,module.sequence,module.template_id,module.template_snapshot.name,module.story_role,module.module_availability,module.outputs.svg,module.outputs.jpeg,unit.id,unit.stage,unit.purpose,unit.user_question,unit.headline,unit.copy,unit.copy_review?.selected,unit.copy_review?.status,unit.layers.product_layer.source,unit.layers.scene_layer.source,unit.source_origin,unit.source_asset_type,unit.product_body_ai_generated,unit.asset_resolution.selected_resolution,unit.claim_ids,unit.claim_source,unit.risk,unit.status]));
  const comparisonProducts = spec.comparison.products || [];
  const comparisonKeys = ["criteria", ...comparisonProducts.map(product=>product.id), "source", "status"];
  const comparisonRows = (spec.comparison.rows || []).map(row => [row.criteria,...comparisonProducts.map(product=>row.values?.[product.id]||""),row.source,row.status]);
  const artAssets = spec.art_direction_spec?.asset_requirements || [];
  const assetRows = artAssets.length
    ? artAssets.map(item => [item.asset_id,item.used_in,item.purpose,item.shot_render_type,item.angle,item.crop,item.resolution,item.transparency,item.required_product_state,item.lighting,item.scene_requirement,item.claim_dependency,item.priority,item.owner,item.status,item.fallback])
    : spec.asset_resolution_plan.records.map(item => [item.visual_id,item.official_scene_available,item.official_product_available,item.ai_background_needed,item.network_reference_needed,item.composite_needed,item.missing_assets,item.priority_order,item.selected_resolution,item.product_asset,item.scene_asset,item.authorization_status,item.status]);
  const gapRows = artAssets.length
    ? artAssets.filter(item=>item.status!=="READY").map(item=>[item.asset_id,item.used_in,item.priority,item.purpose,item.claim_dependency,item.status,item.fallback,item.owner])
    : spec.asset_resolution_plan.records.filter(item=>item.status!=="Resolved").map(item=>[item.visual_id,item.missing_assets,item.authorization_status,item.selected_resolution,item.status,"Provide user-authorized official product/scene assets or retain Blocked"]);
  return [
    {filename:"visual_composition_plan.xlsx",sheet:"Composition Plan",title:"Visual Composition Plan",note:"Gate order: story → layout → final render. Every visual has one template_id and independent Product/Scene/Graphic layers.",columns:columns(["visual_id","type","stage","role","template_id","headline","sub_copy","product_asset","scene_asset","asset_resolution","claim_source","risk","content_status","layout_gate","publish_gate"],["role","headline","sub_copy","product_asset","scene_asset","claim_source","risk"]),rows:compositionRows},
    {filename:"selling_point_matrix.xlsx",sheet:"Selling Points",title:"Selling Point Matrix",note:"One Level 1 Hero value; facts and claims remain source-bounded.",columns:columns(["priority","level","feature","mechanism","benefit","user_problem","scenario","proof","placement","asset_needed","claim_ids","source","status"],["feature","mechanism","benefit","user_problem","scenario","proof","placement","asset_needed","source"]),rows:sellingPoints.map(item=>[item.priority,item.level,item.feature,item.mechanism,item.benefit,item.userProblem,item.scenario,item.proof,item.placement,item.assetNeeded,item.claimIds,item.source,item.status])},
    {filename:"product_image_brief.xlsx",sheet:"Product Images",title:"7-Image Decision Journey Brief",note:"Exactly seven images, mapped to the seven consumer decision stages. Layout freedom is limited by template_id.",columns:columns(["image_id","sequence","stage","user_question","role","key_message","template_id","headline","sub_copy","copy_selected","copy_review_status","proof_items","product_layer","scene_layer","source_origin","source_asset_type","product_body_ai_generated","asset_resolution","claim_ids","claim_source","risk","content_status","editable_svg","final_jpeg"],["user_question","role","key_message","headline","sub_copy","proof_items","product_layer","scene_layer","claim_source","risk"]),rows:imageRows},
    {filename:"aplus_content_plan.xlsx",sheet:"Aplus Plan",title:"A+ Story and Template Plan",note:"Seven modules and sixteen units are retained. Units are not standalone banners; each module uses one formal template_id.",columns:columns(["module_id","sequence","template_id","template_name","story_role","module_availability","editable_svg","final_jpeg","unit_id","stage","purpose","user_question","headline","copy","copy_selected","copy_review_status","product_layer","scene_layer","source_origin","source_asset_type","product_body_ai_generated","asset_resolution","claim_ids","claim_source","risk","content_status"],["story_role","purpose","user_question","headline","copy","product_layer","scene_layer","claim_source","risk"]),rows:aplusRows},
    {filename:"comparison_chart.xlsx",sheet:"Comparison",title:"Source-backed Comparison",note:"Unknown or unapproved cells remain explicit and do not become consumer claims.",columns:columns(comparisonKeys,["criteria","source"]),rows:comparisonRows},
    {filename:"amazon_seo_keywords.xlsx",sheet:"SEO",title:"Amazon Japan SEO",note:"SEO is derived from the same Spec as Title, Bullet and HTML. Avoid terms remain marked.",columns:columns(["category","keyword","priority","placement","status"],["keyword","placement"]),rows:spec.seo.map(item=>[item.category,item.keyword,item.priority,item.placement,item.status])},
    artAssets.length
      ? {filename:"asset_requirements.xlsx",sheet:"Asset Requirements",title:"Art Direction Asset Production Brief",note:"Product Layer is official-only. Scene, shot, crop, state, Claim dependency, priority and fallback are production decisions derived from ART_DIRECTION_SPEC.json.",columns:columns(["asset_id","used_in","purpose","shot_render_type","angle","crop","resolution","transparency","required_product_state","lighting","scene_requirement","claim_dependency","priority","owner","status","fallback"],["used_in","purpose","crop","required_product_state","scene_requirement","claim_dependency","fallback"]),rows:assetRows}
      : {filename:"asset_requirements.xlsx",sheet:"Asset Requirements",title:"Asset Resolution Plan",note:"Priority: official scene → official white/render → authorized material → AI scene without product → placeholder.",columns:columns(["visual_id","official_scene_available","official_product_available","ai_background_needed","network_reference_needed","composite_needed","missing_assets","priority_order","selected_resolution","product_asset","scene_asset","authorization_status","status"],["missing_assets","priority_order","selected_resolution","product_asset","scene_asset","authorization_status"]),rows:assetRows},
    artAssets.length
      ? {filename:"asset_gap_analysis.xlsx",sheet:"Asset Gaps",title:"Art Direction Asset Gaps",note:"P0 blocks final visual production; P1 has major quality impact; P2 may use the approved fallback.",columns:columns(["asset_id","used_in","priority","purpose","claim_dependency","status","fallback","owner"],["used_in","purpose","claim_dependency","fallback"]),rows:gapRows}
      : {filename:"asset_gap_analysis.xlsx",sheet:"Asset Gaps",title:"Asset Gaps Blocking Final",note:"Fixture, temporary, unlicensed and placeholder assets cannot enter Final publication.",columns:columns(["visual_id","missing_assets","authorization_status","current_resolution","status","required_action"],["missing_assets","authorization_status","current_resolution","required_action"]),rows:gapRows},
  ];
}

export async function renderWorkbooksFromSpec(spec, outputDir) {
  const workbookDir = path.join(outputDir, "workbooks");
  const previewDir = path.join(outputDir, "qa", "workbook-previews");
  await Promise.all([workbookDir,previewDir].map(directory=>fs.mkdir(directory,{recursive:true})));
  const inspections = [];
  for (const definition of definitions(spec)) inspections.push(await makeWorkbook(spec,definition,workbookDir,previewDir));
  await fs.mkdir(path.join(outputDir,"qa"),{recursive:true});
  await fs.writeFile(path.join(outputDir,"qa","workbook-inspection.json"),`${JSON.stringify({spec_sha256:spec.meta.spec_sha256,workbooks:inspections},null,2)}\n`,"utf8");
  return inspections;
}

export async function renderArtDirectionWorkbooks(spec, artDirectionSpec, outputDir) {
  const workbookDir = path.join(outputDir, "workbooks");
  const previewDir = path.join(outputDir, "qa", "workbook-previews");
  await Promise.all([workbookDir,previewDir].map(directory=>fs.mkdir(directory,{recursive:true})));
  const enriched = {...spec, art_direction_spec: artDirectionSpec};
  const selected = definitions(enriched).filter(definition=>["asset_requirements.xlsx","asset_gap_analysis.xlsx"].includes(definition.filename));
  const inspections=[];
  for(const definition of selected) inspections.push(await makeWorkbook(enriched,definition,workbookDir,previewDir));
  return inspections;
}
