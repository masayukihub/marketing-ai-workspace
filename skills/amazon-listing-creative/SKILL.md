---
name: amazon-listing-creative
description: "Amazon Listing 内部创意模块：负责页面级故事框架、Gallery/A+创意策略、Brand Story、同品牌Series Comparison、单张深化、局部创意和生产提示词。用户直接请求完整日亚页面、Gallery 套图或 A+/EBC 成品时，必须先按完整范围转交 jp-commerce-content-flow；不得把 EBC 请求误路由为九宫格，也不得只交套图就结束。"
---

# Amazon Listing Creative

把产品事实转化为消费者能快速理解、比较并相信的 Amazon 视觉销售故事。先锁定事实与页面级购买问题，再设计 Gallery、A+、Brand Story、Series Comparison 与 FAQ 的分工；不要用视觉想象补齐未知产品信息。

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

规范化后运行 `python3 scripts/aplus_delivery.py route --scope <scope> --intent <intent>`（路径相对本 Skill）。它输出路由与 `required_outputs`，不调用图片服务，也不批准生产。将该范围和 [A+ 生产交接契约](references/aplus-production-handoff.md) 一并交给主入口；不得只转交一句“调用主流程”。主入口仍负责 Product Truth、Runtime、人工 Gate、实际生产和 QA。

已批准 Handoff 时按正式状态继续生产；没有批准时只停在现有 Material Human Gate。委派到主入口后，不得又把完整请求反向路由回本模块形成循环。用户已要求“生成套图和 EBC”，无需再询问“是否还要生成 EBC”。

“逐张生产”是生产队列的粒度，不是每做完一张就结束整个任务。已完成 Gallery 也不能替代 A+ 完成。资源不足、素材/Claim/Runtime 缺失时，保留精确进度并单独报告 A+ 阻塞点；不重画已锁定套图。

以下创意步骤仅适用于主入口委派的探索/深化子任务；不能拿 9/10 个方向、提示词、缩略图板或模块清单当成完整 EBC 交付。样例中的 9 图不是固定平台数量；继承用户范围和已批准资产集合。

## 先确定创意子任务模式

根据用户目标选择一种模式，并在输出开头说明：

1. **Page Creative System（页面策略子任务）**：先定义消费者决策问题、Why This Product Exists、Page Story Spine，再映射到 Gallery、A+、Brand Story、Series Comparison 与 FAQ。
2. **Listing Set（Gallery 策略子任务）**：为主入口规划或重构 Listing 图片组策略。先生成候选视觉方向，再把选定策略映射到图片角色；具体数量由已批准 Spec 决定。
3. **A+/EBC 9-Grid（仅明确要求探索时）**：为一个信息点生成 9 个真正不同的创意方向，并在用户需要时制作 3×3 探索板。
4. **Direction Deep Dive**：把用户选中的一个方向深化为完整单张 Brief、文案和生成提示词。
5. **Local Revision**：只修改用户指定的元素；其余事实、构图、产品外观、文案或风格保持锁定。

模式的详细输入和交付契约见 [mode-contracts.md](references/mode-contracts.md)。需要输出表格、单张 Brief、提示词或评分时，读取 [output-templates.md](references/output-templates.md)。页面级规划时必须读取 [page-story-framework.md](references/page-story-framework.md)；涉及品牌介绍时读取 [brand-story-contract.md](references/brand-story-contract.md)；涉及比较时读取 [comparison-contract.md](references/comparison-contract.md)；进入视觉生产或 Whole-set Review 时读取 [copy-visual-fidelity.md](references/copy-visual-fidelity.md)。

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

### 3. 定义 Why This Product Exists

完整页面、Listing Set 或 A+ 规划时，在进入图片角色之前先回答：

```text
Consumer Problem
→ Category Trade-off / Existing Alternative
→ Product Answer
→ Hero Promise
→ Proof Pillars
```

不要把“尺寸小、吸力大、功能多”直接当成页面故事。必须说明这些能力解决了什么现实矛盾，以及用户为什么现在需要这个产品。

结构化输出：

```yaml
product_tension:
consumer_problem:
category_tradeoff:
product_answer:
hero_promise:
proof_pillars:
```

详细规则见 [page-story-framework.md](references/page-story-framework.md)。

### 4. 建立 Page Story Spine

完整页面先按消费者决策问题设计，再映射平台内容单元：

1. **What is it?** — 产品识别与类别理解
2. **Why should I care?** — 最强购买理由 / Hero Promise
3. **Why is it different?** — 差异机制与可见证据
4. **Can I believe it?** — Proof、边界、真实使用方式
5. **Is it for me?** — 住宅、用户、适配条件与异议消除
6. **Which one should I buy?** — 同品牌 Series Comparison / 选型帮助
7. **Why this brand?** — Brand Promise、Product Philosophy、Ecosystem / Trust

