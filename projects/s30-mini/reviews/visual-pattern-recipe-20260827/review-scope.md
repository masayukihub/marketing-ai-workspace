# S30 mini Visual Pattern / Recipe Human Review Scope

## 审核目的

本次已由赖晓洪（ライ）完成 S30 mini 项目视觉原则与 Amazon → EDM 结构适配审核，并将批准范围应用为 Project Visual Planning Lock。它不是产品事实、素材、最终视觉或发布审批。

状态：`HUMAN DECISION COMPLETED / PROJECT VISUAL PLANNING LOCK ACTIVE / PRODUCTION REMAINS BLOCKED`

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

## 已写入的人工决定

| 审核对象 | 人工决定 | 生效范围 |
|---|---|---|
| Project Visual DNA | `APPROVE_WITH_MODIFICATION` | 仅用于 S30 Amazon JP / EDM 项目级视觉规划 |
| EDM Channel Intent | `APPROVE` | 与新品价值理解任务匹配 |
| Recipe Core | `APPROVE` | 产品识别 → 利益 → 行动 → 品牌收尾清晰 |
| Mechanism Proof | `APPROVE` | Generic `CONDITIONAL`；S30 在已批准 Claim 与素材齐备时自动启用 |
| Optional Sections | `APPROVE_WITH_MODIFICATION` | 按已批准证据与 Intent 条件启用，不逐项重问 |
| Template Mapping | `APPROVE` | `TPL-LAUNCH-A` 只作条件推荐，Stable Selector 保留最终决定权 |
| Lifecycle | `KEEP_CANDIDATE` | 当前只有单项目 Pilot 证据 |
| EDM Visual Freeze | `DO_NOT_CREATE` | 尚无独立 EDM 视觉批准 |
| Production | `REMAIN_BLOCKED` | Product Truth、Claim、正式素材、CTA 与 ESP Gate 未完成 |

## 决策规则

已填写的人工决定保存在 `decision-template.yaml`，不可变记录保存在 `decision-record.yaml`。合法 Decision 值为：

- `APPROVE`
- `APPROVE_WITH_MODIFICATION`
- `REJECT`
- `DEFER`

本次只批准项目规划方向。即使结构审核通过，也不能自动修改 Pattern/Recipe 生命周期、创建 Final Freeze、批准 Product Truth/Claim/Asset 或进入 Production。

## 当前后续 Gate

`S30_CONTENT_CLAIM_ASSET_UNLOCK`

Decision Record Review 已在本 PR 内完成并通过。该 Gate 完成后直接进入 Existing EDM Runtime → Stable Template Selector → Renderer → Desktop/Mobile QA → Final Human Review → ESP Gate，不再增加视觉方向选择 Gate。
