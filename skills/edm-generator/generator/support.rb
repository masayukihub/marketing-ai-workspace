# frozen_string_literal: true

require "yaml"
require "json"
require "digest"
require "time"
require "date"
require "fileutils"
require "csv"
require "cgi"

module EDMGenerator
  CONTRACT_VERSION = "1.0.0"
  DESIGN_STANDARD_VERSION = "1.0"
  DESIGN_SYSTEM_VERSION = "1.0.0"

  class Repository
    attr_reader :root, :standard, :templates_document, :modules_document,
                :selection_rules, :composition_rules, :visual_rhythm,
                :product_knowledge, :source_manifest

    def initialize(root)
      @root = File.expand_path(root)
      @standard = load_yaml("standards/edm_design_rules_v1.0.yaml")
      @templates_document = load_yaml("design_system/templates_v1.0.yaml")
      @modules_document = load_yaml("design_system/modules_v1.0.yaml")
      @selection_rules = load_yaml("design_system/template_selection_rules_v1.0.yaml")
      @composition_rules = load_yaml("design_system/module_composition_rules_v1.0.yaml")
      @visual_rhythm = File.read(path("design_system/visual_rhythm_rules_v1.0.md"))
      @product_knowledge = ProductKnowledge.new
      @source_manifest = build_source_manifest
      validate_frozen_sources!
    end

    def templates
      @templates ||= templates_document.fetch("templates").to_h { |item| [item.fetch("template_id"), item] }
    end

    def modules
      @modules ||= modules_document.fetch("modules").to_h { |item| [item.fetch("module_id"), item] }
    end

    def families
      @families ||= templates_document.fetch("template_families").to_h { |item| [item.fetch("family_id"), item] }
    end

    def path(relative)
      File.join(root, relative)
    end

    private

    def load_yaml(relative)
      YAML.safe_load(File.read(path(relative)), permitted_classes: [Date, Time], aliases: true)
    end

    def build_source_manifest
      files = [
        "standards/edm_design_standard_v1.0.md",
        "standards/edm_design_rules_v1.0.yaml",
        "design_system/templates_v1.0.yaml",
        "design_system/modules_v1.0.yaml",
        "design_system/template_selection_rules_v1.0.yaml",
        "design_system/module_composition_rules_v1.0.yaml",
        "design_system/visual_rhythm_rules_v1.0.md",
        "phase4_generator_contract.md",
        "generator/input_schema.yaml"
      ]
      files.map do |relative|
        absolute = path(relative)
        {
          "path" => relative,
          "sha256" => Digest::SHA256.file(absolute).hexdigest,
          "status" => "loaded"
        }
      end + product_knowledge.source_manifest
    end

    def validate_frozen_sources!
      raise "Design Standard is not frozen" unless standard["status"] == "frozen"
      raise "Templates are not frozen" unless templates_document["status"] == "Frozen"
      raise "Modules are not frozen" unless modules_document["status"] == "Frozen"
      raise "Template rules are not frozen" unless selection_rules["status"] == "Frozen"
      raise "Composition rules are not frozen" unless composition_rules["status"] == "Frozen"
      raise "Visual rhythm baseline missing" unless visual_rhythm.include?("Final Human Decision")
    end
  end

  class ProductKnowledge
    ROOT = "/Users/lai/.codex/skills/product-knowledge"
    INDEX = File.join(ROOT, "outputs/product_index.json")
    CLAIMS = File.join(ROOT, "references/claim.md")
    COMPLIANCE = File.join(ROOT, "references/compliance.md")
    KNOWN_ISSUES = File.join(ROOT, "references/known_issues.md")

    attr_reader :index

    def initialize
      @index = JSON.parse(File.read(INDEX))
      @products = index.fetch("products").to_h { |item| [item.fetch("product_id"), item] }
    end

    def resolve(product_id)
      record = @products[product_id]
      return {
        "product_id" => product_id,
        "status" => "Blocked",
        "failure_code" => "PRODUCT_IDENTITY_UNRESOLVED",
        "source_path" => relative(INDEX)
      } unless record

      profile = File.join(ROOT, "knowledge", record.fetch("profile_path"))
      {
        "product_id" => product_id,
        "official_name_en" => record.dig("official_name", "en"),
        "official_name_ja" => present(record.dig("official_name", "ja")) || "Pending Verification",
        "market" => record["market"],
        "identity_status" => record["review_status"],
        "completeness" => record["completeness"],
        "last_verified" => record["last_verified_date"],
        "external_publish_ready" => record["external_publish_ready"],
        "approved_external_claim_ids" => record.dig("readiness", "approved_external_claim_ids") || [],
        "current_price_ready" => record.dig("readiness", "current_price_ready"),
        "blocking_reasons" => record.dig("readiness", "blocking_reasons") || [],
        "source_path" => relative(INDEX),
        "profile_path" => File.exist?(profile) ? relative(profile) : "Not Available"
      }
    end

    def source_manifest
      [INDEX, CLAIMS, COMPLIANCE, KNOWN_ISSUES].map do |absolute|
        {
          "path" => relative(absolute),
          "sha256" => Digest::SHA256.file(absolute).hexdigest,
          "status" => "loaded",
          "last_verified" => index["as_of"]
        }
      end
    end

    def publication_ready?
      index["external_publication_ready"] == true
    end

    private

    def present(value)
      value unless value.nil? || value.to_s.strip.empty?
    end

    def relative(absolute)
      absolute.sub(ROOT + "/", "Product Knowledge/")
    end
  end

  module Helpers
    module_function

    def base_metadata(repository, generated_at, scope)
      {
        "contract_version" => CONTRACT_VERSION,
        "design_standard_version" => DESIGN_STANDARD_VERSION,
        "design_system_version" => DESIGN_SYSTEM_VERSION,
        "generated_at" => generated_at,
        "scope" => scope,
        "source_manifest" => repository.source_manifest
      }
    end

    def fingerprint(value)
      Digest::SHA256.hexdigest(JSON.generate(canonical(value)))
    end

    def canonical(value)
      case value
      when Hash
        value.reject { |key, _| key == "generated_at" }.sort.to_h.transform_values { |item| canonical(item) }
      when Array
        value.map { |item| canonical(item) }
      else
        value
      end
    end

    def yaml_dump(value)
      YAML.dump(value).sub(/\A---\s*\n/, "")
    end

    def write_yaml(path, value)
      FileUtils.mkdir_p(File.dirname(path))
      File.write(path, yaml_dump(value))
    end

    def write_text(path, value)
      FileUtils.mkdir_p(File.dirname(path))
      File.write(path, value)
    end

    def truthy?(value)
      value == true || value.to_s == "true"
    end

    def verified_fixture?(value)
      value.to_s == "verified_test_fixture"
    end

    def heading(text)
      text.to_s.gsub(/[#*_`]/, "").strip
    end
  end
end
