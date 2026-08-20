# Decision Journey Architecture

## 固定七阶段

| Order | Stage ID | 用户决策 | 用户问题 | 商品图任务 | A+ 深化任务 |
|---:|---|---|---|---|---|
| 1 | `understand_product` | 理解产品 | 这是什么，包含什么？ | 合规主图与品类识别 | Product definition、内容物、使用前提 |
| 2 | `spark_interest` | 产生兴趣 | 为什么值得继续看？ | 唯一 Hero Benefit | 理想结果、Hero Story、问题张力 |
| 3 | `understand_advantage` | 理解核心优势 | 它为什么更好用？ | 核心机制或优势 | How it works、Supporting values、机制证明 |
| 4 | `see_real_scenario` | 看到真实场景 | 在我的生活里怎么用？ | 一个真实日本生活瞬间 | 多场景、一天旅程、人物/空间适配 |
| 5 | `build_trust` | 相信产品 | 有什么证据？ | Technical Proof / Ecosystem | 数据条件、结构、材料、兼容与证据来源 |
| 6 | `check_fit` | 判断适不适合自己 | 适合我的家、设备和习惯吗？ | 尺寸、兼容、适用范围 | Setup、Requirements、Product Family Comparison |
| 7 | `remove_objections` | 消除购买顾虑 | 会不会买错、装不了或不好用？ | In-box、限制、Support、FAQ | FAQ、限制、安装、退货风险与最后确认 |

## 7 张商品图规则

1. `IMAGE-01` 必须是白底主图，实际销售内容、无营销文字、无虚假配件。平台和类目规则以当次官方核验为准。
2. `IMAGE-02` 只讲唯一 Hero Benefit。
3. `IMAGE-03` 解释核心优势或机制，不做 Feature 拼盘。
4. `IMAGE-04` 展示一个能让日本消费者代入的真实场景。
5. `IMAGE-05` 展示 Proof；没有证据时显示验证缺口，不用装饰性数字。
6. `IMAGE-06` 回答 Fit，包括兼容、尺寸、环境、前置设备或适合谁。
7. `IMAGE-07` 处理最后顾虑，包括安装、内容物、限制、支持或 FAQ。

每张必须有一个主信息、一个 User Question 和一个前后关系。Supporting Features 放入 A+、FAQ、规格或 Comparison，不因为数量多而挤进副图。

## A+ Story Units 与 Module 规则

Visual Unit 是独立的信息与素材需求，不等于 Amazon 后台的 Module，也不等于一个 Feature。

下表是内容检查维度，不是张数配额：

| Stage | 必须回答的问题 | 可用表达 |
|---|---|---|
| 理解产品 | 是什么、包含什么 | Hero、Category、In-box |
| 产生兴趣 | 为什么继续看 | Problem、Outcome、Hero Story |
| 理解优势 | 如何做到 | Mechanism、Core Benefit、Feature Detail |
| 真实场景 | 生活如何改变 | Lifestyle、One Day、Family/User Moment |
| 建立信任 | 凭什么相信 | Technical Proof、Data、Ecosystem、材料/结构 |
| 判断适配 | 是否适合自己 | Compatibility、Requirements、Setup、Comparison |
| 消除顾虑 | 会不会买错 | FAQ、Limitations、Support、Brand/After-sales |

把所需内容单元组合进 5–8 个实际 Module，优先混合 Full-width Hero、50/50 Feature、Three Feature Grid、Lifestyle、Technical Proof、Comparison 与 FAQ。目标是完整购买故事，不是凑 15 张图。Module 名称仅为候选；在当前 Seller Central Builder 中确认后再定稿。

## 副图与 A+ 的深度分工

```text
副图：What + Why now + 快速证据 + 关键适配
A+：Why + How + Scenario + Proof conditions + Comparison + Objection
```

禁止将 `IMAGE-02/03/04` 的标题、正文和构图原样复制到 A+。允许围绕同一 Hero Value 深化，但必须增加机制、情境、证据条件或适用边界。

## 节奏检查

- 相邻两张图不能使用同一版式和同一主 Message。
- 连续两个 A+ Module 不能都是 Full-width Banner。
- 至少一个视觉单元使用真实 Lifestyle、一个展示 Proof、一个明确 Fit、一个处理 Limitation。
- Hero Story 在页面中保持一致，但不要每屏重复同一句话。
