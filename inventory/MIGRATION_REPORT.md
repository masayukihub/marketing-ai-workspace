# Skill Migration Report

## 已迁移

| Skill | 方式 | 说明 |
| --- | --- | --- |
| amazon-japan-pdp-generator | 完整安全副本 | 保留 scripts、references、tests；补充独立 Node 依赖清单，不依赖本机缓存符号链接 |
| product-knowledge | 完整安全副本 | 作为版本副本；正式事实仍需 canonical source 验证 |
| switchbot-campaign-review | 完整安全副本 | 保留原正式名称 |
| customer-review-intelligence | 完整安全副本 | 作为 VOC Analyzer 正式实现；包含非敏感分类与采集配置，不包含评论原始数据 |
| amazon-listing-creative | 完整安全副本 | 保留独立 Creative 责任边界 |
| project-memory-manager | 完整安全副本 | 管理 Project Memory，而非产品事实 |
| influencer-marketing | 完整安全副本 | 提供 KOL 策略能力，不包含联系人数据库 |
| edm-generator | Curated 副本 | 迁移代码、规范、Schema 和测试；排除研究数据、邮件、输出和大体积历史素材 |

## 未迁移

| 内容 | 原因 |
| --- | --- |
| KOL Master 与联系人名单 | 可能含个人联系方式，需先脱敏和确认字段权限 |
| EDM `research/` | 包含邮件研究数据和证据截图，不适合直接提交 |
| EDM `output/`、`outputs/`、`production_output/` | 生成物、Review 截图和运行状态，不应作为源代码迁移 |
| EDM 大体积 `templates/historical/assets/` | 需要单独确认版权、Git LFS 和长期存储策略 |
| 浏览器日志、`.venv`、缓存 | 不属于可版本管理源文件 |
