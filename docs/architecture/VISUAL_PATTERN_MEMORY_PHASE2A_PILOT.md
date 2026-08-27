# Visual Pattern Memory Phase 2A Pilot

## Scope

本 Pilot 只验证 `S30 mini Amazon → EDM` 的跨渠道纵向链路。Lock Ultra Max 仅用于低 Asset Readiness 负向回归；不建设 LP、Campaign HTML、大型 Pattern 管理后台或自动抓取平台。

正式基线：`main@787acb4fe2ba3bdc34eccf876fb86240cfa74f40`。

## Architecture Map

```text
projects/s30-mini/project-context.yaml
→ Project Visual DNA (ROUTER_GENERATED_CANDIDATE)
→ channel_assignments.amazon_jp
   → VP-AMZ-MECHANISM-PROOF
   → Existing Amazon Flow
→ channel_assignments.edm
   → channel_contexts.edm / Channel Intent
   → VP-EDM-COMPLEX-LAUNCH (CANDIDATE)
   → RECIPE-EDM-PRODUCT-LAUNCH-PROOF (CANDIDATE)
   → 6 EDM Section Patterns (CANDIDATE)
   → ADAPTER-EDM-JP
   → template_selection_request
   → skills/switchbot-japan-edm
   → Stable Template Selector / Existing Module System
   → Existing Renderer
   → Product Layer / Asset Gate / Human Review / Hardening
   → Mobile QA / ESP Gate
```

跨渠道只继承 Visual DNA。Amazon Gallery/A+ Layout、尺寸、文案、图片、Claim、价格与 CTA 均不得进入 EDM Assignment。

## Visual Profile Schema v1.1

新增字段：

- `project_visual_dna`
- `pattern_match`
- `execution_readiness`
- `evidence_confidence`
- `channel_assignments`
- `reason_codes`
- `auto_apply`
- `blocking_reasons`
- `source_provenance`

`decision.score` 与 Primary Channel `ranking` 仅保留 Phase 1 兼容性。正式生产资格由 Execution Readiness、Gate、Pattern/Recipe 生命周期和 Human Review 共同决定，不使用单一综合分。

## S30 Project Visual DNA

| Field | Router Candidate |
|---|---|
| Status | `ROUTER_GENERATED_CANDIDATE` |
| Tone | clean / japan consumer friendly |
| Proof Strategy | proof before persuasion |
| Visual Rhythm | product first → mechanism → proof |
| Image Strategy | official product and approved evidence only |
| Information Strategy | source complexity: high / structured progressive disclosure |
| Conversion Style | single verified action after proof |
| Mobile Priority | high |

Visual DNA 不包含产品事实、规格、性能数字、价格、Claim 或素材批准。

## Channel Assignments

### Amazon JP

| Metric | Result |
|---|---|
| Primary Pattern | `VP-AMZ-MECHANISM-PROOF` |
| Legacy Ranking | `89.7`，与 Phase 1 一致 |
| Pattern Match | `97.8 / HIGH` |
| Execution Readiness | `43.5 / BLOCKED_BY_ASSET` |
| Evidence Confidence | `47.5 / LOW` |
| Freeze | Candidate，未继承 |
| Channel Information Density | `high_structured` |

### EDM

| Metric | Result |
|---|---|
| Primary Pattern | `VP-EDM-COMPLEX-LAUNCH / CANDIDATE` |
| Recipe | `RECIPE-EDM-PRODUCT-LAUNCH-PROOF / CANDIDATE` |
| Channel Intent | `product_launch / new_product_value_understanding`，Candidate Routing Input |
| Channel Information Density | `medium_selective` |
| Existing Template | `TPL-LAUNCH-A / CANDIDATE_CONDITIONAL_MATCH`，由 Stable Template Selector 最终决定 |
| Pattern Match | `78.2 / HIGH` |
| Execution Readiness | `28.0 / BLOCKED_BY_ASSET` |
| Evidence Confidence | `32.5 / LOW` |
| Auto Apply | `BLOCKED` |

S30 Candidate Freeze 只覆盖 `amazon_jp`，且其 Amazon Pattern 不支持 EDM，因此 EDM Assignment 明确记录 `applicability=NOT_APPLICABLE_TO_CHANNEL`，并保留：

