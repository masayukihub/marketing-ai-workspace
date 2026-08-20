# frozen_string_literal: true

require "cgi"
require "fileutils"
require "yaml"
require_relative "historical_template_matcher"

module EDMGenerator
  class HistoricalTemplateRenderer
    attr_reader :root, :matcher, :library

    def initialize(root)
      @root = File.expand_path(root)
      @matcher = HistoricalTemplateMatcher.new(@root)
      @library = matcher.library.fetch("templates").to_h { |template| [template.fetch("template_id"), template] }
    end

    def render_all(test_path = "tests/historical_template_test_cases.yaml")
      tests = YAML.safe_load(File.read(File.join(root, test_path)))
      results = tests.fetch("test_cases").map { |test| render(test) }
      summary = {
        "schema_version" => "1.0.0",
        "generated_on" => "2026-08-20",
        "case_count" => results.length,
        "top1_correct" => results.count { |row| row.fetch("top1_correct") },
        "top1_accuracy_percent" => (results.count { |row| row.fetch("top1_correct") }.fdiv(results.length) * 100).round(1),
        "accuracy_scope" => "offline expert-labelled fixture; not Human Review accuracy",
        "results" => results
      }
      File.write(File.join(root, "output", "historical_template_tests", "summary.yaml"), YAML.dump(summary))
      summary
    end

    def render(test)
      case_id = test.fetch("case_id")
      out = File.join(root, "output", "historical_template_tests", case_id)
      FileUtils.mkdir_p(out)
      match = matcher.rank(test.fetch("brief"))
      template_id = match.fetch("selected_template_id")
      raise "No historical template reached the minimum threshold for #{case_id}" unless template_id
      template = library.fetch(template_id)
      assets = copy_assets(test.fetch("assets"), out)
      content = test.fetch("content")
      html = render_html(case_id, template, content, assets, match)
      File.write(File.join(out, "editable_edm.html"), html)
      File.write(File.join(out, "brief.yaml"), YAML.dump(test.slice("case_id", "name", "brief", "content")))
      File.write(File.join(out, "matcher_result.yaml"), YAML.dump(match))
      File.write(File.join(out, "content_mapping.yaml"), YAML.dump(content_mapping(template, content)))
      File.write(File.join(out, "asset_mapping.yaml"), YAML.dump(asset_mapping(template, test.fetch("assets"), assets)))
      result = {
        "case_id" => case_id,
        "name" => test.fetch("name"),
        "expected_top1" => test.fetch("expected_top1"),
        "selected_template_id" => template_id,
        "selected_reference_edm" => match.fetch("selected_reference_edm"),
        "template_fit_score" => match.fetch("top_matches").first.fetch("template_fit_score"),
        "reuse_mode" => match.fetch("route"),
        "top1_correct" => template_id == test.fetch("expected_top1"),
        "truth_status" => content.fetch("truth_status"),
        "render_scope" => content.fetch("truth_status").include?("promotion_unverified") ? "skeleton_validation_only" : "internal_visual_validation",
        "historical_inheritance_target_percent" => 70,
        "controlled_adaptation_budget_percent" => 20,
        "new_design_budget_percent" => 10,
        "output_html" => relative(File.join(out, "editable_edm.html"))
      }
      File.write(File.join(out, "render_result.yaml"), YAML.dump(result))
      result
    end

    private

    def copy_assets(source_assets, out)
      target = File.join(out, "assets")
      FileUtils.mkdir_p(target)
      source_assets.each_with_object({}) do |(slot, source), memo|
        absolute = File.join(root, source)
        raise "Missing official asset #{source}" unless File.file?(absolute)
        name = "#{slot}#{File.extname(source)}"
        FileUtils.cp(absolute, File.join(target, name))
        memo[slot] = "assets/#{name}"
      end
    end

    def render_html(case_id, template, content, assets, match)
      regions = template.fetch("section_sequence")
      rhythm = YAML.safe_load(File.read(File.join(root, "templates", "historical", template.fetch("template_id"), "style_tokens.yaml"))).fetch("section_height_ratios")
      body = case template.fetch("template_id")
             when "HIST-TPL-002" then staged_launch(regions, rhythm, content, assets)
             when "HIST-TPL-003" then product_conversion(regions, rhythm, content, assets)
             when "HIST-TPL-005" then theme_promotion(regions, rhythm, content, assets)
             when "HIST-TPL-008" then editorial_education(regions, rhythm, content, assets)
             else generic_historical(regions, rhythm, content, assets)
             end
      palette = YAML.safe_load(File.read(File.join(root, "templates", "historical", template.fetch("template_id"), "style_tokens.yaml"))).fetch("palette")
      notice = content.fetch("truth_status").include?("promotion_unverified") ? "PROMOTION TRUTH UNVERIFIED · 価格／割引／期間は描画していません" : "INTERNAL HISTORICAL TEMPLATE VALIDATION · 外部配信不可"
      <<~HTML
        <!doctype html>
        <html lang="ja">
        <head>
          <meta charset="utf-8">
          <meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
          <link rel="icon" href="data:,">
          <title>#{h(content.fetch("product_name"))} · #{template.fetch("template_id")}</title>
          <style>#{email_css(palette)}</style>
        </head>
        <body data-case-id="#{case_id}" data-template-id="#{template.fetch("template_id")}" data-reference-id="#{template.fetch("reference_edm")}" data-target-rhythm="#{rhythm.join(",")}" data-historical-inheritance="70" data-controlled-adaptation="20" data-new-design="10">
          <div class="internal-notice">#{h(notice)}</div>
          <main class="email-canvas">
            <header class="brand-head"><strong>SwitchBot</strong><span>#{h(content.fetch("product_name"))}</span></header>
            #{body}
          </main>
          <script>document.documentElement.dataset.rendered = "true";</script>
        </body>
        </html>
      HTML
    end

    def staged_launch(regions, rhythm, c, a)
      parts = []
      parts << region(regions[0], rhythm[0], "hero hero--stage") { image(a.fetch("hero"), c.fetch("product_name"), "hero__image") + copy_block("NEW PRODUCT", c.fetch("headline"), c.fetch("body"), 1) }
      parts << region(regions[1], rhythm[1], "statement statement--dark") { copy_block("PRIMARY VALUE", c.fetch("primary_feature"), c.fetch("body"), 2) + image(a.fetch("hero"), c.fetch("product_name"), "hero__image") }
      parts << region(regions[2], rhythm[2], "visual-panel") { image(a.fetch("ui"), "公式デバイス画面", "visual-panel__image") + copy_block("DETAIL 01", c.fetch("secondary_features")[0], "製品が扱う情報を、公式画面から確認します。", 3) }
      parts << region(regions[3], rhythm[3], "visual-panel visual-panel--reverse") { image(a.fetch("detail"), "公式製品詳細", "visual-panel__image") + copy_block("DETAIL 02", c.fetch("secondary_features")[1], "次の章へ進む前に、製品の役割をひとつに整理します。", 4) }
      parts << region(regions[4], rhythm[4], "feature-band") { feature_list(c.fetch("secondary_features")) }
      parts << region(regions[5], rhythm[5], "product-reset") { image(a.fetch("hero"), c.fetch("product_name"), "product-reset__image") + copy_block("PRODUCT RESET", c.fetch("product_name"), "長い説明のあとに、製品本体へ視線を戻します。", 6) }
      parts << region(regions[6], rhythm[6], "cta-region") { cta(c.fetch("headline"), c.fetch("cta"), c.fetch("cta_url")) }
      parts << region(regions[7], rhythm[7], "deep-footer") { footer(c) }
      parts.join
    end

    def product_conversion(regions, rhythm, c, a)
      parts = []
      parts << region(regions[0], rhythm[0], "hero hero--warm") { copy_block(c.fetch("product_name"), c.fetch("headline"), c.fetch("body"), 1) + image(a.fetch("hero"), c.fetch("product_name"), "hero__image") + cta("", c.fetch("cta"), c.fetch("cta_url")) }
      parts << region(regions[1], rhythm[1], "lifestyle-gallery") { image(a.fetch("lifestyle"), "公式 Lifestyle ビジュアル", "lifestyle-gallery__wide") }
      parts << region(regions[2], rhythm[2], "feature-band") { copy_block("PRIMARY USP", c.fetch("primary_feature"), "製品価値を先に伝え、詳細はその後に展開します。", 3) + feature_list(c.fetch("secondary_features").first(2)) }
      parts << region(regions[3], rhythm[3], "visual-panel") { image(a.fetch("detail"), "取り付け可否確認用の公式対応例", "visual-panel__image") + copy_block("PURCHASE CHECK", c.fetch("secondary_features")[2], c.fetch("disclaimer"), 4) }
      parts << region(regions[4], rhythm[4], "comparison-row") { feature_list(c.fetch("secondary_features")) }
      parts << region(regions[5], rhythm[5], "offer-omitted") { "<p>OPTIONAL OFFER REGION OMITTED · 本キャンペーンは価格／特典なし</p>" }
      parts << region(regions[6], rhythm[6], "product-reset") { image(a.fetch("hero"), c.fetch("product_name"), "product-reset__image") + copy_block("PRODUCT", c.fetch("headline"), "製品本体を再提示し、購入判断へ戻します。", 7) }
      parts << region(regions[7], rhythm[7], "cta-region") { cta(c.fetch("headline"), c.fetch("cta"), c.fetch("cta_url")) }
      parts << region(regions[8], rhythm[8], "deep-footer") { footer(c) }
      parts.join
    end

    def theme_promotion(regions, rhythm, c, a)
      parts = []
      parts << region(regions[0], rhythm[0], "hero hero--security") { copy_block("THEME PROMOTION", c.fetch("headline"), c.fetch("body"), 1) + image(a.fetch("hero"), "テーマシーンの公式素材", "hero__image") }
      parts << region(regions[1], rhythm[1], "problem-frame") { copy_block("WHY NOW", c.fetch("primary_feature"), c.fetch("promotion_notice"), 2) }
      products = [
        [a.fetch("product_a"), a.fetch("hero"), c.fetch("secondary_features")[0], "玄関になじむ外観"],
        [a.fetch("product_a"), a.fetch("detail_a"), c.fetch("secondary_features")[1], "施錠と状態確認"],
        [a.fetch("product_b"), a.fetch("detail_b"), c.fetch("secondary_features")[2], "天気と室内環境"],
        [a.fetch("product_b"), a.fetch("detail_b"), c.fetch("secondary_features")[3], "家族の予定"]
      ]
      4.times do |index|
        product = products[index]
        parts << region(regions[index + 2], rhythm[index + 2], "scenario-product #{index.odd? ? "scenario-product--reverse" : ""}") do
          image(product[0], product[2], "scenario-product__main") + copy_block("SCENE #{format("%02d", index + 1)} · #{product[3]}", product[2], "同じ訴求の繰り返しではなく、役割と確認ポイントを分けて提示します。", index + 3) + image(product[1], "#{product[2]} 公式詳細", "scenario-product__detail")
        end
      end
      parts << region(regions[6], rhythm[6], "proof-guard") { "<strong>PROOF REGION</strong><p>承認済み Review／No.1／数値根拠がないため、空の Proof を捏造しません。</p>" }
      parts << region(regions[7], rhythm[7], "offer-guard") { "<strong>PROMOTION REGION BLOCKED</strong><p>#{h(c.fetch("promotion_notice"))}</p>" }
      parts << region(regions[8], rhythm[8], "cta-region") { cta("製品ごとの役割を確認する", c.fetch("cta"), c.fetch("cta_url")) }
      parts << region(regions[9], rhythm[9], "deep-footer") { footer(c) }
      parts.join
    end

    def editorial_education(regions, rhythm, c, a)
      parts = []
      parts << region(regions[0], rhythm[0], "editorial-hero") { image(a.fetch("hero"), c.fetch("product_name"), "editorial-hero__image") + copy_block("PRODUCT GUIDE", c.fetch("headline"), c.fetch("body"), 1) }
      parts << region(regions[1], rhythm[1], "editorial-context") { copy_block("CONTEXT", c.fetch("primary_feature"), "理解する順番を先に示し、同じ訴求を長く繰り返しません。", 2) }
      parts << region(regions[2], rhythm[2], "comparison-framework") { feature_list(c.fetch("secondary_features")) }
      assets = [a.fetch("detail"), a.fetch("ui"), a.fetch("hero"), a.fetch("detail")]
      4.times do |index|
        title = c.fetch("secondary_features")[index % c.fetch("secondary_features").length]
        parts << region(regions[index + 3], rhythm[index + 3], "editorial-chapter #{index.odd? ? "editorial-chapter--reverse" : ""}") { image(assets[index], "#{title} 公式素材", "editorial-chapter__image") + copy_block("CHAPTER #{format("%02d", index + 1)}", title, index == 3 ? c.fetch("disclaimer") : "画面の役割を一章ずつ理解します。", index + 4) }
      end
      parts << region(regions[7], rhythm[7], "cta-region") { cta("一画面でできることを、公式ページで確認", c.fetch("cta"), c.fetch("cta_url")) }
      parts << region(regions[8], rhythm[8], "deep-footer") { footer(c) }
      parts.join
    end

    def generic_historical(regions, rhythm, c, a)
      regions.map.with_index do |name, index|
        region(name, rhythm[index] || 1, index.zero? ? "hero" : "statement") { copy_block(index.zero? ? c.fetch("product_name") : "SECTION #{index + 1}", index.zero? ? c.fetch("headline") : c.fetch("primary_feature"), c.fetch("body"), index + 1) + (index.zero? ? image(a.values.first, c.fetch("product_name"), "hero__image") : "") }
      end.join
    end

    def region(name, ratio, klass)
      %(<section class="region #{klass}" data-region="#{h(name)}" data-target-ratio="#{ratio}" style="--region-height:#{(ratio.to_f * 580).round}px">#{yield}</section>)
    end

    def copy_block(kicker, title, body, index)
      %(<div class="copy"><small>#{format("%02d", index)} · #{h(kicker)}</small><h#{index == 1 ? 1 : 2}>#{h(title)}</h#{index == 1 ? 1 : 2}><p>#{h(body)}</p></div>)
    end

    def image(path, alt, klass)
      %(<figure class="#{klass}"><img src="#{h(path)}" width="1200" height="1200" alt="#{h(alt)}" loading="#{klass.include?("hero") ? "eager" : "lazy"}"></figure>)
    end

    def feature_list(items)
      %(<ol class="feature-list">#{items.map.with_index(1) { |item, index| "<li><span>#{format("%02d", index)}</span><strong>#{h(item)}</strong></li>" }.join}</ol>)
    end

    def cta(title, label, url)
      title_html = title.to_s.empty? ? "" : "<h2>#{h(title)}</h2>"
      %(<div class="cta-box">#{title_html}<a href="#{h(url)}">#{h(label)}</a></div>)
    end

    def footer(content)
      <<~HTML
        <div class="footer-mark"><strong>SwitchBot</strong><span>暮らしに、心地よいテクノロジーを。</span></div>
        <div class="footer-links"><span>公式サイト</span><span>サポート</span><span>配信設定</span><span>配信停止</span></div>
        <p>社内 Historical Template 骨格検証用です。正式配信前に、承認済みの法務・会社情報・ESP Token・配信停止リンクへ置き換える必要があります。</p>
        <small>Copy source: #{h(content.fetch("copy_source"))}</small>
      HTML
    end

    def email_css(palette)
      <<~CSS
        :root{--paper:#{palette.fetch("paper")};--ink:#{palette.fetch("ink")};--primary:#{palette.fetch("primary")};--secondary:#{palette.fetch("secondary")};--dark:#{palette.fetch("dark")};--white:#fffdf8}
        *{box-sizing:border-box}html,body{margin:0;overflow-x:clip;background:#e9e6df;color:var(--ink);font-family:"Avenir Next","Noto Sans JP","Hiragino Kaku Gothic ProN",sans-serif}body{padding:0 0 48px}.internal-notice{position:sticky;top:0;z-index:10;width:min(600px,100%);margin:0 auto;padding:9px 16px;background:#2b2926;color:#fffdf8;font-size:10px;font-weight:800;letter-spacing:.08em;text-align:center}.email-canvas{width:min(600px,100%);margin:0 auto;background:var(--paper);box-shadow:0 16px 52px rgba(25,20,15,.14)}.brand-head{height:58px;padding:0 26px;display:flex;align-items:center;justify-content:space-between;background:var(--white);border-bottom:1px solid color-mix(in srgb,var(--ink) 14%,transparent);font-size:11px}.brand-head strong{font-size:18px}.region{min-height:var(--region-height);padding:52px 46px;display:grid;align-content:center;gap:28px;overflow:hidden}.copy{max-width:44ch}.copy small{display:block;margin-bottom:12px;color:var(--primary);font-size:10px;font-weight:800;letter-spacing:.14em}.copy h1,.copy h2{margin:0;letter-spacing:-.04em;line-height:1.06}.copy h1{font-size:44px}.copy h2{font-size:32px}.copy p{margin:18px 0 0;font-size:14px;line-height:1.85}.region figure{margin:0}.region img{display:block;width:100%;height:auto}.hero{grid-template-columns:1fr;min-height:680px}.hero__image img{max-height:400px;object-fit:contain}.hero--stage{background:var(--white)}.statement--dark,.hero--security{background:var(--dark);color:var(--white)}.statement--dark .copy small,.hero--security .copy small{color:var(--secondary)}.hero--warm{background:linear-gradient(160deg,var(--paper),color-mix(in srgb,var(--secondary) 20%,var(--paper)))}.statement{min-height:500px}.statement .copy{margin-left:auto;margin-right:auto;text-align:center}.visual-panel,.scenario-product,.editorial-chapter{grid-template-columns:1.05fr .95fr;align-items:center}.visual-panel--reverse .visual-panel__image,.scenario-product--reverse .scenario-product__main,.editorial-chapter--reverse .editorial-chapter__image{order:2}.visual-panel__image img,.scenario-product__main img,.editorial-chapter__image img{max-height:420px;object-fit:cover}.feature-band,.comparison-framework{background:var(--white)}.feature-list{margin:0;padding:0;list-style:none;border-top:1px solid color-mix(in srgb,var(--ink) 20%,transparent)}.feature-list li{min-height:76px;padding:18px 0;display:grid;grid-template-columns:48px 1fr;align-items:center;border-bottom:1px solid color-mix(in srgb,var(--ink) 20%,transparent)}.feature-list span{color:var(--primary);font-size:11px;font-weight:800}.feature-list strong{font-size:17px;line-height:1.45}.lifestyle-gallery{padding:0}.lifestyle-gallery__wide img{min-height:440px;object-fit:cover}.product-reset{background:var(--white);grid-template-columns:1fr 1fr;align-items:center}.product-reset__image img{max-height:360px;object-fit:contain}.comparison-row{background:color-mix(in srgb,var(--secondary) 12%,var(--paper))}.offer-omitted,.proof-guard,.offer-guard{min-height:300px;text-align:center;background:repeating-linear-gradient(-45deg,var(--paper),var(--paper) 12px,color-mix(in srgb,var(--ink) 4%,var(--paper)) 12px,color-mix(in srgb,var(--ink) 4%,var(--paper)) 24px)}.offer-guard{background:var(--secondary);color:var(--ink)}.scenario-product__detail img{max-height:180px;object-fit:contain}.editorial-hero{padding:0;background:var(--white)}.editorial-hero__image img{width:100%;max-height:420px;object-fit:contain}.editorial-hero .copy{padding:20px 46px 60px}.editorial-context{background:var(--dark);color:var(--white)}.cta-region{min-height:360px;background:var(--primary);color:var(--white);text-align:center}.cta-box h2{max-width:18ch;margin:0 auto 24px;font-size:32px;line-height:1.15}.cta-box a{display:inline-flex;min-height:48px;padding:14px 30px;align-items:center;justify-content:center;border-radius:999px;background:var(--dark);color:var(--white);font-weight:800;text-decoration:none}.hero .cta-box{text-align:left}.hero .cta-box a{margin-top:10px}.deep-footer{min-height:520px;background:var(--dark);color:var(--white);align-content:start}.footer-mark{display:flex;justify-content:space-between;align-items:baseline;padding-bottom:24px;border-bottom:1px solid color-mix(in srgb,var(--white) 25%,transparent)}.footer-mark strong{font-size:26px}.footer-mark span{font-size:11px}.footer-links{display:grid;grid-template-columns:1fr 1fr;gap:12px;font-size:12px}.deep-footer p{max-width:58ch;color:color-mix(in srgb,var(--white) 72%,transparent);font-size:11px;line-height:1.8}.deep-footer small{overflow-wrap:anywhere;color:color-mix(in srgb,var(--white) 58%,transparent)}a:focus-visible{outline:3px solid var(--secondary);outline-offset:3px}a:hover{filter:brightness(1.08)}a:active{filter:brightness(.92)}
        @media(max-width:480px){body{padding-bottom:0}.internal-notice{position:static}.email-canvas{box-shadow:none}.brand-head{height:52px;padding:0 18px}.region{padding:40px 24px;gap:22px}.copy h1{font-size:34px}.copy h2,.cta-box h2{font-size:27px}.visual-panel,.scenario-product,.editorial-chapter,.product-reset{grid-template-columns:1fr}.visual-panel--reverse .visual-panel__image,.scenario-product--reverse .scenario-product__main,.editorial-chapter--reverse .editorial-chapter__image{order:0}.hero{min-height:620px}.editorial-hero .copy{padding:16px 24px 44px}.footer-mark{display:block}.footer-mark span{display:block;margin-top:8px}.footer-links{grid-template-columns:1fr}}
        @media(prefers-reduced-motion:reduce){*{scroll-behavior:auto!important;transition:none!important;animation:none!important}}
      CSS
    end

    def content_mapping(template, content)
      {
        "schema_version" => "1.0.0",
        "template_id" => template.fetch("template_id"),
        "reference_edm" => template.fetch("reference_edm"),
        "truth_status" => content.fetch("truth_status"),
        "regions" => template.fetch("section_sequence").map.with_index { |region, index| {"region_id" => region, "mapping_status" => "mapped", "content_source" => content.fetch("copy_source"), "adaptation" => index < 2 || index == template.fetch("section_sequence").length - 1 ? "STRICT" : "FLEXIBLE_OR_OPTIONAL"} }
      }
    end

    def asset_mapping(template, sources, local)
      {"schema_version" => "1.0.0", "template_id" => template.fetch("template_id"), "ai_product_redraw" => false, "assets" => sources.map { |slot, source| {"slot" => slot, "source_path" => source, "local_copy" => local.fetch(slot), "approved_scope" => "internal_renderer_pilot_only", "source_required" => true} }}
    end

    def relative(path)
      path.sub("#{root}/", "")
    end

    def h(value)
      CGI.escapeHTML(value.to_s)
    end
  end
end

if $PROGRAM_NAME == __FILE__
  root = File.expand_path("..", __dir__)
  summary = EDMGenerator::HistoricalTemplateRenderer.new(root).render_all(ARGV[0] || "tests/historical_template_test_cases.yaml")
  puts YAML.dump(summary)
end
