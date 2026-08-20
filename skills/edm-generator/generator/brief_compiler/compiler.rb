# frozen_string_literal: true

module EDMGenerator
  class BriefCompiler
    include Helpers

    FIELD_POLICY = {
      "product" => "Must Verify",
      "campaign_theme" => "Can Infer",
      "objective" => "Must Verify",
      "promotion" => "Must Verify",
      "period" => "Can Default",
      "cta_destination" => "Must Verify"
    }.freeze

    def initialize(repository)
      @repository = repository
    end

    def call(test_case, generated_at)
      inputs = test_case.fetch("inputs")
      context = test_case.fetch("selection_context")
      product_input = inputs["product"] || {}
      product_ids = product_input["product_ids"] || []
      products = product_ids.map { |id| @repository.product_knowledge.resolve(id) }
      product_status = if product_input["scope"] == "brand"
                         "Resolved"
                       elsif products.empty? || products.any? { |item| item["status"] == "Blocked" }
                         "Blocked"
                       elsif products.all? { |item| item["external_publish_ready"] }
                         "Resolved"
                       else
                         "Partial"
                       end

      theme = present(inputs["campaign_theme"])
      objective = present(inputs["objective"])
      promotion = normalize_promotion(inputs["promotion"])
      period = normalize_period(inputs["period"], promotion)
      cta = normalize_cta(inputs["cta_destination"])

      fields = [
        field("product", product_input, product_status, product_status == "Blocked" ? "PRODUCT_IDENTITY_UNRESOLVED" : nil),
        field("campaign_theme", theme || "Unknown", theme ? "Resolved" : "Unknown", theme ? nil : "CAMPAIGN_THEME_UNRESOLVED"),
        field("objective", objective || "Unknown", objective ? "Resolved" : "Blocked", objective ? nil : "PRIMARY_OBJECTIVE_MISSING_OR_MULTIPLE"),
        field("promotion", promotion, promotion["status"], promotion["failure_code"]),
        field("period", period, period["status"], period["failure_code"]),
        field("cta_destination", cta, cta["status"], cta["failure_code"])
      ]

      unresolved = fields.select { |item| %w[Blocked Unknown Conflict Partial Unverified].include?(item["status"]) }
      production_gates = unresolved.map { |item| item["failure_code"] }.compact.uniq
      products.each do |product|
        production_gates << "PRODUCT_KNOWLEDGE_NOT_EXTERNAL_READY" unless product["external_publish_ready"]
        production_gates << "APPROVED_CLAIM_REQUIRED" if product.fetch("approved_external_claim_ids", []).empty?
        production_gates << "CURRENT_PRICE_REQUIRED" if %w[low medium high].include?(promotion["level"]) && !product["current_price_ready"]
      end
      production_gates << "ASSET_PROVENANCE_MISSING" if context["asset_availability"] == "missing_required"

      status = if product_status == "Blocked" || objective.nil?
                 "Blocked"
               elsif unresolved.empty? && products.all? { |item| item["external_publish_ready"] }
                 "Resolved"
               else
                 "Partial"
               end

      Helpers.base_metadata(@repository, generated_at, "campaign_brief").merge(
        "test_case_id" => test_case.fetch("test_case_id"),
        "status" => status,
        "input_original" => inputs,
        "input_resolution" => fields,
        "campaign" => {
          "type" => context["campaign_type"] || "Unknown",
          "theme" => theme || "Unknown",
          "objective" => objective || "Unknown",
          "audience" => inputs["audience"] || "Japan market consumers",
          "audience_status" => inputs["audience"] ? "Resolved" : "Inferred Default",
          "promotion" => promotion,
          "period" => period,
          "cta_destination" => cta
        },
        "product" => {
          "scope" => product_input["scope"] || "Unknown",
          "count" => context["product_count"] || products.length,
          "records" => products,
          "brand" => product_input["brand"],
          "identity_status" => product_status
        },
        "selection_context" => context,
        "verification" => {
          "product_knowledge_snapshot" => @repository.product_knowledge.index["as_of"],
          "external_publication_ready" => @repository.product_knowledge.publication_ready?,
          "production_gates" => production_gates.uniq,
          "fixture_warning" => "verified_test_fixture validates Generator logic only and is not approval for external publication."
        }
      )
    end

    private

    def present(value)
      value unless value.nil? || value.to_s.strip.empty?
    end

    def field(name, normalized, status, failure_code)
      {
        "field" => name,
        "normalized" => normalized,
        "missing_policy" => FIELD_POLICY.fetch(name),
        "status" => status,
        "failure_code" => failure_code
      }
    end

    def normalize_promotion(value)
      return {
        "level" => "Unknown",
        "state" => "Unknown",
        "status" => "Unknown",
        "failure_code" => "REQUIRED_INPUT_UNRESOLVED"
      } if value.nil?

      level = value["level"] || "Unknown"
      state = value["state"] || "Unknown"
      status = if level == "none"
                 "Resolved"
               elsif %w[verified verified_test_fixture].include?(state)
                 "Resolved"
               else
                 "Unverified"
               end
      {
        "level" => level,
        "state" => state,
        "deadline" => value["deadline"],
        "offer_facts" => value["offer_facts"],
        "status" => status,
        "failure_code" => status == "Unverified" ? "PROMOTION_FACT_UNVERIFIED" : nil
      }
    end

    def normalize_period(value, promotion)
      return {
        "state" => "Unknown",
        "status" => promotion["level"] == "none" ? "Not Applicable" : "Unknown",
        "failure_code" => promotion["level"] == "none" ? nil : "PROMOTION_FACT_UNVERIFIED"
      } if value.nil?

      state = value["state"] || "Unknown"
      status = case state
               when "verified", "verified_test_fixture" then "Resolved"
               when "not_applicable_or_runtime", "Not Applicable" then "Not Applicable"
               else "Unverified"
               end
      {
        "start" => value["start"],
        "end" => value["end"],
        "timezone" => value["timezone"] || "Asia/Tokyo",
        "state" => state,
        "status" => status,
        "failure_code" => status == "Unverified" ? "PROMOTION_FACT_UNVERIFIED" : nil
      }
    end

    def normalize_cta(value)
      return {
        "state" => "Unknown",
        "destination_type" => "Unknown",
        "url_or_route" => nil,
        "status" => "Blocked",
        "failure_code" => "CTA_DESTINATION_INVALID"
      } if value.nil?

      state = value["state"] || "Unknown"
      verified = %w[verified verified_test_fixture].include?(state)
      {
        "state" => state,
        "destination_type" => value["destination_type"] || "fixture_route",
        "url_or_route" => value["url_or_route"],
        "fixture_id" => value["fixture_id"],
        "status" => verified ? "Resolved" : "Unverified",
        "failure_code" => verified ? nil : "CTA_DESTINATION_INVALID"
      }
    end
  end
end
