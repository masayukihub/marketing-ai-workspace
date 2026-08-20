# GTC-005 Decision Trace

- Campaign Family: `TF-PROMOTION`
- Confidence: `0.98`
- Selected Template: `TPL-PROMO-B`
- Alternative: `TPL-PROMO-A`
- Status: `selected`

## Why

- VSR-PROMO-B: campaign_type + primary_objective exact match
- product_count=4
- promotion_level=high
- required_assets=complete

## Campaign Classification Reasons

- Campaign Type 与冻结枚举完全匹配
- Primary Objective 命中 VSR-PROMO-B
- 不允许跨 Campaign Family 由分数覆盖

## Rejected Candidates

- `TPL-LAUNCH-A` — 冻结 Campaign Family 边界：不可跨 Family 反向覆盖
- `TPL-LAUNCH-B` — 冻结 Campaign Family 边界：不可跨 Family 反向覆盖
- `TPL-LAUNCH-C` — 冻结 Campaign Family 边界：不可跨 Family 反向覆盖
- `TPL-PROMO-A` — Primary Objective 不匹配
- `TPL-PROMO-C` — Primary Objective 不匹配
- `TPL-CONVERT-A` — 冻结 Campaign Family 边界：不可跨 Family 反向覆盖
- `TPL-CONVERT-B` — 冻结 Campaign Family 边界：不可跨 Family 反向覆盖
- `TPL-EDU-A` — 冻结 Campaign Family 边界：不可跨 Family 反向覆盖

## Determinism

- Structure fingerprint: `fad2e48494dbea625754967b548bb528a1b2893918f48b7c03044fc6f879a745`
- Same input + same sources: `PASS`

This trace reads the frozen v1.0 selection matrix. It does not use Tier D to override SwitchBot family boundaries.
