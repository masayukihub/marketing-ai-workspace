#!/usr/bin/env ruby
require "fileutils"
require "yaml"
require_relative "../core/truth_gate"
require_relative "../core/dependency_context"
require_relative "../typography/japanese"
require_relative "../components/email_components"
require_relative "../layouts/email_document"

ROOT = File.expand_path("../..", __dir__)
CSS = File.read(File.join(ROOT, "renderer", "css", "email.css"))

include PilotRenderer

def write(path, content)
  FileUtils.mkdir_p(File.dirname(path))
  File.write(path, content)
end

def copy_manifest(pilot_id)
  FileUtils.cp(
    File.join(ROOT, "pilot", pilot_id, "truth_pack", "asset_manifest.yaml"),
    File.join(ROOT, "pilot", pilot_id, "asset_manifest.yaml")
  )
end

def design_review(pilot_id:, title:, gate:, template:, template_family:, template_variant:, modules:, risks:, render_file:, objective:, audience:, primary_message:, template_reason:, module_reviews: [])
  module_rows = modules.map { |m| "<li><code>#{m}</code></li>" }.join
  risk_rows = risks.map { |r| "<li>#{r}</li>" }.join
  review_rows = if module_reviews.empty?
    <<~HTML
      <tr><td><code>Not rendered</code></td><td>真值或素材 Gate 未通过，不进入 Final 模块渲染。</td><td>UNVERIFIED / MISSING</td><td>见 Truth Pack 与 Asset Gap Plan</td><td>仅保留证据或线框</td><td>Truth Gate / QA BLOCKED</td></tr>
    HTML
  else
    module_reviews.map do |item|
      <<~HTML
        <tr><td><code>#{item[:id]}</code></td><td>#{item[:purpose]}</td><td lang="ja">#{item[:copy]}</td><td>#{item[:asset]}</td><td>#{item[:layout]}</td><td>#{item[:rules]}</td></tr>
      HTML
    end.join
  end
  <<~HTML
    <!doctype html><html lang="ja"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><link rel="icon" href="data:,">
    <title>#{pilot_id} Design Review</title><style>
    *{box-sizing:border-box}html,body{margin:0;overflow-x:clip}body{font-family:"Hiragino Kaku Gothic ProN","Yu Gothic",sans-serif;background:#eef0f3;color:#222326}.review{max-width:1200px;margin:auto;padding:28px}.head{display:grid;grid-template-columns:1fr auto;gap:20px;border-bottom:1px solid #cfd3d9;padding-bottom:20px}.gate{align-self:start;padding:8px 12px;background:#{gate == "BLOCKED" ? "#f4dfdf" : "#fff1d4"};font-weight:700}.campaign{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:16px;margin:22px 0}.meta{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:16px;margin:22px 0}.panel{background:#f9fafb;border:1px solid #d5d8dd;padding:18px}.panel h2{font-size:15px;margin:0 0 10px}.panel p{line-height:1.65;margin:0}.panel ul{margin:0;padding-left:20px}.trace{margin:22px 0;background:#f9fafb;border:1px solid #d5d8dd;padding:18px;overflow:auto}.trace h2{font-size:17px;margin:0 0 14px}.trace table{width:100%;min-width:980px;border-collapse:collapse;font-size:13px}.trace th,.trace td{padding:12px;border-bottom:1px solid #d5d8dd;text-align:left;vertical-align:top;line-height:1.55}.trace th{background:#e9edf2}.frame{background:#dfe2e6;padding:20px;overflow:auto}.frame iframe{display:block;width:600px;min-height:900px;margin:auto;border:0;background:#fff}@media(max-width:44rem){.review{padding:16px}.head,.campaign,.meta{grid-template-columns:1fr}.frame{padding:10px}.frame iframe{width:390px;max-width:100%}}</style></head>
    <body><main class="review"><header class="head"><div><p>#{pilot_id} · DESIGN REVIEW</p><h1>#{title}</h1></div><span class="gate">#{gate}</span></header>
    <section class="campaign"><article class="panel"><h2>Campaign Objective</h2><p>#{objective}</p></article><article class="panel"><h2>Audience</h2><p>#{audience}</p></article><article class="panel"><h2>Primary Message</h2><p lang="ja">#{primary_message}</p></article><article class="panel"><h2>Template Selection</h2><p>Family: #{template_family}<br>Variant: <code>#{template}</code> — #{template_variant}<br>#{template_reason}</p></article></section>
    <section class="meta"><article class="panel"><h2>Template</h2><code>#{template}</code></article><article class="panel"><h2>Modules</h2><ul>#{module_rows}</ul></article><article class="panel"><h2>风险 / 缺口</h2><ul>#{risk_rows}</ul></article></section>
    <section class="trace"><h2>Module Trace</h2><table><thead><tr><th>Module</th><th>Purpose</th><th>最终日语文案</th><th>Asset Source</th><th>Layout</th><th>Applicable Rules</th></tr></thead><tbody>#{review_rows}</tbody></table></section>
    <section class="frame"><iframe src="#{render_file}" title="#{pilot_id} visual"></iframe></section></main></body></html>
  HTML
end

def build_conditional(spec)
  dependencies = DependencyContext.new(root: ROOT, pilot_id: spec.fetch(:id))
  dependencies.assert_matches!(template: spec.fetch(:template), module_ids: spec.fetch(:modules))
  template_record = dependencies.template_record(spec.fetch(:template))
  gate = TruthGate.new(root: ROOT, pilot_id: spec.fetch(:id))
  gate.assert_renderable!
  c = EmailComponents
  body = +""
  body << c.internal_notice("社内検証用 · Product Knowledge / Footer 承認前 · 配信不可")
  body << c.brand_header(spec.fetch(:context))
  body << c.hero(**spec.fetch(:hero))
  spec.fetch(:sections).each do |section|
    method = section.fetch(:component)
    args = section.reject { |k, _| k == :component }
    body << c.public_send(method, **args)
  end
  body << c.fact_strip(spec.fetch(:facts)) if spec[:facts]
  body << c.cta_band(**spec.fetch(:cta))
  body << c.brand_footer

  html = EmailDocument.render(
    title: spec.fetch(:title), css: CSS, body: body, case_id: spec.fetch(:id), gate: gate.status
  )
  pilot_dir = File.join(ROOT, "pilot", spec.fetch(:id))
  write(File.join(pilot_dir, "editable_edm.html"), html)
  copy_manifest(spec.fetch(:id))

  copy_lines = spec.fetch(:copy).map do |item|
    "- **#{item[:role]}**: #{item[:text]}\n  - Source: #{item[:source]}\n  - Status: #{item[:status]}"
  end.join("\n")
  write(File.join(pilot_dir, "final_copy.md"), <<~MD)
    # #{spec.fetch(:id)} Conditional Pilot Copy

    > Internal renderer validation only. This file is not approved for campaign delivery.

    #{copy_lines}
  MD

  write(File.join(pilot_dir, "design_spec.md"), <<~MD)
    # #{spec.fetch(:id)} Design Spec

    - Gate: CONDITIONAL
    - Canvas: 600px desktop baseline; fluid at 320/375/390/414px
    - Template: #{spec.fetch(:template)}
    - Modules: #{spec.fetch(:modules).join(" → ")}
    - Primary objective: #{spec.fetch(:objective)}
    - CTA destinations: 1
    - Product pixels: official public assets only; no AI redraw, reconstruction, crop replacement or generated UI
    - Mobile: semantic single-column; product visual follows identity copy; CTA becomes full width
    - Production limitation: internal pilot watermark and non-production footer remain until Product Knowledge and legal/footer approval
  MD

  write(File.join(pilot_dir, "design_review.html"), design_review(
    pilot_id: spec.fetch(:id), title: spec.fetch(:title), gate: "CONDITIONAL", template: spec.fetch(:template),
    template_family: dependencies.template_family_name(spec.fetch(:template)), template_variant: template_record.fetch("template_name"),
    modules: spec.fetch(:modules), risks: spec.fetch(:risks), render_file: "editable_edm.html",
    objective: spec.fetch(:objective), audience: spec.fetch(:audience), primary_message: spec.fetch(:primary_message),
    template_reason: spec.fetch(:template_reason), module_reviews: spec.fetch(:module_reviews)
  ))
end

def blocked_wireframe(pilot_id:, title:, reason:, reference_image: nil, objective:, primary_message:, template_reason:)
  template = pilot_id == "P01" ? "TPL-LAUNCH-A" : "TPL-PROMO-B"
  dependencies = DependencyContext.new(root: ROOT, pilot_id: pilot_id)
  dependencies.assert_matches!(template: template)
  template_record = dependencies.template_record(template)
  image = if reference_image
    %(<figure class="evidence"><img src="#{reference_image}" width="1779" height="9267" alt="Historical full EDM evidence"></figure>)
  else
    <<~HTML
      <div class="skeleton" aria-label="Blocked wireframe only">
        <div class="bar"></div><div class="copy"></div><div class="product">OFFICIAL PRODUCT ASSET<br>MISSING</div>
        <div class="row"></div><div class="row short"></div><div class="button">CTA DESTINATION MISSING</div>
      </div>
    HTML
  end
  html = <<~HTML
    <!doctype html><html lang="ja"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><link rel="icon" href="data:,"><title>#{pilot_id} Blocked</title><style>
    *{box-sizing:border-box}html,body{margin:0;overflow-x:clip}body{background:#eceff2;color:#24262a;font-family:"Hiragino Kaku Gothic ProN","Yu Gothic",sans-serif}.canvas{width:100%;max-width:600px;margin:auto;background:#fafafa;min-height:900px}.blocked{padding:16px 24px;background:#8d1b1b;color:#fff;font-weight:800}.intro{padding:42px 32px;border-bottom:1px solid #d4d7db}.intro h1{font-size:30px;line-height:1.25;margin:0 0 14px}.intro p{line-height:1.7;margin:0;color:#62666d}.skeleton{padding:38px 32px;display:grid;gap:22px}.bar,.copy,.row,.button,.product{border:2px dashed #a8adb5;background:#e9ebee}.bar{height:20px;width:38%}.copy{height:70px;width:78%}.product{height:340px;display:grid;place-items:center;text-align:center;color:#6d727a;font-weight:700}.row{height:100px}.row.short{width:64%}.button{height:54px;display:grid;place-items:center;color:#6d727a;font-size:12px}.evidence{margin:0;padding:24px;background:#dfe2e6}.evidence img{display:block;width:100%;height:auto;filter:saturate(.75)}@media(max-width:30rem){.intro,.skeleton{padding:30px 20px}.intro h1{font-size:26px}.evidence{padding:12px}}</style></head>
    <body><main class="canvas"><div class="blocked">BLOCKED · EVIDENCE / WIREFRAME ONLY · NOT A FINAL EDM</div><section class="intro"><h1>#{title}</h1><p>#{reason}</p></section>#{image}</main></body></html>
  HTML
  dir = File.join(ROOT, "pilot", pilot_id)
  write(File.join(dir, "wireframe.html"), html)
  copy_manifest(pilot_id)
  write(File.join(dir, "readiness.md"), "# #{pilot_id} Readiness\n\n- Gate: **BLOCKED**\n- Reason: #{reason}\n- Output allowed: evidence-labelled wireframe only\n")
  write(File.join(dir, "asset_gap_plan.md"), "# #{pilot_id} Asset / Truth Gap Plan\n\n1. Resolve every renderer-blocking `MISSING` or `UNVERIFIED` item in `truth_pack/`.\n2. Re-run Product Knowledge and campaign verification.\n3. Supply a real clickable CTA destination and current production footer.\n4. Re-run the Truth Gate before creating any Final HTML.\n")
  write(File.join(dir, "design_review.html"), design_review(
    pilot_id: pilot_id, title: title, gate: "BLOCKED", template: template,
    template_family: dependencies.template_family_name(template), template_variant: template_record.fetch("template_name"),
    modules: ["Wireframe / evidence only"], risks: [reason], render_file: "wireframe.html",
    objective: objective, audience: "UNVERIFIED — 正式 Campaign Audience 未提供", primary_message: primary_message,
    template_reason: template_reason
  ))
end

specs = [
  {
    id: "P02",
    title: "SwitchBot ロックUltra · Single Product Conversion Pilot",
    context: "SwitchBot ロックUltra",
    template: "TPL-CONVERT-A",
    objective: "single_product_purchase_confidence",
    audience: "UNVERIFIED — 正式 Campaign Audience 未提供",
    primary_message: "ドアに溶け込む、一体型デザイン。",
    template_reason: "单品转化任务，需要先建立产品身份与购买信心，再以兼容性确认和单一 CTA 收束；与冻结的 TPL-CONVERT-A 职责一致。",
    modules: %w[MOD-HERO-PRODUCT MOD-STORY-PRIMARY-USP MOD-STORY-PRODUCT-DETAIL MOD-CONV-CTA-BAND MOD-SYSTEM-BRAND-FOOTER],
    module_reviews: [
      {id: "MOD-HERO-PRODUCT", purpose: "建立产品身份与核心视觉价值。", copy: "ドアに溶け込む、一体型デザイン。", asset: "renderer/assets/official/P02/lock_ultra_main.jpg", layout: "桌面非对称双栏；移动端单栏回流。", rules: "R-PRODUCT-001 / R-ASSET-001 / R-BRAND-001"},
      {id: "MOD-STORY-PRIMARY-USP", purpose: "展开一体型外观与玄关适配感。", copy: "玄関に、すっきりと。", asset: "renderer/assets/official/P02/lock_ultra_lifestyle.jpg", layout: "全宽视觉叙事模块。", rules: "R-CLAIM-001 / R-MODULE-003"},
      {id: "MOD-STORY-PRODUCT-DETAIL", purpose: "在购买前提示安装与兼容性确认。", copy: "ご購入前に、取り付け可否を確認。", asset: "renderer/assets/official/P02/lock_ultra_detail.jpg", layout: "40/60 图文分栏；移动端单栏。", rules: "R-ASSET-001 / R-CLAIM-001 / R-CLAIM-002"},
      {id: "MOD-CONV-CTA-BAND", purpose: "以单一明确动作收束转化路径。", copy: "製品を詳しく見る", asset: "Verified official product-page destination", layout: "深色 CTA Band；移动端按钮全宽。", rules: "R-CTA-001 / R-CTA-004"},
      {id: "MOD-SYSTEM-BRAND-FOOTER", purpose: "明确内部 Pilot 与不可配信边界。", copy: "社内検証用 · 配信不可", asset: "MISSING — production legal/footer asset", layout: "中性关闭模块。", rules: "R-MODULE-001 / R-QA-001"}
    ],
    hero: {
      product: "SwitchBot ロックUltra", headline: "ドアに溶け込む、\n一体型デザイン。",
      subheadline: "一体型カバーデザインで、後付けの存在感を抑えた外観へ。",
      image: "../../renderer/assets/official/P02/lock_ultra_main.jpg", alt: "SwitchBot ロックUltra ブラック", tone: "warm"
    },
    sections: [
      {component: :full_visual, title: "玄関に、すっきりと。", body: "ブラックとシルバー。ドアまわりに合わせて選べる外観。", image: "../../renderer/assets/official/P02/lock_ultra_lifestyle.jpg", alt: "SwitchBot ロックUltra ブラックとシルバー", module_id: "MOD-STORY-PRIMARY-USP", note: "公式公開素材／社内 Renderer Pilot のみ"},
      {component: :image_story, title: "ご購入前に、取り付け可否を確認。", body: "ドアやサムターンの形状によって、確認や調整部品が必要な場合があります。", image: "../../renderer/assets/official/P02/lock_ultra_detail.jpg", alt: "取り付け可否確認用の公式対応例", module_id: "MOD-STORY-PRODUCT-DETAIL", reverse: true, note: "具体的な対応可否は公式ページで確認"}
    ],
    facts: [
      {label: "デザイン", value: "一体型カバー"},
      {label: "カラー", value: "ブラック / シルバー"},
      {label: "ご購入前", value: "取り付け可否を確認"}
    ],
    cta: {title: "取り付け条件と製品情報を確認", label: "製品を詳しく見る", url: "https://www.switchbot.jp/products/switchbot-lock-ultra"},
    risks: ["Product Knowledge external approval pending", "Review proof omitted", "Production footer missing"],
    copy: [
      {role: "Product name", text: "SwitchBot ロックUltra", source: "Official JP product page", status: "VERIFIED"},
      {role: "Headline", text: "ドアに溶け込む、一体型デザイン。", source: "Official JP product page", status: "VERIFIED / internal pilot only"},
      {role: "Hero support", text: "一体型カバーデザインで、後付けの存在感を抑えた外観へ。", source: "Localized from official JP product page", status: "UNVERIFIED / internal pilot only"},
      {role: "USP heading", text: "玄関に、すっきりと。", source: "Renderer localization based on official design imagery", status: "UNVERIFIED / internal pilot only"},
      {role: "USP support", text: "ブラックとシルバー。ドアまわりに合わせて選べる外観。", source: "Official variant data and imagery", status: "VERIFIED / internal pilot only"},
      {role: "Compatibility heading", text: "ご購入前に、取り付け可否を確認。", source: "Official pre-purchase check content", status: "VERIFIED / internal pilot only"},
      {role: "Compatibility support", text: "ドアやサムターンの形状によって、確認や調整部品が必要な場合があります。", source: "Official compatibility asset/page", status: "VERIFIED / internal pilot only"},
      {role: "CTA", text: "製品を詳しく見る", source: "Verified official destination", status: "VERIFIED / internal pilot only"}
    ]
  },
  {
    id: "P04",
    title: "SwitchBot スマートデイリーステーション · Product Education Pilot",
    context: "スマートデイリーステーション",
    template: "TPL-EDU-B",
    objective: "mechanism_or_setup_understanding",
    audience: "UNVERIFIED — 正式 Campaign Audience 未提供",
    primary_message: "暮らしのすべてを、この1画面に。",
    template_reason: "教育任务的重点是让用户先理解产品能汇总哪些日常信息，再通过官方界面与细节图逐层解释；与冻结的 TPL-EDU-B 顺序一致。",
    modules: %w[MOD-HERO-PRODUCT MOD-STORY-APP-UI MOD-STORY-FEATURE-SPLIT MOD-STORY-PRODUCT-DETAIL MOD-CONV-CTA-BAND MOD-SYSTEM-BRAND-FOOTER],
    module_reviews: [
      {id: "MOD-HERO-PRODUCT", purpose: "建立产品类别认知与主要教育命题。", copy: "暮らしのすべてを、この1画面に。", asset: "renderer/assets/official/P04/daily_station_main.jpg", layout: "桌面非对称双栏；移动端单栏回流。", rules: "R-PRODUCT-001 / R-ASSET-001 / R-BRAND-001"},
      {id: "MOD-STORY-APP-UI", purpose: "用官方设备界面说明信息汇总方式。", copy: "必要な情報を、画面ひとつで確認。", asset: "renderer/assets/official/P04/daily_station_ui.jpg", layout: "全宽界面视觉；不重绘 UI。", rules: "R-AI-001 / R-ASSET-001 / R-CLAIM-002"},
      {id: "MOD-STORY-FEATURE-SPLIT / MOD-STORY-PRODUCT-DETAIL", purpose: "解释天气与室内环境信息的查看场景。", copy: "空気も天気も、一画面で。", asset: "renderer/assets/official/P04/daily_station_detail.jpg", layout: "60/40 图文分栏；移动端单栏。", rules: "R-ASSET-001 / R-CLAIM-001 / R-MODULE-003"},
      {id: "MOD-CONV-CTA-BAND", purpose: "引导到官方页继续核对功能与适用条件。", copy: "製品を詳しく見る", asset: "Verified official product-page destination", layout: "深色 CTA Band；移动端按钮全宽。", rules: "R-CTA-001 / R-CTA-004"},
      {id: "MOD-SYSTEM-BRAND-FOOTER", purpose: "明确内部 Pilot 与不可配信边界。", copy: "社内検証用 · 配信不可", asset: "MISSING — production legal/footer asset", layout: "中性关闭模块。", rules: "R-MODULE-001 / R-QA-001"}
    ],
    hero: {
      product: "SwitchBot\nスマートデイリーステーション", headline: "暮らしのすべてを、\nこの1画面に。",
      subheadline: "天気も室内環境も、家族のスケジュールも、これ一台に。",
      image: "../../renderer/assets/official/P04/daily_station_main.jpg", alt: "SwitchBot スマートデイリーステーション", tone: "cool"
    },
    sections: [
      {component: :full_visual, title: "必要な情報を、画面ひとつで確認。", body: "天気も室内環境も、家族のスケジュールも、ひと目で確認。", image: "../../renderer/assets/official/P04/daily_station_ui.jpg", alt: "スマートデイリーステーションの公式情報画面例", module_id: "MOD-STORY-APP-UI", note: "公式 Device UI。App UI ではなく、再構成・改変なし。"},
      {component: :image_story, title: "空気も天気も、一画面で。", body: "室内外の温湿度や天気を、公式画面例で確認できます。", image: "../../renderer/assets/official/P04/daily_station_detail.jpg", alt: "天気と室内環境の公式画面例", module_id: "MOD-STORY-PRODUCT-DETAIL", reverse: false, note: "画像内の数値は公式表示例であり、編集可能な性能 Claim ではありません。"}
    ],
    facts: [
      {label: "確認できる情報", value: "天気 / 室内環境 / 予定"},
      {label: "表示", value: "公式デバイス UI"},
      {label: "ご購入前", value: "機能・対応条件を確認"}
    ],
    cta: {title: "表示内容と製品情報を確認", label: "製品を詳しく見る", url: "https://www.switchbot.jp/products/switchbot-weather-station"},
    risks: ["Product Knowledge external approval pending", "No App UI is used", "Production footer missing"],
    copy: [
      {role: "Product name", text: "SwitchBot スマートデイリーステーション", source: "Official JP product page", status: "VERIFIED"},
      {role: "Headline", text: "暮らしのすべてを、この1画面に。", source: "Official JP product page", status: "VERIFIED / internal pilot only"},
      {role: "Hero support", text: "天気も室内環境も、家族のスケジュールも、これ一台に。", source: "Official JP product image", status: "VERIFIED / internal pilot only"},
      {role: "Education heading", text: "必要な情報を、画面ひとつで確認。", source: "Renderer localization from official JP product page", status: "UNVERIFIED / internal pilot only"},
      {role: "Education support", text: "天気も室内環境も、家族のスケジュールも、ひと目で確認。", source: "Official JP product page and image", status: "UNVERIFIED localization / internal pilot only"},
      {role: "Detail heading", text: "空気も天気も、一画面で。", source: "Official JP product image", status: "VERIFIED / internal pilot only"},
      {role: "Detail support", text: "室内外の温湿度や天気を、公式画面例で確認できます。", source: "Official JP product page", status: "VERIFIED / internal pilot only"},
      {role: "CTA", text: "製品を詳しく見る", source: "Verified official destination", status: "VERIFIED / internal pilot only"}
    ]
  }
]

specs.each { |spec| build_conditional(spec) }
blocked_wireframe(
  pilot_id: "P01", title: "S30 mini Product Launch Pilot",
  reason: "正式な製品アイデンティティ、公式製品主素材、公開可能な Claim、期間、CTA が未確定です。S20 素材は使用できません。",
  objective: "Product Launch — 正式 Identity / Claim / Asset 确认后建立新品认知",
  primary_message: "UNVERIFIED — 正式 Launch Message 未确认",
  template_reason: "结构上对应 TPL-LAUNCH-A，但 Truth Gate 未通过，因此仅展示启动型结构线框，不进入模块与视觉生产。"
)
blocked_wireframe(
  pilot_id: "P03", title: "2026 Prime Day Security Promotion — Historical Evidence",
  reason: "活動は終了済みで、復元時に元の CTA リンクが削除されています。現在の価格・在庫・商品情報として再利用できません。",
  reference_image: "../../research/screenshots/SBG_006_prime_day_security_gmail_full.jpg",
  objective: "Historical Multi-product Promotion Evidence — 当时促销结构复盘",
  primary_message: "最大35%OFF — 仅为已结束的 2026 Prime Day 历史邮件证据",
  template_reason: "历史结构与 TPL-PROMO-B 接近，但活动、价格与 CTA 已失效；只保留真实邮件证据，不重新渲染为当前促销。"
)

puts "Built P02/P04 conditional renders and P01/P03 blocked wireframes."
