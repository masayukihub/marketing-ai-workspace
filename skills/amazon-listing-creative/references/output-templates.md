# Output Templates

## 目录

- [Fact Lock](#fact-lock)
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
## Asset [Current Asset ID] — [Role]

- Purpose:
- Audience Question:
- One Message:
- Benefit:
- Evidence:
- Visual Concept:
- Key Visual Elements:
- Composition / Reading Order:
- Product Lock:
- H1:
- Support Copy:
- Text Safe Zone:
- Post-production Overlay:
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

### Copy & Layout
- H1:
- Support Copy:
- Disclaimer:
- Text Safe Zone:
- Mobile Thumbnail Check:

### Production
- AI Image Prompt:
- Negative Constraints:
- Real Asset Overlay:
- Manual QA:
```

## AI 图片提示词

正式产品素材与消费者文案保留在后期合成任务。以下 Prompt 只交给场景生成模型；先检查官方产品的机位能否与该场景匹配：

```text
Create only an environment layer for [placement and aspect ratio].

Scene and composition:
[specific space, restrained human action, material, scale cue, camera height,
perspective, contact surface, foreground/background, empty product insertion area,
empty text safe zone]

Art direction:
[approved palette, light direction, shadow direction, material, mood]

Allowed changes:
[environment and approved non-product props within the brief]

Do not:
- generate any product, logo, text, UI, technical diagram or supposed evidence
- invent functions, UI, measurements, certifications, awards, ratings, or comparative claims
- add unsupported text or logos
- distort hands, physical contact, scale, shadows, or reflections
- fill the reserved areas; product identity, proof and typography are composited later
```

若画面需要真实 UI、参数、图表、认证、包装文字或法律说明，将其列入 `Post-production Overlay`，并使用原始资产叠加。

## 评分与推荐

```markdown
| Direction | CTR Potential | Instant Understanding | Differentiation | Brand Premium | Amazon Suitability | Evidence Strength | Product Accuracy | Gate |
|---|---:|---:|---:|---:|---:|---:|---:|---|
| | /10 | /10 | /10 | /10 | /10 | /10 | /10 | Pass / Revise / Blocked |
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

此表仅用于有依据的方向比较，不要求填满分数。未看实际成图的维度填“未评估”，CTR 无实验数据时填“待验证假设”。单张修图直接写观察与修复。`Product Accuracy` 或 `Evidence Strength` 有硬伤时，不能靠平均分抵消。
