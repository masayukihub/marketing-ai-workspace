#!/usr/bin/env ruby
require "yaml"
require "uri"
require_relative "../core/dependency_context"

ROOT = File.expand_path("../..", __dir__)
cases = %w[P01 P02 P03 P04]
results = []
browser_qa_path = File.join(ROOT, "renderer", "outputs", "browser_qa.yaml")
browser_qa = File.file?(browser_qa_path) ? YAML.load_file(browser_qa_path).fetch("results") : {}

cases.each do |pilot_id|
  dir = File.join(ROOT, "pilot", pilot_id)
  campaign = YAML.load_file(File.join(dir, "truth_pack", "campaign_truth.yaml"))
  manifest = YAML.load_file(File.join(dir, "truth_pack", "asset_manifest.yaml"))
  gate = campaign.fetch("verification_status")
  html_name = %w[READY CONDITIONAL].include?(gate) ? "editable_edm.html" : "wireframe.html"
  html_path = File.join(dir, html_name)
  html = File.read(html_path)
  campaign_brief = YAML.load_file(File.join(dir, "campaign_brief.yaml"))
  dependency_ok = begin
    PilotRenderer::DependencyContext.new(root: ROOT, pilot_id: pilot_id).assert_matches!(
      template: campaign_brief.fetch("selected_template"),
      module_ids: campaign_brief.fetch("module_sequence", []).map { |item| item.fetch("module_id") }
    )
  rescue StandardError
    false
  end
  status_values = Dir[File.join(dir, "truth_pack", "*.yaml")].flat_map do |path|
    File.read(path).scan(/^\s*status:\s*(\S+)/).flatten
  end
  checks = {
    "html_exists" => File.file?(html_path),
    "viewport_meta" => html.include?("name=\"viewport\""),
    "no_dummy_url" => !html.match?(/href=[\"'](?:#|javascript:|about:blank)/i),
    "no_placeholder_lorem" => !html.match?(/lorem ipsum|dummy url/i),
    "images_have_alt" => html.scan(/<img\b[^>]*>/i).all? { |tag| tag.include?("alt=") },
    "images_have_dimensions" => html.scan(/<img\b[^>]*>/i).all? { |tag| tag.include?("width=") && tag.include?("height=") },
    "gate_label_present" => html.include?(gate) || html.include?("BLOCKED") || html.include?("社内検証用"),
    "frozen_dependencies_resolved" => dependency_ok,
    "truth_and_gate_status_vocabulary" => status_values.all? { |value| %w[VERIFIED UNVERIFIED MISSING NOT_REQUIRED READY CONDITIONAL BLOCKED].include?(value) },
    "production_assets_not_ai_redrawn" => manifest.fetch("assets").select { |asset| asset["approved"] == true }.all? { |asset| asset["source_path"].to_s.start_with?("renderer/assets/official/") }
  }
  if %w[READY CONDITIONAL].include?(gate)
    checks["desktop_baseline_600"] = html.include?("max-width: 600px")
    checks["real_cta"] = html.match?(/href=\"https:\/\/www\.switchbot\.jp\//)
    checks["critical_local_assets_exist"] = manifest.fetch("assets").select { |a| a["status"] == "VERIFIED" && a["source_path"].to_s.start_with?("renderer/") }.all? { |a| File.file?(File.join(ROOT, a["source_path"])) }
  else
    checks["blocked_has_no_editable_edm"] = !File.exist?(File.join(dir, "editable_edm.html"))
  end
  results << [pilot_id, gate, checks]
end

report = ["# Phase 5 Static Render QA", "", "Generated: 2026-08-19", ""]
results.each do |pilot_id, gate, checks|
  report << "## #{pilot_id} — #{gate}"
  report << ""
  checks.each { |name, pass| report << "- [#{pass ? "x" : " "}] #{name}: #{pass ? "PASS" : "FAIL"}" }
  report << ""
  browser = browser_qa[pilot_id]
  browser_lines = if browser
    [
      "Browser QA: **#{browser.fetch("status")}**",
      "- Console errors: #{browser.fetch("console_errors")}",
      "- Broken images: #{browser.fetch("broken_images")}",
      "- Horizontal overflow at 320/375/390/414: #{browser.fetch("horizontal_overflow_viewports").empty? ? "none" : browser.fetch("horizontal_overflow_viewports").join(", ")}",
      "- Full screenshot: `#{browser.fetch("full_page_screenshot")}`"
    ]
  else
    ["Browser QA: pending screenshot run."]
  end
  File.write(File.join(ROOT, "pilot", pilot_id, "render_qa.md"), (["# #{pilot_id} Render QA", "", "Gate: **#{gate}**", ""] + checks.map { |name, pass| "- #{name}: #{pass ? "PASS" : "FAIL"}" } + [""] + browser_lines).join("\n"))
end
File.write(File.join(ROOT, "renderer", "outputs", "static_qa.md"), report.join("\n"))

failed = results.flat_map { |pilot_id, _, checks| checks.select { |_, pass| !pass }.keys.map { |name| "#{pilot_id}:#{name}" } }
puts failed.empty? ? "Static QA PASS" : "Static QA FAIL: #{failed.join(", ")}"
exit(failed.empty? ? 0 : 1)
