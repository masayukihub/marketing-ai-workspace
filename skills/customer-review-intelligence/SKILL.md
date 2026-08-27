---
name: customer-review-intelligence
description: "收集、规范化、去重、映射、分类并分析 SwitchBot 日本市场公开评价与 VOC。适用于 Amazon、楽天、Yahoo、官网、KOL、YouTube、SNS、竞品口碑、差评风险、FAQ和营销信息优化。"
---
## 本地化与输出语言

- 默认用简体中文解释分析、过程、风险和建议。
- 面向日本市场的广告、PR、EDM、LP、SNS及其他对外文案，使用自然、简洁的日语。
- 保留平台名称、指标缩写、公式、代码、命令、文件名、API字段和工具参数的原文。
- 不因本地化改写事实、指标定义、权限边界或操作步骤。


# Customer Review Intelligence

Build an auditable Japanese-market VOC history. Separate actual user feedback from owned, paid, syndicated, or unavailable evidence.

## Project context preflight

For a named existing project, run `project-context-resolver` first and consume only VOC-scoped Project Memory, decisions, and Product Truth. A VOC result may propose a durable learning or risk to Project Memory, but it must not directly promote Product Truth, decisions, or project stage.

## Required workflow

1. Read [standard_run_contract.md](references/standard_run_contract.md), [collection_rules.md](references/collection_rules.md), [data_contract.md](references/data_contract.md), and [analysis_rules.md](references/analysis_rules.md). For product, marketing, EC, support, or management deliverables, also read [business_application_rules.md](references/business_application_rules.md). For a Feishu Miaoda handoff or application, also read [miaoda_integration.md](references/miaoda_integration.md) and use `$lark-apps` for external app actions. When the user requests a Feishu Base / 多维表格 operating layer, also read [feishu_base_operations.md](references/feishu_base_operations.md) and use `$lark-base`.
2. Resolve every product through `$product-knowledge` before product-level analysis. Use identifier lookup first, then exact current aliases. Never fuzzy-map an unknown or ambiguous product.
3. Read the workspace `config/sources.yaml` and `config/products.yaml`. Confirm the requested time window, modules, product pages, pagination boundaries, and supplied KOL/PR links.
4. Collect only public evidence or user-provided exports. Never bypass login, CAPTCHA, rate limits, or platform controls. Save an immutable raw snapshot, manifest, hash, retrieval cutoff, and coverage result.
   When the user explicitly authorizes their external browser, use the browser-assisted fallback in `references/collection_rules.md`: capture the visible page plus screenshots, DOM text, IDs, dates, scroll/page boundaries, and failure state. Never inspect cookies, passwords, storage, or authentication tokens.
5. Run normalization, deduplication, entity mapping, classification, validation, indexing, analysis, and report generation. Preserve old versions; never overwrite source history.
6. Route Critical/High, ambiguous, multi-product, contradictory, suspected duplicate, safety, privacy, return, and low-confidence records to manual review.
7. Report conclusions in this order: conclusion, evidence, cause or alternative explanations, business impact, recommendation, action owner, deadline, and success metric.
8. Build the user-voice-to-action chain: review → topics → scenario → sentiment/severity → value or issue → root-cause hypothesis → action. Keep every action traceable to review IDs and source URLs.

## Run

Use the standardized orchestrator from the skill directory:

```bash
/Users/lai/Documents/marketing/customer-review-intelligence/.venv/bin/python scripts/run_standard_workflow.py \
  --workspace /Users/lai/Documents/marketing/customer-review-intelligence/products/<product-slug> \
  --config-dir /Users/lai/Documents/marketing/customer-review-intelligence/config \
  --product-knowledge-dir /Users/lai/.codex/skills/product-knowledge \
  --modules ec,sns,kol,pr,official,competitor \
  --mode incremental
```

Use `--initial-full` or `--mode full` only for first-time history collection. Use `--date-from` and `--date-to` to declare the requested evidence window, `--products` to limit entity IDs, and `--output-dir` for a separate report destination. Use `--analyze-only` to rebuild outputs from the current normalized database without network collection. Use `--input <csv-or-json>` for official exports or manual evidence.

For Amazon, X, or YouTube without API credentials, prefer the user's explicitly authorized external browser. Store each capture under `raw/<source>/<batch_id>/screenshots/`, write `browser_capture_manifest.json`, validate it with `scripts/validate_browser_capture.py`, then import the extracted records through `--input`. Screenshot-only evidence without extracted visible text remains `Incomplete`.

For a decision-oriented offline dashboard, run `scripts/build_dashboard_v2.py` against the normalized CSV. Preserve the previous dashboard, write the new version under `outputs/dashboard_v2/`, and verify desktop plus narrow layouts, issue-to-voice navigation, source links, filter synchronization, and CSV exports.

