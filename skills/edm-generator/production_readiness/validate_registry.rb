#!/usr/bin/env ruby
# frozen_string_literal: true

require "yaml"
require "json"
require "date"
require "time"

ROOT = File.expand_path("..", __dir__)
REGISTRY = File.join(ROOT, "production_registry")

def load_yaml(path)
  YAML.safe_load(File.read(path), permitted_classes: [Date, Time], aliases: true)
end

policy = load_yaml(File.join(REGISTRY, "status_policy.yaml"))
issues = []

required_directories = %w[products claims assets campaigns pricing legal footer approvals]
required_directories.each do |name|
  issues << "Missing registry directory: #{name}" unless Dir.exist?(File.join(REGISTRY, name))
end

Dir[File.join(REGISTRY, "products", "*.yaml")].each do |path|
  product = load_yaml(path)
  product.fetch("publication_requirements").each do |row|
    node = row.fetch("path").split(".").reduce(product) { |memo, key| memo.is_a?(Hash) ? memo[key] : nil }
    status = node.is_a?(Hash) ? node["status"] : nil
    issues << "#{path}:#{row['path']} invalid status #{status}" unless policy.fetch("product_field_statuses").include?(status)
  end
end

claims = load_yaml(File.join(REGISTRY, "claims", "claim_registry.yaml"))
claim_ids = claims.fetch("claims").map { |row| row.fetch("claim_id") }
issues << "Duplicate claim IDs" unless claim_ids.uniq.length == claim_ids.length
claims.fetch("claims").each do |claim|
  issues << "#{claim['claim_id']} invalid status #{claim['status']}" unless policy.fetch("claim_statuses").include?(claim["status"])
  issues << "#{claim['claim_id']} invalid type #{claim['claim_type']}" unless claims.fetch("allowed_claim_types").include?(claim["claim_type"])
  issues << "#{claim['claim_id']} invalid requirement level #{claim['requirement_level']}" unless policy.fetch("claim_requirement_levels").include?(claim["requirement_level"])
  issues << "#{claim['claim_id']} is Approved without a human approver" if claim["status"] == "APPROVED" && claim["approved_by"].to_s.strip.empty?
end

mapped = claims.fetch("copy_claim_map").values.flat_map do |roles|
  roles.values.flatten.select { |value| value.is_a?(String) && value.start_with?("CLM-") }
end.uniq
unknown = mapped - claim_ids
issues << "Unknown mapped claim IDs: #{unknown.join(', ')}" unless unknown.empty?

assets = load_yaml(File.join(REGISTRY, "assets", "asset_registry.yaml"))
asset_ids = assets.fetch("assets").map { |row| row.fetch("asset_id") }
issues << "Duplicate asset IDs" unless asset_ids.uniq.length == asset_ids.length
assets.fetch("assets").each do |asset|
  issues << "#{asset['asset_id']} invalid status #{asset['production_status']}" unless policy.fetch("asset_production_statuses").include?(asset["production_status"])
  issues << "#{asset['asset_id']} invalid source authenticity #{asset['source_authenticity']}" unless policy.fetch("asset_source_authenticity_statuses").include?(asset["source_authenticity"])
  issues << "#{asset['asset_id']} invalid design usage scope #{asset['usage_scope']}" unless policy.fetch("asset_usage_scope_statuses").include?(asset["usage_scope"])
  issues << "#{asset['asset_id']} invalid channel scope #{asset['channel_scope']}" unless policy.fetch("asset_usage_scope_statuses").include?(asset["channel_scope"])
  issues << "#{asset['asset_id']} missing file #{asset['source_path']}" unless File.file?(File.join(ROOT, asset.fetch("source_path")))
  issues << "#{asset['asset_id']} is Approved without a human approver" if asset["production_status"] == "APPROVED" && asset["approved_by"].to_s.strip.empty?
end

assets.fetch("required_by_case").each do |case_id, ids|
  missing = ids - asset_ids
  issues << "#{case_id} references missing assets: #{missing.join(', ')}" unless missing.empty?
end

