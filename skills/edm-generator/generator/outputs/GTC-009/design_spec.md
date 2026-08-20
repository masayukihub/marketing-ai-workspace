# GTC-009 Design Spec

Status: **BLOCKED_FOR_PRODUCTION**  
Production: **BLOCKED until current Product Knowledge, Claim, Price, destination, and real asset provenance are resolved.**

## Campaign Brief

- Theme: 问题理解与解决路径
- Primary Objective: `problem_and_solution_understanding`
- Primary Message: 課題と解決の考え方を順序立てて理解できるようにする
- Campaign Family: `TF-EDUCATION`
- Template: `TPL-EDU-A`

## Module Sequence

1. `MOD-HERO-EDITORIAL` — 用编辑命题引导 Product Education、Guide 或 Brand Story，不在首屏堆积价格。
   - Message: 課題と解決の考え方を順序立てて理解できるようにする
   - Priority: required
   - Density: medium
2. `MOD-STORY-PROBLEM` — 让用户识别一个具体问题或使用阻碍，为产品答案建立必要语境。
   - Message: Consumer problem context
   - Priority: required
   - Density: medium
3. `MOD-STORY-PRIMARY-USP` — 展开一个主 USP：用户利益、已确认能力与可信证据。
   - Message: Primary USP — Requires Claim Check
   - Priority: required
   - Density: medium
4. `MOD-STORY-IMAGE-TEXT` — 用一张证明型图像与一个短解释回答单一问题。
   - Message: Section transition serving the Primary Objective
   - Priority: recommended
   - Density: medium
5. `MOD-STORY-PRODUCT-DETAIL` — 展示结构、接口、配件或安装细节，支持购买判断。
   - Message: Product evidence — Requires Claim Check
   - Priority: required
   - Density: medium
6. `MOD-STORY-FAQ` — 集中回答 3–6 个真实购买或使用阻碍，避免把长说明塞入 Hero。
   - Message: Section transition serving the Primary Objective
   - Priority: recommended
   - Density: medium
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
