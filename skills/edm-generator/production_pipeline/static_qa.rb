# frozen_string_literal: true

require "yaml"
require "json"
require "uri"
require "date"
require "time"

ROOT = File.expand_path("..", __dir__)
ALLOWED_STATES = %w[VERIFIED APPROVED UNVERIFIED MISSING NOT_REQUIRED].freeze
CASES = %w[PILOT-A-LOCK-ULTRA PILOT-B-DAILY-STATION].freeze

checks = {}

def walk_statuses(node, path = [], rows = [])
  case node
  when Hash
    rows << [path.join("."), node["status"]] if node.key?("status") && node["status"].is_a?(String)
    node.each { |key, value| walk_statuses(value, path + [key], rows) }
  when Array
    node.each_with_index { |value, index| walk_statuses(value, path + [index], rows) }
  end
  rows
end

product_files = Dir[File.join(ROOT, "production_truth", "products", "*.yaml")]
campaign_files = Dir[File.join(ROOT, "production_truth", "campaigns", "*.yaml")]
status_rows = (product_files + campaign_files).flat_map do |path|
  walk_statuses(YAML.safe_load(File.read(path), permitted_classes: [Date, Time], aliases: true)).map { |row| [path.sub("#{ROOT}/", ""), *row] }
end
checks["truth_status_vocabulary"] = {
  "pass" => status_rows.all? { |_, _, state| ALLOWED_STATES.include?(state) },
  "invalid" => status_rows.reject { |_, _, state| ALLOWED_STATES.include?(state) }
}

registry = YAML.safe_load(File.read(File.join(ROOT, "production_truth/assets/asset_registry.yaml")), permitted_classes: [Date, Time], aliases: true)
asset_rows = registry.fetch("assets")
checks["asset_paths_exist"] = {
  "pass" => asset_rows.all? { |asset| File.file?(File.join(ROOT, asset.fetch("source_path"))) },
  "missing" => asset_rows.reject { |asset| File.file?(File.join(ROOT, asset.fetch("source_path"))) }.map { |asset| asset.fetch("asset_id") }
}
hero_ai = asset_rows.select { |asset| asset.fetch("visual_purposes").include?("hero_product") && asset.fetch("asset_type") == "ai_background" }
checks["no_ai_hero_product_asset"] = {"pass" => hero_ai.empty?, "violations" => hero_ai.map { |asset| asset.fetch("asset_id") }}

case_results = {}
CASES.each do |case_id|
  dir = File.join(ROOT, "production_output", case_id)
  manifest = YAML.safe_load(File.read(File.join(dir, "truth_manifest.yaml")), permitted_classes: [Date, Time], aliases: true)
  asset_manifest = YAML.safe_load(File.read(File.join(dir, "asset_manifest.yaml")), permitted_classes: [Date, Time], aliases: true)
  qa = manifest.fetch("qa")
  copy = manifest.fetch("copy")
  required = %w[editable_edm.html desktop_preview.png mobile_preview.png full_edm.png final_copy.md asset_manifest.yaml truth_manifest.yaml design_review.html qa_report.md claim_lint_report.md]
  cta = manifest.dig("campaign", "cta", "url", "value").to_s
  uri = URI.parse(cta) rescue nil
  case_results[case_id] = {
    "required_files_present" => required.all? { |name| File.file?(File.join(dir, name)) },
    "missing_files" => required.reject { |name| File.file?(File.join(dir, name)) },
    "hard_rule_violations" => qa.fetch("blocking_hard_rules"),
    "browser_qa" => qa.fetch("browser_qa"),
    "no_fake_content" => qa.fetch("no_fake_content"),
    "no_product_redraw" => qa.fetch("no_product_redraw"),
    "copy_not_falsely_approved" => copy.fetch("approval_status") != "APPROVED",
    "claim_linter_blocks_external_use" => File.read(File.join(dir, "claim_lint_report.md")).include?("Publication Decision: BLOCK"),
    "cta_url_valid" => uri && %w[http https].include?(uri.scheme) && !uri.host.to_s.empty?,
    "asset_manifest_scoped" => asset_manifest.key?("assets") && asset_manifest.key?("production_scope_gaps"),
    "production_scope_gaps_explicit" => asset_manifest.fetch("production_scope_gaps").any?,
    "production_status" => qa.fetch("production_status")
  }
end
checks["cases"] = case_results

frozen = {
  "design_standard" => YAML.safe_load(File.read(File.join(ROOT, "standards/edm_design_rules_v1.0.yaml")), permitted_classes: [Date, Time], aliases: true).fetch("status"),
  "templates" => YAML.safe_load(File.read(File.join(ROOT, "design_system/templates_v1.0.yaml")), permitted_classes: [Date, Time], aliases: true).fetch("status"),
  "modules" => YAML.safe_load(File.read(File.join(ROOT, "design_system/modules_v1.0.yaml")), permitted_classes: [Date, Time], aliases: true).fetch("status")
}
checks["frozen_dependencies"] = {"pass" => frozen.values.all? { |state| state.to_s.casecmp("frozen").zero? }, "statuses" => frozen}

all_case_checks = case_results.values.all? do |row|
  row.fetch("required_files_present") && row.fetch("hard_rule_violations").empty? && row.fetch("browser_qa") == "PASS" &&
    row.fetch("no_fake_content") && row.fetch("no_product_redraw") && row.fetch("copy_not_falsely_approved") && row.fetch("claim_linter_blocks_external_use") &&
    row.fetch("cta_url_valid") && row.fetch("asset_manifest_scoped") && row.fetch("production_scope_gaps_explicit")
end
overall = checks.fetch("truth_status_vocabulary").fetch("pass") && checks.fetch("asset_paths_exist").fetch("pass") &&
  checks.fetch("no_ai_hero_product_asset").fetch("pass") && checks.fetch("frozen_dependencies").fetch("pass") && all_case_checks

report = {"schema_version" => "1.0.0", "overall" => overall ? "PASS" : "FAIL", "checks" => checks}
File.write(File.join(ROOT, "production_output", "static_qa.json"), JSON.pretty_generate(report) + "\n")
puts JSON.pretty_generate(report)
exit(overall ? 0 : 1)
