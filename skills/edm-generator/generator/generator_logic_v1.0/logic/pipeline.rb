# frozen_string_literal: true

require_relative "support"
require_relative "brief_compiler/compiler"
require_relative "campaign_classifier/classifier"
require_relative "template_selector/selector"
require_relative "message_planner/planner"
require_relative "module_composer/composer"
require_relative "copy_planner/planner"
require_relative "asset_resolver/resolver"
require_relative "qa/checker"

module EDMGenerator
  class Pipeline
    attr_reader :repository

    def initialize(root)
      @repository = Repository.new(root)
      @brief_compiler = BriefCompiler.new(repository)
      @campaign_classifier = CampaignClassifier.new(repository)
      @template_selector = TemplateSelector.new(repository)
      @message_planner = MessagePlanner.new(repository)
      @module_composer = ModuleComposer.new(repository)
      @copy_planner = CopyPlanner.new(repository)
      @asset_resolver = AssetResolver.new(repository)
      @qa_checker = QAChecker.new(repository)
    end

    def run(test_case, generated_at: Time.now.iso8601)
      brief = @brief_compiler.call(test_case, generated_at)
      classification = @campaign_classifier.call(brief, generated_at)
      selection = @template_selector.call(brief, classification, generated_at)
      message = @message_planner.call(brief, selection, generated_at)
      composition = @module_composer.call(brief, selection, message, generated_at)
      copy = @copy_planner.call(brief, message, composition, generated_at)
      assets = @asset_resolver.call(brief, composition, generated_at)
      qa = @qa_checker.call(test_case, brief, classification, selection, message, composition, copy, assets, generated_at)

      result = {
        "test_case_id" => test_case.fetch("test_case_id"),
        "name" => test_case.fetch("name"),
        "coverage" => test_case.fetch("coverage"),
        "input" => test_case.fetch("inputs"),
        "expected" => test_case.fetch("expected"),
        "brief" => brief,
        "classification" => classification,
        "selection" => selection,
        "message" => message,
        "composition" => composition,
        "copy" => copy,
        "assets" => assets,
        "qa" => qa
      }
      result["scores"] = score(result)
      result["structure_fingerprint"] = Helpers.fingerprint(result.reject { |key, _| key == "scores" })
      result
    end

    private

    def score(result)
      brief = result["brief"]
      qa = result["qa"]
      selection = result["selection"]
      expected = result["expected"]
      unresolved_count = brief.fetch("input_resolution").count { |field| !%w[Resolved Not Applicable Inferred\ Default].include?(field["status"]) }
      brief_score = [[5 - unresolved_count, 1].max, 5].min
      brief_score = [brief_score, 3].min unless brief.dig("verification", "external_publication_ready")
      classification_score = result.dig("classification", "status") == "classified" ? 5 : 1
      template_score = selection["selected_template_id"] == expected["selected_template_id"] ? 5 : 1
      message_score = if result.dig("message", "primary_message") == "Unknown"
                        1
                      elsif result.dig("message", "primary_usp", "status") == "Requires Claim Check"
                        4
                      else
                        5
                      end
      module_score = if expected["selected_template_id"].nil? && selection["selected_template_id"].nil?
                       5
                     elsif result.dig("composition", "composition_checks", "blocked").any?
                       2
                     elsif result.dig("composition", "composition_checks", "explain").any?
                       4
                     else
                       5
                     end
      copy_score = if selection["selected_template_id"].nil?
                     1
                   elsif result.dig("copy", "copy_checks", "official_japanese_product_name_verified") &&
                         result.dig("copy", "copy_checks", "final_copy_allowed")
                     5
                   elsif result.dig("brief", "campaign", "cta_destination", "status") != "Resolved"
                     2
                   else
                     3
                   end
      asset_score = qa.dig("asset_checks", "product_redraw_requested") ? 1 : 5
      rule_score = qa.fetch("unsafe_generator_violations").empty? ? 5 : 1
      scores = {
        "brief_completeness" => brief_score,
        "campaign_classification" => classification_score,
        "template_selection" => template_score,
        "message_hierarchy" => message_score,
        "module_composition" => module_score,
        "copy_usability" => copy_score,
        "asset_safety" => asset_score,
        "rule_compliance" => rule_score
      }
      scores["overall"] = (scores.values.sum.to_f / scores.length).round(2)
      scores["scale"] = "1–5"
      scores
    end
  end
end

