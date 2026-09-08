# 内部组件映射

用户只调用 `$jp-commerce-insights`。以下旧 Skill 保留采集器、脚本、测试与专业边界，但不再作为日常入口。

| 旧目录 / 名称 | 内部角色 | 由谁负责 | 处理方式 |
|---|---|---|---|
| `ecommerce-product-selection` / 电商选品情报 | `SELECTION` | 本 Skill 的选品流程 | 方法并入统一入口；无需单独调用 |
| `sorftime-market-intel` | `MARKET_EVIDENCE_ADAPTER` | 外部市场证据适配器 | 有可验证运行时才调用 |
| `amazon-keyword-miner` | `KEYWORD_EVIDENCE` | 关键词证据模块 | 只输出关键词证据，不代替销量或Product Truth |
| `product-intel` | `COMPETITOR_FACT_EVIDENCE` | 竞品事实模块 | 只保存可追溯页面事实 |
| `amazon-review-scraper`（声明名 `amazon-competitor-reviews`） | `AMAZON_VOC_COLLECTION_OWNER` | Amazon评论采集唯一负责人 | 保留成熟采集能力与原始证据 |
| `amazon-voc-browser-scraper` | `LEGACY_VOC_COMPATIBILITY` | 兼容层 | 不再与评论采集负责人并列；不得形成第二套口径 |
| `amazon-listing-asset-capture` | `LISTING_ASSET_EVIDENCE` | 页面素材证据模块 | 只采集Gallery、A+、视频和模块证据，不生成创意 |
| `customer-review-intelligence` | `VOC_ANALYSIS` | VOC分析方法 | 对采集结果做去重、编码、证据和营销含义分析 |

## 运行时解析顺序

只为当前模式解析所需组件，不批量加载：

1. 当前 GitHub 工作区已登记并验证的 `skills/<module>/`；
2. 当前项目 `.agents/internal-skills/<module>/`；
3. `$CODEX_HOME/internal-skills/<module>/`；
4. 迁移期兼容位置 `.agents/skills/<module>/` 或 `$CODEX_HOME/skills/<module>/`；
5. 找不到或Hash不符时返回 `BLOCKED_RUNTIME_MISSING`。

旧 Global Skill 不得覆盖 GitHub `main` 的入口规则、来源边界或输出契约。内部组件缺失时，可以继续完成不依赖该组件的分析，但必须把覆盖范围标为 `Partial` 或 `Blocked`。

## 合并边界

- 合并的是用户入口、路由、术语和交接格式，不是把所有脚本复制进一个超级 Skill。
- `amazon-review-scraper` 是Amazon评论采集的唯一负责人；兼容浏览器入口只转交任务，不另建数据集。
- `amazon-listing-asset-capture` 属于洞察证据层，不属于内容生产层。
- 任何评论、关键词或竞品信息都只能形成 Insight 或 Claim Candidate，不能自动成为产品事实或 Approved Claim。
