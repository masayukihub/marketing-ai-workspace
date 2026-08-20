# frozen_string_literal: true

require "yaml"
require "fileutils"
require_relative "support"
require_relative "asset_resolver"
require_relative "decision_engine"
require_relative "length_engine"
require_relative "copy_pipeline"
require_relative "production_qa"
require_relative "production_renderer"
require_relative "../../generator/historical_template_matcher"

module ProductionEDM
  class Pipeline
    attr_reader :root

    def initialize(root)
      @root = root
      @decisions = DecisionEngine.new
      @resolver = AssetResolver.new(root)
      @length_engine = LengthEngine.new
      @copy_pipeline = CopyPipeline.new
      @qa = ProductionQA.new
      @renderer = ProductionRenderer.new(root)
      @historical_matcher = EDMGenerator::HistoricalTemplateMatcher.new(root)
    end

    def run(input_path)
      input = Support.load_yaml(root, input_path)
      product_id = @decisions.resolve_product_id(input.fetch("product"))
      product = Support.load_yaml(root, "production_truth/products/#{product_id}.yaml")
      campaign = Support.load_yaml(root, "production_truth/campaigns/#{input.fetch("case_id")}.yaml")
      registry_product = Support.load_yaml(root, "production_registry/products/#{product_id}.yaml")
      registry_campaign = Support.load_yaml(root, "production_registry/campaigns/#{input.fetch("case_id")}.yaml")
      claim_registry = Support.load_yaml(root, "production_registry/claims/claim_registry.yaml")
      footer = production_footer_adapter
      readiness = readiness_context(input.fetch("case_id"))
      decision = @decisions.campaign_decision(input)
      available_purposes = available_purposes_for(product_id)
      historical_selection = @historical_matcher.rank(
        {
          "campaign_type" => decision.fetch("campaign_type"),
          "objective" => decision.fetch("primary_objective"),
          "product_count" => 1,
          "promotion_level" => promotion_level(campaign),
          "content_depth" => "high",
          "asset_types" => historical_asset_types(available_purposes),
          "product_complexity" => "high"
        }
      )
      decision["historical_template_first"] = true
      decision["historical_template_selection"] = historical_selection
      decision["selected_historical_template"] = historical_selection["selected_template_id"]
      decision["historical_reference_edm"] = historical_selection["selected_reference_edm"]
      decision["historical_route"] = historical_selection.fetch("route")
      decision["generic_fallback_allowed"] = historical_selection.fetch("generic_fallback_allowed")
      modules = @decisions.module_sequence(decision.fetch("campaign_type"), available_purposes)
      validate_frozen_dependencies!(decision, modules)
      decision["brand"] = "SwitchBot"
      decision["market"] = "Japan"
      decision["render_mode"] = historical_selection["selected_template_id"] ? "historical_template_first" : "generic_fallback"
      decision["product_complexity"] = "HIGH"
      decision["audience"] = Support.status(product.dig("product", "target_audience")) == "UNVERIFIED" ? "UNVERIFIED" : Support.value(product.dig("product", "target_audience"))
      copy = @copy_pipeline.build(
        product: product,
        campaign: campaign,
        decision: decision,
        case_id: input.fetch("case_id"),
        claim_registry: claim_registry,
        final_copy_status: registry_campaign.dig("approval", "final_copy", "status")
      )
      modules = rebalance_modules(modules, copy)
      assets = resolve_assets(product_id, modules)
      decision["length"] = @length_engine.decide(product: product, campaign: campaign, assets: assets, campaign_type: decision.fetch("campaign_type"))
      qa = @qa.evaluate(product: product, campaign: campaign, copy: copy, assets: assets, footer: footer, modules: modules, registry_context: readiness)
      result = {
        "schema_version" => "1.0.0",
        "generated_at" => Time.now.utc.iso8601,
        "case_id" => input.fetch("case_id"),
        "one_shot_input" => input,
        "product_id" => product_id,
        "product_truth_source" => "production_truth/products/#{product_id}.yaml",
        "product_publication_registry_source" => "production_registry/products/#{product_id}.yaml",
        "product_publication_registry" => registry_product,
        "product_knowledge_source" => "/Users/lai/.codex/skills/product-knowledge",
        "product_truth_completeness" => truth_completeness(product),
        "product" => product,
        "campaign_truth_source" => "production_truth/campaigns/#{input.fetch("case_id")}.yaml",
        "campaign_registry_source" => "production_registry/campaigns/#{input.fetch("case_id")}.yaml",
        "campaign" => campaign,
        "decision" => decision,
        "modules" => modules,
        "assets" => assets,
        "copy" => copy,
        "footer" => footer,
        "production_registry_context" => readiness,
        "traceability" => traceability(product_id, product, campaign, assets, copy),
        "qa" => qa
      }
      out = @renderer.write_package(result)
      result["output_dir"] = out.sub("#{root}/", "")
      File.write(File.join(out, "truth_manifest.yaml"), YAML.dump(result))
      result
    end

    private

    def promotion_level(campaign)
      promotion_type = Support.value(campaign.dig("promotion", "type")).to_s
      return "none" if promotion_type.empty? || promotion_type == "none"

      %w[countdown last_chance clearance high].any? { |term| promotion_type.downcase.include?(term) } ? "high" : "medium"
    end

    def historical_asset_types(purposes)
      types = ["product"]
      types << "lifestyle" if purposes.any? { |purpose| purpose.match?(/lifestyle|environment/) }
      types << "detail" if purposes.any? { |purpose| purpose.match?(/detail|compatibility|product_reset/) }
      types << "app_ui" if purposes.any? { |purpose| purpose.match?(/ui|device/) }
      types.uniq
    end

    def available_purposes_for(product_id)
      @resolver.registry.fetch("assets").select do |asset|
        asset.fetch("product_id") == product_id &&
          asset.fetch("source_authenticity") == "OFFICIAL_MARKETING_ASSET" &&
          asset.fetch("usage_scope") == "DESIGN_PRODUCTION_APPROVED"
      end.flat_map { |asset| asset.fetch("visual_purposes") }.uniq
    end

    def readiness_context(case_id)
      path = File.join(root, "production_registry", "readiness_snapshot.yaml")
      return {"overall_status" => "INTERNAL_DRAFT", "domains" => {}} unless File.file?(path)
      snapshot = YAML.safe_load(File.read(path), permitted_classes: [Date, Time], aliases: true)
      snapshot.fetch("cases").find { |item| item.fetch("case_id") == case_id } || {"overall_status" => "INTERNAL_DRAFT", "domains" => {}}
    end

    def production_footer_adapter
      footer = Support.load_yaml(root, "production_registry/footer/switchbot_jp_footer.yaml")
      legal = Support.load_yaml(root, "production_registry/legal/legal_registry.yaml")
      company = footer.fetch("company")
      links_by_id = legal.fetch("static_links").to_h { |item| [item.fetch("legal_id"), item] }
      {
        "component_id" => footer.fetch("component_id"),
        "brand" => {"value" => company.fetch("brand")},
        "company" => {"value" => company.fetch("legal_name")},
        "address" => {"value" => company.fetch("address")},
        "official_store" => {"value" => company.fetch("official_store")},
        "support_email" => {"value" => company.fetch("support_email")},
        "support_phone" => {"value" => company.fetch("support_phone")},
        "copyright" => {"value" => "Copyright © {{current_year}} SwitchBot, Inc. All rights reserved."},
        "preference_center" => {"label" => {"value" => footer.dig("runtime_tokens", "preference_center", "label")}, "url" => {"value" => footer.dig("runtime_tokens", "preference_center", "token")}},
        "unsubscribe" => {"label" => {"value" => footer.dig("runtime_tokens", "unsubscribe", "label")}, "url" => {"value" => footer.dig("runtime_tokens", "unsubscribe", "token")}},
        "required_legal" => footer.fetch("required_legal_ids").map { |legal_id| {"label" => links_by_id.fetch(legal_id).fetch("label"), "url" => links_by_id.fetch(legal_id).fetch("url")} },
        "approval" => {
          "legal_approved_for_new_production" => {"value" => %w[APPROVED INHERITED_APPROVAL].include?(legal.dig("approval", "static_legal_package", "status"))},
          "static_footer_reusable" => {"value" => %w[APPROVED INHERITED_APPROVAL].include?(footer.dig("approval", "static_footer", "status"))},
          "runtime_links_resolved" => {"value" => footer.dig("approval", "esp_token_contract", "status") == "APPROVED"}
        }
      }
    end

    def resolve_assets(product_id, modules)
      modules.each_with_object([]) do |mod, rows|
        next unless mod["visual_purpose"]
        rows << @resolver.resolve(product_id: product_id, module_id: mod.fetch("instance_id"), visual_purpose: mod.fetch("visual_purpose"))
      end
    end

    def rebalance_modules(modules, copy)
      dropped_roles = copy.fetch("dropped_optional_copy", []).map { |item| item.fetch("role") }
      return modules if dropped_roles.empty?

      modules.reject do |mod|
        mod.fetch("module_id") == "MOD-STORY-FAQ" && (dropped_roles & %w[use_condition condition_disclaimer]).any?
      end
    end

    def validate_frozen_dependencies!(decision, modules)
      templates = Support.load_yaml(root, "design_system/templates_v1.0.yaml")
      module_library = Support.load_yaml(root, "design_system/modules_v1.0.yaml")
      template_ids = templates.fetch("templates").map { |item| item.fetch("template_id") }
      module_ids = module_library.fetch("modules").map { |item| item.fetch("module_id") }
      raise "Unknown frozen template #{decision.fetch("selected_template")}" unless template_ids.include?(decision.fetch("selected_template"))
      invalid = modules.map { |item| item.fetch("module_id") }.uniq - module_ids
      raise "Unknown frozen modules: #{invalid.join(", ")}" unless invalid.empty?
      standard = Support.load_yaml(root, "standards/edm_design_rules_v1.0.yaml")
      raise "Frozen standard status changed" unless standard.fetch("status").to_s.casecmp("Frozen").zero?
    end

    def truth_completeness(product)
      critical = [
        product.dig("product", "official_name_ja"),
        product.dig("product", "official_name_en"),
        product.dig("product", "category"),
        product.dig("product", "positioning"),
        product.dig("product", "target_audience"),
        product.dig("message", "primary_value"),
        product.dig("message", "primary_usp"),
        product.dig("claims", "source"),
        product.dig("specs", "source"),
        product["compatibility"],
        product["proof"],
        product["service"],
        product["assets"]
      ]
      ready = critical.count do |item|
        state = item.is_a?(Array) ? (item.empty? ? "MISSING" : "VERIFIED") : Support.status(item)
        %w[VERIFIED VERIFIED_FROM_OFFICIAL_SOURCE VERIFIED_EXISTING_CLAIM LOCALIZATION_CANDIDATE APPROVED INHERITED_APPROVAL NOT_REQUIRED].include?(state)
      end
      {
        "complete_fields" => ready,
        "total_fields" => critical.length,
        "percent" => (ready.fdiv(critical.length) * 100).round(1),
        "external_publish_ready" => Support.value(product.dig("status", "external_publish_ready"))
      }
    end

    def traceability(product_id, product, campaign, assets, copy)
      pricing = Support.load_yaml(root, "production_truth/pricing/#{product_id}.yaml")
      proof = Support.load_yaml(root, "production_truth/proof/#{product_id}.yaml")
      {
        "claims" => {
          "approved_used" => [],
          "verified_existing_used" => copy.fetch("entries").flat_map { |entry| entry.fetch("claim_ids", []) }.uniq,
          "non_numeric_source_copy" => product.fetch("copy_candidates").map { |key, value| {"key" => key, "source" => value["source"], "status" => value["status"]} },
          "excluded_claims" => product.dig("claims", "conditional").to_a + product.dig("claims", "prohibited").to_a
        },
        "price" => {"record" => pricing, "used_in_copy" => false},
        "assets" => assets.map { |item| item.slice("asset_id", "source_path", "source_url", "approval_scope", "visual_purpose") },
        "proof" => {"record" => proof, "used_in_copy" => false},
        "cta" => campaign.fetch("cta")
      }
    end
  end
end
