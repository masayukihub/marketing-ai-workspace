# 能力地图

本 Skill 将原先多个入口整合为一个用户入口。旧名称只用于识别历史请求，不再要求用户逐个调用。

| 旧入口/说法 | 新模块 | 主要用途 | 标准输出 |
|---|---|---|---|
| 电商选品情报 | `SELECTION` | 判断品类、需求、竞争与进入机会 | Opportunity Decision |
| Amazon Keyword Miner | `KEYWORD` | 发现关键词、意图与页面位置 | Keyword Map |
| Amazon Competitor Reviews | `COMPETITOR` + `VOC` | 从竞品评论识别购买驱动、痛点与空位 | Competitor VOC Map |
| Amazon VOC Browser Scraper | `VOC` | 在合规边界内采集可见评论并形成证据包 | VOC Evidence Pack |
| Amazon Listing Asset Capture | `ASSET_CAPTURE` | 盘点页面模块、图片角色和可见素材 | Asset/Module Inventory |

## 路由原则

- 用户问“值不值得做/卖什么”时，从 `SELECTION` 开始。
- 用户问“用户搜什么/页面写什么词”时，使用 `KEYWORD`。
- 用户问“竞品怎么卖/差评是什么”时，组合 `COMPETITOR + VOC`。
- 用户只要抓取评价时，运行 `VOC`，但仍输出覆盖范围和限制。
- 用户要参考图、页面结构或素材清单时，运行 `ASSET_CAPTURE`。
- 用户要完整新品研究时，使用 `FULL`，推荐顺序为：

```text
SELECTION → KEYWORD → COMPETITOR → VOC → ASSET_CAPTURE → SYNTHESIS
```

顺序可根据已有证据调整，但最终必须统一到同一产品、市场、渠道和时间范围。
