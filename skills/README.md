# Skills

本工作区的日本营销主流程只保留四个中文业务入口。旧 Skill 不删除成熟代码，以内部模块、兼容入口或 Runtime 形式保留脚本、测试和回退能力。Lark、插件及其他独立方法 Skill 不在本次精简范围内，仍可正常显示和使用。

先从仓库根目录 [`START_HERE.md`](../START_HERE.md) 开始。用户只需要描述业务目标；`operator/task-routing.yaml` 负责选择入口和内部模块，`operator/review-policy.yaml` 决定自动执行到哪里、什么时候需要人工审核。

## 四个主流程入口

| 用户入口 | 什么时候用 | 内部整合能力 |
|---|---|---|
| `$jp-commerce-insights`（日本电商洞察） | 选品、关键词、竞品、评论、VOC、Listing素材和 KOL/媒体前置证据 | 电商选品情报、Amazon Keyword Miner、Amazon Competitor Reviews、Amazon VOC Browser Scraper、Amazon Listing Asset Capture |
| `$jp-commerce-content-flow`（日本电商内容生成） | 日亚 Gallery、A+、Listing 文案、产品卖点图、Content Review HTML、继续现有项目 | JP Commerce Creative Flow、Japan Listing Demo、Amazon Japan PDP Generator、Amazon Listing Creative、Visual System |
| `$switchbot-japan-campaign`（日本营销活动策划与复盘） | GTM、项目管理、Launch Readiness、KOL/PR、渠道素材、Tracking/UTM、执行和复盘 | Project Context、Project Memory、Influencer Marketing、Campaign Review、Traffic Link Governance |
| `$switchbot-japan-edm`（日本EDM制作） | 日本 EDM 策略、产品排序、日语文案、Brief、历史模板、HTML/视觉和发送前 QA | Optimize Japan EDM、EDM Generator、Visual System、EDM Stable Runtime |

## 截图中的旧名称如何归并

| 你以前看到的 Skill | 现在从哪里进入 | 当前角色 |
|---|---|---|
| 电商选品情报、Amazon Keyword Miner、Amazon Competitor Reviews、Amazon VOC Browser Scraper、Amazon Listing Asset Capture、Customer Review Intelligence | `$jp-commerce-insights` | 选品、关键词、评论、VOC分析与页面证据的内部模块 |
| Amazon Japan PDP Generator、Amazon Listing Creative、Japan Listing Demo、JP Commerce Creative Flow | `$jp-commerce-content-flow` | Spec/模板、创意探索、主路由与来源治理的内部模块 |

这里的“合并”是统一用户入口、自动路由和输出合同。成熟采集器、Renderer、上游Flow、Gate与测试仍各自保留，因此升级和回退不会互相破坏。内部旧目录会从Codex日常发现目录移动到 `internal-skills/`，只是不再显示为独立卡片，不会删除源码；迁移支持恢复。

## 最简单的用法

```text
使用 $jp-commerce-insights，调研 S30 mini 在日本小户型市场的机会，
输出关键词、竞品、VOC、用户障碍和 Creative Handoff。
```

```text
使用 $jp-commerce-content-flow，读取 S30 mini 的 Product Truth 和 Insight Pack，
继续 Amazon Gallery G01-WT、G02、G03；继承已接受的视觉规划，停在下一次内容或视觉审核 Gate。
```

```text
使用 $switchbot-japan-campaign，解析 Lock Ultra Max 项目，
审计过往 Lock 系列和竞品的 KOL/PR，输出合作方向、名单标准、Brief、KPI 和 Launch 节奏。
```

```text
使用 $switchbot-japan-edm，读取已确认的 Campaign Context 和产品资料，
制作一封日本新品 EDM；自动选择可继承模板，完成 HTML、手机预览和发送前 QA。
```

## 常见需求如何路由

| 用户说法 | 路由 |
|---|---|
| “市场怎么样、竞品、关键词、评论、VOC” | `$jp-commerce-insights` |
| “Amazon页面、A+、卖点图、Brief、Review HTML” | `$jp-commerce-content-flow` |
| “GTM、项目管理、KOL、PR、活动策划、复盘、Tracking” | `$switchbot-japan-campaign` |
| “EDM、邮件文案、HTML、手机预览、发送前检查” | `$switchbot-japan-edm` |
| “生成视觉图/Banner/KV” | 按最终渠道进入 Content / Campaign / EDM，再调用内部 Visual System |
| “继续/下一步” | 解析正式项目 Next Action，自动选择对应入口 |
| “建立新品项目” | 先走 Project Bootstrap，不自动创建 Formal Project |

完整路由规则：[`../operator/task-routing.yaml`](../operator/task-routing.yaml)。

## KOL、PR、Brief、视觉和项目管理为什么不再新增入口

这些能力已经可以挂在四个入口下：

