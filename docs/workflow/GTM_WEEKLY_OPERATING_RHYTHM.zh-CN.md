# SwitchBot Japan GTM 周度运行节奏

这份手册用于新品、促销和跨渠道项目管理。目标是让 AI 真正承担 PMO：读取状态、识别依赖和风险、生成 Owner Action，而不是只做提醒或重复汇报。

统一入口：`$switchbot-japan-campaign`

## 1. GTM 项目最小状态

每个 Active Project 至少维护：

```text
Project / Product / Variant / Offer
Market / Channel
Lifecycle Stage
Launch Target
PVT / MP / Sample / Shipment / Inbound
Amazon / DTC / Rakuten / Yahoo Status
Price / Promotion / Inventory
Product Truth / Claim / Asset Gate
KOL / PR / EDM / SNS / Listing Status
Owner / Deadline / Dependency
Risk / Decision / Next Action
state_as_of / source_id
```

没有来源或更新时间的状态不能被当作当前事实。

## 2. 生命周期

```text
Discover
→ Plan
→ Prepare
→ Launch
→ Optimize
→ Review
```

| 阶段 | AI 主要任务 | 你需要决定 |
|---|---|---|
| Discover | 来源、市场、用户、竞品、假设、产品边界 | 是否值得推进、目标用户和核心问题 |
| Plan | Positioning、Offer、渠道角色、预算方向、KPI | 核心策略、产品/Offer 和优先级 |
| Prepare | 时间线、素材、库存、页面、Claim、链接、Owner、风险 | Blocker 处理、例外和发布边界 |
| Launch | 上线状态、链接、Tracking、异常 | 是否暂停、调整或追加动作 |
| Optimize | 数据和反馈监测、具体优化动作 | 预算/信息/渠道的重要调整 |
| Review | 数据质量、结果、原因、学习 | 继续/调整/停止/新增和长期沉淀 |

## 3. 每周固定输出

每周只保留一份管理报告：

```text
weekly-gtm-status.md
weekly-gtm-status.json
weekly-gtm-status.html
```

### 首页只显示

1. 管理判断；
2. 本周新增/变化；
3. P0 / P1 风险；
4. 未来两周关键里程碑；
5. 需要你决定的事项；
6. Owner、Deadline 和 Next Action。

不重复展示所有已关闭事项和整份历史。

## 4. 风险字段

每条风险必须包含：

```text
risk_id
priority
classification: FACT | DECISION | HYPOTHESIS | UNVERIFIED
summary
evidence
source_id
source_as_of
impact_area: LAUNCH | CONTENT | SALES | INVENTORY | COMPLIANCE | MEASUREMENT
impact
probability
owner_role
deadline
dependency
recommended_action
status
blocks_gate
```

缺少 Evidence、Owner 或 Deadline 的风险不能被标记为“已管理”。

## 5. 优先级规则

### P0

满足任一：

- 会导致错品、错价、错 ASIN、错 Offer 或错误 Claim；
- 直接影响上市时间、库存、合规或正式页面；
- 在 7 天内到期且无 Owner/方案；
- 一个节点延误会阻塞多个下游渠道。

### P1

- 影响内容质量、渠道协同、媒体/KOL 节奏或测量；
- 未来 14 天内需要关闭；
- 有替代方案但成本或效果会下降。

### P2

- 不阻塞当前阶段；
- 可以在后续迭代处理；
- 对长期效率或沉淀有影响。

## 6. 自动识别依赖

系统应自动检查：

```text
Product Truth → Claim / Brief / Listing / EDM / KOL
Sample → KOL / PR / Photo / Video
MP / Shipment / Inbound → Preorder / In-stock Launch
Price / Promotion → PDP / EDM / SNS / Tracking
Official Asset → Gallery / A+ / EDM / PR / KOL Brief
ASIN / URL → Tracking / CRM / Campaign Launch
Legal / Certification → External Claim / Launch
```

示例：

```text
Amazon 计划现货开售日期
早于预计入仓日期
→ P0 Inventory / Launch Conflict
→ 建议改为预售、调整日期或重新确认运输计划
```

## 7. 你常用的新品 GTM 字段

### 生产与物流

```text
DVT / PVT / MP1
样机数量与到达时间
出货时间
运输方式
入仓时间
库存数量
补货计划
```

### 渠道

```text
Amazon ASIN / Variation / Listing / Brand Store
官网 PDP / Price / Stock / Promotion
Rakuten Page / Price / Stock / Coupon
Yahoo Page / Price / Stock / Campaign
Preorder / In-stock / Sale Start
```

### 营销

```text
Positioning / Message / Approved Claims
Gallery / A+ / LP
EDM / LINE / App Push / SNS
KOL / PR / Media
Video / Photo / Render
Tracking / Attribution / KPI
```

