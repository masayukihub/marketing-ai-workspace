# S30 mini Visual Pattern / Recipe 人工审核包

状态：`HUMAN DECISION COMPLETED / PROJECT VISUAL PLANNING LOCK ACTIVE / PRODUCTION REMAINS BLOCKED`

本目录用于审核 S30 mini 的 Visual DNA、Amazon → EDM 继承边界、EDM Intent、Product Launch Recipe 与现有 Template 的条件兼容性。

## 文件

- `review.html`：面向营销人员的中文审核页面；
- `decision-template.yaml`：赖晓洪（ライ）已填写的具名人工决策；
- `decision-record.yaml`：不可变、可校验的 Accepted Decision Record；
- `decision-record-review.yaml`：同一 PR 内完成的独立自动决策记录复核；
- `asset-gap-register.yaml`：当前缺口登记，不代表补齐或批准；
- `review-scope.md`：范围、排除项、建议与 Gate。

## 后续使用方法

1. 执行“继续 S30 mini”“做 S30 mini 的 EDM”或“继续日本电商内容生成”时，先由 Project Resolver 读取 Accepted Decision Record；
2. 没有适用 Approved Freeze 时，Router 自动继承 Project Visual Planning Lock，并输出 `reask_visual_direction=false`；
3. 用户明确改方向、渠道硬冲突、Pattern Deprecated、无兼容 Template 或新批准方向冲突时，才重新打开视觉方向审核；
4. 当前下一步只处理 `S30_CONTENT_CLAIM_ASSET_UNLOCK`；
5. 不因 Planning Lock 绕过 Product Truth、Claim、Asset、Renderer、Final Human、ESP 或 Send Gate。

## 特别规则

- Generic Recipe 中 `Mechanism Proof = CONDITIONAL`；
- S30 项目中 `Mechanism Proof = REQUIRED_WHEN_APPROVED_EVIDENCE_AVAILABLE`；
- `TPL-LAUNCH-A` 只是 `CANDIDATE_CONDITIONAL_MATCH`，Stable Template Selector 拥有最终选择权；
- Amazon Candidate Freeze 只适用于 `amazon_jp`，不得转成 EDM Freeze；
- 本审核通过也不代表 Product Truth、Claim、Asset、Production、ESP 或 Send 获批。

## 当前 Gate

Next Gate：`S30_CONTENT_CLAIM_ASSET_UNLOCK`

在 Product Truth、Approved JP Claim、正式素材、CTA 与 Legal/ESP 输入补齐前，EDM Production 必须保持 `BLOCKED`。
