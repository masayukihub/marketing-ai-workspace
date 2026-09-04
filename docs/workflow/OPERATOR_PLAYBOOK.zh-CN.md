# SwitchBot Japan Marketing AI 操作手册

这份手册面向日常营销工作，不面向程序开发。目标是把 ChatGPT、Codex、飞书、GitHub、Skill、Renderer 和视觉工具组成一条稳定流程，并减少重复确认。

## 1. 每个工具只负责一层

| 工具 | 主要职责 | 不应承担 |
|---|---|---|
| 飞书 / 官方资料 | 原始产品、GTM、价格、审批、项目表和团队协作 | Skill 源码和版本控制 |
| GitHub `main` | Skill、规则、Project Manifest、Decision、测试和 Runtime 版本 | 大量飞书原文、未授权素材、Secret |
| ChatGPT 网页版 | 营销判断、策略讨论、资料综合、日语 Review、视觉 Review、任务调度 | 在未验证工具时假装执行脚本或读到飞书正文 |
| Codex | 读取仓库、执行 Skill、批处理、生成 HTML、跑测试、维护 Git/PR | 自行批准 Product Truth、Claim、价格、发布 |
| Product Knowledge | 产品实体、规格、Claim、价格、兼容性和冲突治理 | 项目 Owner、Deadline 和阶段管理 |
| Project Memory | 项目背景、决策、风险、状态、Owner、Next Action、长期学习 | 充当产品规格库 |
| 四个中文入口 Skill | 完成具体营销任务 | 要求用户手动挑选内部模块 |
| Visual System / Renderer | 路由视觉 Pattern、制作和 QA | 改写 Product Truth 或自动批准最终视觉 |

## 2. 你的默认工作链

```text
飞书 / 官方来源
→ 项目解析与 Source Snapshot
→ Product Knowledge / Product Truth
→ Project Memory / Campaign Context
→ 四个中文入口 Skill
→ Draft / Brief / HTML / Visual Candidate
→ Automated QA
→ 一次性 Human Review
→ 受控写回或人工发布
```

### 普通任务最少输入

```text
项目：
目标：
来源：
期望输出：
限制：
```

项目、来源或限制可以省略；系统应先读取正式状态，不应立即重复询问。

## 3. 四个入口怎么选

### `$jp-commerce-insights`

用于：日本市场机会、关键词、竞品、评论、VOC、Listing 证据、创意前置研究。

常见任务：

- S30 mini 日本小户型清洁需求；
- 竞品扫地机 Amazon 评论与购买障碍；
- Lock 系列与竞品 KOL/PR 历史证据；
- Amazon 页面结构和素材盘点；
- 旧研究 Pack 的增量更新。

正式输出是 `Commerce Insight Pack`。研究结论不能直接变成 Approved Claim。

### `$jp-commerce-content-flow`

用于：Amazon JP Gallery、A+、Listing 文案、卖点图、Creative Brief、Content Review HTML 和最终 Hardening。

常见任务：

- S30 mini 水箱版 G01-WT / G02 / G03；
- Lock Ultra Max 单品、套装、包装、A+；
- 从营销文档生成完整卖点图；
- 只修改一张已批准候选；
- 组装 Desktop / Mobile Review HTML。

正常顺序：

```text
Product Truth
→ Insight Handoff
→ Planning
→ Content Review
→ Visual Direction
→ One-asset Production
→ Whole-set Review
→ Hardening
```

### `$switchbot-japan-campaign`

用于：GTM、活动策划、Launch Readiness、项目执行、KOL/PR、渠道素材、Tracking、预算方向、风险和复盘。

常见任务：

- 新品上市项目管理；
- 2026 秋促策划；
- KOL/PR 历史复盘与后续计划；
- 渠道素材需求汇总；
- 周风险报告；
- Campaign 数据复盘。

### `$switchbot-japan-edm`

