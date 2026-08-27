---
name: amazon-japan-pdp-generator
description: 将产品营销资料、已确认事实与用户提供的官方产品素材转化为 KNOW→REFERENCE→PLAN→Story Gate→DESIGN→Layout Gate→PRODUCE→QA→Publish Gate、Spec 驱动、模板驱动、可恢复和可重渲染的日本 Amazon PDP。REFERENCE=ON 默认通过 Matcher 阈值与 Decision Adapter 真正改变 Gallery/A+ Story、Layout 和 Sequence；VISUAL_QUALITY=ON 默认以 Visual Role、节奏检测、SwitchBot Brand Fit 和反模板规则参数化现有 19 个 Primitive。Art Direction 在不改变 Story/Claim/Reference/Primitive 的前提下，把已批准设计转换为分层、可执行的资产生产 Brief。OFF 模式保留用于回归与排障。禁止复制竞品文案、图片、Trade Dress 或完整 Layout。正式产品本体禁止 AI 生成；AI 仅可用于无产品的场景、人物、背景和构图扩展。
---

# Amazon Japan PDP Generator V4

目标是“减少自由度，提升稳定度”。V4 保持 KNOW / PLAN / DESIGN / PRODUCE 四个生产阶段，并在 KNOW 与 PLAN 之间加入非人工 Gate 的 REFERENCE 决策层。禁止从营销资料直接跳到 Final Design：

```text
KNOW
→ REFERENCE
→ PLAN
→ Story Gate
→ DESIGN
→ Layout Gate
→ PRODUCE
→ QA
→ Publish Gate
```

## 必读资源

- 若任务指向现有项目，先使用 `project-context-resolver`，只消费 Amazon 所需的 Product Truth、Decision、Approved Claim、Visual Profile/Freeze 与 Asset 指针；不得自行全仓搜索上下文。
- 每次执行先完整读取 [spec-template-system.md](references/spec-template-system.md)、[decision-journey.md](references/decision-journey.md) 与 [input-schema.md](references/input-schema.md)。
- 进入 REFERENCE 时完整读取 [reference-library-system.md](references/reference-library-system.md)；只按需读取匹配到的 Reference Analysis、Pattern Library 与 [layout_primitive_mapping.json](reference-library/layout/layout_primitive_mapping.json)，不得把 Reference 当作产品事实源。
- DESIGN/PRODUCE 前读取 [visual-production-workflow.md](references/visual-production-workflow.md)、[visual-layout-system.md](references/visual-layout-system.md)、[visual-quality-system.md](references/visual-quality-system.md)、[japanese-copy-review.md](references/japanese-copy-review.md) 与 [template_library.json](templates/template_library.json)。进入资产生产 Brief 或 Art Direction 任务时，还必须完整读取 [art-direction-system.md](references/art-direction-system.md)。
- 用户要求模拟 Amazon Japan 消费者页面、Above-the-fold、Premium A+ 或页面 Fidelity QA 时，读取 [amazon-jp-fidelity-mode.md](references/amazon-jp-fidelity-mode.md)。
- 核对阶段、目录、Gate 与验收证据时读取 [output-contract.md](references/output-contract.md)。
- Story Gate、REFERENCE Adapter 或顺序变更相关任务必须读取 [story-sequence-lock.md](references/story-sequence-lock.md)；Asset Resolver、Product Layer 或 Publish Gate 相关任务必须读取 [asset-provenance-rules.md](references/asset-provenance-rules.md)。
- 涉及 Amazon 当前图片、Title、A+ 或合规规则时读取 [amazon-jp-policy-check.md](references/amazon-jp-policy-check.md)，并核对本次 Amazon 官方来源。
- SwitchBot 产品先查询工作区最小相关 Knowledge Unit，再调用 `product-knowledge` 核对 canonical record；聊天记忆和旧生成物不是产品事实源。

## PHASE 1 · KNOW

只理解产品，不规划图片，不生成 A+，不调用图像模型，不做高保真视觉。

输出：`spec/PRODUCT_BRIEF.json`、`review/product_understanding_cn.html`、`PROJECT_STATE.json`。

Brief 必须区分 Approved、Confirmed、Need Verification、Conflict、Blocked、Prohibited、Not Available。至少包含产品、品类、受众、核心问题、核心价值、卖点候选、Feature/Benefit、场景、证据、顾虑、限制、兼容、FAQ、竞品、Claim、价格、来源映射与事实检查。不得把未知或旧信息补成事实。

