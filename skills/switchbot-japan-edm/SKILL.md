---
name: switchbot-japan-edm
description: 统一创建、优化、审查、重排和继续 SwitchBot 日本市场 EDM，覆盖活动策略、产品排序、自然日语文案、历史模板选择、设计 Brief、600px 响应式 HTML、桌面/手机版视觉稿、素材与事实检查、Final Human Review 及 ESP 发送准备。适用于促销、预热、Launch、Reminder、Last Call、品类专题和既有 EDM 修改，也承接原 optimize-japan-edm、EDM Visual Template 及 EDM Generator 相关请求。
---

# 日本 EDM 制作

把策略、文案、历史邮件证据、可执行版式和发布前 QA 合成一个入口。直接交付用户要求的文案、Brief、HTML 或视觉稿；默认用简体中文解释判断和风险，对外 Copy 使用自然日语。用户要求参考过去 EDM 时，先实际读取对应邮件及可用视觉证据，不能仅选择一个模板名后自行套用通用商品卡。

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

读取 [references/edm-production-method.md](references/edm-production-method.md)。执行历史检索、视觉制作或重新设计时，再读 [references/history-evidence-workflow.md](references/history-evidence-workflow.md)。使用：

`实际邮件证据 → 版式 Recipe → Section → Module → 当前 Content/Asset Slot`

- 用户指定 Gmail 或历史邮件时，优先使用已连接 Gmail 工具检索和读取；也可复用本任务已经取得、来源可核对的邮件快照，不需要每次重复搜索。
- 先区分实际推送、测试、重复和非 EDM 邮件，再按活动阶段、任务、产品数量和素材条件选参考。保留简短的选源理由及未选理由。
- 主题、摘要或纯文本只能支持文案与内容顺序；只有实际读到 HTML 或图片仍不足以自动声称整封视觉已验证，需记录完整性、资源加载情况与实际查看范围。没有完整视觉证据时，可以生成清晰标注的新候选，但不得称为“已继承历史视觉”。
- 可移植结构位于 `assets/history-recipes.json`；它保存脱敏 Recipe，不包含原始邮件，也不替代本次真实证据。原邮件、收件信息、个性化链接与证据图外置，不提交 GitHub。

若当前 EDM 属于 `projects/<project-id>/` 的正式项目，先调用共享 `visual-system/`：读取项目 `project-context.yaml`、有效 `visual-freeze.yaml`、Accepted Project Visual Planning Decision 和 `visual-profile.yaml`；需要时运行 Visual Router，并应用 `ADAPTER-EDM-JP`。具体映射读取 [Visual Pattern 接入](references/visual-pattern-integration.md)。有效 Approved Freeze 优先继承；没有 Approved Freeze 时继承适用的 Planning Lock，不重新要求用户选择同一视觉方向。Candidate Freeze、素材不足或未批准内容仍保留各自 Gate。

Visual Router 只负责项目级视觉一致性与 Pattern 排序。EDM Runtime 仍负责 Formula、Section、Module、600px HTML、Desktop/Mobile QA、Final Human 与 ESP Gate；不得用 Visual Profile 绕过这些检查。

- 历史模板决定结构职责，不复制过期文案、价格或产品。
- 优先保留已经验证的 Template、Module 和 Visual Rhythm。
- 在改稿前输出“历史模块 → 新模块”对照，说明继承、调整、新增与省略；改已有稿时再补“旧稿 → 新稿”。对照必须落实到 Hero 构图、商品图文位置、背景节奏和 CTA，不能只替换模板 ID 或背景颜色。
- 历史邮件也需要筛选：占位 Preheader、过长商品表、失效链接、过期 No.1/优惠券和重复内容不能作为继承规则。修正有依据的问题，保留其有效视觉特征。
- 没有合格模板或确有新结构需求时，才建立新模板候选；候选必须人工 Review，不能自动进入正式库。
- 不修改冻结的 Design System、Runtime Manifest 或回归 Fixture 来迁就单次 Campaign。

### 4. 建立移动端阅读路径

没有更适合当前任务的历史版式或已接受视觉决定时，使用以下候选阅读路径：

