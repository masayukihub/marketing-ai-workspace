# GTC-004 Design Spec

Status: **BLOCKED_FOR_PRODUCTION**  
Production: **BLOCKED until current Product Knowledge, Claim, Price, destination, and real asset provenance are resolved.**

## Campaign Brief

- Theme: 夏季室内环境主题
- Primary Objective: `theme_relevance_then_offer_conversion`
- Primary Message: テーマとの関連を示した後、対象オファーへ案内する
- Campaign Family: `TF-PROMOTION`
- Template: `TPL-PROMO-A`

## Module Sequence

1. `MOD-HERO-PROMOTION` — 在一个活动主命题下传达真实优惠或截止信息，并提供明确行动入口。
   - Message: テーマとの関連を示した後、対象オファーへ案内する
   - Priority: required
   - Density: medium
2. `MOD-STORY-PROBLEM` — 让用户识别一个具体问题或使用阻碍，为产品答案建立必要语境。
   - Message: Consumer problem context
   - Priority: recommended
   - Density: medium
3. `MOD-COMMERCE-PRODUCT-GRID` — 在已有 Category / Theme Context 后，用一致卡片帮助浏览多个 SKU。
   - Message: Section transition serving the Primary Objective
   - Priority: required
   - Density: high
4. `MOD-COMMERCE-OFFER-BAND` — 用一条紧凑区域概括 Campaign Benefit、Deal 与期间，不重复整张价格卡。
   - Message: Promotion fact — verified source required
   - Priority: required
   - Density: medium
5. `MOD-TRUST-REVIEW` — 用真实、可追溯评价支撑一个具体购买理由。
   - Message: Trust proof — source required
   - Priority: recommended
   - Density: medium
6. `MOD-COMMERCE-COUPON` — 说明真实 Coupon 的金额、领取/使用方式、期限与条件。
   - Message: Promotion fact — verified source required
   - Priority: recommended
   - Density: high
7. `MOD-CONV-CTA-BAND` — 在完成必要理解后提供一个明确主行动。
   - Message: 詳細を確認する
   - Priority: required
   - Density: low
8. `MOD-SYSTEM-BRAND-FOOTER` — 以品牌、必要链接与退订/管理入口结束邮件，不引入新 Campaign Message。
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
