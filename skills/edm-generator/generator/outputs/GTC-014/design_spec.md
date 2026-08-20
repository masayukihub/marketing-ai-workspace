# GTC-014 Design Spec

Status: **BLOCKED_FOR_PRODUCTION**  
Production: **BLOCKED until current Product Knowledge, Claim, Price, destination, and real asset provenance are resolved.**

## Campaign Brief

- Theme: 品牌长期价值与观点
- Primary Objective: `brand_meaning_and_trust`
- Primary Message: ブランドの考え方と信頼の根拠を一つの物語で伝える
- Campaign Family: `TF-BRAND`
- Template: `TPL-BRAND-A`

## Module Sequence

1. `MOD-HERO-EDITORIAL` — 用编辑命题引导 Product Education、Guide 或 Brand Story，不在首屏堆积价格。
   - Message: ブランドの考え方と信頼の根拠を一つの物語で伝える
   - Priority: required
   - Density: medium
2. `MOD-STORY-IMAGE-TEXT` — 用一张证明型图像与一个短解释回答单一问题。
   - Message: Section transition serving the Primary Objective
   - Priority: required
   - Density: medium
3. `MOD-STORY-LIFESTYLE` — 在正文中把已确认能力放回真实生活场景，缓冲高密度事实模块。
   - Message: Section transition serving the Primary Objective
   - Priority: recommended
   - Density: low
4. `MOD-TRUST-USER-VOICE` — 按使用场景或产品整理真实用户语言，帮助理解实际价值。
   - Message: Trust proof — source required
   - Priority: recommended
   - Density: medium
5. `MOD-TRUST-AWARD` — 用当前有效 Award 或媒体证据支撑信任，不替代产品事实。
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
