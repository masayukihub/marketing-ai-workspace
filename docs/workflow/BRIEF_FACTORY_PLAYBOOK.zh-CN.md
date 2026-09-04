# SwitchBot Japan Marketing Brief 工厂

这份手册把你常用的 Amazon、EDM、KOL、PR、视频、SNS、设计和 Landing Page Brief 统一成一个方法。目标不是让 AI 生成一份漂亮但空泛的文档，而是把已经确认的策略、事实、素材和交付要求转成可执行任务。

## 1. Brief 在工作流中的位置

```text
Product Truth / Campaign Context / Insight
→ Message 与目标确认
→ Brief
→ 制作
→ QA
→ Human Review
```

Brief 不能代替 Product Truth，也不能自动批准 Claim。缺失事实应显示 `NEED_CONFIRMATION`，不能用文案补齐。

## 2. 统一输入

任何 Brief 先收集以下最小字段：

```text
project_id
brief_id
brief_type
market / locale
channel
objective
campaign_stage
target_audience
product / variant / bundle / offer
single_core_message
supporting_messages
approved_claims
forbidden_or_pending_claims
cta / destination
promotion / period / conditions
available_assets
required_deliverables
dimensions_or_format
deadline
owner
references
review_and_approval_boundary
```

### 来源优先级

```text
当前官方来源 / Product Knowledge
→ Accepted Project Decision / Campaign Context
→ 本轮用户明确确认
→ 已审核历史模板
→ 外部参考
→ 推测
```

外部参考只能贡献结构和灵感，不能贡献 SwitchBot 产品事实。

## 3. 统一 Brief 骨架

所有类型的 Brief 共享以下部分：

1. **Background**：为什么现在要做；
2. **Objective**：希望用户或受众完成什么；
3. **Target Audience**：谁、什么场景、当前障碍；
4. **Product / Offer Scope**：准确的产品、Variant、Bundle、渠道与地区；
5. **Single Core Message**：唯一主信息；
6. **Supporting Proof**：2–3 个支撑点及来源；
7. **Content / Visual Direction**：表达结构和视觉方向；
8. **Mandatory**：必须出现的内容；
9. **Do Not**：禁止使用的 Claim、素材和表达；
10. **CTA / Destination**：真实下一步；
11. **Deliverables**：数量、尺寸、格式和命名；
12. **Review / Approval**：谁审什么、允许几轮修改；
13. **Success Criteria**：什么算完成；
14. **Open Questions / Blockers**：仍缺什么。

## 4. Brief 质量 Gate

Brief 进入制作前必须回答：

- 这是哪个准确产品和 Offer；
- 这份内容只解决什么主要问题；
- 核心 Message 是否有事实或洞察支持；
- 哪些 Claim 已批准、哪些不能说；
- 需要哪些官方素材；
- CTA 是否真实存在；
- 制作者能否只看 Brief 就理解要交付什么；
- 验收者能否明确判断 PASS / REVISION / BLOCKED。

缺少 Product / Offer、核心 Message、关键素材或真实 CTA 时，Brief 可以成为内部草稿，但不得标记 `PRODUCTION_READY`。

## 5. Amazon Gallery / A+ Brief

统一入口：`$jp-commerce-content-flow`

每张图必须单独包含：

```text
Asset ID
Page Role
Consumer Question
Primary Message
Supporting Message
Reason to Believe
Evidence Object
Source IDs
Evidence Mode
Official Product Assets
Scene Layer
Graphic / Copy Layer
Japanese Headline Direction
Copy Length Limit
Composition Direction
Mobile Priority
Forbidden Claims
Open Issues
```

### Evidence Mode

- `SOURCE_FAITHFUL`：产品、包装、套装或 Offer 身份必须完全忠于官方素材；
- `CREATIVE_MOCK`：可生成生活场景，但产品身份不能被重画；
- `PROOF_VISUAL`：尺寸、安装、机制、UI、兼容性等事实证明，必须绑定权威来源。

### 验收重点

- 一张图只有一个 Primary Message；
- Gallery 和 A+ 不重复承担同一职责；
- 日本消费者能快速理解“是什么、为什么需要、为什么可信、是否适合我”；
- 正式产品层没有 AI 重构；
- Mobile 端标题和信息密度可读。

## 6. EDM Brief

统一入口：`$switchbot-japan-edm`

除统一骨架外，增加：

```text
Audience Segment
Campaign Stage
Desired Action
Reason to Click Now
Subject Direction
Preheader Direction
Formula / Template Request
Product Priority
Module Order
Primary / Secondary CTA
600px Mobile Path
Footer / Legal
ESP Variables
Send Readiness Boundary
```

### 常用 Campaign Stage

```text
NEW_PRODUCT_LAUNCH
SALE_LAUNCH
MID_CAMPAIGN
FINAL_DAY
PRODUCT_EDUCATION
CATEGORY_GUIDE
CRM_UPGRADE
```

### 验收重点

- 一封邮件只有一个主要任务；
- Subject 与 Preheader 不重复；
- 产品顺序有商业理由；
- 历史模板只贡献结构，不带入旧价格和旧产品；
- 320–414px 手机端可读；
- `VISUAL_DELIVERABLE_CANDIDATE` 不等于 `ESP_READY`。

## 7. KOL / Creator Brief

统一入口：`$switchbot-japan-campaign`，内部调用 `influencer-marketing`。

增加：

