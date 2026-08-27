# 运行时契约

## 首选运行时

优先级：

1. 当前工作区中的 `masayukihub/jp-commerce-creative-flow`；
2. 当前仓库 `.agents/skills/jp-commerce-creative-flow/` 与其Sibling Skills；
3. 已验证的 `heymio/japan-listing-demo` 加 SwitchBot JP Overlay；
4. 仅做策略/Brief，不声称实际渲染。

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
