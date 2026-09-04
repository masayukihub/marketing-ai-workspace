# Workflow Playbooks

这里保存面向日常业务的操作手册。先从仓库根目录 [`START_HERE.md`](../../START_HERE.md) 开始，再按任务进入对应手册。

| 手册 | 适用场景 |
|---|---|
| [`OPERATOR_PLAYBOOK.zh-CN.md`](OPERATOR_PLAYBOOK.zh-CN.md) | ChatGPT、Codex、飞书、GitHub 和四个中文入口如何协作 |
| [`BRIEF_FACTORY_PLAYBOOK.zh-CN.md`](BRIEF_FACTORY_PLAYBOOK.zh-CN.md) | Amazon、EDM、KOL、PR、视频、SNS、设计与 LP Brief |
| [`VISUAL_AI_PLAYBOOK.zh-CN.md`](VISUAL_AI_PLAYBOOK.zh-CN.md) | 产品卖点图、AI 场景、产品层合成、视觉 QA 与交付 |
| [`KOL_PR_PLAYBOOK.zh-CN.md`](KOL_PR_PLAYBOOK.zh-CN.md) | KOL/Creator、媒体、PR、名单、Brief、KPI、Tracking 与复盘 |
| [`GTM_WEEKLY_OPERATING_RHYTHM.zh-CN.md`](GTM_WEEKLY_OPERATING_RHYTHM.zh-CN.md) | 新品与 Campaign 的周报、依赖、风险、Owner 和 Decision Queue |
| [`GIT_GUIDE.md`](GIT_GUIDE.md) | Git 分支、提交、PR 和安全回退 |

## 使用原则

- 手册决定“如何执行”，不决定产品事实。
- 具名项目仍先读取最新 `project.yaml`、Product Knowledge、Project Memory 和 Decision。
- 普通用户只使用四个中文入口；内部模块由 `operator/task-routing.yaml` 自动选择。
- 默认执行到下一个 Material Human Gate，不在普通步骤反复确认。
- 未经授权不写飞书、不改 Product Knowledge、不上传 Amazon、不发送 EDM、不对外发布。
