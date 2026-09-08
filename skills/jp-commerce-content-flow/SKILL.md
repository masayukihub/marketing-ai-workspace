---
name: jp-commerce-content-flow
description: 将产品营销资料、Product Knowledge、飞书来源、Commerce Insight Pack与官方素材转化为日本Amazon/日本电商的商品图组、Gallery、A+/EBC、Listing文案、视觉方向、单张深化、完整Content Review HTML、移动端预览与交付QA。Use when the user asks for Amazon Japan PDP Generator, Amazon Listing Creative, JP Commerce Creative Flow, 日本Amazon页面, 日亚商品图, A+, Gallery, Listing文案, 电商视觉稿, Content Review HTML, “继续下一步”, low-cost MVP, or local revision of an approved asset. 这是用户唯一的内容生成入口；默认用中文解释进度，内部路由研究、规划、创意、生产、验证和交付，不要求用户手动选择旧 Skill。
---

# 日本电商内容生成

把原先分散的 `Amazon Japan PDP Generator`、`Amazon Listing Creative` 与 `JP Commerce Creative Flow` 合并为一个用户入口。旧能力保留为内部模块，不再让用户判断调用顺序。

## 首先读取

任务指向现有仓库项目时，先运行 `project-context-resolver`。只消费 Amazon/Design/Visual Context Package 返回的 Product Truth、Decision、Approved Claim、Visual Context/Profile/Freeze 与 Asset 指针；`project.yaml` 是导航和 Gate，`project-context.yaml` 仅是 Visual Router 输入，两者都不替代 Product Truth。

每次执行先读取 [capability-map.md](references/capability-map.md)、[internal-components.md](references/internal-components.md) 与 [runtime-contract.md](references/runtime-contract.md)。需要定义交付物或完成条件时再读取 [output-contract.md](references/output-contract.md)。进入 Planning、Visual Production 或继续老项目时，还必须读取 [visual-router-integration.md](references/visual-router-integration.md)。

## 直接这样用

```text
使用 $jp-commerce-content-flow，读取【产品/项目】的Product Truth、已批准Claim、
正式项目状态和视觉锁。目标渠道为【Amazon.co.jp】，本次范围为【Gallery/A+/Listing】。
自动继承已批准决定，只执行到下一个人工审核Gate；未确认内容保持“未确认”。
```

继续老项目时不需要再写内部 Skill 名称：

```text
使用 $jp-commerce-content-flow，继续【项目名】的【资产ID/阶段】。
只修改【明确范围】，其他已批准内容保持锁定，完成后给我审核HTML。
```

用户无需分别调用 `JP Commerce Creative Flow`、`Japan Listing Demo`、`Amazon Japan PDP Generator`、`Amazon Listing Creative` 或各个 Listing Stage；主入口按正式状态自动选择内部模块。

## 选择执行模式

- `FULL_FLOW`：从来源到完整Gallery、A+、HTML和QA。
- `MVP`：按用户指定的市场、渠道、Offer和少量资产跑通正式流程，不擅自扩展范围。
- `PLAN_ONLY`：只完成产品理解、消费者策略、故事顺序和Production Handoff。
- `CREATIVE_EXPLORE`：针对一个信息点探索不同视觉方向，不生产完整页面。
- `PRODUCE`：从已批准Handoff逐张制作正式候选。
- `LOCAL_REVISION`：只修改指定资产和元素，锁定其他内容。
- `RESUME`：从当前正式状态继续，不从头重做。
- `HARDEN`：验证最终文件、组装单文件HTML并完成PC/移动端QA。

用户说“继续”“下一步”“go”时，读取当前项目状态并进入下一必要阶段；不要重复上一轮理论、重新发散或重做已批准资产。

## 固定流程

```text
Source Intake
→ Product Truth
→ Commerce Insight Handoff
→ Project Visual Resolution
→ Planning
→ Human Review
→ Visual Production
→ Whole-set Review
→ Hardening / Evidence Audit
→ Standalone HTML / Delivery QA
```

### 1. Source Intake

读取用户指定的飞书、工作区、Product Knowledge、官方资料与产品素材。真实工具未返回内容时不得声称已读取。记录来源、更新时间、产品/变体/套装和适用范围。

产品事实优先级：

```text
用户本次明确确认
→ 当前官方Source / Product Knowledge
→ 已批准项目记录
→ 其他参考资料
```

聊天记忆、竞品页面、评论、旧生成物和AI推断都不能覆盖产品事实。

### 2. Product Truth

生成并锁定 Product Truth Packet，至少区分：

- Product / Variant / Bundle / Offer；
- Confirmed Specs；
- Approved / Unapproved Claims；
- Compatibility / Installation；
- Target User / Scenario；
- Price / Promotion；
- Available Assets / Asset Rights；
- Forbidden Claims；
- Unknown / Conflict / Need Confirmation；
- Sources。

缺少关键事实时返回 `BLOCKED` 或 `PARTIAL_BUT_ACTIONABLE`，不要用更好看的文案补齐。

### 3. Commerce Insight Handoff

已有 `$jp-commerce-insights` 输出时只读取其 Creative Handoff，不重复抓取全部市场资料。没有洞察且用户要求完整策略时，调用 `$jp-commerce-insights` 补齐最小必要研究。

研究结论和Claim Candidate不能自动升级为Approved Claim。

### 4. Project Visual Resolution

