# S30 mini Visual Pattern / Recipe 人工审核包

状态：`PENDING_HUMAN`

本目录用于审核 S30 mini 的 Visual DNA、Amazon → EDM 继承边界、EDM Intent、Product Launch Recipe 与现有 Template 的条件兼容性。

## 文件

- `review.html`：面向营销人员的中文审核页面；
- `decision-template.yaml`：人工决策记录，所有人工字段初始为空；
- `asset-gap-register.yaml`：当前缺口登记，不代表补齐或批准；
- `review-scope.md`：范围、排除项、建议与 Gate。

## 使用方法

1. 先打开 `review.html`，阅读 Visual DNA、渠道差异、Recipe 与缺口；
2. 审核人只在 `decision-template.yaml` 的 `reviewer`、各 `decision`、说明字段与 `next_gate` 中填写结果；
3. 决策只能使用 `APPROVE`、`APPROVE_WITH_MODIFICATION`、`REJECT`、`DEFER`；
4. Recommended Decision 是系统建议，不能视为人工批准；
5. 填写后提交独立 Decision Record Review，不直接修改 Recipe、Pattern、Freeze 或 Production 状态。

## 特别规则

- Generic Recipe 中 `Mechanism Proof = CONDITIONAL`；
- S30 项目中 `Mechanism Proof = REQUIRED_WHEN_APPROVED_EVIDENCE_AVAILABLE`；
- `TPL-LAUNCH-A` 只是 `CANDIDATE_CONDITIONAL_MATCH`，Stable Template Selector 拥有最终选择权；
- Amazon Candidate Freeze 只适用于 `amazon_jp`，不得转成 EDM Freeze；
- 本审核通过也不代表 Product Truth、Claim、Asset、Production、ESP 或 Send 获批。

## 当前 Gate

Recommended Human Gate：`S30_VISUAL_PATTERN_RECIPE_HUMAN_REVIEW`

在 Product Truth、Approved JP Claim、正式素材、CTA 与 Legal/ESP 输入补齐前，EDM Production 必须保持 `BLOCKED`。
