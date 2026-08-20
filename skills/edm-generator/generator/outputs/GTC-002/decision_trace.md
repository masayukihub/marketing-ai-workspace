# GTC-002 Decision Trace

- Campaign Family: `TF-LAUNCH`
- Confidence: `0.98`
- Selected Template: `TPL-LAUNCH-B`
- Alternative: `TPL-LAUNCH-A`
- Status: `selected`

## Why

- VSR-LAUNCH-B: campaign_type + primary_objective exact match
- product_count=1
- promotion_level=none
- required_assets=complete

## Campaign Classification Reasons

- Campaign Type 与冻结枚举完全匹配
- Primary Objective 命中 VSR-LAUNCH-B
- 不允许跨 Campaign Family 由分数覆盖

## Rejected Candidates

- `TPL-LAUNCH-A` — Primary Objective 不匹配
- `TPL-LAUNCH-C` — Primary Objective 不匹配
- `TPL-PROMO-A` — 冻结 Campaign Family 边界：不可跨 Family 反向覆盖
- `TPL-PROMO-B` — 冻结 Campaign Family 边界：不可跨 Family 反向覆盖
- `TPL-PROMO-C` — 冻结 Campaign Family 边界：不可跨 Family 反向覆盖
- `TPL-CONVERT-A` — 冻结 Campaign Family 边界：不可跨 Family 反向覆盖
- `TPL-CONVERT-B` — 冻结 Campaign Family 边界：不可跨 Family 反向覆盖
- `TPL-EDU-A` — 冻结 Campaign Family 边界：不可跨 Family 反向覆盖

## Determinism

- Structure fingerprint: `a60a6dbd41d664a1c62e0f06d133f8991870e62de426b28fe7f633a73fa33dcb`
- Same input + same sources: `PASS`

This trace reads the frozen v1.0 selection matrix. It does not use Tier D to override SwitchBot family boundaries.
