# EDM Internal Runtime

本目录是 `$switchbot-japan-edm` 使用的内部确定性 Runtime，不是日常用户入口。

- 保留冻结的 Design System、Generator、Renderer、Truth Gate、审批状态机与回归资产。
- 不新增 `SKILL.md`，也不允许它绕过统一入口的事实和发布门禁。
- `VISUAL_DELIVERABLE_CANDIDATE` 不等于 `PRODUCTION_READY`。
- 截图中的 `switchbot-japan-edm-generator-v1-1-internal` 与 `switchbot-japan-edm-visual-template-skill` 源码尚未进入本仓库；取得完整目录、Manifest 和测试前，只保留接口映射，不宣称完成源码合并。
- 修改本 Runtime 前必须运行原有 Ruby、Renderer、Browser QA 和工作空间回归测试。
