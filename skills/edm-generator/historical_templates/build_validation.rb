# frozen_string_literal: true

require "cgi"
require "csv"
require "json"
require "yaml"

ROOT = File.expand_path("..", __dir__)
library = YAML.safe_load(File.read(File.join(ROOT, "templates", "historical", "library_v1.0.yaml")))
summary = YAML.safe_load(File.read(File.join(ROOT, "output", "historical_template_tests", "summary.yaml")))
browser = JSON.parse(File.read(File.join(ROOT, "output", "historical_template_tests", "browser_qa.json")))
tests = YAML.safe_load(File.read(File.join(ROOT, "tests", "historical_template_test_cases.yaml"))).fetch("test_cases").to_h { |row| [row.fetch("case_id"), row] }
audit = CSV.read(File.join(ROOT, "research", "historical_template_audit.csv"), headers: true)
templates = library.fetch("templates").to_h { |row| [row.fetch("template_id"), row] }
qa_by_case = browser.fetch("results").to_h { |row| [row.fetch("caseId"), row] }

def h(value)
  CGI.escapeHTML(value.to_s)
end

def score_options
  '<option value="">未填写</option>' + (1..5).map { |score| "<option value=\"#{score}\">#{score}</option>" }.join
end

library_rows = library.fetch("templates").map do |template|
  "<tr><td>#{h(template.fetch("template_id"))}</td><td>#{h(template.fetch("reference_edm"))}</td><td>#{h(template.fetch("template_name"))}</td><td>#{h(template.fetch("campaign_types").join(" / "))}</td><td>#{h(template.fetch("best_for"))}</td></tr>"
end.join

