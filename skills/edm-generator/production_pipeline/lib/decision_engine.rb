# frozen_string_literal: true

module ProductionEDM
  class DecisionEngine
    def resolve_product_id(name)
      return "lock_ultra" if name.to_s.match?(/ロックUltra|Lock Ultra/i)
      return "daily_station" if name.to_s.match?(/デイリーステーション|Daily Station/i)

      raise "Unknown product alias: #{name}"
    end

    def campaign_decision(input)
      if input.fetch("objective") == "product_mechanism_understanding" || input.fetch("theme").to_s.match?(/理解|教育|Education/i)
        {
          "campaign_type" => "product_education",
          "primary_objective" => "mechanism_or_setup_understanding",
          "selected_template" => "TPL-EDU-B",
          "selection_rule" => "VSR-EDU-B",
          "selection_reason" => "Mechanism / device UI understanding is the primary task."
        }
      else
        {
          "campaign_type" => "single_product_conversion",
          "primary_objective" => "single_product_purchase_confidence",
          "selected_template" => "TPL-CONVERT-A",
          "selection_rule" => "VSR-CONVERT-A",
          "selection_reason" => "One product needs value and pre-purchase confidence; promotion is not the reason to act."
        }
      end
    end

    def module_sequence(campaign_type, available_purposes)
      if campaign_type == "product_education"
        sequence = [
          module_row("MOD-HERO-PRODUCT", "hero_product", "Product identity"),
          module_row("MOD-STORY-PRIMARY-USP", nil, "One-screen value"),
          module_row("MOD-STORY-APP-UI", "device_ui", "Official device UI"),
          module_row("MOD-STORY-FEATURE-SPLIT", "environment_detail", "Environment information"),
          module_row("MOD-STORY-IMAGE-TEXT", nil, "Family schedule scenario"),
          module_row("MOD-STORY-FAQ", nil, "Use conditions"),
          module_row("MOD-CONV-SECONDARY", nil, "Mid-course action"),
          module_row("MOD-STORY-PRODUCT-DETAIL", "product_reset", "Product re-entry"),
          module_row("MOD-CONV-CTA-BAND", nil, "Final action"),
          module_row("MOD-SYSTEM-BRAND-FOOTER", nil, "Legal and subscription closure")
        ]
      else
        sequence = [
          module_row("MOD-HERO-PRODUCT", "hero_product", "Product identity"),
          module_row("MOD-STORY-LIFESTYLE", "lifestyle", "Entrance context"),
          module_row("MOD-STORY-PRODUCT-DETAIL", nil, "Product identity detail", 1),
          module_row("MOD-STORY-PROBLEM", nil, "Pre-purchase question"),
          module_row("MOD-STORY-PRODUCT-DETAIL", "compatibility", "Compatibility evidence", 2),
          module_row("MOD-STORY-FAQ", nil, "Purchase checklist"),
          module_row("MOD-CONV-SECONDARY", nil, "Mid-course action"),
          module_row("MOD-STORY-PRIMARY-USP", "product_reset", "Product re-entry"),
          module_row("MOD-CONV-CTA-BAND", nil, "Final action"),
          module_row("MOD-SYSTEM-BRAND-FOOTER", nil, "Legal and subscription closure")
        ]
      end
      sequence.reject do |row|
        row["visual_purpose"] && !available_purposes.include?(row["visual_purpose"])
      end
    end

    private

    def module_row(module_id, visual_purpose, decision_question, instance = 1)
      {
        "module_id" => module_id,
        "instance_id" => instance == 1 ? module_id : "#{module_id}@#{instance}",
        "visual_purpose" => visual_purpose,
        "decision_question" => decision_question
      }
    end
  end
end

