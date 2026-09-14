---
name: amazon-listing-creative
description: "Amazon Listing 内部创意模块：负责九宫格概念探索、单张深化、局部创意和生产提示词。用户直接请求完整日亚页面、Gallery 套图或 A+/EBC 成品时，必须先按完整范围转交 jp-commerce-content-flow；不得把 EBC 请求误路由为九宫格，也不得只交套图就结束。"
---

# Amazon Listing Creative

把产品事实转化为消费者能在 3 秒内理解的 Amazon 视觉销售故事。先锁定事实和唯一信息，再设计创意；不要用视觉想象补齐未知产品信息。

## Project context preflight

若用户指定现有项目，先使用 `project-context-resolver`，只读取 Amazon Context Package 返回的 Product Truth、Decision、Approved Claim、Visual Profile/Freeze 与 Asset。Manifest 只负责导航和 Gate，不替代 Fact Lock。

## 先路由，再创意（完整页面不得停在九宫格）

本模块是 `jp-commerce-content-flow` 的内部创意方法，不是第二套完整 Listing Runtime。
**EBC / A+ / A＋ / 商品紹介コンテンツ指完整页面内容时，不等于 A+/EBC 9-Grid。**

先从用户完整请求确认 `scope` 和 `intent`，而不是看到旧 Skill 名称就进入探索：

| 用户请求 | scope / intent | 执行方式 |
|---|---|---|
| 完整日亚页面、套图＋EBC、Gallery＋A+ | full / create | 转交 `$jp-commerce-content-flow`；Gallery 与 A+ 都是必交付范围 |
| 只生成/补齐 EBC、已有套图不要重做 | aplus / create 或 resume | 转交主入口；保留 Gallery 精确文件，只做 A+ 缺失项 |
| 只做套图、不做 A+ | gallery / create | 转交主入口；不擅自扩大到 EBC |
| 只出策划/Brief | 明确范围 / plan | PLAN_ONLY，不声称已出图 |
| 明确要求九宫格、九个创意方向 | concept / explore | 留在本模块，使用 9-Grid；不是 EBC 成品 |
| 深化一个已选方向 | concept / deep_dive | 留在本模块，使用 Direction Deep Dive |
| 修改指定页面/文件 | 明确范围 / revise | 主入口 LOCAL_REVISION；本模块仅处理受托的创意修改 |

规范化后运行 `python3 scripts/aplus_delivery.py route --scope <scope> --intent <intent>`（路径相对本 Skill）。它输出路由与 `required_outputs`，不调用图片服务，也不批准生产。**将该范围和 [A+ 生产交接契约](references/aplus-production-handoff.md) 一并交给主入口；不得只转交一句“调用主流程”。** 主入口仍负责 Product Truth、Runtime、人工 Gate、实际生产和 QA。

已批准 Handoff 时按正式状态继续生产；没有批准时只停在现有 Material Human Gate。委派到主入口后，不得又把完整请求反向路由回本模块形成循环。用户已要求“生成套图和 EBC”，无需再询问“是否还要生成 EBC”。

“逐张生产”是生产队列的粒度，不是每做完一张就结束整个任务。已完成 Gallery 也不能替代 A+ 完成。资源不足、素材/Claim/Runtime 缺失时，保留精确进度并单独报告 A+ 阻塞点；不重画已锁定套图。

以下创意步骤仅适用于主入口委派的探索/深化子任务；不能拿 9/10 个方向、提示词、缩略图板或模块清单当成完整 EBC 交付。样例中的 9 图不是固定平台数量；继承用户范围和已批准资产集合。

## 先确定创意子任务模式

根据用户目标选择一种模式，并在输出开头说明：

1. **Listing Set（策略子任务）**：为主入口规划或重构 Listing 图片组策略。先生成 10 个候选视觉方向并推荐 Top 3，再把选定策略映射到图片 1–9。
2. **A+/EBC 9-Grid（仅明确要求探索时）**：为一个信息点生成 9 个真正不同的创意方向，并在用户需要时制作 3×3 探索板。
3. **Direction Deep Dive**：把用户选中的一个方向深化为完整单张 Brief、文案和生成提示词。
4. **Local Revision**：只修改用户指定的元素；其余事实、构图、产品外观、文案或风格保持锁定。

