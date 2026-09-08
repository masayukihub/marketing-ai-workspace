# 内部组件映射

用户只调用 `$jp-commerce-content-flow`。旧名称继续用于识别历史请求；成熟 Runtime、阶段Gate和回归测试保持独立。

| 旧目录 / 名称 | 内部角色 | 主要职责 | 禁止事项 |
|---|---|---|---|
| `jp-commerce-creative-flow` | `SOURCE_GOVERNANCE_OVERLAY` | 飞书/Product Knowledge来源治理、Product Truth Packet、SwitchBot JP Overlay | 不跳过事实与人工Gate |
| `japan-listing-demo` | `UPSTREAM_LISTING_ROUTER` | 上游阶段路由、Checkpoint与Context Firewall | 不为业务定制重写Upstream Core |
| `listing-planning` | `STAGE_0_TO_7_PLANNING` | 策略、故事线、页面结构与Production Handoff | 未批准不得进入生产 |
| `listing-production` | `STAGE_7_5_TO_8_PRODUCTION` | 逐张生产、候选锁定与Production Freeze | 不替换已锁定候选 |
| `listing-hardening` | `STAGE_8_5_TO_10_HARDENING` | 精确文件核验、Demo组装、PC/移动端交付QA | 未实测不得声称通过 |
| `listing-evidence-auditor` | `FINAL_EVIDENCE_AUDITOR` | 对最终文件、来源、Hash、Asset-to-Slot做独立核验 | 不补写上游决策 |
| `amazon-japan-pdp-generator` | `SPEC_TEMPLATE_RENDERER` | Amazon Spec、模板、页面预览和移动端回归 | 不从原始资料直接生成成品 |
| `amazon-listing-creative` | `CONTROLLED_CREATIVE_MODULE` | 单张方向探索、深化和局部修改 | 不建立第二套完整Listing流程 |

## 正式调用链

```text
$jp-commerce-content-flow
→ project-context-resolver
→ Product Knowledge / Feishu Source Intake
→ Product Truth Packet + SwitchBot JP Overlay
→ Commerce Insight Handoff
→ Visual Freeze / Accepted Planning Decision / Visual Profile
→ japan-listing-demo
   ├─ Stage 0–7 → listing-planning
   ├─ Stage 7.5–8 → listing-production
   └─ Stage 8.5–10 → listing-hardening → listing-evidence-auditor
→ Amazon Adapter
   ├─ amazon-japan-pdp-generator
   └─ amazon-listing-creative（仅探索或局部修改）
→ Review / Mobile QA / Delivery Gate
```

## 运行时解析顺序

1. `marketing-ai-workspace` GitHub `main` 中锁定的入口与兼容模块；
2. 已登记commit的 `jp-commerce-creative-flow` fork；
3. fork内的 SwitchBot JP Overlay；
4. fork内未修改的 Upstream Core；
5. 当前项目 `.agents/internal-skills/<module>/`；
6. `$CODEX_HOME/internal-skills/<module>/`；
7. 迁移期兼容位置 `.agents/skills/<module>/` 或 `$CODEX_HOME/skills/<module>/`；
8. 找不到或Hash不符时返回 `BLOCKED_RUNTIME_MISSING`。

Global Mirror 只能从 clean `main` 单向生成，不得反向覆盖GitHub。内部目录迁移不删除源代码，也不改变Upstream linkage。

## 当前能力漂移

旧Global入口曾声明通用 Visual Reference Inbox / LP Page Pattern 能力，但当前 GitHub `main` 只有 Reference Ingestion Schema，没有登记可执行的通用 Inbox Runtime。合并时不得把声明当成已经可用：

- 有实际运行时和来源时，只能按现有Reference Ingestion合同生成 `DRAFT` / `CANDIDATE`；
- 没有可验证执行器时返回 `BLOCKED_RUNTIME_MISSING`；
- 不得让旧Global副本覆盖新版Project Context、Visual Planning Decision或Gate顺序。