再映射到：

```text
Gallery
A+ Module / Carousel / Native Copy
Brand Story
Series Comparison
FAQ
```

同一问题可以跨多个单元，但不得让 Gallery、A+、Brand Story 和 Comparison 机械重复同一句卖点。

### 5. 翻译价值

并行使用两条链路，最后只保留最有说服力的一条主 Benefit：

```text
Feature → Mechanism → User Pain → Functional Benefit → Emotional Benefit → Identity
Feature → Advantage → Benefit → Evidence
```

没有证据时，不要把形容词升级为可验证 Claim。把证据缺口显式标为 `Pending Verification`。

### 6. Brand Story 独立规划

Brand Story 不等于 Gallery 最后一张，也不等于重复产品卖点。使用 [brand-story-contract.md](references/brand-story-contract.md) 分层：

```text
Brand Promise
→ Brand Role
→ Product Philosophy
→ Why This Product Fits the Brand
→ Ecosystem / Trust
```

公司级品牌主张、当前产品哲学和生态/信任证据必须分开。无正式依据时不要生成抽象品牌 Claim。Cross-sell 产品必须来自当前正式 Product Knowledge；不从旧页面或竞品页面猜测。

### 7. Comparison 分成内部研究与可发布两层

使用 [comparison-contract.md](references/comparison-contract.md)：

- **Internal Competitor Matrix**：可比较竞争品牌，用于定位、差异、VOC 和购买障碍研究；不得直接作为 Amazon A+ 发布资产。
- **Publishable Series Comparison**：默认只比较同品牌、已确认且适合当前渠道的产品/Variant，用于帮助用户选型。

正式比较必须优先回答“适合谁 / 适合什么住宅 / 为什么选它”，再给规格。不得为了填满表格虚构竞品参数、价格、No.1 或优越性。

### 8. 探索不同方向

按所选模式生成 9 或 10 个方向。每个方向必须改变故事、构图、视觉母题、用户体验或信息表达机制；只换颜色、背景或机位不算新方向。

优先覆盖与产品相关的尺度感、真实使用瞬间、产品美感、类别差异、证据呈现和异议消除。不要为了凑数使用不适合产品的模板。

### 9. 组织图片角色

Gallery 的战略顺序由 Page Story 决定，常见角色可以包括：

- 产品识别与点击意愿
- Hero Promise / 最强购买理由
- 差异机制与 Proof
- 使用场景与适用条件
- 异议消除
- 同品牌选择帮助或品牌价值

具体数量、顺序和平台合规要求必须来自已批准 Spec / Handoff；不得固定机械要求 Image 1–9。

每张图都要说明它在购买决策中的任务、消费者问题以及与前后图片的关系。

### 10. 写文案和制作提示词

内部分析默认使用简体中文。面向日本市场的 H1、说明文案和 CTA 使用自然、简洁的日语；仅在用户要求时增加其他语言。

将画面生成与文字排版分开：

- 图片生成提示词优先描述产品参考、场景、构图、尺度、光线、材质和允许变化。
- 明确列出不可改变的产品结构、比例、颜色、SKU 特征和禁止生成内容。
- 长文案、精确 UI、参数表、认证标识和法律文字使用真实素材或后期叠加，不依赖生成模型直接渲染。
- 对每张图给出 H1、必要的短辅助文案和文字安全区；不要塞入长段正文。

### 11. 建立 Copy ↔ Visual Fidelity Contract

每个视觉 Asset 在生产前必须同时定义：

```yaml
message:
copy_claim:
consumer_takeaway:
visual_proof:
  proof_object:
  proof_action:
  proof_visibility:
copy_role:
render_role:
semantic_match:
  copy_supported_by_visual:
  visual_introduces_new_claim:
  proof_visible_without_copy:
mobile:
  readable:
  proof_visible:
```

核心原则：**Render 不能只是“把文案旁边放一张漂亮产品图”。** 对需要视觉证明的卖点，用户遮住文字后仍应大致理解 Benefit 或机制；否则必须标记 `WEAK` 或 `FAIL`。

Gate：

- `PASS`：Visual 与 Copy 同义，Proof 可见，未引入新 Claim。
- `WEAK`：Visual 仅装饰或辅助，主要依赖 Copy 才能理解。
- `FAIL`：Visual 与 Copy 语义不一致、Proof 不可见或视觉新增未批准 Claim。

