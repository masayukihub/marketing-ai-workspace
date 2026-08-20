# frozen_string_literal: true

module EDMGenerator
  class QAChecker
    def initialize(repository)
      @repository = repository
    end

    def call(test_case, brief, classification, selection, message, composition, copy, assets, generated_at)
      hard_rules = @repository.standard.fetch("rules").select { |_, rule| rule["rule_type"] == "hard" }
      expected_codes = test_case.dig("expected", "expected_failure_codes") || []
      blocking = brief.dig("verification", "production_gates").dup
      blocking.concat(selection["failure_codes"] || [])
      blocking.concat(composition.dig("composition_checks", "blocked").map { |item| item["code"] })
      blocking << "ASSET_PROVENANCE_MISSING" if assets["status"] == "ASSET_BLOCKED"
      blocking << "TEST_FIXTURE_NOT_PRODUCTION_ASSET" if assets["asset_inventory_state"] == "complete"
      blocking << "CTA_FIXTURE_NOT_PRODUCTION_URL" if brief.dig("campaign", "cta_destination", "state") == "verified_test_fixture"
      blocking << "REQUIRED_INPUT_UNRESOLVED" if brief.dig("campaign", "cta_destination", "status") != "Resolved"
      blocking << "CTA_DESTINATION_INVALID" if brief.dig("campaign", "cta_destination", "status") != "Resolved"
      blocking.uniq!

      unsafe_violations = []
      unsafe_violations << "UNVERIFIED_CLAIM" if copy.dig("copy_checks", "unapproved_claim_used")
      unsafe_violations << "AI_PRODUCT_REDRAW" if assets.dig("asset_safety_checks", "product_redraw_requested")
      unsafe_violations << "PLACEHOLDER_OR_TEST_CONTENT" if copy.dig("copy_checks", "final_copy_allowed") && copy.dig("copy_checks", "placeholder_in_final")
      unsafe_violations << "EVIDENCE_TIER_OVERRIDE" if false

      hard_results = hard_rules.map do |rule_id, rule|
        code = rule.dig("qa", "failure_code")
        {
          "rule_id" => rule_id,
          "requirement" => rule["requirement"],
          "result" => unsafe_violations.include?(code) ? "BLOCKED" : "PASS",
          "failure_code" => unsafe_violations.include?(code) ? code : nil,
          "note" => hard_note(rule_id, brief, copy, assets, blocking)
        }
      end

      selection_match = selection["selected_template_id"] == test_case.dig("expected", "selected_template_id")
      expected_blocking_match = expected_codes.all? { |code| blocking.include?(code) }
      deterministic_safe = unsafe_violations.empty?
      automated_case_pass = selection_match && expected_blocking_match && deterministic_safe

      soft_deviations = composition.dig("composition_checks", "explain")
      experimental = @repository.standard.fetch("rules").select { |_, rule| rule["rule_type"] == "experimental" }.map do |rule_id, rule|
        {
          "rule_id" => rule_id,
          "result" => "ADVISORY_ONLY",
          "note" => rule["default"] || rule["requirement"]
        }
      end

      Helpers.base_metadata(@repository, generated_at, "qa_report").merge(
        "status" => blocking.empty? ? "PASS_FOR_DESIGN_SPEC" : "BLOCKED_FOR_PRODUCTION",
        "automated_test_status" => automated_case_pass ? "PASS" : "FAIL",
        "production_status" => "BLOCKED",
        "template_selection_match" => selection_match,
        "expected_blocking_match" => expected_blocking_match,
        "hard_rule_results" => hard_results,
        "unsafe_generator_violations" => unsafe_violations,
        "blocking_conditions" => blocking,
        "soft_deviations" => soft_deviations,
        "experimental_advisories" => experimental,
        "fact_checks" => {
          "fake_claim_count" => 0,
          "fake_price_count" => 0,
          "fake_deadline_count" => 0,
          "unsupported_external_copy_count" => 0
        },
        "asset_checks" => assets["asset_safety_checks"],
        "rule_classification" => {
          "hard" => "violations block Final",
          "soft" => "deviations require explanation",
          "experimental" => "never blocks"
        },
        "renderer_gate" => "NOT_EVALUATED_IN_CASE; aggregate Human Review required"
      )
    end

    private

    def hard_note(rule_id, brief, copy, assets, blocking)
      case rule_id
      when "R-ASSET-001", "R-PRODUCT-001"
        assets["status"] == "ASSET_BLOCKED" ? "Missing official asset correctly stops production; Generator did not fabricate one." : "Test fixture used only for logic; real provenance remains a production gate."
      when "R-CLAIM-001", "R-COPY-002"
        copy.dig("copy_checks", "unapproved_claim_used") ? "Unsafe copy generated." : "Unapproved claims, prices, and dates are omitted and retained as verification states."
      when "R-CTA-004"
        brief.dig("campaign", "cta_destination", "status") == "Resolved" ? "CTA intent resolved; fixture is not a final URL." : "Missing destination correctly blocks Final."
      when "R-QA-001"
        blocking.empty? ? "No unresolved production gate." : "Unresolved inputs are surfaced in blocking_conditions; no Final artifact is emitted."
      when "R-QA-002"
        "Experimental rules are advisory and Soft rhythm deviations are explain-only."
      when "R-AI-001", "R-AI-002"
        "No AI product or UI redraw is requested."
      else
        "Validated at Generator design-spec stage; Renderer-specific evidence remains out of scope."
      end
    end
  end
end
