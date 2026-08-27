# Visual Pattern Memory（Phase 1 + Phase 2A Pilot）

这是 `marketing-ai-workspace` 的共享内部视觉能力，不是用户可见 Skill。

它负责：

1. 读取 `projects/<project-id>/project-context.yaml`；
2. 优先检查人工批准的 `visual-freeze.yaml`；
3. 在没有可继承 Freeze 时，对 Registry 中的 Pattern 做确定性排序；
4. 生成 `visual-profile.yaml`；
5. 通过 Channel Adapter 把共享 Pattern 转成 Amazon JP、EDM、LP 或 Campaign HTML 的执行约束；
6. 保留 Product Truth、Claim、Asset、Human Review、Hardening 与 Mobile QA 的原有 Gate。

Phase 2A Pilot 增量加入 `Project Visual DNA`、独立的 Pattern Match / Execution Readiness / Evidence Confidence，以及 Amazon 与 EDM 共用的 `channel_assignments`。EDM Recipe 和 Section Pattern 只映射到既有 Template/Module Runtime，不替代 Renderer 或 ESP Gate。

当前 Pilot 只验证 S30 mini Amazon → EDM，Lock Ultra Max 仅作为低 Asset Readiness 负向回归。它不生成正式 EDM，也不批准 Product Truth、Claim、素材或视觉成品。

## 目录

| 目录 | 作用 |
|---|---|
| `references/` | Reference 摄入规则与现有参考系统适配器 |
| `patterns/` | 可复用的结构、节奏、组件与转化 Pattern |
| `registry/` | Pattern/Reference 注册表与 Schema |
| `routing/` | 排序、Freeze 优先与 Channel Adapter |
| `design-systems/` | 品牌级视觉约束，不保存单项目成品 |
| `tests/` | Router、Project Contract 与回归测试 |

## 运行

```bash
python3 visual-system/routing/visual_router.py --project projects/s30-mini
python3 visual-system/routing/visual_router.py --project projects/lock-ultra-max
python3 visual-system/routing/render_visual_review.py --project projects/s30-mini
python3 -m unittest discover -s visual-system/tests -p 'test_*.py' -v
```

中文使用方法见 [USAGE.zh-CN.md](references/USAGE.zh-CN.md)。