```text
Creator Segment
Why This Creator
Audience Fit
Recommended Format
Recommended Story Flow
2–3 Talking Points
Required Demo / Proof
Must Show
Must Mention
Must Not Say
Creative Freedom
Disclosure
Usage Rights
Whitelisting / Paid Media Rights
Exclusivity
Deliverables
Posting Window
Draft Review Boundary
Tracking / Coupon / Attribution
Expected KPI
Sample Logistics
```

### 原则

- 不逐字脚本化创作者；
- 锁定真实卖点、必须演示、禁区、CTA 和披露；
- 给创作者保留符合其频道风格的表达空间；
- 未批准性能、价格、No.1、认证和兼容性不得进入 Brief；
- 合作前确认 Usage Rights 和二次投放权限。

## 8. PR / Media Brief

统一入口：`$switchbot-japan-campaign`。

增加：

```text
News Angle
Why Now
Target Media Segment
Headline Direction
3 Key Messages
Evidence / Data / Demo
Spokesperson / Interview Topic
Embargo / Launch Timing
Media Assets
Hands-on / Loan Unit Plan
Approved Claims
Media FAQ
Prohibited Claims
Follow-up Plan
Measurement
```

### 原则

- 新闻角度不能只是“发布新品”；
- 需要说明对日本消费者、品类或生活方式的意义；
- KOL 播放量逻辑不能直接套到 PR；
- 媒体报道质量、核心 Message 命中、Hands-on 和长期搜索价值优先于纯曝光。

## 9. 视频制作 Brief

统一入口按用途路由：Amazon 视频进入 `$jp-commerce-content-flow`，Campaign/SNS 视频进入 `$switchbot-japan-campaign`。

增加：

```text
Video Objective
Duration / Aspect Ratio / Platform
Hook in First 3 Seconds
Scene List
Shot List
Product Interaction
Must-use Official Product References
AI / Live-action Boundary
Narration / On-screen Copy
Sound / Music Direction
Transition
End Card / CTA
Continuity Risks
Product Fidelity Risks
```

### AI 视频边界

- 产品外观、按钮、接口、安装关系、Logo 和 UI 必须依赖官方素材或实拍；
- AI 可以做环境、镜头气氛、人物和辅助场景；
- 门锁、ハブ等结构精确产品不应由模型自由重建；
- 先做 5–10 秒产品 Fidelity Demo，再决定是否扩展完整视频。

## 10. SNS / Banner / Campaign Visual Brief

统一入口：Campaign 视觉用 `$switchbot-japan-campaign`，Amazon 用 `$jp-commerce-content-flow`，EDM 用 `$switchbot-japan-edm`。

增加：

```text
Platform / Placement
Dimensions
Audience State
Scroll-stop Hook
Single Message
Product Hierarchy
Scene / Background
Copy-free or Copy-on-visual
Safe Area
CTA
Asset Reuse Family
Master / Adaptation Relationship
```

### 原则

- 先决定母版，再规划 X、Instagram、LINE、PR TIMES 等尺寸改版；
- 同一 Campaign 保持品牌 DNA，但不同版位不能机械裁切；
- 没有正式产品素材时只交付 Scene Layer 或 Wireframe，不用 AI 近似产品冒充成品。

## 11. Landing Page / Website Brief

增加：

```text
Page Objective
Traffic Source
Primary Audience
Primary Conversion
Information Architecture
Hero Message
Proof / Trust Modules
Product / Category Modules
FAQ / Objections
SEO Intent
CTA Hierarchy
Mobile Behavior
Analytics Events
Legal / Policy Dependencies
```

不得从竞品网站复制承诺、UGC、认证、Trade Dress 或完整布局。

## 12. Brief 自动化边界

### 可自动完成

- 从已确认 Product Truth、Campaign Context 和 Insight Pack 提取字段；
- 选择相应 Brief 类型；
- 生成结构、信息层级、素材表和验收标准；
- 对缺口按 Owner 分类；
- 自动检查重复、遗漏、跨 Offer 和未批准 Claim；
- 输出 Markdown、JSON 和 Review HTML。

### 必须人审

- Product / Variant / Bundle / Offer；
- 新 Claim、价格、折扣、日期、认证、法律文案；
- 核心 Target、Positioning 和 Primary Message；
- 正式 Usage Rights、合同、预算和外部承诺；
- 精确最终素材和发布。

## 13. 直接复制的通用指令

```text
读取最新 GitHub main，解析【项目名】及当前正式状态。
根据已确认的 Product Truth、Project Memory、Campaign Context 和可用素材，
为【渠道/交付物】生成一份可执行 Brief。

要求：
1. 自动选择正确的四个中文入口和内部模块；
2. 一份 Brief 只保留一个核心任务和一个 Primary Message；
3. 所有事实、Claim、价格、日期和素材标明来源或 NEED_CONFIRMATION；
4. 输出 Mandatory、Do Not、Deliverables、Owner、Deadline、Acceptance Criteria；
5. 缺口一次性按 Owner 汇总，不逐项询问；
6. 自动检查跨产品、跨 Offer、未批准 Claim 和素材权利；
7. 停在 Brief Human Review Gate，不自动发送、发布或写回正式系统。
```

## 14. Brief 版本与复用

每份正式 Brief 建议记录：

```text
brief_id
project_id
brief_type
version
source_snapshot_ids
product_truth_version
campaign_context_version
created_at
review_status
approved_by
approved_at
supersedes
output_refs
```

跨项目可复用的是 Brief 结构和 QA 规则，不是单次产品事实、价格、日期或文案。
