# Mode Contracts

## 目录

- [统一输入](#统一输入)
- [Mode 1 Listing Set](#mode-1-listing-set)
- [Mode 2 A+EBC 9-Grid](#mode-2-aebc-9-grid)
- [Mode 3 Direction Deep Dive](#mode-3-direction-deep-dive)
- [Mode 4 Local Revision](#mode-4-local-revision)
- [方向库](#方向库)

## 统一输入

接受结构化表格、自然语言、产品文档、图片或现有页面。先规范化为：

| 字段 | 要求 |
|---|---|
| Product Name / Category | 必填；区分具体 SKU |
| Target Market / Audience | 决定场景、文案语言与购买顾虑 |
| Placement | Main Image、Secondary Images、A+/EBC 或 Brand Store |
| Marketing Goal | CTR、理解、证明、异议消除或品牌提升 |
| Product Images | 记录角度、颜色、附件、型号和可用分辨率 |
| Brand Style | 色彩、字体、语气、禁用表达和参考视觉 |
| Features / Mechanisms | 分开记录功能与原理 |
| Specifications / Proof | 标注来源、日期、适用 SKU 与状态 |
| VOC | 保留原话、来源和样本边界；未提供则不得编造 |
| Competitors | 仅使用有来源的差异；未知时不做强比较 |
| Price / Offer | 记录市场、渠道、时间与是否需复核 |
| Existing Creative | 识别保留项、问题和可验证表现数据 |
| Constraints | 法务、平台、素材、时间、比例和输出限制 |

## Mode 1 Listing Set

用于从零规划或评审重构完整图片组。

### 阶段 A：策略

1. 完成 Fact Lock、定位、JTBD 和 Hero Story。
2. 生成 10 个候选视觉方向。每个方向包含 Core Idea、Visual Mechanism、Layout、Emotion、Platform Fit 和主要风险。
3. 按统一评分维度推荐 Top 3。不要仅用总分排序；Product Accuracy 或 Evidence Strength 不合格时淘汰。

### 阶段 B：图片组

将选定策略映射到 9 张图：

| Image | 决策任务 | 最小输出 |
|---:|---|---|
| 1 | 产品识别与 CTR | 产品呈现原则、背景/构图、合规待确认项 |
| 2 | 最强购买理由 | Hero message、视觉证明、H1 |
| 3 | 关键功能 1 | Feature → Benefit → Evidence |
| 4 | 关键功能 2 | Feature → Benefit → Evidence |
| 5 | 关键功能 3 或机制 | 可视化机制，不虚构内部结构 |
| 6 | 使用场景或范围 | 人物、空间、尺度和适用边界 |
| 7 | 异议消除 1 | 购买顾虑、回答、证据 |
| 8 | 异议消除 2 / 比较 | 只使用有来源的比较维度 |
| 9 | 品牌或生活方式 | 情绪、身份与品牌记忆 |

若产品信息不足，不强行填满 9 张：用 `Pending Verification` 占位，或建议合并重复内容。

## Mode 2 A+EBC 9-Grid

用于一个 EBC/A+ 信息点的创意探索，不等于最终生产稿。

1. 锁定一个 Message、一个 Benefit 和一个证据。
2. 生成 9 个概念上不同的方向。
3. 每个方向仅输出 Direction Name、Core Message、Visual Mother Idea、Hero Copy 和 Conversion Rationale。
4. 需要探索板时，为每个方向单独生成或准备画面，再排成 3×3。每格只保留编号、H1 和核心画面。
5. 九格使用同一品牌体系和同一 SKU；构图与母题必须不同。
6. 明确标注 `Concept Exploration — Not Final Artwork`。

## Mode 3 Direction Deep Dive

用于用户已选择方向后的单张执行方案。

交付：

1. Locked Fact / Message / Benefit / Evidence
2. Audience moment 与购买任务
3. 画面故事、主视觉、构图层级和视线顺序
4. 产品参考图及不可改变项
5. 人物、场景、道具、光线、材质与色彩
6. H1、辅助文案、必要免责声明及文字安全区
7. AI image prompt、negative constraints 与后期叠加清单
8. Product Accuracy / Evidence / Mobile Readability QA

## Mode 4 Local Revision

先建立变更控制表：

| 类型 | 内容 |
|---|---|
| Change | 用户明确要求修改的元素 |
| Lock | 必须保持不变的事实、产品、构图、文案或风格 |
| Dependency | 修改后必须同步检查的相关元素 |
| Risk | 可能引发的事实、可读性或平台风险 |

输出新版本号和简短 diff。不要借局部修改重新设计整套方案。

## 方向库

按产品与目标选用，不要机械覆盖全部：

1. Benefit Hero
2. Before / After
3. Process Flow
4. One Day Journey
5. JTBD Scene
6. Product Evolution
7. Category Redefinition
8. Outcome Comparison
9. Extreme Scenario
10. Lifestyle
11. Emotional Story
12. Invisible Technology
13. Future Vision
14. Metaphor
15. Data / Proof
16. Human Scale
17. Objection Removal
18. Product Beauty

使用 Before / After、Extreme Scenario、Comparison、Data / Proof 或 Invisible Technology 时，必须先确认画面和 Claim 均有证据支持。
