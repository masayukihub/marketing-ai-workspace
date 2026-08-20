# frozen_string_literal: true

require "csv"
require "fileutils"
require "open3"
require "yaml"

ROOT = File.expand_path("..", __dir__)
TEMPLATE_ROOT = File.join(ROOT, "templates", "historical")

TEMPLATES = [
  {
    "template_id" => "HIST-TPL-001",
    "template_name" => "Pet Ecosystem Launch",
    "reference_edm" => "SBG_001",
    "reference_campaign" => "スマートペット家電 発売記念",
    "original_product" => "SwitchBot スマートペット家電",
    "campaign_types" => %w[product_launch ecosystem_launch category_multi_product],
    "best_for" => "2–6 SKU 的生态新品／组合发布，先讲组合价值再拆产品卡",
    "not_for" => "单一功能更新、短促销、缺少多产品官方素材的任务",
    "length_px" => 7043,
    "section_count" => 9,
    "module_count" => 22,
    "hero_structure" => "产品家族居中 Hero + 一个发布命题 + 次级优惠提示",
    "section_sequence" => ["launch_hero", "family_intro", "product_grid_a", "product_grid_b", "lifestyle_use_cases", "feature_detail", "app_ecosystem", "campaign_closure", "deep_footer"],
    "module_sequence" => ["MOD-HERO-PRODUCT", "MOD-STORY-PRIMARY-USP", "MOD-STORY-PRODUCT-GRID", "MOD-STORY-LIFESTYLE", "MOD-STORY-FEATURE-SPLIT", "MOD-STORY-APP-UI", "MOD-CONV-CTA-BAND", "MOD-SYSTEM-BRAND-FOOTER"],
    "cta_pattern" => "产品卡 CTA + 活动收束 CTA；每次重复绑定不同目的地",
    "footer_structure" => "服务／渠道／信任／品牌的深 Footer",
    "mobile_behavior" => "源码含单列适配；产品卡由双列转单列，CTA 保持全宽",
    "fit_profile" => {"objectives" => %w[ecosystem_value_understanding multi_product_discovery new_product_value_understanding], "sku_range" => [2, 6], "promotion_levels" => %w[low medium], "content_depth" => "high", "asset_types" => %w[product lifestyle app_ui], "product_complexity" => %w[medium high]},
    "palette" => {"paper" => "#fff7ec", "ink" => "#4d2d20", "primary" => "#f1474d", "secondary" => "#f3a51f", "dark" => "#4b120d"},
    "rhythm" => [1.18, 0.52, 0.92, 0.92, 1.12, 0.88, 0.72, 0.62, 0.86]
  },
  {
    "template_id" => "HIST-TPL-002",
    "template_name" => "Staged Product Reveal Launch",
    "reference_edm" => "SBG_007",
    "reference_campaign" => "Pro 产品发布",
    "original_product" => "Pro 系列双产品",
    "campaign_types" => %w[product_launch single_product_launch dual_product_launch],
    "best_for" => "高复杂度新品、需要大图分阶段揭示性能与使用场景的发布",
    "not_for" => "多 SKU 大促、简单配件、没有大幅产品／场景图的任务",
    "length_px" => 12_863,
    "section_count" => 8,
    "module_count" => 11,
    "hero_structure" => "Lifestyle 引入 + 大产品 Reveal；商业信息延后",
    "section_sequence" => ["lifestyle_launch_hero", "primary_value", "product_detail", "secondary_reveal", "feature_expansion", "installation_context", "commerce_bonus", "deep_footer"],
    "module_sequence" => ["MOD-HERO-PRODUCT", "MOD-STORY-LIFESTYLE", "MOD-STORY-PRIMARY-USP", "MOD-STORY-PRODUCT-DETAIL", "MOD-STORY-FEATURE-SPLIT", "MOD-CONV-CTA-BAND", "MOD-SYSTEM-BRAND-FOOTER"],
    "cta_pattern" => "Hero 后轻 CTA，产品理解完成后出现主要购买 CTA",
    "footer_structure" => "活动条件 + 品牌闭合的深 Footer",
    "mobile_behavior" => "单列大图；Copy 与产品 Reveal 交替，不压缩产品辨识度",
    "fit_profile" => {"objectives" => %w[new_product_value_understanding staged_product_reveal new_product_desirability_in_context], "sku_range" => [1, 2], "promotion_levels" => %w[none low], "content_depth" => "high", "asset_types" => %w[product lifestyle detail], "product_complexity" => %w[high]},
    "palette" => {"paper" => "#f7f4ef", "ink" => "#191919", "primary" => "#ea3323", "secondary" => "#d7cec1", "dark" => "#151515"},
    "rhythm" => [0.92, 1.28, 1.05, 1.18, 1.12, 0.96, 0.74, 0.82]
  },
  {
    "template_id" => "HIST-TPL-003",
    "template_name" => "Product-led Lifestyle Conversion",
    "reference_edm" => "SBG_016",
    "reference_campaign" => "木目調空気清浄機 新商品／販促",
    "original_product" => "SwitchBot 空気清浄機",
    "campaign_types" => %w[product_launch single_product_conversion single_product_promotion],
    "best_for" => "单品、家居场景、需要 Lifestyle→功能→细节→选择判断的任务",
    "not_for" => "Last Chance、多 SKU 分类页、无 Lifestyle 素材的任务",
    "length_px" => 6448,
    "section_count" => 9,
    "module_count" => 11,
    "hero_structure" => "产品与家居场景同屏，主承诺与一个行动入口",
    "section_sequence" => ["product_lifestyle_hero", "lifestyle_gallery", "feature_overview", "product_detail", "comparison", "offer", "related_products", "closing_cta", "deep_footer"],
    "module_sequence" => ["MOD-HERO-PRODUCT", "MOD-STORY-LIFESTYLE", "MOD-STORY-PRIMARY-USP", "MOD-STORY-PRODUCT-DETAIL", "MOD-STORY-COMPARISON", "MOD-CONV-CTA-BAND", "MOD-SYSTEM-BRAND-FOOTER"],
    "cta_pattern" => "Hero／中段／收束各一次，均围绕同一产品任务",
    "footer_structure" => "活动条件、信任资产与订阅关闭",
    "mobile_behavior" => "Gallery 与比较卡改为单列；主产品视觉保持在文本之后完整出现",
    "fit_profile" => {"objectives" => %w[single_product_purchase_confidence product_led_conversion new_product_desirability_in_context], "sku_range" => [1, 1], "promotion_levels" => %w[none low medium], "content_depth" => "medium", "asset_types" => %w[product lifestyle detail], "product_complexity" => %w[medium high]},
    "palette" => {"paper" => "#f6efe5", "ink" => "#382d26", "primary" => "#f04a22", "secondary" => "#e8b11a", "dark" => "#5c3523"},
    "rhythm" => [1.12, 0.76, 0.90, 0.88, 0.82, 0.50, 0.74, 0.54, 0.78]
  },
  {
    "template_id" => "HIST-TPL-004",
    "template_name" => "Immersive Single Product Launch",
    "reference_edm" => "SBG_019",
    "reference_campaign" => "ワイヤーネオンライト 新製品",
    "original_product" => "SwitchBot ワイヤーネオンライト",
    "campaign_types" => %w[single_product_launch product_launch single_product_conversion],
    "best_for" => "视觉效果本身是购买理由、需要完整完成态／使用态展示的单品",
    "not_for" => "缺少 Lifestyle 视觉、多产品促销、纯功能通知",
    "length_px" => 4797,
    "section_count" => 10,
    "module_count" => 11,
    "hero_structure" => "沉浸式 Lifestyle Hero + 清晰产品识别 + 克制双路径 CTA",
    "section_sequence" => ["immersive_hero", "primary_value", "compatibility_context", "feature_use_case", "product_detail", "proof_comparison", "commerce", "offer", "cta_closure", "deep_footer"],
    "module_sequence" => ["MOD-HERO-PRODUCT", "MOD-STORY-LIFESTYLE", "MOD-STORY-FEATURE-SPLIT", "MOD-STORY-PRODUCT-DETAIL", "MOD-STORY-PRIMARY-USP", "MOD-CONV-CTA-BAND", "MOD-SYSTEM-BRAND-FOOTER"],
    "cta_pattern" => "Hero 双去向仅在目的地不同；末段回到一个主购买行动",
    "footer_structure" => "Proof／渠道／品牌的深 Footer",
    "mobile_behavior" => "完成态 Hero 保持全宽；横向效果图改为纵向节拍",
    "fit_profile" => {"objectives" => %w[visual_product_desirability single_product_purchase_confidence new_product_value_understanding], "sku_range" => [1, 1], "promotion_levels" => %w[none low], "content_depth" => "medium", "asset_types" => %w[product lifestyle detail], "product_complexity" => %w[medium]},
    "palette" => {"paper" => "#f7f4f8", "ink" => "#21132a", "primary" => "#ee3e3e", "secondary" => "#7555ff", "dark" => "#160d1f"},
    "rhythm" => [1.16, 0.62, 0.66, 0.66, 0.76, 0.68, 0.52, 0.46, 0.50, 0.86]
  },
  {
    "template_id" => "HIST-TPL-005",
    "template_name" => "Scenario-led Theme Promotion",
    "reference_edm" => "SBG_006",
    "reference_campaign" => "Prime Day 防犯主题活动",
    "original_product" => "SwitchBot 防犯产品群",
    "campaign_types" => %w[theme_promotion category_promotion seasonal_campaign],
    "best_for" => "2–6 SKU 围绕一个生活问题的主题促销，每个场景绑定对应产品",
    "not_for" => "单一新品、无真实优惠信息、没有场景素材的任务",
    "length_px" => 8913,
    "section_count" => 10,
    "module_count" => 18,
    "hero_structure" => "深色主题 Hero；先定义问题，再展开多个场景与产品",
    "section_sequence" => ["theme_hero", "problem_frame", "scenario_product_a", "scenario_product_b", "scenario_product_c", "scenario_product_d", "user_proof", "offer_terms", "channel_cta", "deep_footer"],
    "module_sequence" => ["MOD-HERO-CAMPAIGN", "MOD-STORY-PROBLEM", "MOD-STORY-LIFESTYLE", "MOD-STORY-PRODUCT-GRID", "MOD-STORY-PRODUCT-DETAIL", "MOD-CONV-OFFER", "MOD-CONV-CTA-BAND", "MOD-SYSTEM-BRAND-FOOTER"],
    "cta_pattern" => "场景产品 CTA 重复 + 末段渠道收束；不得出现无归属 CTA",
    "footer_structure" => "优惠条件／渠道／法务／品牌的超深 Footer",
    "mobile_behavior" => "场景与产品固定成对单列；产品网格降为单列卡片",
    "fit_profile" => {"objectives" => %w[theme_relevance_then_offer_conversion category_problem_solution], "sku_range" => [2, 6], "promotion_levels" => %w[medium high], "content_depth" => "high", "asset_types" => %w[product lifestyle detail], "product_complexity" => %w[medium high]},
    "palette" => {"paper" => "#f5f2eb", "ink" => "#161925", "primary" => "#f1453d", "secondary" => "#f4c84e", "dark" => "#11192a"},
    "rhythm" => [1.12, 0.52, 0.86, 0.86, 0.86, 0.86, 0.58, 0.62, 0.50, 0.82]
  },
  {
    "template_id" => "HIST-TPL-006",
    "template_name" => "Deadline Commerce Grid",
    "reference_edm" => "SBG_005",
    "reference_campaign" => "Prime Day Last Chance",
    "original_product" => "SwitchBot 多产品",
    "campaign_types" => %w[countdown_last_chance high_promotion multi_product_promotion],
    "best_for" => "有真实截止时间、多个 SKU、价格／券结构完整的最终提醒",
    "not_for" => "Evergreen、无真实截止时间、品牌故事、产品教育",
    "length_px" => 7101,
    "section_count" => 9,
    "module_count" => 13,
    "hero_structure" => "截止时间优先 Hero + 产品群 + 单一活动利益",
    "section_sequence" => ["urgency_hero", "featured_products", "price_offer", "product_cta", "additional_products", "coupon", "deadline_reset", "final_cta", "deep_footer"],
    "module_sequence" => ["MOD-HERO-CAMPAIGN", "MOD-STORY-PRODUCT-GRID", "MOD-CONV-OFFER", "MOD-CONV-CTA-BAND", "MOD-SYSTEM-BRAND-FOOTER"],
    "cta_pattern" => "统一商品卡 CTA + 一次最终截止 CTA",
    "footer_structure" => "活动条款、渠道与品牌关闭",
    "mobile_behavior" => "商品双列改单列；价格、优惠、CTA 垂直保持相同顺序",
    "fit_profile" => {"objectives" => %w[deadline_driven_conversion multi_product_offer_discovery], "sku_range" => [2, 8], "promotion_levels" => %w[high], "content_depth" => "medium", "asset_types" => %w[product], "product_complexity" => %w[low medium]},
    "palette" => {"paper" => "#fff8ed", "ink" => "#171c38", "primary" => "#f04c2f", "secondary" => "#f5ad22", "dark" => "#151b3a"},
    "rhythm" => [1.04, 1.10, 0.70, 0.36, 1.18, 0.54, 0.46, 0.48, 0.80]
  },
  {
    "template_id" => "HIST-TPL-007",
    "template_name" => "User Voice Product Education Hybrid",
    "reference_edm" => "SBG_003",
    "reference_campaign" => "サーキュレーター活用術／User Voice",
    "original_product" => "SwitchBot サーキュレーター系列",
    "campaign_types" => %w[product_education user_voice_promotion seasonal_education],
    "best_for" => "有可追溯 User Voice、多个相关产品、需要使用方法与促销共同出现的内容",
    "not_for" => "无 User Voice 证据、单一新品首次发布、通用 Mobile 基线",
    "length_px" => 6599,
    "section_count" => 10,
    "module_count" => 10,
    "hero_structure" => "User Voice + 活动利益的条件性双层 Hero",
    "section_sequence" => ["voice_promotion_hero", "voice_context", "ranked_product_a", "ranked_product_b", "ranked_product_c", "coupon", "product_education", "cross_sell", "cta_closure", "deep_footer"],
    "module_sequence" => ["MOD-HERO-CAMPAIGN", "MOD-STORY-USER-VOICE", "MOD-STORY-PRODUCT-DETAIL", "MOD-CONV-OFFER", "MOD-STORY-PRIMARY-USP", "MOD-CONV-CTA-BAND", "MOD-SYSTEM-BRAND-FOOTER"],
    "cta_pattern" => "每个产品块绑定目的地清晰的 CTA；末段只做一次总收束",
    "footer_structure" => "Coupon 条件／渠道／品牌关闭",
    "mobile_behavior" => "历史源码固定 600px、无可靠 Reflow；只能作为桌面骨架，Mobile 需受 Design Standard QA",
    "fit_profile" => {"objectives" => %w[user_voice_understanding seasonal_usage_education product_comparison_with_proof], "sku_range" => [2, 4], "promotion_levels" => %w[low medium high], "content_depth" => "high", "asset_types" => %w[product lifestyle user_voice], "product_complexity" => %w[medium]},
    "palette" => {"paper" => "#fff7d6", "ink" => "#13384a", "primary" => "#18aed0", "secondary" => "#ff6a42", "dark" => "#16465d"},
    "rhythm" => [0.86, 0.42, 1.12, 1.12, 1.02, 0.54, 0.72, 0.64, 0.40, 0.76]
  },
  {
    "template_id" => "HIST-TPL-008",
    "template_name" => "Editorial Category Guide",
    "reference_edm" => "SBG_020",
    "reference_campaign" => "ロボット掃除機 Brand Story／選び方",
    "original_product" => "SwitchBot ロボット掃除機系列",
    "campaign_types" => %w[brand_story category_guide product_education multi_product_comparison],
    "best_for" => "高内容深度、需要建立品类理解或选择框架后再转化的任务",
    "not_for" => "短促销、价格通知、只有一个浅卖点的任务",
    "length_px" => 8397,
    "section_count" => 9,
    "module_count" => 22,
    "hero_structure" => "编辑型 Lifestyle Hero；商业行动延后",
    "section_sequence" => ["editorial_hero", "category_context", "comparison_framework", "product_chapter_a", "product_chapter_b", "product_chapter_c", "product_chapter_d", "selection_closure", "deep_footer"],
    "module_sequence" => ["MOD-HERO-EDITORIAL", "MOD-STORY-PROBLEM", "MOD-STORY-COMPARISON", "MOD-STORY-PRODUCT-DETAIL", "MOD-STORY-PRIMARY-USP", "MOD-CONV-CTA-BAND", "MOD-SYSTEM-BRAND-FOOTER"],
    "cta_pattern" => "读者理解品类／差异之后，再按产品目的地重复 CTA",
    "footer_structure" => "选择指导、Proof、渠道与品牌的超深 Footer",
    "mobile_behavior" => "比较框架转单列；章节标题、产品图、Proof、CTA 保持同一重复语法",
    "fit_profile" => {"objectives" => %w[choice_framework_and_product_fit brand_meaning_and_trust mechanism_or_setup_understanding category_understanding], "sku_range" => [1, 5], "promotion_levels" => %w[none low], "content_depth" => "high", "asset_types" => %w[product lifestyle detail app_ui], "product_complexity" => %w[high]},
    "palette" => {"paper" => "#f4f1ea", "ink" => "#2b2926", "primary" => "#e33b34", "secondary" => "#a9a095", "dark" => "#3a3631"},
    "rhythm" => [0.88, 0.76, 0.94, 0.82, 0.82, 0.82, 0.82, 0.58, 0.86]
  }
].freeze

