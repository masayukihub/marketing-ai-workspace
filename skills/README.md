# Skills

面向日常使用只保留四个中文入口。旧 Skill 不删除成熟代码，以内部模块、兼容入口或 Runtime 形式保留脚本、测试和回退能力。

| 用户入口 | 什么时候用 | 内部整合能力 |
|---|---|---|
| `$jp-commerce-insights`（日本电商洞察） | 选品、关键词、竞品、评论、VOC、Listing素材采集 | 电商选品情报、Amazon Keyword Miner、Amazon Competitor Reviews、Amazon VOC Browser Scraper、Amazon Listing Asset Capture |
| `$jp-commerce-content-flow`（日本电商内容生成） | 日亚 Gallery、A+、Listing 文案、视觉稿、Content Review HTML、继续现有项目 | JP Commerce Creative Flow、Amazon Japan PDP Generator、Amazon Listing Creative |
| `$switchbot-japan-campaign`（日本营销活动策划与复盘） | GTM、Launch Readiness、渠道素材需求、Tracking/UTM、目标、执行和复盘 | gtm-thinking-framework、jp-traffic-link-governance、switchbot-campaign-review |
| `$switchbot-japan-edm`（日本EDM制作） | 日本 EDM 策略、产品排序、日语文案、历史模板、HTML/视觉和发送前 QA | optimize-japan-edm、edm-generator，以及待源码核验的 EDM Stable Runtime/Visual Template |

## 最简单的用法

```text
使用 $jp-commerce-insights，调研S30 mini在日本小户型市场的机会，
输出关键词、竞品、VOC、用户障碍和Creative Handoff。
```

```text
使用 $jp-commerce-content-flow，读取S30 mini的Product Truth和Insight Pack，
继续Amazon Gallery G01-G03；完成Review后再进入正式HTML。
```

```text
使用 $switchbot-japan-campaign，沿用历史活动结构，
完成2026秋促的渠道素材需求、营销策划、Tracking计划和复盘模板。
```

```text
使用 $switchbot-japan-edm，读取已确认的Campaign Truth和产品资料，
制作一封日本促销EDM；先交付日语文案，再完成HTML、手机预览和发送前QA。
```

## 上下文衔接

```text
日本电商洞察 ──Insight Pack──> 日本电商内容生成
日本营销活动策划与复盘 ──Campaign Context──> 日本EDM制作
                                  └──────────────> 其他渠道素材
```

用户说“继续”“下一步”“只修改这张/这一段”时，入口 Skill 先读取正式项目状态，只执行最小必要步骤。下游不得重新解释已经冻结的产品、Offer、日期、链接或指标口径。

## Runtime 一致性

- GitHub `main` 下的 `skills/` 是正式 Runtime Authority。
- `runtime/skill-lock.json` 锁定 Project Context、Project Memory、Product Knowledge 与四个中文入口的完整仓库 Tree Hash。
- `$CODEX_HOME/skills/` 只作为安装镜像；实时状态由 `scripts/verify_codex_runtime.py` 输出。
- `scripts/sync_codex_skill_mirror.py` 只允许从 clean `main` 单向同步，禁止 Global Mirror 反向写回仓库。
- `inventory/skill_inventory.csv` 和 `docs/SKILL_CATALOG.md` 均由 `scripts/build_skill_inventory.py` 生成；本机存在但仓库无源码的接口不列为正式 Skill。

## 能力边界

- Product Knowledge、官方资料和正式项目记录仍是事实源。
- 研究洞察和评论不能自动升级为 Approved Claim。
- 正式产品本体不能由 AI 重绘。
- 价格、Offer、法务、正式写入、Bitly、发布、人工 Final 和 ESP Gate 不得被自动绕过。
- `VISUAL_DELIVERABLE_CANDIDATE` 不等于 `PRODUCTION_READY`。
- 截图中声明已安装、但源码尚未进入本仓库的 Skill 只记录接口映射；取得完整目录和测试前，不宣称完成源码迁移。
- GitHub 只保存可版本管理的规则、Schema、脚本、空模板和合成 Fixture；不提交 Secret、未发布产品资料、真实审批、飞书快照或未授权素材。

## 更新规则

新能力优先并入上述四个入口的模块和统一 Handoff。只有当能力拥有完全不同的用户任务、数据契约和交付物时，才新增用户可见 Skill。旧入口默认关闭隐式触发，但保留成熟 Runtime 与回归测试。
