# EDM Visual Generator — Visual Rhythm Rules v1.0 (Phase 3 Review)

状态：**Human Review Required**  
基线：`standards/edm_design_rules_v1.0.yaml`  
用途：为 Template 与 Module 的组合提供节奏约束，避免机械拼装。本文不是 Renderer 的像素规范，不恢复已移除的 `R-SPACING-001`。

## 1. 节奏状态模型

每个 Module 在组合时至少标记五个状态：

| Axis | Allowed values | 说明 |
|---|---|---|
| surface_tone | `light` / `dark` / `neutral` | 明暗层，不代表固定品牌色 |
| layout_family | `full_width` / `split` / `grid` / `band` / `text` | 模块主结构 |
| subject | `product` / `lifestyle` / `proof` / `commerce` / `system` | 主要视觉或内容对象 |
| density | `low` / `medium` / `high` | 信息密度，只作组合诊断 |
| container | `plain` / `card` / `full_bleed` | 容器语法 |

Generator 先满足 v1.0 Hard Rules，再检查以下 Rhythm Defaults。违反 Rhythm Default 不直接 `BLOCKED`，但必须写出 Campaign、Product、Promotion 或 Content Requirement 原因。

## 2. Light / Dark Section Rhythm

- 默认使用 `light → neutral/dark → light` 的单一主转折；Dark 用于信息阶段变化，不用于装饰性隔段。
- 不连续放置两个 Dark Full-width Module。若确因 Night Scene 或产品视觉需要，第二段必须改变 `layout_family` 与 `density`，并记录原因。
- 高促销邮件也不得让整封邮件持续高对比。Promotion Hero 后至少在两个模块内回到 Light 或 Neutral Product/Proof 区域。
- Brand Story 可不使用 Dark；不强行为了“节奏”加入深色段。

**Recommended:** `Light Hero → Light Context → Dark Proof/Detail → Light Commerce → Neutral Footer`  
**Avoid:** `Dark Hero → Dark Feature → Dark Grid → Dark CTA`

## 3. Full-width / Split Rhythm

- `Split` 最多连续 2 次；第 2 次必须改变语义方向或信息重心，不能只机械左右翻转。
- 连续两个 Split 后，下一模块优先 `full_width`、`grid`、`band` 或 `text`。
- Full-width 模块不连续超过 2 个大型视觉段；否则插入短 Proof、Band 或结构化 Content。
- Mobile 以语义顺序堆叠，不因 Desktop 左右位置决定先后。`R-MOBILE-002` 仍为 Experimental。

**Recommended:** `Full Hero → Split USP → Full Product Detail → Grid Proof`  
**Avoid:** `50/50 Split → 50/50 Split → 50/50 Split`

## 4. Product / Lifestyle Rhythm

- Lifestyle 不得成为唯一产品证据；其前后至少一侧必须邻接 Product Detail、Primary USP、Product Grid 或可辨认 Product Hero。
- 连续两个 Product-only 模块后，下一模块优先 Lifestyle、Problem Context 或 Proof，避免“产品居中目录”感。
- 连续两个 Lifestyle 模块后，下一模块必须回到产品事实或可信 Proof。
- Promotion 邮件中的 Lifestyle 只负责主题/场景，不承担优惠事实。

**Recommended:** `Product Hero → USP → Lifestyle → Detail → Proof`  
**Avoid:** `Lifestyle Hero → Lifestyle Scene → Generic Lifestyle → CTA`

## 5. High-density / Low-density Rhythm

- High-density 最多连续 2 个模块；下一模块使用 Low 或 Medium Density，除非 Legal 条款必须紧邻。
- Product Grid、Comparison Table、Coupon/Price 组合视为 High-density 候选，不能三个连续。
- Low-density 不是“信息不足”：仍需回答一个完整消费者问题，并保留必要的产品/Proof/CTA 连接。
- 模块数量不是阻塞阈值；检查内容职责与密度交替，而不是追求固定段数。

**Recommended:** `High Grid → Medium Proof → Low Lifestyle → High Price/CTA`  
**Avoid:** `Grid → Comparison → Price Matrix → Coupon Matrix`

## 6. Text-heavy / Visual-heavy Rhythm

