# GTC-001 Decision Trace

- Campaign Family: `TF-LAUNCH`
- Confidence: `0.98`
- Selected Template: `TPL-LAUNCH-A`
- Alternative: `TPL-LAUNCH-B`
- Status: `selected`

## Why

- VSR-LAUNCH-A: campaign_type + primary_objective exact match
- product_count=1
- promotion_level=none
- required_assets=complete

## Campaign Classification Reasons

- Campaign Type 与冻结枚举完全匹配
- Primary Objective 命中 VSR-LAUNCH-A
- 不允许跨 Campaign Family 由分数覆盖

## Rejected Candidates

- `TPL-LAUNCH-B` — Primary Objective 不匹配
- `TPL-LAUNCH-C` — Primary Objective 不匹配
- `TPL-PROMO-A` — 冻结 Campaign Family 边界：不可跨 Family 反向覆盖
- `TPL-PROMO-B` — 冻结 Campaign Family 边界：不可跨 Family 反向覆盖
- `TPL-PROMO-C` — 冻结 Campaign Family 边界：不可跨 Family 反向覆盖
- `TPL-CONVERT-A` — 冻结 Campaign Family 边界：不可跨 Family 反向覆盖
- `TPL-CONVERT-B` — 冻结 Campaign Family 边界：不可跨 Family 反向覆盖
- `TPL-EDU-A` — 冻结 Campaign Family 边界：不可跨 Family 反向覆盖

## Determinism

- Structure fingerprint: `0b6e161bbc38d1cf46e77cd37194ee0cc533108c6734be43139e44ca5e62d91d`
- Same input + same sources: `PASS`

This trace reads the frozen v1.0 selection matrix. It does not use Tier D to override SwitchBot family boundaries.
