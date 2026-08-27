# Visual Router Integration

## 目的

`visual-system/` 是共享内部能力，用于在项目级别继承已批准视觉方向或自动选择最适合的结构 Pattern。它不新增用户可见 Skill，也不替代 Amazon Reference Matcher。

## 与 Amazon Reference System 的分工

| 层级 | 能力 | 决策对象 |
|---|---|---|
| Project | Visual Router | 跨渠道视觉方向、项目 Freeze、Pattern Ranking |
| Amazon Page | Reference Matcher | 竞品结构参考、同类目 Gate、Top references |
| Amazon Production | Decision Adapter / Templates | Gallery/A+ 顺序、已注册 Primitive、Renderer |

Visual Router 选择 `Pattern` 后，Amazon Channel Adapter 仍须调用现有 Reference Matcher、Category Semantics、Template Registry 与 Renderer Gate。两层不复制评分逻辑。

## 执行合同

```text
resolve_project
→ load projects/<id>/project-context.yaml
→ load projects/<id>/visual-freeze.yaml if present
→ load projects/<id>/visual-profile.yaml if current
→ run visual-system/routing/visual_router.py if needed
→ apply ADAPTER-AMAZON-JP
→ continue Planning / Production / Hardening
```

当 Context、素材状态、Registry、Pattern 或 Freeze 更新时，Profile 视为需重新生成。不得手工改 Router 评分来迎合单个项目。

## Freeze 合同

只有 `status: APPROVED`、`active: true`、具名人工、渠道兼容、Pattern 未 Deprecated 且必需素材满足时自动继承。

`status: CANDIDATE` 只供人工复核，不视为批准。Freeze 的创意范围不得扩张到 Product Truth、Claim、素材授权、Amazon Upload、Hardening 或 Mobile QA。

## 下游 Gate

Router 的输出最多决定视觉结构建议。以下 Gate 保持原顺序和所有权：

- Product Truth；
- Human Review；
- Claim Gate；
- Product Layer；
- Hardening；
- Mobile QA。

任一 Gate 未满足时，返回原有 `BLOCKED` / `PARTIAL_BUT_ACTIONABLE`，不得因 Pattern 高分而继续正式生产。
