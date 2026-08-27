# 来源与证据规则

## 来源等级

1. `CANONICAL`：用户提供并确认的官方资料、Product Knowledge、平台官方规则。
2. `PRIMARY_PUBLIC`：品牌官网、当前Listing、官方公告、官方帮助文档。
3. `USER_VOICE`：可追溯的真实评论、问答、用户发布内容。
4. `MARKET_SIGNAL`：搜索趋势、关键词工具、排名、媒体或KOL内容。
5. `REFERENCE_ONLY`：竞品视觉、案例、设计灵感。

## 不可替代关系

- `USER_VOICE` 可说明用户表达，不可确认产品规格。
- `MARKET_SIGNAL` 可说明关注度，不可直接证明市场规模或销量。
- `REFERENCE_ONLY` 可启发结构，不可复制文案、图片、Trade Dress或完整布局。
- 竞品页面只能确认其当时可见表达，不能证明真实性能。

## 采集记录

每个批次至少记录：

- source_id
- source_type
- url
- market/channel
- product/variant
- retrieved_at
- requested_window
- observed_scope
- record_count
- coverage_status
- limitations

原始文本、截图和页面证据保持不可变；翻译、摘要、标签和建议作为派生字段保存。

## 评论与VOC

- 区分真实用户评价、KOL合作、PR、媒体转载和官方内容。
- 只在同一来源范围完成复查后判断内容是否删除。
- 评论星级和文本情绪分开保存。
- 保留样本量、时间、产品变体和抓取边界。
- 引用用户原话时使用最短必要片段，并保留来源链接。

## 当前性

价格、优惠、排名、评论数、关键词热度、平台规则和页面结构都会变化。使用这些信息时必须标记获取日期。无法确认当前状态时标记 `Unverified`。
