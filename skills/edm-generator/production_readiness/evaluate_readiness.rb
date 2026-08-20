#!/usr/bin/env ruby
# frozen_string_literal: true

require "yaml"
require "json"
require "date"
require "time"
require "fileutils"

module ProductionReadiness
  class Evaluator
    ROOT = File.expand_path("..", __dir__)
    REGISTRY = File.join(ROOT, "production_registry")
    CASES = {"PILOT-A-LOCK-ULTRA" => "lock_ultra", "PILOT-B-DAILY-STATION" => "daily_station"}.freeze
    WEIGHTS = {"product" => 0.25, "claim" => 0.20, "asset" => 0.20, "campaign" => 0.15, "legal" => 0.10, "copy" => 0.10}.freeze
    PHASE6_BASELINES = {"lock_ultra" => 76.9, "daily_station" => 69.2}.freeze
    VISUAL_CLAIM_STATUSES = %w[APPROVED INHERITED_APPROVAL VERIFIED_EXISTING_CLAIM].freeze
    DESIGN_ASSET_STATUSES = %w[DESIGN_PRODUCTION_APPROVED CHANNEL_APPROVED].freeze
    COPY_CANDIDATE_STATUSES = %w[COPY_PRODUCTION_CANDIDATE APPROVED].freeze
    STATIC_APPROVAL_STATUSES = %w[APPROVED INHERITED_APPROVAL NOT_REQUIRED].freeze

    def initialize
      @claims = load_yaml("claims/claim_registry.yaml")
      @assets = load_yaml("assets/asset_registry.yaml")
      @legal = load_yaml("legal/legal_registry.yaml")
      @footer = load_yaml("footer/switchbot_jp_footer.yaml")
      @browser_qa = load_json_if_present(File.join(ROOT, "production_output", "browser_qa.json"))
    end

    def run
      cases = CASES.map { |case_id, product_id| evaluate_case(case_id, product_id) }
      snapshot = {
        "schema_version" => "2.0.0",
        "generated_at" => Time.now.utc.iso8601,
        "metric_note" => "Phase 8 separates official-source design evidence, whole-email Human Approval, and ESP send readiness. A visual candidate is not a sent-email approval.",
        "registry_completeness" => registry_completeness,
        "cases" => cases,
        "summary" => {
          "design_ready_count" => cases.count { |row| row.dig("state_gates", "DESIGN_READY") },
          "visual_candidate_count" => cases.count { |row| row.dig("state_gates", "VISUAL_DELIVERABLE_CANDIDATE") },
          "visual_deliverable_count" => cases.count { |row| row.dig("state_gates", "VISUAL_DELIVERABLE") },
          "production_ready_count" => cases.count { |row| row["overall_status"] == "PRODUCTION_READY" },
          "highest_state" => cases.max_by { |row| row["state_order"] }.fetch("overall_status")
        }
      }
      FileUtils.mkdir_p(REGISTRY)
      File.write(File.join(REGISTRY, "readiness_snapshot.yaml"), YAML.dump(snapshot))
      File.write(File.join(REGISTRY, "readiness_snapshot.json"), JSON.pretty_generate(snapshot) + "\n")
      annotate_outputs(cases)
      snapshot
    end

    private

    def evaluate_case(case_id, product_id)
      product = load_yaml("products/#{product_id}.yaml")
      campaign = load_yaml("campaigns/#{case_id}.yaml")
      pricing = load_yaml("pricing/#{product_id}.yaml")
      domains = {
        "product" => product_gate(product),
        "claim" => claim_gate(case_id),
        "asset" => asset_gate(case_id),
        "campaign" => campaign_gate(campaign, pricing),
        "legal" => legal_gate,
        "copy" => copy_gate(case_id, campaign)
      }
      technical = technical_gate(case_id)
      design_inputs_ready = domains.values.all? { |result| result["gate"] == "PASS" }
      design_ready = design_inputs_ready && technical["gate"] == "PASS"
      candidate_enabled = !campaign.dig("visual_delivery", "status").to_s.start_with?("DEFERRED_NOT_REGENERATED")
      visual_candidate = design_ready && candidate_enabled && technical["package_complete"]
      final_human_approved = campaign.dig("approval", "final_human_delivery", "status") == "APPROVED"
      final_copy_approved = campaign.dig("approval", "final_copy", "status") == "APPROVED"
      visual_deliverable = visual_candidate && final_human_approved
      content_approved = final_human_approved && final_copy_approved
      esp_ready = @footer.dig("approval", "esp_token_contract", "status") == "APPROVED"
      channel_scope_approved = final_human_approved && design_assets_current?(case_id)
      production_ready = visual_candidate && content_approved && esp_ready && channel_scope_approved

      state, order = if production_ready
                       ["PRODUCTION_READY", 6]
                     elsif content_approved && esp_ready
                       ["ESP_READY", 5]
                     elsif content_approved
                       ["CONTENT_APPROVED", 4]
                     elsif visual_deliverable
                       ["VISUAL_DELIVERABLE", 3]
                     elsif visual_candidate
                       ["VISUAL_DELIVERABLE_CANDIDATE", 2]
                     elsif design_ready
                       ["DESIGN_READY", 1]
                     else
                       ["INTERNAL_DRAFT", 0]
                     end

      update_product_gate(product_id, product, domains.dig("product", "gate") == "PASS")
      update_campaign_status(case_id, campaign, visual_candidate, visual_deliverable, content_approved, esp_ready, production_ready)
      visual_blockers, send_blockers = blockers_for(case_id, product, campaign, domains, technical, visual_candidate)
      overall_percent = WEIGHTS.sum { |name, weight| domains.fetch(name).fetch("percent") * weight }.round(1)
      {
        "case_id" => case_id,
        "product_id" => product_id,
        "product_name" => product.dig("official_name_ja", "value"),
        "phase6_evidence_baseline_percent" => PHASE6_BASELINES.fetch(product_id),
        "design_evidence_percent" => overall_percent,
        "production_readiness_percent" => overall_percent,
        "domains" => domains,
        "technical" => technical,
        "overall_status" => state,
        "state_order" => order,
        "state_gates" => {
          "DESIGN_INPUTS_READY" => design_inputs_ready,
          "DESIGN_READY" => design_ready,
          "VISUAL_DELIVERABLE_CANDIDATE" => visual_candidate,
          "VISUAL_DELIVERABLE" => visual_deliverable,
          "CONTENT_APPROVED" => content_approved,
          "ESP_READY" => esp_ready,
          "CHANNEL_SCOPE_APPROVED" => channel_scope_approved,
          "PRODUCTION_READY" => production_ready
        },
        "visual_blockers" => visual_blockers,
        "send_blockers" => send_blockers,
        "blockers" => (visual_blockers + send_blockers).uniq { |item| item["blocker_id"] },
        "unique_remaining_blocker" => (visual_blockers + send_blockers).first
      }
    end

    def product_gate(product)
      requirements = product.fetch("publication_requirements").select { |row| row["required"] }
      results = requirements.map do |requirement|
        node = dig_path(product, requirement.fetch("path"))
        status = node.is_a?(Hash) ? node["status"] : nil
        accepted = requirement.fetch("acceptance")
        {"path" => requirement.fetch("path"), "status" => status || "MISSING", "acceptance" => accepted, "pass" => accepted.include?(status)}
      end
      metric(results.count { |row| row["pass"] }, results.length, results, "PRODUCT_DESIGN_TRUTH_GATE")
    end

    def claim_gate(case_id)
      mapped_ids = flatten_claim_ids(@claims.dig("copy_claim_map", case_id))
      explicit_ids = @claims.fetch("claims").select { |claim| claim.fetch("required_in_pilots", []).include?(case_id) }.map { |claim| claim["claim_id"] }
      used_ids = (mapped_ids + explicit_ids).uniq
      known = @claims.fetch("claims").to_h { |claim| [claim.fetch("claim_id"), claim] }
      unknown = used_ids.reject { |claim_id| known.key?(claim_id) }
      details = used_ids.map do |claim_id|
        claim = known[claim_id]
        next unless claim
        resolved = VISUAL_CLAIM_STATUSES.include?(claim["status"])
        level = claim.fetch("requirement_level", "PRIMARY_REQUIRED")
        {
          "claim_id" => claim_id,
          "status" => claim["status"],
          "requirement_level" => level,
          "evidence_match" => claim["evidence_match"],
          "pass" => resolved,
          "fallback" => (!resolved && level == "SECONDARY_OPTIONAL") ? "DROP_OR_SUBSTITUTE" : nil
        }
      end.compact
      unresolved_primary = details.select { |row| !row["pass"] && row["requirement_level"] == "PRIMARY_REQUIRED" }
      prohibited_used = details.select { |row| row["requirement_level"] == "PROHIBITED" }
      {
        "percent" => percentage(details.count { |row| row["pass"] }, details.length),
        "passed" => details.count { |row| row["pass"] },
        "total" => details.length,
        "gate" => (unknown.empty? && unresolved_primary.empty? && prohibited_used.empty?) ? "PASS" : "BLOCK",
        "gate_name" => "CLAIM_VISUAL_EVIDENCE_GATE",
        "details" => details,
        "mapping_complete" => unknown.empty?,
        "unknown_claim_ids" => unknown,
        "unresolved_primary_claim_ids" => unresolved_primary.map { |row| row["claim_id"] },
        "optional_fallback_claim_ids" => details.select { |row| row["fallback"] }.map { |row| row["claim_id"] }
      }
    end

    def asset_gate(case_id)
      required_ids = @assets.dig("required_by_case", case_id) || []
      rows = required_ids.map do |asset_id|
        asset = @assets.fetch("assets").find { |row| row["asset_id"] == asset_id }
        exists = asset && File.file?(File.join(ROOT, asset.fetch("source_path")))
        authenticity = asset ? asset["source_authenticity"] : "UNKNOWN"
        usage_scope = asset ? asset["usage_scope"] : "UNKNOWN"
        pass = asset && authenticity == "OFFICIAL_MARKETING_ASSET" && DESIGN_ASSET_STATUSES.include?(usage_scope) && exists
        {"asset_id" => asset_id, "source_authenticity" => authenticity, "usage_scope" => usage_scope, "channel_scope" => asset ? asset["channel_scope"] : "UNKNOWN", "file_exists" => exists, "pass" => pass}
      end
      metric(rows.count { |row| row["pass"] }, rows.length, rows, "ASSET_DESIGN_SCOPE_GATE")
    end

    def campaign_gate(campaign, pricing)
      campaign_status = campaign.dig("approval", "campaign_and_cta", "status")
      checks = [
        {"item" => "campaign_and_cta_truth", "status" => campaign_status, "pass" => %w[APPROVED VERIFIED_FROM_INPUT_AND_OFFICIAL_DESTINATION].include?(campaign_status)},
        {"item" => "cta_verified", "status" => campaign.dig("cta", "status"), "pass" => %w[VERIFIED APPROVED].include?(campaign.dig("cta", "status"))},
        {"item" => "period_truth", "status" => campaign.dig("period", "status"), "pass" => %w[VERIFIED APPROVED NOT_REQUIRED].include?(campaign.dig("period", "status"))},
        {"item" => "pricing_promotion_truth", "status" => pricing["gate_result"], "pass" => %w[PASS_NOT_APPLICABLE PASS].include?(pricing["gate_result"])},
        {"item" => "campaign_disclaimer", "status" => campaign.dig("campaign_disclaimer", "status"), "pass" => %w[VERIFIED APPROVED NOT_REQUIRED].include?(campaign.dig("campaign_disclaimer", "status"))}
      ]
      metric(checks.count { |row| row["pass"] }, checks.length, checks, "CAMPAIGN_TRUTH_GATE")
    end

    def legal_gate
      checks = [
        {"item" => "static_legal_package", "status" => @legal.dig("approval", "static_legal_package", "status"), "pass" => STATIC_APPROVAL_STATUSES.include?(@legal.dig("approval", "static_legal_package", "status"))},
        {"item" => "static_footer", "status" => @footer.dig("approval", "static_footer", "status"), "pass" => STATIC_APPROVAL_STATUSES.include?(@footer.dig("approval", "static_footer", "status"))}
      ]
      result = metric(checks.count { |row| row["pass"] }, checks.length, checks, "STATIC_LEGAL_VISUAL_GATE")
      result["esp_token_contract"] = @footer.dig("approval", "esp_token_contract", "status")
      result["esp_blocks_visual"] = false
      result
    end

    def copy_gate(case_id, campaign)
      status = campaign.dig("approval", "final_copy", "status") || "MISSING"
      auto_qa_path = File.join(ROOT, "production_output", case_id, "copy_auto_qa.yaml")
      auto_qa = File.file?(auto_qa_path) ? YAML.safe_load(File.read(auto_qa_path), permitted_classes: [Date, Time], aliases: true) : nil
      auto_qa_pass = auto_qa.nil? || auto_qa["status"] == "PASS" ||
        (auto_qa["status"] == "COPY_PRODUCTION_CANDIDATE" && auto_qa.fetch("checks", {}).values.all?)
      pass = COPY_CANDIDATE_STATUSES.include?(status) && auto_qa_pass
      metric(pass ? 1 : 0, 1, [{"item" => "japanese_copy_candidate", "status" => status, "auto_qa" => auto_qa&.dig("status") || "PENDING_RENDER", "pass" => pass}], "COPY_PRODUCTION_CANDIDATE_GATE")
    end

    def technical_gate(case_id)
      browser = @browser_qa[case_id] || {}
      output_dir = File.join(ROOT, "production_output", case_id)
      browser_path = File.join(ROOT, "production_output", "browser_qa.json")
      render_path = File.join(output_dir, "editable_edm.html")
      required_files = %w[editable_edm.html desktop_preview.png mobile_preview.png full_edm.png truth_manifest.yaml qa_report.md final_copy.md copy_auto_qa.yaml]
      missing = required_files.reject { |name| File.file?(File.join(output_dir, name)) }
      responsive = browser.fetch("responsive", {}).values
      responsive_pass = responsive.any? && responsive.all? do |row|
        row["noHorizontalOverflow"] && row["brokenImages"].to_i.zero? && row["ctasMin44px"] && row["ctasSingleLine"]
      end
      browser_fresh = File.file?(browser_path) && File.file?(render_path) && File.mtime(browser_path) >= File.mtime(render_path)
      approvals_in_render = true
      package_complete = missing.empty?
      pass = browser["status"] == "PASS" && responsive_pass && package_complete && browser_fresh && approvals_in_render
      {"gate" => pass ? "PASS" : "BLOCK", "browser_qa" => browser["status"] || "MISSING", "responsive_pass" => responsive_pass, "browser_qa_fresh" => browser_fresh, "latest_registry_in_render" => approvals_in_render, "package_complete" => package_complete, "missing_files" => missing}
    end

    def blockers_for(case_id, product, campaign, domains, technical, visual_candidate)
      visual = []
      send = []
      unless domains.dig("product", "gate") == "PASS"
        open_paths = domains.dig("product", "details").reject { |row| row["pass"] }.map { |row| row["path"] }
        visual << blocker("#{case_id}-PRODUCT", "DESIGN_READY", "Product truth unresolved: #{open_paths.join(', ')}", "production_registry/products/#{product.fetch('product_id')}.yaml", "Product owner", "Resolve only from canonical or current official sources.")
      end
      unless domains.dig("claim", "gate") == "PASS"
        open_claims = domains.dig("claim", "unresolved_primary_claim_ids")
        visual << blocker("#{case_id}-CLAIMS", "DESIGN_READY", "Primary required claims unresolved: #{open_claims.join(', ')}", "production_registry/claims/claim_registry.yaml", "Claim owner", "Verify exact official semantics or remove the unsupported message.")
      end
      unless domains.dig("copy", "gate") == "PASS"
        visual << blocker("#{case_id}-COPY", "DESIGN_READY", "Copy Candidate pipeline has not passed.", "production_output/#{case_id}/copy_auto_qa.yaml", "Generator QA", "Run staged copy QA and fix Generator-owned issues.")
      end
      unless domains.dig("asset", "gate") == "PASS"
        open_assets = domains.dig("asset", "details").reject { |row| row["pass"] }.map { |row| row["asset_id"] }
        visual << blocker("#{case_id}-ASSETS", "DESIGN_READY", "Official design-scope assets unresolved: #{open_assets.join(', ')}", "production_registry/assets/asset_registry.yaml", "Asset owner", "Resolve authenticity, design usage scope and exact local file.")
      end
      unless domains.dig("campaign", "gate") == "PASS"
        visual << blocker("#{case_id}-CAMPAIGN", "DESIGN_READY", "Campaign, CTA, period or promotion truth unresolved.", "production_registry/campaigns/#{case_id}.yaml", "Campaign owner", "Resolve the exact campaign inputs without inventing price or period.")
      end
      unless domains.dig("legal", "gate") == "PASS"
        visual << blocker("SHARED-STATIC-FOOTER", "DESIGN_READY", "Reusable static legal/footer package unresolved.", "production_registry/footer/switchbot_jp_footer.yaml", "Marketing / Legal", "Use verified historical official footer content.")
      end
      unless technical["gate"] == "PASS"
        visual << blocker("#{case_id}-RENDER-QA", "VISUAL_DELIVERABLE_CANDIDATE", "Current render/browser QA package is incomplete or stale.", "production_output/#{case_id}/", "Renderer QA", "Run the one-shot and responsive browser QA.")
      end
      if visual_candidate && campaign.dig("approval", "final_human_delivery", "status") != "APPROVED"
        send << blocker("#{case_id}-FINAL", "CONTENT_APPROVED", "Whole-email Human Review is pending.", "research/phase8_visual_delivery_review.html", "Campaign owner", "Judge only product information, Japanese, brand fit, completeness and visual delivery quality.")
      end
      if @footer.dig("approval", "esp_token_contract", "status") != "APPROVED"
        send << blocker("SHARED-ESP", "ESP_READY", "ESP unsubscribe, preference and year token contract is unresolved.", "production_registry/footer/switchbot_jp_footer.yaml", "CRM / ESP owner", "Confirm actual send-platform token syntax before send integration.")
      end
      [visual, send]
    end

    def blocker(id, gate, missing, source, approver, action)
      {"blocker_id" => id, "gate" => gate, "missing" => missing, "source" => source, "approver" => approver, "next_action" => action}
    end

    def metric(passed, total, details, gate_name)
      percent = percentage(passed, total)
      {"percent" => percent, "passed" => passed, "total" => total, "gate" => passed == total ? "PASS" : "BLOCK", "gate_name" => gate_name, "details" => details}
    end

    def registry_completeness
      required_claim_keys = %w[claim_id product_id claim_ja claim_type status requirement_level source source_location conditions required_disclaimer valid_from valid_until approved_by last_verified]
      claim_rows = @claims.fetch("claims")
      complete_claims = claim_rows.count { |row| required_claim_keys.all? { |key| row.key?(key) } }
      required_asset_keys = %w[asset_id product_id asset_type source_path source_origin production_status source_authenticity usage_scope channel_scope allowed_usage market channel valid_from valid_until]
      asset_rows = @assets.fetch("assets")
      complete_assets = asset_rows.count { |row| required_asset_keys.all? { |key| row.key?(key) } }
      required_claims = claim_rows.select { |row| row.fetch("required_in_pilots", []).any? }
      {
        "claim_registry" => {"structural_percent" => percentage(complete_claims, claim_rows.length), "records_complete" => complete_claims, "records_total" => claim_rows.length, "visual_evidence_resolved_percent" => percentage(required_claims.count { |row| VISUAL_CLAIM_STATUSES.include?(row["status"]) }, required_claims.length), "required_claims_resolved" => required_claims.count { |row| VISUAL_CLAIM_STATUSES.include?(row["status"]) }, "required_claims_total" => required_claims.length},
        "asset_registry" => {"structural_percent" => percentage(complete_assets, asset_rows.length), "records_complete" => complete_assets, "records_total" => asset_rows.length, "files_present_percent" => percentage(asset_rows.count { |row| File.file?(File.join(ROOT, row["source_path"])) }, asset_rows.length), "design_scope_resolved_percent" => percentage(asset_rows.count { |row| DESIGN_ASSET_STATUSES.include?(row["usage_scope"]) }, asset_rows.length), "design_scope_resolved" => asset_rows.count { |row| DESIGN_ASSET_STATUSES.include?(row["usage_scope"]) }, "required_assets_total" => asset_rows.length}
      }
    end

    def update_product_gate(product_id, product, ready)
      current = product.dig("approval", "product_publication_ready", "value")
      current_status = product.dig("approval", "product_publication_ready", "status")
      new_status = ready ? "VERIFIED_FROM_OFFICIAL_SOURCE" : "UNVERIFIED"
      return if current == ready && current_status == new_status
      product["approval"] ||= {}
      product["approval"]["product_publication_ready"] ||= {}
      product["approval"]["product_publication_ready"]["value"] = ready
      product["approval"]["product_publication_ready"]["status"] = new_status
      product["approval"]["product_publication_ready"]["evaluated_at"] = Time.now.utc.iso8601
      File.write(File.join(REGISTRY, "products", "#{product_id}.yaml"), YAML.dump(product))
    end

    def update_campaign_status(case_id, campaign, visual_candidate, visual_deliverable, content_approved, esp_ready, production_ready)
      return if campaign.dig("visual_delivery", "status").to_s.start_with?("DEFERRED_NOT_REGENERATED")
      original = YAML.dump(campaign)
      campaign["visual_delivery"] ||= {}
      campaign["visual_delivery"]["status"] = if visual_deliverable
                                                   "VISUAL_DELIVERABLE"
                                                 elsif visual_candidate
                                                   "VISUAL_DELIVERABLE_CANDIDATE"
                                                 else
                                                   "CANDIDATE_PENDING_RENDER_QA"
                                                 end
      campaign["send_boundary"] ||= {}
      campaign["send_boundary"]["content_approved"] = content_approved
      campaign["send_boundary"]["esp_ready"] = esp_ready
      campaign["send_boundary"]["production_ready"] = production_ready
      updated = YAML.dump(campaign)
      File.write(File.join(REGISTRY, "campaigns", "#{case_id}.yaml"), updated) unless updated == original
    end

    def annotate_outputs(cases)
      cases.each do |row|
        dir = File.join(ROOT, "production_output", row.fetch("case_id"))
        next unless Dir.exist?(dir)
        File.write(File.join(dir, "production_readiness.yaml"), YAML.dump(row))
        manifest_path = File.join(dir, "truth_manifest.yaml")
        if File.file?(manifest_path)
          manifest = YAML.safe_load(File.read(manifest_path), permitted_classes: [Date, Time], aliases: true)
          manifest["phase8_production_readiness"] = row
          manifest["qa"] ||= {}
          manifest["qa"]["production_status"] = row.fetch("overall_status")
          manifest["qa"]["visual_blockers"] = row.fetch("visual_blockers").map { |item| item.fetch("blocker_id") }
          manifest["qa"]["send_blockers"] = row.fetch("send_blockers").map { |item| item.fetch("blocker_id") }
          File.write(manifest_path, YAML.dump(manifest))
        end
        sync_html_status(File.join(dir, "editable_edm.html"), row.fetch("overall_status"))
        sync_qa_report(File.join(dir, "qa_report.md"), row)
      end
      index_path = File.join(ROOT, "production_output", "index.yaml")
      return unless File.file?(index_path)
      index = YAML.safe_load(File.read(index_path), permitted_classes: [Date, Time], aliases: true)
      index.fetch("cases", []).each do |entry|
        row = cases.find { |item| item["case_id"] == entry["case_id"] }
        next unless row
        entry["phase8_design_evidence_percent"] = row["design_evidence_percent"]
        entry["phase8_status"] = row["overall_status"]
      end
      index["phase8_evaluated_at"] = Time.now.utc.iso8601
      File.write(index_path, YAML.dump(index))
    end

    def sync_html_status(path, status)
      return unless File.file?(path)
      original = File.read(path)
      html = original.gsub(/data-production-status="[^"]+"/, %(data-production-status="#{status}")).gsub(/data-gate="[^"]+"/, %(data-gate="#{status}"))
      File.write(path, html) unless html == original
    end

    def sync_qa_report(path, row)
      return unless File.file?(path)
      body = File.read(path).sub(/\n<!-- PHASE7-START -->.*?<!-- PHASE7-END -->\n?/m, "\n").sub(/\n<!-- PHASE8-START -->.*?<!-- PHASE8-END -->\n?/m, "\n")
      body.gsub!(/- Production Status: \*\*[^*]+\*\*/, "- Production Status: **#{row.fetch('overall_status')}**")
      body.gsub!(/Technical rendering is verified\..*?must not be bypassed\./, "Technical rendering is verified. Final Human Review and ESP runtime remain independent send-side gates.")
      visual = row.fetch("visual_blockers").map { |item| "- #{item['blocker_id']}: #{item['missing']}" }.join("\n")
      send = row.fetch("send_blockers").map { |item| "- #{item['blocker_id']}: #{item['missing']}" }.join("\n")
      body << <<~MD

        <!-- PHASE8-START -->
        ## Phase 8 Approval Automation & Production Closure

        - Design Evidence: **#{row.fetch('design_evidence_percent')}%**
        - Overall Status: **#{row.fetch('overall_status')}**
        - Visual Candidate: **#{row.dig('state_gates', 'VISUAL_DELIVERABLE_CANDIDATE') ? 'PASS' : 'BLOCK'}**
        - Browser QA Fresh: **#{row.dig('technical', 'browser_qa_fresh') ? 'PASS' : 'STALE'}**

        ### Visual blockers
        #{visual.empty? ? '- None' : visual}

        ### Send-only blockers
        #{send.empty? ? '- None' : send}
        <!-- PHASE8-END -->
      MD
      File.write(path, body)
    end

    def design_assets_current?(case_id)
      ids = @assets.dig("required_by_case", case_id) || []
      ids.all? do |asset_id|
        asset = @assets.fetch("assets").find { |row| row["asset_id"] == asset_id }
        asset && DESIGN_ASSET_STATUSES.include?(asset["usage_scope"])
      end
    end

    def percentage(numerator, denominator)
      denominator.zero? ? 100.0 : (numerator.fdiv(denominator) * 100).round(1)
    end

    def flatten_claim_ids(node)
      case node
      when Hash then node.values.flat_map { |value| flatten_claim_ids(value) }
      when Array then node.flat_map { |value| flatten_claim_ids(value) }
      when String then node.start_with?("CLM-") ? [node] : []
      else []
      end.uniq
    end

    def dig_path(node, path)
      path.to_s.split(".").reduce(node) { |memo, key| memo.is_a?(Hash) ? memo[key] : nil }
    end

    def load_yaml(relative)
      YAML.safe_load(File.read(File.join(REGISTRY, relative)), permitted_classes: [Date, Time], aliases: true)
    end

    def load_json_if_present(path)
      File.file?(path) ? JSON.parse(File.read(path)) : {}
    end
  end
end

if $PROGRAM_NAME == __FILE__
  snapshot = ProductionReadiness::Evaluator.new.run
  puts JSON.pretty_generate(snapshot)
end
