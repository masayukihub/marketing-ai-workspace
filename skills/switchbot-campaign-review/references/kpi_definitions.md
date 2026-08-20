# KPI Definitions

## Core formulas

| Metric | Formula | Required fields |
|---|---|---|
| CTR | Clicks / Impressions | Clicks, Impressions |
| CPC | Spend / Clicks | Spend, Clicks |
| CPM | Spend / Impressions × 1,000 | Spend, Impressions |
| CVR | Conversions / Clicks | Conversions, Clicks |
| CPA | Spend / Conversions | Spend, Conversions |
| ROAS | Revenue / Spend | Revenue, Spend |
| Budget Utilization | Spend / Budget | Spend, Budget |
| YoY | (Current - Previous) / Previous | Comparable current and previous values |

Return blank when the denominator is missing or zero. Do not manufacture infinity or zero.

## Aggregation

Calculate overall ratios from summed base values, such as `Overall CTR = SUM(Clicks) / SUM(Impressions)`. Never average row-level or channel-level ratios.

## Contribution and standardized efficiency

- Budget share = Channel Spend / Total Spend
- Impression contribution = Channel Impressions / Total Impressions
- Click contribution = Channel Clicks / Total Clicks
- Conversion contribution = Channel Conversions / Total Conversions
- Revenue contribution = Channel Revenue / Total Revenue
- Contribution gap = Result contribution - Spend share
- Impressions per ¥10,000 = Impressions / Spend × 10,000
- Clicks per ¥10,000 = Clicks / Spend × 10,000
- Conversions per ¥10,000 = Conversions / Spend × 10,000

Use the source currency in labels. Do not combine currencies without explicit FX rates and dates.

## Comparability

Before YoY, check duration, channel coverage, conversion definition, attribution window, tax basis, agency fees, currency, product mix, and source completeness. Mark non-comparable metrics as `Not Comparable`.
