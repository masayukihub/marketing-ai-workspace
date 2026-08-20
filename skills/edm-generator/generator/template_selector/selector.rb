# frozen_string_literal: true

module EDMGenerator
  class TemplateSelector
    def initialize(repository)
      @repository = repository
    end

    def call(brief, classification, generated_at)
      context = selection_context(brief)
      preflight_failures = @repository.selection_rules.fetch("hard_preflight").select do |gate|
        condition_matches?(gate.fetch("when"), context)
      end

      if preflight_failures.any?
        return Helpers.base_metadata(@repository, generated_at, "template_selection").merge(
          "status" => "BLOCKED",
          "selected_template_id" => nil,
          "alternative_template_id" => nil,
          "selection_reasons" => preflight_failures.map { |gate| "#{gate["id"]}: #{gate["failure_code"]}" },
          "failure_codes" => preflight_failures.map { |gate| gate["failure_code"] }.uniq,
          "required_module_ids" => [],
          "optional_module_ids" => [],
          "rejected_candidates" => [],
          "deterministic_tie_break" => "not_applicable_preflight_blocked"
        )
      end

      matrix_match = @repository.selection_rules.fetch("variant_resolution_matrix").find do |row|
        row.fetch("when").all? { |field, value| context[field] == value }
      end
      unless matrix_match
        return Helpers.base_metadata(@repository, generated_at, "template_selection").merge(
          "status" => "BLOCKED_TEMPLATE_SELECTION_AMBIGUOUS",
          "selected_template_id" => nil,
          "alternative_template_id" => nil,
          "selection_reasons" => ["冻结 Variant Resolution Matrix 无唯一匹配"],
          "failure_codes" => ["BLOCKED_TEMPLATE_SELECTION_AMBIGUOUS"],
          "required_module_ids" => [],
          "optional_module_ids" => [],
          "rejected_candidates" => [],
          "deterministic_tie_break" => "ambiguity_is_blocked_not_randomized"
        )
      end

      selected = @repository.templates.fetch(matrix_match.fetch("select"))
      family_variants = @repository.templates.values.select do |item|
        item["template_family_id"] == selected["template_family_id"] && item["template_id"] != selected["template_id"]
      end
      scored = family_variants.map { |item| [item, candidate_score(item, context)] }
      alternative = scored.sort_by { |item, score| [-score, item["template_id"]] }.first&.first
      rejected = @repository.templates.values.reject { |item| item["template_id"] == selected["template_id"] }.map do |item|
        reason = if item["template_family_id"] != selected["template_family_id"]
                   "冻结 Campaign Family 边界：不可跨 Family 反向覆盖"
                 elsif item["primary_objective"] != context["primary_objective"]
                   "Primary Objective 不匹配"
                 else
                   "产品数量、促销或素材条件弱于唯一矩阵命中"
                 end
        { "template_id" => item["template_id"], "reason" => reason }
      end

      Helpers.base_metadata(@repository, generated_at, "template_selection").merge(
        "status" => "selected",
        "campaign_family" => classification["campaign_family"],
        "selected_template_id" => selected["template_id"],
        "selected_template_name" => selected["template_name"],
        "alternative_template_id" => alternative && alternative["template_id"],
        "why_selected" => matrix_match["decisive_condition"],
        "selection_reasons" => [
          "#{matrix_match["id"]}: campaign_type + primary_objective exact match",
          "product_count=#{context["product_count"]}",
          "promotion_level=#{context["promotion_level"]}",
          "required_assets=#{context["asset_availability"]}"
        ],
        "failure_codes" => [],
        "required_module_ids" => selected.fetch("required_modules"),
        "recommended_module_sequence" => selected.fetch("recommended_module_sequence"),
        "optional_module_ids" => selected.fetch("optional_modules"),
        "rejected_candidates" => rejected,
        "deterministic_tie_break" => @repository.selection_rules.fetch("tie_breakers"),
        "responsibility_boundary" => @repository.selection_rules.fetch("responsibility_boundaries").find do |row|
          row.fetch("pair").include?(selected["template_id"])
        end
      )
    end

    private

    def selection_context(brief)
      context = brief.fetch("selection_context").dup
      context["primary_objective"] = brief.dig("campaign", "objective")
      context["promotion_level"] = brief.dig("campaign", "promotion", "level")
      context
    end

    def condition_matches?(condition, context)
      if condition["all"]
        return condition["all"].all? { |item| condition_matches?(item, context) }
      end
      field = condition["field"]
      actual = context[field]
      expected = condition["value"]
      case condition["op"]
      when "equal" then actual == expected
      when "not_equal" then actual != expected
      when "in" then Array(expected).include?(actual)
      when "not_in" then !Array(expected).include?(actual)
      when "greater_than_or_equal" then actual.to_i >= expected.to_i
      else false
      end
    end

    def candidate_score(template, context)
      model = @repository.selection_rules.fetch("score_model")
      score = 0
      score += model["campaign_type_exact"].to_i if template["campaign_type"] == context["campaign_type"]
      score += model["primary_objective_exact"].to_i if template["primary_objective"] == context["primary_objective"]
      range = template["product_count_range"] || {}
      score += model["product_count_in_range"].to_i if context["product_count"].to_i.between?(range["min"].to_i, range["max"].to_i)
      score += model["promotion_level_supported"].to_i if Array(template["promotion_level"]).include?(context["promotion_level"])
      score += model["required_assets_complete"].to_i if context["asset_availability"] == "complete"
      score
    end
  end
end

