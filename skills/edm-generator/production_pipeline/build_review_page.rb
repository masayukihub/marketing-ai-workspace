# frozen_string_literal: true

require "yaml"
require "json"
require "cgi"
require "date"
require "time"

ROOT = File.expand_path("..", __dir__)
CASES = %w[PILOT-A-LOCK-ULTRA PILOT-B-DAILY-STATION].freeze
QUESTIONS = [
  ["brand_fit", "01", "像不像 SwitchBot", "与 Approved 历史 EDM 放在一起，是否属于同一品牌视觉体系？"],
  ["content_completeness", "02", "内容是否完整", "是否讲清该复杂产品完成购买判断所需的内容？"],
  ["length_necessity", "03", "长度是否由内容驱动", "模块是否各自承担新信息，而不是重复四个卖点凑长度？"],
  ["visual_rhythm", "04", "视觉节奏是否继承品牌习惯", "产品、场景、Feature、CTA 与 Footer 的出现节奏是否成立？"],
  ["japanese_copy", "05", "日语文案是否可继续推进", "语气是否自然、具体，并且没有把未核实内容伪装成事实？"],
  ["traceability", "06", "真值与素材是否可追溯", "Claim、价格、CTA、素材和缺口是否清楚可查？"]
].freeze

def load_yaml(path)
  YAML.safe_load(File.read(path), permitted_classes: [Date, Time], aliases: true)
end

def h(value)
  CGI.escapeHTML(value.to_s)
end

def value(node)
  node.is_a?(Hash) && node.key?("value") ? node["value"] : node
end

def status(node)
  node.is_a?(Hash) ? node["status"] : nil
end

