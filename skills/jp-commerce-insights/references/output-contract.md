# Commerce Insight Pack

## 最小结构

```yaml
pack_version: "1.0"
scope:
  market: JP
  channels: []
  product_or_category: ""
  variants: []
  decision: ""
  cutoff: ""
source_coverage: []
product_boundary:
  confirmed: []
  unknown: []
market_opportunity: {}
target_user: []
jobs_to_be_done: []
keyword_map: []
competitor_map: []
voc_themes: []
purchase_drivers: []
purchase_barriers: []
objections: []
claim_candidates: []
asset_inventory: []
asset_gaps: []
opportunities: []
risks: []
tests: []
creative_handoff: {}
need_confirmation: []
sources: []
```

## Creative Handoff

只传递下游制作需要的目标用户与场景、购买任务与矛盾、购买驱动和障碍、关键词意图、竞品表达空位、有证据的Proof机会、素材缺口、候选信息层级和禁止升级为事实的推测。

`claim_candidates` 不是 `approved_claims`。内容生成仍必须回到Product Truth确认。

## 用户可读摘要

默认用中文先给：

1. 一句话判断；
2. 最重要的5条证据结论；
3. 目标用户与购买场景；
4. 机会/风险；
5. 建议动作；
6. 数据限制；
7. 是否可进入内容制作。