模式的详细输入和交付契约见 [mode-contracts.md](references/mode-contracts.md)。需要输出表格、单张 Brief、提示词或评分时，读取 [output-templates.md](references/output-templates.md)。

用户提供真实商品图参考、要求商业渲染/功能效果，或反馈“不是同一种图片”时，先读取 [商业画面制作](references/commercial-visual-production.md)。将画面类型、已查看参考、视觉证据、生产方法及代表图比较一并交接；先重开镜头与制作方法，不能只在原模板上增加箭头、水花和标签。

## 建立证据边界

1. 只把本次任务提供的产品资料、已读取的权威来源和用户确认内容当作事实。参考案例只能启发结构，不能成为产品事实或平台规则。
2. 记录每项关键内容的状态：`Confirmed`、`Pending Verification`、`Conflict`、`Unsupported` 或 `Not Applicable`。
3. 禁止虚构参数、尺寸、认证、测试结果、销量、评价、VOC、竞品差异、UI、功能、价格或促销。
4. 有冲突时并列记录来源和差异，不自行选择更有利的版本。缺失信息可以留占位符，不要补猜。
5. 若是 SwitchBot 日本市场产品，先查询 `codex_knowledge/knowledge_manifest.json` 的最小相关单元；产品事实缺失、过期、冲突或未批准时，调用 `product-knowledge` 并核对 canonical source。
6. 最终制作若依赖 Amazon 当前政策、尺寸或合规要求，查询 Amazon 官方最新规则。未验证时标记 `Pending Verification`，不要把示例经验写成现行规则。
7. 仅当缺少产品外观参考会使实际出图失真，或一个关键歧义会彻底改变结果时，集中询问一次；否则基于明确假设继续。

## 执行工作流

### 1. 盘点输入

检查并整理：产品名称与类别、目标市场、目标用户、价格或 Offer、页面位置、产品图、品牌规范、功能、机制、规格、证明、VOC、竞品、既有 Listing/A+、营销目标和限制。列出已确认资料与缺口。

读取所有用户指定的产品图片。识别 SKU、颜色、材质、比例、接口、配件和不可改变的外观特征；不要把相似型号混为一谈。

### 2. 完成 Fact Lock

先输出并锁定：

- 本张或本组的唯一信息点
- 最重要的用户 Benefit
- 支持 Benefit 的证据
- 用户应该记住的一句话
- 禁止出现的未确认内容

坚持 `One Image = One Message`。完整图片组可以有多个信息点，但每张图只能承担一个主任务。

### 3. 翻译价值

并行使用两条链路，最后只保留最有说服力的一条主 Benefit：

```text
Feature → Mechanism → User Pain → Functional Benefit → Emotional Benefit → Identity
Feature → Advantage → Benefit → Evidence
```

没有证据时，不要把形容词升级为可验证 Claim。把证据缺口显式标为 `Pending Verification`。

### 4. 定义销售故事

输出：

- 定位句：`For [target customer], [product] is a [category] that helps [benefit] through [unique mechanism].`
- Functional / Emotional / Social Job
- Hero Story：`从 ______ 到 ______` 或 `This product helps users ______ without ______.`

### 5. 探索不同方向

按所选模式生成 9 或 10 个方向。每个方向必须改变故事、构图、视觉母题、用户体验或信息表达机制；只换颜色、背景或机位不算新方向。

优先覆盖与产品相关的尺度感、真实使用瞬间、产品美感、类别差异、证据呈现和异议消除。不要为了凑数使用不适合产品的模板。

### 6. 组织图片角色

对 Listing Set 使用以下战略顺序；具体 Amazon 合规细节必须另行验证：

- Image 1：产品识别与点击意愿
- Image 2：最强购买理由 / Hero KV
- Image 3–6：功能、机制与证据
- Image 7–8：异议消除、适用边界或比较
- Image 9：品牌、生活方式或身份价值

