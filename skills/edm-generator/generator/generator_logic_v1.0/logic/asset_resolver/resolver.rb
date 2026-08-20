# frozen_string_literal: true

module EDMGenerator
  class AssetResolver
    OFFICIAL_ONLY = %w[product ui packaging accessory installation detail_closeup].freeze
    AI_ALLOWED = %w[environment person prop lighting background atmosphere].freeze

    def initialize(repository)
      @repository = repository
    end

    def call(brief, composition, generated_at)
      availability = brief.dig("selection_context", "asset_availability")
      fixture_complete = availability == "complete"
      fixture_missing = availability == "missing_required"
      product_ids = (brief.dig("product", "records") || []).map { |item| item["product_id"] }

      module_assets = composition.fetch("module_sequence").map do |module_item|
        required_types = asset_types(module_item)
        {
          "module_id" => module_item["module_id"],
          "required_asset_types" => required_types,
          "resolved_assets" => fixture_complete ? required_types.map { |type| fixture_asset(type, product_ids) } : [],
          "missing_assets" => fixture_missing ? required_types : [],
          "production_provenance_status" => "Unverified",
          "test_resolution_status" => fixture_complete ? "verified_test_fixture" : "missing_required",
          "ai_generation" => ai_policy(required_types)
        }
      end

      missing_product = fixture_missing && (
        product_ids.any? || module_assets.any? { |item| item["required_asset_types"].include?("product") }
      )
      status = missing_product ? "ASSET_BLOCKED" : "resolved_for_logic_test_only"
      missing_required_assets = module_assets.flat_map do |item|
        item["missing_assets"].map { |type| "#{item["module_id"]}:#{type}" }
      end
      missing_required_assets << "campaign:official_product_asset" if missing_product && missing_required_assets.empty?

      Helpers.base_metadata(@repository, generated_at, "asset_plan").merge(
        "status" => status,
        "product_ids" => product_ids,
        "asset_inventory_state" => availability,
        "module_assets" => module_assets,
        "missing_required_assets" => missing_required_assets,
        "official_only_asset_types" => OFFICIAL_ONLY,
        "ai_allowed_asset_types" => AI_ALLOWED,
        "ai_forbidden" => ["product redraw", "product reconstruction", "UI reconstruction", "packaging redraw", "installation relationship invention"],
        "asset_safety_checks" => {
          "product_redraw_requested" => false,
          "ui_redraw_requested" => false,
          "untraceable_final_asset_allowed" => false,
          "missing_official_product_correctly_blocked" => missing_product
        },
        "production_note" => "Test fixtures do not represent files, rights, approvals, or provenance. Real official assets must be resolved before Renderer/Final."
      )
    end

    private

    def asset_types(module_item)
      id = module_item["module_id"]
      types = []
      types << "product" if id.match?(/HERO-PRODUCT|HERO-LIFESTYLE|HERO-MULTI|PRODUCT|FEATURE|COMPARISON|PRICE|GRID/)
      types << "ui" if id.include?("APP-UI")
      types << "lifestyle" if id.include?("LIFESTYLE")
      types << "proof" if id.match?(/REVIEW|AWARD|USER-VOICE|WARRANTY/)
      types << "promotion_source" if id.match?(/PROMOTION|PRICE|COUPON|OFFER|LAST-CHANCE/)
      types << "brand" if id.include?("BRAND-FOOTER")
      types << "legal" if id.include?("LEGAL-FOOTER")
      types << "editorial" if id.include?("EDITORIAL")
      types.empty? ? ["content_support"] : types.uniq
    end

    def fixture_asset(type, product_ids)
      {
        "asset_type" => type,
        "asset_id" => "TEST-FIXTURE-#{type.upcase.tr("_", "-")}",
        "product_ids" => product_ids,
        "source_path" => nil,
        "provenance" => "verified_test_fixture",
        "usage_right" => "test_logic_only",
        "production_approved" => false
      }
    end

    def ai_policy(types)
      if types.any? { |type| OFFICIAL_ONLY.include?(type) }
        {
          "allowed" => false,
          "reason" => "Product/UI/packaging/accessory/installation/detail assets require official or verified source."
        }
      else
        {
          "allowed" => true,
          "scope" => AI_ALLOWED,
          "condition" => "Cannot change product facts, geometry, color, proportion, installation relationship, or UI."
        }
      end
    end
  end
end
