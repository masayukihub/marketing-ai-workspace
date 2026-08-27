---
name: switchbot-japan-edm
description: 统一创建、优化、审查、重排和继续 SwitchBot 日本市场 EDM，覆盖活动策略、产品排序、自然日语文案、历史模板选择、设计 Brief、600px 响应式 HTML、桌面/手机版视觉稿、素材与事实检查、Final Human Review 及 ESP 发送准备。适用于促销、预热、Launch、Reminder、Last Call、品类专题和既有 EDM 修改，也承接原 optimize-japan-edm、EDM Visual Template 及 EDM Generator 相关请求。
---

# 日本 EDM 制作

把策略、文案、历史模板、视觉生成和发布前 QA 合成一个入口。直接交付用户要求的文案、Brief、HTML 或视觉稿；默认用简体中文解释判断和风险，对外 Copy 使用自然日语。

## 选择最小工作模式

- `CRITIQUE`：检查已有截图、文案或 HTML，给出精确修改清单。
- `COPY`：完成主题、Preheader、模块文案、产品排序和 CTA。
- `DESIGN_BRIEF`：输出可交给设计或制作的模块化 Brief。
- `HTML_VISUAL`：匹配历史模板，生成 HTML 和桌面/手机版视觉稿并 QA。
- `LOCAL_REVISION`：只修改指定模块、句子、产品顺序或样式，不重做整封。
- `RESUME`：读取上次 Manifest、Readiness、Review 和批准状态，只执行下一项允许动作。
- `SEND_READINESS`：检查 Final Human 与 ESP 条件；不自动发送。

用户只要求文案或小改时，不启动完整视觉 Runtime。用户说“继续”时，不重新选择已冻结模板或推翻已经批准的事实。

## 事实与上下文

优先复用 `$switchbot-japan-campaign` 输出的 Campaign Context；没有时只补齐当前 EDM 的最小信息，不重做完整 GTM。

至少盘点：

`目标/活动阶段 | 受众 | 产品/SKU | 产品角色 | MSRP/活动价/折扣/券/赠品 | 日期 | Claim/证据 | CTA/落地页/Tracking | 素材/授权 | Footer/Legal | 输出格式`

来源优先级：当前官方或正式项目资料 > Approved Product/Campaign/Pricing/Link/Asset 记录 > 已审核历史模板 > 用户本轮明确输入 > 外部参考 > 推测。

- 不得编造产品名、功能、价格、折扣、库存、日期、奖项、评论、稀缺性或链接。
- 缺失、冲突或不稳定信息在工作稿中标记 `要確認`；不能写成 0 或自动选一个版本。
- 评论、VOC、竞品信息和营销洞察不能自动升级为 Approved Claim。

## 核心流程

### 1. 明确一封邮件的唯一任务

分类为预热、促销上线、品类/场景专题、新品教育、Reminder 或 Last Call，并写清：

`Audience → Campaign Stage → Desired Action → Landing Destination → Reason to Click Now`

优先一个主 CTA。Amazon 引流、官网教育、Wishlist 和品牌故事并存时，必须建立明确层级。

### 2. 按商业角色排序产品

默认权重：

`主题匹配 > 活动阶段任务 > 战略优先级 > 销量/销售额表现 > Offer 强度 > 库存与事实确定性`

把产品标为流量主力、营收主力、战略新品、场景搭档、次级补充或移除。不要仅按一个排名字段机械排序。

### 3. 先匹配历史模板，再做受控调整

读取 [references/edm-production-method.md](references/edm-production-method.md)。使用：

`Formula → Section → Module → Content Slot`

若当前 EDM 属于 `projects/<project-id>/` 的正式项目，先调用共享 `visual-system/`：读取项目 `project-context.yaml`、有效 `visual-freeze.yaml` 和 `visual-profile.yaml`；需要时运行 Visual Router，并应用 `ADAPTER-EDM-JP`。具体映射读取 [Visual Pattern 接入](references/visual-pattern-integration.md)。有效 Freeze 默认继承，不重新要求用户选择视觉方向；Candidate、渠道冲突、素材不足或未验证 Pattern 必须保留 Human Review。

Visual Router 只负责项目级视觉一致性与 Pattern 排序。EDM Runtime 仍负责 Formula、Section、Module、600px HTML、Desktop/Mobile QA、Final Human 与 ESP Gate；不得用 Visual Profile 绕过这些检查。

- 历史模板决定结构职责，不复制过期文案、价格或产品。
- 优先保留已经验证的 Template、Module 和 Visual Rhythm。
- 没有合格模板或确有新结构需求时，才建立新模板候选；候选必须人工 Review，不能自动进入正式库。
- 不修改冻结的 Design System、Runtime Manifest 或回归 Fixture 来迁就单次 Campaign。

### 4. 建立移动端阅读路径

默认：

`Hero → 用户需求/场景 → 主推产品或方案 → 信任/UGC → 统一 CTA → 条款`

