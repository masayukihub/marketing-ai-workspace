# 运行时契约

## 首选运行时

优先级：

1. `marketing-ai-workspace` GitHub `main` 中锁定的入口与兼容模块；
2. 已登记commit的 `masayukihub/jp-commerce-creative-flow`；
3. fork内的 SwitchBot JP Overlay；
4. fork内未修改的 `heymio/japan-listing-demo` Upstream Core；
5. 当前项目 `.agents/internal-skills/<module>/`；
6. `$CODEX_HOME/internal-skills/<module>/`；
7. 迁移期兼容位置 `.agents/skills/<module>/` 或 `$CODEX_HOME/skills/<module>/`；
8. 仅做策略/Brief，不声称实际渲染。

解析细节见 [internal-components.md](internal-components.md)。GitHub规则和旧Global副本不一致时，以已验证的GitHub Runtime为准；不得把旧Global声明当成可用功能。

## 阶段所有权

- Stage 0–7：Planning。
- Stage 7.5–8：Production。
- Stage 8.5–10：Hardening。
- 精确文件证据：Evidence Auditor。

下游发现上游缺口时返回：

```yaml
status: BLOCKED
missing_field: ""
return_to: "Product Truth | Planning | Production"
affected_asset_ids: []
```

不得在下游静默补写上游决策。

## 画面类型与制作能力

Production Handoff 额外传递 `visual_type`、实际看过的参考及视觉证据任务，详见 [商业画面制作](../../amazon-listing-creative/references/commercial-visual-production.md)。运行记录同时写 requested visual type、实际 Renderer/工具、输入输出和替代行为。

模板/排字/预览 Renderer 不等于摄影或机理 CG 生产服务。具备 Layout ID 或输出 PNG，不证明它能完成指定镜头、场景融合和部件动作。不具备能力时明确 `VISUAL_CAPABILITY_MISMATCH`，将缺口交回 Production；不能静默输出信息图后继续宣称商业成片达标。外部制作或自写脚本若被采用，也必须如实记录其身份并接受同一代表图检查，不继承未执行 Runtime 的通过状态。

## 状态与恢复

正式状态至少保留：

- Project Brief；
- Product Truth Packet；
- Creative Strategy Kernel；
- Production Handoff；
- Asset Ledger / Production Freeze；
- Delivery State。

聊天记录不是项目数据库。用户要求继续时优先读取这些正式状态，不重新解析全部历史。

## 兼容旧项目

旧项目使用 `amazon-japan-pdp-generator` 的Spec或HTML时，先建立迁移映射，不直接覆盖。稳定的Story、Claim、Asset与用户批准保持锁定；只把缺少的Truth、Handoff和Evidence状态补齐。
