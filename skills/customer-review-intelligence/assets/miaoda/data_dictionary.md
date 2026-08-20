# 妙搭数据字典

| 表 | 用途 | 主键/幂等键 | Skill 管理字段 | 妙搭协作字段 |
|---|---|---|---|---|
| `voc_review` | 审核后的用户原声 | `review_id` | 日文原文、来源ID、URL、raw snapshot、批次、评分、情绪、主题、置信度 | 人工状态、备注、负责人、优先级、复核时间、修正说明 |
| `voc_issue` | 聚合问题与优先级 | `issue_key` | 样本量、负面率、趋势、证据、置信度 | 状态、负责人、截止日、复盘备注 |
| `voc_action` | 产品改善 Backlog | `action_key` | 建议、依据、验收指标 | 状态、负责人、截止日、复盘结果 |
| `voc_marketing_insight` | 营销卖点与顾虑 | `insight_key` | 表达、禁用表达、渠道、证据 | 采用状态、负责人、实验结果 |
| `voc_import_batch` | 批次与数据质量 | `batch_id` | 覆盖状态、计数、manifest hash | 审核备注 |

`voc_review` 原始字段至少包括 `source`, `source_review_id`, `original_text`, `source_url`, `published_at`, `rating`, `author_display_name`, `raw_snapshot_ref`, `capture_batch_id`。清洗文本、翻译、摘要、主题、情绪、词云 token 和建议均为独立派生字段。`original_text` 不可由前端覆盖。

为未来真实飞书 Base 同步预留 `future_feishu_base_record_id`, `future_feishu_base_table_id`, `sync_status`, `sync_error`。预留字段不代表已经连接；只有读回真实 Base 记录后才能标记为同步成功。

枚举建议：

- `coverage_status`: `complete`, `zero_confirmed`, `partial`, `blocked`, `not_configured`, `unverified`
- `priority`: `p0`, `p1`, `p2`, `monitor`
- `confidence`: `high`, `medium`, `low`
- `workflow_status`: `new`, `triaged`, `in_progress`, `validating`, `done`, `wont_fix`

比例字段必须同时保存分子和分母。评论者公开显示名仅进入受控证据层，默认不在报告或管理层页面展示。
