# GTC-003 Design Spec

Status: **BLOCKED_FOR_PRODUCTION**  
Production: **BLOCKED until current Product Knowledge, Claim, Price, destination, and real asset provenance are resolved.**

## Campaign Brief

- Theme: 夏季生活场景
- Primary Objective: `new_product_desirability_in_context`
- Primary Message: 使用シーンから新品への関心を高める
- Campaign Family: `TF-LAUNCH`
- Template: `TPL-LAUNCH-C`

## Module Sequence

1. `MOD-HERO-LIFESTYLE` — 用完成态或使用场景建立欲望，同时保留清楚的产品识别与主任务。
   - Message: 使用シーンから新品への関心を高める
   - Priority: required
   - Density: medium
2. `MOD-STORY-PRODUCT-DETAIL` — 展示结构、接口、配件或安装细节，支持购买判断。
   - Message: Product evidence — Requires Claim Check
   - Priority: required
   - Density: medium
3. `MOD-STORY-LIFESTYLE` — 在正文中把已确认能力放回真实生活场景，缓冲高密度事实模块。
   - Message: Section transition serving the Primary Objective
   - Priority: recommended
   - Density: low
4. `MOD-STORY-FEATURE-ICONS` — 快速概览 3–6 个次级 Feature，不与 Primary USP 争夺层级。
   - Message: Product evidence — Requires Claim Check
   - Priority: recommended
   - Density: medium
5. `MOD-STORY-IMAGE-TEXT` — 用一张证明型图像与一个短解释回答单一问题。
   - Message: Section transition serving the Primary Objective
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