case_sections = summary.fetch("results").map.with_index(1) do |result, index|
  case_id = result.fetch("case_id")
  test = tests.fetch(case_id)
  template = templates.fetch(result.fetch("selected_template_id"))
  qa = qa_by_case.fetch(case_id)
  match = YAML.safe_load(File.read(File.join(ROOT, "output", "historical_template_tests", case_id, "matcher_result.yaml")))
  top3 = match.fetch("top_matches").map do |row|
    "<tr><td>#{row.fetch("rank")}</td><td>#{h(row.fetch("template_id"))}</td><td>#{h(row.fetch("reference_edm"))}</td><td>#{row.fetch("template_fit_score")}</td><td>#{h(row.fetch("reuse_mode"))}</td><td>#{h(row.fetch("requires_adjustment").join(" → "))}</td></tr>"
  end.join
  status_class = result.fetch("reuse_mode") == "Direct Reuse" ? "status status--direct" : "status"
  truth_note = result.fetch("render_scope") == "skeleton_validation_only" ? "Promotion Truth 未确认；没有显示价格、折扣或期间，只审视觉骨架。" : "使用现有 Product Truth 与内部 Renderer Pilot 官方素材；仍不等于外部配信批准。"
  <<~HTML
    <article class="case" id="#{case_id}" data-review-case="#{case_id}" data-template-id="#{result.fetch("selected_template_id")}" data-reference-id="#{result.fetch("selected_reference_edm")}">
      <header class="case__head">
        <div>
          <span class="case__index">CASE #{format("%02d", index)} · #{case_id}</span>
          <h2>#{h(result.fetch("name"))}</h2>
          <p class="lede">Top-1 选择 #{h(result.fetch("selected_template_id"))}（#{h(result.fetch("selected_reference_edm"))}）。#{h(template.fetch("best_for"))}</p>
        </div>
        <dl class="case__facts">
          <div><dt>Fit Score</dt><dd>#{result.fetch("template_fit_score")}</dd></div>
          <div><dt>Route</dt><dd><span class="#{status_class}">#{h(result.fetch("reuse_mode"))}</span></dd></div>
          <div><dt>Structural Similarity</dt><dd>#{qa.fetch("structuralVisualSimilarity")}%</dd></div>
          <div><dt>Browser QA</dt><dd>#{qa.fetch("qaPass") ? "PASS" : "FAIL"}</dd></div>
        </dl>
      </header>
      <section class="matcher" aria-labelledby="#{case_id}-matcher">
        <h3 id="#{case_id}-matcher">Matcher Top 3</h3>
        <table class="top3-table"><thead><tr><th>Rank</th><th>Template</th><th>Reference</th><th>Score</th><th>Route</th><th>主要调整</th></tr></thead><tbody>#{top3}</tbody></table>
      </section>
      <div class="comparison">
        <figure class="visual-pane">
          <figcaption><strong>Original Historical Template</strong><a href="../templates/historical/#{result.fetch("selected_template_id")}/reference_full.png" target="_blank" rel="noreferrer">打开原图</a></figcaption>
          <div class="visual-scroll" data-visual-scroll="reference"><img src="../templates/historical/#{result.fetch("selected_template_id")}/reference_full.png" alt="#{h(result.fetch("selected_reference_edm"))} 历史 EDM 完整视觉" loading="lazy"></div>
        </figure>
        <figure class="visual-pane">
          <figcaption><strong>New Generated EDM</strong><a href="../output/historical_template_tests/#{case_id}/generated_full.png" target="_blank" rel="noreferrer">打开新稿</a></figcaption>
          <div class="visual-scroll" data-visual-scroll="generated"><img src="../output/historical_template_tests/#{case_id}/generated_full.png" alt="#{h(result.fetch("name"))} Historical-first 生成视觉" loading="lazy"></div>
        </figure>
      </div>
      <label class="sync-control"><input type="checkbox" data-sync-scroll checked> 左右按长图进度同步滚动</label>
      <p class="evidence-note">#{h(truth_note)} 当前 #{qa.fetch("structuralVisualSimilarity")}% 是“生成稿浏览器实测节奏 vs 历史视觉提取节奏”的结构相似度，不是像素级相似度，也不是 Human Acceptance。</p>
      <section class="review-panel" aria-labelledby="#{case_id}-review">
        <h3 id="#{case_id}-review">Human Review</h3>
        <div class="review-grid">
          <div class="field"><label for="#{case_id}-template">1. 像原历史 Template？</label><select id="#{case_id}-template" data-human-field="historical_template_similarity_score">#{score_options}</select><small>1–5，留空不自动填写</small></div>
          <div class="field"><label for="#{case_id}-brand">2. 像 SwitchBot？</label><select id="#{case_id}-brand" data-human-field="switchbot_brand_fit_score">#{score_options}</select><small>1–5</small></div>
          <div class="field"><label for="#{case_id}-content">3. 新内容适配合理？</label><select id="#{case_id}-content" data-human-field="content_adaptation_score">#{score_options}</select><small>1–5</small></div>
          <div class="field"><label for="#{case_id}-natural">4. 模板感自然？</label><select id="#{case_id}-natural" data-human-field="template_naturalness_score">#{score_options}</select><small>1=明显生硬，5=自然</small></div>
          <div class="field"><label for="#{case_id}-delivery">5. 达到交付水平？</label><select id="#{case_id}-delivery" data-human-field="deliverability_score">#{score_options}</select><small>1–5</small></div>
          <div class="field"><label for="#{case_id}-final">Final Decision</label><select id="#{case_id}-final" data-human-field="final_decision"><option value="">未填写</option><option>DELIVERABLE</option><option>MINOR_REVISION</option><option>MAJOR_REVISION</option><option>WRONG_TEMPLATE</option></select><small>只允许四种结果</small></div>
          <div class="field field--wide"><label for="#{case_id}-reason">Human Reason</label><textarea id="#{case_id}-reason" data-human-field="human_reason" placeholder="具体说明哪一段不像、哪一段适配自然、应如何调整"></textarea><small>本地保存；导出 CSV 后用于下一轮校准</small></div>
        </div>
      </section>
    </article>
  HTML
end.join

