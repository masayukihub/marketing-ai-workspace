# frozen_string_literal: true

require "fileutils"
require "csv"
require "date"
require "digest"
require "yaml"
require "time"

root = File.expand_path("..", __dir__)
target = File.join(root, "generator/generator_logic_v1.0")
abort "Freeze target already exists: #{target}" if Dir.exist?(target)

files = {
  "generator/input_schema.yaml" => "schema/input_schema.yaml",
  "generator/support.rb" => "logic/support.rb",
  "generator/pipeline.rb" => "logic/pipeline.rb",
  "generator/brief_compiler/compiler.rb" => "logic/brief_compiler/compiler.rb",
  "generator/campaign_classifier/classifier.rb" => "logic/campaign_classifier/classifier.rb",
  "generator/template_selector/selector.rb" => "logic/template_selector/selector.rb",
  "generator/message_planner/planner.rb" => "logic/message_planner/planner.rb",
  "generator/module_composer/composer.rb" => "logic/module_composer/composer.rb",
  "generator/copy_planner/planner.rb" => "logic/copy_planner/planner.rb",
  "generator/asset_resolver/resolver.rb" => "logic/asset_resolver/resolver.rb",
  "generator/qa/checker.rb" => "logic/qa/checker.rb",
  "generator/run_tests.rb" => "harness/run_tests.rb",
  "generator/finalize_human_validation.rb" => "harness/finalize_human_validation.rb",
  "standards/edm_design_standard_v1.0.md" => "rules/edm_design_standard_v1.0.md",
  "standards/edm_design_rules_v1.0.yaml" => "rules/edm_design_rules_v1.0.yaml",
  "design_system/templates_v1.0.yaml" => "rules/templates_v1.0.yaml",
  "design_system/modules_v1.0.yaml" => "rules/modules_v1.0.yaml",
  "design_system/template_selection_rules_v1.0.yaml" => "rules/template_selection_rules_v1.0.yaml",
  "design_system/module_composition_rules_v1.0.yaml" => "rules/module_composition_rules_v1.0.yaml",
  "design_system/visual_rhythm_rules_v1.0.md" => "rules/visual_rhythm_rules_v1.0.md",
  "phase4_generator_contract.md" => "contract/phase4_generator_contract.md",
  "tests/generator_test_cases.yaml" => "validation/generator_test_cases.yaml",
  "generator/outputs/test_results.yaml" => "validation/test_results.yaml",
  "generator/outputs/scorecard.yaml" => "validation/scorecard.yaml",
  "research/generator_human_review.csv" => "validation/generator_human_review.csv",
  "research/phase4_failure_analysis.md" => "validation/phase4_failure_analysis.md"
}.freeze

review_rows = CSV.read(File.join(root, "research/generator_human_review.csv"), headers: true)
human_counts = review_rows.group_by { |row| row["overall_decision"] }.transform_values(&:length)
acceptance_rate = ((human_counts.fetch("Pass", 0) + human_counts.fetch("Needs Modification", 0)) * 1.0 / review_rows.length).round(4)
scorecard = YAML.safe_load(File.read(File.join(root, "generator/outputs/scorecard.yaml")), permitted_classes: [Date, Time], aliases: false)
abort "Phase 5 Renderer Gate is not PASS" unless scorecard.dig("renderer_gate", "phase5_renderer_gate") == "PASS"

manifest_files = files.map do |source_relative, snapshot_relative|
  source = File.join(root, source_relative)
  abort "Missing freeze source: #{source_relative}" unless File.file?(source)

  destination = File.join(target, snapshot_relative)
  FileUtils.mkdir_p(File.dirname(destination))
  FileUtils.cp(source, destination, preserve: true)
  {
    "source_path" => source_relative,
    "snapshot_path" => snapshot_relative,
    "sha256" => Digest::SHA256.file(destination).hexdigest
  }
end

manifest = {
  "version" => "1.0.0",
  "status" => "Frozen",
  "frozen_at" => Time.now.getlocal("+08:00").iso8601,
  "phase5_renderer_gate" => "PASS",
  "human_review" => {
    "total" => review_rows.length,
    "pass" => human_counts.fetch("Pass", 0),
    "needs_modification" => human_counts.fetch("Needs Modification", 0),
    "fail" => human_counts.fetch("Fail", 0),
    "acceptance_rate" => acceptance_rate,
    "decision_source" => "validation/generator_human_review.csv"
  },
  "design_system_policy" => "Snapshot only. Original frozen Design System v1.0 remains the project source of truth and was not overwritten.",
  "files" => manifest_files
}

File.write(File.join(target, "manifest.yaml"), YAML.dump(manifest).sub(/\A---\s*\n/, ""))
File.write(File.join(target, "README.md"), <<~MD)
  # EDM Generator Logic v1.0

  Status: **Frozen after Phase 4 Human Validation**

  This directory is a read-only snapshot of the Generator Schema, Decision Logic, frozen rule dependencies, test harness, 17 test fixtures, automated scorecard and Human-assisted Review used to pass the Phase 5 Renderer Gate.

  - Human Acceptance Rate: 100.0% (Pass 2 + Needs Modification 15 + Fail 0)
  - Template Selection Accuracy: 100.0% (17/17)
  - Unsafe Hard Rule Violations: 0
  - Fake Claim / Price / Product Asset: 0
  - Negative-path validation: GTC-016 and GTC-017 PASS

  Do not edit files inside this snapshot. Create a new version for future Generator Logic changes. The original Design Standard and Design System v1.0 remain unchanged outside this directory.
MD

puts target
