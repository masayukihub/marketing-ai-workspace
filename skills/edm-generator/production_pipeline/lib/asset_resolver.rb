# frozen_string_literal: true

require_relative "support"

module ProductionEDM
  class AssetResolver
    TYPE_SCORE = {
      "official_png" => 700,
      "official_product_scene" => 600,
      "lifestyle" => 600,
      "official_detail" => 500,
      "detail" => 500,
      "official_app_ui" => 400,
      "app_ui" => 400,
      "approved_campaign_asset" => 300,
      "approved_brand_asset" => 200,
      "ai_background" => 100
    }.freeze

    attr_reader :root, :registry

    def initialize(root)
      @root = root
      source = Support.load_yaml(root, "production_registry/assets/asset_registry.yaml")
      @registry = {
        "assets" => source.fetch("assets").map do |asset|
          {
            "asset_id" => asset.fetch("asset_id"),
            "product_id" => asset.fetch("product_id"),
            "asset_type" => asset.fetch("asset_type"),
            "source_path" => asset.fetch("source_path"),
            "source_url" => asset.fetch("source_origin"),
            "approval_status" => asset.fetch("production_status"),
            "source_authenticity" => asset.fetch("source_authenticity", "UNVERIFIED"),
            "usage_scope" => asset.fetch("usage_scope", "INTERNAL_ONLY"),
            "channel_scope" => asset.fetch("channel_scope", "UNKNOWN"),
            "approval_scope" => asset.fetch("usage_scope", "INTERNAL_ONLY") == "DESIGN_PRODUCTION_APPROVED" ? "design_production" : "internal_renderer_pilot_only",
            "visual_purposes" => asset.fetch("allowed_usage"),
            "fit_score" => 100,
            "usage" => asset.fetch("allowed_usage").join(", "),
            "fallback" => nil,
            "notes" => "Resolved from the Phase 8 source-authenticity and usage-scope registry. Channel scope remains a send-time gate."
          }
        end
      }
    end

    def resolve(product_id:, module_id:, visual_purpose:)
      candidates = registry.fetch("assets").select do |asset|
        asset.fetch("product_id") == product_id &&
          asset.fetch("source_authenticity") == "OFFICIAL_MARKETING_ASSET" &&
          asset.fetch("usage_scope") == "DESIGN_PRODUCTION_APPROVED" &&
          asset.fetch("visual_purposes").include?(visual_purpose)
      end
      ranked = candidates.sort_by do |asset|
        [-(TYPE_SCORE.fetch(asset.fetch("asset_type"), 0)), -asset.fetch("fit_score").to_i]
      end
      selected = ranked.first
      return missing(product_id, module_id, visual_purpose) unless selected

      {
        "module_id" => module_id,
        "visual_purpose" => visual_purpose,
        "asset_id" => selected.fetch("asset_id"),
        "asset_type" => selected.fetch("asset_type"),
        "source_path" => selected.fetch("source_path"),
        "source_url" => selected.fetch("source_url"),
        "approval_status" => selected.fetch("approval_status"),
        "source_authenticity" => selected.fetch("source_authenticity"),
        "usage_scope" => selected.fetch("usage_scope"),
        "channel_scope" => selected.fetch("channel_scope"),
        "approval_scope" => selected.fetch("approval_scope"),
        "fit_score" => selected.fetch("fit_score"),
        "usage" => selected.fetch("usage"),
        "fallback" => selected["fallback"],
        "notes" => selected["notes"],
        "file_exists" => File.file?(File.join(root, selected.fetch("source_path")))
      }
    end

    private

    def missing(product_id, module_id, visual_purpose)
      {
        "module_id" => module_id,
        "visual_purpose" => visual_purpose,
        "asset_id" => nil,
        "asset_type" => nil,
        "source_path" => nil,
        "approval_status" => "MISSING",
        "approval_scope" => nil,
        "fit_score" => 0,
        "usage" => nil,
        "fallback" => visual_purpose == "hero_product" ? nil : "omit_module",
        "notes" => "No matching approved asset. AI cannot replace a missing product main asset.",
        "file_exists" => false,
        "product_id" => product_id
      }
    end
  end
end
