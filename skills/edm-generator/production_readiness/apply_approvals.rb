#!/usr/bin/env ruby
# frozen_string_literal: true

require "yaml"
require "json"
require "csv"
require "date"
require "time"
require "fileutils"
require "digest"

ROOT = File.expand_path("..", __dir__)
REGISTRY = File.join(ROOT, "production_registry")
QUEUE_PATH = File.join(REGISTRY, "approvals", "pending_approvals.yaml")
LEDGER_PATH = File.join(REGISTRY, "approvals", "approval_ledger.jsonl")
HISTORY_DIR = File.join(REGISTRY, "approvals", "history")
ALLOWED_DECISIONS = %w[APPROVE MINOR_REVISION MAJOR_REVISION REJECT].freeze

abort("Usage: ruby production_readiness/apply_approvals.rb decisions.csv [--apply]") unless ARGV[0]
csv_path = File.expand_path(ARGV[0])
apply = ARGV.include?("--apply")
abort("CSV not found: #{csv_path}") unless File.file?(csv_path)

queue = YAML.safe_load(File.read(QUEUE_PATH), permitted_classes: [Date, Time], aliases: true)
queue_by_id = queue.fetch("items").to_h { |item| [item.fetch("approval_id"), item] }
existing_keys = if File.file?(LEDGER_PATH)
                  File.readlines(LEDGER_PATH, chomp: true).reject(&:empty?).map { |line| JSON.parse(line).fetch("audit_key") }
                else
                  []
                end

def locate_selector(node, selector)
  case node
  when Array
    match = node.find { |item| item.is_a?(Hash) && selector.all? { |key, value| item[key.to_s] == value } }
    return match if match
    node.each do |item|
      found = locate_selector(item, selector)
      return found if found
    end
  when Hash
    node.each_value do |value|
      found = locate_selector(value, selector)
      return found if found
    end
  end
  nil
end

def dig_parent(node, path)
  keys = path.split(".")
  leaf = keys.pop
  parent = keys.reduce(node) do |memo, key|
    abort("Invalid target path #{path}") unless memo.is_a?(Hash) && memo.key?(key)
    memo[key]
  end
  abort("Invalid target path #{path}") unless parent.is_a?(Hash) && parent.key?(leaf)
  [parent, leaf]
end

def status_for(decision, target, current)
  case decision
  when "APPROVE" then target.fetch("approve_status", "APPROVED")
  when "REJECT" then "REJECTED"
  when "MINOR_REVISION", "MAJOR_REVISION" then current == "INTERNAL_ONLY" || current == "UNKNOWN" ? "UNKNOWN" : "DRAFT"
  else abort("Unsupported decision: #{decision}")
  end
end

def parse_modifications(raw)
  return {} if raw.to_s.strip.empty?
  JSON.parse(raw)
rescue JSON::ParserError
  abort("Revision requires modified_value as a JSON object: {\"products/file.yaml#path.to.value\":\"new value\"}")
end

rows = CSV.read(csv_path, headers: true).map(&:to_h).select { |row| !row["human_decision"].to_s.strip.empty? }
abort("No completed human decisions in #{csv_path}") if rows.empty?

operations = []
rows.each do |row|
  id = row.fetch("approval_id")
  item = queue_by_id[id] || abort("Unknown approval_id: #{id}")
  abort("#{id} is not active in Phase 8") unless queue.fetch("active_human_approval_ids").include?(id)
  abort("#{id} must be applied with apply_phase8_visual_review.rb so all five dimensions are preserved") if id == "APR-LOCK-FINAL"
  decision = row.fetch("human_decision").to_s.strip
  abort("Invalid decision for #{id}: #{decision}") unless ALLOWED_DECISIONS.include?(decision)
  reviewer = row.fetch("reviewer", "").to_s.strip
  abort("Named human reviewer required for #{id}") if reviewer.empty? || reviewer.match?(/codex|openai|assistant|ai\b/i)
  decision_at = row.fetch("decision_at", "").to_s.strip
  abort("decision_at required for #{id}") if decision_at.empty?
  Time.iso8601(decision_at)
  evidence_note = row.fetch("evidence_note", "").to_s.strip
  if decision == "APPROVE" && item["requires_evidence_note"] && evidence_note.empty?
    abort("#{id} requires evidence_note before Approve")
  end
  audit_key = Digest::SHA256.hexdigest([id, decision, reviewer, decision_at].join("|"))
  next if existing_keys.include?(audit_key)
  operations << {"row" => row, "item" => item, "decision" => decision, "reviewer" => reviewer, "decision_at" => decision_at, "evidence_note" => evidence_note, "audit_key" => audit_key}
