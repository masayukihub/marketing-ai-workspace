# Phase 4 EDM Generator Contract

状态：**Contract Frozen / Generator Not Implemented**  
日期：2026-08-19  
Design Standard：`standards/edm_design_rules_v1.0.yaml`  
Design System：`design_system/*_v1.0.*`

本文件定义 Phase 4 正式 EDM Generator Skill 的输入、依赖、决策流程与输出边界。它不是 Renderer、Template 实现、Module 实现或正式 EDM。

## 1. Contract Principles

1. Product Truth、Claim、Price、Promotion、Period、CTA Destination 与 Asset provenance 必须可追溯。
2. Generator 每次只解决一个 Primary Objective；无法确认时返回 `BLOCKED`，不猜测。
3. Template Selection 必须返回一个冻结 Variant；不得让 Tier D 覆盖 Tier A 或日本本地化规则。
4. Hard Rule 违反令 `QA = BLOCKED`；Soft Rule 偏离需要原因；Experimental Rule 仅提供建议。
5. 产品本体、App UI、包装、配件与安装关系不得由 AI 重绘或补画。
6. Phase 4 首先产出可审核 Design Spec；Renderer 仍在本 Contract 范围外。

## 2. Minimum Input

```yaml
product: null
campaign_theme: null
objective: null
promotion: null
period: null
cta_destination: null
```

六个字段允许缺失，但缺失不等于空值、无促销或 Evergreen。Generator 必须按下表处理：

| Field | Normalized form | Missing behavior | Production gate |
|---|---|---|---|
| `product` | product_id / product list / brand scope | 查询 Product Knowledge；无法唯一解析时请求确认 | 未解析产品、Variant、Bundle 或能力归属时 `BLOCKED` |
| `campaign_theme` | 一句话主题 + audience context | 可从已确认 Campaign Brief 提取；不能唯一提取则标 `Unknown` | 可先建立问题清单，但不得生成 Final Message |
| `objective` | 一个受控 Primary Objective | 从 Brief 提议候选并请求确认；不得自行选择多个 | 缺失或冲突触发 `PRIMARY_OBJECTIVE_MISSING_OR_MULTIPLE` |
| `promotion` | level + offer facts + verification state | 保持 `Unknown`；不得默认 `none` | 任何 Price/Coupon/Deadline 模块在事实未验证时 `BLOCKED` |
| `period` | start/end/timezone + verification state | 对非时效内容可标 `Not Applicable`；促销、倒计时与 Last Chance 必须补齐 | 时效型 Campaign 缺失触发 `PROMOTION_FACT_UNVERIFIED` |
| `cta_destination` | destination type + verified URL/route | 可先写 CTA intent，不得编造链接 | Final 缺失触发 `CTA_DESTINATION_INVALID` |

可选输入：audience、channel、product_count、product_familiarity、asset_inventory、comparison_data、approved_claims、marketplace、legal_requirement、desired_send_time。可选输入不能覆盖最低输入和 Hard Rule。

## 3. Knowledge Dependencies

| Dependency | Required content | Source/gate |
|---|---|---|
| Product Knowledge | product identity、Variant/Bundle、capability owner、status、limitations | Product Knowledge Hub；JP applicability 与 last_verified 必查 |
| Brand Rules | Brand principles、naming、visual boundaries | Design Standard v1.0 + current approved brand source |
| Claim | approved wording、conditions、allowed channels | Approved Claim only；Pending/Conflict/Prohibited 不得外发 |
| Pricing | product、market、channel、tax basis、effective period | dated channel-specific source |
| Assets | source path、asset type、product/variant mapping、usage right | official/verified assets with provenance |
| Campaign Brief | audience、theme、objective、promotion、period、destination | timestamped approved brief |
| Human Decisions | frozen Template/Module/Rhythm result | `research/phase3_design_system_human_decisions.csv` |

Dependency 输出必须携带 `status`、`source_id/source_path`、`last_verified` 与适用条件。`Pending Verification`、`Conflict`、`Unknown`、`Not Available` 与 `Partial` 是合法结果。

## 4. Decision Flow

```text
Input
→ Brief
→ Campaign Type
→ Template Selection
→ Message Hierarchy
→ Module Composition
→ Copy
→ Asset Resolution
→ Design Spec
→ QA
```

### 4.1 Input → Brief

- 规范化六个最低输入并记录缺口，不静默默认。
- Product Knowledge 解析 `product_id`、Variant、Bundle 与能力归属。
- 输出 `resolved`、`partial`、`conflict`、`blocked` 四态 Brief。

