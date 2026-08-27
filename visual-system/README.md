# Visual Pattern Memory（Phase 1）

这是 `marketing-ai-workspace` 的共享内部视觉能力，不是用户可见 Skill。

它负责：

1. 读取 `projects/<project-id>/project-context.yaml`；
2. 优先检查人工批准的 `visual-freeze.yaml`；
3. 在没有可继承 Freeze 时，对 Registry 中的 Pattern 做确定性排序；
4. 生成 `visual-profile.yaml`；
5. 通过 Channel Adapter 把共享 Pattern 转成 Amazon JP、EDM、LP 或 Campaign HTML 的执行约束；
6. 保留 Product Truth、Claim、Asset、Human Review、Hardening 与 Mobile QA 的原有 Gate。

当前只实现 Phase 1：Pattern 合同、Router、两个真实项目验证和最小接入。它不生成最终页面，也不批准 Claim、素材或视觉成品。

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
python3 -m unittest discover -s visual-system/tests -p 'test_*.py' -v
```

中文使用方法见 [USAGE.zh-CN.md](references/USAGE.zh-CN.md)。
