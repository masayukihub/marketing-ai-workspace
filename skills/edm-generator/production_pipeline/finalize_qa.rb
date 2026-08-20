# frozen_string_literal: true

require "json"
require "yaml"
require "time"
require "date"

ROOT = File.expand_path("..", __dir__)
BROWSER_QA_PATH = File.join(ROOT, "production_output", "browser_qa.json")

abort("Missing browser QA: #{BROWSER_QA_PATH}") unless File.file?(BROWSER_QA_PATH)

browser_qa = JSON.parse(File.read(BROWSER_QA_PATH))
index_path = File.join(ROOT, "production_output", "index.yaml")
index = YAML.safe_load(File.read(index_path), permitted_classes: [Date, Time], aliases: true)

index.fetch("cases").each do |entry|
  case_id = entry.fetch("case_id")
  browser = browser_qa.fetch(case_id)
  output_dir = File.join(ROOT, "production_output", case_id)
  manifest_path = File.join(output_dir, "truth_manifest.yaml")
  manifest = YAML.safe_load(File.read(manifest_path), permitted_classes: [Date, Time], aliases: true)
  manifest.fetch("qa")["browser_qa"] = browser.fetch("status")
  manifest.fetch("qa")["browser_metrics"] = browser.fetch("desktop").slice(
    "totalLengthPx",
    "documentWidthPx",
    "moduleCount",
    "imageCount",
    "brokenImages",
    "ctaCount",
    "runtimeTokens",
    "footerComponent",
    "horizontalOverflow"
  )
  manifest.fetch("qa")["responsive_qa"] = browser.fetch("responsive")
  manifest.fetch("qa")["browser_console_errors"] = browser.fetch("consoleErrors")
  manifest["generated_visual_files"] = browser.fetch("files")
  File.write(manifest_path, YAML.dump(manifest))

  qa = manifest.fetch("qa")
  hard = qa.fetch("hard_rule_checks").map { |name, pass| "- [#{pass ? "x" : " "}] #{name}: #{pass ? "PASS" : "FAIL"}" }.join("\n")
  production = qa.fetch("production_readiness_checks").map { |name, pass| "- [#{pass ? "x" : " "}] #{name}: #{pass ? "PASS" : "OPEN"}" }.join("\n")
  responsive = browser.fetch("responsive").map do |width, row|
    "- #{width}px: #{row.fetch("noHorizontalOverflow") && row.fetch("brokenImages").zero? && row.fetch("ctasMin44px") && row.fetch("ctasSingleLine") ? "PASS" : "FAIL"}"
  end.join("\n")
  File.write(
    File.join(output_dir, "qa_report.md"),
    <<~MD
      # #{case_id} Production QA

      - Production Status: **#{qa.fetch("production_status")}**
      - Browser QA: **#{browser.fetch("status")}**
      - No Fake Content: **#{qa.fetch("no_fake_content") ? "PASS" : "FAIL"}**
      - No Product Redraw: **#{qa.fetch("no_product_redraw") ? "PASS" : "FAIL"}**
      - Rendered size: **#{browser.dig("desktop", "documentWidthPx")} × #{browser.dig("desktop", "totalLengthPx")} px**
      - Runtime ESP tokens still open: **#{browser.dig("desktop", "runtimeTokens")}**

      ## Hard Rules

      #{hard}

      ## Browser / Responsive

      #{responsive}

      - Broken images: #{browser.dig("desktop", "brokenImages")}
      - Console errors: #{browser.fetch("consoleErrors").length}
      - Horizontal overflow: #{browser.dig("desktop", "horizontalOverflow")}

      ## Production Readiness

      #{production}

      ## Open Gates

      #{qa.fetch("production_gaps").map { |gap| "- #{gap}" }.join("\n")}

      Technical rendering is verified. These truth/approval gates keep the package at `#{qa.fetch("production_status")}` and must not be bypassed.
    MD
  )
  entry["browser_qa"] = browser.fetch("status")
  entry["rendered_length_px"] = browser.dig("desktop", "totalLengthPx")
end

index["browser_qa_finalized_at"] = Time.now.utc.iso8601
File.write(index_path, YAML.dump(index))
puts "Finalized browser QA for #{index.fetch("cases").length} cases."
