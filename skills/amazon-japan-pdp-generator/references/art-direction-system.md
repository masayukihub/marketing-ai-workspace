# Art Direction System

Before deriving any Art Direction record, build `PRODUCT_SEMANTIC_CONTEXT` from the current product and the matching `category-semantics/<category>.json`. Story Role, Visual Objective, Scene, Technical Proof, Asset request and scoring may use only that context. `Semantic Relevance` is a hard Gate: any `CROSS_PRODUCT_SEMANTIC_CONTAMINATION` hit blocks the entire Art Direction result, regardless of the average quality score.

Art Direction 是 DESIGN 已批准后、正式 Asset Production 前的衍生执行层。它不新增 Workflow Phase、人工 Gate、Reference、Layout Primitive、Gallery/A+ 数量，也不得改写 `PRODUCT_PAGE_SPEC.json`。唯一输入是已锁定的 Product Page Spec；唯一目的，是把既有 Story、Copy、Claim、Visual Role、Primitive 与 Rhythm 转换成可执行的摄影、3D、合成、技术图和场景制作 Brief。

## 输出与冻结边界

- 输出 `spec/ART_DIRECTION_SPEC.json`、`review/ART_DIRECTION_CONTACT_SHEET.html`、Art Direction 指南、优先级、回归与 QA 报告。
- Gallery 固定 7 张；A+ 保持 7 Modules / 16 Units 或当前已批准结构。
- 必须记录输入 Spec hash、Story Sequence fingerprint、Gallery ID 与 A+ Module/Unit 结构；生成前后必须相等。
- Art Direction 只能补充视觉执行字段，不得修改 Claim、文案、顺序、Reference、Primitive、Visual Role、Gate 或产品事实。

## 每个视觉单元的最小字段

Gallery 每张图和 A+ 每个 Unit 都必须包含：`visual_objective`、`consumer_takeaway`、`hero_object`、`secondary_object`、`scene_type`、`composition`、`camera_angle`、`product_scale`、`product_position`、`background`、`lighting`、`depth`、`material_treatment`、`human_presence`、`lifestyle_props`、`technical_annotation`、`motion_action`、`negative_space`、`desktop_crop`、`mobile_crop`、`required_asset`、`preferred_asset_source`、`production_method`、`production_method_reason`、`risk`、`fallback`。

允许的 `production_method` 只有：

```text
OFFICIAL_ASSET_COMPOSITE
3D_RENDER
REAL_PHOTOGRAPHY
AI_SCENE_ONLY
TECHNICAL_DIAGRAM
UI_COMPOSITE
ILLUSTRATION
MIXED
```

## Product Layer 安全规则

- Product Layer 只能来自用户提供且已验证、已授权的官方产品素材或工程批准的官方 3D Render。
- AI 只能生成不含产品、Logo、日文、UI、技术文字或 Comparison Table 的 Scene Layer。
- Product Layer、Scene Layer、Graphic Layer 必须分层生产；消费者文字和技术标注由 HTML/CSS/SVG 程序化排版。
- Placeholder 可用于 Contact Sheet 与 Layout Review，但不得进入可发布 Final。

## 视觉生产规则

- 摄影、3D、技术图、AI Scene 的选择必须由该单元的 Consumer Question、Visual Role、证据需求和资产状态决定，不得按模板 ID 机械分配。
- 产品尺度、镜头、背景和光线必须形成可解释的页面节奏；连续重复需产生 warning，而不是随机换版。
- Desktop 与 390px Mobile 必须分别定义裁切；Mobile 不得只做 Desktop 中心裁切。
- 日本生活场景必须说明居住类型、空间尺度、家具、地板、收纳、人的出现方式和使用动作；禁止用泛化的“漂亮客厅”代替真实日本生活语境。
- 技术图必须区分 confirmed geometry、conceptual explanation 与 pending engineering validation；不得凭视觉想象制造结构、性能、Before/After 或未批准 Claim。

## Asset Brief 与优先级

`asset_requirements.xlsx` 必须包含 Asset ID、Used In、Purpose、Shot/Render Type、Angle、Crop、Resolution、Transparency、Required Product State、Lighting、Scene Requirement、Claim Dependency、Priority、Owner、Status、Fallback。`asset_gap_analysis.xlsx` 以相同 Asset ID 记录缺口、优先级、状态、Fallback 与 Owner。

- P0：阻断关键 Product Layer、机制 Proof、准确性或核心 Story 的资产。
- P1：显著影响日本场景可信度、所有权体验或视觉差异的资产。
- P2：不阻断结构理解、可用安全 fallback 完成的增强资产。

## QA 与 Contact Sheet

Contact Sheet 至少同时展示现状视觉、线框、推荐方向、生产方法、资产、风险、Desktop/Mobile crop 与人工 Decision/Comment。Desktop 1440×1000 和 Mobile 390×844 必须检查 broken image、overflow、可读字号、单元完整性和表单持久化。

Art Direction 的语义检查与字段完整性仍按真实元数据计算。品牌、真实感、构图、JP Fit 和总体视觉分在未观察成图前保持 null / NOT_ASSESSED；不得展示固定的基线分与推荐分暗示效果提升。生产 Brief 不能表示 Final Asset 已达到相同质量，也不得覆盖 Product、Claim、Asset、Mobile 或 Publish Gate。

## 命令

```bash
node scripts/generate_art_direction.mjs \
  --spec <output-dir>/spec/PRODUCT_PAGE_SPEC.json \
  --output <output-dir>

node tests/art_direction_regression.mjs \
  <output-dir>/spec/PRODUCT_PAGE_SPEC.json
```
