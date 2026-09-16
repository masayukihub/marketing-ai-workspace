# Output Templates

## 目录

- [Fact Lock](#fact-lock)
- [Page Story Map](#page-story-map)
- [Brand Story Brief](#brand-story-brief)
- [Series Comparison Matrix](#series-comparison-matrix)
- [Copy Visual Fidelity](#copy-visual-fidelity)
- [候选方向](#候选方向)
- [Listing 图片 Brief](#listing-图片-brief)
- [九宫格方向矩阵](#九宫格方向矩阵)
- [单张深化](#单张深化)
- [AI 图片提示词](#ai-图片提示词)
- [评分与推荐](#评分与推荐)

只读取和使用当前模式需要的模板。删除空字段；未知信息保留状态，不要补猜。

## Fact Lock

```markdown
## Fact Lock

- Mode:
- Product / SKU:
- Target Market:
- Placement:
- One Message:
- Core Benefit:
- Evidence:
- Remember This:
- Confirmed Facts:
- Pending Verification:
- Conflict:
- Forbidden / Unsupported Claims:
```

## Page Story Map

```markdown
## Why This Product Exists

- Consumer Problem:
- Category Trade-off / Existing Alternative:
- Product Answer:
- Hero Promise:
- Proof Pillars:

## Page Story Spine

| # | Consumer Question | Page Unit | Story Role | Message | Proof | Asset / Native Field | Status |
|---:|---|---|---|---|---|---|---|
| 1 | What is it? | | | | | | |
| 2 | Why should I care? | | | | | | |
| 3 | Why is it different? | | | | | | |
| 4 | Can I believe it? | | | | | | |
| 5 | Is it for me? | | | | | | |
| 6 | Which one should I buy? | | | | | | |
| 7 | Why this brand? | | | | | | |
```

Page Unit 可使用 `Gallery`、`A+ Module`、`Carousel`、`Native Copy`、`Brand Story`、`Series Comparison`、`FAQ`。不是每个问题都必须独立占一个模块；重点是消费者问题被完整回答且不同单元不过度重复。

## Brand Story Brief

```markdown
## Brand Story Brief

- Brand Promise:
- Brand Role in Consumer Life:
- Product Philosophy:
- Why This Product Fits the Brand:
- Ecosystem Connection:
- Trust Evidence:
- Cross-sell Products:
- Consumer Takeaway:
- Visual Direction:
- Native Copy / CTA:
- Source / Approval Status:
- Prohibited / Unsupported Brand Claims:
```

Brand Promise、Product Philosophy 与当前产品卖点必须分开。没有正式 Source 时不得生成企业使命、No.1、奖项、规模、用户数量或生态覆盖 Claim。

## Series Comparison Matrix

```markdown
## Comparison Mode

- Mode: Internal Competitor Matrix / Publishable Series Comparison
- Publishability:
- Source Date:

| Decision Dimension | User Meaning | Current Product | Alternative A | Alternative B | Source | Status |
|---|---|---|---|---|---|---|
| Recommended For | | | | | | |
| Home / Usage Fit | | | | | | |
| Core Cleaning Method | | | | | | |
| Body Size / Placement | | | | | | |
| Station / Maintenance | | | | | | |
| Key Differentiator | | | | | | |
```

内部竞品矩阵允许跨品牌研究，但不得直接成为 Amazon 发布资产。正式 Series Comparison 默认只使用同品牌、已确认、渠道允许的产品/Variant。

## Copy Visual Fidelity

```markdown
## Copy ↔ Visual Fidelity

| Asset | H1 / Claim | Consumer Takeaway | Visual Proof | Proof Visible Without Copy | Visual Introduces New Claim | Mobile Proof Visible | Gate |
|---|---|---|---|---|---|---|---|
| | | | | Yes / Partial / No | Yes / No | Yes / Partial / No | PASS / WEAK / FAIL |
```

单个 Asset 详细字段：

```yaml
message:
copy_claim:
consumer_takeaway:
visual_proof:
  proof_object:
  proof_action:
  proof_visibility:
copy_role:
  headline:
  support:
  native_text:
render_role:
  scene:
  product:
  mechanism:
  evidence:
semantic_match:
  copy_supported_by_visual:
  visual_introduces_new_claim:
  proof_visible_without_copy:
mobile:
  readable:
  proof_visible:
gate: PASS | WEAK | FAIL
```

## 候选方向

```markdown
### Direction [ID] — [Name]

- Core Idea:
- Core Message:
- Visual Mother Idea:
- Visual Mechanism:
- Layout:
- Emotional Feeling:
- Platform Fit:
- Hero Copy:
- Conversion Rationale:
- Evidence Used:
- Risk / Pending Verification:
```

## Listing 图片 Brief

```markdown
## Image [ID] — [Role]

- Purpose:
- Audience Question:
- One Message:
- Benefit:
- Evidence:
- Visual Concept:
- Visual Proof:
- Key Visual Elements:
- Composition / Reading Order:
- Product Lock:
- H1:
- Support Copy:
- Text Safe Zone:
- Post-production Overlay:
- Copy-Visual Fidelity Target:
- Risk / Pending Verification:
- AI Image Prompt:
- Negative Constraints:
```

若用户要求多语言，按目标市场增加独立文案行，例如 `Copy — Japanese`。不要默认生成无关语言。

## 九宫格方向矩阵

```markdown
| # | Direction | Core Message | Visual Mother Idea | H1 | Why It Converts | Evidence / Risk |
|---:|---|---|---|---|---|---|
| 01 | | | | | | |
| 02 | | | | | | |
| 03 | | | | | | |
| 04 | | | | | | |
| 05 | | | | | | |
| 06 | | | | | | |
| 07 | | | | | | |
| 08 | | | | | | |
| 09 | | | | | | |
```

探索板每格只排编号、H1 和核心画面。不要把表格中的说明文字全部塞入图片。

## 单张深化

```markdown
## Direction Deep Dive — [Name]

### Locked Strategy
- One Message:
- Benefit:
- Evidence:
- Hero Story:

### Art Direction
- Audience Moment:
- Visual Story:
- Hero Object:
- Scene / Props:
- Composition:
- Camera / Lens Feel:
- Lighting:
- Color / Material:
- Brand Cues:

### Product Accuracy
- Reference Image(s):
- Immutable Features:
- Allowed Changes:
- Forbidden Changes:

### Copy & Visual Proof
- H1:
- Support Copy:
- Disclaimer:
- Visual Proof:
- Proof Visible Without Copy:
- Text Safe Zone:
- Mobile Thumbnail Check:
- Copy-Visual Fidelity Gate:

### Production
- AI Image Prompt:
- Negative Constraints:
- Real Asset Overlay:
- Manual QA:
```

## AI 图片提示词

优先使用结构化英文提示词承载视觉指令，把面向消费者的文案单独列出：

```text
Create a premium Amazon commerce key visual for [placement].

Product and reference:
- Product: [exact product and SKU]
- Use the attached reference image(s) as the source of truth.
- Preserve exactly: [shape, proportions, materials, colors, controls, ports, accessories].

Single message:
[one message]

Visual proof:
[how the scene visibly proves the benefit]

Scene and composition:
[setting, human moment, scale cue, foreground/background, camera, reading order, text safe zone]

Art direction:
[brand style, palette, lighting, realism, mood, aspect ratio]

Allowed changes:
[background, camera angle, lighting, approved props]

Do not:
- change the product design, SKU, proportions, materials, colors, controls, ports, or accessories
- invent functions, UI, measurements, certifications, awards, ratings, or comparative claims
- add unsupported text or logos
- distort hands, physical contact, scale, shadows, or reflections
- render long copy; reserve a clean text-safe area for post-production
```

若画面需要真实 UI、参数、图表、认证、包装文字或法律说明，将其列入 `Post-production Overlay`，并使用原始资产叠加。

## 评分与推荐

```markdown
| Direction | CTR Potential | Instant Understanding | Differentiation | Brand Premium | Amazon Suitability | Evidence Strength | Product Accuracy | Copy-Visual Fidelity | Gate |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---|
| | /10 | /10 | /10 | /10 | /10 | /10 | /10 | /10 | Pass / Revise / Blocked |
```

```markdown
## Top 3 Recommendation

### 1. [Direction]
- Why / Commercial Value:
- Main Strength:
- Risk:
- Verification Needed:
- Confidence: High / Medium / Low
```

评分只用于比较方向，不能替代事实门槛。`Product Accuracy`、`Evidence Strength` 或 `Copy-Visual Fidelity` 有硬伤时，Gate 必须为 `Blocked` 或 `Revise`。
