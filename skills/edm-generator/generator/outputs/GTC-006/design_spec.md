# GTC-006 Design Spec

Status: **BLOCKED_FOR_PRODUCTION**  
Production: **BLOCKED until current Product Knowledge, Claim, Price, destination, and real asset provenance are resolved.**

## Campaign Brief

- Theme: 活动最终提醒
- Primary Objective: `deadline_driven_conversion`
- Primary Message: 確認済みの終了時点と次の行動を明確に伝える
- Campaign Family: `TF-PROMOTION`
- Template: `TPL-PROMO-C`

## Module Sequence

1. `MOD-HERO-PROMOTION` — 在一个活动主命题下传达真实优惠或截止信息，并提供明确行动入口。
   - Message: 確認済みの終了時点と次の行動を明確に伝える
   - Priority: required
   - Density: medium
2. `MOD-COMMERCE-OFFER-BAND` — 用一条紧凑区域概括 Campaign Benefit、Deal 与期间，不重复整张价格卡。
   - Message: Promotion fact — verified source required
   - Priority: required
   - Density: medium
3. `MOD-COMMERCE-PRODUCT-GRID` — 在已有 Category / Theme Context 后，用一致卡片帮助浏览多个 SKU。
   - Message: Section transition serving the Primary Objective
   - Priority: recommended
   - Density: high
4. `MOD-COMMERCE-COUPON` — 说明真实 Coupon 的金额、领取/使用方式、期限与条件。
   - Message: Promotion fact — verified source required
   - Priority: recommended
   - Density: high
5. `MOD-CONV-LAST-CHANCE` — 在邮件末段重复一次真实截止信息与主 CTA，不新增主命题。
   - Message: Promotion fact — verified source required
   - Priority: required
   - Density: medium
6. `MOD-SYSTEM-LEGAL-FOOTER` — 承载优惠条件、法务说明、来源限定与必要免责。
   - Message: Brand, legal, and destination closure
   - Priority: required
   - Density: medium
7. `MOD-SYSTEM-BRAND-FOOTER` — 以品牌、必要链接与退订/管理入口结束邮件，不引入新 Campaign Message。
   - Message: Brand, legal, and destination closure
   - Priority: required
   - Density: low

## Desktop Contract

- Content width baseline: `600px` from `R-DESKTOP-001`.
- Preserve one dominant reading path and semantic order.
- Product, Proof, and Primary CTA form an intelligible task; no fixed Hero height ratio is invented.

## Mobile Contract

- Reflow by semantic order, not Desktop coordinates.
- Preserve product aspect ratio and recognizability; destructive crop is prohibited.
- `390px` is an Experimental QA viewport and cannot block Production by itself.
- Renderer behavior is intentionally not implemented in Phase 4.

## Visual Rhythm

- Explain-only deviations: None
- Experimental rules remain advisory.
