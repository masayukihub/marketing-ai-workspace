# frozen_string_literal: true

module EDMGenerator
  class CampaignClassifier
    def initialize(repository)
      @repository = repository
    end

    def call(brief, generated_at)
      campaign_type = brief.dig("campaign", "type")
      objective = brief.dig("campaign", "objective")
      exact = @repository.selection_rules.fetch("variant_resolution_matrix").find do |row|
        row.dig("when", "campaign_type") == campaign_type &&
          row.dig("when", "primary_objective") == objective
      end
      template = exact && @repository.templates[exact["select"]]
      selected_family = template && template["template_family_id"]

      rejected = @repository.families.values.reject { |family| family["family_id"] == selected_family }.map do |family|
        {
          "family_id" => family["family_id"],
          "reason" => family["campaign_type"] == campaign_type ? "Primary Objective 不匹配" : "Campaign Type 不匹配"
        }
      end

      status = selected_family ? "classified" : "BLOCKED"
      Helpers.base_metadata(@repository, generated_at, "campaign_classification").merge(
        "status" => status,
        "campaign_family" => selected_family || "Unknown",
        "campaign_type" => campaign_type,
        "confidence" => selected_family ? 0.98 : 0.0,
        "reason" => selected_family ? [
          "Campaign Type 与冻结枚举完全匹配",
          "Primary Objective 命中 #{exact["id"]}",
          "不允许跨 Campaign Family 由分数覆盖"
        ] : ["Campaign Type 或 Primary Objective 未命中冻结矩阵"],
        "rejected_families" => rejected,
        "failure_code" => selected_family ? nil : "CAMPAIGN_TYPE_UNRESOLVED"
      )
    end
  end
end