Use `--build-business --build-dashboard-v2 --export-miaoda` for a single decision-dashboard handoff. Use `--export-miaoda-multichannel --coverage-csv <unified_channel_statistics.csv>` when the application must include every collected channel and distinguish Natural VOC from Context Only, KOL, PR, media, and official content. Both exporters create local, hash-manifested bundles only. They do not create, migrate, import, release, or publish a Feishu app. For a collaborative Miaoda system use `full_stack`; for a read-only snapshot use `html`. For a new app, confirm local-code versus Miaoda-cloud development before initialization.

Treat the source-language review text as immutable evidence. Summaries, translations, taxonomies, word-cloud tokens, issue clusters, and recommendations are derived fields and must never overwrite it. Product and marketing recommendations require linked `review_id` evidence and source-language quotations; if no relevant evidence exists, label the recommendation `Evidence Insufficient`.

## Analysis rules

- Keep rating and text sentiment separate. Use `Positive`, `Neutral`, `Negative`, or `Mixed`.
- For business-application outputs, additionally derive `Strong Positive`, `Positive`, `Neutral`, `Negative`, `Strong Negative`, or `Mixed` without overwriting the core four-state field. Save `rating_sentiment_mismatch` and the derivation basis.
- Keep `[Fact]`, `[Insight]`, `[Hypothesis]`, `[Recommendation]`, `[Data Gap]`, and `[Risk]` distinct.
- Never call paid KOL, PR placement, media syndication, or official posts natural VOC. Only their user comments can qualify.
- Do not mark an absent record `Deleted` unless a complete recheck of the same source scope succeeded.
- Treat `0 reviews`, `Blocked`, `Incomplete`, `Not Available`, and `Unverified` as different states.
- Do not say “用户普遍认为” for a small or unrepresentative sample.
- Do not turn every complaint into a TODO. Apply the responsibility and repetition rules in `analysis_rules.md`.
- Do not expose reviewer display names in reports.
- Calculate issue priority transparently from frequency, negative intensity, rating impact, helpfulness, recency, and product importance. Never present a black-box score; show components, sample size, confidence, and coverage limitations.
- Produce separate, evidence-backed backlogs for Product/Engineering, Marketing/EC/PR/KOL, and Customer Support/Content Education. Do not route logistics complaints to Product Quality.

## Outputs

Generate timestamped batches under the workspace:

```text
raw/<source>/<batch_id>/
normalized/reviews.csv
normalized/reviews.parquet
normalized/review_versions.csv
normalized/review_index.json
reports/product/
reports/manual_review/
reports/biweekly/latest.md
outputs/collection_report.md
outputs/data_quality_report.md
outputs/duplicate_report.md
outputs/unmapped_products.md
outputs/action_plan.csv
outputs/product_summary.csv
outputs/channel_comparison.csv
outputs/trend_analysis.csv
outputs/latest_review_summary.html
outputs/customer_voice_library.xlsx
outputs/product_improvement_backlog.xlsx
outputs/marketing_insight_playbook.xlsx
outputs/support_content_backlog.xlsx
outputs/voc_action_plan.xlsx
outputs/latest_update_summary.md
outputs/review_dashboard.html
outputs/dashboard_data.json
outputs/dashboard_v2/index.html
outputs/dashboard_v2/dashboard_data.json
outputs/dashboard_v2/dashboard.css
outputs/dashboard_v2/dashboard.js
outputs/dashboard_v2/design_notes.md
outputs/dashboard_v2/data_validation_report.md
miaoda_bundle/manifest.json
miaoda_bundle/data/
miaoda_bundle/migrations/001_create_voc_tables.sql
miaoda_bundle/docs/
miaoda_bundle/dashboard/
miaoda_bundle_multichannel/manifest.json
miaoda_bundle_multichannel/data/voc_review.csv
miaoda_bundle_multichannel/data/voc_source_coverage.csv
miaoda_bundle_multichannel/data/voc_issue.csv
miaoda_bundle_multichannel/data/voc_action.csv
miaoda_bundle_multichannel/data/voc_marketing_insight.csv
state/last_success.json
```

If required sources are incomplete, mark the run `Partial`, suppress unsupported trend or prevalence claims, and keep remediation actions explicit.

## Completion check

- Confirm every requested product/source pair has `Complete`, `Zero Confirmed`, `Partial`, `Blocked`, or `Not Configured`.
- Confirm raw hashes match the manifest and every normalized row traces to a raw file and source URL.
- Confirm product, variant, and bundle mapping status is explicit.
- Confirm duplicate and version histories are preserved.
- Reconcile counts across CSV, index, workbook, Markdown, and HTML.
- Verify the HTML and every XLSX sheet visually before delivery.
- Verify every Miaoda bundle SHA-256, ensure reviewer names are absent, and keep evidence-managed fields separate from Miaoda-owned workflow fields.