def badge(label, kind = nil)
  cls = kind || label.to_s.downcase.gsub(/[^a-z]+/, "-")
  %(<span class="badge badge--#{h(cls)}">#{h(label)}</span>)
end

def select_field(case_id, id, label, help, options)
  option_html = ["<option value=\"\">未选择</option>"] + options.map { |item| %(<option value="#{h(item)}">#{h(item)}</option>) }
  <<~HTML
    <label class="review-field" for="#{h(case_id)}-#{h(id)}">
      <span class="review-field__label">#{h(label)}</span>
      <span class="review-field__help">#{h(help)}</span>
      <select id="#{h(case_id)}-#{h(id)}" name="#{h(id)}" data-review-field="#{h(id)}">
        #{option_html.join("\n")}
      </select>
      <span class="review-field__state" aria-live="polite"></span>
    </label>
  HTML
end

def case_html(case_id, manifest, browser)
  input = manifest.fetch("one_shot_input")
  decision = manifest.fetch("decision")
  length = decision.fetch("length")
  product = manifest.fetch("product")
  campaign = manifest.fetch("campaign")
  qa = manifest.fetch("qa")
  copy = manifest.fetch("copy")
  assets = manifest.fetch("assets")
  name = value(product.dig("product", "official_name_ja"))
  modules = manifest.fetch("modules").each_with_index.map do |mod, index|
    %(<li><span>#{format("%02d", index + 1)}</span><strong>#{h(mod.fetch("module_id"))}</strong><small>#{h(mod["reason"] || mod["visual_purpose"] || "system")}</small></li>)
  end.join
  asset_rows = assets.map do |asset|
    <<~HTML
      <tr>
        <td>#{h(asset["asset_id"] || "MISSING")}</td>
        <td>#{h(asset["asset_type"] || "—")}</td>
        <td>#{h(asset["visual_purpose"])}</td>
        <td>#{badge(asset["approval_status"], asset["approval_status"] == "APPROVED" ? "pass" : "open")}</td>
        <td>#{badge(asset["approval_scope"], asset["approval_scope"] == "production" ? "pass" : "open")}</td>
      </tr>
    HTML
  end.join
  copy_rows = copy.fetch("entries").map do |row|
    <<~HTML
      <tr>
        <td>#{h(row.fetch("role"))}</td>
        <td lang="ja">#{h(row.fetch("text"))}</td>
        <td>#{badge(row.fetch("evidence_status"), row.fetch("evidence_status") == "VERIFIED" ? "pass" : "open")}</td>
        <td>#{badge(row.fetch("approval_status"), row.fetch("approval_status") == "APPROVED" ? "pass" : "open")}</td>
      </tr>
    HTML
  end.join
  gaps = qa.fetch("production_gaps").map { |gap| "<li>#{h(gap)}</li>" }.join
  review_fields = QUESTIONS.map do |id, number, title, help|
    select_field(case_id, id, "#{number} · #{title}", help, %w[Yes Partially No])
  end.join
  final_field = select_field(case_id, "final_decision", "Final Decision", "请在完成六项判断后给出该 Pilot 的最终人工决定。", %w[READY MINOR_REVISION MAJOR_REVISION REJECT])

  <<~HTML
    <article class="case" id="#{h(case_id)}" data-case-id="#{h(case_id)}">
      <header class="case-hero">
        <p class="case-hero__index">#{h(case_id)}</p>
        <h2>#{h(name)}</h2>
        <p class="case-hero__purpose">#{h(value(campaign.dig("campaign", "theme")))} · #{h(value(campaign.dig("campaign", "objective")))}</p>
        <div class="case-hero__status">#{badge(qa.fetch("production_status"), "open")} #{badge("Browser #{browser.fetch("status")}", "pass")}</div>
      </header>

      <section class="stage" id="#{h(case_id)}-input">
        <div class="stage__number">1.0</div>
        <div class="stage__body">
          <h3>One-shot Input</h3>
          <blockquote>#{h(input.fetch("raw_input"))}</blockquote>
          <dl class="compact-dl">
            <div><dt>明确输入</dt><dd>Product · Theme · Objective · Promotion · Period · CTA</dd></div>
            <div><dt>未由用户指定</dt><dd>Template · Module · Length · Hero</dd></div>
          </dl>
        </div>
      </section>

      <section class="stage">
        <div class="stage__number">2.0</div>
        <div class="stage__body">
          <h3>Truth Resolution</h3>
          <div class="metric-line">
            <div><span>Product Truth</span><strong>#{h(manifest.dig("product_truth_completeness", "percent"))}%</strong></div>
            <div><span>External Publish</span><strong>#{value(product.dig("status", "external_publish_ready")) ? "READY" : "NOT READY"}</strong></div>
            <div><span>Approved Claims Used</span><strong>#{manifest.dig("traceability", "claims", "approved_used").length}</strong></div>
            <div><span>Price Used</span><strong>#{manifest.dig("traceability", "price", "used_in_copy") ? "YES" : "NO"}</strong></div>
          </div>
          <div class="truth-grid">
            <div><span>Official name</span><strong>#{h(name)}</strong>#{badge(status(product.dig("product", "official_name_ja")), "pass")}</div>
            <div><span>CTA URL</span><a href="#{h(value(campaign.dig("cta", "url")))}">#{h(value(campaign.dig("cta", "url")))}</a>#{badge(status(campaign.dig("cta", "url")), "pass")}</div>
            <div><span>Claims</span><strong>Approved external claim: 0</strong>#{badge("OPEN", "open")}</div>
            <div><span>Pricing</span><strong>Campaign does not use price</strong>#{badge("NOT_REQUIRED", "pass")}</div>
          </div>
        </div>
      </section>

      <section class="stage">
        <div class="stage__number">3.0</div>
        <div class="stage__body">
          <h3>Automatic Decisions</h3>
          <div class="decision-grid">
            <div><span>Campaign Type</span><strong>#{h(decision.fetch("campaign_type"))}</strong></div>
            <div><span>Template</span><strong>#{h(decision.fetch("selected_template"))}</strong></div>
            <div><span>Length</span><strong>#{h(length.fetch("length_class"))}</strong><small>#{h(length["reason"] || length["rationale"])}</small></div>
            <div><span>Rendered Length</span><strong>#{h(browser.dig("desktop", "totalLengthPx"))} px</strong></div>
            <div><span>Brand Mode</span><strong>#{h(decision.fetch("render_mode"))}</strong></div>
            <div><span>Modules</span><strong>#{h(manifest.fetch("modules").length)}</strong></div>
          </div>
          <ol class="module-sequence">#{modules}</ol>
        </div>
      </section>

      <section class="stage">
        <div class="stage__number">4.0</div>
        <div class="stage__body">
          <h3>Asset Resolver</h3>
          <p class="lede">官方素材优先；产品主图缺失即 Block。AI 只允许支持背景/生活方式，不得重绘或替代产品本体。</p>
          <div class="table-wrap" tabindex="0"><table><thead><tr><th>Asset</th><th>Type</th><th>Purpose</th><th>Resolver</th><th>Production Scope</th></tr></thead><tbody>#{asset_rows}</tbody></table></div>
        </div>
      </section>

      <section class="stage stage--visual">
        <div class="stage__number">5.0</div>
        <div class="stage__body">
          <h3>Rendered Output</h3>
          <div class="visual-grid">
            <figure><figcaption>Desktop Preview · 600 × 900</figcaption><img src="../production_output/#{h(case_id)}/desktop_preview.png" alt="#{h(name)} Desktop EDM Preview" width="600" height="900"></figure>
            <figure><figcaption>Mobile Preview · 390 × 844</figcaption><img src="../production_output/#{h(case_id)}/mobile_preview.png" alt="#{h(name)} Mobile EDM Preview" width="390" height="844"></figure>
            <figure class="visual-grid__full"><figcaption>Full-length EDM · 600 × #{h(browser.dig("desktop", "totalLengthPx"))}</figcaption><div class="full-scroll" tabindex="0"><img src="../production_output/#{h(case_id)}/full_edm.png" alt="#{h(name)} Full-length EDM" width="600" height="#{h(browser.dig("desktop", "totalLengthPx"))}"></div></figure>
          </div>
          <div class="output-links">
            <a href="../production_output/#{h(case_id)}/editable_edm.html">Editable HTML</a>
            <a href="../production_output/#{h(case_id)}/final_copy.md">Final Japanese Copy</a>
            <a href="../production_output/#{h(case_id)}/asset_manifest.yaml">Asset Manifest</a>
            <a href="../production_output/#{h(case_id)}/truth_manifest.yaml">Truth Manifest</a>
            <a href="../production_output/#{h(case_id)}/qa_report.md">QA Report</a>
          </div>
        </div>
      </section>

      <section class="stage">
        <div class="stage__number">6.0</div>
        <div class="stage__body">
          <h3>Copy & Traceability</h3>
          <div class="table-wrap" tabindex="0"><table><thead><tr><th>Role</th><th>Japanese Copy</th><th>Evidence</th><th>Approval</th></tr></thead><tbody>#{copy_rows}</tbody></table></div>
          <aside class="gate-note">
            <h4>Why this is still #{h(qa.fetch("production_status"))}</h4>
            <ul>#{gaps}</ul>
            <p>Browser QA PASS 只证明渲染技术成立，不会覆盖 Product Knowledge、外部 Claim、生产素材授权、Campaign、Footer/Legal、ESP 链接与文案审批。</p>
          </aside>
        </div>
      </section>

      <section class="human-review" aria-labelledby="#{h(case_id)}-review-title">
        <header>
          <p>Human Gate</p>
          <h3 id="#{h(case_id)}-review-title">Marketing Delivery Review</h3>
        </header>
        <div class="review-grid">#{review_fields}</div>
        <div class="final-decision">#{final_field}</div>
      </section>
    </article>
  HTML
end

browser_qa = JSON.parse(File.read(File.join(ROOT, "production_output", "browser_qa.json")))
manifests = CASES.to_h { |case_id| [case_id, load_yaml(File.join(ROOT, "production_output", case_id, "truth_manifest.yaml"))] }
anchors = Dir[File.join(ROOT, "output/playwright/phase5_5/approved/*.png")].sort.map do |path|
  file = File.basename(path)
  %(<figure><img src="../output/playwright/phase5_5/approved/#{h(file)}" alt="Tier A Approved #{h(file.sub("_recovered.png", ""))}" width="600" loading="lazy"><figcaption>#{h(file.sub("_recovered.png", ""))}</figcaption></figure>)
end.join
case_sections = CASES.map { |case_id| case_html(case_id, manifests.fetch(case_id), browser_qa.fetch(case_id)) }.join("\n")

html = <<~HTML
  <!doctype html>
  <html lang="zh-CN" data-theme="phase6-cobalt">
  <head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>Phase 6 · One-shot End-to-End Review</title>
    <link rel="icon" href="data:,">
    <link rel="stylesheet" href="../tokens.css">
    <style>
      /* Hallmark · genre: modern-minimal · macrostructure: Narrative Workflow · theme: Cobalt · tone: technical-utilitarian · nav: N9 edge-aligned minimal · footer: Ft2 inline single-line · contrast: pass (40–41) · slop: pass (42–45) · honest: pass (46) · chrome: pass (47) · tokens: pass (48) · responsive: pass (49) · mobile: pass (34, 49, 50–57) · icons: pass (30) */
      /* Hallmark · pre-emit critique: P5 H5 E5 S5 R5 V5 */
      * { box-sizing: border-box; }
      html { scroll-behavior: smooth; background: var(--p6-paper); color: var(--p6-ink); }
      body { margin: 0; min-width: 0; overflow-x: clip; font-family: var(--p6-font-body); background: var(--p6-paper); color: var(--p6-ink); line-height: 1.6; }
      img { display: block; max-width: 100%; height: auto; }
      a { color: var(--p6-accent); text-underline-offset: var(--p6-space-3xs); overflow-wrap: anywhere; }
      button, select { font: inherit; }
      button:focus-visible, select:focus-visible, a:focus-visible, [tabindex="0"]:focus-visible { outline: var(--rule-strong) solid var(--p6-focus); outline-offset: var(--p6-space-3xs); }
      h1, h2, h3, h4 { margin: 0; font-family: var(--p6-font-display); line-height: 1.08; overflow-wrap: anywhere; min-width: 0; }
      p { margin-block: 0; }
      .topline { display: flex; align-items: center; justify-content: space-between; gap: var(--p6-space-sm); min-height: 4rem; padding: var(--p6-space-sm); border-bottom: var(--rule-thin) solid var(--p6-rule); background: var(--p6-paper); }
      .wordmark { font-family: var(--p6-font-mono); font-size: var(--text-xs); font-weight: 700; letter-spacing: .08em; text-transform: uppercase; }
      .export { min-height: var(--p6-control-height); padding-inline: var(--p6-space-md); border: var(--rule-thin) solid var(--p6-accent); border-radius: var(--p6-radius); background: var(--p6-accent); color: var(--p6-accent-ink); font-weight: 700; cursor: pointer; white-space: nowrap; transition: background var(--p6-dur-micro) var(--p6-ease-out); }
      .export:hover { background: var(--p6-accent-hover); }
      .export:active { transform: translateY(var(--rule-thin)); }
      .export:disabled { opacity: .55; cursor: not-allowed; }
      .export[data-state="loading"] { cursor: progress; }
      .export[data-state="error"] { background: var(--p6-error); border-color: var(--p6-error); }
      .export[data-state="success"] { background: var(--p6-success); border-color: var(--p6-success); }
      .intro { max-width: var(--p6-page-max); margin-inline: auto; padding: var(--p6-space-4xl) var(--p6-space-sm) var(--p6-space-5xl); border-bottom: var(--rule-strong) solid var(--p6-ink); }
      .intro__meta { font-family: var(--p6-font-mono); color: var(--p6-accent); font-size: var(--text-sm); }
      .intro h1 { max-width: 18ch; margin-top: var(--p6-space-sm); font-size: clamp(2.5rem, 8vw, 6.4rem); letter-spacing: -.055em; }
      .intro__lede { max-width: var(--p6-copy-max); margin-top: var(--p6-space-xl); color: var(--p6-ink-2); font-size: var(--text-lg); }
      .intro__gate { max-width: var(--p6-copy-max); margin-top: var(--p6-space-md); padding-left: var(--p6-space-md); border-left: var(--rule-strong) solid var(--p6-warning); color: var(--p6-muted); }
      .anchor-band { max-width: var(--p6-page-max); margin-inline: auto; padding: var(--p6-space-3xl) var(--p6-space-sm); }
      .anchor-band header { display: grid; gap: var(--p6-space-xs); max-width: var(--p6-copy-max); }
      .anchor-band header p { font-family: var(--p6-font-mono); color: var(--p6-accent); font-size: var(--text-xs); text-transform: uppercase; }
      .anchor-band h2 { font-size: clamp(1.8rem, 4vw, 3.5rem); }
      .anchor-band__grid { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: var(--p6-space-xs); margin-top: var(--p6-space-xl); }
      .anchor-band figure { margin: 0; background: var(--p6-surface); border: var(--rule-thin) solid var(--p6-rule); }
      .anchor-band figure img { width: 100%; aspect-ratio: 3 / 4; object-fit: cover; object-position: top; }
      .anchor-band figcaption, .visual-grid figcaption { padding: var(--p6-space-xs); font-family: var(--p6-font-mono); color: var(--p6-muted); font-size: var(--text-xs); }
      .case { border-top: var(--rule-strong) solid var(--p6-ink); }
      .case-hero { display: grid; grid-template-columns: minmax(0, 1fr); gap: var(--p6-space-sm); width: 100%; max-width: var(--p6-page-max); margin-inline: auto; padding: var(--p6-space-4xl) var(--p6-space-sm) var(--p6-space-5xl); }
      .case-hero > * { min-width: 0; max-width: 100%; overflow-wrap: anywhere; }
      .case-hero__index { font-family: var(--p6-font-mono); color: var(--p6-accent); font-size: var(--text-sm); }
      .case-hero h2 { max-width: 17ch; font-size: clamp(2.4rem, 7vw, 6rem); letter-spacing: -.045em; }
      .case-hero__purpose { max-width: var(--p6-copy-max); color: var(--p6-muted); font-size: var(--text-lg); }
      .case-hero__status { display: flex; flex-wrap: wrap; gap: var(--p6-space-xs); margin-top: var(--p6-space-md); }
      .badge { display: inline-flex; align-items: center; min-height: 1.75rem; padding-inline: var(--p6-space-xs); border: var(--rule-thin) solid var(--p6-rule-strong); border-radius: var(--p6-radius); background: var(--p6-surface-2); color: var(--p6-ink-2); font-family: var(--p6-font-mono); font-size: var(--text-xs); line-height: 1; white-space: nowrap; }
      .badge--pass { border-color: var(--p6-success); background: var(--p6-success-soft); color: var(--p6-ink); }
      .badge--open { border-color: var(--p6-warning); background: var(--p6-warning-soft); color: var(--p6-ink); }
      .stage { display: grid; grid-template-columns: minmax(0, 1fr); width: 100%; max-width: var(--p6-page-max); margin-inline: auto; border-top: var(--rule-thin) solid var(--p6-rule); }
      .stage__number { padding: var(--p6-space-xl) var(--p6-space-sm) 0; color: var(--p6-accent); font-family: var(--p6-font-mono); font-size: var(--text-sm); }
      .stage__body { min-width: 0; padding: var(--p6-space-xl) var(--p6-space-sm) var(--p6-space-3xl); }
      .stage h3 { font-size: clamp(1.7rem, 4vw, 3rem); }
      blockquote { margin: var(--p6-space-xl) 0 0; max-width: var(--p6-copy-max); padding: var(--p6-space-md); border-left: var(--rule-strong) solid var(--p6-accent); background: var(--p6-surface); font-size: var(--text-md); }
      .compact-dl { display: grid; gap: var(--p6-space-xs); margin: var(--p6-space-lg) 0 0; }
      .compact-dl div { display: grid; gap: var(--p6-space-3xs); padding-block: var(--p6-space-xs); border-bottom: var(--rule-thin) solid var(--p6-rule); }
      dt { color: var(--p6-muted); font-size: var(--text-sm); }
      dd { margin: 0; font-weight: 700; }
      .metric-line, .decision-grid, .truth-grid { display: grid; grid-template-columns: minmax(0, 1fr); gap: var(--p6-space-xs); margin-top: var(--p6-space-xl); }
      .metric-line > div, .decision-grid > div, .truth-grid > div { display: grid; gap: var(--p6-space-2xs); min-width: 0; padding: var(--p6-space-md); border: var(--rule-thin) solid var(--p6-rule); background: var(--p6-surface); }
      .metric-line span, .decision-grid span, .truth-grid span { color: var(--p6-muted); font-size: var(--text-sm); }
      .metric-line strong { font-family: var(--p6-font-display); font-size: var(--text-xl); line-height: 1; }
      .decision-grid small { color: var(--p6-muted); }
      .truth-grid .badge { justify-self: start; }
      .module-sequence { display: grid; gap: 0; margin: var(--p6-space-xl) 0 0; padding: 0; list-style: none; border-top: var(--rule-thin) solid var(--p6-rule); }
      .module-sequence li { display: grid; grid-template-columns: 2.5rem minmax(0, 1fr); gap: var(--p6-space-xs); padding-block: var(--p6-space-xs); border-bottom: var(--rule-thin) solid var(--p6-rule); }
      .module-sequence li span { color: var(--p6-accent); font-family: var(--p6-font-mono); }
      .module-sequence li small { grid-column: 2; color: var(--p6-muted); }
      .lede { max-width: var(--p6-copy-max); margin-top: var(--p6-space-md); color: var(--p6-muted); }
      .table-wrap { width: 100%; max-width: 100%; min-width: 0; margin-top: var(--p6-space-xl); overflow-x: auto; overscroll-behavior-inline: contain; border: var(--rule-thin) solid var(--p6-rule); background: var(--p6-surface); }
      table { width: 100%; border-collapse: collapse; min-width: 46rem; }
      th, td { padding: var(--p6-space-xs); border-bottom: var(--rule-thin) solid var(--p6-rule); text-align: left; vertical-align: top; }
      th { background: var(--p6-surface-2); font-family: var(--p6-font-mono); color: var(--p6-muted); font-size: var(--text-xs); }
      td { font-size: var(--text-sm); }
      .visual-grid { display: grid; grid-template-columns: minmax(0, 1fr); gap: var(--p6-space-sm); margin-top: var(--p6-space-xl); align-items: start; }
      .visual-grid figure { margin: 0; min-width: 0; border: var(--rule-thin) solid var(--p6-rule); background: var(--p6-surface); }
      .visual-grid figure > img { width: 100%; }
      .full-scroll { max-height: 52rem; overflow: auto; border-top: var(--rule-thin) solid var(--p6-rule); background: var(--p6-surface-2); }
      .full-scroll img { width: 100%; }
      .output-links { display: flex; flex-wrap: wrap; gap: var(--p6-space-xs) var(--p6-space-md); margin-top: var(--p6-space-lg); }
      .output-links a { min-height: var(--p6-control-height); display: inline-flex; align-items: center; white-space: nowrap; }
      .gate-note { margin-top: var(--p6-space-xl); padding: var(--p6-space-lg); border-left: var(--rule-strong) solid var(--p6-warning); background: var(--p6-warning-soft); }
      .gate-note h4 { font-size: var(--text-lg); }
      .gate-note ul { margin-block: var(--p6-space-sm); padding-left: var(--p6-space-lg); }
      .gate-note li { min-width: 0; overflow-wrap: anywhere; }
      .gate-note p { max-width: var(--p6-copy-max); color: var(--p6-ink-2); }
      .human-review { max-width: var(--p6-page-max); margin-inline: auto; padding: var(--p6-space-4xl) var(--p6-space-sm) var(--p6-space-5xl); border-top: var(--rule-strong) solid var(--p6-accent); background: var(--p6-accent-soft); }
      .human-review header { display: grid; gap: var(--p6-space-xs); max-width: var(--p6-copy-max); }
      .human-review header p { color: var(--p6-accent); font-family: var(--p6-font-mono); font-size: var(--text-xs); text-transform: uppercase; }
      .human-review h3 { font-size: clamp(1.8rem, 4vw, 3.5rem); }
      .review-grid { display: grid; grid-template-columns: minmax(0, 1fr); gap: var(--p6-space-sm); margin-top: var(--p6-space-xl); }
      .review-field { display: grid; gap: var(--p6-space-2xs); min-width: 0; padding: var(--p6-space-md); border: var(--rule-thin) solid var(--p6-rule-strong); background: var(--p6-surface); }
      .review-field__label { font-weight: 800; }
      .review-field__help { min-height: 3lh; color: var(--p6-muted); font-size: var(--text-sm); }
      select { width: 100%; min-height: var(--p6-control-height); padding-inline: var(--p6-space-xs); border: var(--rule-thin) solid var(--p6-rule-strong); border-radius: var(--p6-radius); background: var(--p6-surface); color: var(--p6-ink); cursor: pointer; }
      select:hover { border-color: var(--p6-accent); }
      select:active { background: var(--p6-surface-2); }
      select:disabled { opacity: .55; cursor: not-allowed; }
      select[data-state="loading"] { cursor: progress; }
      select[data-state="error"] { border-color: var(--p6-error); background: var(--p6-error-soft); }
      select[data-state="success"] { border-color: var(--p6-success); background: var(--p6-success-soft); }
      .review-field__state { min-height: 1lh; color: var(--p6-muted); font-size: var(--text-xs); }
      .final-decision { max-width: 36rem; margin-top: var(--p6-space-lg); }
      .inline-footer { display: flex; flex-wrap: wrap; justify-content: space-between; gap: var(--p6-space-xs); padding: var(--p6-space-md) var(--p6-space-sm); border-top: var(--rule-thin) solid var(--p6-rule); color: var(--p6-muted); font-family: var(--p6-font-mono); font-size: var(--text-xs); }
      .toast { position: fixed; inset: auto var(--p6-space-sm) var(--p6-space-sm) auto; z-index: 500; max-width: min(24rem, calc(100vw - 2rem)); padding: var(--p6-space-sm); border: var(--rule-thin) solid var(--p6-success); background: var(--p6-success-soft); color: var(--p6-ink); opacity: 0; pointer-events: none; transform: translateY(var(--p6-space-sm)); transition: opacity var(--p6-dur-short) var(--p6-ease-out), transform var(--p6-dur-short) var(--p6-ease-out); }
      .toast[data-visible="true"] { opacity: 1; transform: translateY(0); }
      @media (min-width: 40rem) {
        .topline, .intro, .anchor-band, .case-hero, .human-review, .inline-footer { padding-inline: var(--p6-space-xl); }
        .anchor-band__grid { grid-template-columns: repeat(4, minmax(0, 1fr)); }
        .stage { grid-template-columns: minmax(3.5rem, .32fr) minmax(0, 2fr); }
        .stage__number { padding-bottom: var(--p6-space-xl); border-right: var(--rule-thin) solid var(--p6-rule); }
        .metric-line { grid-template-columns: repeat(2, minmax(0, 1fr)); }
        .decision-grid, .truth-grid, .review-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); }
        .visual-grid { grid-template-columns: minmax(0, 1.08fr) minmax(0, .7fr); }
        .visual-grid__full { grid-column: 1 / -1; }
      }
      @media (min-width: 64rem) {
        .anchor-band__grid { grid-template-columns: repeat(8, minmax(0, 1fr)); }
        .metric-line { grid-template-columns: repeat(4, minmax(0, 1fr)); }
        .decision-grid { grid-template-columns: repeat(3, minmax(0, 1fr)); }
        .visual-grid { grid-template-columns: minmax(0, 1fr) minmax(0, .65fr) minmax(0, 1.15fr); }
        .visual-grid__full { grid-column: auto; }
        .review-grid { grid-template-columns: repeat(3, minmax(0, 1fr)); }
      }
      @media (prefers-reduced-motion: reduce) { *, *::before, *::after { scroll-behavior: auto !important; transition-duration: 0.01ms !important; } }
    </style>
  </head>
  <body>
    <nav class="topline" aria-label="Phase 6 Review">
      <span class="wordmark">SwitchBot · Phase 6</span>
      <button class="export" id="export-review" type="button">Export CSV</button>
    </nav>
    <main>
      <section class="intro">
        <p class="intro__meta">Production Integration · One-shot End-to-End</p>
        <h1>Small input. Full chain. Honest gates.</h1>
        <p class="intro__lede">两条输入没有指定 Template、Module、Length 或 Hero。系统自动读取 Product Knowledge 与 Production Truth，完成决策、日语文案、素材解析、渲染和 QA。</p>
        <p class="intro__gate">当前两案技术渲染均 PASS，但外部事实与审批门仍开放，因此真实状态是 INTERNAL_DRAFT，不允许发送。</p>
      </section>
      <section class="anchor-band" aria-labelledby="anchor-title">
        <header><p>Brand Baseline</p><h2 id="anchor-title">Tier A Approved EDM 仍是最高视觉权重</h2><span>外部 EDM 不与 SwitchBot Approved 样本同权，也不会反向覆盖品牌习惯。</span></header>
        <div class="anchor-band__grid">#{anchors}</div>
      </section>
      #{case_sections}
    </main>
    <footer class="inline-footer"><span>EDM Visual Generator · Phase 6</span><span>Standard / Design System remain frozen · Generated 2026-08-19</span></footer>
    <div class="toast" id="toast" role="status" aria-live="polite">Human Review CSV 已导出。</div>
    <script>
      (() => {
        const fields = [...document.querySelectorAll('[data-review-field]')];
        const storageKey = 'edm-phase6-human-review-v1';
        const saved = JSON.parse(localStorage.getItem(storageKey) || '{}');
        fields.forEach((field) => {
          const caseId = field.closest('[data-case-id]').dataset.caseId;
          const key = `${caseId}::${field.dataset.reviewField}`;
          if (saved[key]) field.value = saved[key];
          field.addEventListener('change', () => {
            saved[key] = field.value;
            field.dataset.state = field.value ? 'success' : '';
            field.nextElementSibling.textContent = field.value ? 'Saved locally' : '';
            localStorage.setItem(storageKey, JSON.stringify(saved));
          });
        });
        const button = document.getElementById('export-review');
        button.addEventListener('click', () => {
          button.dataset.state = 'loading';
          const headers = ['case_id', #{QUESTIONS.map { |row| "'#{row[0]}'" }.join(", ")}, 'final_decision'];
          const rows = [...document.querySelectorAll('[data-case-id]')].map((section) => {
            const values = [...section.querySelectorAll('[data-review-field]')].map((field) => field.value);
            return [section.dataset.caseId, ...values];
          });
          const csv = [headers, ...rows].map((row) => row.map((cell) => `"${String(cell).replaceAll('"', '""')}"`).join(',')).join('\\n');
          const blob = new Blob(['\\ufeff', csv], { type: 'text/csv;charset=utf-8' });
          const link = document.createElement('a');
          link.href = URL.createObjectURL(blob);
          link.download = 'phase6_human_review.csv';
          link.click();
          URL.revokeObjectURL(link.href);
          button.dataset.state = 'success';
          const toast = document.getElementById('toast');
          toast.dataset.visible = 'true';
          window.setTimeout(() => { button.dataset.state = ''; toast.dataset.visible = 'false'; }, 1800);
        });
      })();
    </script>
  </body>
  </html>
HTML

File.write(File.join(ROOT, "research", "end_to_end_review.html"), html)

CASES.each do |case_id|
  manifest = manifests.fetch(case_id)
  browser = browser_qa.fetch(case_id)
  product_name = value(manifest.dig("product", "product", "official_name_ja"))
  decisions = manifest.fetch("decision")
  case_review = <<~HTML
    <!doctype html><html lang="zh-CN" data-theme="phase6-cobalt"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>#{h(case_id)} Design Review</title><link rel="stylesheet" href="../../tokens.css"><style>
    /* Hallmark · genre: modern-minimal · macrostructure: Narrative Workflow · theme: Cobalt · tone: technical-utilitarian · nav: N9 · footer: Ft2 */
    *{box-sizing:border-box}body{margin:0;padding:var(--p6-space-xl);font-family:var(--p6-font-body);background:var(--p6-paper);color:var(--p6-ink)}main{max-width:80rem;margin:auto}h1,h2{font-family:var(--p6-font-display);line-height:1.08;overflow-wrap:anywhere}h1{font-size:clamp(2rem,7vw,5rem);max-width:17ch}.meta{display:grid;grid-template-columns:repeat(auto-fit,minmax(12rem,1fr));gap:var(--p6-space-xs);margin-block:var(--p6-space-xl)}.meta div{padding:var(--p6-space-sm);border:1px solid var(--p6-rule);background:var(--p6-surface)}.meta span{display:block;color:var(--p6-muted);font-size:var(--text-sm)}.gallery{display:grid;grid-template-columns:minmax(0,1fr);gap:var(--p6-space-sm)}figure{margin:0;border:1px solid var(--p6-rule);background:var(--p6-surface)}img{display:block;width:100%;height:auto}figcaption{padding:var(--p6-space-xs);color:var(--p6-muted)}.full{max-height:52rem;overflow:auto}a{color:var(--p6-accent);white-space:nowrap}@media(min-width:48rem){.gallery{grid-template-columns:minmax(0,1fr) minmax(0,.65fr)}.gallery figure:last-child{grid-column:1/-1}}
    </style></head><body><main><p>#{h(case_id)} · #{badge(manifest.dig("qa", "production_status"), "open")}</p><h1>#{h(product_name)}</h1><div class="meta"><div><span>Template</span><strong>#{h(decisions.fetch("selected_template"))}</strong></div><div><span>Length</span><strong>#{h(decisions.dig("length", "length_class"))} · #{h(browser.dig("desktop", "totalLengthPx"))}px</strong></div><div><span>Modules</span><strong>#{h(manifest.fetch("modules").length)}</strong></div><div><span>Browser QA</span><strong>#{h(browser.fetch("status"))}</strong></div></div><div class="gallery"><figure><figcaption>Desktop</figcaption><img src="desktop_preview.png" alt="Desktop preview" width="600" height="900"></figure><figure><figcaption>Mobile</figcaption><img src="mobile_preview.png" alt="Mobile preview" width="390" height="844"></figure><figure><figcaption>Full EDM</figcaption><div class="full"><img src="full_edm.png" alt="Full EDM" width="600" height="#{h(browser.dig("desktop", "totalLengthPx"))}"></div></figure></div><p><a href="../../research/end_to_end_review.html##{h(case_id)}">Open combined human review</a></p></main></body></html>
  HTML
  File.write(File.join(ROOT, "production_output", case_id, "design_review.html"), case_review)
end

puts "Built research/end_to_end_review.html and #{CASES.length} case design review pages."
