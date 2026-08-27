# Visual Router 规则

## 执行顺序

```text
resolve_project
→ load_visual_freeze
→ load_visual_profile
→ resolve_project_visual_dna
→ resolve_channel_intent
→ visual_router_if_needed
→ evaluate_pattern_match
→ evaluate_execution_readiness
→ apply_channel_adapter
→ continue_existing_flow
```

`visual-profile.yaml` 是生成物。只要 `project-context.yaml`、Registry、Pattern、素材状态或 Freeze 发生变化，就重新运行 Router，不手工改评分。

## Match、Readiness 与 Confidence

- `pattern_match` 只计算 Channel、Category、Consumer Goal、Brand、Information Complexity 与 Mobile Fit，不包含生产素材。
- `execution_readiness` 独立检查 Product Truth、Claim、Required Asset、Pattern/Recipe 生命周期和 Human Review。
- `evidence_confidence` 表示当前受治理证据完整度，不是转化率预测。
- Match 高、Readiness 低时必须保持 `HUMAN_REVIEW_REQUIRED` 或 `BLOCKED_BY_ASSET`，不能进入正式 Visual Production。
- 一个项目只使用一份 Context；各渠道写入 `channel_assignments`。跨渠道只继承 Project Visual DNA，禁止继承完整 Layout。
- Project Visual DNA 保存 `information_strategy`；Amazon 与 EDM 分别生成渠道级 Information Density。
- Product Truth、Claim 与 Asset 使用各自状态评分表；只有 `APPROVED`、`VERIFIED_FOR_CHANNEL`、`NOT_REQUIRED` 可获得生产级 100。
- EDM Recipe 必须匹配已解析 Channel Intent；缺少 Intent 时不得默认使用 Product Launch Recipe。

## Freeze 优先

仅当 `visual-freeze.yaml` 同时满足以下条件时自动继承：

- `status: APPROVED`；
- `active: true`；
- 存在具名 `approved_by` 与 `approved_at`；
- Pattern 已注册且未 Deprecated；
- 当前 Channel 在 Freeze Scope 内；
- 当前 Channel 被 Freeze Pattern 的 `fit.channels` 支持；
- Pattern 所需素材仍满足；
- 用户未明确要求探索新视觉。

Candidate Freeze 只表示“发现了可供复核的人工记录”，不会自动激活，也不会把范围外的 Product Truth、Claim、素材、上架或发送状态升级为 Approved。

Freeze 不在当前 Channel Scope 或其 Pattern 不支持当前 Channel 时，标记 `NOT_APPLICABLE_TO_CHANNEL`。该记录保留用于审计，但不进入当前渠道 Readiness Blocker。

## Pattern Ranking

| 维度 | 权重 |
|---|---:|
| Channel Fit | 20 |
| Category Fit | 15 |
| Consumer Goal Fit | 15 |
| Brand Fit | 15 |
| Information Complexity | 10 |
| Asset Availability | 15 |
| Mobile Fit | 5 |
| Historical Performance | 5 |

缺失上下文按中性分处理并保留不确定性；没有历史效果数据时为 `UNKNOWN`，不虚构转化提升。

## Human Review 触发

- Top 1 / Top 2 差距小于 8；
- Brand Fit 小于 70；
- 任何必需素材不是 `AVAILABLE`；
- 选中 Pattern 仍是 `CANDIDATE`；
- Top score 小于 68；
- 用户明确要求探索新视觉；
- 已批准 Freeze 与当前渠道、素材或 Pattern 生命周期冲突。

其余情况自动选择最高分 Pattern，不继续向用户提问“选 A 还是 B”。Human Review 只处理实际冲突或未满足 Gate。
