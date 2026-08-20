#!/usr/bin/env ruby
# frozen_string_literal: true

require "json"
require "fileutils"
require "date"
require "time"
require_relative "lib/pipeline"

root = File.expand_path("..", __dir__)
inputs = if ARGV.empty?
           %w[
             production_pipeline/inputs/pilot_a_lock_ultra.yaml
             production_pipeline/inputs/pilot_b_daily_station.yaml
           ]
         else
           ARGV.map { |path| Pathname.new(path).absolute? ? Pathname.new(path).relative_path_from(Pathname.new(root)).to_s : path }
         end

snapshot_path = File.join(root, "production_registry", "readiness_snapshot.yaml")
if File.file?(snapshot_path) && ENV["PHASE7_GATE_BYPASS"] != "1"
  snapshot = YAML.safe_load(File.read(snapshot_path), permitted_classes: [Date, Time], aliases: true)
  requested_case_ids = inputs.map { |path| YAML.safe_load(File.read(File.join(root, path)), permitted_classes: [Date, Time], aliases: true).fetch("case_id") }
  blocked = requested_case_ids.map do |case_id|
    row = snapshot.fetch("cases").find { |item| item.fetch("case_id") == case_id }
    next nil unless row && !row.dig("state_gates", "DESIGN_INPUTS_READY")
    [case_id, row.fetch("overall_status"), row.dig("unique_remaining_blocker", "missing") || "Design inputs are not ready"]
  end.compact
  unless blocked.empty?
    abort(blocked.map { |case_id, status, reason| "#{case_id}: One-shot blocked at #{status}. Next blocker: #{reason}" }.join("\n"))
  end
end

pipeline = ProductionEDM::Pipeline.new(root)
results = inputs.map { |path| pipeline.run(path) }
index = {
  "schema_version" => "1.0.0",
  "generated_at" => Time.now.utc.iso8601,
  "cases" => results.map do |result|
    {
      "case_id" => result.fetch("case_id"),
      "raw_input" => result.dig("one_shot_input", "raw_input"),
      "product_id" => result.fetch("product_id"),
      "selected_template" => result.dig("decision", "selected_template"),
      "length_class" => result.dig("decision", "length", "length_class"),
      "module_count" => result.fetch("modules").length,
      "production_status" => result.dig("qa", "production_status"),
      "output_dir" => result.fetch("output_dir")
    }
  end
}
FileUtils.mkdir_p(File.join(root, "production_output"))
File.write(File.join(root, "production_output/index.yaml"), YAML.dump(index))
puts JSON.pretty_generate(index)
