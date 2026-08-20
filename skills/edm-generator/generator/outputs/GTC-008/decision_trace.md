# GTC-008 Decision Trace

- Campaign Family: `TF-CONVERSION`
- Confidence: `0.98`
- Selected Template: `TPL-CONVERT-B`
- Alternative: `TPL-CONVERT-A`
- Status: `selected`

## Why

- VSR-CONVERT-B: campaign_type + primary_objective exact match
- product_count=1
- promotion_level=high
- required_assets=complete

## Campaign Classification Reasons

- Campaign Type 与冻结枚举完全匹配
- Primary Objective 命中 VSR-CONVERT-B
- 不允许跨 Campaign Family 由分数覆盖

## Rejected Candidates

- `TPL-LAUNCH-A` — 冻结 Campaign Family 边界：不可跨 Family 反向覆盖
- `TPL-LAUNCH-B` — 冻结 Campaign Family 边界：不可跨 Family 反向覆盖
- `TPL-LAUNCH-C` — 冻结 Campaign Family 边界：不可跨 Family 反向覆盖
- `TPL-PROMO-A` — 冻结 Campaign Family 边界：不可跨 Family 反向覆盖
- `TPL-PROMO-B` — 冻结 Campaign Family 边界：不可跨 Family 反向覆盖
- `TPL-PROMO-C` — 冻结 Campaign Family 边界：不可跨 Family 反向覆盖
- `TPL-CONVERT-A` — Primary Objective 不匹配
- `TPL-EDU-A` — 冻结 Campaign Family 边界：不可跨 Family 反向覆盖

## Determinism

- Structure fingerprint: `56735fd9f2e7c0f98b15bcc09f2429f8a1fdafd2ad2ef9aca2eae0e79395cf79`
- Same input + same sources: `PASS`

This trace reads the frozen v1.0 selection matrix. It does not use Tier D to override SwitchBot family boundaries.
