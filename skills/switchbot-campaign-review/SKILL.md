---
name: switchbot-campaign-review
description: "分析和复盘 SwitchBot 日本市场营销活动，支持飞书Base、电子表格、文档、Wiki、Excel、CSV、JSON和PDF表格。适用于Prime Day、Black Friday、新品、品牌活动、同比、渠道效率、预算调整和管理层报告。"
---
## 本地化与输出语言

- 默认用简体中文解释分析、过程、风险和建议。
- 面向日本市场的广告、PR、EDM、LP、SNS及其他对外文案，使用自然、简洁的日语。
- 保留平台名称、指标缩写、公式、代码、命令、文件名、API字段和工具参数的原文。
- 不因本地化改写事实、指标定义、权限边界或操作步骤。


# SwitchBot Campaign Review

Turn campaign files into an evidence-backed management review for SwitchBot Japan. Work as a Japan Marketing Director, Performance Marketing Lead, e-commerce analyst, data analyst, and Campaign Planner.

## Project context preflight

For a named existing project, run `project-context-resolver` before source intake. Consume only Campaign-scoped Project Memory, decisions, Product Truth, approved Claims, and assets. Write campaign artifacts first; propose durable results or risks to Project Memory instead of directly changing multiple Truth Sources.

## Inputs

- Identify the campaign, current and comparison periods, audience, requested deliverables, and whether budget advice is needed.
- Accept Feishu/Lark URLs, a `sources.yaml` registry, a project note containing Feishu links, or a local task directory.
- Use simplified Chinese for internal analysis unless the user requests another language. Write requested Japanese copy in natural Japanese marketing language.
- Make and record reasonable low-risk assumptions. Ask only when a missing choice would materially change the result.

## Workflow

1. Read [switchbot_business_context.md](references/switchbot_business_context.md) and [analysis_framework.md](references/analysis_framework.md).
2. If any Feishu/Lark link or source registry is present, read [feishu_source_intake.md](references/feishu_source_intake.md). Resolve all configured sources, capture a timestamped local snapshot, verify its manifest and integrity report, then analyze only the batch's `normalized/` directory. Do not request manual downloads until the automated CLI/API/export/browser paths fail.
3. When `$product-knowledge` is available and a populated product dimension exists, invoke it and load its generated `outputs/product_index.json`. Never infer a product from a fuzzy name match. If the companion skill or index is unavailable, continue the overall and channel review but omit product rollups and record the limitation.
4. Scan all supported snapshot/local files and every workbook sheet. Never stop at the first plausible file or sheet.
5. Read [data_quality_rules.md](references/data_quality_rules.md), then classify issues by fixability and decision impact. Preserve source files and snapshots.
6. Preserve the source product string as `product_raw`, resolve it exactly to `product_id`, and record unknown or one-to-many aliases as Critical issues. If the knowledge base is missing, its index is invalid, or any populated product remains unresolved, fail closed only for product-level analysis. Continue supported overall and channel analysis and record why product outputs were omitted. A source with no product dimension may continue as pure channel analysis and must record that product verification was not applicable.
7. Read [kpi_definitions.md](references/kpi_definitions.md), recalculate metrics from raw numerators and denominators, and reconcile totals.
8. Read [channel_evaluation_rules.md](references/channel_evaluation_rules.md) before evaluating channels. Do not apply a direct-ROAS standard to every channel.
9. Read [trend_analysis_rules.md](references/trend_analysis_rules.md) before YoY or multi-period claims. Separate scale, efficiency, mix, timing, and comparability.
10. State the overall conclusion first. Then present evidence, causes, impact, recommendations, and action owners.
11. Generate only supported artifacts. Explain every omitted artifact in Data Limitations.

## Run the Pipeline

From this skill directory, run:

```bash
python scripts/run_campaign_review.py \
  --sources <sources.yaml> \
  --output <output-directory>
```

For local files without Feishu intake, run:

```bash
python scripts/build_report.py \
  --input-dir <campaign-data-directory> \
  --campaign-name <campaign-name> \
  --output-dir <output-directory> \
  --language zh-CN
```

Before the first run, verify `requirements.txt` in an isolated Python environment. Do not modify the global Python installation; request approval if dependency installation needs network access.

Omit `--output-dir` to create `output/<campaign-slug>-<timestamp>/`. Use `--mapping-file` for explicit field mappings and `--current-period` or `--comparison-period` to override period selection. Add `--product-knowledge-dir <skill-directory>` when a validated Product Knowledge index is available.

Run individual stages only for diagnosis or partial regeneration:

- `scripts/parse_feishu_url.py`
- `scripts/create_source_snapshot.py`
- `scripts/fetch_feishu_bitable.py`
- `scripts/fetch_feishu_sheet.py`
- `scripts/export_feishu_document.py`
- `scripts/inspect_files.py`
- `scripts/clean_marketing_data.py`
- `scripts/calculate_metrics.py`
- `scripts/analyze_trends.py`
- `scripts/build_charts.py`

## Analysis Rules

- Use `[Fact]`, `[Insight]`, `[Hypothesis]`, `[Recommendation]`, `[Data Gap]`, and `[Risk]` on important conclusions.
- Never turn unavailable revenue, cost, non-unique matches, or invalid denominators into zero.
- Never form formal conclusions from a live Feishu page; trace them to a snapshot batch and cutoff.
- Compute overall ratios from summed numerators and denominators; never average channel ratios.
- Do not aggregate different currencies without supplied FX rates.
- Treat inconsistent tax bases, attribution windows, campaign durations, and conversion definitions as comparability limits.
- Call a change a sustained trend only with at least three comparable periods.
- For root causes, give evidence, plausible causes, alternative explanations, impact, validation method, and next action.
- For budget advice, consider scale, marginal efficiency, brand role, minimum effective spend, stability, and confidence—not historical ROAS rank alone.

## Outputs

Default user-facing outputs:

```text
output/<campaign-slug>-<timestamp>/
├── executive_summary.md
├── full_analysis.md
├── data_quality_report.md
├── cleaned_data.xlsx
├── channel_evaluation.csv
├── trend_analysis.csv
├── action_plan.csv
├── report.html
├── source_integrity_report.md
├── charts/
└── _intermediate/
```

Use templates in `templates/`. Keep `_intermediate/` auditable but do not present it as a final deliverable.

## Completion Check

- Confirm every file and sheet was inventoried.
- For Feishu inputs, confirm manifest completeness, retrieval cutoff, required-source status, and snapshot-only analysis.
- Reconcile core totals and weighted ratios.
- List concrete data-quality issues and unresolved mappings.
- Confirm `run_manifest.json` records campaign-identity verification plus the Product Knowledge path, index generation time, index validation status, product-resolution status, recognition rate, and unresolved product names.
- Separate Fact, Insight, Hypothesis, Recommendation, Data Gap, and Risk.
- Include overall, channel, period, and product detail where supported.
- Include executable actions with owner, timing, priority, and success metric.
- Verify CSV, XLSX, chart, and HTML outputs open successfully.
