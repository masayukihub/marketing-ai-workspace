---
name: jp-commerce-insights
description: 统一完成日本电商选品、市场机会、Amazon关键词、竞品Listing、竞品评论、Amazon及日本EC用户评价/VOC、公开页面素材盘点与创意前置证据整理。Use when the user asks for 电商选品情报, Amazon Keyword Miner, Amazon Competitor Reviews, Amazon VOC Browser Scraper, Amazon Listing Asset Capture, 日本市场评论分析, 竞品分析, 关键词研究, 商品机会判断, or a research pack that will feed Amazon/楽天/Yahoo/官网内容制作. 可执行单一模块或完整研究；默认用中文解释，并为下游日本电商内容生成输出统一 Insight Pack。
---

# 日本电商洞察

把原先分散的选品、关键词、竞品、VOC、评论与素材采集整合为一个入口。保留专业分工，但不要求用户判断该调用哪个旧 Skill。

## 开始方式

任务指向现有仓库项目时，先运行 `project-context-resolver`，按 Competitor/VOC/Amazon 任务类型只读取 Context Package 返回的最小 Project Memory、Decision、Product Truth 与视觉/资产指针。研究结果只能作为 Insight、Hypothesis、Risk 或 Claim Candidate 回写提案，不得直接改变 Manifest Gate 或 Product Truth。

先读取 [capability-map.md](references/capability-map.md)，根据用户需求选择最小模式：

- `FULL`：完整机会研究，串联全部必要模块。
- `SELECTION`：品类、需求、竞争、价格带与进入机会。
- `KEYWORD`：关键词发现、意图、聚类、页面位置与证据强度。
- `COMPETITOR`：竞品、Listing结构、Offer、评论与差异机会。
- `VOC`：Amazon、楽天、Yahoo、官网、YouTube、SNS等真实用户反馈。
- `ASSET_CAPTURE`：竞品/自有Listing可见素材、模块和页面结构盘点。
- `UPDATE`：对既有 Insight Pack 做增量更新，不重做稳定结论。

用户说“帮我研究这个产品”且未指定模块时，默认使用 `FULL`。用户只问一个明确问题时，只运行相关模块。

## 固定流程

### 1. 锁定研究对象

确认市场、渠道、品类、产品/型号、目标决策和时间范围。存在同名、旧型号、套装或变体时先拆开；不得把相似型号合并。

SwitchBot 产品先读取当前项目的 Product Knowledge 或官方资料。找不到权威事实时标记 `NEED_CONFIRMATION`，不要从评论、竞品页面或聊天记忆补齐产品事实。

### 2. 建立来源与覆盖表

按 [source-rules.md](references/source-rules.md) 执行。记录来源URL、渠道、对象、获取时间、范围、页数/条数、状态和限制。区分：

- 官方事实与平台规则；
- 搜索需求证据；
- 竞品公开页面；
- 真实用户反馈；
- KOL/媒体/品牌自有内容；
- 参考素材与创意灵感。

这些来源不能互相替代。品牌文案不是VOC，竞品页面不是产品事实，搜索量不是销量。

### 3. 执行模块

读取 [workflow-modules.md](references/workflow-modules.md)，只加载本次需要的模块。所有判断区分：

`FACT` / `INSIGHT` / `HYPOTHESIS` / `RECOMMENDATION` / `DATA_GAP` / `RISK`

缺少证据时使用：

`Complete` / `Partial` / `Blocked` / `Not Available` / `Not Comparable` / `Unverified`

不得把缺失值写成0，不得用少量评论写“用户普遍认为”，不得把不同抓取时间的互动数据直接横向排名。

### 4. 形成决策结论

不要停在数据罗列。按以下顺序输出：

```text
结论 → 证据 → 影响 → 建议动作 → 风险/限制 → 下一步
```

完整研究必须回答：

1. 这个机会值不值得继续；
2. 目标用户和核心场景是什么；
3. 用户最在意、最不满和最犹豫什么；
4. 竞品已经占据哪些表达，仍有哪些空位；
5. 应优先覆盖哪些关键词和购买问题；
6. 哪些素材/证据已具备，哪些会阻塞内容制作；
7. 下一步应进入测试、补证、内容规划还是停止。

### 5. 输出统一 Insight Pack

完整研究或需要交给下游 Skill 时，读取 [output-contract.md](references/output-contract.md)，生成统一的 `Commerce Insight Pack`。最少包含：

- Scope 与版本；
- Source Coverage；
- Product/Category Boundary；
- Market Opportunity；
- Target User 与 JTBD；
- Keyword Map；
- Competitor Map；
- VOC Themes 与证据；
- Purchase Drivers / Barriers / Objections；
- Claim Candidates（不等于已批准Claim）；
- Asset/Proof Inventory 与缺口；
- Opportunities / Risks / Tests；
- Creative Handoff；
- Unknown / Need Confirmation。

若用户只要单一模块，可用精简版，不必强制生成全部字段。

## 工具与采集边界

- 用户明确要求搜索最新信息时，使用可用的网络搜索并引用实际来源。
- 用户明确要求操作或查看网页时，使用可用浏览器能力；只读取页面可见内容。
- Amazon等平台受登录、CAPTCHA、频率或地区限制时如实标记 `Blocked` 或 `Partial`，不要绕过限制。
- 不读取Cookie、Token、密码、浏览器存储或其他凭据。
- 保存原始证据时保留URL、时间和范围；分析字段不得覆盖原文。
- 报告不公开评论者姓名、私人联系方式或未授权个人信息。

## 中文与日本市场输出

- 默认使用简体中文解释研究逻辑、结论、风险和行动。
- 日文关键词、用户原话、Amazon模块名与平台字段保留原文，并提供中文解释。
- 面向日本消费者的候选文案只作为研究派生项；正式内容制作交给 `$jp-commerce-content-flow`。

## 与内容生成的交接

当用户要求继续制作Amazon Gallery、A+、Listing文案、视觉稿或HTML时，不在本 Skill 内重新搭建生产流程。先冻结当前 Insight Pack，再交给 `$jp-commerce-content-flow`。

研究洞察不能自动升级为产品事实或Approved Claim。下游仍必须执行 Product Truth 与人工审批。
