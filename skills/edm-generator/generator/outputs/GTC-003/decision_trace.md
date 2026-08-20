# GTC-003 Decision Trace

- Campaign Family: `TF-LAUNCH`
- Confidence: `0.98`
- Selected Template: `TPL-LAUNCH-C`
- Alternative: `TPL-LAUNCH-A`
- Status: `selected`

## Why

- VSR-LAUNCH-C: campaign_type + primary_objective exact match
- product_count=1
- promotion_level=none
- required_assets=complete

## Campaign Classification Reasons

- Campaign Type 与冻结枚举完全匹配
- Primary Objective 命中 VSR-LAUNCH-C
- 不允许跨 Campaign Family 由分数覆盖

## Rejected Candidates

- `TPL-LAUNCH-A` — Primary Objective 不匹配
- `TPL-LAUNCH-B` — Primary Objective 不匹配
- `TPL-PROMO-A` — 冻结 Campaign Family 边界：不可跨 Family 反向覆盖
- `TPL-PROMO-B` — 冻结 Campaign Family 边界：不可跨 Family 反向覆盖
- `TPL-PROMO-C` — 冻结 Campaign Family 边界：不可跨 Family 反向覆盖
- `TPL-CONVERT-A` — 冻结 Campaign Family 边界：不可跨 Family 反向覆盖
- `TPL-CONVERT-B` — 冻结 Campaign Family 边界：不可跨 Family 反向覆盖
- `TPL-EDU-A` — 冻结 Campaign Family 边界：不可跨 Family 反向覆盖

## Determinism

- Structure fingerprint: `6ddab85157e56961d0fdce27eca242fda6d49768a01b677ce4dff57e2192105e`
- Same input + same sources: `PASS`

This trace reads the frozen v1.0 selection matrix. It does not use Tier D to override SwitchBot family boundaries.
