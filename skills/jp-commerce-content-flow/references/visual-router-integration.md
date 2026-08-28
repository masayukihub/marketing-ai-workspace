# Visual Router Integration

## 目的

`visual-system/` 是共享内部能力，用于在项目级别继承已批准视觉方向或自动选择最适合的结构 Pattern。它不新增用户可见 Skill，也不替代 Amazon Reference Matcher。

## 与 Amazon Reference System 的分工

| 层级 | 能力 | 决策对象 |
|---|---|---|
| Project | Visual Router | Project Visual DNA、跨渠道 Assignment、项目 Freeze、Pattern Match 与 Execution Readiness |
| Amazon Page | Reference Matcher | 竞品结构参考、同类目 Gate、Top references |
| Amazon Production | Decision Adapter / Templates | Gallery/A+ 顺序、已注册 Primitive、Renderer |

Visual Router 选择 `Pattern` 后，Amazon Channel Adapter 仍须调用现有 Reference Matcher、Category Semantics、Template Registry 与 Renderer Gate。两层不复制评分逻辑。

## 执行合同

```text
resolve_project
→ load projects/<id>/project-context.yaml
→ load projects/<id>/visual-freeze.yaml if present
→ load accepted Project Visual Planning Decision when no Approved Freeze applies
→ load projects/<id>/visual-profile.yaml if current
→ resolve Project Visual DNA
→ run visual-system/routing/visual_router.py if needed
→ evaluate Pattern Match / Execution Readiness / Evidence Confidence separately
→ apply the requested Channel Assignment and Adapter
→ continue Planning / Production / Hardening
```

当 Context、素材状态、Registry、Pattern 或 Freeze 更新时，Profile 视为需重新生成。不得手工改 Router 评分来迎合单个项目。

一个项目只维护一份 `project-context.yaml`。Amazon、EDM 等渠道写入同一份 Profile 的 `channel_assignments`；跨渠道只继承 `project_visual_dna`，不继承完整 Layout。

渠道任务必须优先读取 `channel_contexts.<channel>`。缺少 EDM Campaign Type 或 Primary Objective 时返回 `EDM_INTENT_NOT_RESOLVED / HUMAN_REVIEW_REQUIRED`，不得默认套用 Launch Recipe。

## Freeze 合同

只有 `status: APPROVED`、`active: true`、具名人工、当前渠道同时在 Freeze Scope 与 Pattern `fit.channels` 中、Pattern 未 Deprecated 且必需素材满足时自动继承。

`status: CANDIDATE` 只供人工复核，不视为批准。Freeze 的创意范围不得扩张到 Product Truth、Claim、素材授权、Amazon Upload、Hardening 或 Mobile QA。

## Project Visual Planning Lock

Approved Visual Freeze 始终拥有最高优先级。没有适用的 Approved Freeze 时，Router 可读取 `project.yaml.sources.visual_planning_decision` 指向的 `ACCEPTED / ACTIVE` Decision Record。

Planning Lock 只允许继承 Project Visual DNA、Channel Intent、Recipe Core、Mechanism Proof Policy、Optional Section Policy 与条件 Template Recommendation。它输出 `project_visual_direction_status=HUMAN_APPROVED_FOR_PROJECT_PLANNING` 与 `reask_visual_direction=false`，但仍保留 Product Truth、Claim、Asset、Renderer、Final Human、Mobile QA、ESP 与 Send Gate。

只有用户明确要求改变方向、渠道硬冲突、已批准项目方向冲突、Reviewed Pattern Deprecated 或 Stable Selector 无兼容 Template 时重新打开视觉方向审核。Candidate Freeze 不得覆盖该 Planning Lock，也不能由此升级为 Approved Freeze。

先判断 Freeze 对当前渠道是否适用。其他渠道的 Freeze 记录为 `NOT_APPLICABLE_TO_CHANNEL`，保留 Scope / Pattern 冲突原因，但不得进入当前渠道 Readiness Blocker 或降低 Readiness 分数。

## 下游 Gate

Router 的输出最多决定视觉结构建议。以下 Gate 保持原顺序和所有权：

- Product Truth；
- Human Review；
- Claim Gate；
- Product Layer；
- Hardening；
- Mobile QA。
- EDM 的 Asset Gate 与 ESP Gate。

任一 Gate 未满足时，返回原有 `BLOCKED` / `PARTIAL_BUT_ACTIONABLE`，不得因 Pattern 高分而继续正式生产。