html = <<~HTML
  <!doctype html>
  <html lang="zh-CN">
  <head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
    <link rel="icon" href="data:,">
    <link rel="stylesheet" href="historical_template_validation.css">
    <title>SwitchBot Historical Template Validation</title>
  </head>
  <body>
    <a class="skip-link" href="#main">跳到主要内容</a>
    <div class="command-strip" role="region" aria-label="Review controls">
      <span class="command-strip__mark">Historical Template v1.0</span>
      <span class="command-strip__status" data-review-progress>0 / 4 Final Decision 已完成</span>
      <div class="command-strip__actions"><button class="button" type="button" data-clear-review>清空本地审核</button><button class="button button--primary" type="button" data-export-review>导出 Human Review CSV</button></div>
    </div>
    <main id="main" class="page">
      <header class="folio-mast">
        <div><p class="kicker">SwitchBot Japan · Historical Template First</p><h1>从真实历史稿出发，不再每次重做一套品牌。</h1></div>
        <div class="folio-mast__note"><strong>本页只审核 4 个新任务。</strong>左侧是真实 Approved Historical EDM，右侧是换入新产品／新内容后的结果。判断模板继承、品牌一致性、内容适配、模板生硬感与交付水平。</div>
      </header>
      <section class="strategy-ledger" aria-label="Visual decision budget"><div><b>70%</b><span>历史模板固定骨架：Section 顺序、节奏、CTA 语法、Footer 深度</span></div><div><b>20%</b><span>自动适配：FLEXIBLE 区域、文案长度、素材裁切</span></div><div><b>10%</b><span>新设计兜底：仅填真实缺口，不能覆盖历史骨架</span></div></section>
      <section class="section" id="library"><div class="section__head"><p class="kicker">Library Index</p><h2>8 个正式模板，全部绑定真实 SwitchBot Reference。</h2><p class="lede">共审核 21 个 Tier A/B 完整截图；排除 2 个 Test-only 后，19 个可用历史样本。v1.0 只把其中 8 个“完整视觉 + 恢复 HTML + Approved Anchor”升格为生产母版。</p></div><table class="library-table"><thead><tr><th>Template</th><th>Reference</th><th>结构名</th><th>覆盖 Campaign</th><th>Best For</th></tr></thead><tbody>#{library_rows}</tbody></table></section>
      #{case_sections}
      <section class="review-summary"><strong data-review-progress>0 / 4 Final Decision 已完成</strong><span>Human 字段没有自动填写；完成后使用顶部按钮导出 CSV。</span></section>
      <footer class="audit-footer"><div><strong>SwitchBot Historical EDM Template Library v1.0</strong><span>Source priority: Approved SwitchBot historical &gt; sent historical &gt; Usable historical &gt; Generic fallback. 外部案例不参与主视觉决策。</span></div><div><strong>QA</strong><span>4/4 Browser QA PASS<br>320 / 375 / 414 / 768 / 1280</span></div><div><strong>Evidence note</strong><span>Structural similarity is measured; Human Acceptance is pending.</span></div></footer>
    </main>
    <script src="historical_template_validation.js"></script>
  </body>
  </html>
HTML
File.write(File.join(ROOT, "research", "historical_template_validation.html"), html)

usable = audit.count { |row| row["usable_complete_historical"] == "true" }
full = audit.count { |row| row["screenshot_dimensions"] != "missing" }
formal = audit.count { |row| !row["formal_template_id"].to_s.empty? }
case_lines = summary.fetch("results").map do |row|
  qa = qa_by_case.fetch(row.fetch("case_id"))
  "| `#{row.fetch("case_id")}` | #{row.fetch("name")} | `#{row.fetch("selected_template_id")}` / `#{row.fetch("selected_reference_edm")}` | #{row.fetch("template_fit_score")} / #{row.fetch("reuse_mode")} | #{qa.fetch("structuralVisualSimilarity")}% | #{row.fetch("render_scope")} |"
