# Skills

面向日常使用只保留两个中文入口。旧 Skill 不删除代码，以内部模块形式保留兼容性、脚本和测试。

| 用户入口 | 什么时候用 | 内部整合能力 |
|---|---|---|
| `$jp-commerce-insights`（日本电商洞察） | 选品、关键词、竞品、评论、VOC、Listing素材采集 | 电商选品情报、Amazon Keyword Miner、Amazon Competitor Reviews、Amazon VOC Browser Scraper、Amazon Listing Asset Capture、customer-review-intelligence |
| `$jp-commerce-content-flow`（日本电商内容生成） | 日亚Gallery、A+、Listing文案、视觉稿、Content Review HTML、继续现有项目 | JP Commerce Creative Flow、Amazon Japan PDP Generator、Amazon Listing Creative |

## 最简单的用法

```text
使用 $jp-commerce-insights，调研S30 mini在日本小户型换机市场的机会，
输出关键词、竞品、VOC、用户障碍和Creative Handoff。
```

```text
使用 $jp-commerce-content-flow，读取S30 mini的Product Truth和Insight Pack，
继续水箱版Amazon Gallery G01-G03，完成Review后再进入单文件HTML。
```

用户不需要手动调用内部模块。说“继续”“下一步”“只修改这张”时，内容生成入口读取正式项目状态并执行最小必要步骤。

## 能力边界

- Product Knowledge与官方资料仍是产品事实源。
- 研究洞察和评论不能自动升级为Approved Claim。
- 正式产品本体不能由AI生成。
- 创意批准不等于Publish Ready。
- GitHub只保存可版本管理的规则、Schema、脚本、空模板和合成Fixture；不提交Secret、未发布产品资料、真实审批、飞书快照或未授权素材。

## 更新规则

新的电商研究能力优先并入 `jp-commerce-insights` 的模块和统一Insight Pack；新的Listing生成能力优先并入 `jp-commerce-content-flow` 的阶段路由。只有当能力拥有完全不同的用户任务、数据契约和交付物时，才新增用户可见Skill。