详细规则见 [copy-visual-fidelity.md](references/copy-visual-fidelity.md)。

### 12. 生成实际视觉

用户已要求实际图片或 EBC 成品，即构成生成意图，但不替代现有 Handoff/素材/Claim 审批。完整生产由主入口执行。仅在明确的九宫格探索子任务中，逐张完成概念候选后再组合 3×3 探索板；不得把九宫格当成 A+ 页面。

正式组合遵循：

```text
Scene Layer（AI / Stock / Lifestyle）
+ Official Product Layer
+ Graphic / Approved Copy Layer
```

禁止 AI 生成、重画或改变正式产品本体、Logo、精确 UI、日文文字、参数表、认证标识或法律说明。消费者文案与数值优先程序化排版或使用已批准真实素材。

实际生成后逐张检查产品结构、SKU、手部与场景物理关系、文案拼写、手机端可读性、视觉 Proof 和全套节奏。无法确认的视觉细节标记为 `Needs Manual QA`。

### 13. Whole-set Review

除了传统的 Product Accuracy / Brand / Mobile QA，必须增加 Copy ↔ Render Fidelity Review：

| Asset | H1 / Claim | Visual Proof | Without Copy | Semantic Match | Gate |
|---|---|---|---|---|---|
| | | | Understandable / Partial / No | PASS / WEAK / FAIL | |

同时检查：

- Page Story 是否完整回答主要购买问题
- Gallery / A+ / Brand Story / Comparison 是否职责清楚且不过度重复
- Brand Promise 与 Product Philosophy 是否混淆
- Internal Competitor Matrix 是否误进入 Publishable Asset
- Comparison 是否帮助用户选择，而不是只罗列规格
- 文案是否超出画面可证明的范围
- Render 是否引入了文案中没有的新 Claim
- Mobile 缩小时主要 Proof 是否仍可见

### 14. 评分并推荐

按需要评估：CTR Potential、Instant Understanding、Differentiation、Brand Premium、Amazon Suitability、Evidence Strength、Product Accuracy 和 **Copy-Visual Fidelity**。给出 Top 3，并分别说明商业价值、主要优势、风险和需要验证的内容。

不要展示内部推理过程。输出简洁的评分、依据和结论。

## 质量门槛

交付前检查：

- 3 秒能否理解主 Benefit
- 是否回答明确的消费者购买问题
- 是否只有一个主 Message
- Benefit 是否先于 Feature
- 画面是否真正证明而非只复述文案
- Copy ↔ Visual Fidelity 是否为 PASS；WEAK 必须说明原因，FAIL 必须返工
- Brand Story 是否提供品牌意义而非重复产品卖点
- Comparison 是否区分内部竞品研究和可发布同品牌选型
- 是否有购买理由和异议消除
- 缩略图和手机端是否可读
- 各方向是否在概念上不同
- 品牌体系与产品外观是否一致
- 所有 Claim 是否有来源且状态正确
- 是否混入其他 SKU、历史项目或未经确认的信息

任一核心项低于 8/10 时先修订再交付。产品准确性、事实合规或 Copy-Visual Fidelity 为 FAIL 时，不得以平均分掩盖，直接标记 `Blocked` 或 `Pending Verification`。

## 迭代规则

- 用户“选择方向”时，只深化该方向，不重新发散。
- 用户“输出所有方向”时，分别生成完整 Brief；实际图片仍需逐张制作与 QA。
- 用户“修改”时，先列出锁定项和变更项，只改指定内容。
- 保留版本号与变更摘要，避免迭代时漂移产品外观、核心 Claim 或已批准文案。
- 页面级结构已批准后，局部资产返工不得重写 Brand Story、Comparison 或 Page Story Spine，除非变更确实影响这些部分。

## 完整交付防漏检

从本入口转交的成品请求，交付前必须按 [A+ 生产交接契约](references/aplus-production-handoff.md) 分别核对 Gallery、A+、Brand Story、Series Comparison 与必要 Native Copy。使用兼容 `PRODUCT_PAGE_SPEC.json` 时运行 `scripts/aplus_delivery.py audit`，即使 renderer 中途报错也核对已落盘文件；保存原始错误，不能让文件检查覆盖原始失败。

检查器只确认约定图像文件/原生字段的产物覆盖，执行可用的图像解码检查，但不是 Browser QA、Claim 批准或 Publish Gate。完整 A+ 还必须完成模块装配、全部轮播页、Native Copy、品牌/比较区绑定和实际 Desktop/Mobile 浏览器检查。任何缺口都必须在最终回答单独列出，不能只说“套图生成完成”。
