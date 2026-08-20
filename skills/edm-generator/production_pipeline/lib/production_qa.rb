# frozen_string_literal: true

require_relative "support"

module ProductionEDM
  class ProductionQA
    def evaluate(product:, campaign:, copy:, assets:, footer:, modules:, registry_context:)
      main = assets.find { |item| item["visual_purpose"] == "hero_product" }
      hard = {
        "primary_objective_present" => !Support.value(campaign.dig("campaign", "objective")).to_s.empty?,
        "official_japanese_product_name_verified" => product.dig("product", "official_name_ja", "status") == "VERIFIED",
        "campaign_truth_gate_pass" => Support.value(campaign.dig("verification", "campaign_truth_gate")) == "PASS",
        "cta_url_valid" => Support.valid_http_url?(Support.value(campaign.dig("cta", "url"))),
        "official_main_asset_present" => main && main["source_authenticity"] == "OFFICIAL_MARKETING_ASSET" && main["usage_scope"] == "DESIGN_PRODUCTION_APPROVED" && main["file_exists"],
        "no_ai_product_redraw" => assets.compact.none? { |item| item["asset_type"] == "ai_background" && item["visual_purpose"] == "hero_product" },
        "no_forbidden_claim" => copy.dig("checks", "forbidden_claim_hits").empty?,
        "no_numeric_performance_claim" => copy.dig("checks", "numeric_performance_claims").empty?,
        "no_price_or_promotion_in_copy" => copy.dig("checks", "price_tokens").empty?,
        "all_factual_copy_mapped_to_claim_id" => copy.dig("checks", "unmapped_factual_roles").empty?,
        "no_repeated_non_cta_lines" => copy.dig("checks", "repeated_non_cta_lines").empty?,
        "module_sequence_nonempty" => !modules.empty?
      }
      visual = {
        "product_publication_gate" => registry_context.dig("domains", "product", "gate") == "PASS",
        "used_claims_verified" => registry_context.dig("domains", "claim", "gate") == "PASS",
        "official_design_scope_main_asset" => main && main["approval_scope"] == "design_production",
        "campaign_truth_verified" => registry_context.dig("domains", "campaign", "gate") == "PASS",
        "footer_legal_approved" => Support.value(footer.dig("approval", "legal_approved_for_new_production")) == true,
        "static_footer_reusable" => Support.value(footer.dig("approval", "static_footer_reusable")) == true,
        "copy_production_candidate" => %w[COPY_PRODUCTION_CANDIDATE APPROVED].include?(copy.fetch("approval_status"))
      }
      send = {
        "final_delivery_human_approved" => copy.fetch("approval_status") == "APPROVED",
        "footer_runtime_links_resolved" => Support.value(footer.dig("approval", "runtime_links_resolved")) == true
      }
      blocking_hard = hard.select { |_, passed| !passed }.keys
      status = if blocking_hard.any?
                 "BLOCKED"
               elsif visual.values.all?
                 "DESIGN_READY_PENDING_BROWSER_QA"
               else
                 registry_context.fetch("overall_status", "INTERNAL_DRAFT")
               end
      {
        "production_status" => status,
        "hard_rule_checks" => hard,
        "visual_readiness_checks" => visual,
        "send_readiness_checks" => send,
        "production_readiness_checks" => visual.merge(send),
        "blocking_hard_rules" => blocking_hard,
        "visual_gaps" => visual.select { |_, passed| !passed }.keys,
        "send_gaps" => send.select { |_, passed| !passed }.keys,
        "production_gaps" => visual.merge(send).select { |_, passed| !passed }.keys,
        "browser_qa" => "PENDING",
        "no_fake_content" => hard.values_at("no_forbidden_claim", "no_numeric_performance_claim", "no_price_or_promotion_in_copy").all?,
        "no_product_redraw" => hard.fetch("no_ai_product_redraw")
      }
    end
  end
end