## REFERENCE · 设计决策知识层

只读取 `spec/PRODUCT_BRIEF.json` 与 `reference-library/`，输出 `reference/REFERENCE_SELECTION.json` 和 `reference/REFERENCE_SELECTION.md`。它不是新的人工 Gate，必须在 PLAN 之前运行；`REFERENCE=ON` 为正式默认模式。

Matcher 使用 Category、Product Complexity、Primary USP、Consumer Tension、Product Type、Story Requirement、Technical Complexity 与 Target Audience；Brief 未提供的字段保持 `Not Available`，不推断为事实。结构候选必须同时通过 Same Category、Minimum Match Score、Product Role Match 与 Page Intent Match。跨类目或低分候选只能用于 Problem Expression / Visual Inspiration，不得影响 Gallery/A+ 结构与 Module Order。匹配信号不足时不得强行生成 Top 3；没有结构合格候选时 PLAN 直接阻断。

REFERENCE 与 PLAN 之间的 `Reference Decision Adapter` 必须将合格 Pattern 转换为 Gallery Story、A+ Story、Layout 与 Sequence 决策。每个候选决策必须通过 Role Match、Renderer Availability、390px Mobile Readability 与 Claim Provenance 四项硬 Gate；任一失败不得进入正式 Spec。输出 `reference/REFERENCE_DECISION_TRACE_V2.{json,md}` 与 `reports/REFERENCE_DECISION_TRACE.md`，逐项记录 Reference Source、Learned Principle、SwitchBot Adaptation、Layout Decision 与 Intentionally Not Copied。

`REFERENCE=OFF` 或 `--reference-mode off` 仅用于 regression / troubleshooting；不得调用 Decision Adapter。旧 `PROJECT_STATE.json` 缺少 Reference 字段时自动以 OFF 兼容运行，不强制迁移。再次显式设为 ON 后，必须先完成 REFERENCE。

REFERENCE 只提供故事结构、信息架构、密度控制与视觉节奏原则。禁止复制竞品文案、图片、Trade Dress、Logo、UI、技术图或完整 Layout；生产仍只使用 19 个现有实体模板、官方 Product Layer 与程序化 Graphic Layer。详细契约见 [reference-library-system.md](references/reference-library-system.md)，浏览入口为 [reference_library.html](reference-library/viewer/reference_library.html)。

## PHASE 2 · PLAN

基于 Product Brief 与已完成的 `REFERENCE_SELECTION.json` 建立 `SELLING_POINT_MATRIX.json` 与 `PRODUCT_PAGE_SPEC.json`。ON 模式必须由 Decision Adapter 产生真实、可追踪的 Story/Layout/Sequence 差异，不允许只把 Reference 写入 metadata；OFF 模式保持 V4 原有 PLAN。生成 Story Review 后停止。

固定消费者决策顺序：

```text
理解产品 → 产生兴趣 → 理解核心优势 → 看到真实场景 → 相信产品 → 判断适不适合自己 → 消除购买顾虑
```

- 商品图固定 7 张，一图只回答一个主要购买问题；不按 Feature 数量扩图。
- A+ 保持 5–8 个模块。Hub 3 基准保持 7 模块 / 16 内容单元；Unit 组合进 Module。
- 商品图负责快速判断，A+ 负责解释、证明、适配与异议消除，不原样重复。
- 每个视觉必须指定 `template_id`，但 PLAN 不生产最终视觉。

Gate 1 输出 `review/story_review.html`，确认 Hero Value、7 图结构、A+ Story、最终日文 Headlines 和 Selling Point Hierarchy。未批准时 DESIGN/PRODUCE 必须阻断。

Story Gate 一经 Approved，Gallery 与 A+ 的 ID、顺序、增删、合并和拆分即被锁定。REFERENCE Adapter 此后只可注释、映射和补充 Reference 决策，不得重排或改变结构。需要结构调整时必须显式 Reset Story Gate、解除锁定、重新运行 PLAN，并重新批准 Story。详见 [story-sequence-lock.md](references/story-sequence-lock.md)。

## PHASE 3 · DESIGN

只有 Story Gate 为 Approved 才可进入。此阶段完成 Asset Resolver、模板匹配、Grid、Product/Text/Safe Area、桌面/移动规则与低/中保真整页。

输出 `review/layout_review.html`：真实官方 Product Layer、Placeholder/已授权 Scene Layer、最终文案、最终 Template 与 Layout。未批准时 PRODUCE 必须阻断。

