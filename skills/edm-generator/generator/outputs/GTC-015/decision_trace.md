# GTC-015 Decision Trace

- Campaign Family: `TF-BRAND`
- Confidence: `0.98`
- Selected Template: `TPL-BRAND-B`
- Alternative: `TPL-BRAND-A`
- Status: `selected`

## Why

- VSR-BRAND-B: campaign_type + primary_objective exact match
- product_count=3
- promotion_level=none
- required_assets=complete

## Campaign Classification Reasons

- Campaign Type 与冻结枚举完全匹配
- Primary Objective 命中 VSR-BRAND-B
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

- Structure fingerprint: `0101079101421fc58cb1085542713d5371dfa149313bd4646fc04d9697e86a85`
- Same input + same sources: `PASS`

This trace reads the frozen v1.0 selection matrix. It does not use Tier D to override SwitchBot family boundaries.
