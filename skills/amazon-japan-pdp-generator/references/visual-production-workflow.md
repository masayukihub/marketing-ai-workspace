# Visual Production Workflow

本工作流属于 DESIGN/PRODUCE。KNOW 只建立 Product Brief；PLAN 只建立卖点矩阵、页面 Spec 与 Story Review。Story Gate 未批准时不得开始下面的视觉流程；Layout Gate 未批准时不得进入高保真与 Final。

## Non-negotiable sequence

Execute every product image and A+ module in this order:

```text
Selling Point
→ Page Role
→ Information Structure
→ Wireframe
→ Japanese Copy Review
→ Asset Selection
→ Product Layer Composite
→ Scene Layer Completion
→ Graphic Layer
→ Round 1
→ Visual Review
→ Round 2
→ Final QA
```

Do not move to final rendering while the Composition Sheet, Layout ID, information hierarchy, three copy options, product source, scene source and Claim source are incomplete.

## Composition gate

Create `visual_composition_plan.xlsx` before rendering. Include at least:

| Field | Required decision |
|---|---|
| Visual ID | Image or A+ Module |
| Role | The single purchase question it answers |
| Layout / Template | Product Layout MAIN/A–F or A+ SB-A01–SB-A08 |
| Headline | Selected Japanese Option |
| Sub Copy | One supporting benefit |
| Product Asset | User-provided official source |
| Scene Asset | Official, licensed or AI scene without a generated product |
| AI Needed | Yes / No plus allowed elements |
| Graphic Elements | Headline, proof, diagram, labels or comparison |
| Priority | Conversion and production priority |
| Claim Source / Risk / Status | Review gate |

## Three-layer production

1. `Product Layer`: only official product files. Preserve silhouette, proportion, color, material, Logo, button, port, screen, accessory, installation structure and real combination.
2. `Scene Layer`: official or licensed scene, or AI-generated Japanese home, person, pet, background, light, prop and empty composition space. Never ask AI to draw the SwitchBot product.
3. `Graphic Layer`: programmatic SVG/HTML/Canvas typography, icon, arrow, label, proof, diagram and comparison. Never ask an image model to draw Japanese copy.

Network images are visual references only unless commercial rights are confirmed.

## Two-round design

- Round 1: render the selected template with real assets and selected copy.
- Visual Review: check visual center, whitespace, hierarchy, Japanese line breaks, product scale/accuracy, scene dominance and five-second comprehension.
- Round 2: correct layout, scale, copy density and mobile safe area. Only Round 2 that passes QA enters `design/product_images/` or `design/aplus/`.
- Preserve Round 1 in `design/editable/round_01/` and editable Final SVG in `design/editable/final/`.

## Automatic rejection

Reject after Round 2 when any of these remain:

- no fixed Layout / Template ID;
- more than three information levels or more than four proof items;
- Headline over 28 Japanese characters without an approved exception;
- excessive supporting copy, broken Japanese wrapping or mobile unreadability;
- product too small, cropped, distorted, obscured or visually secondary;
- background competes with the product;
- product body is AI-generated, AI-redrawn or source is untraceable;
- user cannot state the image's one message within five seconds.

Design QA and Publish Gate are independent. A visual may pass design QA but remain `Blocked` because official user-provided assets or approved Claims are missing.

## Re-render rule

所有视觉都必须可从 `PRODUCT_PAGE_SPEC.json`、Asset Mapping 与实体模板包重建。修改 Headline、Sub Copy、Product Layer、Scene Layer、`template_id` 或顺序后重新渲染；不得只修 Flattened JPEG。局部变更必须生成 impact report，列出受影响的视觉、HTML、XLSX 与需要重新审核的 Gate。