避免重复卖点。每张图都要说明它在购买决策中的任务和与前后图片的关系。

### 7. 写文案和制作提示词

内部分析默认使用简体中文。面向日本市场的 H1、说明文案和 CTA 使用自然、简洁的日语；仅在用户要求时增加其他语言。

将画面生成与文字排版分开：

- 图片生成提示词优先描述产品参考、场景、构图、尺度、光线、材质和允许变化。
- 明确列出不可改变的产品结构、比例、颜色、SKU 特征和禁止生成内容。
- 长文案、精确 UI、参数表、认证标识和法律文字使用真实素材或后期叠加，不依赖生成模型直接渲染。
- 对每张图给出 H1、必要的短辅助文案和文字安全区；不要塞入长段正文。
- 先选场景动作、机理可视化或信息图，再按产品镜头安排文字；固定白顶栏、50/50 分栏或同一产品机位不是全套默认设计。

### 8. 生成实际视觉

用户已要求实际图片或 EBC 成品，即构成生成意图，但不替代现有 Handoff/素材/Claim 审批。完整生产由主入口执行。仅在明确的九宫格探索子任务中，逐张完成概念候选后再组合 3×3 探索板；不得把九宫格当成 A+ 页面。产品本体来自官方/批准素材，AI 仅处理允许的 Scene Layer；文字、UI 和技术标注独立排版。

实际生成后逐张检查产品结构、SKU、手部与场景物理关系、文案拼写、手机端可读性和九张之间的一致性。无法确认的视觉细节标记为 `Needs Manual QA`。

商业画面先完成当前类型的少量代表图，实际对照参考检查产品融合与作用过程，再扩展到其余授权范围。分层用于保真与编辑，不要求成片呈现为抠图、背景和外围标签三个割裂部分。内部结构缺证据时使用局部外部动作表达，不靠特效补造管路。

### 9. 评分并推荐

按需要评估：CTR Potential、Instant Understanding、Differentiation、Brand Premium、Amazon Suitability、Evidence Strength 和 Product Accuracy。给出 Top 3，并分别说明商业价值、主要优势、风险和需要验证的内容。

不要展示内部推理过程。输出简洁的评分、依据和结论。

## 质量门槛

交付前检查：

- 3 秒能否理解主 Benefit
- 是否只有一个主 Message
- Benefit 是否先于 Feature
- 画面是否真正证明而非只复述文案
- 是否有购买理由和异议消除
- 缩略图和手机端是否可读
- 各方向是否在概念上不同
- 品牌体系与产品外观是否一致
- 所有 Claim 是否有来源且状态正确
- 是否混入其他 SKU、历史项目或未经确认的信息

只有实际看过成片，才能给出带观察依据的视觉判断。方向预估、固定分数、文件/版式检查不能标成视觉通过。核心项有明确问题时先修订；产品准确性或事实合规不通过时，不得以平均分掩盖，直接标记 `Blocked` 或 `Pending Verification`。

## 迭代规则

- 用户“选择方向”时，只深化该方向，不重新发散。
- 用户“输出所有方向”时，分别生成完整 Brief；实际图片仍需逐张制作与 QA。
- 用户“修改”时，先列出锁定项和变更项，只改指定内容。
- 保留版本号与变更摘要，避免迭代时漂移产品外观、核心 Claim 或已批准文案。

## 完整交付防漏检

从本入口转交的成品请求，交付前必须按 [A+ 生产交接契约](references/aplus-production-handoff.md) 分别核对 Gallery 与 A+。使用兼容 `PRODUCT_PAGE_SPEC.json` 时运行 `scripts/aplus_delivery.py audit`，即使 renderer 中途报错也核对已落盘文件；保存原始错误，不能让文件检查覆盖原始失败。

检查器只确认约定图像文件/原生字段的产物覆盖，执行可用的图像解码检查，但不是 Browser QA、Claim 批准或 Publish Gate。完整 A+ 还必须完成模块装配、全部轮播页、Native Copy 和实际 Desktop/Mobile 浏览器检查。任何 A+ 缺口都必须在最终回答单独列出，不能只说“套图生成完成”。
