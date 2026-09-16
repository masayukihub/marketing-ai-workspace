# Mode Contracts

本 Skill 是 `jp-commerce-content-flow` 的内部创意方法。完整页面生产仍由主入口负责；本文件只定义创意子任务的输入与交付边界。

## 1. Page Creative System

适用：完整日亚页面、Gallery + A+、Brand Story、Series Comparison、FAQ 或整页重构的策略阶段。

必须先完成：

```text
Fact Lock
→ Why This Product Exists
→ Consumer Decision Questions
→ Page Story Spine
→ Gallery / A+ / Brand / Comparison / FAQ 分工
→ Page Unit Handoff
```

输入：

- Product Truth / Approved Claim / Forbidden Claim；
- Target User / Scenario / Positioning；
- 当前 Gallery / A+ / Brand Story / Comparison；
- 官方产品素材与品牌规范；
- Commerce Insight Handoff（如有）；
- 当前渠道与账户模块能力（已验证时）。

交付：

- Why This Product Exists；
- Page Story Map；
- Gallery / A+ 分工；
- Brand Story Brief；
- Comparison Mode 与 Series Comparison Matrix；
- FAQ / Objection Map；
- 每个 Page Unit 的 Message / Proof / Asset / Native Field；
- Copy ↔ Visual Fidelity Target；
- Blocker / Pending Verification。

不得：

- 用 Feature 数量机械决定模块数量；
- 把竞品研究表直接当成可发布 Comparison；
- 把 Brand Story 当成产品卖点重复区；
- 把 Page Plan 声称为已渲染页面。

## 2. Listing Set

适用：Gallery 图片组策略、旧套图重构、图片顺序与角色规划。

先继承 Page Story 中属于 Gallery 的购买问题；若没有 Page Story 且任务只要求 Gallery，可建立最小 Story Spine。

交付：

- Gallery Role Map；
- 每张图的 Audience Question / One Message / Benefit / Evidence；
- 候选视觉方向与 Top Recommendation；
- 每张图的 Copy / Visual Proof Target；
- 顺序、重复检查与 Mobile Thumbnail 风险。

具体图片数量从已批准 Spec / Handoff 读取；不得固定要求 9 张。

## 3. A+/EBC 9-Grid

只在用户明确要求九宫格或一个信息点的多方向探索时使用。

输入：一个明确的 Message / Benefit / Evidence。

输出：9 个概念上真正不同的方向，区别必须来自故事、构图、视觉机制、Proof 或用户体验，不是只换颜色、背景、角度。

九宫格不是完整 EBC，也不是九个 A+ Module。

## 4. Direction Deep Dive

适用：用户已经选定一个方向，需要制作单张可执行 Brief。

锁定：

- One Message；
- Benefit；
- Evidence；
- Product / SKU；
- 不可改变产品特征。

输出：

- Art Direction；
- Composition；
- Visual Proof；
- H1 / Support Copy；
- Copy ↔ Visual Fidelity Target；
- AI Scene Prompt；
- Official Product Overlay；
- Manual QA。

不要重新打开其它方向。

## 5. Local Revision

适用：用户明确指定一张图、一个模块、某段文案或某个视觉元素进行修改。

先列：

```text
Locked
Change Requested
Affected Evidence
Affected Assets
```

只修改受影响范围。

如果局部修改导致：

- Claim 改变；
- Page Story 改变；
- Comparison Publishability 改变；
- Brand Promise 改变；
- Product / SKU 改变；

则停止在相应 Human Gate，不以“局部修改”为由越权。

## 6. Comparison Mode

### Internal Competitor Matrix

- 可跨品牌；
- 只用于 Strategy / Positioning / VOC / Creative Opportunity；
- 默认 `INTERNAL_ONLY`；
- 不直接成为 Amazon 发布资产。

### Publishable Series Comparison

- 默认同品牌；
- 每个产品/Variant 必须有正式 Source；
- 优先 Recommended For / Usage Fit / Key Differentiator，再展示规格；
- 当前平台/账户规则未验证时标 `Pending Verification`。

## 7. Brand Story Mode

Brand Story 必须至少区分：

```text
Brand Promise
Product Philosophy
Why This Product Fits Brand
Ecosystem / Trust
```

没有正式品牌 Source 时，不生成 No.1、用户规模、奖项、全球覆盖、媒体背书等 Claim。

## 8. Copy ↔ Visual Fidelity Gate

生产与 Whole-set Review 必须评估：

- Copy supported by visual；
- Proof visible without copy；
- Visual introduces new claim；
- Mobile proof visibility。

Gate：`PASS / WEAK / FAIL`。

Mechanism / Evidence Asset 为 WEAK 时必须返工；FAIL 不得进入 Whole-set Approval。
