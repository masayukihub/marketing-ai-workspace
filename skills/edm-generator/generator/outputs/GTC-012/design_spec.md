# GTC-012 Design Spec

Status: **BLOCKED_FOR_PRODUCTION**  
Production: **BLOCKED until current Product Knowledge, Claim, Price, destination, and real asset provenance are resolved.**

## Campaign Brief

- Theme: Security 产品入口
- Primary Objective: `category_context_and_product_discovery`
- Primary Message: カテゴリーの入口を示し、複数製品の発見へつなぐ
- Campaign Family: `TF-CATEGORY`
- Template: `TPL-CATEGORY-A`

## Module Sequence

1. `MOD-HERO-MULTI` — 用一个主题连接多个产品，并为后续 Product Grid 建立分类上下文。
   - Message: カテゴリーの入口を示し、複数製品の発見へつなぐ
   - Priority: required
   - Density: medium
2. `MOD-STORY-IMAGE-TEXT` — 用一张证明型图像与一个短解释回答单一问题。
   - Message: Section transition serving the Primary Objective
   - Priority: required
   - Density: medium
3. `MOD-COMMERCE-PRODUCT-GRID` — 在已有 Category / Theme Context 后，用一致卡片帮助浏览多个 SKU。
   - Message: Section transition serving the Primary Objective
   - Priority: required
   - Density: high
4. `MOD-COMMERCE-COMPARISON` — 用同口径字段帮助用户选择产品或方案。
   - Message: Section transition serving the Primary Objective
   - Priority: recommended
   - Density: high
5. `MOD-TRUST-WARRANTY` — 说明已确认的保修、配送、退换或服务边界，消除购买阻碍。
   - Message: Trust proof — source required
   - Priority: recommended
   - Density: medium
6. `MOD-CONV-CTA-BAND` — 在完成必要理解后提供一个明确主行动。
   - Message: 製品を比較・確認する
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
