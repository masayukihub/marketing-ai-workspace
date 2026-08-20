# Production Registry

Phase 7 的统一 Production Truth 与审批层。这里的状态控制外发资格；`production_truth/` 继续保留为 Phase 6 历史输入，不再被视为生产批准来源。

核心原则：

- `VERIFIED` 表示证据已核对，不等于获得发布批准。
- `APPROVED` 只能来自有姓名的人工审批，不由 Generator 或 Codex 自动写入。
- `INTERNAL_ONLY` 素材只能用于内部预览，Final Renderer 只能解析 `APPROVED` 素材。
- 所有审批通过 `production_readiness/apply_approvals.rb` 回写，并追加审计记录。
- `Pending Verification`、`UNVERIFIED`、`MISSING` 和冲突都可以是合法结果，但会阻止相应 Gate。

运行顺序：

```bash
ruby production_readiness/evaluate_readiness.rb
ruby production_readiness/build_review_pages.rb
ruby production_readiness/validate_registry.rb
```

人工审批后：

```bash
ruby production_readiness/apply_approvals.rb path/to/exported.csv --apply
ruby production_readiness/evaluate_readiness.rb
ruby production_readiness/build_review_pages.rb
```

