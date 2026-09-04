# Skill Cleanup — 2026-09-04

## 结论

本轮只删除三个没有实际 Runtime、没有 `SKILL.md`、没有脚本/测试，并且已有正式替代入口的空壳目录。

删除不代表对应业务能力被取消；业务继续由正式入口和成熟内部模块承担。

## 已删除

| 旧目录 | 删除原因 | 正式替代 |
|---|---|---|
| `skills/campaign-review/` | 仅有 180 字节 Alias README，无执行代码、Schema、测试或独立数据契约 | 用户从 `$switchbot-japan-campaign` 的 `REVIEW` 模式进入；内部使用 `skills/switchbot-campaign-review/` |
| `skills/voc-analyzer/` | 仅有 Alias README，无执行代码、Schema、测试或独立数据契约 | 用户从 `$jp-commerce-insights` 的 `VOC` 模式进入；内部使用 `skills/customer-review-intelligence/` |
| `skills/kol-database/` | 仅有“Not Migrated”说明，无正式 Skill；真实名单可能含私人联系方式，不应复制进 GitHub | KOL/PR 从 `$switchbot-japan-campaign` 进入，内部使用 `influencer-marketing`；名单保存在授权的私有 Source of Record |

Git 不保存空目录；对应 README 删除后，上述目录自然消失。

## 明确保留

以下能力有真实用途，不能因为不是用户入口就删除：

- `product-knowledge`：产品事实、Claim、价格与兼容性治理；
- `project-context-resolver`：项目和任务上下文路由；
- `project-memory-manager`：项目背景、风险、Decision 与 Next Action；
- `jp-commerce-insights`：日本市场、关键词、竞品和 VOC 统一入口；
- `jp-commerce-content-flow`：Amazon JP 内容与视觉统一入口；
- `switchbot-japan-campaign`：GTM、KOL/PR、Tracking 和复盘统一入口；
- `switchbot-japan-edm`：日本 EDM 统一入口；
- `amazon-japan-pdp-generator`：内部 Review HTML / PDP 兼容渲染能力；
- `amazon-listing-creative`：受控单张创意探索方法；
- `customer-review-intelligence`：评论采集、实体映射、分类和分析；
- `switchbot-campaign-review`：可复现的数据清洗、指标和复盘 Runtime；
- `influencer-marketing`：KOL 筛选、合作模型、Brief、权利和衡量方法；
- `edm-generator`：已验证的 EDM Design System、Generator、Renderer 和 QA Runtime；
- `visual-system/`：跨 Amazon、EDM 和 Campaign 的内部视觉 Pattern 与 Router。

## 删除标准

未来只有同时满足以下条件，才建议直接删除一个 Skill 目录：

1. 没有正式 `SKILL.md`；
2. 没有脚本、Schema、测试或生产 Runtime；
3. 没有独立且仍有效的数据契约；
4. 已有明确的正式替代入口；
5. 全仓库搜索没有有效运行引用；
6. 删除不会破坏历史结果复现、Runtime Lock 或 Project Manifest；
7. 完整 CI 通过。

只要仍有成熟代码、回归测试、历史模板或内部路由职责，就应先降级为内部模块，而不是直接删除。

## 用户入口保持不变

日常仍只使用：

- `$jp-commerce-insights`
- `$jp-commerce-content-flow`
- `$switchbot-japan-campaign`
- `$switchbot-japan-edm`

本轮不修改 Product Truth、Project Memory、项目状态、Runtime Lock、飞书、Amazon、EDM 发送或任何外部发布状态。
