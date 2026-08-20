#!/usr/bin/env ruby
require "json"
require "yaml"

root = File.expand_path("../..", __dir__)

def load_yaml(root, relative)
  YAML.load_file(File.join(root, relative))
end

checks = {}

standard = load_yaml(root, "standards/edm_design_rules_v1.0.yaml")
templates = load_yaml(root, "design_system/templates_v1.0.yaml")
modules = load_yaml(root, "design_system/modules_v1.0.yaml")
checks[:frozen_dependencies] = {
  pass: [standard, templates, modules].all? { |document| document.fetch("status").to_s.casecmp("Frozen").zero? },
  detail: "Design Standard, Template Library and Module Library v1.0 remain Frozen"
}

reverse = load_yaml(root, "brand_system/switchbot_approved_reverse_engineering_v1.0.yaml")
lengths = reverse.fetch("samples").map { |sample| sample.fetch("total_length").to_i }
module_counts = reverse.fetch("samples").map { |sample| sample.fetch("module_count") }
checks[:approved_evidence] = {
  pass: reverse.fetch("samples").length == 8 && lengths.min == 4797 && lengths.max == 12_863,
  detail: { samples: reverse.fetch("samples").length, min_px: lengths.min, max_px: lengths.max, module_range: [module_counts.min, module_counts.max] }
}

proposal = load_yaml(root, "brand_system/template_calibration_proposal_v1.0.yaml")
checks[:template_audit] = {
  pass: proposal.fetch("templates").length == 15,
  detail: proposal.fetch("templates").group_by { |row| row.fetch("decision") }.transform_values(&:length)
}

variants = load_yaml(root, "brand_system/switchbot_long_form_variants_v1.0.yaml")
families = variants.fetch("variants").map { |variant| variant.fetch("family") }.uniq
checks[:long_form_coverage] = {
  pass: families.length == 6,
  detail: families
}

rules = load_yaml(root, "brand_system/switchbot_composition_rules_v1.0.yaml")
checks[:evidence_priority] = {
  pass: rules.dig("evidence_priority", "order").first == "Tier A Approved SwitchBot EDM" &&
    rules.dig("scope", "render_mode") == "switchbot_brand",
  detail: rules.fetch("evidence_priority").fetch("order")
}

brand_qa = JSON.parse(File.read(File.join(root, "output", "playwright", "phase5_5", "brand_renderer_qa.json")))
checks[:brand_renders] = {
  pass: %w[P02 P04].all? do |id|
    item = brand_qa.fetch(id).fetch("switchbot_brand_v2")
    item.fetch("render_mode") == "switchbot_brand" && item.fetch("module_count") == 10 && item.fetch("broken_images").zero?
  end,
  detail: %w[P02 P04].to_h do |id|
    item = brand_qa.fetch(id).fetch("switchbot_brand_v2")
    [id, { length_px: item.fetch("total_length_px"), modules: item.fetch("module_count"), images: item.fetch("image_count"), ctas: item.fetch("cta_count") }]
  end
}

checks[:responsive] = {
  pass: %w[P02 P04].all? do |id|
    brand_qa.fetch(id).fetch("responsive").values.all? do |row|
      row.fetch("no_horizontal_overflow") && row.fetch("broken_images").zero? && row.fetch("ctas_min_44px") && row.fetch("ctas_single_line")
    end
  end,
  detail: "320/375/390/414/768px"
}

asset_results = %w[P02 P04].to_h do |id|
  manifest = load_yaml(root, "pilot/#{id}/truth_pack/asset_manifest.yaml")
  approved = manifest.fetch("assets").select { |asset| asset["approved"] == true }
  paths_ok = approved.all? { |asset| File.file?(File.join(root, asset.fetch("source_path"))) }
  [id, { approved_assets: approved.length, paths_exist: paths_ok, production_footer: manifest.fetch("assets").find { |asset| asset["asset_type"] == "footer_asset" }.fetch("status") }]
end
checks[:asset_truth] = {
  pass: asset_results.values.all? { |row| row[:paths_exist] && row[:production_footer] == "MISSING" },
  detail: asset_results
}

review_qa = JSON.parse(File.read(File.join(root, "output", "playwright", "phase5_5", "review_pages_qa.json")))
review = review_qa.fetch("brand_calibration_review")
checks[:human_review_surface] = {
  pass: review.fetch("case_forms") == 2 && review.fetch("score_selects") == 14 && review.fetch("feel_selects") == 2 && review.fetch("all_human_fields_blank") && review.dig("csv_export", "lines") == 3,
  detail: { cases: review.fetch("case_forms"), score_fields: review.fetch("score_selects"), feel_fields: review.fetch("feel_selects"), blank: review.fetch("all_human_fields_blank"), csv_lines: review.dig("csv_export", "lines") }
}

pass = checks.values.all? { |check| check[:pass] }
payload = { phase: "5.5", status: pass ? "PASS" : "FAIL", checks: checks }
output_dir = File.join(root, "output", "playwright", "phase5_5")
File.write(File.join(output_dir, "static_qa.json"), "#{JSON.pretty_generate(payload)}\n")

report = +"# Phase 5.5 QA\n\n- Overall: **#{payload[:status]}**\n"
checks.each do |name, check|
  report << "- #{name}: **#{check[:pass] ? "PASS" : "FAIL"}** — #{check[:detail].is_a?(String) ? check[:detail] : check[:detail].to_json}\n"
end
report << "\n## Scope boundary\n\n- P02/P04 remain CONDITIONAL internal Brand Calibration outputs.\n- Product Knowledge external approval, proof/service evidence and production footer/legal remain unresolved.\n- Frozen Design Standard and Design System v1.0 were not overwritten.\n"
File.write(File.join(root, "research", "phase5_5_qa.md"), report)

puts JSON.pretty_generate(payload)
exit(pass ? 0 : 1)
