# S30 mini Visual Pattern / Recipe Human Review Scope

## 审核目的

本次只审核 S30 mini 的项目视觉原则与 Amazon → EDM 结构适配是否适合继续作为 Pilot 使用。它是 `human_review_preparation`，不是产品事实、素材或发布审批。

## 正式基线

- PR #5 Merge Commit：`437a38ebb3d4714ad2ff3ccfe78c02c8c9c75800`
- Review 分支基线：最新 `main@e7e8657da0af3e2be611c4e1acf2850fc1560729`
- Project Visual Profile：`projects/s30-mini/visual-profile.yaml`
- Amazon Candidate Freeze：`projects/s30-mini/visual-freeze.yaml`
- EDM Candidate Recipe：`visual-system/patterns/recipes/edm-product-launch-proof/recipe.yaml`

## 本次审核对象

1. S30 Project Visual DNA；
2. Amazon → EDM 只继承 Visual DNA 与信息层级原则，不继承完整 Layout；
3. EDM `product_launch / new_product_value_understanding` Channel Intent；
4. Product Launch Recipe 的核心顺序；
5. Required / Conditional / Optional Section；
6. `TPL-LAUNCH-A / CANDIDATE_CONDITIONAL_MATCH`；
7. Pattern / Recipe 继续保持 Candidate；
8. 当前事实、Claim、素材、CTA 与 Legal 缺口；
9. 下一人工 Gate。

## 不在本次范围

- Product Truth Approval；
- Claim Approval；
- Asset Approval；
- Pricing、正式 CTA 或促销信息；
- Visual Freeze Approval 或新建 EDM Freeze；
- Renderer、ESP Send、Publication；
- Pattern / Recipe Lifecycle Promotion。

## 推荐判断（非人工决定）

| 审核对象 | 系统建议 | 理由 |
|---|---|---|
| Project Visual DNA | `APPROVE_WITH_SCOPE` | 可用于结构规划，但不批准事实、Claim、素材或 Layout |
| EDM Channel Intent | `APPROVE` | 与新品价值理解任务匹配 |
| Recipe Core | `APPROVE` | 产品识别 → 利益 → 行动 → 品牌收尾清晰 |
| Mechanism Proof | Generic `CONDITIONAL`；S30 `REQUIRED_WHEN_APPROVED_EVIDENCE_AVAILABLE` | S30 的价值理解需要机制证据，但必须先获得已批准证据 |
| Optional Sections | `CONDITIONAL` | 仅在目标与素材满足时加入 |
| Template Mapping | `ACCEPT_AS_CONDITIONAL_RECOMMENDATION` | Stable Template Selector 保留最终决定权 |
| Lifecycle | `KEEP_CANDIDATE` | 当前只有单项目 Pilot 证据 |
| EDM Visual Freeze | `DO_NOT_CREATE` | 尚无独立 EDM 视觉批准 |
| Production | `REMAIN_BLOCKED` | Product Truth、Claim、正式素材、CTA 与 ESP Gate 未完成 |

## 决策规则

人工只能在 `decision-template.yaml` 中选择：

- `APPROVE`
- `APPROVE_WITH_MODIFICATION`
- `REJECT`
- `DEFER`

所有字段默认空白。Recommended Decision 只用于帮助审核，不得复制为人工决定。即使本次结构审核通过，也不能自动修改 Pattern、Recipe、Freeze、Product Truth、Claim、Asset 或 Production 状态。

## Recommended Human Gate

`S30_VISUAL_PATTERN_RECIPE_HUMAN_REVIEW`

完成具名审核后，应先进行 Decision Record Review；只有被接受的正式决策才可以进入后续项目状态更新。
