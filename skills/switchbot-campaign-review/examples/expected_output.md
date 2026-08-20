# Expected Example Output

## Feishu/source-registry mode

- `manifest.json` records the snapshot batch, analysis cutoff, registry fingerprint, source status, retrieval method, row/column counts, raw/normalized files, normalized SHA-256 values, and a combined content fingerprint.
- `fetch_log.md` records every attempted method and fallback without credentials.
- `source_integrity_report.md` distinguishes Complete, Complete with Warnings, Partial, Failed, Permission Required, and Unverified sources.
- Formal analysis reads only `snapshots/<batch>/normalized/`; live Feishu pages are not re-read during `--analyze-only`.
- `full_analysis.md` and `report.html` include a Data Snapshot section. Required incomplete sources also appear in Data Limitations and lower confidence.

Run the full pipeline against the two `sample_*_campaign_data.csv` files with
`--campaign-name "Prime Day"`. A materially different requested campaign name
must be flagged as a Critical identity conflict and must block period/channel comparisons.

## Expected inventory and cleaning

- Two CSV sources are inventoried.
- Thirteen normalized detail rows remain: four rows for 2024, four for 2025, and five for 2026.
- One exact duplicate KOL row is excluded.
- One `Total` row is excluded.
- `Notes` is retained as an `extra__notes` field and listed as unmapped.
- Explicit values such as `1.16%` are normalized to `0.0116`.
- Original CSV files remain unchanged.
- Without a validated Product Knowledge index or complete exact product mapping, the run completes with `partial` status, omits product rollups, and records a Critical product-verification limitation. Overall and channel analysis still completes.

## Expected current-period metrics

| Metric | Expected |
|---|---:|
| Current period | 2026 |
| Comparison period | 2025 |
| Spend | 825000 |
| Revenue | 1370000 |
| Conversions | 1720 |
| Clicks | 55800 |
| Impressions | 6800000 |
| CTR | 0.0082058824 |
| CVR | 0.0308243728 |
| ROAS | 1.6606060606 |

## Expected analytical behavior

- Overall ROAS is recalculated from total Revenue / total Spend.
- Current-period row dates span multiple days while each historical period is represented by one date; the pipeline flags the date granularity as non-comparable instead of presenting a confident YoY.
- Google Ads has a positive Revenue-contribution-minus-Spend-share gap, but its multi-day current data versus single-date historical data blocks the YoY; the budget decision is downgraded to `Continue Testing` with low confidence rather than expanded automatically.
- YouTube is evaluated as Brand / Video rather than on direct ROAS alone.
- KOL uses views and cost per view in addition to tracked revenue.
- EDM uses delivery and click-rate evidence.
- Three comparable periods allow a trend classification; a single YoY comparison is not called a long-term trend. The overall example path is withheld because its date coverage is not comparable, while channels with three comparable observations may still receive a trend label.
- Monotonic CPC, CPM, and CPA declines are classified as sustained improvement even when one interval changes by less than 5%.
- The `zh-CN` management report uses Chinese section headings and display labels while keeping stable English CSV schemas.
- Data Limitations includes role-specific measurement gaps for Brand / Video, KOL, and CRM.
- The cross-period Spend/Revenue chart is omitted when the comparison is blocked by date coverage or another material scope conflict.
- Budget guidance uses an absolute budget index (`1.00` = current budget) so “Slightly Increase” cannot conflict with a normalized scenario share.
- The action plan includes the Product Knowledge data-quality fix, confirmation of ambiguous data issues, a controlled Google Ads comparability test, and the supported KOL action.
- Important report statements use Fact, Insight, Hypothesis, Recommendation, Data Gap, or Risk labels.

## Expected files

`executive_summary.md`, `full_analysis.md`, `data_quality_report.md`, `cleaned_data.xlsx`, `channel_evaluation.csv`, `trend_analysis.csv`, `action_plan.csv`, `report.html`, at least three PNG charts, and auditable `_intermediate/` files.