用于：日本 EDM 策略、日语文案、设计 Brief、历史模板、HTML、视觉、修改和发送前 QA。

常见任务：

- 新品 Launch EDM；
- Sale / Reminder / Last Call；
- Category / Ecosystem EDM；
- 只修改某个模块；
- 从 Campaign Context 继续稳定 Runtime；
- 检查 ESP Ready，但不自动发送。

## 4. ChatGPT 与 Codex 的分工

### 先在 ChatGPT 做

- 判断真正的问题；
- 确定 Target、Positioning、核心购买理由和优先级；
- 审核 Codex 的策略、日语、视觉和业务边界；
- 把大任务收缩成一个可验证 Pilot；
- 判断哪些结论值得沉淀到 Skill 或 Project Memory。

### 再交给 Codex 做

- 读取项目 Manifest 和 Context；
- 运行 Skill / Flow；
- 整理大量文件和结构化数据；
- 生成 Markdown、JSON、CSV、HTML；
- 渲染 Desktop / Mobile；
- 跑测试、创建分支和 PR；
- 输出一次性 Review Pack。

### 推荐循环

```text
ChatGPT：判断方向
→ Codex：执行到 Human Gate
→ ChatGPT / 你：一次性 Review
→ Codex：应用决定、QA、版本化
```

## 5. 默认不再反复确认

以下步骤默认自动继续：

- 读取最新 `main`；
- 解析项目和任务类型；
- 选择四个入口及内部模块；
- 读取最小必要来源；
- 格式化、去重、分类和生成 Run Manifest；
- 使用已批准视觉决定、Template 或 Formula；
- 生成内部 Draft / Brief / Review HTML；
- 两次以内的文案去重、缩短、排版和移动端修复；
- 把缺口合并成按 Owner 分类的补证包。

只有以下情况停下：

- Product / Variant / Bundle / Offer 无法唯一确定；
- 需要批准 Claim、价格、促销、日期、认证、法务或外部链接；
- 核心 Target、Positioning、Primary Message 或 Scope 发生变化；
- 没有可继承视觉方向且 Router 低置信度或冲突；
- 需要选择精确最终资产、批准整套视觉、ESP 或发布；
- 两次修复后硬性 QA 仍失败。

详细规则见 `operator/review-policy.yaml`。

## 6. 新品 GTM 的推荐完整 Flow

```text
项目建档
→ Source / Product Truth
→ 日本市场与 VOC
→ Positioning / Message
→ GTM 与 Launch Readiness
→ Amazon / EDM / KOL / PR Handoff
→ 渠道执行
→ 数据复盘
→ Project Memory / Skill Learning Proposal
```

### 你的人工 Gate

1. **Product / Offer Gate**：到底卖哪个产品、版本和套装；
2. **Strategy Gate**：目标人群、核心购买理由和优先信息；
3. **Creative Gate**：代表图、视觉方向或整套 Storyline；
4. **Final Gate**：正式内容、精确资产、链接和发布。

其余过程尽量自动执行。

## 7. Amazon 卖点图的最高效方式

```text
产品营销文档与官方素材
→ Product Truth
→ Commerce Insight Pack
→ Gallery / A+ Storyline
→ 每张图一个 Consumer Question
→ Visual Direction / Anchor
→ 逐张生产
→ Whole-set Review
→ Standalone HTML
```

关键原则：

- 不一次性盲生成整套图；
- 有可继承的 Visual Planning Decision 时不重复问方向；
- 正式产品本体使用官方素材；
- AI 只生成场景层；
- 文案和图形层程序化排版；
- 局部问题只修改最小范围；
- `PROOF_VISUAL` 必须绑定 Claim 和权威来源。

## 8. EDM 的最高效方式

```text
Campaign Context
→ Truth / Promotion / CTA / Asset Preflight
→ 自动选 Formula / Template / Length
→ Render
→ Desktop / Mobile QA
→ 最多两次安全修复
→ 一次批量 Human Review
→ 条件式自动批准轻微修改
→ Final / ESP Gate
```