end

abort("All supplied decisions are already present in the audit ledger") if operations.empty?

preview = operations.map do |op|
  {"approval_id" => op["item"]["approval_id"], "decision" => op["decision"], "reviewer" => op["reviewer"], "targets" => op["item"]["targets"].length}
end
puts JSON.pretty_generate({"mode" => apply ? "APPLY" : "DRY_RUN", "operations" => preview})
exit(0) unless apply

FileUtils.mkdir_p(HISTORY_DIR)
operations.each do |op|
  item = op.fetch("item")
  modifications = parse_modifications(op.dig("row", "modified_value"))
  grouped_targets = item.fetch("targets").group_by { |target| target.fetch("file") }
  audit_changes = []
  grouped_targets.each do |relative_file, targets|
    full_path = File.join(REGISTRY, relative_file)
    abort("Registry target missing: #{full_path}") unless File.file?(full_path)
    document = YAML.safe_load(File.read(full_path), permitted_classes: [Date, Time], aliases: true)
    timestamp = Time.iso8601(op["decision_at"]).utc.strftime("%Y%m%dT%H%M%SZ")
    safe_id = item.fetch("approval_id").gsub(/[^A-Za-z0-9_-]/, "_")
    safe_file = File.basename(relative_file, ".yaml")
    before_path = File.join(HISTORY_DIR, "#{timestamp}_#{safe_id}_#{safe_file}_before.yaml")
    after_path = File.join(HISTORY_DIR, "#{timestamp}_#{safe_id}_#{safe_file}_after.yaml")
    File.write(before_path, YAML.dump(document))
    targets.each do |target|
      base = target["selector"] ? locate_selector(document, target.fetch("selector")) : document
      abort("Selector not found for #{item['approval_id']}: #{target['selector']}") unless base
      parent, leaf = dig_parent(base, target.fetch("path"))
      previous = parent[leaf]
      new_status = status_for(op.fetch("decision"), target, previous)
      parent[leaf] = new_status
      if leaf == "status"
        parent["approved_by"] = op.fetch("reviewer") if op.fetch("decision") == "APPROVE"
        parent["approved_at"] = op.fetch("decision_at") if op.fetch("decision") == "APPROVE"
      end
      audit_changes << {"file" => relative_file, "path" => target.fetch("path"), "selector" => target["selector"], "previous_value" => previous, "new_value" => new_status}
    end
    if %w[MINOR_REVISION MAJOR_REVISION].include?(op.fetch("decision"))
      modifications.each do |qualified_path, value|
        file_key, value_path = qualified_path.split("#", 2)
        next unless file_key == relative_file
        parent, leaf = dig_parent(document, value_path)
        previous = parent[leaf]
        parent[leaf] = value
        audit_changes << {"file" => relative_file, "path" => value_path, "previous_value" => previous, "new_value" => value}
      end
    end
    File.write(full_path, YAML.dump(document))
    File.write(after_path, YAML.dump(document))
  end
  ledger_entry = {
    "audit_key" => op.fetch("audit_key"),
    "approval_id" => item.fetch("approval_id"),
    "decision" => op.fetch("decision"),
    "approved_by" => op.fetch("reviewer"),
    "approved_at" => op.fetch("decision_at"),
    "source" => item.fetch("source"),
    "evidence_note" => op.fetch("evidence_note"),
    "previous_value" => audit_changes.map { |change| change.slice("file", "path", "selector", "previous_value") },
    "new_value" => audit_changes.map { |change| change.slice("file", "path", "selector", "new_value") }
  }
  File.open(LEDGER_PATH, "a") { |file| file.puts(JSON.generate(ledger_entry)) }
end

system("ruby", File.join(__dir__, "evaluate_readiness.rb")) || abort("Readiness re-evaluation failed")
system("ruby", File.join(__dir__, "build_review_pages.rb")) || abort("Review-page rebuild failed")
puts "Applied #{operations.length} human decisions with append-only audit history."
