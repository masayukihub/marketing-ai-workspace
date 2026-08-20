#!/usr/bin/env ruby
# frozen_string_literal: true

require "yaml"
require "date"
require "time"

ROOT = File.expand_path("..", __dir__)
INPUTS = {
  "PILOT-A-LOCK-ULTRA" => "production_pipeline/inputs/pilot_a_lock_ultra.yaml",
  "PILOT-B-DAILY-STATION" => "production_pipeline/inputs/pilot_b_daily_station.yaml"
}.freeze

case_id = ARGV[0]
abort("Usage: ruby production_readiness/advance_pilot.rb PILOT-A-LOCK-ULTRA|PILOT-B-DAILY-STATION") unless INPUTS.key?(case_id)

system("ruby", File.join(__dir__, "evaluate_readiness.rb"), out: File::NULL) || abort("Readiness evaluation failed")
snapshot = YAML.safe_load(File.read(File.join(ROOT, "production_registry", "readiness_snapshot.yaml")), permitted_classes: [Date, Time], aliases: true)
row = snapshot.fetch("cases").find { |item| item.fetch("case_id") == case_id }
unless row.dig("state_gates", "DESIGN_INPUTS_READY")
  blocker = row.fetch("unique_remaining_blocker")
  abort("#{case_id} cannot rerun from #{row.fetch('overall_status')}. Unique next blocker: #{blocker.fetch('missing')} | Next action: #{blocker.fetch('next_action')}")
end

puts "#{case_id}: DESIGN_INPUTS_READY. Running one-shot with automatic Template / Module / Length / Hero decisions."
system("ruby", File.join(ROOT, "production_pipeline", "run_one_shot.rb"), INPUTS.fetch(case_id), chdir: ROOT) || abort("One-shot generation failed")

file_base = "file://#{ROOT}"
system({"EDM_BASE_URL" => file_base}, "node", File.join(ROOT, "production_pipeline", "browser_qa.js"), chdir: ROOT) || abort("Desktop/mobile browser QA failed")
system("ruby", File.join(ROOT, "production_pipeline", "finalize_qa.rb"), chdir: ROOT) || abort("QA finalization failed")
system("ruby", File.join(__dir__, "evaluate_readiness.rb"), out: File::NULL) || abort("Readiness re-evaluation failed")
system("ruby", File.join(__dir__, "build_review_pages.rb"), out: File::NULL) || abort("Review-page rebuild failed")

snapshot = YAML.safe_load(File.read(File.join(ROOT, "production_registry", "readiness_snapshot.yaml")), permitted_classes: [Date, Time], aliases: true)
row = snapshot.fetch("cases").find { |item| item.fetch("case_id") == case_id }
puts "#{case_id}: #{row.fetch('overall_status')} (#{row.fetch('production_readiness_percent')}%)."
puts "Next blocker: #{row.dig('unique_remaining_blocker', 'missing')}" if row["unique_remaining_blocker"]
