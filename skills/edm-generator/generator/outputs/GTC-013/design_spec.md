# GTC-013 Design Spec

Status: **BLOCKED_FOR_PRODUCTION**  
Production: **BLOCKED until current Product Knowledge, Claim, Price, destination, and real asset provenance are resolved.**

## Campaign Brief

- Theme: 当前 SKU 购买选择
- Primary Objective: `multi_product_choice_decision`
- Primary Message: 現在の候補から自分に合う製品を選べるようにする
- Campaign Family: `TF-CATEGORY`
- Template: `TPL-CATEGORY-B`

## Module Sequence

1. `MOD-HERO-EDITORIAL` — 用编辑命题引导 Product Education、Guide 或 Brand Story，不在首屏堆积价格。
   - Message: 現在の候補から自分に合う製品を選べるようにする
   - Priority: required
   - Density: medium
2. `MOD-COMMERCE-COMPARISON` — 用同口径字段帮助用户选择产品或方案。
   - Message: Section transition serving the Primary Objective
   - Priority: required
   - Density: high
3. `MOD-COMMERCE-PRODUCT-GRID` — 在已有 Category / Theme Context 后，用一致卡片帮助浏览多个 SKU。
   - Message: Section transition serving the Primary Objective
   - Priority: required
   - Density: high
4. `MOD-STORY-PRODUCT-DETAIL` — 展示结构、接口、配件或安装细节，支持购买判断。
   - Message: Product evidence — Requires Claim Check
   - Priority: recommended
   - Density: medium
5. `MOD-STORY-FAQ` — 集中回答 3–6 个真实购买或使用阻碍，避免把长说明塞入 Hero。
   - Message: Section transition serving the Primary Objective
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
