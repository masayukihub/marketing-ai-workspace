# frozen_string_literal: true

require_relative "pipeline"

module EDMGenerator
  class ReviewPageBuilder
    def initialize(root)
      @root = File.expand_path(root)
      @pipeline = Pipeline.new(root)
    end

    def build
      test_document = YAML.safe_load(
        File.read(File.join(@root, "tests/generator_test_cases.yaml")),
        permitted_classes: [Date, Time],
        aliases: true
      )
      scorecard = YAML.safe_load(
        File.read(File.join(@root, "generator/outputs/scorecard.yaml")),
        permitted_classes: [Date, Time],
        aliases: true
      )
      generated_at = scorecard.fetch("generated_at").to_s
      human_reviews = load_human_reviews
      results = test_document.fetch("test_cases").map do |test_case|
        result = @pipeline.run(test_case, generated_at: generated_at)
        result["automated_case_status"] = result.dig("qa", "automated_test_status")
        result["human_review"] = human_reviews[test_case.fetch("test_case_id")] || {
          "template_correct" => "",
          "message_correct" => "",
          "module_correct" => "",
          "copy_usable" => "",
          "asset_plan_correct" => "",
          "overall_decision" => "",
          "human_reason" => ""
        }
        result
      end
      data = {
        "generated_at" => generated_at,
        "scorecard" => scorecard,
        "results" => results
      }
      output = File.join(@root, "research/generator_test_review.html")
      Helpers.write_text(output, html(data))
      puts output
    end

    private

    def load_human_reviews
      path = File.join(@root, "research/generator_human_review.csv")
      return {} unless File.exist?(path)

      CSV.read(path, headers: true, encoding: "bom|utf-8").each_with_object({}) do |row, reviews|
        reviews[row.fetch("test_case_id")] = {
          "template_correct" => row["template_correct"].to_s,
          "message_correct" => row["message_correct"].to_s,
          "module_correct" => row["module_correct"].to_s,
          "copy_usable" => row["copy_usable"].to_s,
          "asset_plan_correct" => row["asset_plan_correct"].to_s,
          "overall_decision" => row["overall_decision"].to_s,
          "human_reason" => row["human_reason"].to_s
        }
      end
    end

    def html(data)
      json = JSON.generate(data).gsub("<", "\\u003c")
      <<~HTML
        <!doctype html>
        <html lang="zh-CN" data-theme="phase4-coral">
        <head>
          <meta charset="utf-8">
          <meta name="viewport" content="width=device-width, initial-scale=1">
          <title>Phase 4 · Generator Test Review</title>
          <style>
            @import url("../tokens.css");
            /* Hallmark · macrostructure: Stat-Led · genre: modern-minimal · tone: technical-utilitarian · anchor hue: coral · nav: N5 floating pill · footer: Ft5 statement · enrichment: none · contrast: pass (40–41) · slop: pass (42–45) · honest: pass (46) · chrome: pass (47) · tokens: pass (48) · responsive: pass (49) · icons: pass (30) · mobile: pass (34, 49, 50–57) */
            /* Hallmark · pre-emit critique: P5 H5 E4 S5 R5 V5 */
            * { box-sizing: border-box; }
            html, body { margin: 0; overflow-x: clip; }
            html { background: var(--p4-paper); color: var(--p4-ink); font-family: var(--p4-font-body); line-height: 1.55; }
            body { min-width: 20rem; background: var(--p4-paper); }
            button, select, textarea { font: inherit; }
            button, select { min-height: var(--p4-control-height); }
            button, select, textarea {
              border: var(--rule-thin) solid var(--p4-rule-strong);
              border-radius: var(--p4-radius);
              outline: var(--rule-strong) solid transparent;
              outline-offset: var(--rule-thin);
              color: var(--p4-ink);
              background: var(--p4-surface);
              transition: background-color var(--dur-fast) var(--ease-standard), border-color var(--dur-fast) var(--ease-standard), color var(--dur-fast) var(--ease-standard);
            }
            button { padding-inline: var(--space-4); cursor: pointer; white-space: nowrap; font-weight: 700; }
            button:hover, select:hover, textarea:hover { border-color: var(--p4-ink); }
            button:active { background: var(--p4-paper-2); }
            select:active, textarea:active { border-color: var(--p4-accent); background: var(--p4-paper-2); }
            button:focus-visible, select:focus-visible, textarea:focus-visible, summary:focus-visible {
              outline-color: var(--p4-focus);
              outline-offset: var(--rule-thin);
            }
            button:disabled, select:disabled, textarea:disabled { opacity: 0.55; cursor: not-allowed; background: var(--p4-paper-2); }
            textarea { width: 100%; min-height: 7rem; resize: vertical; padding: var(--space-3); }
            a { color: var(--p4-ink); text-decoration-thickness: var(--rule-thin); text-underline-offset: var(--space-1); }
            a:hover { color: var(--p4-accent-hover); }
            a:active { color: var(--p4-accent); }
            a:focus-visible { outline: var(--rule-strong) solid var(--p4-focus); outline-offset: var(--rule-thin); }
            code, pre, .mono { font-family: var(--p4-font-mono); }
            pre { margin: 0; max-width: 100%; overflow: auto; white-space: pre-wrap; overflow-wrap: anywhere; font-size: var(--text-xs); color: var(--p4-ink-2); }
            h1, h2, h3 { margin: 0; font-family: var(--p4-font-display); font-style: normal; overflow-wrap: anywhere; min-width: 0; }
            p { max-width: var(--p4-copy-measure); }
            .shell { width: min(100% - var(--space-6), var(--p4-page-max)); margin-inline: auto; }
            .floating-nav {
              position: sticky;
              top: var(--p4-nav-offset);
              z-index: var(--p4-z-nav);
              display: flex;
              align-items: center;
              justify-content: center;
              gap: var(--space-2);
              width: fit-content;
              max-width: calc(100% - var(--space-4));
              margin: var(--space-3) auto 0;
              padding: var(--space-2);
              border: var(--rule-thin) solid var(--p4-rule-strong);
              border-radius: var(--p4-radius-pill);
              background: var(--p4-surface);
              box-shadow: 0 var(--space-2) var(--space-5) var(--p4-shadow);
            }
            .floating-nav__title { padding-inline: var(--space-3); font-size: var(--text-sm); font-weight: 800; white-space: nowrap; line-height: 1; }
            .floating-nav select { max-width: 12rem; padding-inline: var(--space-3); }
            .button--accent { border-color: var(--p4-accent); color: var(--p4-accent-ink); background: var(--p4-accent); }
            .button--accent:hover { border-color: var(--p4-accent-hover); background: var(--p4-accent-hover); }
            .button--accent:active { background: var(--p4-ink); }
            .hero {
              display: grid;
              grid-template-columns: minmax(0, 1.25fr) minmax(0, 0.75fr);
              gap: var(--space-7);
              align-items: end;
              padding-block: var(--space-7) var(--space-9);
              border-bottom: var(--rule-strong) solid var(--p4-ink);
            }
            .hero__kicker { margin: 0 0 var(--space-4); font-family: var(--p4-font-mono); font-size: var(--text-xs); letter-spacing: 0.08em; text-transform: uppercase; }
            .hero h1 { max-width: 14ch; font-size: clamp(2.4rem, 7vw, 6rem); line-height: 0.98; letter-spacing: -0.055em; }
            .hero__lede { margin: var(--space-5) 0 0; color: var(--p4-ink-2); font-size: var(--text-md); }
            .hero__status { align-self: end; padding-left: var(--space-5); border-left: var(--rule-strong) solid var(--p4-accent); }
            .hero__status strong { display: block; font-family: var(--p4-font-display); font-size: var(--text-xl); line-height: 1.05; }
            .hero__status p { margin: var(--space-3) 0 0; color: var(--p4-muted); }
            .stats {
              display: grid;
              grid-template-columns: repeat(4, minmax(0, 1fr));
              border-bottom: var(--rule-strong) solid var(--p4-ink);
            }
            .stat { min-width: 0; padding: var(--space-5); border-right: var(--rule-thin) solid var(--p4-rule); }
            .stat:last-child { border-right: 0; }
            .stat__value { display: block; font-family: var(--p4-font-display); font-size: clamp(2rem, 4vw, 3.5rem); font-weight: 800; line-height: 1; }
            .stat__label { display: block; margin-top: var(--space-2); color: var(--p4-muted); font-size: var(--text-sm); }
            .gate-note { padding-block: var(--space-6); border-bottom: var(--rule-thin) solid var(--p4-rule-strong); }
            .gate-note h2 { font-size: var(--text-lg); }
            .gate-note p { margin: var(--space-2) 0 0; color: var(--p4-muted); }
            .gate-line { display: flex; align-items: center; gap: var(--space-3); margin-top: var(--space-4); flex-wrap: wrap; }
            .chip { display: inline-flex; align-items: center; min-height: 1.75rem; padding-inline: var(--space-3); border: var(--rule-thin) solid var(--p4-rule-strong); border-radius: var(--p4-radius-pill); font-size: var(--text-xs); font-weight: 750; white-space: nowrap; line-height: 1; }
            .chip--pass { color: var(--p4-success); background: var(--p4-success-soft); }
            .chip--wait { color: var(--p4-warning); background: var(--p4-warning-soft); }
            .chip--block { color: var(--p4-error); background: var(--p4-error-soft); }
            .section-head { display: flex; flex-direction: column; gap: var(--space-2); padding-block: var(--space-7) var(--space-5); }
            .section-head h2 { font-size: var(--text-xl); }
            .section-head p { margin: 0; color: var(--p4-muted); }
            .case-list { border-top: var(--rule-strong) solid var(--p4-ink); }
            .case { border-bottom: var(--rule-strong) solid var(--p4-ink); background: var(--p4-surface); }
            .case[hidden] { display: none; }
            .case summary {
              display: grid;
              grid-template-columns: minmax(0, 1fr) auto;
              gap: var(--space-5);
              align-items: center;
              padding: var(--space-5);
              cursor: pointer;
              list-style: none;
              outline: var(--rule-strong) solid transparent;
              outline-offset: calc(var(--rule-thin) * -1);
            }
            .case summary::-webkit-details-marker { display: none; }
            .case summary:hover { background: var(--p4-paper-2); }
            .case summary:active { background: var(--p4-accent-soft); }
            .case__id { font-family: var(--p4-font-mono); color: var(--p4-muted); font-size: var(--text-xs); }
            .case__title { margin-top: var(--space-1); font-size: var(--text-lg); }
            .case__meta { display: flex; align-items: center; justify-content: flex-end; gap: var(--space-2); flex-wrap: wrap; }
            .case__body { padding: 0 var(--space-5) var(--space-7); }
            .evidence-grid { display: grid; grid-template-columns: minmax(0, 1fr) minmax(0, 1fr); gap: var(--space-6); }
            .evidence { min-width: 0; padding-block: var(--space-5); border-top: var(--rule-thin) solid var(--p4-rule); }
            .evidence--wide { grid-column: 1 / -1; }
            .evidence h3 { font-size: var(--text-md); }
            .evidence p { margin: var(--space-2) 0 0; color: var(--p4-ink-2); }
            .evidence dl { display: grid; grid-template-columns: minmax(8rem, 0.38fr) minmax(0, 1fr); gap: var(--space-2) var(--space-4); margin: var(--space-4) 0 0; }
            .evidence dt { color: var(--p4-muted); font-size: var(--text-sm); }
            .evidence dd { margin: 0; min-width: 0; overflow-wrap: anywhere; }
            .sequence { display: flex; align-items: center; gap: var(--space-2); flex-wrap: wrap; margin-top: var(--space-4); }
            .sequence span { font-family: var(--p4-font-mono); font-size: var(--text-xs); }
            .copy-list { display: grid; gap: var(--space-4); margin-top: var(--space-4); }
            .copy-row { padding-top: var(--space-3); border-top: var(--rule-thin) solid var(--p4-rule); }
            .copy-row strong { display: block; font-size: var(--text-sm); }
            .copy-row p { margin: var(--space-1) 0 0; }
            .score-table { width: 100%; margin-top: var(--space-4); border-collapse: collapse; }
            .score-table th, .score-table td { padding: var(--space-2); border-bottom: var(--rule-thin) solid var(--p4-rule); text-align: left; }
            .score-table th { color: var(--p4-muted); font-size: var(--text-xs); font-weight: 600; }
            .score-table td:last-child { text-align: right; font-family: var(--p4-font-mono); }
            .review {
              margin-top: var(--space-6);
              padding-top: var(--space-6);
              border-top: var(--rule-strong) solid var(--p4-accent);
            }
            .review__head { display: flex; align-items: center; justify-content: space-between; gap: var(--space-4); }
            .review__head h3 { font-size: var(--text-lg); }
            .review__grid { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: var(--space-4); margin-top: var(--space-5); }
            .field { display: flex; flex-direction: column; gap: var(--space-2); min-width: 0; }
            .field--wide { grid-column: 1 / -1; }
            .field label { font-size: var(--text-sm); font-weight: 750; }
            .field select { width: 100%; padding-inline: var(--space-3); }
            .helper { min-height: 1lh; margin: 0; color: var(--p4-muted); font-size: var(--text-xs); }
            .empty-state { display: none; padding: var(--space-7); border-block: var(--rule-strong) solid var(--p4-ink); }
            .empty-state.is-visible { display: block; }
            .footer { padding-block: var(--space-9) var(--space-7); }
            .footer__statement { max-width: 18ch; font-family: var(--p4-font-display); font-size: clamp(2rem, 5vw, 4.5rem); font-weight: 800; line-height: 1.02; letter-spacing: -0.04em; }
            .footer__meta { display: flex; align-items: center; justify-content: space-between; gap: var(--space-5); margin-top: var(--space-7); padding-top: var(--space-4); border-top: var(--rule-thin) solid var(--p4-rule-strong); color: var(--p4-muted); font-size: var(--text-sm); }
            @media (max-width: 48rem) {
              .shell { width: min(100% - var(--space-4), var(--p4-page-max)); }
              .floating-nav { width: calc(100% - var(--space-4)); flex-wrap: wrap; border-radius: var(--p4-radius); }
              .floating-nav__title { flex: 1 1 auto; }
              .floating-nav select { flex: 1 1 10rem; max-width: none; min-width: 0; }
              .hero { grid-template-columns: minmax(0, 1fr); gap: var(--space-6); padding-block: var(--space-6) var(--space-8); }
              .hero h1 { max-width: 12ch; font-size: clamp(2.35rem, 14vw, 4.6rem); line-height: 1.02; }
              .hero__status { padding-left: 0; padding-top: var(--space-4); border-left: 0; border-top: var(--rule-strong) solid var(--p4-accent); }
              .stats { grid-template-columns: repeat(2, minmax(0, 1fr)); }
              .stat:nth-child(2) { border-right: 0; }
              .stat:nth-child(-n + 2) { border-bottom: var(--rule-thin) solid var(--p4-rule); }
              .case summary { grid-template-columns: minmax(0, 1fr); gap: var(--space-3); }
              .case__meta { justify-content: flex-start; }
              .evidence-grid, .review__grid { grid-template-columns: minmax(0, 1fr); }
              .evidence--wide, .field--wide { grid-column: auto; }
              .evidence dl { grid-template-columns: minmax(0, 1fr); }
              .evidence dd { padding-bottom: var(--space-2); }
              .footer__meta { flex-direction: column; align-items: flex-start; }
            }
            @media (max-width: 25.875rem) {
              .floating-nav__title { display: none; }
              .floating-nav select { flex-basis: 100%; }
              .case__body, .case summary { padding-inline: var(--space-4); }
              .stats { grid-template-columns: minmax(0, 1fr); }
              .stat, .stat:nth-child(2) { border-right: 0; border-bottom: var(--rule-thin) solid var(--p4-rule); }
              .stat:last-child { border-bottom: 0; }
            }
            @media (prefers-reduced-motion: reduce) {
              *, *::before, *::after { scroll-behavior: auto !important; transition-duration: 0.01ms !important; animation-duration: 0.01ms !important; animation-iteration-count: 1 !important; }
            }
          </style>
        </head>
        <body>
          <nav class="floating-nav" aria-label="Review controls">
            <span class="floating-nav__title">Phase 4 / <span id="reviewProgress">0 / 17</span></span>
            <select id="caseFilter" aria-label="筛选测试案例">
              <option value="all">全部案例</option>
              <option value="negative">负向路径</option>
              <option value="awaiting">待审核</option>
              <option value="reviewed">已审核</option>
            </select>
            <button type="button" id="expandAll">展开全部</button>
            <button type="button" class="button--accent" id="exportCsv">CSV 导出</button>
          </nav>

          <main class="shell">
            <header class="hero">
              <div>
                <p class="hero__kicker">EDM Visual Generator · Phase 4</p>
                <h1>Generator Test Review</h1>
                <p class="hero__lede">审核 17 个确定性 Design Spec：Template、Message、Module、日语草稿、素材计划与 QA。此页不生成 Renderer 或正式 EDM。</p>
              </div>
              <div class="hero__status">
                <strong>Human Validation 已完成，Renderer Gate = PASS。</strong>
                <p>自动测试通过不等于可外发。Product Knowledge、Approved Claim、真实素材与链接仍是 Production Gate。</p>
              </div>
            </header>

            <section class="stats" aria-label="Automated test summary">
              <div class="stat"><span class="stat__value" id="statExecuted">17/17</span><span class="stat__label">案例已执行</span></div>
              <div class="stat"><span class="stat__value" id="statAccuracy">100%</span><span class="stat__label">Template 命中率</span></div>
              <div class="stat"><span class="stat__value" id="statHard">0</span><span class="stat__label">Unsafe Hard Violations</span></div>
              <div class="stat"><span class="stat__value" id="statOverall">4.34</span><span class="stat__label">平均自动评分 / 5</span></div>
            </section>

            <section class="gate-note">
              <h2>Renderer Gate</h2>
              <p>Human `Pass + Needs Modification = 100.0%`，Phase 5 Renderer Gate 已通过。该结论只授权进入 Renderer 开发，不代表各 Test Fixture 已达到 Production Ready。</p>
              <div class="gate-line" id="gateLine"></div>
            </section>

            <section>
              <div class="section-head">
                <h2>17 个 Generator Test Cases</h2>
                <p>页面已预载正式 Human-assisted Review；仍可在本机调整并重新导出 CSV。项目正式记录位于 `research/generator_human_review.csv`。</p>
              </div>
              <div class="case-list" id="caseList"></div>
              <div class="empty-state" id="emptyState">当前筛选没有案例。</div>
            </section>
          </main>

          <footer class="footer shell">
            <div class="footer__statement">Phase 4 已关闭；Generator Logic v1.0 已冻结，Renderer 尚未实现。</div>
            <div class="footer__meta">
              <span>EDM Standard → Design System → Generator Logic → Human Gate</span>
              <a href="../generator/outputs/scorecard.yaml">查看机器评分清单</a>
            </div>
          </footer>

          <script>
            const DATA = #{json};
            const STORAGE_KEY = "switchbot-edm-generator-phase4-review-v1";
            const REVIEW_FIELDS = ["template_correct", "message_correct", "module_correct", "copy_usable", "asset_plan_correct", "overall_decision", "human_reason"];
            const state = loadState();
            DATA.results.forEach(result => {
              const seeded = result.human_review || {};
              const saved = state[result.test_case_id] || {};
              state[result.test_case_id] = Object.fromEntries(REVIEW_FIELDS.map(field => [
                field,
                saved[field] || seeded[field] || ""
              ]));
            });

            function esc(value) {
              return String(value ?? "").replace(/[&<>\"']/g, char => {
                if (char === "&") return "&amp;";
                if (char === "<") return "&lt;";
                if (char === ">") return "&gt;";
                if (char === '\"') return "&quot;";
                return "&#39;";
              });
            }
            function pretty(value) { return esc(JSON.stringify(value, null, 2)); }
            function options(current, type = "standard") {
              const values = type === "overall" ? ["", "Pass", "Needs Modification", "Fail"] : ["", "Yes", "Needs Modification", "No"];
              return values.map(value => `<option value="${esc(value)}" ${value === current ? "selected" : ""}>${value || "— 请选择 —"}</option>`).join("");
            }
            function loadState() {
              try { return JSON.parse(localStorage.getItem(STORAGE_KEY) || "{}"); }
              catch (_) { return {}; }
            }
            function saveState() {
              localStorage.setItem(STORAGE_KEY, JSON.stringify(state));
              updateProgress();
            }
            function reviewFor(id) {
              if (!state[id]) state[id] = Object.fromEntries(REVIEW_FIELDS.map(field => [field, ""]));
              return state[id];
            }
            function statusChip(label, type) { return `<span class="chip chip--${type}">${esc(label)}</span>`; }
            function inputSummary(result) {
              const product = result.input.product || {};
              const names = product.display_names_en || (product.brand ? [product.brand] : []);
              return names.length ? names.join(" / ") : "Brand scope";
            }
            function renderCase(result) {
              const id = result.test_case_id;
              const review = reviewFor(id);
              const negative = ["GTC-016", "GTC-017"].includes(id);
              const modules = result.composition.module_sequence || [];
              const moduleCopy = result.copy.module_copy || [];
              const blocking = result.qa.blocking_conditions || [];
              const scores = Object.entries(result.scores).filter(([key]) => !["overall", "scale"].includes(key));
              const reviewed = Boolean(review.overall_decision);
              return `
                <details class="case" data-id="${esc(id)}" data-negative="${negative}" data-reviewed="${reviewed}">
                  <summary>
                    <div>
                      <div class="case__id">${esc(id)} · ${esc(result.classification.campaign_family)}</div>
                      <h3 class="case__title">${esc(result.name)}</h3>
                    </div>
                    <div class="case__meta">
                      ${statusChip(result.qa.automated_test_status, "pass")}
                      ${result.selection.selected_template_id ? statusChip(result.selection.selected_template_id, "wait") : statusChip("SELECTION BLOCKED", "block")}
                      ${reviewed ? statusChip(review.overall_decision, review.overall_decision === "Pass" ? "pass" : "wait") : statusChip("Awaiting Human", "wait")}
                    </div>
                  </summary>
                  <div class="case__body">
                    <div class="evidence-grid">
                      <section class="evidence">
                        <h3>Input</h3>
                        <dl>
                          <dt>Product</dt><dd>${esc(inputSummary(result))}</dd>
                          <dt>Theme</dt><dd>${esc(result.input.campaign_theme || "Unknown")}</dd>
                          <dt>Objective</dt><dd><code>${esc(result.input.objective || "Unknown")}</code></dd>
                          <dt>Promotion</dt><dd><code>${esc(result.brief.campaign.promotion.level)} / ${esc(result.brief.campaign.promotion.status)}</code></dd>
                          <dt>CTA</dt><dd><code>${esc(result.brief.campaign.cta_destination.status)}</code></dd>
                        </dl>
                      </section>
                      <section class="evidence">
                        <h3>Compiled Brief</h3>
                        <dl>
                          <dt>Status</dt><dd><code>${esc(result.brief.status)}</code></dd>
                          <dt>Audience</dt><dd>${esc(result.brief.campaign.audience)} · ${esc(result.brief.campaign.audience_status)}</dd>
                          <dt>PK Snapshot</dt><dd><code>${esc(result.brief.verification.product_knowledge_snapshot)}</code></dd>
                          <dt>External Ready</dt><dd><code>${esc(result.brief.verification.external_publication_ready)}</code></dd>
                        </dl>
                      </section>
                      <section class="evidence">
                        <h3>Campaign + Template Decision</h3>
                        <dl>
                          <dt>Family</dt><dd><code>${esc(result.classification.campaign_family)}</code> · ${esc(result.classification.confidence)}</dd>
                          <dt>Selected</dt><dd><code>${esc(result.selection.selected_template_id || "BLOCKED")}</code></dd>
                          <dt>Alternative</dt><dd><code>${esc(result.selection.alternative_template_id || "None")}</code></dd>
                          <dt>Why</dt><dd>${esc(result.selection.why_selected || result.selection.selection_reasons.join(" / "))}</dd>
                        </dl>
                      </section>
                      <section class="evidence">
                        <h3>Message Hierarchy</h3>
                        <dl>
                          <dt>Primary</dt><dd>${esc(result.message.primary_message)}</dd>
                          <dt>USP</dt><dd><code>${esc(result.message.primary_usp.status || "Unknown")}</code></dd>
                          <dt>CTA Intent</dt><dd>${esc(result.message.cta.intent)}</dd>
                          <dt>Promotion</dt><dd>${esc(result.message.promotion.expression)}</dd>
                        </dl>
                      </section>
                      <section class="evidence evidence--wide">
                        <h3>Module Sequence</h3>
                        <div class="sequence">${modules.length ? modules.map(item => `<span class="chip">${esc(item.position)} · ${esc(item.module_id)}</span>`).join("") : statusChip("No sequence — upstream blocked", "block")}</div>
                      </section>
                      <section class="evidence evidence--wide">
                        <h3>Japanese Copy Draft</h3>
                        <dl>
                          <dt>Subject</dt><dd>${esc(result.copy.subject.text)} <code>${esc(result.copy.subject.status)}</code></dd>
                          <dt>H1</dt><dd>${esc(result.copy.h1.text)} <code>${esc(result.copy.h1.length)} chars</code></dd>
                          <dt>CTA</dt><dd>${esc(result.copy.cta.text)} <code>${esc(result.copy.cta.status)}</code></dd>
                        </dl>
                        <div class="copy-list">${moduleCopy.map(item => `<div class="copy-row"><strong>${esc(item.module_id)} · ${esc(item.status)}</strong><p>${esc(item.headline)}</p><p>${esc(item.body)}</p></div>`).join("") || "<p>No module copy.</p>"}</div>
                      </section>
                      <section class="evidence">
                        <h3>Asset Plan</h3>
                        <dl>
                          <dt>Status</dt><dd><code>${esc(result.assets.status)}</code></dd>
                          <dt>Inventory</dt><dd><code>${esc(result.assets.asset_inventory_state)}</code></dd>
                          <dt>Missing</dt><dd>${esc(result.assets.missing_required_assets.join(" / ") || "None")}</dd>
                          <dt>AI boundary</dt><dd>${esc(result.assets.ai_forbidden.join(" / "))}</dd>
                        </dl>
                      </section>
                      <section class="evidence">
                        <h3>QA + Auto Score</h3>
                        <dl>
                          <dt>Design Spec</dt><dd><code>${esc(result.qa.status)}</code></dd>
                          <dt>Production</dt><dd><code>${esc(result.qa.production_status)}</code></dd>
                          <dt>Blocking</dt><dd>${blocking.map(code => `<code>${esc(code)}</code>`).join(" · ")}</dd>
                          <dt>Unsafe Hard</dt><dd><code>${esc(result.qa.unsafe_generator_violations.length)}</code></dd>
                        </dl>
                        <table class="score-table"><thead><tr><th>Dimension</th><th>1–5</th></tr></thead><tbody>${scores.map(([key, value]) => `<tr><td>${esc(key.replaceAll("_", " "))}</td><td>${esc(value)}</td></tr>`).join("")}<tr><th>Overall</th><td>${esc(result.scores.overall)}</td></tr></tbody></table>
                      </section>
                      <section class="evidence evidence--wide">
                        <h3>Full Input Evidence</h3>
                        <pre>${pretty(result.input)}</pre>
                      </section>
                    </div>

                    <section class="review" aria-labelledby="review-${esc(id)}">
                      <div class="review__head"><h3 id="review-${esc(id)}">Human Review</h3>${statusChip("Blank by default", "wait")}</div>
                      <div class="review__grid">
                        ${reviewField(id, "template_correct", "Template Correct", review.template_correct)}
                        ${reviewField(id, "message_correct", "Message Correct", review.message_correct)}
                        ${reviewField(id, "module_correct", "Module Correct", review.module_correct)}
                        ${reviewField(id, "copy_usable", "Copy Usable", review.copy_usable)}
                        ${reviewField(id, "asset_plan_correct", "Asset Plan Correct", review.asset_plan_correct)}
                        ${reviewField(id, "overall_decision", "Overall Decision", review.overall_decision, "overall")}
                        <div class="field field--wide"><label for="${esc(id)}-human_reason">Human Reason</label><textarea id="${esc(id)}-human_reason" data-field="human_reason" data-id="${esc(id)}" placeholder="请输入具体修改理由、保留点或失败原因">${esc(review.human_reason)}</textarea><p class="helper">不会自动填写；仅保存于当前浏览器并进入导出 CSV。</p></div>
                      </div>
                    </section>
                  </div>
                </details>`;
            }
            function reviewField(id, field, label, current, type = "standard") {
              return `<div class="field"><label for="${esc(id)}-${field}">${esc(label)}</label><select id="${esc(id)}-${field}" data-field="${field}" data-id="${esc(id)}">${options(current, type)}</select><p class="helper">${type === "overall" ? "仅允许 Pass / Needs Modification / Fail" : "判断是否符合预期；必要时选择 Needs Modification"}</p></div>`;
            }
            function render() {
              const score = DATA.scorecard;
              document.getElementById("statExecuted").textContent = `${score.execution.executed_cases}/${score.execution.defined_cases}`;
              document.getElementById("statAccuracy").textContent = `${score.execution.template_selection_accuracy}%`;
              document.getElementById("statHard").textContent = score.execution.unsafe_hard_rule_violations;
              document.getElementById("statOverall").textContent = score.average_scores.overall;
              const gate = score.renderer_gate;
              document.getElementById("gateLine").innerHTML = [
                statusChip(`17 cases · ${gate.automated_case_execution}`, gate.automated_case_execution === "PASS" ? "pass" : "block"),
                statusChip(`Template ≥85% · ${gate.template_selection_accuracy_min_85}`, gate.template_selection_accuracy_min_85 === "PASS" ? "pass" : "block"),
                statusChip(`Human ≥90% · ${gate.human_pass_plus_needs_modification_min_90}`, "wait"),
                statusChip(`Overall · ${gate.overall}`, "block")
              ].join("");
              document.getElementById("caseList").innerHTML = DATA.results.map(renderCase).join("");
              bindReviewInputs();
              applyFilter();
              updateProgress();
            }
            function bindReviewInputs() {
              document.querySelectorAll("[data-field]").forEach(input => {
                input.addEventListener("change", event => {
                  const {id, field} = event.target.dataset;
                  reviewFor(id)[field] = event.target.value;
                  saveState();
                  document.querySelector(`.case[data-id="${id}"]`).dataset.reviewed = Boolean(reviewFor(id).overall_decision);
                  applyFilter();
                });
                if (input.tagName === "TEXTAREA") input.addEventListener("input", event => {
                  const {id, field} = event.target.dataset;
                  reviewFor(id)[field] = event.target.value;
                  saveState();
                });
              });
            }
            function updateProgress() {
              const reviewed = DATA.results.filter(result => Boolean(reviewFor(result.test_case_id).overall_decision)).length;
              document.getElementById("reviewProgress").textContent = `${reviewed} / ${DATA.results.length}`;
            }
            function applyFilter() {
              const value = document.getElementById("caseFilter").value;
              let visible = 0;
              document.querySelectorAll(".case").forEach(node => {
                const show = value === "all" || (value === "negative" && node.dataset.negative === "true") || (value === "awaiting" && node.dataset.reviewed === "false") || (value === "reviewed" && node.dataset.reviewed === "true");
                node.hidden = !show;
                if (show) visible += 1;
              });
              document.getElementById("emptyState").classList.toggle("is-visible", visible === 0);
            }
            function exportCsv() {
              const headers = ["test_case_id", ...REVIEW_FIELDS];
              const rows = DATA.results.map(result => {
                const review = reviewFor(result.test_case_id);
                return [result.test_case_id, ...REVIEW_FIELDS.map(field => review[field] || "")];
              });
              const csv = [headers, ...rows].map(row => row.map(value => `"${String(value).replaceAll('"', '""')}"`).join(",")).join("\\r\\n");
              const blob = new Blob(["\ufeff", csv], {type: "text/csv;charset=utf-8"});
              const link = document.createElement("a");
              const downloadUrl = URL.createObjectURL(blob);
              link.href = downloadUrl;
              link.download = "generator_human_review.csv";
              document.body.appendChild(link);
              link.click();
              link.remove();
              window.setTimeout(() => URL.revokeObjectURL(downloadUrl), 1000);
            }
            document.getElementById("caseFilter").addEventListener("change", applyFilter);
            document.getElementById("expandAll").addEventListener("click", event => {
              const visible = [...document.querySelectorAll(".case:not([hidden])")];
              const shouldOpen = visible.some(item => !item.open);
              visible.forEach(item => { item.open = shouldOpen; });
              event.currentTarget.textContent = shouldOpen ? "收起全部" : "展开全部";
            });
            document.getElementById("exportCsv").addEventListener("click", exportCsv);
            render();
          </script>
        </body>
        </html>
      HTML
    end
  end
end

if $PROGRAM_NAME == __FILE__
  project_root = File.expand_path("..", __dir__)
  EDMGenerator::ReviewPageBuilder.new(project_root).build
end
