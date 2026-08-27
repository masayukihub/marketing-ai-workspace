# Visual Pattern 接入

正式项目的 EDM 先读取同一份 `projects/<project-id>/project-context.yaml` 与 `visual-profile.yaml`。不要为 EDM 复制另一份 Project Context。

执行顺序：

```text
Project Visual DNA
→ channel_assignments.edm
→ EDM Page Recipe
→ Section Pattern
→ ADAPTER-EDM-JP
→ Existing Template / Module System
→ Existing Renderer
→ Product Layer / Asset Gate / Human Review / Hardening
→ Mobile QA / ESP Gate
```

## Match 与 Readiness

- `pattern_match` 只说明结构与项目的匹配度。
- `execution_readiness` 独立检查 Product Truth、Claim、素材、Pattern 生命周期与人工 Gate。
- Match 高而 Readiness 低时，只能生成内部 Review 或线框，不能进入正式 Renderer。
- `auto_apply.eligible: false` 时不得自动生产、导出或发送。

## 跨渠道继承

Amazon → EDM 只能继承 `project_visual_dna` 中的 Tone、Proof Strategy、Visual Rhythm、Image Strategy、Information Density、Conversion Style 与 Mobile Priority。

禁止继承 Amazon Gallery/A+ 的完整 Layout、尺寸、文案、图片、Claim、价格或 CTA。EDM 继续使用 600px、邮件客户端兼容和语义堆叠规则。

## Pilot Recipe 映射

`RECIPE-EDM-PRODUCT-LAUNCH-PROOF` 是 CANDIDATE，只提供结构建议。它映射到既有 `TPL-LAUNCH-A` 和 Module Registry，但不能覆盖 Stable Template Selector。

Pattern、Recipe、Template 与 HTML 必须分离。Router 推荐结构，既有 Runtime 最终决定 Template、Module、Renderer、Mobile QA 和 ESP Gate。

Visual Router 不能删除或替代 Product Truth、Claim Gate、Product Layer、Asset Gate、Human Review、Hardening、Mobile QA 与 ESP Gate。
