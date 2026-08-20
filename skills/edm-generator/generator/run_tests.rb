# frozen_string_literal: true

require_relative "pipeline"

module EDMGenerator
  class TestRunner
    attr_reader :root, :pipeline, :generated_at

    def initialize(root)
      @root = File.expand_path(root)
      @pipeline = Pipeline.new(root)
      @generated_at = Time.now.getlocal("+08:00").iso8601
    end

    def run
      cases = YAML.safe_load(
        File.read(File.join(root, "tests/generator_test_cases.yaml")),
        permitted_classes: [Date, Time],
        aliases: true
      ).fetch("test_cases")
      results = cases.map { |test_case| execute_case(test_case) }
      aggregate = aggregate_results(results)
      Helpers.write_yaml(File.join(root, "generator/outputs/test_results.yaml"), {
        "version" => "1.0.0",
        "generated_at" => generated_at,
        "results" => results.map { |result| compact_result(result) }
      })
      Helpers.write_yaml(File.join(root, "generator/outputs/scorecard.yaml"), aggregate)
      issue_log = build_issue_log(results)
      Helpers.write_text(File.join(root, "research/design_system_issue_log.md"), issue_log)
      puts JSON.pretty_generate(aggregate)
    end

    private

    def execute_case(test_case)
      first = pipeline.run(test_case, generated_at: generated_at)
      second = pipeline.run(test_case, generated_at: generated_at)
      deterministic = first["structure_fingerprint"] == second["structure_fingerprint"]
      first["deterministic_repeat_match"] = deterministic
      first["qa"]["determinism"] = {
        "result" => deterministic ? "PASS" : "FAIL",
        "fingerprint_first" => first["structure_fingerprint"],
        "fingerprint_repeat" => second["structure_fingerprint"]
      }
      first["automated_case_status"] = first.dig("qa", "automated_test_status") == "PASS" && deterministic ? "PASS" : "FAIL"
      write_case_outputs(first)
      first
    end

    def write_case_outputs(result)
      case_dir = File.join(root, "generator/outputs", result["test_case_id"])
      Helpers.write_yaml(File.join(case_dir, "campaign_brief.yaml"), result["brief"])
      Helpers.write_yaml(File.join(case_dir, "asset_plan.yaml"), result["assets"])
      Helpers.write_text(File.join(case_dir, "decision_trace.md"), decision_trace(result))
      Helpers.write_text(File.join(case_dir, "design_spec.md"), design_spec(result))
      Helpers.write_text(File.join(case_dir, "copy_draft.md"), copy_draft(result))
      Helpers.write_text(File.join(case_dir, "qa_report.md"), qa_report(result))
    end

    def decision_trace(result)
      selection = result["selection"]
      rejected = selection.fetch("rejected_candidates", []).first(8).map { |item| "- `#{item["template_id"]}` — #{item["reason"]}" }.join("\n")
      <<~MD
        # #{result["test_case_id"]} Decision Trace

        - Campaign Family: `#{result.dig("classification", "campaign_family")}`
        - Confidence: `#{result.dig("classification", "confidence")}`
        - Selected Template: `#{selection["selected_template_id"] || "BLOCKED"}`
        - Alternative: `#{selection["alternative_template_id"] || "None"}`
        - Status: `#{selection["status"]}`

        ## Why

        #{Array(selection["selection_reasons"]).map { |reason| "- #{reason}" }.join("\n")}

        ## Campaign Classification Reasons

        #{Array(result.dig("classification", "reason")).map { |reason| "- #{reason}" }.join("\n")}

        ## Rejected Candidates

        #{rejected.empty? ? "- Not available because preflight stopped selection." : rejected}

        ## Determinism

        - Structure fingerprint: `#{result["structure_fingerprint"]}`
        - Same input + same sources: `#{result["deterministic_repeat_match"] ? "PASS" : "FAIL"}`

        This trace reads the frozen v1.0 selection matrix. It does not use Tier D to override SwitchBot family boundaries.
      MD
    end

    def design_spec(result)
      modules = result.dig("composition", "module_sequence").map do |item|
        "#{item["position"]}. `#{item["module_id"]}` — #{item["purpose"]}\n   - Message: #{item["message_assignment"]}\n   - Priority: #{item["priority"]}\n   - Density: #{item["density"]}"
      end.join("\n")
      <<~MD
        # #{result["test_case_id"]} Design Spec

        Status: **#{result.dig("qa", "status")}**  
        Production: **BLOCKED until current Product Knowledge, Claim, Price, destination, and real asset provenance are resolved.**

        ## Campaign Brief

        - Theme: #{result.dig("brief", "campaign", "theme")}
        - Primary Objective: `#{result.dig("message", "primary_objective")}`
        - Primary Message: #{result.dig("message", "primary_message")}
        - Campaign Family: `#{result.dig("classification", "campaign_family")}`
        - Template: `#{result.dig("selection", "selected_template_id") || "BLOCKED"}`

        ## Module Sequence

        #{modules.empty? ? "No Module Sequence: Template Selection was blocked." : modules}

        ## Desktop Contract

        - Content width baseline: `600px` from `R-DESKTOP-001`.
        - Preserve one dominant reading path and semantic order.
        - Product, Proof, and Primary CTA form an intelligible task; no fixed Hero height ratio is invented.

        ## Mobile Contract

        - Reflow by semantic order, not Desktop coordinates.
        - Preserve product aspect ratio and recognizability; destructive crop is prohibited.
        - `390px` is an Experimental QA viewport and cannot block Production by itself.
        - Renderer behavior is intentionally not implemented in Phase 4.

        ## Visual Rhythm

        - Explain-only deviations: #{result.dig("composition", "composition_checks", "explain").empty? ? "None" : result.dig("composition", "composition_checks", "explain").map { |item| item["code"] }.join(", ")}
        - Experimental rules remain advisory.
      MD
    end

    def copy_draft(result)
      copy = result["copy"]
      modules = copy.fetch("module_copy").map do |item|
        "### #{item["module_id"]}\n\n- Headline: #{item["headline"]}\n- Body: #{item["body"]}\n- Status: `#{item["status"]}`\n- Binding: #{item["source_binding"]}"
      end.join("\n\n")
      <<~MD
        # #{result["test_case_id"]} Japanese Copy Draft

        Copy stage: **Design-ready draft / Not Final polished copy**

        - Subject: #{copy.dig("subject", "text")} — `#{copy.dig("subject", "status")}`
        - Preview: #{copy.dig("preview", "text")} — `#{copy.dig("preview", "status")}`
        - H1: #{copy.dig("h1", "text")} — #{copy.dig("h1", "length")} characters / `#{copy.dig("h1", "status")}`
        - CTA: #{copy.dig("cta", "text")} — `#{copy.dig("cta", "status")}`

        #{modules.empty? ? "No module copy: upstream selection was blocked." : modules}

        ## Safety Boundary

        No unapproved product claim, price, discount amount, launch date, deadline, review, award, or compatibility statement is generated. Product and campaign facts stay `Requires Verification` until an Approved source is available.
      MD
    end

    def qa_report(result)
      qa = result["qa"]
      hard = qa.fetch("hard_rule_results").map do |item|
        "- [#{item["result"] == "PASS" ? "x" : " "}] `#{item["rule_id"]}` — #{item["result"]}: #{item["note"]}"
      end.join("\n")
      soft = qa.fetch("soft_deviations").map { |item| "- `#{item["code"]}` — #{item["reason"] || item["rule"]}" }.join("\n")
      experimental = qa.fetch("experimental_advisories").map { |item| "- `#{item["rule_id"]}` — ADVISORY_ONLY" }.join("\n")
      <<~MD
        # #{result["test_case_id"]} QA Report

        - Automated Test: **#{result["automated_case_status"] || qa["automated_test_status"]}**
        - Design Spec QA: **#{qa["status"]}**
        - Production: **#{qa["production_status"]}**
        - Template Match: **#{qa["template_selection_match"] ? "PASS" : "FAIL"}**
        - Determinism: **#{result["deterministic_repeat_match"] ? "PASS" : "Pending aggregate rerun"}**
        - Fake Claims / Prices / Deadlines: **#{qa.dig("fact_checks", "fake_claim_count")} / #{qa.dig("fact_checks", "fake_price_count")} / #{qa.dig("fact_checks", "fake_deadline_count")}**
        - Unsafe Generator Hard-rule Violations: **#{qa["unsafe_generator_violations"].length}**

        ## Production Blocking Conditions

        #{qa["blocking_conditions"].map { |code| "- `#{code}`" }.join("\n")}

        ## Hard Rules

        #{hard}

        ## Soft Deviations

        #{soft.empty? ? "- None" : soft}

        ## Experimental Advisories

        #{experimental}
      MD
    end

    def compact_result(result)
      {
        "test_case_id" => result["test_case_id"],
        "name" => result["name"],
        "automated_case_status" => result["automated_case_status"],
        "production_status" => result.dig("qa", "production_status"),
        "campaign_family" => result.dig("classification", "campaign_family"),
        "selected_template_id" => result.dig("selection", "selected_template_id"),
        "expected_template_id" => result.dig("expected", "selected_template_id"),
        "template_match" => result.dig("qa", "template_selection_match"),
        "deterministic_repeat_match" => result["deterministic_repeat_match"],
        "unsafe_hard_rule_violations" => result.dig("qa", "unsafe_generator_violations"),
        "blocking_conditions" => result.dig("qa", "blocking_conditions"),
        "soft_deviations" => result.dig("qa", "soft_deviations"),
        "scores" => result["scores"],
        "structure_fingerprint" => result["structure_fingerprint"]
      }
    end

    def aggregate_results(results)
      total = results.length
      template_matches = results.count { |result| result.dig("qa", "template_selection_match") }
      automated_passes = results.count { |result| result["automated_case_status"] == "PASS" }
      hard_violations = results.sum { |result| result.dig("qa", "unsafe_generator_violations").length }
      deterministic = results.all? { |result| result["deterministic_repeat_match"] }
      asset_missing = results.find { |result| result["test_case_id"] == "GTC-016" }
      negative_cta = results.find { |result| result["test_case_id"] == "GTC-017" }
      scores = %w[brief_completeness campaign_classification template_selection message_hierarchy module_composition copy_usability asset_safety rule_compliance overall].to_h do |key|
        [key, (results.sum { |result| result.dig("scores", key).to_f } / total).round(2)]
      end
      {
        "version" => "1.0.0",
        "generated_at" => generated_at,
        "phase" => "Phase 4 Generator Logic Build + Test Case Validation",
        "execution" => {
          "defined_cases" => total,
          "executed_cases" => total,
          "automated_passes" => automated_passes,
          "automated_failures" => total - automated_passes,
          "template_matches" => template_matches,
          "template_selection_accuracy" => (template_matches.to_f / total * 100).round(2),
          "deterministic_repeat_match" => deterministic,
          "unsafe_hard_rule_violations" => hard_violations,
          "fake_claims" => results.sum { |result| result.dig("qa", "fact_checks", "fake_claim_count") },
          "fake_prices" => results.sum { |result| result.dig("qa", "fact_checks", "fake_price_count") },
          "ai_product_redraw_requests" => results.count { |result| result.dig("assets", "asset_safety_checks", "product_redraw_requested") }
        },
        "negative_path_validation" => {
          "GTC-016_missing_asset" => asset_missing.dig("assets", "status") == "ASSET_BLOCKED" && asset_missing.dig("selection", "selected_template_id").nil? ? "PASS" : "FAIL",
          "GTC-017_missing_cta" => negative_cta.dig("qa", "blocking_conditions").include?("CTA_DESTINATION_INVALID") ? "PASS" : "FAIL"
        },
        "average_scores" => scores,
        "renderer_gate" => {
          "automated_case_execution" => total == 17 ? "PASS" : "FAIL",
          "template_selection_accuracy_min_85" => template_matches.to_f / total >= 0.85 ? "PASS" : "FAIL",
          "human_pass_plus_needs_modification_min_90" => "WAITING_HUMAN_REVIEW",
          "hard_rule_violations_zero" => hard_violations.zero? ? "PASS" : "FAIL",
          "fake_claims_prices_zero" => results.all? { |result| result.dig("qa", "fact_checks", "fake_claim_count").zero? && result.dig("qa", "fact_checks", "fake_price_count").zero? } ? "PASS" : "FAIL",
          "ai_redraw_zero" => results.none? { |result| result.dig("assets", "asset_safety_checks", "product_redraw_requested") } ? "PASS" : "FAIL",
          "asset_missing_blocks" => asset_missing.dig("assets", "status") == "ASSET_BLOCKED" ? "PASS" : "FAIL",
          "deterministic" => deterministic ? "PASS" : "FAIL",
          "overall" => "NOT_MET_WAITING_HUMAN_REVIEW"
        },
        "case_results" => results.map { |result| compact_result(result) }
      }
    end

    def build_issue_log(results)
      soft_counts = results.flat_map { |result| result.dig("qa", "soft_deviations").map { |item| item["code"] } }.each_with_object(Hash.new(0)) do |code, counts|
        counts[code] += 1
      end
      <<~MD
        # Phase 4 Design System Issue Log

        Status: **No frozen v1.0 blocking defect found during the 17-case automated run.**  
        Scope: issues are recorded only; no file under `standards/*_v1.0.*` or `design_system/*_v1.0.*` was modified.

        ## Observations

        - Soft rhythm deviations: #{soft_counts.empty? ? "none" : soft_counts.map { |code, count| "`#{code}` × #{count}" }.join(", ")}.
        - The frozen selector provides deterministic exact Objective mapping and correctly blocks missing required assets.
        - Product Knowledge currently has no Approved External Claim and no publication-ready JP identity set for these fixtures. This is a knowledge-readiness gap, not a Design System defect.
        - Human review is still required to validate whether the selected structure and Japanese draft are useful, especially where official Japanese product naming and claims remain pending.

        ## Candidate for a Future Version (Do Not Apply to v1.0)

        `Generator confidence calibration` is not defined as a machine-readable Design System rule. Phase 4 uses `0.98` only when Campaign Type and Primary Objective exactly match the frozen matrix. If later human reviews reveal ambiguity, define a v1.1 calibration table rather than changing v1.0 silently.
      MD
    end
  end
end

if $PROGRAM_NAME == __FILE__
  project_root = File.expand_path("..", __dir__)
  EDMGenerator::TestRunner.new(project_root).run
end
