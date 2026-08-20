# GTC-010 Design Spec

Status: **BLOCKED_FOR_PRODUCTION**  
Production: **BLOCKED until current Product Knowledge, Claim, Price, destination, and real asset provenance are resolved.**

## Campaign Brief

- Theme: 机制与操作理解
- Primary Objective: `mechanism_or_setup_understanding`
- Primary Message: 仕組みまたは設定手順を視覚的に理解できるようにする
- Campaign Family: `TF-EDUCATION`
- Template: `TPL-EDU-B`

## Module Sequence

1. `MOD-HERO-PRODUCT` — 以官方产品本体作为首屏主要事实证据，完成产品身份、核心价值与主 CTA。
   - Message: 仕組みまたは設定手順を視覚的に理解できるようにする
   - Priority: required
   - Density: medium
2. `MOD-STORY-APP-UI` — 解释已确认 App 界面、联动或控制流程，不重构 UI。
   - Message: Product evidence — Requires Claim Check
   - Priority: required
   - Density: medium
3. `MOD-STORY-FEATURE-SPLIT` — 用图文分栏解释一个 Feature 与其用户利益。
   - Message: Product evidence — Requires Claim Check
   - Priority: recommended
   - Density: medium
4. `MOD-STORY-PRODUCT-DETAIL` — 展示结构、接口、配件或安装细节，支持购买判断。
   - Message: Product evidence — Requires Claim Check
   - Priority: required
   - Density: medium
5. `MOD-STORY-FAQ` — 集中回答 3–6 个真实购买或使用阻碍，避免把长说明塞入 Hero。
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
