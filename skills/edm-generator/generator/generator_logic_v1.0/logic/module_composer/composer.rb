# frozen_string_literal: true

module EDMGenerator
  class ModuleComposer
    HIGH_DENSITY = %w[
      MOD-COMMERCE-PRODUCT-GRID MOD-COMMERCE-PRICE MOD-COMMERCE-COUPON
      MOD-COMMERCE-COMPARISON
    ].freeze
    LOW_DENSITY = %w[
      MOD-STORY-LIFESTYLE MOD-SYSTEM-DIVIDER MOD-SYSTEM-SPACER MOD-CONV-CTA-BAND
      MOD-SYSTEM-BRAND-FOOTER
    ].freeze

    def initialize(repository)
      @repository = repository
    end

    def call(brief, selection, message, generated_at)
      return blocked_result(generated_at) unless selection["selected_template_id"]

      sequence = selection.fetch("recommended_module_sequence")
      modules = sequence.each_with_index.map do |module_id, index|
        definition = @repository.modules.fetch(module_id)
        {
          "position" => index + 1,
          "module_id" => module_id,
          "module_name" => definition["module_name"],
          "category" => definition["module_category"],
          "purpose" => definition["purpose"],
          "message_assignment" => message_assignment(module_id, message),
          "required_inputs" => definition["required_inputs"] || [],
          "asset_requirements" => definition["asset_requirements"] || [],
          "copy_requirements" => definition["copy_requirements"] || [],
          "priority" => selection.fetch("required_module_ids").include?(module_id) ? "required" : "recommended",
          "desktop_behavior" => definition["desktop_behavior"],
          "mobile_behavior" => definition["mobile_behavior"],
          "applicable_rules" => definition["applicable_rules"],
          "anti_patterns" => definition["anti_patterns"],
          "density" => density(module_id)
        }
      end

      checks = composition_checks(sequence, modules, brief)
      Helpers.base_metadata(@repository, generated_at, "module_composition").merge(
        "status" => checks["blocked"].empty? ? "composed" : "BLOCKED",
        "template_id" => selection["selected_template_id"],
        "module_sequence" => modules,
        "optional_candidates" => selection["optional_module_ids"],
        "composition_checks" => checks,
        "rhythm_source" => "design_system/visual_rhythm_rules_v1.0.md",
        "rhythm_policy" => "Soft/Advisory only; never overrides Hard Rule or inserts modules recursively."
      )
    end

    private

    def blocked_result(generated_at)
      Helpers.base_metadata(@repository, generated_at, "module_composition").merge(
        "status" => "blocked_before_composition",
        "template_id" => nil,
        "module_sequence" => [],
        "optional_candidates" => [],
        "composition_checks" => {
          "blocked" => [],
          "explain" => [],
          "advisory" => [],
          "required_checks" => {
            "repeated_module" => false,
            "homogeneous_run" => false,
            "high_density_run" => false,
            "cta_repetition" => false,
            "duplicate_usp" => false,
            "module_without_task" => false,
            "unnecessary_module" => false
          }
        }
      )
    end

    def message_assignment(module_id, message)
      case module_id
      when /HERO/ then message["primary_message"]
      when /PRIMARY-USP/ then "Primary USP — #{message.dig("primary_usp", "status") || "Resolved"}"
      when /PROBLEM/ then "Consumer problem context"
      when /PRODUCT-DETAIL|FEATURE|APP-UI/ then "Product evidence — Requires Claim Check"
      when /REVIEW|AWARD|USER-VOICE|WARRANTY/ then "Trust proof — source required"
      when /PRICE|COUPON|OFFER|LAST-CHANCE/ then "Promotion fact — verified source required"
      when /CTA/ then message.dig("cta", "intent")
      when /FOOTER/ then "Brand, legal, and destination closure"
      else "Section transition serving the Primary Objective"
      end
    end

    def density(module_id)
      return "high" if HIGH_DENSITY.include?(module_id)
      return "low" if LOW_DENSITY.include?(module_id)
      "medium"
    end

    def composition_checks(sequence, modules, brief)
      explain = []
      blocked = []
      advisory = []
      duplicate_ids = sequence.group_by(&:itself).select { |_, values| values.length > 1 }.keys
      high_run = max_run(modules.map { |item| item["density"] == "high" })
      same_layout_run = max_run(modules.map { |item| layout_family(item["module_id"]) })
      cta_repeat = sequence.each_cons(2).any? { |pair| pair == ["MOD-CONV-CTA-BAND", "MOD-CONV-CTA-BAND"] }
      module_without_task = modules.any? { |item| item["message_assignment"].to_s.strip.empty? }

      explain << {
        "code" => "HIGH_DENSITY_RUN",
        "rule" => "RHYTHM-DENSITY",
        "reason" => "#{high_run} 个 High-density Module 连续出现；冻结节奏建议最多 2 个。"
      } if high_run >= 3
      explain << {
        "code" => "HOMOGENEOUS_MODULE_RUN",
        "rule" => "RHYTHM-CROSS-AXIS",
        "reason" => "#{same_layout_run} 个同构布局连续出现，需要人工确认视觉变化。"
      } if same_layout_run >= 3
      explain << { "code" => "CTA_BAND_REPEAT", "rule" => "MCR-006" } if cta_repeat
      explain << { "code" => "DUPLICATE_MODULE", "modules" => duplicate_ids } unless duplicate_ids.empty?
      blocked << { "code" => "MODULE_WITHOUT_TASK", "rule" => "R-MODULE-001" } if module_without_task

      if sequence.include?("MOD-STORY-APP-UI") && brief.dig("selection_context", "ui_asset_available") != true
        blocked << { "code" => "OFFICIAL_UI_ASSET_REQUIRED", "rule" => "R-ASSET-001" }
      end
      if sequence.include?("MOD-CONV-LAST-CHANCE") && brief.dig("selection_context", "deadline_verified") != true
        blocked << { "code" => "PROMOTION_FACT_UNVERIFIED", "rule" => "R-PROMO-002" }
      end

      {
        "blocked" => blocked,
        "explain" => explain,
        "advisory" => advisory,
        "required_checks" => {
          "repeated_module" => !duplicate_ids.empty?,
          "homogeneous_run" => same_layout_run >= 3,
          "high_density_run" => high_run >= 3,
          "cta_repetition" => cta_repeat,
          "duplicate_usp" => false,
          "module_without_task" => module_without_task,
          "unnecessary_module" => false
        }
      }
    end

    def max_run(values)
      max = 0
      current = 0
      previous = Object.new
      values.each do |value|
        if value == true
          current += 1
        elsif value == false
          current = 0
        elsif value == previous
          current += 1
        else
          current = 1
        end
        max = [max, current].max
        previous = value
      end
      max
    end

    def layout_family(module_id)
      case module_id
      when /HERO/ then "hero"
      when /FEATURE-SPLIT|IMAGE-TEXT|APP-UI/ then "split"
      when /PRODUCT-GRID|PRODUCT-CARD|COMPARISON/ then "card_grid"
      when /OFFER-BAND|CTA-BAND|LAST-CHANCE/ then "band"
      when /FOOTER/ then "footer"
      when /LIFESTYLE|PRODUCT-DETAIL/ then "visual_full"
      else "text_or_proof"
      end
    end
  end
end
