# frozen_string_literal: true

module ProductionEDM
  class LengthEngine
    def decide(product:, campaign:, assets:, campaign_type:)
      complexity = "HIGH"
      distinct_assets = assets.count { |item| item["approval_status"] == "APPROVED" }
      approved_claims = product.dig("claims", "approved").to_a.length
      proof_available = product.dig("proof", "status") != "MISSING"
      external_service_approved = product.dig("service", "approval_scope") == "production"
      target = complexity == "HIGH" ? "Long-form" : "Standard"
      content_depth = distinct_assets + approved_claims + (proof_available ? 1 : 0) + (external_service_approved ? 1 : 0)

      if target == "Long-form" && content_depth < 6
        {
          "length_class" => "Standard",
          "target_module_range" => [8, 11],
          "reason" => "HIGH product complexity would justify Long-form, but verified truth / asset depth is insufficient; capped at Standard.",
          "long_form_gate" => "CAPPED_BY_TRUTH_AND_ASSET_COVERAGE",
          "inputs" => {
            "product_complexity" => complexity,
            "campaign_type" => campaign_type,
            "distinct_approved_internal_assets" => distinct_assets,
            "approved_external_claims" => approved_claims,
            "verified_proof" => proof_available,
            "production_service_approved" => external_service_approved
          }
        }
      else
        {
          "length_class" => target,
          "target_module_range" => target == "Long-form" ? [12, 18] : [8, 11],
          "reason" => "Product and campaign information depth supports the selected length.",
          "long_form_gate" => "PASS",
          "inputs" => {"product_complexity" => complexity, "campaign_type" => campaign_type}
        }
      end
    end
  end
end