### 4.2 Brief → Campaign Type

- Campaign Type 必须来自受控枚举。
- Primary Objective 必须唯一，并映射到 `template_selection_rules_v1.0.yaml` 的 exact matrix。
- 无法唯一判断时返回 `CAMPAIGN_TYPE_UNRESOLVED` 或 `PRIMARY_OBJECTIVE_MISSING_OR_MULTIPLE`。

### 4.3 Template Selection

- 先按 Campaign Family 过滤，再按 Primary Objective 精确选择 Variant。
- 再检查 product_count、promotion、assets、comparison/UI availability。
- 四组相似结构使用冻结的 responsibility boundary，不允许跨 Family 由分数反向覆盖。
- 仍有多个候选时返回 `BLOCKED_TEMPLATE_SELECTION_AMBIGUOUS`，不得随机选择。

### 4.4 Message Hierarchy

- 生成一个 Primary Objective、一个 Primary Message、默认一个 Primary USP。
- Secondary USP、Proof、Promotion 与 CTA 必须服务于同一任务。
- 日文文案遵守 Japan Localization 与自然语义换行；不从 Tier D 推导日文密度或 CTA。

### 4.5 Module Composition

- 从 Template required sequence 开始，只加入满足输入与资产条件的 optional module。
- 使用有限验证 Pass；禁止递归自动插入 Module。
- 所有 required_inputs、asset_requirements、claim/promotion gates 先于视觉节奏。
- Rhythm 偏差只记录 Explain/Advisory，不能覆盖 Hard Rule。

### 4.6 Copy

- 仅使用 Approved/allowed Claim 与当前有效 Promotion/Price。
- 缺失事实保留内部状态，不生成看似完成的 Placeholder Copy。
- 日本市场外发文案必须自然、具体、可理解，不做中文直译。

### 4.7 Asset Resolution

- 输出每个 Module 所需 Asset、已解析 Asset、缺失 Asset、来源与使用边界。
- 产品、UI、包装、配件和安装关系必须为官方或已验证素材。
- AI 只可用于环境、人物、背景、道具、光线与气氛探索。

### 4.8 Design Spec → QA

- Design Spec 描述结构、内容职责、素材映射、Desktop/Mobile 行为，不实现 Renderer。
- QA 顺序：Fact → Asset → Claim/Promotion → Template → Module → Copy → CTA → Responsive → Rule classification。
- QA 报告必须列出每条 Hard Rule 的 PASS/BLOCKED、Soft deviation reason 与 Experimental advisory。

## 5. Output Contract

Generator 每次必须输出以下 8 个对象，缺一不可：

1. **Campaign Brief**：输入原值、规范化值、来源、缺失项、状态。
2. **Message Hierarchy**：Primary Objective、Primary Message、USP、Proof、Promotion、CTA intent。
3. **Selected Template**：唯一 Variant ID、选择理由、排除候选及边界命中记录。
4. **Module Sequence**：有序 Module ID、required/optional 来源、每段职责与转换理由。
5. **Japanese Copy**：Subject/Preview/H1/Module copy/CTA；每个事实绑定 Claim/Source 状态。
6. **Asset Requirements**：所需素材、已解析素材、source_path、provenance、缺口与 AI 边界。
7. **Design Spec**：Desktop/Mobile 语义结构、布局语法、视觉节奏、内容密度与状态说明。
8. **QA Report**：总体 `PASS/BLOCKED`、failure codes、Hard/Soft/Experimental 结果和未解决项。

每个对象必须包含 `contract_version: 1.0.0`、`design_standard_version: 1.0`、`design_system_version: 1.0.0`、`generated_at` 与 `source_manifest`。

## 6. Failure and Recovery Contract

- `BLOCKED` 不是异常终止；Generator 仍输出已完成的 Brief、缺口、推荐补充材料与可重试入口。
- 不得把 `Unknown` 改写成否定或肯定事实。
- 补充输入后从最早受影响节点重新执行，不复用过期 Price、Promotion、Claim 或 Asset approval。
- 同一输入与同一知识快照应得到同一 Template；任何差异必须记录规则版本或知识版本变化。

## 7. Explicit Exclusions

本 Contract 不包含 HTML/CSS Renderer、ESP integration、图片生成、正式 `SKILL.md`、发送排期、A/B Test 执行或正式 EDM Production。Phase 4 实现必须另行授权。
