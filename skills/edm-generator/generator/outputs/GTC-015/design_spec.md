# GTC-015 Design Spec

Status: **BLOCKED_FOR_PRODUCTION**  
Production: **BLOCKED until current Product Knowledge, Claim, Price, destination, and real asset provenance are resolved.**

## Campaign Brief

- Theme: 多个产品的生态关系理解
- Primary Objective: `ecosystem_relationship_understanding`
- Primary Message: 複数製品の関係性を理解できるようにする
- Campaign Family: `TF-BRAND`
- Template: `TPL-BRAND-B`

## Module Sequence

1. `MOD-HERO-LIFESTYLE` — 用完成态或使用场景建立欲望，同时保留清楚的产品识别与主任务。
   - Message: 複数製品の関係性を理解できるようにする
   - Priority: required
   - Density: medium
2. `MOD-STORY-IMAGE-TEXT` — 用一张证明型图像与一个短解释回答单一问题。
   - Message: Section transition serving the Primary Objective
   - Priority: required
   - Density: medium
3. `MOD-STORY-APP-UI` — 解释已确认 App 界面、联动或控制流程，不重构 UI。
   - Message: Product evidence — Requires Claim Check
   - Priority: recommended
   - Density: medium
4. `MOD-COMMERCE-PRODUCT-GRID` — 在已有 Category / Theme Context 后，用一致卡片帮助浏览多个 SKU。
   - Message: Section transition serving the Primary Objective
   - Priority: required
   - Density: high
5. `MOD-TRUST-WARRANTY` — 说明已确认的保修、配送、退换或服务边界，消除购买阻碍。
   - Message: Trust proof — source required
   - Priority: recommended
   - Density: medium
6. `MOD-CONV-CTA-BAND` — 在完成必要理解后提供一个明确主行动。
   - Message: 詳細を確認する
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