所有视觉只可从 `templates/amazon/<template>/` 的实体模板包选择。每包含 `template.json`、`template.html`、`template.css`、`template.svg`、`preview.jpg`、`README.md`。模板存在不代表必须使用，不得为凑模板增加页面模块。

## PHASE 4 · PRODUCE

只有 Layout Gate 为 Approved 才可进入。所有下游内容只读取落盘后的 `spec/PRODUCT_PAGE_SPEC.json`：HTML、SVG、JPEG、Review、Preview、8 个 XLSX、SEO、Comparison、Asset reports 与 `reports/`。`final/`、`export/` 只在 Publish Gate `PASS` 后生成；`BLOCKED` 时必须不存在，并写入 `reports/FINAL_OUTPUT_NOT_GENERATED.md`。Planner 选择的每个 Primitive 必须在 renderer registry 中存在；A+ 同时生成 Desktop 与 780px Mobile asset，并在 390px Preview 中由 `<picture>` 自动切换。

Headline、Sub Copy、产品图、Scene、Template、卖点顺序发生变化时，只改 Spec 或 Asset Mapping 后重渲染；Flattened JPG 不是唯一源文件。

## Visual Quality Layer

`VISUAL_QUALITY=ON` 是正式默认渲染模式；`VISUAL_QUALITY=OFF` 只用于 Before/After regression 与排障。该层不增加 Workflow Phase、人工 Gate、Reference、Primitive、模块、内容单元或工作簿，只参数化现有 19 个 Primitive 的背景、构图、商品位置、卡片结构、密度、比例与 Mobile 行为。

每个 Gallery / A+ 模块必须获得 IMPACT、EXPLAIN、DETAIL、BREATHE、SCENARIO、PROOF、COMPARE、CLOSURE 之一的视觉角色。系统对 Background、Layout Family、Product Position、Card Structure、Text Density 与 Product Scale 分开检查；连续三次及以上相同即输出 `VISUAL_RHYTHM_WARNING`。只有 Story 连贯性确实需要时才能保留，并写明 Decision Reason，禁止随机换版、机械深浅交替或删减必要信息提高分数。

Gallery 继续承担 Decision Acceleration；A+ 承担 Understanding、Trust 与 Story。A+ 不得成为 Gallery 放大版。Mobile 必须保留各视觉角色差异，不得把所有模块折叠为同一圆角长卡。输出 `reports/VISUAL_QUALITY_MANIFEST.json`；评分用于审阅，不得覆盖 Claim、Asset、Mobile、Story Lock 或 Publish Gate 硬失败。完整规则见 [visual-quality-system.md](references/visual-quality-system.md)。

## Art Direction Layer

Art Direction 是 DESIGN 已批准后、正式 Asset Production 前的衍生执行层，不新增 Phase 或人工 Gate。它只读取锁定的 `PRODUCT_PAGE_SPEC.json`，把既有 Story、Copy、Claim、Reference、Visual Role、Primitive 与 Rhythm 转换为 Gallery 7 张和全部 A+ Unit 的摄影、3D、技术图、合成与日本生活场景 Brief；不得反向改写 Spec 或重排 Story。

每个单元必须定义视觉目的、消费者 takeaway、主体/次要对象、场景、构图、镜头、产品尺度/位置、背景、光线、景深、材质、人/道具、技术标注、动作、留白、Desktop/Mobile crop、所需素材、优先来源、生产方法、理由、风险与 fallback。Product Layer 永远使用已验证官方素材；AI 只生产无产品、无 Logo、无文字、无 UI 的 Scene Layer。输出 `spec/ART_DIRECTION_SPEC.json`、`review/ART_DIRECTION_CONTACT_SHEET.html`、Art Direction 指南/优先级/回归报告，并升级既有 `asset_requirements.xlsx` 与 `asset_gap_analysis.xlsx`，但工作簿总数保持 8。完整规则见 [art-direction-system.md](references/art-direction-system.md)。

Art Direction 必须先建立 `PRODUCT_SEMANTIC_CONTEXT`。Visual Objective、Scene、Technical Proof、Asset 与评分只能读取当前产品和匹配品类的 semantic layer；`Semantic Relevance` 是硬 Gate，不得用综合分覆盖。跨产品语义命中即 `CROSS_PRODUCT_SEMANTIC_CONTAMINATION` P0，Art Direction 整体阻断。

## Amazon JP Fidelity Preview Mode

