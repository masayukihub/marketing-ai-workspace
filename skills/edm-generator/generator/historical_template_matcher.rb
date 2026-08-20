# frozen_string_literal: true

require "yaml"

module EDMGenerator
  class HistoricalTemplateMatcher
    WEIGHTS = {
      "campaign_similarity" => 0.22,
      "objective_similarity" => 0.18,
      "sku_similarity" => 0.14,
      "content_depth_similarity" => 0.14,
      "promotion_similarity" => 0.12,
      "asset_similarity" => 0.10,
      "product_complexity_similarity" => 0.10
    }.freeze

    DEPTH = {"low" => 0, "medium" => 1, "high" => 2}.freeze
    PROMOTION = {"none" => 0, "low" => 1, "medium" => 2, "high" => 3}.freeze

    attr_reader :root, :library

    def initialize(root)
      @root = File.expand_path(root)
      @library = YAML.safe_load(File.read(File.join(@root, "templates", "historical", "library_v1.0.yaml")))
    end

    def rank(brief, limit: 3)
      normalized = normalize(brief)
      rankings = library.fetch("templates").map { |template| score(template, normalized) }.sort_by { |row| [-row.fetch("ranking_score"), -row.fetch("template_fit_score"), row.fetch("template_id")] }
      top = rankings.first
      explicit_new = normalized.fetch("new_structure_requested")
      {
        "schema_version" => "1.0.0",
        "historical_template_first" => true,
        "brief" => normalized,
        "weights" => WEIGHTS,
        "top_matches" => rankings.first(limit).map.with_index { |row, index| row.merge("rank" => index + 1) },
        "selected_template_id" => !explicit_new && top.fetch("template_fit_score") >= 50 ? top.fetch("template_id") : nil,
        "selected_reference_edm" => !explicit_new && top.fetch("template_fit_score") >= 50 ? top.fetch("reference_edm") : nil,
        "route" => explicit_new ? "User-requested New Design Candidate" : route(top.fetch("template_fit_score")),
        "generic_fallback_allowed" => explicit_new || top.fetch("template_fit_score") < 50,
        "human_review_required" => explicit_new || top.fetch("template_fit_score") < 80,
        "note" => "Top-3 is an evidence-backed shortlist. Human DELIVERABLE/MINOR_REVISION/MAJOR_REVISION/WRONG_TEMPLATE review remains the promotion gate."
      }
    end

    private

    def normalize(brief)
      {
        "campaign_type" => brief.fetch("campaign_type").to_s,
        "objective" => brief.fetch("objective").to_s,
        "product_count" => [brief.fetch("product_count", 1).to_i, 0].max,
        "promotion_level" => brief.fetch("promotion_level", "none").to_s,
        "content_depth" => brief.fetch("content_depth", "medium").to_s,
        "asset_types" => Array(brief.fetch("asset_types", [])).map(&:to_s).uniq,
        "product_complexity" => brief.fetch("product_complexity", "medium").to_s,
        "new_structure_requested" => brief.fetch("new_structure_requested", false) == true
      }
    end

    def score(template, brief)
      profile = template.fetch("fit_profile")
      dimensions = {
        "campaign_similarity" => campaign_score(brief.fetch("campaign_type"), template.fetch("campaign_types")),
        "objective_similarity" => objective_score(brief.fetch("objective"), profile.fetch("objectives")),
        "sku_similarity" => range_score(brief.fetch("product_count"), profile.fetch("sku_range")),
        "content_depth_similarity" => ordinal_score(brief.fetch("content_depth"), profile.fetch("content_depth"), DEPTH),
        "promotion_similarity" => allowed_ordinal_score(brief.fetch("promotion_level"), profile.fetch("promotion_levels"), PROMOTION),
        "asset_similarity" => asset_score(brief.fetch("asset_types"), profile.fetch("asset_types")),
        "product_complexity_similarity" => allowed_value_score(brief.fetch("product_complexity"), profile.fetch("product_complexity"))
      }
      raw_total = dimensions.sum { |name, value| value * WEIGHTS.fetch(name) }.round
      total = raw_total
      total = [total, 79].min if dimensions.fetch("asset_similarity") < 80
      total = [total, 49].min unless brief.fetch("asset_types").include?("product")
      direct = template.fetch("section_sequence").first(2)
      flexible = template.fetch("section_sequence").drop(2).reject { |name| name.match?(/footer/) }.first(3)
      {
        "template_id" => template.fetch("template_id"),
        "template_name" => template.fetch("template_name"),
        "reference_edm" => template.fetch("reference_edm"),
        "ranking_score" => raw_total,
        "template_fit_score" => total,
        "reuse_mode" => route(total),
        "dimension_scores" => dimensions,
        "why_similar" => explanations(dimensions, brief, template),
        "direct_reuse" => direct,
        "requires_adjustment" => flexible,
        "not_for" => template.fetch("not_for")
      }
    end

    def campaign_score(value, allowed)
      return 100 if allowed.include?(value)
      families = [
        %w[product_launch single_product_launch dual_product_launch],
        %w[single_product_conversion single_product_promotion],
        %w[theme_promotion category_promotion seasonal_campaign multi_product_promotion high_promotion countdown_last_chance],
        %w[product_education seasonal_education category_guide multi_product_comparison],
        %w[brand_story category_guide ecosystem_launch category_multi_product]
      ]
      families.any? { |family| family.include?(value) && (family & allowed).any? } ? 72 : 20
    end

    def objective_score(value, allowed)
      return 100 if allowed.include?(value)
      value_terms = value.split("_") - %w[and then the]
      overlap = allowed.map { |candidate| (value_terms & candidate.split("_")).length }.max.to_i
      overlap >= 2 ? 72 : (overlap == 1 ? 48 : 20)
    end

    def range_score(value, range)
      min, max = range.map(&:to_i)
      return 100 if value.between?(min, max)
      distance = value < min ? min - value : value - max
      [100 - distance * 35, 10].max
    end

    def ordinal_score(value, target, scale)
      return 100 unless scale.key?(value) && scale.key?(target)
      [100 - (scale.fetch(value) - scale.fetch(target)).abs * 38, 24].max
    end

    def allowed_ordinal_score(value, allowed, scale)
      return 100 if allowed.include?(value)
      scores = allowed.map { |target| ordinal_score(value, target, scale) }
      scores.max || 20
    end

    def asset_score(available, required)
      return 100 if required.empty?
      core = required.include?("product") && available.include?("product") ? 30 : 0
      optional = required - ["product"]
      return core if optional.empty?
      covered = (optional & available).length.fdiv(optional.length)
      (core + covered * 70).round
    end

    def allowed_value_score(value, allowed)
      return 100 if allowed.include?(value)
      allowed.empty? ? 50 : 35
    end

    def explanations(dimensions, brief, template)
      strongest = dimensions.sort_by { |_, score| -score }.first(3).map(&:first)
      [
        "#{brief.fetch("campaign_type")} 与 #{template.fetch("reference_campaign")} 的结构任务匹配度由 #{strongest.join(", ")} 支持。",
        "可直接继承 #{template.fetch("hero_structure")} 与 #{template.fetch("cta_pattern")}。",
        "只允许在 FLEXIBLE/OPTIONAL 区域适配；#{template.fetch("not_for")}。"
      ]
    end

    def route(score)
      return "Direct Reuse" if score >= 80
      return "Reuse + Adapt" if score >= 65
      return "Heavy Adapt + Human Review" if score >= 50

      "Generic / New Template Candidate"
    end
  end
end

if $PROGRAM_NAME == __FILE__
  root = File.expand_path("..", __dir__)
  brief_path = ARGV.fetch(0)
  brief = YAML.safe_load(File.read(brief_path))
  puts YAML.dump(EDMGenerator::HistoricalTemplateMatcher.new(root).rank(brief))
end