end.join("\n")
template_lines = library.fetch("templates").map { |row| "| `#{row.fetch("template_id")}` | `#{row.fetch("reference_edm")}` | #{row.fetch("template_name")} | #{row.fetch("campaign_types").join(", ")} |" }.join("\n")
report = <<~MD
  # SwitchBot Historical EDM Template Library v1.0 — Completion Report

  生成日期：2026-08-20  
  策略：**70% Historical Skeleton + 20% Controlled Adaptation + 10% New-design Fallback**

  ## Executive Summary

  - Tier A/B 中共有 **#{full}** 个完整截图；排除 `SBG_011`、`SBG_014` 两个 Test-only Capture 后，**#{usable}** 个满足“正式发送或高可信历史视觉”的可用口径。
  - v1.0 正式冻结 **#{formal}** 个 Historical Template；每个都有完整 Reference、600px Desktop Snapshot、未改动的历史 HTML 与对应 source assets。
  - 来源分布：15 个 official-sender sent/production evidence、4 个 high-confidence Gmail visual、2 个 Test-only（不升格）。
  - 4 个新任务的离线 Expert-labelled Matcher Top-1 为 **4/4（100%）**。这是 N=4 的离线夹具准确率，**不是 Human Review Accuracy**。
  - 4 个生成稿均通过 320/375/414/768/1280 浏览器 QA。平均结构视觉相似度 **#{browser.fetch("averageStructuralVisualSimilarity")}%**；该指标比较浏览器实测生成节奏与历史视觉提取节奏，不代表像素级相似或人工认可。

  ## Formal Template Index

  | Template | Reference | Structure | Campaign Coverage |
  |---|---|---|---|
  #{template_lines}

  ## Campaign Coverage

  当前覆盖：Product Launch、Single Product Launch/Conversion、Ecosystem Launch、Theme/Seasonal Promotion、Countdown/Last Chance、User Voice + Education、Brand Story、Category Guide、Multi-product Comparison。

  ## Four Validation Tasks

  | Case | Task | Top-1 | Fit / Route | Structural Similarity | Truth Scope |
  |---|---|---|---|---:|---|
  #{case_lines}

  Promotion 案例 `HIST-VAL-003` 的价格、折扣、期间均未确认，因此只生成模板骨架验证稿；没有把任何 Promotion Fixture 当作真实 Campaign Truth。

  ## Core Production Templates

  - `HIST-TPL-002 / SBG_007`：高复杂度新品发布；大图分阶段 Reveal。
  - `HIST-TPL-003 / SBG_016`：最稳定的单品 Lifestyle→功能→细节→CTA 生产骨架。
  - `HIST-TPL-005 / SBG_006`：多产品主题促销；必须有真实场景、优惠与产品素材。
  - `HIST-TPL-008 / SBG_020`：长内容 Product Education／Category Guide。
  - `HIST-TPL-001 / SBG_001`：生态／多产品组合发布。
  - `HIST-TPL-006 / SBG_005`：只在真实 Last Chance 条件成立时使用。

  ## Not Yet Covered

  - 纯 Feature/App Update、短公告、低复杂度配件发布尚无 source-complete HTML 母版。
  - 纯 Sale Grid 虽有 `SBG_004` 完整截图，但没有恢复 HTML，先保留候选，不进入 v1.0 正式母版。
  - Cart Abandonment、Welcome、Replenishment 等 Lifecycle/Transactional EDM 不在当前历史视觉库覆盖范围。
  - `HIST-TPL-007` 的 User Voice 必须有可追溯评价证据；没有证据时不能借用结构伪造 Proof。
  - 独立 Desktop/Mobile 历史 Pair 仍不足；Mobile 继续由 Design Standard QA 约束，不声称已从每个母版恢复真实 Reflow。

  ## Matcher and Production Boundary

  - `historical_template_first: true` 已写入策略与生产路由。
  - `>=80` Direct Reuse；`65–79` Reuse + Adapt；`50–64` Heavy Adapt + Human Review；`<50` 才允许进入 Generic/New Candidate。
  - Design Standard 只负责 QA；Module Library 只允许在 FLEXIBLE/OPTIONAL 区域有限增删；Tier D 与外部案例不能覆盖历史骨架。
  - 新结构只有在实际上线或 Human Approved 后，才可通过 Promotion Loop 进入 Historical Library；当前 4 个新稿尚未完成 Human Review，因此没有自动升格。

  ## Review Gate

  Review 页面：`research/historical_template_validation.html`  
  Human 字段保持空白。等待 `DELIVERABLE / MINOR_REVISION / MAJOR_REVISION / WRONG_TEMPLATE` 决策后再校准，不继续自由生成。
MD
File.write(File.join(ROOT, "research", "historical_template_report.md"), report)

puts "Built validation page and report for #{summary.fetch("case_count")} cases."