Visual Router 是共享内部能力，不是新的用户入口。进入 Planning / Visual Production 前按以下顺序执行：

```text
resolve_project
→ load_visual_freeze
→ load_accepted_project_visual_planning_decision_if_no_approved_freeze
→ load_visual_profile
→ visual_router_if_needed
→ apply_channel_adapter
→ continue_existing_flow
```

- `project-context.yaml` 只保存产品、市场、渠道、目标用户、定位、信息复杂度、素材状态与视觉原则，不写死具体 Pattern。
- 存在有效人工批准 `visual-freeze.yaml` 时默认继承，不重新问用户视觉方向。
- 没有有效 Approved Freeze 时，读取 Project Manifest 指向的 Accepted Project Visual Planning Decision。其 `reask_visual_direction=false` 只锁定项目 Visual DNA、渠道 Intent、Recipe Core 与条件模块政策；不得锁定最终 Layout、Template、文案、素材或 Claim。
- Freeze 不可用或不存在时，运行 `visual-system/routing/visual_router.py` 生成 `visual-profile.yaml`，默认采用最高匹配 Pattern。
- 只有 Top 1 / Top 2 过近、Brand Fit 不达标、必需素材不满足、Pattern 未验证、Freeze 冲突或用户明确探索时进入 Human Review。
- Channel Adapter 只把共享 Pattern 映射到 Amazon Gallery/A+ 与已注册模板原语，不能修改 Product Truth、Claim、正式产品层或已批准资产。
- 任何路由结果都不得绕过 Product Truth、Human Review、Claim Gate、Product Layer、Hardening 或 Mobile QA。

### 5. Planning

完成目标用户、JTBD、购买障碍、核心承诺、Reasons to Believe、信息层级、Gallery/A+分工、完整资产集合、Page Visual System和Evidence Mode。

坚持：

- 一张图只回答一个主要购买问题；
- Gallery负责快速判断，A+负责解释、证明、适配和异议消除；
- 同一艺术方向不等于重复构图；
- 不按Feature数量机械加图；
- 不复制竞品文案、图片、Trade Dress或完整Layout。

输出可审核的Story/Content Review并暂停。用户批准后锁定资产ID、顺序、主信息和日文文案。

### 6. Visual Production

一次只生产一个Asset ID。输入只使用已批准Handoff、当前Asset Packet、官方产品素材与批准参考，不把长篇研究、Gate术语或项目状态塞进生成提示词。

三层素材规则：

```text
Official Product Asset = Product Layer
AI / Stock / Lifestyle = Scene Layer
HTML / CSS / SVG = Graphic Layer
```

禁止AI生成、重画或改变正式SwitchBot产品本体、Logo、精确UI、日文文字、参数表和技术标注。AI只可生成不含产品、Logo、文字和UI的场景层；最终文字使用程序化排版或真实素材。

用户选择某一候选后，锁定精确候选和文件。除非用户明确说“重做”“修改这张”或“换版本”，不得静默替换。

### 7. Whole-set Review

完成当前范围后生成Contact Sheet或整页Review，检查：

- 故事和购买决策顺序；
- 场景/构图/明暗/产品比例节奏；
- 产品外观一致性；
- 日文自然度与手机端可读性；
- Claim与证据；
- Gallery/A+重复；
- 当前资产集合是否完整。

局部问题只重开最小必要资产，不默认整套重做。

### 8. Hardening 与交付

对精确最终文件重新计算物理信息和SHA-256，核对来源、批准对象、Asset-to-Slot、尺寸、格式、嵌图、移动端、交互和页面完整性。文件名或旧状态不能替代真实验证。

默认Demo交付为一个可独立打开的单文件HTML：图片内嵌、CSS/JS内联、PC和390px移动端可阅读。未实际完成浏览器验证时，不得声称Carousel、移动端或交互QA已通过。

## 用户沟通方式

默认用中文，避免把用户淹没在技术状态中。普通阶段只显示：

```text
已完成：
待确认：
下一步：
```

只有 `BLOCKED`、`PARTIAL` 或用户要求审计时，才展开Gate、Hash、Provenance和详细状态。

面向日本市场的消费者文案使用自然、简洁的日语；关键文案同时给中文含义。公司名统一写 `SWITCHBOT株式会社`，产品名采用 `SwitchBot + 产品名`，日语中的hub写「ハブ」。

## 运行时与GitHub边界

优先使用当前工作区已验证的 `masayukihub/jp-commerce-creative-flow` 运行时及其SwitchBot JP Overlay。`amazon-japan-pdp-generator` 可作为旧模板/渲染兼容层，`amazon-listing-creative` 可作为单张创意探索方法，但两者不得绕过主Flow的Product Truth、人工Review、Evidence和Hardening边界。

如果运行时、模板或验证脚本不在当前工作区：

1. 仍可完成来源整理、Product Truth、策略和可审核Brief；
2. 明确标记实际渲染或自动QA为 `BLOCKED_RUNTIME_MISSING`；
3. 不用通用HTML或AI图片假装正式Flow已经跑完。

公开GitHub只保存通用规则、Schema、脚本、空模板和合成Fixture。未发布产品事实、价格、审批、飞书快照和正式产品素材不得提交到公开仓库。

## 完成条件

按 [output-contract.md](references/output-contract.md) 验收。Creative Approval不等于Publish Ready；只有事实、Claim、素材授权、日文、文件、页面和移动端验证均满足当前交付范围时，才可标记完成。
