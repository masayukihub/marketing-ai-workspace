# GTC-011 Decision Trace

- Campaign Family: `TF-EDUCATION`
- Confidence: `0.98`
- Selected Template: `TPL-EDU-C`
- Alternative: `TPL-EDU-A`
- Status: `selected`

## Why

- VSR-EDU-C: campaign_type + primary_objective exact match
- product_count=3
- promotion_level=none
- required_assets=complete

## Campaign Classification Reasons

- Campaign Type 与冻结枚举完全匹配
- Primary Objective 命中 VSR-EDU-C
- 不允许跨 Campaign Family 由分数覆盖

## Rejected Candidates

- `TPL-LAUNCH-A` — 冻结 Campaign Family 边界：不可跨 Family 反向覆盖
- `TPL-LAUNCH-B` — 冻结 Campaign Family 边界：不可跨 Family 反向覆盖
- `TPL-LAUNCH-C` — 冻结 Campaign Family 边界：不可跨 Family 反向覆盖
- `TPL-PROMO-A` — 冻结 Campaign Family 边界：不可跨 Family 反向覆盖
- `TPL-PROMO-B` — 冻结 Campaign Family 边界：不可跨 Family 反向覆盖
- `TPL-PROMO-C` — 冻结 Campaign Family 边界：不可跨 Family 反向覆盖
- `TPL-CONVERT-A` — 冻结 Campaign Family 边界：不可跨 Family 反向覆盖
- `TPL-CONVERT-B` — 冻结 Campaign Family 边界：不可跨 Family 反向覆盖

## Determinism

- Structure fingerprint: `d9d0ba4666e64dcf8b2690c4019075d64bfc283c550e64937c80ea3ed0e6d8f6`
- Same input + same sources: `PASS`

This trace reads the frozen v1.0 selection matrix. It does not use Tier D to override SwitchBot family boundaries.
