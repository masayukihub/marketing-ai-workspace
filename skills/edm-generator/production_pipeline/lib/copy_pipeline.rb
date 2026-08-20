# frozen_string_literal: true

require_relative "support"

module ProductionEDM
  class CopyPipeline
    VISUAL_CLAIM_STATUSES = %w[APPROVED INHERITED_APPROVAL VERIFIED_EXISTING_CLAIM].freeze
    FINAL_CLAIM_STATUSES = %w[APPROVED INHERITED_APPROVAL].freeze
    PIPELINE_STAGES = [
      "Draft",
      "Product Name Check",
      "Claim Mapping",
      "Japanese Localization",
      "Brand Tone Check",
      "Repetition Check",
      "Length Check",
      "Grammar QA",
      "Production Candidate"
    ].freeze
    FORBIDDEN_PATTERNS = [
      /日本第一|No\.1|99\.9%|100%|ゼロリスク|絶対的な安心|78\.6%|20dB|最大1,?000回/
    ].freeze

    def build(product:, campaign:, decision:, case_id:, claim_registry:, final_copy_status:)
      entries = decision.fetch("campaign_type") == "product_education" ? daily_entries(product, campaign) : lock_entries(product, campaign)
      claim_map = claim_registry.fetch("copy_claim_map").fetch(case_id)
      non_factual_roles = claim_registry.fetch("non_factual_copy_roles").fetch(case_id)
      claims_by_id = claim_registry.fetch("claims").to_h { |claim| [claim.fetch("claim_id"), claim] }
      dropped = []
      entries.each do |item|
        role = item.fetch("role")
        ids = Array(claim_map[role]).compact
        item["claim_ids"] = ids
        item["factual"] = !ids.empty?
        mapped_or_non_factual = item["factual"] || non_factual_roles.include?(role)
        unresolved = ids.map do |claim_id|
          claim = claims_by_id.fetch(claim_id)
          claim_id unless VISUAL_CLAIM_STATUSES.include?(claim.fetch("status"))
        end.compact
        unresolved_primary = unresolved.select { |claim_id| claims_by_id.fetch(claim_id).fetch("requirement_level", "PRIMARY_REQUIRED") == "PRIMARY_REQUIRED" }
        unresolved_optional = unresolved - unresolved_primary
        item["claim_resolution"] = unresolved.empty? ? "PASS" : (unresolved_primary.empty? ? "DROP_OR_SUBSTITUTE" : "BLOCK")
        item["unresolved_claim_ids"] = unresolved
        item["mapped_or_non_factual"] = mapped_or_non_factual
        if item["factual"] && unresolved_primary.empty? && unresolved_optional.any? && unresolved_optional.length == ids.length
          dropped << {"role" => role, "text" => item.fetch("text"), "claim_ids" => ids, "reason" => "SECONDARY_OPTIONAL claim unavailable"}
          item["drop"] = true
          next
        end
        visual_claims = ids.all? { |claim_id| VISUAL_CLAIM_STATUSES.include?(claims_by_id.fetch(claim_id).fetch("status")) }
        final_claims = ids.all? { |claim_id| FINAL_CLAIM_STATUSES.include?(claims_by_id.fetch(claim_id).fetch("status")) }
        whole_email_human_approval = final_copy_status == "APPROVED" && mapped_or_non_factual && visual_claims
        item["approval_status"] = if whole_email_human_approval || (final_copy_status == "APPROVED" && mapped_or_non_factual && final_claims)
                                    "APPROVED"
                                  elsif mapped_or_non_factual && unresolved_primary.empty?
                                    "COPY_PRODUCTION_CANDIDATE"
                                  else
                                    "BLOCKED"
                                  end
      end
      entries.reject! { |item| item["drop"] }
      text_blob = entries.map { |item| item.fetch("text") }.join("\n")
      forbidden = FORBIDDEN_PATTERNS.flat_map { |pattern| text_blob.scan(pattern) }
      unmapped_factual_roles = entries.reject { |item| item["factual"] || non_factual_roles.include?(item.fetch("role")) }.map { |item| item.fetch("role") }.uniq
      checks = {
        "product_name_check" => text_blob.include?(Support.value(product.dig("product", "official_name_ja"))),
        "claim_mapping" => unmapped_factual_roles.empty? && entries.none? { |item| item["claim_resolution"] == "BLOCK" },
        "japanese_localization" => japanese_localization_pass?(entries),
        "brand_tone" => forbidden.empty? && brand_tone_pass?(text_blob),
        "repetition" => repeated_lines(entries).empty?,
        "length" => length_pass?(entries),
        "grammar" => grammar_pass?(entries)
      }
      candidate = checks.values.all?
      {
        "pipeline" => PIPELINE_STAGES,
        "finalization_status" => candidate ? "COPY_PRODUCTION_CANDIDATE" : "BLOCKED",
        "verification_status" => candidate ? "FACTS_VERIFIED_LOCALIZATION_CANDIDATE" : "BLOCKED",
        "approval_status" => final_copy_status == "APPROVED" ? "APPROVED" : (candidate ? "COPY_PRODUCTION_CANDIDATE" : "BLOCKED"),
        "scope" => final_copy_status == "APPROVED" ? "production" : (candidate ? "visual_deliverable_candidate" : "internal_draft"),
        "entries" => entries,
        "dropped_optional_copy" => dropped,
        "auto_qa" => checks,
        "checks" => {
          "product_name_present" => checks.fetch("product_name_check"),
          "forbidden_claim_hits" => forbidden,
          "numeric_performance_claims" => text_blob.scan(/\b(?:\d+(?:\.\d+)?%|\d+dB|\d+年|\d+回)\b/),
          "price_tokens" => text_blob.scan(/¥|円|OFF|クーポン/),
          "repeated_non_cta_lines" => repeated_lines(entries),
          "unmapped_factual_roles" => unmapped_factual_roles
        }
      }
    end

    private

    def entry(role, text, source, evidence_status: "LOCALIZATION_CANDIDATE", approval_status: "COPY_PRODUCTION_CANDIDATE")
      {"role" => role, "text" => text, "source" => source, "evidence_status" => evidence_status, "approval_status" => approval_status}
    end

    def candidate(product, key)
      item = product.fetch("copy_candidates").fetch(key)
      [Support.value(item), item.fetch("source"), item.fetch("status")]
    end

    def lock_entries(product, campaign)
      name = Support.value(product.dig("product", "official_name_ja"))
      hero, hero_source, hero_status = candidate(product, "hero_headline")
      hero_body, hero_body_source, hero_body_status = candidate(product, "hero_body")
      lifestyle, lifestyle_source, lifestyle_status = candidate(product, "lifestyle_title")
      identity, identity_source, identity_status = candidate(product, "product_identity_title")
      purchase, purchase_source, purchase_status = candidate(product, "purchase_check_title")
      disclaimer, disclaimer_source, disclaimer_status = candidate(product, "disclaimer")
      cta = Support.value(campaign.dig("cta", "copy"))
      [
        entry("product_name", name, product.dig("product", "official_name_ja", "source"), evidence_status: "VERIFIED"),
        entry("hero_headline", hero, hero_source, evidence_status: hero_status),
        entry("hero_body", hero_body, hero_body_source, evidence_status: hero_body_status),
        entry("lifestyle_heading", lifestyle, lifestyle_source, evidence_status: lifestyle_status),
        entry("lifestyle_body", "ブラックとシルバー。ドアまわりに合わせて選べる、2つのカラーをご用意しています。", "https://www.switchbot.jp/products/switchbot-lock-ultra", evidence_status: "VERIFIED_FROM_OFFICIAL_SOURCE"),
        entry("product_identity", identity, identity_source, evidence_status: identity_status),
        entry("product_identity_body", "マグネットセンサーでドアの開閉状態を検知し、自動で施錠。アプリでは、ドアの状態と開閉履歴を確認できます。", "https://www.switchbot.jp/products/switchbot-lock-ultra", evidence_status: "VERIFIED_EXISTING_CLAIM"),
        entry("pre_purchase_question", "ドアが閉まれば、そっと施錠。", "Phase 8 localization based on CLM-LOCK-FEATURE-004"),
        entry("problem_body", "マグネットセンサーがドアの開閉状態を検知し、自動で施錠します。", "https://www.switchbot.jp/products/switchbot-lock-ultra#ドアが閉まれば、そっと施錠", evidence_status: "VERIFIED_EXISTING_CLAIM"),
        entry("compatibility_heading", purchase, purchase_source, evidence_status: purchase_status),
        entry("compatibility_disclaimer", "購入前に適合性を確認してください。取り付け後は、アプリの手順に沿って解施錠位置を自動で調節します。", "https://www.switchbot.jp/products/switchbot-lock-ultra", evidence_status: "VERIFIED_EXISTING_CLAIM"),
        entry("check_item", "サムターンの中心からドア枠までの距離", "https://www.switchbot.jp/products/switchbot-lock-ultra#ご購入前に必ずご確認ください", evidence_status: "VERIFIED_EXISTING_CLAIM"),
        entry("check_item", "対応するサムターンの種類", "https://www.switchbot.jp/products/switchbot-lock-ultra#ご購入前に必ずご確認ください", evidence_status: "VERIFIED_EXISTING_CLAIM"),
        entry("check_item", "高さ調節ケースやアタッチメントの要否", "https://www.switchbot.jp/products/switchbot-lock-ultra#ご購入前に必ずご確認ください", evidence_status: "VERIFIED_EXISTING_CLAIM"),
        entry("mid_cta", "取り付け条件を確認する", campaign.dig("cta", "url", "source")),
        entry("mid_cta_body", "ご自宅のドアに取り付けられるか、公式ページで確認できます。", "Phase 8 CTA localization"),
        entry("final_cta_title", "ロックUltraを、さらに詳しく。", "Phase 8 CTA localization"),
        entry("final_cta_body", "現在の製品情報と取り付け条件を、公式ページでご確認ください。", "Phase 8 CTA localization"),
        entry("final_cta", cta, campaign.dig("cta", "copy", "source"), evidence_status: "VERIFIED")
      ]
    end

    def daily_entries(product, campaign)
      name = Support.value(product.dig("product", "official_name_ja"))
      hero, hero_source, hero_status = candidate(product, "hero_headline")
      body, body_source, body_status = candidate(product, "hero_body")
      one, one_source, one_status = candidate(product, "one_screen_title")
      ui, ui_source, ui_status = candidate(product, "ui_title")
      env, env_source, env_status = candidate(product, "environment_title")
      schedule, schedule_source, schedule_status = candidate(product, "schedule_title")
      disclaimer, disclaimer_source, disclaimer_status = candidate(product, "disclaimer")
      cta = Support.value(campaign.dig("cta", "copy"))
      [
        entry("product_name", name, product.dig("product", "official_name_ja", "source"), evidence_status: "VERIFIED"),
        entry("hero_headline", hero, hero_source, evidence_status: hero_status),
        entry("hero_body", body, body_source, evidence_status: body_status),
        entry("one_screen_heading", one, one_source, evidence_status: one_status),
        entry("one_screen_body", "毎日見る情報を、一つのデバイス画面で確認。", "https://www.switchbot.jp/products/switchbot-weather-station", evidence_status: "VERIFIED"),
        entry("device_ui_heading", ui, ui_source, evidence_status: ui_status),
        entry("device_ui_body", "公式のデバイス画面で、表示内容と情報のまとまり方を確認できます。", "https://www.switchbot.jp/products/switchbot-weather-station", evidence_status: "VERIFIED"),
        entry("environment_heading", env, env_source, evidence_status: env_status),
        entry("environment_body", "室内外の情報と天気を、公式画面例で確認できます。", "https://www.switchbot.jp/products/switchbot-weather-station", evidence_status: "VERIFIED"),
        entry("schedule_heading", schedule, schedule_source, evidence_status: schedule_status),
        entry("schedule_body", "予定と日々の情報を同じデバイス画面で見る、という製品の使い方を確認します。", "https://www.switchbot.jp/products/switchbot-weather-station", evidence_status: "VERIFIED"),
        entry("use_condition", "天気予報と室内外の温湿度", "https://www.switchbot.jp/products/switchbot-weather-station", evidence_status: "VERIFIED_EXISTING_CLAIM"),
        entry("use_condition", "家族の予定を共有する画面構成", "https://www.switchbot.jp/products/switchbot-weather-station", evidence_status: "VERIFIED_EXISTING_CLAIM"),
        entry("use_condition", "公式ページに掲載された現在の画面例", "https://www.switchbot.jp/products/switchbot-weather-station", evidence_status: "VERIFIED_EXISTING_CLAIM"),
        entry("condition_disclaimer", "機能ごとの連携条件は、公式製品ページの最新情報でご確認ください。", disclaimer_source, evidence_status: disclaimer_status),
        entry("mid_cta", "表示内容を確認", campaign.dig("cta", "url", "source")),
        entry("mid_cta_body", "公式ページで現在の画面例と条件を確認する。", "Phase 7 CTA localization"),
        entry("final_cta_title", "製品情報を、公式ページで確認。", "Phase 7 CTA localization"),
        entry("final_cta_body", "現在の表示内容・対応条件・購入情報をご確認ください。", "Phase 7 CTA localization"),
        entry("final_cta", cta, campaign.dig("cta", "copy", "source"), evidence_status: "VERIFIED")
      ]
    end

    def repeated_lines(entries)
      values = entries.reject { |item| item.fetch("role").include?("cta") }.map { |item| item.fetch("text") }
      counts = values.each_with_object(Hash.new(0)) { |value, memo| memo[value] += 1 }
      counts.select { |_, count| count > 1 }.keys
    end

    def japanese_localization_pass?(entries)
      entries.all? do |item|
        text = item.fetch("text").to_s
        !text.empty? && !text.match?(/或者|点击|确认|产品|未解決URL|Phase\s*[0-9]/i)
      end
    end

    def brand_tone_pass?(text)
      !text.match?(/革新的|圧倒的|究極|次世代|絶対的な安心|業界\s*No\.?1|AIが選んだ|スマートな暮らし/)
    end

    def length_pass?(entries)
      entries.all? do |item|
        limit = item.fetch("role").include?("headline") || item.fetch("role").include?("heading") || item.fetch("role").include?("title") ? 60 : 140
        item.fetch("text").to_s.length <= limit
      end
    end

    def grammar_pass?(entries)
      entries.all? do |item|
        text = item.fetch("text").to_s
        !text.match?(/[。！？]{2,}/) && text.count("（") == text.count("）") && !text.match?(/\s{2,}/)
      end
    end
  end
end
