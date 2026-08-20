# GTC-007 Design Spec

Status: **BLOCKED_FOR_PRODUCTION**  
Production: **BLOCKED until current Product Knowledge, Claim, Price, destination, and real asset provenance are resolved.**

## Campaign Brief

- Theme: 单品价值与购买信任
- Primary Objective: `single_product_purchase_confidence`
- Primary Message: 単品の価値と根拠を順に示し、購入判断を支える
- Campaign Family: `TF-CONVERSION`
- Template: `TPL-CONVERT-A`

## Module Sequence

1. `MOD-HERO-PRODUCT` — 以官方产品本体作为首屏主要事实证据，完成产品身份、核心价值与主 CTA。
   - Message: 単品の価値と根拠を順に示し、購入判断を支える
   - Priority: required
   - Density: medium
2. `MOD-STORY-PRIMARY-USP` — 展开一个主 USP：用户利益、已确认能力与可信证据。
   - Message: Primary USP — Requires Claim Check
   - Priority: required
   - Density: medium
3. `MOD-STORY-PRODUCT-DETAIL` — 展示结构、接口、配件或安装细节，支持购买判断。
   - Message: Product evidence — Requires Claim Check
   - Priority: recommended
   - Density: medium
4. `MOD-STORY-FEATURE-SPLIT` — 用图文分栏解释一个 Feature 与其用户利益。
   - Message: Product evidence — Requires Claim Check
   - Priority: recommended
   - Density: medium
5. `MOD-TRUST-REVIEW` — 用真实、可追溯评价支撑一个具体购买理由。
   - Message: Trust proof — source required
   - Priority: required
   - Density: medium
6. `MOD-COMMERCE-PRICE` — 清楚呈现一个 SKU 的已验证价格、参考价、优惠与条件。
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
