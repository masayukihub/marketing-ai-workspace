# frozen_string_literal: true

require "csv"
require "digest"
require "json"
require "yaml"

root = File.expand_path("..", __dir__)
checks = {}
library = YAML.safe_load(File.read(File.join(root, "templates", "historical", "library_v1.0.yaml")))
strategy = YAML.safe_load(File.read(File.join(root, "generator", "historical_template_first_strategy_v1.0.yaml")))
templates = library.fetch("templates")
required = %w[reference_full.png reference_desktop.png reference_source.html structure.yaml style_tokens.yaml editable_regions.yaml asset_slots.yaml copy_slots.yaml template_preview.html]

checks["template_count_is_8"] = templates.length == 8
checks["template_ids_unique"] = templates.map { |row| row.fetch("template_id") }.uniq.length == 8
checks["references_unique"] = templates.map { |row| row.fetch("reference_edm") }.uniq.length == 8
checks["all_template_files_present"] = templates.all? do |template|
  required.all? { |name| File.file?(File.join(root, "templates", "historical", template.fetch("template_id"), name)) }
end
checks["source_html_is_untouched_copy"] = templates.all? do |template|
  source = File.join(root, "research", "mobile_evidence", "html", "#{template.fetch("reference_edm")}.html")
  copy = File.join(root, "templates", "historical", template.fetch("template_id"), "reference_source.html")
  Digest::SHA256.file(source).hexdigest == Digest::SHA256.file(copy).hexdigest
end
checks["source_assets_copied"] = templates.all? do |template|
  ref = template.fetch("reference_edm")
  source_count = Dir[File.join(root, "research", "mobile_evidence", "assets", ref, "*")].count { |path| File.file?(path) }
  copied_count = Dir[File.join(root, "templates", "historical", "assets", ref, "*")].count { |path| File.file?(path) }
  source_count.positive? && source_count == copied_count
end
budget = strategy.fetch("visual_decision_budget")
checks["decision_budget_is_70_20_10"] = budget.values_at("historical_skeleton_percent", "controlled_adaptation_percent", "new_design_fallback_percent") == [70, 20, 10]
checks["historical_first_default_true"] = strategy.fetch("historical_template_first") == true
checks["external_reference_cannot_override"] = strategy.dig("inheritance_guards", "external_reference_override") == "blocked"
checks["generic_is_fallback_only"] = strategy.dig("roles", "generic_template") == "fallback_only" && strategy.dig("selection_policy", "generic_generation_default") == false

audit = CSV.read(File.join(root, "research", "historical_template_audit.csv"), headers: true)
checks["audit_has_21_complete_tier_ab"] = audit.count { |row| row["screenshot_dimensions"] != "missing" } == 21
checks["audit_has_19_usable_non_test"] = audit.count { |row| row["usable_complete_historical"] == "true" } == 19
checks["test_only_not_promoted"] = audit.select { |row| row["delivery_evidence"] == "test_only" }.all? { |row| row["formal_template_id"].to_s.empty? && row["audit_status"] == "excluded_test_only" }

summary = YAML.safe_load(File.read(File.join(root, "output", "historical_template_tests", "summary.yaml")))
browser = JSON.parse(File.read(File.join(root, "output", "historical_template_tests", "browser_qa.json")))
review_qa = JSON.parse(File.read(File.join(root, "output", "historical_template_tests", "review_page_qa.json")))
checks["matcher_top1_fixture_4_of_4"] = summary.fetch("case_count") == 4 && summary.fetch("top1_correct") == 4 && summary.fetch("top1_accuracy_percent") == 100.0
checks["accuracy_scope_is_honest"] = summary.fetch("accuracy_scope").include?("not Human Review accuracy")
checks["all_four_render_browser_qa_pass"] = browser.fetch("caseCount") == 4 && browser.fetch("passCount") == 4 && browser.fetch("results").all? { |row| row.fetch("qaPass") }
checks["review_page_browser_qa_pass"] = review_qa.fetch("pass") == true
checks["all_generated_outputs_present"] = summary.fetch("results").all? do |row|
  out = File.join(root, "output", "historical_template_tests", row.fetch("case_id"))
  %w[editable_edm.html generated_full.png generated_desktop.png generated_mobile.png matcher_result.yaml content_mapping.yaml asset_mapping.yaml browser_visual_qa.json].all? { |name| File.file?(File.join(out, name)) }
end
checks["no_fake_price_or_discount_in_test_html"] = summary.fetch("results").all? do |row|
  html = File.read(File.join(root, "output", "historical_template_tests", row.fetch("case_id"), "editable_edm.html"))
  !html.match?(/\d[\d,]*円|\d+\s*(?:%|％)\s*OFF/i)
end
checks["promotion_fixture_is_fail_closed"] = File.read(File.join(root, "output", "historical_template_tests", "HIST-VAL-003", "editable_edm.html")).include?("価格／割引／期間は描画していません")
checks["production_pipeline_routes_historical_first"] = File.read(File.join(root, "production_pipeline", "lib", "pipeline.rb")).include?("historical_template_first")

review_html = File.read(File.join(root, "research", "historical_template_validation.html"))
checks["human_review_fields_blank"] = review_html.scan(/data-human-field=/).length == 28 && !review_html.match?(/<option[^>]+selected/i)
checks["final_decisions_exact"] = %w[DELIVERABLE MINOR_REVISION MAJOR_REVISION WRONG_TEMPLATE].all? { |value| review_html.include?(">#{value}</option>") }
checks["report_and_review_exist"] = File.file?(File.join(root, "research", "historical_template_report.md")) && File.file?(File.join(root, "research", "historical_template_validation.html"))

failed = checks.select { |_, passed| !passed }.keys
result = {"generated_on" => "2026-08-20", "checks" => checks, "pass_count" => checks.count { |_, value| value }, "check_count" => checks.length, "failed" => failed, "status" => failed.empty? ? "PASS" : "FAIL"}
File.write(File.join(root, "output", "historical_template_tests", "static_qa.yaml"), YAML.dump(result))
puts YAML.dump(result)
exit(failed.empty? ? 0 : 1)
