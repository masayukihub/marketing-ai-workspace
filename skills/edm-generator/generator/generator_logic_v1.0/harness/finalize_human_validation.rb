# frozen_string_literal: true

require "csv"
require "date"
require "time"
require "yaml"

root = File.expand_path("..", __dir__)
review_path = File.join(root, "research/generator_human_review.csv")
scorecard_path = File.join(root, "generator/outputs/scorecard.yaml")

allowed_statuses = ["Pass", "Needs Modification", "Fail"].freeze
expected_ids = (1..17).map { |index| format("GTC-%03d", index) }

rows = CSV.read(review_path, headers: true)
ids = rows.map { |row| row["test_case_id"] }
abort "Human Review must contain exactly 17 unique cases" unless rows.length == 17 && ids.uniq.length == 17
abort "Human Review test case IDs do not match the frozen fixtures" unless ids.sort == expected_ids

invalid_statuses = rows.reject { |row| allowed_statuses.include?(row["overall_decision"]) }
abort "Invalid or blank Human Review status" unless invalid_statuses.empty?

counts = allowed_statuses.to_h { |status| [status, rows.count { |row| row["overall_decision"] == status }] }
acceptance_rate = ((counts["Pass"] + counts["Needs Modification"]) * 100.0 / rows.length).round(1)

scorecard = YAML.safe_load(File.read(scorecard_path), permitted_classes: [Date, Time], aliases: false)
execution = scorecard.fetch("execution")
negative_paths = scorecard.fetch("negative_path_validation")

gate_checks = {
  "automated_case_execution" => execution["executed_cases"] == execution["defined_cases"] && execution["automated_failures"].zero?,
  "template_selection_accuracy_min_85" => execution["template_selection_accuracy"].to_f >= 85.0,
  "human_pass_plus_needs_modification_min_90" => acceptance_rate >= 90.0,
  "hard_rule_violations_zero" => execution["unsafe_hard_rule_violations"].zero?,
  "fake_claims_zero" => execution["fake_claims"].zero?,
  "fake_prices_zero" => execution["fake_prices"].zero?,
  "fake_product_asset_zero" => execution["ai_product_redraw_requests"].zero?,
  "asset_missing_blocks" => negative_paths["GTC-016_missing_asset"] == "PASS",
  "missing_promotion_cta_period_handled" => negative_paths["GTC-017_missing_cta"] == "PASS",
  "template_selection_no_systemic_error" => execution["template_matches"] == execution["executed_cases"],
  "deterministic" => execution["deterministic_repeat_match"] == true
}

scorecard["human_validation"] = {
  "source" => "research/generator_human_review.csv",
  "review_mode" => "human_assisted_by_codex_with_user_authorization",
  "total_cases" => rows.length,
  "pass" => counts["Pass"],
  "needs_modification" => counts["Needs Modification"],
  "fail" => counts["Fail"],
  "human_acceptance_rate_percent" => acceptance_rate
}
scorecard["renderer_gate"] = gate_checks.transform_values { |passed| passed ? "PASS" : "FAIL" }
scorecard["renderer_gate"]["overall"] = gate_checks.values.all? ? "PASS" : "FAIL"
scorecard["renderer_gate"]["phase5_renderer_gate"] = gate_checks.values.all? ? "PASS" : "FAIL"

File.write(scorecard_path, YAML.dump(scorecard).sub(/\A---\s*\n/, ""))

puts({
  pass: counts["Pass"],
  needs_modification: counts["Needs Modification"],
  fail: counts["Fail"],
  acceptance_rate_percent: acceptance_rate,
  phase5_renderer_gate: scorecard.dig("renderer_gate", "phase5_renderer_gate")
}.to_yaml)
