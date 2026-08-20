# frozen_string_literal: true

module EDMGenerator
  class MessagePlanner
    MESSAGE_INTENTS = {
      "new_product_value_understanding" => "新品の価値を一つの主命題で理解できるようにする",
      "problem_recognition_then_product_solution" => "生活上の課題を示し、製品による解決方向へつなぐ",
      "new_product_desirability_in_context" => "使用シーンから新品への関心を高める",
      "theme_relevance_then_offer_conversion" => "テーマとの関連を示した後、対象オファーへ案内する",
      "multi_product_offer_discovery" => "複数製品の対象オファーを比較しやすく提示する",
      "deadline_driven_conversion" => "確認済みの終了時点と次の行動を明確に伝える",
      "single_product_purchase_confidence" => "単品の価値と根拠を順に示し、購入判断を支える",
      "single_product_offer_conversion" => "単品の価値を保ちながら、確認済みオファーへ案内する",
      "problem_and_solution_understanding" => "課題と解決の考え方を順序立てて理解できるようにする",
      "mechanism_or_setup_understanding" => "仕組みまたは設定手順を視覚的に理解できるようにする",
      "choice_framework_and_product_fit" => "選び方を先に示し、製品ごとの適合を判断できるようにする",
      "category_context_and_product_discovery" => "カテゴリーの入口を示し、複数製品の発見へつなぐ",
      "multi_product_choice_decision" => "現在の候補から自分に合う製品を選べるようにする",
      "brand_meaning_and_trust" => "ブランドの考え方と信頼の根拠を一つの物語で伝える",
      "ecosystem_relationship_understanding" => "複数製品の関係性を理解できるようにする"
    }.freeze

    def initialize(repository)
      @repository = repository
    end

    def call(brief, selection, generated_at)
      objective = brief.dig("campaign", "objective")
      primary_message = MESSAGE_INTENTS[objective] || "Unknown"
      products = brief.dig("product", "records") || []
      approved_claims = products.flat_map { |item| item["approved_external_claim_ids"] || [] }.uniq
      promotion = brief.dig("campaign", "promotion")
      cta = brief.dig("campaign", "cta_destination")

      checks = {
        "objective_unique" => objective != "Unknown",
        "message_conflict" => false,
        "message_overload" => false,
        "promotion_overload" => promotion["level"] == "high" && promotion["status"] != "Resolved",
        "cta_intent_resolved" => cta["status"] == "Resolved"
      }

      Helpers.base_metadata(@repository, generated_at, "message_hierarchy").merge(
        "status" => selection["selected_template_id"] ? "planned" : "blocked_before_planning",
        "primary_objective" => objective,
        "primary_message" => primary_message,
        "primary_usp" => approved_claims.empty? ? {
          "value" => "Pending Verification",
          "status" => "Requires Claim Check",
          "note" => "Product Knowledge has no Approved External Claim for this fixture."
        } : {
          "claim_ids" => approved_claims,
          "status" => "Approved Source Available"
        },
        "secondary_usps" => [],
        "proof" => {
          "status" => "Requires Claim Check",
          "allowed_types" => ["approved product fact", "sourced review", "approved award", "verified UI or product visual"]
        },
        "promotion" => {
          "level" => promotion["level"],
          "status" => promotion["status"],
          "expression" => promotion["status"] == "Resolved" && promotion["level"] != "none" ? "Offer fact slot reserved; no amount invented" : "No offer copy generated"
        },
        "cta" => {
          "intent" => cta_intent(objective),
          "destination_status" => cta["status"],
          "destination" => cta["url_or_route"],
          "fixture_id" => cta["fixture_id"]
        },
        "checks" => checks,
        "risk_flags" => checks.select { |_, value| value == true }.keys & %w[message_conflict message_overload promotion_overload]
      )
    end

    private

    def cta_intent(objective)
      case objective
      when "deadline_driven_conversion", "single_product_offer_conversion", "multi_product_offer_discovery"
        "対象内容を確認する"
      when "choice_framework_and_product_fit", "multi_product_choice_decision", "category_context_and_product_discovery"
        "製品を比較・確認する"
      else
        "詳細を確認する"
      end
    end
  end
end

