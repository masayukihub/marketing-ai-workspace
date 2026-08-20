#!/usr/bin/env ruby
# frozen_string_literal: true

require "csv"
require "yaml"
require "json"
require "time"
require "date"

ROOT = File.expand_path("..", __dir__)
REGISTRY = File.join(ROOT, "production_registry")
DECISIONS = %w[APPROVE MINOR_REVISION MAJOR_REVISION REJECT].freeze
DIMENSIONS = %w[product_information japanese_usability brand_fit content_completeness visual_delivery_quality].freeze

csv_path = ARGV[0]
apply = ARGV.include?("--apply")
abort("Usage: ruby production_readiness/apply_phase8_visual_review.rb review.csv [--apply]") unless csv_path && File.file?(csv_path)

row = CSV.read(csv_path, headers: true, encoding: "bom|utf-8").first
abort("Review CSV is empty") unless row
abort("Only PILOT-A-LOCK-ULTRA is accepted in Phase 8") unless row["case_id"] == "PILOT-A-LOCK-ULTRA"
abort("Invalid overall_decision: #{row['overall_decision']}") unless DECISIONS.include?(row["overall_decision"])
missing_dimensions = DIMENSIONS.select { |field| row[field].to_s.strip.empty? }
abort("Missing review dimensions: #{missing_dimensions.join(', ')}") unless missing_dimensions.empty?
reviewer = row["reviewer"].to_s.strip
abort("Human reviewer is required") if reviewer.empty? || reviewer.match?(/codex|openai|assistant|ai\b/i)

campaign_path = File.join(REGISTRY, "campaigns", "PILOT-A-LOCK-ULTRA.yaml")
campaign = YAML.safe_load(File.read(campaign_path), permitted_classes: [Date, Time], aliases: true)
decision = row["overall_decision"]
now = Time.now.utc.iso8601

if decision == "APPROVE"
  campaign["approval"]["final_human_delivery"] = {"status" => "APPROVED", "approved_by" => reviewer, "approved_at" => now, "source" => File.expand_path(csv_path)}
  campaign["approval"]["final_copy"]["status"] = "APPROVED"
  campaign["approval"]["final_copy"]["approved_by"] = reviewer
  campaign["approval"]["final_copy"]["approved_at"] = now
  campaign["visual_delivery"]["status"] = "VISUAL_DELIVERABLE"
  campaign["send_boundary"]["content_approved"] = true
else
  campaign["approval"]["final_human_delivery"] = {"status" => decision, "approved_by" => reviewer, "approved_at" => now, "source" => File.expand_path(csv_path), "reason" => row["human_reason"]}
  campaign["visual_delivery"]["status"] = "CANDIDATE_REVISION_REQUIRED"
end

event = {
  "event_id" => "PHASE8-LOCK-FINAL-#{Time.now.utc.strftime('%Y%m%dT%H%M%SZ')}",
  "case_id" => row["case_id"],
  "decision" => decision,
  "dimensions" => DIMENSIONS.to_h { |field| [field, row[field]] },
  "human_reason" => row["human_reason"],
  "reviewer" => reviewer,
  "reviewed_at" => row["reviewed_at"].to_s.empty? ? now : row["reviewed_at"],
  "source_csv" => File.expand_path(csv_path),
  "applied" => apply
}

unless apply
  puts JSON.pretty_generate(event)
  warn "Dry run only. Re-run with --apply to write the campaign registry."
  exit 0
end

File.write(campaign_path, YAML.dump(campaign))
ledger_path = File.join(REGISTRY, "approvals", "approval_ledger.jsonl")
File.open(ledger_path, "a") { |file| file.puts(JSON.generate(event)) }
system("ruby", File.join(ROOT, "production_readiness", "evaluate_readiness.rb")) || abort("Readiness evaluation failed")
system("ruby", File.join(ROOT, "production_readiness", "build_review_pages.rb")) || abort("Review-page rebuild failed")
puts "Applied #{decision} for PILOT-A-LOCK-ULTRA by #{reviewer}."