轻微修改在不改变 Product、Offer、Claim、价格、素材和链接的前提下，可以预授权为：

```text
MINOR_REVISION_AUTO_APPROVE_IF_QA_PASS
```

这样修改后不需要第二次确认。

## 9. KOL / PR 的推荐方式

不要只让 AI “找名单”。正确 Flow 是：

```text
项目目标与产品范围
→ 历史合作证据
→ 竞品合作证据
→ 受众和内容方向
→ KOL / Media Segment
→ Candidate Shortlist
→ Brief / Rights / Tracking / KPI
→ Human Review
→ 人工邀约与执行
→ 结果复盘和长期关系分层
```

完整规则和模板见 `KOL_PR_PLAYBOOK.zh-CN.md`。

## 10. GTM 项目管理的推荐方式

每周只需要一个统一输出：

```text
项目状态
P0/P1 风险
下一个里程碑
Owner
Deadline
依赖
影响 Launch / Content / Sales
Next Action
需要你决定的事项
```

事实、决定、假设和建议必须分列。AI 不应只做提醒，而应根据依赖和时间关系判断风险。

推荐指令：

```text
使用 $switchbot-japan-campaign 的 EXECUTION 模式，解析【项目名】。
更新本周 GTM 风险报告；只输出新增/变化项、P0/P1、Owner、Deadline、影响和 Next Action。
缺失内容合并为一次性补证包，不逐项询问。
```

## 11. Campaign Review 的推荐方式

```text
数据质量
→ 统一产品和渠道映射
→ 指标计算
→ 目标/历史对比
→ 渠道/产品/阶段/素材拆解
→ 原因与替代解释
→ 继续 / 调整 / 停止 / 新增
→ Memory Proposal
```

必须注意：

- CTR、CVR、CPC、CPM 等整体比例从总分子/总分母计算；
- 不平均各渠道比例；
- 不同周期、币种、税口径和归因窗不可直接合并；
- 相关性不能自动写成直接归因。

## 12. 飞书连接与降级路径

优先使用只读 `get_feishu_resource` 读取 Docx、Sheet 和 Bitable。

成功读取必须返回正文或结构化数据以及来源元数据。只有登录成功、工具存在或只返回标题都不算完整读取。

失败时：

```text
记录真实错误类型
→ 保留 SOURCE BLOCKED
→ 使用明确确认的 Local File / Manual Snapshot fallback
→ 不伪装为实时飞书读取
```

正式写飞书必须单独预览变更并获得授权。

## 13. 项目状态和历史聊天

- 具名项目先读取最新 GitHub `main` 和 `project.yaml`；
- 历史聊天只帮助发现需求，不能自动覆盖正式状态；
- 对话中说“批准”后，只有写入正式 Decision 并合并 `main` 才成为 Formal State；
- `chatgpt-context.md` 是阅读缓存，不是 Truth Source。

## 14. 你应该沉淀什么

每个项目结束后，只沉淀三类内容：

1. **Product Knowledge Proposal**：可复用产品事实、Claim、价格或兼容性变化；
2. **Project Memory Proposal**：决策、风险、结果、长期学习和 Next Action；
3. **Skill / Pattern Learning Proposal**：重复出现且跨项目有效的方法、模板和 QA 规则。

一次项目的临时修补，不应直接写成全局规则。

## 15. 每次交付的最低验收

- 结论清楚，不只罗列数据；
- 重要事实和 Claim 有来源；
- Product / Offer / Channel 范围无混淆；
- 未确认信息保持可见；
- 有 Owner 和 Next Action；
- HTML / Visual 的 Desktop / Mobile QA 状态真实；
- Candidate 和 Publish Ready 明确区分；
- 没有 Secret、私人联系方式或未授权数据进入 GitHub。
