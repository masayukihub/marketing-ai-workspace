#!/usr/bin/env ruby
require "fileutils"
require "yaml"
require_relative "../core/truth_gate"
require_relative "../core/brand_context"
require_relative "../components/switchbot_brand_components"
require_relative "../layouts/email_document"

ROOT = File.expand_path("../..", __dir__)
CSS = File.read(File.join(ROOT, "renderer", "css", "switchbot_brand_email.css"))

include PilotRenderer

def write(path, content)
  FileUtils.mkdir_p(File.dirname(path))
  File.write(path, content)
end

def build_brand_case(spec)
  gate = TruthGate.new(root: ROOT, pilot_id: spec.fetch(:id))
  gate.assert_renderable!
  brand_context = BrandContext.new(root: ROOT)
  mode = brand_context.assert_switchbot_brand!(brand: "SwitchBot", market: "Japan")
  c = SwitchBotBrandComponents

  body = +""
  body << c.internal_notice("社内 Brand Calibration 用 · Product Knowledge / Production Footer 承認前 · 配信不可")
  body << c.brand_header(context: spec.fetch(:context), chapter: spec.fetch(:variant))
  spec.fetch(:modules).each do |mod|
    method = mod.fetch(:component)
    args = mod.reject { |key, _| key == :component }
    body << c.public_send(method, **args)
  end

  html = EmailDocument.render(
    title: spec.fetch(:title), css: CSS, body: body, case_id: spec.fetch(:id), gate: gate.status
  ).sub("<body ", %(<body data-render-mode="#{mode}" ))

  out = File.join(ROOT, "pilot", spec.fetch(:id), "brand_v2")
  write(File.join(out, "editable_edm.html"), html)
  FileUtils.cp(File.join(ROOT, "pilot", spec.fetch(:id), "truth_pack", "asset_manifest.yaml"), File.join(out, "asset_manifest.yaml"))
  write(File.join(out, "renderer_mode.yaml"), {
    "brand" => "SwitchBot", "market" => "Japan", "render_mode" => mode,
    "brand_rules" => "brand_system/switchbot_composition_rules_v1.0.yaml",
    "brand_variant" => spec.fetch(:variant), "product_complexity" => "HIGH",
    "length_class" => "Standard", "core_module_count" => spec.fetch(:modules).length,
    "long_form_gate" => "CAPPED_BY_TRUTH_AND_ASSET_COVERAGE"
  }.to_yaml)

  copy_lines = spec.fetch(:copy).map do |item|
    "- **#{item.fetch(:role)}**: #{item.fetch(:text)}\n  - Source: #{item.fetch(:source)}\n  - Status: #{item.fetch(:status)}"
  end.join("\n")
  write(File.join(out, "final_copy.md"), <<~MD)
    # #{spec.fetch(:id)} Brand V2 Copy

    > Internal Brand Calibration only. This copy is not approved for campaign delivery.

    #{copy_lines}
  MD

  write(File.join(out, "design_spec.md"), <<~MD)
    # #{spec.fetch(:id)} Brand-calibrated V2 Design Spec

    - Gate: **CONDITIONAL**
    - Render mode: `#{mode}`
    - Product complexity: **HIGH**
    - Length class: **Standard**; Long-form is justified by complexity but capped by verified Truth / Asset coverage
    - Brand variant: `#{spec.fetch(:variant)}`
    - Core modules: #{spec.fetch(:modules).length} (header and internal notice excluded; footer included)
    - Module sequence: #{spec.fetch(:modules).map { |mod| mod.fetch(:module_id) }.join(" → ")}
    - Product rhythm: Hero identity → evidence/use case → detail/UI → pre-purchase question → action checkpoint → product reset → final action → deep footer
    - Product pixels: official public assets only; no AI redraw, reconstruction or generated UI
    - CTA: one verified official product-page destination, repeated only after different information stages
    - Missing proof/service: omitted and reported; not invented
    - Production limitation: Product Knowledge external approval and approved current footer/legal package are still missing
  MD

  write(File.join(out, "render_qa.md"), <<~MD)
    # #{spec.fetch(:id)} Brand V2 Render QA

    - Gate: CONDITIONAL / internal calibration only
    - Brand mode: #{mode}
    - Core modules declared: #{spec.fetch(:modules).length}
    - Browser dimensions: pending `renderer/qa/phase5_5_brand_browser_qa.js`
    - Truth / Claim: no new numerical, superiority, price, promotion, service or compatibility claims added
    - Asset: official product/device UI assets only; no AI product redraw
    - Footer: deep structural simulation only; production footer remains MISSING
    - Long-form decision: not forced; Standard used because verified content and asset depth stop before 12 justified modules
  MD
end

