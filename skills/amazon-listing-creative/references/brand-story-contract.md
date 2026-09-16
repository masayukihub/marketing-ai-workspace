# Brand Story Contract

Brand Story 是独立页面角色，不等于 Gallery 最后一张，也不等于把产品卖点重新写一遍。

## 1. 三层品牌信息

### Brand Promise

回答：品牌希望为消费者带来什么长期价值？

必须来自当前正式品牌资料或已接受项目 Decision。没有来源时保持 `Pending Verification`，不要自动生成企业使命、市场地位或规模 Claim。

### Product Philosophy

回答：这个产品为什么符合品牌做产品的方式？

它可以更接近当前产品，例如“减少空间占用但不牺牲核心使用体验”，但不能冒充公司级品牌使命。

### Ecosystem / Trust

回答：用户为什么相信品牌，以及购买本产品后能与什么已确认生态连接。

只使用已确认：

- App / Automation 能力；
- 同品牌可关联产品；
- 已批准服务、支持或生态事实；
- 已批准品牌信任证据。

不得自行加入 No.1、奖项、用户数量、覆盖国家数、媒体评价等未批准内容。

## 2. Brand Story Brief

每次至少输出：

```yaml
brand_story:
  brand_promise:
  brand_role:
  product_philosophy:
  why_this_product_fits_brand:
  ecosystem_connection:
  trust_evidence:
  cross_sell_products:
  consumer_takeaway:
  visual_direction:
  prohibited_claims:
```

## 3. 与 Product Story 的边界

Product Story 负责：

- 产品是什么；
- 为什么值得买；
- 机制与 Proof；
- 适配与异议。

Brand Story 负责：

- 品牌长期角色；
- 产品哲学；
- 生态与信任；
- 同品牌关系。

如果 Brand Story 的 H1 只是把产品 Hero Copy 换一种说法，则判定为 `BRAND_STORY_DUPLICATES_PRODUCT_STORY`。

## 4. Visual Direction

优先使用：

- 产品与品牌系统的关系；
- 家庭生活中的品牌角色；
- 已确认生态设备；
- 品牌统一的材质、空间、色彩与信息节奏。

避免：

- 纯 Logo 墙；
- 空泛“未来生活”画面；
- 没有来源的全球规模/权威感；
- 与产品 A+ 完全相同的 Hero 构图。

## 5. Cross-sell

Cross-sell 产品必须：

1. 来自当前 Product Knowledge / 正式项目 Source；
2. 与当前用户购买场景有逻辑关系；
3. 不用过期 SKU、停产产品或未确认新品；
4. 不因为视觉上好看就添加。

## 6. Review Gate

Brand Story 在交付前检查：

- Brand Promise 是否有正式来源；
- Product Philosophy 是否与 Corporate Brand Message 混淆；
- 是否重复产品主卖点；
- Ecosystem 是否真实；
- Cross-sell 是否当前有效；
- 文案是否过度抽象；
- Visual 是否体现品牌，而不是只有 Logo。