- KOL / PR 属于 Campaign 与 GTM 的一部分，由 `$switchbot-japan-campaign` 控制，`$jp-commerce-insights` 提供证据，`influencer-marketing` 负责内部评估方法；
- Amazon / EDM / KOL / PR / 视频 / SNS Brief 由目标渠道入口生成，统一方法见 [`BRIEF_FACTORY_PLAYBOOK.zh-CN.md`](../docs/workflow/BRIEF_FACTORY_PLAYBOOK.zh-CN.md)；
- 视觉生产通过目标渠道入口调用 `visual-system/`，统一规则见 [`VISUAL_AI_PLAYBOOK.zh-CN.md`](../docs/workflow/VISUAL_AI_PLAYBOOK.zh-CN.md)；
- GTM 周报、Owner、Deadline、依赖和风险由 `$switchbot-japan-campaign` 执行，方法见 [`GTM_WEEKLY_OPERATING_RHYTHM.zh-CN.md`](../docs/workflow/GTM_WEEKLY_OPERATING_RHYTHM.zh-CN.md)；
- KOL / PR 方法见 [`KOL_PR_PLAYBOOK.zh-CN.md`](../docs/workflow/KOL_PR_PLAYBOOK.zh-CN.md)。

这样可以避免用户面对十几个相似 Skill，也避免多个入口分别读取不同版本的 Product Truth。

## 上下文衔接

```text
日本电商洞察 ──Commerce Insight Pack──> 日本电商内容生成
日本营销活动策划与复盘 ──Campaign Context──> 日本 EDM 制作
                                  ├──────────────> KOL / PR
                                  ├──────────────> 渠道素材
                                  └──────────────> Campaign Review
```

用户说“继续”“下一步”“只修改这张/这一段”时，入口 Skill 先读取正式项目状态，只执行最小必要步骤。下游不得重新解释已经冻结的产品、Offer、日期、链接、指标口径或精确资产。

## 默认自动化

默认执行到下一个 Material Human Gate，而不是每一步确认。

自动完成：

- 项目解析、来源定位、内部路由；
- 在已批准范围内选择模式、Formula、Template 或 Pattern；
- Draft、Brief、Review HTML、Run Manifest 和 QA；
- 两轮以内不改变事实/范围的文案、排版和移动端修复；
- 按 Owner 合并缺口和补证请求；
- 保留已批准内容，只重开最小必要范围。

必须人审：

- Product / Variant / Bundle / Offer；
- Claim、价格、折扣、日期、认证、法务和外部链接；
- Target、Positioning、Primary Message 或 Scope 改变；
- 新视觉方向、精确最终资产、Visual Freeze；
- 飞书/Product Knowledge 正式写回、Bitly、Amazon 上传、ESP 发送和外部发布。

详细边界：[`../operator/review-policy.yaml`](../operator/review-policy.yaml)。

## Runtime 一致性

- GitHub `main` 下的 `skills/` 是正式 Runtime Authority。
- `runtime/skill-lock.json` 锁定 Project Context、Project Memory、Product Knowledge 与四个中文入口的完整仓库 Tree Hash。
- `$CODEX_HOME/skills/` 只作为安装镜像；实时状态由 `scripts/verify_codex_runtime.py` 输出。
- `scripts/sync_codex_skill_mirror.py` 只允许从 clean `main` 单向同步，禁止 Global Mirror 反向写回仓库。
- `inventory/skill_inventory.csv` 和 `docs/SKILL_CATALOG.md` 由 `scripts/build_skill_inventory.py` 生成；本机存在但仓库无源码的接口不列为正式 Skill。
- 未进入 Runtime Lock 的 supporting Skill 在使用前必须验证；缺失时输出 `BLOCKED_RUNTIME_MISSING`，不能假装已经运行。
- `runtime/skill-surface.yaml` 定义四个用户入口、旧Skill归属和内部目录；`scripts/consolidate_codex_skill_surface.py` 默认只输出迁移计划，只有在 clean `main` 且Runtime验证通过时才允许移动。`--restore` 只恢复本次Journal记录的移动，不会把迁移前已在内部目录的模块重新暴露。
- 正式入口若仍是旧Runtime软链接，单向同步会用GitHub版本替换该链接，但不会删除链接指向的原源码；回退仍可从原仓库或Git历史执行。

合并后的本机启用顺序固定为：先从 clean `main` 运行 `sync_codex_skill_mirror.py --apply`，确认所有锁定入口为 `RUNTIME_IN_SYNC`；再运行 `consolidate_codex_skill_surface.py --project-root <workspace> --apply`。顺序不满足时脚本会拒绝移动旧入口。

## 能力边界

- Product Knowledge、官方资料和正式项目记录仍是事实源。
- 研究洞察、评论、KOL 和媒体内容不能自动升级为 Approved Claim。
- 正式产品本体不能由 AI 重绘。
- 价格、Offer、法务、正式写入、Bitly、发布、Final Human 和 ESP Gate 不得被自动绕过。
- `VISUAL_DELIVERABLE_CANDIDATE` 不等于 `PRODUCTION_READY`。
- Renderer、浏览器或正式 Runtime 没有实际运行时，不得声称相应 QA 已通过。
- GitHub 只保存可版本管理的规则、Schema、脚本、空模板和合成 Fixture；不提交 Secret、未发布产品资料、真实审批、飞书快照或未授权素材。

## 更新规则

新能力优先并入上述四个入口的模块和统一 Handoff。只有当能力拥有完全不同的用户任务、数据契约和交付物时，才新增用户可见 Skill。旧入口默认关闭隐式触发，但保留成熟 Runtime 与回归测试。