p02_url = "https://www.switchbot.jp/products/switchbot-lock-ultra"
p04_url = "https://www.switchbot.jp/products/switchbot-weather-station"

specs = [
  {
    id: "P02",
    title: "SwitchBot ロックUltra · Brand-calibrated V2",
    context: "SwitchBot ロックUltra",
    variant: "SB-LF-CONVERSION / TRUTH-CAPPED STANDARD",
    modules: [
      {component: :hero, module_id: "MOD-HERO-PRODUCT", product: "SwitchBot ロックUltra", headline: "ドアに溶け込む、\n一体型デザイン。", body: "一体型カバーデザインで、後付けの存在感を抑えた外観へ。", image: "../../../renderer/assets/official/P02/lock_ultra_main.jpg", alt: "SwitchBot ロックUltra ブラック", theme: "warm"},
      {component: :visual_feature, module_id: "MOD-STORY-LIFESTYLE", kicker: "DESIGN IN CONTEXT", title: "玄関に、\nすっきりと。", body: "ブラックとシルバー。ドアまわりに合わせて選べる外観。", image: "../../../renderer/assets/official/P02/lock_ultra_lifestyle.jpg", alt: "SwitchBot ロックUltra ブラックとシルバー", note: "公式公開素材。見出しは社内 Pilot 用ローカライズで未承認。", tone: "paper"},
      {component: :statement, module_id: "MOD-STORY-PRODUCT-DETAIL", kicker: "PRODUCT IDENTITY", title: "一体型カバー。\n2つのカラー。", body: "製品の外観とカラーを、購入前に確認できます。ブラック／シルバーは既存 Truth Pack の範囲です。", tone: "white"},
      {component: :statement, module_id: "MOD-STORY-PROBLEM", kicker: "BEFORE PURCHASE", title: "取り付け前に、\n確認しておきたいこと。", body: "ドアやサムターンの形状によって、確認や調整部品が必要な場合があります。", tone: "red"},
      {component: :visual_feature, module_id: "MOD-STORY-PRODUCT-DETAIL#2", kicker: "COMPATIBILITY", title: "ご購入前に、\n取り付け可否を確認。", body: "具体的な対応可否は、公式製品ページの最新情報でご確認ください。", image: "../../../renderer/assets/official/P02/lock_ultra_detail.jpg", alt: "取り付け可否確認用の公式対応例", note: "公式対応例。具体的な互換率・対応保証は記載していません。", tone: "paper"},
      {component: :checklist, module_id: "MOD-STORY-FAQ", kicker: "PURCHASE CHECK", title: "確認するのは、\nこの3点。", items: ["ドアとサムターンの形状", "必要に応じた調整部品", "公式ページの最新の取り付け条件"], note: "既存 required_disclaimers と互換性確認文だけを再構成。新しい適合 Claim はありません。"},
      {component: :cta_checkpoint, module_id: "MOD-CONV-SECONDARY", title: "取り付け条件を確認", body: "ここまでの確認を、公式ページで続ける。", label: "取り付け条件を確認", url: p02_url},
      {component: :product_reset, module_id: "MOD-STORY-PRIMARY-USP#2", product: "SwitchBot ロックUltra", title: "ドアに溶け込む、\n一体型デザイン。", image: "../../../renderer/assets/official/P02/lock_ultra_main.jpg", alt: "SwitchBot ロックUltra 製品本体", note: "最終アクション前の製品再提示。新しい Claim は追加していません。"},
      {component: :final_cta, module_id: "MOD-CONV-CTA-BAND", title: "製品情報を、\n公式ページで確認。", body: "現在の仕様・取り付け条件・購入情報をご確認ください。", label: "製品を詳しく見る", url: p02_url},
      {component: :brand_footer, module_id: "MOD-SYSTEM-BRAND-FOOTER", case_id: "P02"}
    ],
    copy: [
      {role: "Headline", text: "ドアに溶け込む、一体型デザイン。", source: "Official JP product page", status: "VERIFIED / internal pilot only"},
      {role: "Lifestyle heading", text: "玄関に、すっきりと。", source: "Renderer localization based on official design imagery", status: "UNVERIFIED / internal pilot only"},
      {role: "Compatibility", text: "ドアやサムターンの形状によって、確認や調整部品が必要な場合があります。", source: "Existing P02 Truth Pack", status: "VERIFIED / internal pilot only"},
      {role: "Mid CTA", text: "取り付け条件を確認", source: "Renderer localization + verified official destination", status: "UNVERIFIED copy / VERIFIED URL"},
      {role: "Final CTA", text: "製品を詳しく見る", source: "Existing Campaign Truth", status: "VERIFIED / internal pilot only"}
    ]
  },
  {
    id: "P04",
    title: "SwitchBot スマートデイリーステーション · Brand-calibrated V2",
    context: "SwitchBot スマートデイリーステーション",
    variant: "SB-LF-EDUCATION / TRUTH-CAPPED STANDARD",
    modules: [
      {component: :hero, module_id: "MOD-HERO-PRODUCT", product: "SwitchBot スマートデイリーステーション", headline: "暮らしのすべてを、\nこの1画面に。", body: "天気も室内環境も、家族のスケジュールも、これ一台に。", image: "../../../renderer/assets/official/P04/daily_station_main.jpg", alt: "SwitchBot スマートデイリーステーション", theme: "cool"},
      {component: :statement, module_id: "MOD-STORY-PRIMARY-USP", kicker: "ONE SCREEN", title: "必要な情報を、\n画面ひとつで確認。", body: "天気も室内環境も、家族のスケジュールも、ひと目で確認。", tone: "paper"},
      {component: :visual_feature, module_id: "MOD-STORY-APP-UI", kicker: "OFFICIAL DEVICE UI", title: "暮らしの情報を、\n手元の1画面へ。", body: "公式のデバイス画面で、表示内容と情報のまとまり方を確認できます。", image: "../../../renderer/assets/official/P04/daily_station_ui.jpg", alt: "スマートデイリーステーションの公式デバイス画面例", note: "公式 Device UI。App UI ではなく、再構成・改変なし。", tone: "cool"},
      {component: :split_feature, module_id: "MOD-STORY-FEATURE-SPLIT", kicker: "WEATHER / INDOOR", title: "空気も天気も、\n一画面で。", body: "室内外の温湿度や天気を、公式画面例で確認できます。", image: "../../../renderer/assets/official/P04/daily_station_detail.jpg", alt: "天気と室内環境の公式画面例", note: "画像内数値は公式表示例。編集可能な性能 Claim ではありません。", reverse: false, tone: "white"},
      {component: :statement, module_id: "MOD-STORY-IMAGE-TEXT", kicker: "FAMILY SCHEDULE", title: "家族の予定を、\n画面ひとつに。", body: "予定と日々の情報を同じデバイス画面で見る、という製品の使い方を確認します。対応サービスの詳細は未確認です。", tone: "paper"},
      {component: :checklist, module_id: "MOD-STORY-FAQ", kicker: "BEFORE USE", title: "利用条件は、\n購入前に確認。", items: ["表示したい情報と画面例", "必要なWi-Fi・サービス・対応アカウント", "センサーや連携機器の必要条件"], note: "既存 required_disclaimers を購入前確認として表示。個別対応可否は未確認です。"},
      {component: :cta_checkpoint, module_id: "MOD-CONV-SECONDARY", title: "表示内容を確認", body: "公式ページで現在の画面例と条件を確認する。", label: "表示内容を確認", url: p04_url},
      {component: :product_reset, module_id: "MOD-STORY-PRODUCT-DETAIL", product: "SwitchBot スマートデイリーステーション", title: "暮らしのすべてを、\nこの1画面に。", image: "../../../renderer/assets/official/P04/daily_station_main.jpg", alt: "SwitchBot スマートデイリーステーション 製品本体", note: "最終アクション前の製品再提示。数値・AI・性能 Claim は追加していません。"},
      {component: :final_cta, module_id: "MOD-CONV-CTA-BAND", title: "製品情報を、\n公式ページで確認。", body: "現在の表示内容・対応条件・購入情報をご確認ください。", label: "製品を詳しく見る", url: p04_url},
      {component: :brand_footer, module_id: "MOD-SYSTEM-BRAND-FOOTER", case_id: "P04"}
    ],
    copy: [
      {role: "Headline", text: "暮らしのすべてを、この1画面に。", source: "Official JP product page", status: "VERIFIED / internal pilot only"},
      {role: "Primary USP", text: "天気も室内環境も、家族のスケジュールも、これ一台に。", source: "Official JP product image", status: "VERIFIED / internal pilot only"},
      {role: "Schedule heading", text: "家族の予定を、画面ひとつに。", source: "Official JP product page", status: "VERIFIED wording / external Product Knowledge approval UNVERIFIED"},
      {role: "Dependency check", text: "必要なWi-Fi・サービス・対応アカウント、センサーや連携機器の条件を確認。", source: "Existing P04 required disclaimer", status: "UNVERIFIED localization / internal pilot only"},
      {role: "Mid CTA", text: "表示内容を確認", source: "Renderer localization + verified official destination", status: "UNVERIFIED copy / VERIFIED URL"},
      {role: "Final CTA", text: "製品を詳しく見る", source: "Existing Campaign Truth", status: "VERIFIED / internal pilot only"}
    ]
  }
]

specs.each { |spec| build_brand_case(spec) }
puts "Built P02/P04 SwitchBot Brand V2 renders."
