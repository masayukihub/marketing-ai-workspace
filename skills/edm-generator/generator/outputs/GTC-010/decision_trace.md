# GTC-010 Decision Trace

- Campaign Family: `TF-EDUCATION`
- Confidence: `0.98`
- Selected Template: `TPL-EDU-B`
- Alternative: `TPL-EDU-A`
- Status: `selected`

## Why

- VSR-EDU-B: campaign_type + primary_objective exact match
- product_count=1
- promotion_level=none
- required_assets=complete

## Campaign Classification Reasons

- Campaign Type 与冻结枚举完全匹配
- Primary Objective 命中 VSR-EDU-B
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

- Structure fingerprint: `d362edbf221eaed37f459a84195e1c6cc9d1fc9615986b11aa2b95eba3491568`
- Same input + same sources: `PASS`

This trace reads the frozen v1.0 selection matrix. It does not use Tier D to override SwitchBot family boundaries.
