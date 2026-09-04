# Project Inbox

这里记录从历史工作和对话中识别出的“可能需要正式建档”的项目候选。它只是 Discovery Inbox，不是 Active Project Registry，也不代表任何产品事实、上市状态、日期、Claim、Owner 或预算已经获批。

正式项目仍以 `projects/<project-id>/project.yaml` 为准。当前已存在的正式入口为：

- `s30-mini`
- `lock-ultra-max`
- `daily-station`
- `homerunpet`

## 候选项目

| Candidate ID | 暂定名称 | 为什么可能需要建档 | 当前状态 | 建档前必须确认 |
|---|---|---|---|---|
| `video-doorbell-vision-jp` | Video Doorbell Vision Japan | 过往工作中已涉及日本新品、Listing、门锁套装与场景视觉，但仓库目前没有独立 Project Manifest | `DISCOVERY_ONLY` | 正式产品名、Product ID、Variant/Offer、当前 GTM 阶段、Owner、权威来源、与 Lock 套装的边界 |
| `hub-4-jp` | Hub 4 Japan | 过往工作中已出现新品时间线与产品规划需求，但尚无正式项目入口 | `DISCOVERY_ONLY` | 正式产品定义、当前阶段、产品资料、Owner、与既有ハブ产品的边界、是否已成为实际 GTM 项目 |
| `ai-mindclip-jp` | AI MindClip Japan | 已存在 PDP/功能对比等历史任务和 Product Knowledge 线索，但没有正式 Project Memory / Manifest | `DISCOVERY_ONLY` | 项目目标、产品状态、正式命名、渠道范围、Owner、当前有效来源与历史输出是否仍可用 |
| `autumn-campaign-2026-jp` | 2026 Japan Autumn Campaign | 过往已讨论秋促策略、KOL/PR 和预算方向，但审计未发现正式项目记录 | `DISCOVERY_ONLY` | 活动 ID、日期、预算、目标、产品/Offer、渠道、Owner、历史参考、KPI 和审批状态 |

## 不自动建档的原因

历史聊天、旧输出目录、Product Knowledge 实体或临时需求都只能证明“曾经讨论或制作过”，不能证明项目目前仍处于 Active 状态。

因此系统遇到以上候选时应返回：

```text
PROJECT_BOOTSTRAP_REQUIRED
```

并先生成建档 Review Pack，而不是直接创建正式状态。

## Project Bootstrap 最小输入

```text
project_id
project_name
aliases
market
business_objective
owner_role
lifecycle_stage
product / variant / bundle / offer
source_registry
state_as_of
current_blockers
next_actions
required_human_decisions
```

缺失内容使用 `UNKNOWN` 或 `NEED_CONFIRMATION`。

## 建档流程

```text
发现候选
→ 读取当前官方来源和历史材料
→ Source Map
→ Product / Project Boundary
→ Project Bootstrap Review Pack
→ Human Review
→ 创建 Project Memory
→ 创建 project.yaml
→ Resolver 校验
→ PR
→ 合并 main 后成为 Formal Project
```

## 直接复制的建档指令

```text
读取最新 GitHub main，并检查 projects/PROJECT_INBOX.md。
为【候选项目】执行 PROJECT_BOOTSTRAP_REQUIRED 流程：
只整理来源、项目目标、产品/Offer边界、Owner角色、阶段、Blocker和Next Action；
生成一次性 Project Bootstrap Review Pack。
不要自动创建 Product Truth、批准 Claim、写飞书或把候选标记为 Active。
```