- 基线宽度 600px，并检查 320、375、390、414 与 768px。
- Hero 在数秒内说明活动、利益、时间和动作。
- 主推产品使用大卡，次级产品使用规律网格；卡片只保留一个主要利益点。
- 模块之间留白、模块内部聚合；不得通过缩小文字解决信息过载。

### 5. 写自然日语

- Subject 短而利益明确；Preheader 补充时间、品类或 Offer，不重复 Subject。
- 先写生活结果，再用功能证明；避免中文直译、参数堆砌和泛化 CRM 套话。
- 产品卡保留正式产品名、一个利益句、已确认价格/Offer 和具体 CTA。
- CTA 写真实下一步，例如 `Amazonでセール価格を見る`，避免无信息的 `詳しくはこちら`。
- 使用 `SWITCHBOT株式会社`、`SwitchBot + 製品名` 及已确认的日本正式术语。

### 6. 使用可信素材

- 产品本体、App UI、包装、配件和安装关系只能使用官方或已批准素材。
- 不用 AI 重绘、补画或近似生成正式产品层。
- AI 仅可用于获准的背景、人物、环境、道具、光线和氛围；生成层与官方产品层必须分开。
- 缺少正式产品素材时，交付素材缺口或内部线框稿，不把占位图冒充正式视觉。
- UGC 必须有原始来源、产品映射、授权和正确归属；缺失时列需求，不编造日本用户或评价。

### 7. 运行稳定 Runtime

只有 `HTML_VISUAL` 或 `RESUME` 需要运行视觉管线。

当工作区存在 `skills/edm-generator` 时，把它作为内部 Runtime，优先复用其冻结的历史模板、Design System、Generator、Renderer、Truth Gate 和 QA；不得把它重新注册为日常用户入口。

- 先验证 Runtime 实际存在、依赖可用、路径不是失效的本机绝对路径、当前产品/活动类型受支持。
- 当前促销、折扣或新产品若不在已验证范围内，仍可交付内部文案、Brief 或视觉草稿，但标记 `BLOCKED_RUNTIME_SCOPE`，不得声称已达到正式生产状态。
- 浏览器 QA 没有实际运行时，不得写“移动端已验证”或“HTML 已通过”。
- Runtime 不存在时继续完成安全的文案/Brief，并标记 `BLOCKED_RUNTIME_MISSING`；不要用通用占位 HTML 冒充稳定 Runtime 输出。

### 8. QA 与发布门禁

检查：

- 日本语自然度、产品名、价格/税込、折扣计算、日期/星期、Claim、免责声明；
- 图片授权、产品层真实性、Alt Text、CTA、目标 URL 和 Tracking；
- 600px 结构、移动端字号、按钮、换行、溢出、图例/标签与邮件客户端限制；
- 退订、偏好设置、年份 Token、Footer、Legal、ESP 变量和发送环境。

发布状态严格按：

`INTERNAL_DRAFT → DESIGN_READY → VISUAL_DELIVERABLE_CANDIDATE → CONTENT_APPROVED → ESP_READY → PRODUCTION_READY`

- `VISUAL_DELIVERABLE_CANDIDATE` 不等于可正式发送。
- `CONTENT_APPROVED` 必须来自具名人工 Review；Codex 不能代签。
- `ESP_READY` 必须验证正式 URL、Token、邮件客户端和发送平台。
- 不自动发送 EDM、不自动创建短链、不自动写正式飞书，也不扩大文件权限。

## 输出方式

按请求交付：

- **快速诊断**：问题位置、精确修改、原因、影响、优先级。
- **文案稿**：最终日语 Copy 在前，只附必要的中文说明和 `要確認`。
- **设计 Brief**：`模块 | 元素 | 最终文案 | 设计要求 | 素材/来源 | 事实状态 | 优先级`。
- **完整 EDM**：策略、Subject/Preheader、结构、日语文案、CTA、素材计划和 QA。
- **HTML/视觉稿**：可编辑 HTML、桌面/手机版预览、Manifest、QA、状态和 Blocker。
- **小改模式**：按 `必须 / 建议 / 有余力` 排序，只改用户指定范围。

不要用“更高级”“更简洁”作为最终建议；明确指出哪一屏、哪句话、哪个模块、顺序、间距、素材或 CTA 如何改。

## 上下游衔接

- 活动目标、产品/Offer、阶段、CTA、落地页或 Tracking 冲突时，回到 `$switchbot-japan-campaign` 修正 Campaign Context。
- 需要 Amazon 关键词、竞品或 VOC 时使用 `$jp-commerce-insights`。
- 需要 Amazon Gallery、A+ 或 Listing 时使用 `$jp-commerce-content-flow`。

## 完成检查

- 交付物与用户请求模式一致，没有不必要地重跑完整流程。
- 每个事实、价格、Claim、链接和素材都有来源或明确 `要確認`。
- 历史模板只贡献结构，不携带旧活动事实。
- 正式产品层没有 AI 重绘。
- 桌面/移动端和浏览器 QA 状态真实可追溯。
- Final Human、ESP 和发送门禁没有被视觉完成状态绕过。