- 连续两个 Text-heavy 模块后，必须进入 Visual-heavy 或 Proof-led 模块。
- Visual-heavy 模块必须有可读 Caption/Headline，不能只有无法解释的图。
- Product Education 的长说明拆成问题、机制、Proof、FAQ；Hero 不承担步骤墙。
- Brand Story 允许较长正文，但每段仍遵守可扫描分章，并在两章内出现视觉或 Proof 停顿。

**Recommended:** `Editorial Hero → Text Context → Visual Explanation → FAQ → CTA`  
**Avoid:** `Long Intro → Long Feature Copy → Long FAQ → Legal Copy`

## 7. Card / Full Bleed Rhythm

- Card-dominant 模块最多连续 2 个；下一模块改为 Full Bleed、Split、Text 或 Band。
- Product Grid 必须保持卡片语法一致，不使用 Bento 式不规则 SKU span。
- 不使用 Card-in-card；Product Card 的 Price 与 CTA 属于同一层，不再套内层 Price Card。
- Full Bleed 只用于 Hero、Lifestyle 或明确阶段转换，不作为每段背景切换手段。

**Recommended:** `Full Bleed Hero → Plain USP → Card Grid → Full-width Proof → CTA Band`  
**Avoid:** `Card Grid → Card Proof → Card Price → Card CTA`

## 8. Cross-axis Combination Rules

1. 任意三个连续 Module，不得同时在 `layout_family`、`density`、`container` 三个 Axis 上完全相同。
2. 若连续两个 Module 同属 `split`，第 3 个必须改变结构；不能只交换图文左右。
3. 若连续两个 Module 都是 `high + card`，第 3 个必须是 `low/medium` 且 `plain/full_bleed/band`。
4. Promotion Hero 后不得立即出现完整 Price Card，除非 `primary_objective = offer_conversion`；否则先进入 Offer Band、Product Detail 或 Product Grid。
5. Product Grid 前必须存在 Category / Theme Context。
6. CTA Band 不连续出现；Closing CTA 之前应有 Product、Proof、Price 或 FAQ 中至少一个有效前置模块。
7. User Voice、Review、Award 必须有真实来源；缺少来源不是节奏偏差，而是 `R-CLAIM-001` Hard Failure。
8. 任何节奏规则都不能绕过 Asset、Claim、CTA、Primary Objective 与 QA Hard Rules。

## 9. Template Rhythm Profiles

| Family | Recommended rhythm | Main risk |
|---|---|---|
| Product Launch | Visual-heavy → Medium proof → Lifestyle pause → Commerce | 连续 Feature Split |
| Theme Promotion | High Hero → Context pause → High Grid → Proof → Closing action | 全程高密度、高促销 |
| Single Product Conversion | Product → USP/Detail → Proof → Price/CTA | 价格过早覆盖价值 |
| Product Education | Text question → Visual answer → Detail/FAQ → CTA | 文字墙或步骤塞进 Hero |
| Category / Multi-product | Context → Grid → Compare → Proof → CTA | Grid 前无分类语境 |
| Brand / Ecosystem Story | Editorial/Lifestyle → Text → Visual/System → Proof → CTA | 长文无章节、产品出场过晚 |

## 10. QA Checklist

- [ ] 没有连续 3 个同构 Module。
- [ ] 没有连续 3 个 High-density 或 Card-dominant Module。
- [ ] Lifestyle 邻接产品事实。
- [ ] Product Grid 前有 Category / Theme Context。
- [ ] Promotion Hero 与 Price Card 未无条件连续。
- [ ] CTA Band 未连续，目的地总数符合 `R-CTA-001`。
- [ ] Mobile 顺序按语义而非 Desktop 坐标。
- [ ] Experimental Rule 没有被当作 Blocking Constraint。
- [ ] 未冻结 Padding、Module Spacing 或 Hero Ratio 像素值。

## 11. Human Review Focus

请只决定以下六组节奏是否 `Keep / Modify / Merge / Remove`：

- `RHYTHM-LIGHT-DARK`
- `RHYTHM-FULL-SPLIT`
- `RHYTHM-PRODUCT-LIFESTYLE`
- `RHYTHM-DENSITY`
- `RHYTHM-TEXT-VISUAL`
- `RHYTHM-CARD-FULLBLEED`

Phase 3 Human Review 完成前，这些规则保持 `Review Required`；不得进入正式 Generator Skill。
