# Visual Router 规则

## 执行顺序

```text
resolve_project
→ load_visual_freeze
→ load_visual_profile
→ visual_router_if_needed
→ apply_channel_adapter
→ continue_existing_flow
```

`visual-profile.yaml` 是生成物。只要 `project-context.yaml`、Registry、Pattern、素材状态或 Freeze 发生变化，就重新运行 Router，不手工改评分。

## Freeze 优先

仅当 `visual-freeze.yaml` 同时满足以下条件时自动继承：

- `status: APPROVED`；
- `active: true`；
- 存在具名 `approved_by` 与 `approved_at`；
- Pattern 已注册且未 Deprecated；
- 当前 Channel 在 Freeze Scope 内；
- Pattern 所需素材仍满足；
- 用户未明确要求探索新视觉。

Candidate Freeze 只表示“发现了可供复核的人工记录”，不会自动激活，也不会把范围外的 Product Truth、Claim、素材、上架或发送状态升级为 Approved。

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