queue = load_yaml(File.join(REGISTRY, "approvals", "pending_approvals.yaml"))
issues << "Approval decision vocabulary changed" unless queue.fetch("decisions") == policy.fetch("human_decisions")
approval_ids = queue.fetch("items").map { |row| row.fetch("approval_id") }
issues << "Duplicate approval IDs" unless approval_ids.uniq.length == approval_ids.length
active_ids = queue.fetch("active_human_approval_ids")
issues << "Unknown active approval IDs: #{(active_ids - approval_ids).join(', ')}" unless (active_ids - approval_ids).empty?
issues << "Phase 8 manual approval KPI exceeds 5" if active_ids.length > 5
issues << "Phase 8 expected 2 active approvals, got #{active_ids.length}" unless active_ids.length == 2
issues << "Phase 8 before/after approval counts inconsistent" unless queue["before_human_approval_items"] == 15 && queue["after_automation_human_approval_items"] == active_ids.length
queue.fetch("resolution_index").each do |approval_id, resolution|
  issues << "Unknown approval resolution ID #{approval_id}" unless approval_ids.include?(approval_id)
  issues << "#{approval_id} invalid resolution #{resolution['resolution']}" unless policy.fetch("approval_resolution_types").include?(resolution["resolution"])
end
queue.fetch("items").each do |item|
  item.fetch("targets").each do |target|
    issues << "#{item['approval_id']} missing target #{target['file']}" unless File.file?(File.join(REGISTRY, target.fetch("file")))
  end
end

snapshot_path = File.join(REGISTRY, "readiness_snapshot.yaml")
issues << "Missing readiness_snapshot.yaml" unless File.file?(snapshot_path)
if File.file?(snapshot_path)
  snapshot = load_yaml(snapshot_path)
  snapshot.fetch("cases").each do |row|
    issues << "#{row['case_id']} has invalid state #{row['overall_status']}" unless %w[INTERNAL_DRAFT DESIGN_READY VISUAL_DELIVERABLE_CANDIDATE VISUAL_DELIVERABLE CONTENT_APPROVED ESP_READY PRODUCTION_READY].include?(row["overall_status"])
    issues << "#{row['case_id']} readiness outside 0–100" unless row["production_readiness_percent"].between?(0, 100)
    issues << "#{row['case_id']} missing output readiness annotation" unless File.file?(File.join(ROOT, "production_output", row.fetch("case_id"), "production_readiness.yaml"))
    if row["overall_status"] == "PRODUCTION_READY"
      %w[CONTENT_APPROVED ESP_READY CHANNEL_SCOPE_APPROVED PRODUCTION_READY].each do |gate|
        issues << "#{row['case_id']} Production Ready without #{gate}" unless row.dig("state_gates", gate)
      end
    end
  end
end

state_machine = load_yaml(File.join(REGISTRY, "state_machine.yaml"))
expected_states = %w[INTERNAL_DRAFT DESIGN_READY VISUAL_DELIVERABLE_CANDIDATE CONTENT_APPROVED ESP_READY PRODUCTION_READY]
issues << "State machine order changed" unless state_machine.fetch("primary_path").map { |row| row.fetch("state") } == expected_states
issues << "Visual gate is not independent from ESP" unless state_machine.dig("independent_gates", "VISUAL_DELIVERABLE", "not_blocked_by").to_a.include?("ESP_RUNTIME_TOKEN")

%w[research/production_readiness_dashboard.html research/manual_approval_queue.html research/phase8_visual_delivery_review.html].each do |relative|
  issues << "Missing review surface: #{relative}" unless File.file?(File.join(ROOT, relative))
end

browser_report_path = File.join(REGISTRY, "browser_qa.json")
issues << "Missing production-readiness browser QA" unless File.file?(browser_report_path)
if File.file?(browser_report_path)
  browser_report = JSON.parse(File.read(browser_report_path))
  issues << "Production-readiness browser QA is #{browser_report['status']}" unless browser_report["status"] == "PASS"
end

ledger_path = File.join(REGISTRY, "approvals", "approval_ledger.jsonl")
if File.file?(ledger_path)
  File.readlines(ledger_path, chomp: true).reject(&:empty?).each_with_index do |line, index|
    JSON.parse(line)
  rescue JSON::ParserError
    issues << "Invalid approval ledger JSON at line #{index + 1}"
  end
end

result = {"status" => issues.empty? ? "PASS" : "FAIL", "issues" => issues, "checked_at" => Time.now.utc.iso8601}
File.write(File.join(REGISTRY, "validation_report.json"), JSON.pretty_generate(result) + "\n")
puts JSON.pretty_generate(result)
exit(issues.empty? ? 0 : 1)
