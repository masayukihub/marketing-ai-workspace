# frozen_string_literal: true

require "fileutils"
require "yaml"
require_relative "support"
require_relative "../../renderer/components/switchbot_brand_components"
require_relative "../../renderer/layouts/email_document"

module ProductionEDM
  class ProductionRenderer
    attr_reader :root, :css

    def initialize(root)
      @root = root
      @css = File.read(File.join(root, "renderer/css/switchbot_brand_email.css"))
    end

    def write_package(result)
      out = File.join(root, "production_output", result.fetch("case_id"))
      FileUtils.mkdir_p(out)
      html = render_html(result, out)
      File.write(File.join(out, "editable_edm.html"), html)
      File.write(
        File.join(out, "asset_manifest.yaml"),
        YAML.dump(
          {
            "schema_version" => "1.0.0",
            "case_id" => result.fetch("case_id"),
            "resolver_policy" => "official-first; missing hero product asset blocks rendering; AI may support backgrounds only",
            "assets" => result.fetch("assets"),
            "design_scope_gaps" => result.fetch("assets").select { |asset| asset["approval_scope"] != "design_production" }.map { |asset| asset["asset_id"] },
            "send_time_channel_scope_gaps" => result.fetch("assets").select { |asset| asset["channel_scope"] != "CHANNEL_APPROVED" }.map { |asset| asset["asset_id"] }
          }
        )
      )
      File.write(File.join(out, "truth_manifest.yaml"), YAML.dump(result.reject { |key, _| key == "html" }))
      File.write(File.join(out, "final_copy.md"), final_copy_markdown(result))
      File.write(File.join(out, "copy_auto_qa.yaml"), YAML.dump({"case_id" => result.fetch("case_id"), "status" => result.dig("copy", "finalization_status"), "pipeline" => result.dig("copy", "pipeline"), "checks" => result.dig("copy", "auto_qa"), "dropped_optional_copy" => result.dig("copy", "dropped_optional_copy")}))
      File.write(File.join(out, "qa_report.md"), qa_markdown(result))
      out
    end

    private

    def render_html(result, out)
      c = PilotRenderer::SwitchBotBrandComponents
      product = result.fetch("product")
      campaign = result.fetch("campaign")
      decision = result.fetch("decision")
      status = result.dig("qa", "production_status")
      name = Support.value(product.dig("product", "official_name_ja"))
      body = +""
      body << c.brand_header(context: name, chapter: "PRODUCT STORY")
      result.fetch("modules").each do |mod|
        body << render_module(c, mod, result, out)
      end
      rendered = PilotRenderer::EmailDocument.render(
        title: "#{name} · Visual Deliverable Candidate",
        css: "#{css}\n#{historical_template_css(decision.fetch("selected_historical_template", nil))}",
        body: body,
        case_id: result.fetch("case_id"),
        gate: status
      )
      rendered.sub(
        "<body ",
        %(<body data-render-mode="#{decision.fetch("render_mode")}" data-historical-template="#{decision.fetch("selected_historical_template", "")}" data-historical-reference="#{decision.fetch("historical_reference_edm", "")}" data-production-status="#{status}" )
      )
    end

    def render_module(c, mod, result, out)
      module_id = mod.fetch("module_id")
      product_id = result.fetch("product_id")
      product = result.fetch("product")
      campaign = result.fetch("campaign")
      name = Support.value(product.dig("product", "official_name_ja"))
      url = Support.value(campaign.dig("cta", "url"))
      final_label = Support.value(campaign.dig("cta", "copy"))
      copy = result.fetch("copy").fetch("entries")
      asset = result.fetch("assets").find { |item| item["module_id"] == mod.fetch("instance_id") || item["module_id"] == module_id }
      image = asset && asset["source_path"] ? Support.relative_asset(root, out, asset.fetch("source_path")) : nil

      if product_id == "lock_ultra"
        render_lock_module(c, mod, copy, name, url, final_label, image, result)
      else
        render_daily_module(c, mod, copy, name, url, final_label, image, result)
      end
    end

    def historical_template_css(template_id)
      case template_id
      when "HIST-TPL-003"
        <<~CSS
          body[data-historical-template="HIST-TPL-003"] .email-canvas { background: #f6efe5; }
          body[data-historical-template="HIST-TPL-003"] .sb-hero { min-height: 47rem; }
          body[data-historical-template="HIST-TPL-003"] .sb-visual-feature { background: #f4e7d8; }
          body[data-historical-template="HIST-TPL-003"] .sb-final-cta { background: #f04a22; }
        CSS
      when "HIST-TPL-008"
        <<~CSS
          body[data-historical-template="HIST-TPL-008"] .email-canvas { background: #f4f1ea; }
          body[data-historical-template="HIST-TPL-008"] .sb-hero { min-height: 44rem; background: #f7f5f0; }
          body[data-historical-template="HIST-TPL-008"] .sb-statement { background: #3a3631; color: #fffdf8; }
          body[data-historical-template="HIST-TPL-008"] .sb-visual-feature,
          body[data-historical-template="HIST-TPL-008"] .sb-split-feature { border-top: 1px solid #b8aea2; }
        CSS
      else
        ""
      end
    end

    def render_lock_module(c, mod, copy, name, url, final_label, image, result)
      id = mod.fetch("instance_id")
      case [mod.fetch("module_id"), id]
      when ["MOD-HERO-PRODUCT", "MOD-HERO-PRODUCT"]
        c.hero(product: name, headline: text(copy, "hero_headline"), body: text(copy, "hero_body"), image: image, alt: "#{name} ブラック", module_id: id, theme: "warm")
      when ["MOD-STORY-LIFESTYLE", "MOD-STORY-LIFESTYLE"]
        c.visual_feature(kicker: "DESIGN", title: text(copy, "lifestyle_heading"), body: text(copy, "lifestyle_body"), image: image, alt: "#{name} ブラックとシルバーの公式ビジュアル", module_id: id, note: "", tone: "paper", media_class: "sb-media--lock-lifestyle")
      when ["MOD-STORY-PRODUCT-DETAIL", "MOD-STORY-PRODUCT-DETAIL"]
        c.statement(kicker: "EVERYDAY SECURITY", title: text(copy, "product_identity"), body: text(copy, "product_identity_body"), module_id: id, tone: "white")
      when ["MOD-STORY-PROBLEM", "MOD-STORY-PROBLEM"]
        c.statement(kicker: "AUTO-LOCK", title: text(copy, "pre_purchase_question"), body: text(copy, "problem_body"), module_id: id, tone: "red")
      when ["MOD-STORY-PRODUCT-DETAIL", "MOD-STORY-PRODUCT-DETAIL@2"]
        c.visual_feature(kicker: "INSTALLATION", title: text(copy, "compatibility_heading"), body: text(copy, "compatibility_disclaimer"), image: image, alt: "取り付け可否確認用の公式対応例", module_id: id, note: "", tone: "paper")
      when ["MOD-STORY-FAQ", "MOD-STORY-FAQ"]
        c.checklist(kicker: "PURCHASE CHECK", title: "購入前に、3つだけ確認。", items: texts(copy, "check_item"), module_id: id, note: "")
      when ["MOD-CONV-SECONDARY", "MOD-CONV-SECONDARY"]
        c.cta_checkpoint(title: text(copy, "mid_cta"), body: text(copy, "mid_cta_body"), label: text(copy, "mid_cta"), url: url, module_id: id)
      when ["MOD-STORY-PRIMARY-USP", "MOD-STORY-PRIMARY-USP"]
        c.product_reset(product: name, title: text(copy, "hero_headline"), image: image, alt: "#{name} 製品本体", module_id: id, note: "")
      when ["MOD-CONV-CTA-BAND", "MOD-CONV-CTA-BAND"]
        c.final_cta(title: text(copy, "final_cta_title"), body: text(copy, "final_cta_body"), label: final_label, url: url, module_id: id)
      when ["MOD-SYSTEM-BRAND-FOOTER", "MOD-SYSTEM-BRAND-FOOTER"]
        c.production_footer(footer: result.fetch("footer"), case_id: result.fetch("case_id"), production_status: result.dig("qa", "production_status"), module_id: id)
      else
        ""
      end
    end

    def render_daily_module(c, mod, copy, name, url, final_label, image, result)
      id = mod.fetch("instance_id")
      case mod.fetch("module_id")
      when "MOD-HERO-PRODUCT"
        c.hero(product: name, headline: text(copy, "hero_headline"), body: text(copy, "hero_body"), image: image, alt: name, module_id: id, theme: "cool")
      when "MOD-STORY-PRIMARY-USP"
        c.statement(kicker: "ONE SCREEN", title: text(copy, "one_screen_heading"), body: text(copy, "one_screen_body"), module_id: id, tone: "paper")
      when "MOD-STORY-APP-UI"
        c.visual_feature(kicker: "DEVICE UI", title: text(copy, "device_ui_heading"), body: text(copy, "device_ui_body"), image: image, alt: "#{name} の公式デバイス画面例", module_id: id, note: "", tone: "cool")
      when "MOD-STORY-FEATURE-SPLIT"
        c.split_feature(kicker: "WEATHER / INDOOR", title: text(copy, "environment_heading"), body: text(copy, "environment_body"), image: image, alt: "天気と室内環境の公式画面例", module_id: id, note: "", reverse: false, tone: "white")
      when "MOD-STORY-IMAGE-TEXT"
        c.statement(kicker: "FAMILY SCHEDULE", title: text(copy, "schedule_heading"), body: text(copy, "schedule_body"), module_id: id, tone: "paper")
      when "MOD-STORY-FAQ"
        c.checklist(kicker: "BEFORE USE", title: "利用条件は、購入前に確認。", items: texts(copy, "use_condition"), module_id: id, note: text(copy, "condition_disclaimer"))
      when "MOD-CONV-SECONDARY"
        c.cta_checkpoint(title: text(copy, "mid_cta"), body: text(copy, "mid_cta_body"), label: text(copy, "mid_cta"), url: url, module_id: id)
      when "MOD-STORY-PRODUCT-DETAIL"
        c.product_reset(product: name, title: text(copy, "hero_headline"), image: image, alt: "#{name} 製品本体", module_id: id, note: "")
      when "MOD-CONV-CTA-BAND"
        c.final_cta(title: text(copy, "final_cta_title"), body: text(copy, "final_cta_body"), label: final_label, url: url, module_id: id)
      when "MOD-SYSTEM-BRAND-FOOTER"
        c.production_footer(footer: result.fetch("footer"), case_id: result.fetch("case_id"), production_status: result.dig("qa", "production_status"), module_id: id)
      else
        ""
      end
    end

    def text(entries, role)
      entries.find { |entry| entry.fetch("role") == role }.fetch("text")
    end

    def texts(entries, role)
      entries.select { |entry| entry.fetch("role") == role }.map { |entry| entry.fetch("text") }
    end

    def final_copy_markdown(result)
      copy = result.fetch("copy")
      rows = copy.fetch("entries").map do |item|
        "- **#{item.fetch("role")}**: #{item.fetch("text")}\n  - Evidence: #{item.fetch("evidence_status")}\n  - Approval: #{item.fetch("approval_status")}\n  - Source: #{item.fetch("source")}"
      end.join("\n")
      <<~MD
        # #{result.fetch("case_id")} Final Japanese Copy

        - Finalization: **#{copy.fetch("finalization_status")}**
        - Verification: **#{copy.fetch("verification_status")}**
        - Approval: **#{copy.fetch("approval_status")}**
        - Scope: `#{copy.fetch("scope")}`

        - Auto-QA: **#{copy.fetch("auto_qa").values.all? ? "PASS" : "BLOCK"}**

        #{rows}

        ## Excluded from Candidate

        - Price/promotion: not applicable to this evergreen campaign; no price token appears in copy.
        - Numeric/performance claims: excluded.
        - Proof/review claims: excluded because no Approved proof record exists.
      MD
    end

    def qa_markdown(result)
      qa = result.fetch("qa")
      hard = qa.fetch("hard_rule_checks").map { |name, pass| "- [#{pass ? "x" : " "}] #{name}: #{pass ? "PASS" : "FAIL"}" }.join("\n")
      production = qa.fetch("production_readiness_checks").map { |name, pass| "- [#{pass ? "x" : " "}] #{name}: #{pass ? "PASS" : "OPEN"}" }.join("\n")
      <<~MD
        # #{result.fetch("case_id")} Production QA

        - Production Status: **#{qa.fetch("production_status")}**
        - Browser QA: **PENDING**
        - No Fake Content: **#{qa.fetch("no_fake_content") ? "PASS" : "FAIL"}**
        - No Product Redraw: **#{qa.fetch("no_product_redraw") ? "PASS" : "FAIL"}**

        ## Hard Rules

        #{hard}

        ## Production Readiness

        #{production}

        ## Open Gates

        #{qa.fetch("production_gaps").map { |gap| "- #{gap}" }.join("\n")}
      MD
    end
  end
end