def yaml_write(path, object)
  File.write(path, YAML.dump(object))
end

def snapshot_template(template)
  id = template.fetch("template_id")
  ref = template.fetch("reference_edm")
  dir = File.join(TEMPLATE_ROOT, id)
  FileUtils.mkdir_p(dir)

  recovered = File.join(ROOT, "output", "playwright", "phase5_5", "approved", "#{ref}_recovered.png")
  full = File.join(dir, "reference_full.png")
  FileUtils.cp(recovered, full)
  desktop = File.join(dir, "reference_desktop.png")
  system("sips", "-c", "1000", "600", "--cropOffset", "0", "0", full, "--out", desktop, out: File::NULL, err: File::NULL)
  FileUtils.cp(full, desktop) unless File.file?(desktop)

  source_html = File.join(ROOT, "research", "mobile_evidence", "html", "#{ref}.html")
  FileUtils.cp(source_html, File.join(dir, "reference_source.html"))
  source_assets = File.join(ROOT, "research", "mobile_evidence", "assets", ref)
  target_assets = File.join(TEMPLATE_ROOT, "assets", ref)
  FileUtils.mkdir_p(File.dirname(target_assets))
  FileUtils.rm_rf(target_assets)
  FileUtils.cp_r(source_assets, target_assets)

  regions = template.fetch("section_sequence").map.with_index do |region, index|
    policy = if index.zero? || index == 1 || index == template.fetch("section_sequence").length - 1
               "STRICT"
             elsif region.match?(/offer|coupon|related|proof|cross_sell|secondary/)
               "OPTIONAL"
             else
               "FLEXIBLE"
             end
    {"region_id" => region, "order" => index + 1, "policy" => policy, "inheritance_share" => policy == "STRICT" ? 1.0 : (policy == "FLEXIBLE" ? 0.7 : 0.0)}
  end

  structure = template.reject { |key, _| %w[palette rhythm fit_profile].include?(key) }.merge(
    "schema_version" => "1.0.0",
    "historical_template_first" => true,
    "reference_visual" => "reference_full.png",
    "reference_source" => "reference_source.html",
    "structure_policy" => {"strict" => "Must retain order, function and dominant geometry", "flexible" => "May resize or reduce within the 20% adaptation budget", "optional" => "May omit when truth/assets are unavailable; no substitute filler"},
    "regions" => regions
  )
  yaml_write(File.join(dir, "structure.yaml"), structure)
  yaml_write(File.join(dir, "style_tokens.yaml"), {
    "schema_version" => "1.0.0",
    "template_id" => id,
    "source" => ref,
    "measurement_type" => "browser_measured_length_plus_visual_extraction",
    "canvas" => {"desktop_width_px" => 600, "reference_length_px" => template.fetch("length_px"), "mobile_baseline_px" => 390},
    "palette" => template.fetch("palette"),
    "section_height_ratios" => template.fetch("rhythm"),
    "fixed_tokens" => %w[canvas_width section_sequence spacing_rhythm cta_geometry footer_depth],
    "flexible_tokens" => %w[product_specific_accent image_crop text_length section_height_within_15_percent],
    "forbidden" => ["generic card-grid replacement", "AI redrawn product body", "unbounded module insertion", "external reference palette override"]
  })
  yaml_write(File.join(dir, "editable_regions.yaml"), {
    "schema_version" => "1.0.0", "template_id" => id,
    "budget" => {"historical_skeleton_percent" => 70, "controlled_adaptation_percent" => 20, "new_design_fallback_percent" => 10},
    "regions" => regions,
    "fixed_regions" => regions.select { |row| row["policy"] == "STRICT" }.map { |row| row["region_id"] },
    "optional_regions" => regions.select { |row| row["policy"] == "OPTIONAL" }.map { |row| row["region_id"] }
  })
  yaml_write(File.join(dir, "asset_slots.yaml"), {
    "schema_version" => "1.0.0", "template_id" => id,
    "rules" => {"official_product_asset_required" => true, "ai_product_redraw_allowed" => false, "missing_required_asset" => "BLOCK_RENDER"},
    "slots" => [
      {"slot_id" => "hero_product", "policy" => "STRICT", "accepted" => %w[official_png official_product_scene], "crop" => "preserve_product_body"},
      {"slot_id" => "lifestyle", "policy" => "FLEXIBLE", "accepted" => %w[official_product_scene approved_campaign_asset], "fallback" => "omit_region"},
      {"slot_id" => "detail", "policy" => "FLEXIBLE", "accepted" => %w[official_detail official_app_ui], "fallback" => "text_only_if_claim_verified"},
      {"slot_id" => "footer_asset", "policy" => "STRICT", "accepted" => %w[approved_brand_asset text_wordmark], "fallback" => "approved_text_wordmark"}
    ]
  })
  yaml_write(File.join(dir, "copy_slots.yaml"), {
    "schema_version" => "1.0.0", "template_id" => id,
    "rules" => {"primary_objective_count" => 1, "placeholder_in_final" => "BLOCK", "unverified_claim" => "BLOCK", "copy_may_not_force_new_section" => true},
    "slots" => [
      {"slot_id" => "hero_headline", "policy" => "STRICT", "max_lines_desktop" => 3, "source_required" => true},
      {"slot_id" => "hero_body", "policy" => "FLEXIBLE", "max_chars_ja" => 90},
      {"slot_id" => "primary_feature", "policy" => "STRICT", "max_items" => 1},
      {"slot_id" => "secondary_features", "policy" => "FLEXIBLE", "max_items" => 4},
      {"slot_id" => "promotion", "policy" => "OPTIONAL", "verification_required" => true},
      {"slot_id" => "cta", "policy" => "STRICT", "url_required" => true},
      {"slot_id" => "period", "policy" => "OPTIONAL", "verification_required" => true}
    ]
  })
  html = <<~HTML
    <!doctype html>
    <html lang="ja">
    <head>
      <meta charset="utf-8">
      <meta name="viewport" content="width=device-width, initial-scale=1">
      <title>#{id} · #{template.fetch("template_name")}</title>
      <style>
        :root{--paper:#{template.dig("palette", "paper")};--ink:#{template.dig("palette", "ink")};--accent:#{template.dig("palette", "primary")}}
        *{box-sizing:border-box}html,body{margin:0;overflow-x:clip;background:#ebe8e1;color:var(--ink);font-family:"Avenir Next","Noto Sans JP",sans-serif}
        main{width:min(100%,1040px);margin:auto;padding:32px;display:grid;grid-template-columns:minmax(0,600px) minmax(220px,1fr);gap:28px;align-items:start}
        figure{margin:0;background:var(--paper);box-shadow:0 12px 40px rgba(0,0,0,.12)}img{display:block;width:100%;height:auto}
        aside{position:sticky;top:24px}h1{margin:0 0 8px;font-size:28px;line-height:1.05}p{line-height:1.6}ol{padding-left:20px}li+li{margin-top:8px}.tag{display:inline-block;padding:4px 8px;border:1px solid var(--accent);color:var(--accent);font-size:12px;font-weight:700}
        a{color:inherit}a:focus-visible{outline:3px solid var(--accent);outline-offset:3px}
        @media(max-width:760px){main{grid-template-columns:1fr;padding:16px}aside{position:static;order:-1}}
      </style>
    </head>
    <body>
      <main>
        <figure><img src="reference_full.png" width="600" height="#{template.fetch("length_px")}" alt="#{ref} 历史 EDM 完整视觉"></figure>
        <aside>
          <span class="tag">#{id} · #{ref}</span>
          <h1>#{template.fetch("template_name")}</h1>
          <p>#{template.fetch("best_for")}</p>
          <p><strong>不适用：</strong>#{template.fetch("not_for")}</p>
          <h2>结构骨架</h2>
          <ol>#{template.fetch("section_sequence").map { |s| "<li>#{s}</li>" }.join}</ol>
          <p><a href="reference_source.html">查看未修改的历史 HTML</a></p>
        </aside>
      </main>
    </body>
    </html>
  HTML
  File.write(File.join(dir, "template_preview.html"), html)
end

FileUtils.mkdir_p(TEMPLATE_ROOT)
TEMPLATES.each { |template| snapshot_template(template) }
yaml_write(File.join(TEMPLATE_ROOT, "library_v1.0.yaml"), {
  "schema_version" => "1.0.0",
  "name" => "SwitchBot Historical EDM Template Library v1.0",
  "status" => "Frozen for historical-first pilot",
  "generated_on" => "2026-08-20",
  "source_policy" => ["Tier A Approved SwitchBot historical EDM", "complete full visual", "recovered source HTML", "Anchor analysis"],
  "priority" => ["Approved SwitchBot historical", "sent SwitchBot historical", "Usable SwitchBot historical", "Generic fallback", "external reference excluded"],
  "routing" => {"historical_skeleton_percent" => 70, "controlled_adaptation_percent" => 20, "new_design_fallback_percent" => 10},
  "templates" => TEMPLATES.map { |t| t.reject { |key, _| %w[palette rhythm].include?(key) } }
})

manifest = CSV.read(File.join(ROOT, "research", "phase2_input_manifest.csv"), headers: true)
inventory = CSV.read(File.join(ROOT, "research", "switchbot_inventory.csv"), headers: true)
inventory_by_visual = inventory.select { |row| row["visual_sample_id"].to_s.start_with?("SBG_") }.group_by { |row| row["visual_sample_id"] }
formal = TEMPLATES.to_h { |t| [t.fetch("reference_edm"), t.fetch("template_id")] }
audit_rows = manifest.select { |row| %w[Tier\ A Tier\ B].include?(row["tier"]) }.map do |row|
  image = File.join(ROOT, row.fetch("screenshot_path"))
  dimensions = if File.file?(image)
                 out, = Open3.capture2("sips", "-g", "pixelWidth", "-g", "pixelHeight", image)
                 [out[/pixelWidth: (\d+)/, 1], out[/pixelHeight: (\d+)/, 1]].compact.join("x")
               else
                 "missing"
               end
  html = File.file?(File.join(ROOT, "research", "mobile_evidence", "html", "#{row.fetch("sample_id")}.html"))
  inventory_rows = inventory_by_visual.fetch(row.fetch("sample_id"), [])
  test_only = inventory_rows.any? && inventory_rows.all? { |item| item["campaign"].to_s.start_with?("[Test]") || item["notes"].to_s.include?("Test") }
  delivery_evidence = if test_only
                        "test_only"
                      elsif inventory_rows.any? { |item| item["source_type"] == "gmail_official_sender" && !item["campaign"].to_s.start_with?("[Test]") }
                        "official_sender_sent_or_production"
                      else
                        "high_confidence_gmail_visual"
                      end
  usable = dimensions != "missing" && !test_only
  status = if formal.key?(row.fetch("sample_id"))
             "formal_template"
           elsif test_only
             "excluded_test_only"
           else
             "candidate_not_promoted"
           end
  reason = if status == "formal_template"
             "complete_visual + recovered_html + Approved Anchor"
           elsif status == "excluded_test_only"
             "complete screenshot but Test-only evidence is not promoted"
           elsif row["tier"] == "Tier B"
             "Usable only; retained as supporting candidate"
           else
             "complete screenshot but no recovered HTML and/or overlaps a stronger Anchor"
           end
  [row["sample_id"], row["tier"], row["human_classification"], row["campaign_type"], dimensions, html, delivery_evidence, usable, formal[row["sample_id"]], status, reason, row["screenshot_path"]]
end
CSV.open(File.join(ROOT, "research", "historical_template_audit.csv"), "w") do |csv|
  csv << %w[sample_id tier human_classification campaign_type screenshot_dimensions recovered_html delivery_evidence usable_complete_historical formal_template_id audit_status audit_reason source_path]
  audit_rows.each { |row| csv << row }
end

puts "Built #{TEMPLATES.length} historical templates and audited #{audit_rows.length} Tier A/B samples."
