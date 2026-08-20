# frozen_string_literal: true

module EDMGenerator
  class CopyPlanner
    def initialize(repository)
      @repository = repository
    end

    def call(brief, message, composition, generated_at)
      products = brief.dig("product", "records") || []
      product_names = products.map { |item| item["official_name_ja"] == "Pending Verification" ? item["official_name_en"] : item["official_name_ja"] }
      theme = brief.dig("campaign", "theme")
      objective = brief.dig("campaign", "objective")
      cta = message.dig("cta", "intent")
      subject = subject_for(theme, product_names)
      h1 = h1_for(theme, product_names)
      module_copy = composition.fetch("module_sequence").map do |item|
        copy_for_module(item, theme, product_names, cta)
      end

      Helpers.base_metadata(@repository, generated_at, "japanese_copy_draft").merge(
        "status" => composition["status"].start_with?("blocked") ? "blocked_before_copy" : "draft_requires_verification",
        "copy_stage" => "design-ready draft; not final polished copy",
        "subject" => {
          "text" => subject,
          "status" => "Draft / Requires Localization Review",
          "fact_dependency" => "campaign theme and verified product identity"
        },
        "preview" => {
          "text" => "内容をわかりやすくご案内します。",
          "status" => "Draft / No Product Claim"
        },
        "h1" => {
          "text" => h1,
          "length" => h1.length,
          "status" => h1.length <= 28 ? "Within Soft Default" : "Explain",
          "fact_dependency" => "no unapproved product capability used"
        },
        "module_copy" => module_copy,
        "cta" => {
          "text" => cta,
          "status" => brief.dig("campaign", "cta_destination", "status") == "Resolved" ? "Intent Resolved / Destination Fixture Only" : "Blocked / Destination Missing"
        },
        "copy_checks" => {
          "placeholder_in_final" => false,
          "unapproved_claim_used" => false,
          "invented_price_used" => false,
          "invented_deadline_used" => false,
          "official_japanese_product_name_verified" => products.empty? || products.all? { |item| item["official_name_ja"] != "Pending Verification" },
          "final_copy_allowed" => false
        },
        "objective" => objective,
        "note" => "事实槽位保留为结构化状态，不用看似完成的句子代替未知 Product Claim、Price 或 Period。"
      )
    end

    private

    def subject_for(theme, product_names)
      lead = product_names.first || "SwitchBot"
      "【#{lead}】#{theme}のご案内"
    end

    def h1_for(theme, product_names)
      lead = product_names.first
      return "#{theme}を、もっとわかりやすく。" unless lead
      "#{lead}を、わかりやすく。"
    end

    def copy_for_module(item, theme, product_names, cta)
      module_id = item["module_id"]
      headline, body, status = case module_id
                               when /HERO/
                                 ["#{theme}を、ひとつの流れで。", "製品・活動の確認済み情報をもとに、主要メッセージを配置します。", "Draft / Requires Claim Check"]
                               when /PROBLEM/
                                 ["まず、課題を整理。", "ユーザー課題は Campaign Brief または承認済み VOC から確定してください。", "Requires Source"]
                               when /PRIMARY-USP/
                                 ["選ぶ理由を、ひと目で。", "Approved Claim を取得後、Primary USP を一つだけ反映します。", "Requires Claim Check"]
                               when /PRODUCT-DETAIL|FEATURE|APP-UI/
                                 ["ポイントを詳しく確認。", "仕様・機能・UI は Product Knowledge の Approved Fact と公式素材を受け取るまで確定しません。", "Requires Claim and Asset Check"]
                               when /PRODUCT-GRID|COMPARISON|PRODUCT-CARD/
                                 ["目的に合う製品をチェック。", product_names.empty? ? "製品一覧は Product Knowledge 解決後に反映します。" : product_names.join(" / "), "Product Identity Only / Claims Pending"]
                               when /PRICE|COUPON|OFFER|LAST-CHANCE/
                                 ["キャンペーン情報を確認。", "価格・割引・期間は現在のチャネル別ソース確認後に反映します。", "Requires Promotion Verification"]
                               when /REVIEW|AWARD|USER-VOICE|WARRANTY/
                                 ["信頼できる根拠を確認。", "出典と使用条件が確認できた Proof のみを反映します。", "Requires Source"]
                               when /CTA/
                                 [cta, "リンク先が確認できるまで Final には進みません。", "CTA Intent Draft"]
                               when /FOOTER/
                                 ["SwitchBot", "必要な法務情報、配信情報、確認済みリンクを配置します。", "Structure Draft"]
                               else
                                 ["次のポイントへ。", "このモジュールは Primary Objective の一つの問いに回答します。", "Structure Draft"]
                               end
      {
        "module_id" => module_id,
        "headline" => headline,
        "body" => body,
        "status" => status,
        "source_binding" => item["message_assignment"]
      }
    end
  end
end

