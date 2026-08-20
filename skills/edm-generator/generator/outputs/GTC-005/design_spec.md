# GTC-005 Design Spec

Status: **BLOCKED_FOR_PRODUCTION**  
Production: **BLOCKED until current Product Knowledge, Claim, Price, destination, and real asset provenance are resolved.**

## Campaign Brief

- Theme: Robot Vacuum 主题优惠
- Primary Objective: `multi_product_offer_discovery`
- Primary Message: 複数製品の対象オファーを比較しやすく提示する
- Campaign Family: `TF-PROMOTION`
- Template: `TPL-PROMO-B`

## Module Sequence

1. `MOD-HERO-MULTI` — 用一个主题连接多个产品，并为后续 Product Grid 建立分类上下文。
   - Message: 複数製品の対象オファーを比較しやすく提示する
   - Priority: required
   - Density: medium
2. `MOD-COMMERCE-OFFER-BAND` — 用一条紧凑区域概括 Campaign Benefit、Deal 与期间，不重复整张价格卡。
   - Message: Promotion fact — verified source required
   - Priority: recommended
   - Density: medium
3. `MOD-COMMERCE-PRODUCT-GRID` — 在已有 Category / Theme Context 后，用一致卡片帮助浏览多个 SKU。
   - Message: Section transition serving the Primary Objective
   - Priority: required
   - Density: high
4. `MOD-COMMERCE-PRICE` — 清楚呈现一个 SKU 的已验证价格、参考价、优惠与条件。
   - Message: Promotion fact — verified source required
   - Priority: recommended
   - Density: high
5. `MOD-TRUST-WARRANTY` — 说明已确认的保修、配送、退换或服务边界，消除购买阻碍。
   - Message: Trust proof — source required
   - Priority: recommended
   - Density: medium
6. `MOD-CONV-CTA-BAND` — 在完成必要理解后提供一个明确主行动。
   - Message: 対象内容を確認する
   - Priority: required
   - Density: low
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