`PREVIEW_MODE=AMAZON_JP_FIDELITY` 是消费者页面 Fidelity 模式，保留既有 Amazon Preview、Mobile Preview、Design Review 与 Art Direction Review，不替代它们。该模式从同一 `PRODUCT_PAGE_SPEC.json` 渲染 Amazon 风格 Header/Search、Gallery、Title、Rating、Price、Bullet、Buy Box、Product Description、1464px Premium A+ Carousel/Overlay、Comparison 与 FAQ；不得出现内部 Dashboard、评分卡、Source ID、状态芯片或 Fixture 数据。

Spec 缺少价格、评分、评论数、配送、库存或卖家数据时必须显示 `—` / `情報なし`，不得从公开页面、回归快照或示例值反写 Product Truth。当前 Amazon 页面仅可作为标记为 `LIVE_REFERENCE_ONLY` 的结构/密度参考。Desktop 与 390px consumer view、Gallery 切换、A+ Carousel、broken image、overflow、missing content、console error 均需实际浏览器 QA。完整契约见 [amazon-jp-fidelity-mode.md](references/amazon-jp-fidelity-mode.md)。

## 三层素材硬规则

```text
Official Product Asset = Product Layer
AI / Stock / Lifestyle = Scene Layer
HTML / CSS / SVG = Graphic Layer
```

正式上线 Product Layer 必须同时满足 `source_origin = User Provided Official`、允许的官方素材类型、`product_body_ai_generated = false`，且 provenance 为 `source_type = official`、`file_resolved = true`、`source_verified = true`、`usage_approved = true`、`product_layer_allowed = true`。`resolved` 只代表文件找到，绝不等于官方、已验证或已授权。官网下载图只可做结构研究或回归 Fixture，Publish Gate 必须 Blocked。详见 [asset-provenance-rules.md](references/asset-provenance-rules.md)。

AI 不得生成或重画 SwitchBot 产品、Logo、日文、Comparison Table、Technical Diagram 文字或 UI。消费者文字、表格、技术标签全部程序化排版。

Asset Resolver 优先级：

```text
官方场景图 → 官方白底/Render → 已授权素材 → AI无产品场景 → Placeholder
```

未授权、Fixture、测试夹具与 Placeholder 不得进入可发布 Final。

产品评分/评论数只有在值、来源、允许的 `source_type` 与批准状态均可验证时才显示。缺失或来源类型未知时输出 `—`，禁止使用 `4.6`、`132` 或任何固定测试评分补位。

## Gate 与 Force

- `story_gate != approved`：阻断 DESIGN 和 PRODUCE。
- `layout_gate != approved`：阻断 PRODUCE。
- `--force` 只允许输出带风险警告的审阅产物，不构成业务、法务、品牌或发布批准。
- `internal-test` 只用于样例回归；不得写成外部 Publish Ready。
- Structural Gate Pass 不得覆盖 Publish Gate Blocked。
- Publish Gate `BLOCKED` 时必须删除/拒绝生成 `final/` 与 `export/`，并输出精确标记 `FINAL_OUTPUT_NOT_GENERATED\nReason: Publish Gate BLOCKED`；只有 `PASS` 可创建交付目录。

Publish Gate 独立检查 Product Accuracy、Claim、Japan Localization Copy、Template/Layout、390px Mobile、Asset Authorization 与 SwitchBot Amazon Visual Consistency。Mobile Readability 不是“无 overflow 即通过”，还必须检查有效字号、标题/正文行数、字符密度、双栏折叠、Padding、CTA 与裁切。

## 标准命令

```bash
REFERENCE=ON node scripts/run_phase.mjs --input <pdp-input.json> --output <output-dir> --phase know
REFERENCE=ON node scripts/run_phase.mjs --output <output-dir> --phase reference
REFERENCE=ON node scripts/run_phase.mjs --input <pdp-input.json> --output <output-dir> --phase plan
# 审核人更新 Story Gate 后
node scripts/run_phase.mjs --output <output-dir> --phase design
# 审核人更新 Layout Gate 后
node scripts/run_phase.mjs --output <output-dir> --phase produce
```

恢复、从 Spec 和重渲染：

```bash
node scripts/run_phase.mjs --input <pdp-input.json> --output <output-dir> --resume
node scripts/run_phase.mjs --output <output-dir> --phase design --from-spec <PRODUCT_PAGE_SPEC.json>
node scripts/run_phase.mjs --output <output-dir> --rerender --from-spec <PRODUCT_PAGE_SPEC.json>
```