- `FREEZE_CHANNEL_SCOPE_EXCLUDES_CHANNEL`
- `FREEZE_PATTERN_CHANNEL_INCOMPATIBLE`

该 Freeze 只作为跨渠道治理记录存在，不进入 EDM `execution_readiness.blocking_reasons`，也不降低 EDM Readiness。只有 Freeze 对当前渠道适用、但审批状态不满足时，才是当前渠道 Blocker。

## EDM Recipe and Section Patterns

Recipe：

Required：`Product-first Hero → Benefit Summary → Purchase CTA → Brand Footer`

Optional / Conditional：`Consumer Problem → Mechanism Proof → Product/Lifestyle Context → App/Automation → Legal Note`

Recipe 只提交 `template_selection_request`。`TPL-LAUNCH-A` 当前是 `CANDIDATE_CONDITIONAL_MATCH`，不得覆盖 Stable Template Selector。缺少已解析 EDM Intent 时，Router 返回 `EDM_INTENT_NOT_RESOLVED / HUMAN_REVIEW_REQUIRED`，不得默认选择 Launch Recipe。

新增 Section Pattern 不超过六个：

1. `SEC-EDM-PRODUCT-FIRST-HERO`
2. `SEC-EDM-CONSUMER-PROBLEM`
3. `SEC-EDM-BENEFIT-SUMMARY`
4. `SEC-EDM-MECHANISM-PROOF`
5. `SEC-EDM-APP-AUTOMATION`
6. `SEC-EDM-CHANNEL-CTA`

全部为 `CANDIDATE`。Pattern Package 包含 `pattern.yaml`、`anatomy.zh-CN.md`、`slots.yaml`、`channel-map.yaml`、`anti-patterns.md` 和 `validation.yaml`。

## EDM Reference Ingestion

Source：仓库内 Frozen Template/Module System、Tier A SwitchBot EDM 结构化反向分析和 Production Registry Gate。

只沉淀 Information Architecture、Visual Rhythm、Section Structure、Conversion Pattern、Responsive Principle 和 Design Principle。

未保存 Mailchimp `mc:*`、Logo、原文、图片、价格、Coupon、Claim、完整 Layout 或 Trade Dress。当前输出只能注册为 Candidate。

## Lock Ultra Max Regression

| Metric | Result |
|---|---|
| Amazon Pattern | `VP-AMZ-JAPAN-FIT-TRUST` |
| Legacy Ranking | `81.1`，与 Phase 1 一致 |
| Pattern Match | `98.2 / HIGH` |
| Execution Readiness | `15.0 / BLOCKED_BY_ASSET` |
| Freeze | 不存在，也未创建 |
| Auto Apply | `false` |
| Decision | `HUMAN_REVIEW_REQUIRED` |

没有丰富 Lock Ultra Max 的正式视觉内容。

## Protected Hashes

基线保存在 `visual-system/tests/phase2a-protected-hashes.yaml`：

- Product Truth：Product Master、Facts、Specs、Compatibility、Compliance、Known Issues；
- Claim：`skills/product-knowledge/references/claim.md`。

Pilot 不修改这些文件。S30 当前没有可直接解析的 Approved Product Knowledge 实体，因此不能把 Visual DNA 或 Recipe 当成 S30 Product Truth。

## Local Absolute Path Debt

基线为 29 个文件、80 处用户目录绝对路径。Pilot 不清理历史债务；测试允许数量减少，但禁止新增文件或让 Allowlist 文件的出现次数增加。

## Human Gate

Recommended Gate：`HUMAN_PATTERN_AND_ASSET_REVIEW`。

在以下项目完成前，不进入正式 EDM Renderer：

1. S30 日本正式产品与 Offer 定义；
2. Approved Product Truth 与 Approved JP Claim；
3. 官方产品、机制、Lifestyle、UI / Automation 素材及使用范围；
4. 真实 CTA、落地页、Legal/Footer；
5. Candidate Recipe 与六个 Section Pattern 的人工结构 Review；
6. Existing Runtime 的 Template Selection、Mobile QA、Final Human 与 ESP Gate。
