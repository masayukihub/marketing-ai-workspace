#!/usr/bin/env ruby
# frozen_string_literal: true

require "yaml"
require "json"
require "cgi"
require "date"
require "time"

ROOT = File.expand_path("..", __dir__)
REGISTRY = File.join(ROOT, "production_registry")
RESEARCH = File.join(ROOT, "research")
STATES = %w[INTERNAL_DRAFT DESIGN_READY VISUAL_DELIVERABLE_CANDIDATE CONTENT_APPROVED ESP_READY PRODUCTION_READY].freeze

def load_yaml(path)
  YAML.safe_load(File.read(path), permitted_classes: [Date, Time], aliases: true)
end

def h(value)
  CGI.escapeHTML(value.to_s)
end

def slug(value)
  value.to_s.downcase.gsub(/[^a-z0-9]+/, "-").gsub(/^-|-$/, "")
end

def status_badge(status)
  %(<span class="status status--#{slug(status)}">#{h(status)}</span>)
end

def source_link(source)
  text = source.to_s
  if text.start_with?("http://", "https://")
    %(<a href="#{h(text)}" target="_blank" rel="noreferrer">#{h(text)}</a>)
  else
    first = text.split(/\s+and\s+|\s+plus\s+/).first
    path = first.split("#").first
    if File.exist?(File.join(ROOT, path))
      %(<a href="../#{h(path)}">#{h(text)}</a>)
    else
      %(<code>#{h(text)}</code>)
    end
  end
end

def page_shell(title:, subtitle:, active:, body:)
  nav = [
    ["Registry Index", "production_readiness_dashboard.html#index"],
    ["Readiness", "production_readiness_dashboard.html#readiness"],
    ["State Machine", "production_readiness_dashboard.html#state-machine"],
    ["Blockers", "production_readiness_dashboard.html#blockers"],
    ["Approval Queue", "manual_approval_queue.html#approval-queue"],
    ["Final Visual Review", "phase8_visual_delivery_review.html#final-review"]
  ].map { |label, href| %(<a href="#{href}">#{label}</a>) }.join
  <<~HTML
    <!doctype html>
    <html lang="zh-CN" data-theme="phase7-almanac">
    <head>
      <meta charset="utf-8">
      <meta name="viewport" content="width=device-width, initial-scale=1">
      <meta name="color-scheme" content="light">
      <title>#{h(title)}</title>
      <link rel="icon" href="data:,">
      <link rel="stylesheet" href="../tokens.css">
      <link rel="stylesheet" href="production_readiness.css">
    </head>
    <body>
      <a class="skip-link" href="#main">Skip to content</a>
      <header class="mobile-header"><a href="production_readiness_dashboard.html">Phase 8 Registry</a><a href="phase8_visual_delivery_review.html">Final Review</a></header>
      <div class="shell">
        <aside class="rail" aria-label="Phase 8 navigation">
          <a class="rail__mark" href="production_readiness_dashboard.html">SwitchBot EDM<br>Production Registry</a>
          <div class="rail__phase">Phase 8 · #{h(active)}</div>
          <nav>#{nav}</nav>
          <div class="rail__foot">Evidence ≠ Approval<br>Generated #{Time.now.strftime('%Y-%m-%d')}</div>
        </aside>
        <main class="content" id="main">
          <header class="mast">
            <div><p class="kicker">Approval Automation & Production Closure</p><h1>#{h(title)}</h1></div>
            <div class="mast__note"><strong>#{h(subtitle)}</strong>官方来源可以关闭设计证据；整封 Human Review 与 ESP Send Gate 保持独立。</div>
          </header>
          #{body}
          <footer class="dense-footer">
            <div><strong>SwitchBot Japan EDM Production Registry</strong>统一管理 Product、Claim、Asset、Campaign、Pricing、Legal、Footer 与 Approval State。</div>
            <div><strong>Frozen inputs</strong>Design Standard v1.0<br>Design System v1.0<br>Generator Logic v1.0</div>
            <div><strong>Phase boundary</strong>Visual Gate ≠ ESP Gate<br>No new templates<br>No pattern mining</div>
          </footer>
        </main>
      </div>
    </body>
    </html>
  HTML
end

snapshot = load_yaml(File.join(REGISTRY, "readiness_snapshot.yaml"))
registry = snapshot.fetch("registry_completeness")
cases = snapshot.fetch("cases")

index_rows = cases.map do |row|
  <<~HTML
    <tr>
      <td><a href="#case-#{h(row['product_id'])}"><strong>#{h(row['product_name'])}</strong></a><br><code>#{h(row['case_id'])}</code></td>
      <td class="percent">#{row['phase6_evidence_baseline_percent']}%</td>
      <td class="percent">#{row['design_evidence_percent']}%</td>
      <td>#{status_badge(row['overall_status'])}</td>
      <td>#{row['blockers'].length}</td>
    </tr>
  HTML
end.join

case_sections = cases.map do |row|
  metrics = row.fetch("domains").map do |name, metric|
    <<~HTML
      <div class="metric">
        <div class="metric__label"><span>#{h(name)}</span><span>#{h(metric['gate'])}</span></div>
        <div class="metric__value">#{metric['percent']}%</div>
        <div class="meter" aria-label="#{h(name)} #{metric['percent']} percent"><span style="width: #{metric['percent']}%"></span></div>
      </div>
    HTML
  end.join
  state_chain = STATES.map do |state|
    current = state == row["overall_status"] ? " is-current" : ""
    gate = state == "INTERNAL_DRAFT" ? true : row.dig("state_gates", state)
    %(<div class="state-chain__item#{current}"><b>#{state}</b><span>#{gate ? 'Gate satisfied' : 'Waiting'}</span></div>)
  end.join
  blockers = row.fetch("blockers").map do |blocker|
    <<~HTML
      <details class="blocker">
        <summary><span class="blocker__id">#{h(blocker['blocker_id'])}</span><strong>#{h(blocker['missing'])}</strong><span class="status status--block">Blocks #{h(blocker['gate'])}</span></summary>
        <dl class="blocker__body">
          <div><dt>Source</dt><dd>#{source_link(blocker['source'])}</dd></div>
          <div><dt>Approver</dt><dd>#{h(blocker['approver'])}</dd></div>
          <div><dt>Next action</dt><dd>#{h(blocker['next_action'])}</dd></div>
        </dl>
      </details>
    HTML
  end.join
  <<~HTML
    <article class="case" id="case-#{h(row['product_id'])}">
      <div class="case__head">
        <div><p class="eyebrow">#{h(row['case_id'])}</p><h3>#{h(row['product_name'])}</h3><p class="lede">Phase 6 evidence baseline: #{row['phase6_evidence_baseline_percent']}%. Phase 8 measures design evidence separately from Human Approval and ESP readiness.</p></div>
        <div class="case__score"><b>#{row['design_evidence_percent']}%</b><span>DESIGN EVIDENCE</span><br>#{status_badge(row['overall_status'])}</div>
      </div>
      <div class="metric-grid">#{metrics}</div>
      <div class="state-chain" aria-label="#{h(row['product_name'])} state machine">#{state_chain}</div>
      <div class="blocker-list">#{blockers}</div>
    </article>
  HTML
end.join

dashboard_body = <<~HTML
  <section class="section" id="index">
    <div class="section__head"><h2>视觉交付与发送资格分开管理</h2><p class="lede">Design Evidence 表示视觉生产所需真值已闭合；Human Review 和 ESP Runtime 只在各自 Gate 发生作用。</p></div>
    <table class="index-table">
      <thead><tr><th>Product / Case</th><th>Evidence baseline</th><th>Design evidence</th><th>Status</th><th>Open gates</th></tr></thead>
      <tbody>#{index_rows}</tbody>
    </table>
  </section>
  <section class="section" id="registry">
    <div class="section__head"><h2>证据已自动闭合，不重复索取人工点击</h2><p class="lede">官方 Claim 与官方素材满足 Visual Candidate；最终整封审核和 ESP Token 仍保持人工业务责任。</p></div>
    <div class="registry-stats">
      <div class="registry-stat"><b>#{registry.dig('claim_registry', 'structural_percent')}%</b><span>Claim registry structural</span></div>
      <div class="registry-stat"><b>#{registry.dig('claim_registry', 'visual_evidence_resolved_percent')}%</b><span>Required claims resolved</span></div>
      <div class="registry-stat"><b>#{registry.dig('asset_registry', 'structural_percent')}%</b><span>Asset registry structural</span></div>
      <div class="registry-stat"><b>#{registry.dig('asset_registry', 'design_scope_resolved_percent')}%</b><span>Design assets resolved</span></div>
    </div>
  </section>
  <section class="section" id="readiness">
    <div class="section__head"><h2>按 Gate 而不是按感觉晋级</h2><p class="lede">点击任一 Blocker 可直接查看缺口、来源、审批人和下一步动作。</p></div>
    #{case_sections}
  </section>
  <section class="section" id="state-machine">
    <div class="section__head"><h2>Visual 与 ESP 两条 Gate</h2><p class="lede">`VISUAL_DELIVERABLE_CANDIDATE` 不受 ESP Runtime Token 阻塞；实际发送仍必须完成 Content、ESP 与 Final Delivery Gate。</p></div>
    <div class="state-chain">#{STATES.map { |state| %(<div class="state-chain__item"><b>#{state}</b><span>#{STATES.index(state)}</span></div>) }.join}</div>
  </section>
  <section class="section" id="blockers">
    <div class="section__head"><h2>下一步只审整封 Lock Ultra</h2><p class="lede">15 项中间审批已压缩为 2 项：Lock Ultra 整封 Final Review，以及发送阶段 ESP Runtime Contract。</p><p><a class="button button--primary" href="phase8_visual_delivery_review.html">Open Final Visual Review</a></p></div>
  </section>
HTML

File.write(File.join(RESEARCH, "production_readiness_dashboard.html"), page_shell(title: "Production Readiness", subtitle: "Lock Ultra 已达到 Visual Candidate。", active: "Dashboard", body: dashboard_body))

queue = load_yaml(File.join(REGISTRY, "approvals", "pending_approvals.yaml"))

def locate_selector(node, selector)
  case node
  when Array
    match = node.find { |item| item.is_a?(Hash) && selector.all? { |key, value| item[key.to_s] == value } }
    return match if match
    node.each { |item| found = locate_selector(item, selector); return found if found }
  when Hash
    node.each_value { |value| found = locate_selector(value, selector); return found if found }
  end
  nil
end

def current_target_status(item)
  statuses = item.fetch("targets").map do |target|
    doc = load_yaml(File.join(REGISTRY, target.fetch("file")))
    base = target["selector"] ? locate_selector(doc, target.fetch("selector")) : doc
    target.fetch("path").split(".").reduce(base) { |memo, key| memo.is_a?(Hash) ? memo[key] : nil }
  end.uniq
  statuses.length == 1 ? statuses.first : statuses.join(" / ")
end

active_ids = queue.fetch("active_human_approval_ids")
active_items = queue.fetch("items").select { |item| active_ids.include?(item.fetch("approval_id")) }
cards = active_items.map do |item|
  current_status = current_target_status(item)
  <<~HTML
    <article class="approval-card" data-approval-card data-approval-id="#{h(item['approval_id'])}" data-type="#{h(item['type'])}" data-product="#{h(item['product'])}" data-current-status="#{h(current_status)}">
      <div class="approval-card__head">
        <div class="approval-card__id">#{h(item['approval_id'])}</div>
        <div><p class="eyebrow">#{h(item['type'])}</p><h3>#{h(item['product'])}</h3></div>
        #{status_badge(current_status)}
      </div>
      <dl class="approval-meta">
        <div><dt>Proposed Value</dt><dd>#{h(item['proposed_value'])}</dd></div>
        <div><dt>Source</dt><dd>#{source_link(item['source'])}</dd></div>
        <div><dt>Why Needed</dt><dd>#{h(item['why_needed'])}</dd></div>
        <div><dt>Used In</dt><dd>#{h(item['used_in'])}</dd></div>
        <div><dt>Risk</dt><dd>#{h(item['risk'])}</dd></div>
        <div><dt>Write-back Targets</dt><dd>#{item.fetch('targets').length} registry field(s)</dd></div>
      </dl>
      <div class="approval-fields">
        <div class="field"><label for="decision-#{h(item['approval_id'])}">Human Decision</label><select id="decision-#{h(item['approval_id'])}" data-field="human_decision"><option value="">Select…</option>#{queue.fetch('decisions').map { |value| %(<option value="#{h(value)}">#{h(value)}</option>) }.join}</select></div>
        <div class="field"><label for="reviewer-#{h(item['approval_id'])}">Reviewer</label><input id="reviewer-#{h(item['approval_id'])}" data-field="reviewer" autocomplete="name" placeholder="Human reviewer name"></div>
        <div class="field field--wide"><label for="evidence-#{h(item['approval_id'])}">Evidence Note</label><textarea id="evidence-#{h(item['approval_id'])}" data-field="evidence_note" placeholder="Optional for most items; required to Approve high-risk unverified evidence or ESP token contract."></textarea></div>
        <div class="field field--wide"><label for="modify-#{h(item['approval_id'])}">Revision Value</label><textarea id="modify-#{h(item['approval_id'])}" data-field="modified_value" placeholder='For MINOR/MAJOR_REVISION only: {"footer/switchbot_jp_footer.yaml#runtime_tokens.unsubscribe.token":"actual token"}'></textarea><small>Revision uses a JSON object keyed by registry file and exact value path. Final Lock review must be applied through the dedicated five-dimension review script.</small></div>
      </div>
    </article>
  HTML
end.join

products = active_items.map { |item| item.fetch("product") }.uniq
statuses = active_items.map { |item| current_target_status(item) }.uniq
queue_body = <<~HTML
  <section class="section" id="approval-queue">
    <div class="section__head"><h2>只审真正阻塞 Production 的项目</h2><p class="lede">所有 Human Decision 默认留空。页面仅保存在本机浏览器；导出 CSV 不会直接修改 Registry。</p></div>
    <div class="queue-toolbar">
      <select class="queue-filter" id="filter-product" aria-label="Filter product"><option value="all">All products</option>#{products.map { |value| %(<option value="#{h(value)}">#{h(value)}</option>) }.join}</select>
      <select class="queue-filter" id="filter-state" aria-label="Filter current status"><option value="all">All statuses</option>#{statuses.map { |value| %(<option value="#{h(value)}">#{h(value)}</option>) }.join}</select>
      <button class="button button--primary" id="export-approvals" type="button">Export Human Approval CSV</button>
      <button class="button" id="clear-local" type="button">Clear Local Draft</button>
      <span class="queue-progress" id="queue-progress">0 / #{active_items.length} decisions completed</span>
    </div>
    <div class="approval-list">#{cards}</div>
  </section>
  <section class="section" id="write-back">
    <div class="section__head"><h2>导出后由审计脚本回写</h2><p class="lede"><code>ruby production_readiness/apply_approvals.rb path/to/exported.csv --apply</code></p><p class="lede">脚本会保存 before / after 快照，追加 JSONL Ledger，记录 reviewer、decision time、source、previous value 与 new value，然后自动重算 Dashboard。Codex / AI 不能作为 reviewer。</p></div>
  </section>
  <script src="production_readiness.js"></script>
HTML

File.write(File.join(RESEARCH, "manual_approval_queue.html"), page_shell(title: "Manual Approval Queue", subtitle: "15 → 2，只保留真实业务责任。", active: "Human Approval", body: queue_body))

lock_row = cases.find { |row| row["case_id"] == "PILOT-A-LOCK-ULTRA" }
review_options = %w[PASS NEEDS_REVISION FAIL]
decision_options = queue.fetch("decisions")
review_fields = [
  ["product_information", "1. 产品信息是否正确"],
  ["japanese_usability", "2. 日语是否可以使用"],
  ["brand_fit", "3. 品牌感是否正确"],
  ["content_completeness", "4. 内容是否完整"],
  ["visual_delivery_quality", "5. 视觉是否达到交付水平"]
].map do |field, label|
  <<~HTML
    <div class="field">
      <label for="#{field}">#{h(label)}</label>
      <select id="#{field}" data-review-field="#{field}">
        <option value="">Select…</option>
        #{review_options.map { |value| %(<option value="#{value}">#{value}</option>) }.join}
      </select>
    </div>
  HTML
end.join

review_body = <<~HTML
  <section class="section" id="final-review">
    <div class="section__head">
      <p class="eyebrow">PILOT-A-LOCK-ULTRA · WHOLE EMAIL REVIEW</p>
      <h2>只判断最终交付，不再审批中间状态</h2>
      <p class="lede">当前状态：#{status_badge(lock_row.fetch('overall_status'))}。Product Truth、Claim Mapping、官方素材、日语自动 QA、Desktop/Mobile Browser QA 均已通过。</p>
    </div>
    <div class="visual-review-grid">
      <figure class="visual-review visual-review--desktop">
        <figcaption><strong>Full-length EDM</strong><span>600px · 10 modules · 2 CTA · 5194px</span></figcaption>
        <img src="../production_output/PILOT-A-LOCK-ULTRA/full_edm.png" alt="SwitchBot ロックUltra full-length EDM candidate">
      </figure>
      <div class="visual-review-side">
        <figure class="visual-review visual-review--mobile">
          <figcaption><strong>Mobile Preview</strong><span>390 × 844 viewport</span></figcaption>
          <img src="../production_output/PILOT-A-LOCK-ULTRA/mobile_preview.png" alt="SwitchBot ロックUltra mobile EDM candidate">
        </figure>
        <div class="review-evidence">
          <p class="eyebrow">Verified package</p>
          <ul>
            <li>6 / 6 used Claim IDs resolved</li>
            <li>3 / 3 official assets resolved for design production</li>
            <li>Japanese Copy Pipeline: PASS</li>
            <li>320 / 375 / 390 / 414 / 768 responsive QA: PASS</li>
            <li>No price, promotion, numeric performance or No.1 claim</li>
          </ul>
          <p><a class="button" href="../production_output/PILOT-A-LOCK-ULTRA/editable_edm.html">Open Editable HTML</a></p>
        </div>
      </div>
    </div>
  </section>
  <section class="section" id="human-decision" data-phase8-final-review data-case-id="PILOT-A-LOCK-ULTRA" data-current-status="#{h(lock_row.fetch('overall_status'))}">
    <div class="section__head"><h2>Final Human Decision</h2><p class="lede">所有字段默认留空。`APPROVE` 只关闭整封内容与视觉审核；ESP Runtime Token 仍独立阻塞实际发送。</p></div>
    <div class="final-review-fields">
      #{review_fields}
      <div class="field">
        <label for="overall_decision">Overall Decision</label>
        <select id="overall_decision" data-review-field="overall_decision"><option value="">Select…</option>#{decision_options.map { |value| %(<option value="#{h(value)}">#{h(value)}</option>) }.join}</select>
      </div>
      <div class="field">
        <label for="reviewer">Reviewer</label>
        <input id="reviewer" data-review-field="reviewer" autocomplete="name" placeholder="Human reviewer name">
      </div>
      <div class="field field--wide">
        <label for="human_reason">Human Reason / Revision Direction</label>
        <textarea id="human_reason" data-review-field="human_reason" placeholder="Minor/Major revision 时请写明具体需要修改的内容。"></textarea>
      </div>
    </div>
    <div class="review-actions">
      <button class="button button--primary" id="export-phase8-review" type="button">Export Final Review CSV</button>
      <button class="button" id="clear-phase8-review" type="button">Clear Local Draft</button>
      <span class="queue-progress" id="phase8-review-progress">0 / 6 review fields completed</span>
    </div>
  </section>
  <section class="section">
    <div class="section__head"><h2>Gate boundary</h2><p class="lede">Approve 后可进入 `VISUAL_DELIVERABLE` / `CONTENT_APPROVED`。只有实际 ESP Token 合同完成后，才可进入 `ESP_READY` 与 `PRODUCTION_READY`。</p></div>
  </section>
  <script src="phase8_visual_review.js"></script>
HTML

File.write(File.join(RESEARCH, "phase8_visual_delivery_review.html"), page_shell(title: "Lock Ultra Final Review", subtitle: "Visual Candidate，等待一次整封判断。", active: "Final Visual Review", body: review_body))
puts "Built production_readiness_dashboard.html, manual_approval_queue.html and phase8_visual_delivery_review.html"
