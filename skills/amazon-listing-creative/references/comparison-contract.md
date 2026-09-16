# Comparison Contract

Amazon 页面中的“比较”必须区分内部竞品研究和可发布的同品牌选型，不能混为同一张表。

## 1. Internal Competitor Matrix

用途：

- 找 Category Trade-off；
- 找差异化；
- 找 VOC / Objection；
- 找 Positioning 与 Creative Opportunity；
- 验证消费者为什么会选当前产品。

允许比较竞争品牌，但所有数据必须有来源、日期和适用 SKU。

默认状态：

```text
INTERNAL_ONLY
NOT_PUBLISHABLE_AS_AMAZON_A_PLUS
```

禁止：

- 直接复制竞品图片、文案、Trade Dress；
- 为了突出己方产品选择性漏项；
- 未验证价格、评分、销量、No.1、认证和性能；
- 将内部分析表直接当成 Amazon 发布资产。

## 2. Publishable Series Comparison

目的：帮助用户在同品牌产品、Variant 或 Bundle 之间做选择。

优先顺序：

1. `Recommended For` — 适合谁；
2. `Home / Usage Fit` — 适合什么住宅或场景；
3. `Key Differentiator` — 为什么选它；
4. 再展示尺寸、清洁方式、Station、维护、连接等已确认规格。

规格表不是比较的起点。用户应该先能回答：

> “我应该买哪一个？”

再阅读参数差异。

## 3. Publishability Gate

每个比较对象必须有：

```yaml
product_id:
product_name:
brand:
variant_or_bundle:
source:
source_date:
status:
publishability:
```

默认只允许：

```text
SAME_BRAND_CONFIRMED_PRODUCT
```

进入正式发布表。

以下保持内部使用：

- 竞争品牌；
- 未确认新品；
- 过期或停产状态不明产品；
- 数据冲突产品；
- 缺少正式名称或关键规格来源的产品。

如当前 Amazon 政策、账户模块能力或法务规则要求更严格，以最新已验证规则为准。

## 4. Decision-oriented Matrix

推荐结构：

| Decision Dimension | User Meaning | Current Product | Alternative A | Alternative B |
|---|---|---|---|---|
| Recommended For | 谁最适合 | | | |
| Home / Usage Fit | 住宅 / 场景 | | | |
| Key Differentiator | 为什么选 | | | |
| Body Size | 放置 / 通行 | | | |
| Cleaning Method | 清洁方式 | | | |
| Station / Maintenance | 维护负担 | | | |
| Other Confirmed Dimension | 用户实际差异 | | | |

不要为了“表格完整”加入与购买决策无关的参数。

## 5. Copy Rules

推荐：

- 「省スペース重視の方に」
- 「家具が多い住まいに」
- 「水拭きを重視したい方に」

前提是这些推荐有事实和产品定位依据。

避免：

- 「圧倒的に優れる」
- 「他社より最強」
- 「No.1」
- 未经验证的竞品贬低式表达。

## 6. Review Gate

比较区交付前检查：

- Internal / Publishable 是否明确分开；
- 发布表是否只包含允许对象；
- 每个字段是否有当前来源；
- 首屏是否帮助选型；
- 是否机械堆参数；
- 是否存在过期价格/Claim；
- Mobile 下是否仍可横向或堆叠阅读；
- 当前产品是否因列顺序、缺失项或文案获得不真实优势。
