# GTC-009 Decision Trace

- Campaign Family: `TF-EDUCATION`
- Confidence: `0.98`
- Selected Template: `TPL-EDU-A`
- Alternative: `TPL-EDU-B`
- Status: `selected`

## Why

- VSR-EDU-A: campaign_type + primary_objective exact match
- product_count=1
- promotion_level=none
- required_assets=complete

## Campaign Classification Reasons

- Campaign Type 与冻结枚举完全匹配
- Primary Objective 命中 VSR-EDU-A
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

- Structure fingerprint: `ec486ded6b6d2c9eb4185d9aa8ff7a7f934587fd112273eb00ab09d7c6682825`
- Same input + same sources: `PASS`

This trace reads the frozen v1.0 selection matrix. It does not use Tier D to override SwitchBot family boundaries.
