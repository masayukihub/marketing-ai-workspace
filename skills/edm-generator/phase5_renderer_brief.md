# Phase 5 Renderer Brief

状态：**Approved Input Brief / Renderer Not Implemented**  
日期：2026-08-19  
Generator Baseline：`generator/generator_logic_v1.0/`  
Design Baseline：EDM Design Standard v1.0 + EDM Design System v1.0

## 1. Phase 5 Objective

将 Generator 已完成的 Campaign、Template、Message、Module、Copy 与 Asset 决策转换为可审核的视觉生产物。Renderer 不重新判断 Campaign Type，不重选 Template，不创造 Product Claim，也不改变 Frozen Design Rules。

## 2. Renderer Input

Renderer 必须直接读取以下版本化对象：

1. `campaign_brief`
2. `selected_template`
3. `module_sequence`
4. `copy`
5. `asset_plan`
6. `design_rules`
7. `visual_rhythm_rules`

最低机器输入建议：

```yaml
renderer_job:
  job_id: required
  campaign_brief_path: required
  decision_trace_path: required
  design_spec_path: required
  copy_draft_path: required
  asset_plan_path: required
  design_rules_path: standards/edm_design_rules_v1.0.yaml
  templates_path: design_system/templates_v1.0.yaml
  modules_path: design_system/modules_v1.0.yaml
  visual_rhythm_path: design_system/visual_rhythm_rules_v1.0.md
  output_locale: ja-JP
  desktop_content_width: 600px
  mobile_qa_viewports: [320, 375, 390, 414, 768]
```

### Input Gate

- Template 和 Module Sequence 必须来自冻结 Generator 输出，不允许 Renderer 自行替换。
- Copy 中的 `Requires Claim Check`、`Unknown`、`Unverified`、`Blocked` 不得渲染成确定性事实。
- Asset Plan 缺少官方产品、UI、包装、配件或安装关系时，Renderer 必须返回 `RENDER_BLOCKED_ASSET`。
- Price、Promotion、Period 或 CTA 未验证时，只能生成内部结构预览；不得标记为 Final。

## 3. Renderer Output

每个 Renderer Job 最少输出：

1. **Desktop EDM Preview**
2. **Mobile EDM Preview**
3. **Full-length EDM PNG**
4. **Editable HTML**
5. **Asset Manifest**
6. **Render QA Report**

推荐目录契约：

```text
renderer/outputs/<job_id>/
├── desktop_preview.png
├── mobile_preview.png
├── full_length_edm.png
├── editable_edm.html
├── asset_manifest.yaml
└── render_qa_report.md
```

这些文件仅在 Render QA 通过后标记为 `review_ready`；只有 Fact、Asset、Claim、Price、CTA 与 Legal Gate 全部通过后，才能标记为 `production_ready`。

## 4. Visual Production Principle

```text
真实产品素材
+
HTML/CSS Layout
+
AI Generated Background / Lifestyle Support
+
Typography / CTA / Price / Badge
```

### Layer Responsibility

- **真实产品素材**：产品本体、App UI、包装、配件、安装关系与 Detail Close-up 的唯一事实来源。
- **HTML/CSS Layout**：控制 600px Desktop 基线、Mobile Reflow、Typography、Spacing、CTA、Price、Badge、Legal 与 Module Rhythm。
- **AI Generated Support**：仅用于环境、人物、道具、背景、光线和气氛探索。
- **Composition**：官方产品素材与环境层组合时，保持轮廓、颜色、比例、接口、传感器、按钮、安装关系与功能事实不变。

```text
AI 不得重绘、重构、补画或替换产品本体与 App UI。
```

## 5. Rendering Flow

```text
Validated Generator Output
→ Renderer Job Validation
→ Template Layout Binding
→ Module Component Binding
→ Copy Slot Binding
→ Official Asset Resolution
→ Background / Lifestyle Support
→ Desktop Render
→ Mobile Semantic Reflow
→ Full-length Capture
→ Render QA
→ Review-ready Package
```

Renderer 不得回到 Campaign Classifier 或 Template Selector。发现上游冲突时，返回明确 Failure Code，并要求重新运行 Generator。

## 6. HTML/CSS Requirements

- Desktop 内容宽度基线固定为 `600px`。
- Module 组件使用语义化 HTML，Copy、URL、Price、Badge 与图片均保持可编辑。
- CSS 必须复用 Design System Module ID 与布局语法，不创建用途重叠的新 Template。
- Mobile 按语义顺序单列重排，不按 Desktop 左右坐标推导顺序。
- 图片保持原始比例；禁止破坏性裁切产品或隐藏关键 Proof。
- CTA 必须有明确动作/目的地，且每个 Module 最多一个 Primary CTA。
- Experimental Mobile 数值只用于测试，不得变成 Production Block。

## 7. Asset Composition Requirements

Asset Manifest 每项至少记录：

```yaml
asset_id:
asset_type:
product_id:
variant:
source_path:
source_id:
provenance:
usage_right:
last_verified:
module_id:
transformations:
ai_generated: false
ai_scope: null
```

- 产品图必须可追溯至官方或明确批准的源文件。
- AI 背景必须与产品图分层，保留替换能力。
- 合成后必须检查产品边缘、透视、尺度、接触阴影、安装关系与可辨认度。
- 缺少产品主素材时不得用 AI 生成“近似产品”继续渲染。

## 8. Render QA Contract

### Hard Block

- 产品本体或 UI 被 AI 重绘。
- 产品、UI、包装、配件、安装关系无 Provenance。
- Placeholder、Test Copy、Dummy URL 或缺图占位进入 Final。
- 未验证 Claim、Price、Promotion、Period、Deadline 或 CTA 被确定性渲染。
- Desktop 内容宽度偏离 600px 基线。
- 产品在 Desktop/Mobile 关键视口不可辨认或被破坏性裁切。
- 关键图片加载失败、HTML 模块缺失或 CTA 目的地失效。

### Responsive QA

- Desktop：至少验证 1280×800 与 1440×900 浏览器表面。
- Mobile：验证 320、375、390、414、768px。
- 无横向页面溢出。
- Module 顺序符合语义，不因 Reflow 改变 Message Hierarchy。
- CTA 可点击文本不换行，图片不变形，价格/Legal 不溢出。

### Output Status

```text
RENDER_BLOCKED_INPUT
RENDER_BLOCKED_ASSET
RENDER_BLOCKED_CLAIM
RENDER_BLOCKED_RESPONSIVE
REVIEW_READY
PRODUCTION_READY
```

## 9. Phase 5 Test Priorities

P0：

1. GTC-016：确认缺产品主素材时 Renderer 不创建任何假产品视觉。
2. GTC-017：确认缺 CTA / Promotion / Period 时只能生成内部结构预览。
3. Product Launch、Promotion、Education 各选择一个 Asset-complete 的真实案例进行 Desktop/Mobile Pair。

P1：

1. 多 SKU Product Grid 的 600px / Mobile Reflow。
2. 官方 UI 与 Product Detail 的无重绘组合。
3. Price、Coupon、Period、Legal 的动态槽位与长文本压力测试。

## 10. Explicit Exclusions

本 Brief 不实现 Renderer，不生成正式 EDM，不接入 ESP，不发送邮件，不创建新的 Template/Module，不修改 Frozen Standard 或 Design System。Phase 5 Implementation 必须另行执行并通过 Render QA。