Hub 3 等内部回归可在 PLAN/DESIGN 分别使用 `--gate-mode internal-test` 模拟两次批准；每次命令仍只执行一个阶段。

Reference OFF 回归或旧项目排障：

```bash
REFERENCE=OFF node scripts/run_phase.mjs --input <pdp-input.json> --output <output-dir> --phase know
REFERENCE=OFF node scripts/run_phase.mjs --input <pdp-input.json> --output <output-dir> --phase plan
```

Visual Quality OFF 仅用于旧视觉回归；Reference 模式保持独立：

```bash
VISUAL_QUALITY=OFF node scripts/run_phase.mjs --output <output-dir> --rerender --from-spec <PRODUCT_PAGE_SPEC.json>
```

Story 与 Layout 已批准后生成可执行的 Art Direction/Asset Brief：

```bash
node scripts/generate_art_direction.mjs --spec <output-dir>/spec/PRODUCT_PAGE_SPEC.json --output <output-dir>
node tests/art_direction_regression.mjs <output-dir>/spec/PRODUCT_PAGE_SPEC.json
node tests/semantic_contamination_regression.mjs <output-dir>/spec/PRODUCT_PAGE_SPEC.json
```

Amazon JP Fidelity Preview：

```bash
PREVIEW_MODE=AMAZON_JP_FIDELITY node scripts/amazon_jp_fidelity.mjs \
  --spec <output-dir>/spec/PRODUCT_PAGE_SPEC.json \
  --output <review-project-dir> \
  --prefix <PRODUCT_PREFIX>
```

兼容的一次性入口 `generate_pdp.mjs` 仅供旧自动化迁移，不是 V4 默认生产方式。浏览器 QA、证据附加、结构验证与同步测试命令见 [output-contract.md](references/output-contract.md)。

## 完成标准

- KNOW / REFERENCE / PLAN / DESIGN / PRODUCE 可独立调用、恢复；`PROJECT_STATE.json` 正确记录 Reference 状态与双 Gate。
- REFERENCE 输出结构/灵感候选分离、阈值结果与组合策略；ON 模式产生 7 Gallery + 7 A+ 共 14 个 Accepted Decision Trace，OFF 模式不调用 Adapter。
- `PRODUCT_PAGE_SPEC.json` 是所有页面/设计/工作簿的唯一源；衍生文件带同一 Spec hash。
- 正好 7 张商品图；A+ 模块数不因升级增加；每个视觉有正式 `template_id`。
- Gate 2 未通过时没有高保真 Final Render。
- Desktop 1440×1000 与 Mobile 390×844 完成浏览器 QA；console error、broken image、horizontal overflow、missing content 均为 0，Mobile Readability Gate PASS；8 个 XLSX 完成结构与视觉检查。
- Amazon Preview 不暴露内部状态或虚构评分；Design Review 对每个 Gallery 和每个 A+ Unit 显示 ID、Consumer Question、Story Role、Main Message、Selected Reference、Reference Role、Decision Reason、Learned Principle、SwitchBot Adaptation、Layout Primitive、Why This Layout、What Was Not Copied 与 Status。
- A/B/C/D 局部变更回归证明 Copy、Scene、顺序、Claim 的影响可追踪，且不无故重跑 KNOW。
- Publish Gate 对 Fixture、未授权产品素材、未批准 Claim、未通过日文审核或缺少 Mobile 证据保持 Blocked。
- Story Approval 后的 sequence fingerprint 在 `PROJECT_STATE`、Spec 与重新计算结果之间保持一致；删除/重写 Spec lock 或结构变更未经过 Reset + Re-PLAN + Re-approval 时硬失败。
- Publish Gate `BLOCKED` 时 `final/`、`export/` 不存在且未生成标记存在；`PASS` 回归 Fixture 验证两目录只在 PASS 后创建。
- Visual Quality 默认 ON；Visual Role、节奏警告与 Decision Reason 可追踪，Gallery/A+ 角色分离，390px Mobile 保留角色差异；OFF 显式回归可重现旧视觉输出。
- Art Direction 覆盖 7 张 Gallery 与全部 A+ Unit；输入 Spec hash、Story fingerprint、ID/顺序保持冻结；生产方法、Product Layer、Desktop/Mobile crop、P0/P1/P2 Asset Brief 和人工 Contact Sheet 可追踪，且不新增 Primitive、Reference、Gate、模块或工作簿。