### 商业与审批

```text
MSRP / Sale Price / Tax
Offer / Bundle / Gift
Inventory Allocation
Legal / Compliance
Owner Approval
Publication Gate
```

## 8. 日常自动更新

低风险自动动作：

- 读取最新项目状态和来源时间；
- 对比上周与本周差异；
- 检查 Deadline、依赖和 Gate；
- 将重复问题合并；
- 为缺失字段按 Owner 生成补证清单；
- 生成周报和 Review HTML；
- 将完成结果提出 Project Memory Writeback Proposal。

必须人审：

- 改上市日期；
- 改价格、促销、库存承诺；
- 改 Product / Offer / Channel Scope；
- 批准 Claim、法务和合规；
- 取消或新增重大渠道；
- 对外发布、发送或正式写回。

## 9. 避免反复确认

系统默认采用：

```text
AUTONOMOUS_TO_NEXT_MATERIAL_HUMAN_GATE
```

不要在每个缺失字段上提问。先完成全部自动检查，再按 Owner 输出：

```text
Product Owner Questions
Engineering Evidence Request
Supply Chain Action Pack
Amazon Channel Action Pack
Legal / Compliance Request
Marketing Decision Queue
Source Access Request
```

只有真正影响 Strategy、Product/Offer、Claim、价格、日期、合规或发布的事项进入你的 Decision Queue。

## 10. 周度会议前流程

### 会前

```text
读取项目状态
→ Source / Freshness 检查
→ 与上周 Diff
→ 风险和依赖计算
→ 生成 Owner Action Pack
→ 生成管理摘要
```

### 会中

只讨论：

- P0；
- 未来两周里程碑；
- 跨部门依赖；
- 需要决定或升级的事项；
- 计划发生变化的部分。

### 会后

```text
Decision Record
→ Owner / Deadline 更新提案
→ Project Memory Proposal
→ Manifest Gate / Next Action 更新提案
→ 人工审核
→ PR / 正式写回
```

对话中的决定只有写入正式 Decision 并合并 `main` 后，才成为 Formal State。

## 11. GTM Review HTML

推荐页面区块：

```text
Executive Summary
Project Health
Gates
P0 / P1 Risks
Milestone Timeline
Channel Status
Content / Asset Status
Owner Action Table
Decision Queue
Changes Since Last Week
Source Freshness
```

技术细节和完整来源默认折叠。

## 12. 多项目视图

当前正式项目：

- S30 mini；
- Lock Ultra Max；
- Daily Station；
- homerunPET。

多项目周报只显示：

```text
Project
Lifecycle Stage
Overall Gate
Top Blocker
Next Milestone
Owner
Deadline
Next Action
```

不能把项目状态相加为一个虚假的总完成率。

## 13. 直接复制的周报指令

```text
使用 $switchbot-japan-campaign 的 EXECUTION 模式。
读取最新 GitHub main，并解析当前所有 Active Projects。

生成本周 SwitchBot Japan GTM 管理包：
1. 只展示相较上周新增或变化的状态；
2. 输出每个项目的 Lifecycle Stage、Overall Gate、Top Blocker、未来两周里程碑；
3. 自动检查生产、样机、物流、入仓、页面、价格、库存、Claim、素材、KOL、PR、EDM、SNS和Tracking依赖；
4. 风险必须包含 Evidence、Impact、Owner、Deadline、Next Action；
5. 区分 FACT / DECISION / HYPOTHESIS / UNVERIFIED；
6. 缺口一次性按 Owner 分组，不逐项询问；
7. 自动执行到下一个 Material Human Gate；
8. 不写飞书、不改正式日期/价格/Offer、不自动发布。

输出 Markdown、JSON、Review HTML 和 Project Memory Writeback Proposal。
```

## 14. 单个新品指令

```text
使用 $switchbot-japan-campaign，解析【项目名】。
更新当前 GTM 状态和未来两周风险，只处理当前项目。
优先检查 Product Truth、PVT/MP、样机、出货/入仓、Amazon/官网/楽天/Yahoo、价格、库存、Listing、素材、KOL、PR、EDM、SNS和Tracking。
已批准内容不要重新询问；缺口合并成 Owner Action Pack；停在需要我做业务决定的 Gate。
```

## 15. 复盘与学习

项目或 Campaign 结束后：

- 事实结果写入 Campaign Review Artifact；
- 可持续项目学习提出 Project Memory Proposal；
- 跨项目稳定规则提出 Skill Learning Proposal；
- 临时异常不直接写成全局规则；
- 下一次 GTM 必须复用已验证的时间线、风险模式和渠道依赖，而不是从空白模板开始。