`Hero → 用户需求/场景 → 主推产品或方案 → 信任/UGC → 统一 CTA → 条款`

- 基线宽度 600px，并检查 320、375、390、414 与 768px。
- Hero 在数秒内说明活动、利益、时间和动作。
- 产品角色决定视觉权重，已选历史 Recipe 决定大卡、横向图文、网格等具体形式；不要把所有邮件强制重排成同一种白底商品卡。每个商品只保留一个主要利益点。
- 模块之间留白、模块内部聚合；不得通过缩小文字解决信息过载。

### 5. 写自然日语

- Subject 短而利益明确；Preheader 补充时间、品类或 Offer，不重复 Subject。
- Subject 负责收件箱打开理由，Preheader 补充信息，Hero 标题负责进入邮件后的活动利益。重新设计时先提出少量不同主题角度，选择一个并说明理由；用户已确认的标题继续使用，不为换视觉而擅自改写。
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

按范围选择内部实现，不新增用户入口：

- 已由 `skills/edm-generator` 覆盖、且依赖与证据可用的冻结单品案例，继续使用原 Ruby Runtime、Truth Gate 和回归流程。
- 多产品促销、真实历史邮件驱动的新设计或原 Runtime 未覆盖的视觉候选，使用本 Skill 的可移植 adapter。它将历史证据、Recipe 和当前内容绑定到 HTML，状态为内部视觉候选，不等于冻结 Runtime 已扩展或生产通过。
- 原 Ruby Runtime、冻结 Design System、Runtime Manifest、已批准视觉和回归 Fixture 保持原有职责；不要修改冻结规则来迁就单次输出。

在本 Skill 目录执行下列命令，输入和输出均指向任务目录；完整证据准备与结果检查见 [历史证据工作流](references/history-evidence-workflow.md)：

```bash
python scripts/edm_history.py plan --brief <brief.json> --evidence <evidence.json> --out <plan-directory>
python scripts/render_edm.py --input <render-input.json> --plan <plan.json> --out <output-directory>
```

命令存在、计划生成和 HTML 导出分别记录实际结果；上述接口不代表当前环境已经执行成功。引用实际生成的计划路径，不伪造运行结果。

- 先验证 Runtime 实际存在、依赖可用、路径不是失效的本机绝对路径、当前产品/活动类型受支持。
- 当前促销、折扣或新产品若不在旧 Runtime 已验证范围内，记录 `BLOCKED_RUNTIME_SCOPE`；可继续使用 adapter 制作内部候选，但不得用 adapter 完成状态覆盖原 Runtime 的限制。
- 日期、现价、优惠或 URL 未确认不必停止整封视觉制作：使用明确的内部草稿状态，省略未确认价格/折扣，保留可编辑配置；缺少当前官方产品图时使用标明缺图的版位。完整排版不等于事实或素材已确认。
- 长图应从实际生成的 HTML 导出，并记录 HTML、素材、渲染方式和实际宽度；AI 只生成获准场景层，不能绘制整封邮件冒充 HTML 渲染。
- 浏览器 QA 没有实际运行时，不得写“移动端已验证”或“HTML 已通过”。
- 离线静态排版图只标记为排版参考，不等于浏览器截图、响应式验证或邮件客户端验证。
- 所选 Runtime 不存在时继续完成安全的文案/Brief，并标记 `BLOCKED_RUNTIME_MISSING`；不要用通用占位 HTML 冒充稳定 Runtime 输出。

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
- **HTML/视觉稿**：可编辑 HTML、实际 HTML 导出的桌面/手机长图或真实渲染阻塞说明、历史选源与模块对照、主题/Subject/Preheader/Hero 方案、Manifest、QA、状态和 Blocker。避免只交付文件链接而不说明继承了哪些可见特征。
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
- 历史引用有真实读取证据；实际继承的构图、图文关系和 CTA 与模块对照一致，没有靠模板标签自证继承。
- 正式产品层没有 AI 重绘。
- 桌面/移动端和浏览器 QA 状态真实可追溯。
- Final Human、ESP 和发送门禁没有被视觉完成状态绕过。
