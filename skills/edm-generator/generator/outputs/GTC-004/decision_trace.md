# GTC-004 Decision Trace

- Campaign Family: `TF-PROMOTION`
- Confidence: `0.98`
- Selected Template: `TPL-PROMO-A`
- Alternative: `TPL-PROMO-B`
- Status: `selected`

## Why

- VSR-PROMO-A: campaign_type + primary_objective exact match
- product_count=3
- promotion_level=high
- required_assets=complete

## Campaign Classification Reasons

- Campaign Type 与冻结枚举完全匹配
- Primary Objective 命中 VSR-PROMO-A
- 不允许跨 Campaign Family 由分数覆盖

## Rejected Candidates

- `TPL-LAUNCH-A` — 冻结 Campaign Family 边界：不可跨 Family 反向覆盖
- `TPL-LAUNCH-B` — 冻结 Campaign Family 边界：不可跨 Family 反向覆盖
- `TPL-LAUNCH-C` — 冻结 Campaign Family 边界：不可跨 Family 反向覆盖
- `TPL-PROMO-B` — Primary Objective 不匹配
- `TPL-PROMO-C` — Primary Objective 不匹配
- `TPL-CONVERT-A` — 冻结 Campaign Family 边界：不可跨 Family 反向覆盖
- `TPL-CONVERT-B` — 冻结 Campaign Family 边界：不可跨 Family 反向覆盖
- `TPL-EDU-A` — 冻结 Campaign Family 边界：不可跨 Family 反向覆盖

## Determinism

- Structure fingerprint: `3aadfe698407d386fed527294dcfc53bfa6e91af27a9495542a801044347d5f3`
- Same input + same sources: `PASS`

This trace reads the frozen v1.0 selection matrix. It does not use Tier D to override SwitchBot family boundaries.
