# 从这里开始：SwitchBot Japan Marketing AI Workspace

这个页面是日常使用入口。你不需要先判断该调用哪个旧 Skill，也不需要理解内部 Router、Hash 或 Gate 实现。

## 30 秒开始

给 ChatGPT 或 Codex 说明四件事即可：

```text
项目：
要解决的问题：
可用来源：
期望输出：
```

系统随后应自动完成：

```text
确认最新 GitHub main
→ 解析项目 Manifest
→ 读取最小必要 Context
→ 自动路由到四个中文入口之一
→ 执行到下一个真正需要人工判断的 Gate
→ 只显示“已完成 / 待处理 / 下一步”
```

默认不要求你选择内部 Skill、模板、Renderer 或测试命令。

## 四个日常入口

| 你要做的事 | 统一入口 | 常用模式 |
|---|---|---|
| 日本市场、关键词、竞品、VOC、Listing 证据、KOL/媒体前置研究 | `$jp-commerce-insights` | `FULL` / `COMPETITOR` / `VOC` / `KEYWORD` / `UPDATE` |
| Amazon JP Gallery、A+、Listing 文案、产品卖点图、Creative Brief、Review HTML | `$jp-commerce-content-flow` | `MVP` / `PLAN_ONLY` / `PRODUCE` / `LOCAL_REVISION` / `RESUME` / `HARDEN` |
| GTM、Launch Readiness、项目管理、KOL/PR 规划、渠道素材、Tracking、活动复盘 | `$switchbot-japan-campaign` | `PLAN` / `READINESS` / `EXECUTION` / `TRAFFIC` / `REVIEW` / `FULL` |
| 日本 EDM 文案、Brief、HTML、视觉、修改和发送前 QA | `$switchbot-japan-edm` | `COPY` / `DESIGN_BRIEF` / `HTML_VISUAL` / `LOCAL_REVISION` / `RESUME` / `SEND_READINESS` |

内部的 Product Knowledge、Project Memory、Project Context Resolver、Visual Router、Amazon Renderer、Campaign Review Runtime、EDM Runtime、Influencer Marketing 等能力由系统自动调用。

## 直接复制的常用指令

### 继续一个已有项目

```text
读取最新 GitHub main，解析【项目名】的 project.yaml 和当前 Next Action。
不要重新询问已经批准的决定，也不要让我选择内部 Skill。
自动执行到下一个 Material Human Gate；普通过程只汇报：已完成、待处理、下一步。
```

### S30 mini：继续 Amazon 三图

```text
使用 $jp-commerce-content-flow，解析 S30 mini 项目。
只继续 Amazon.co.jp 水箱版 G01-WT、G02、G03 当前允许的范围。
继承已接受的 Visual Planning Decision；不要重新问视觉方向，不要使用未批准 Claim，不要混入 Mini 水基站能力。
自动完成最小必要规划和 QA，停在下一次内容或视觉人工审核 Gate。
```

### Lock Ultra Max：KOL 与 PR 历史复盘

```text
使用 $switchbot-japan-campaign，解析 Lock Ultra Max 项目。
先调用 $jp-commerce-insights 完成 SwitchBot 过往 Lock 系列及竞品的 KOL/PR 证据审计，
再由 influencer-marketing 内部模块形成合作方向、名单标准、媒体方向、Brief 和预期指标。
一次性输出 Review Pack；不要逐条询问，不要自动发送邀约。
```

### homerunPET：YouTube KOL 名单与 Brief

```text
使用 $switchbot-japan-campaign，解析 homerunPET 项目。
目标为日本 YouTube 宠物向 KOL，优先 1万–10万粉丝、测评过同类竞品、未合作过 homerunPET、适合喂食器/吹水机/洗澡器。
先完成来源可追溯的候选名单和筛选理由，再输出合作 Brief、预期结果和 Tracking 方案。
私人联系方式不得提交 GitHub；停在名单与 Brief 人工审核 Gate。
```

### Daily Station：新品 EDM

```text
使用 $switchbot-japan-edm，解析 Daily Station 项目和已确认 Campaign Context。
先检查 Product Truth、官方素材、CTA 和活动信息；可用时自动选择历史 Formula/Template 并生成日语文案、600px HTML、桌面和移动端 QA。
缺少硬性输入时一次性输出按 Owner 分组的 Blocker Pack，不要逐项询问。
```

### 统一生成 Brief

```text
读取最新 GitHub main，解析【项目名】。
根据已确认的 Product Truth、Project Memory、Campaign Context 和可用素材，
为【Amazon / EDM / KOL / PR / 视频 / SNS / LP】生成可执行 Brief。
自动路由到正确入口；所有事实和 Claim 标明来源或 NEED_CONFIRMATION；
输出 Mandatory、Do Not、Deliverables、Owner、Deadline 和 Acceptance Criteria，停在 Brief Human Review Gate。
```

### 生成产品视觉或卖点图

```text
根据【项目】当前有效 Product Truth、Insight Pack、官方产品素材和 Visual Decision，
自动选择正确渠道入口，生成【交付范围】的视觉候选。
正式产品本体不得由 AI 重画；AI 只生成 Scene Layer；文字和图形程序化排版。
自动完成两轮以内安全修复和 Desktop/Mobile QA，停在精确资产或 Whole-set Human Review Gate。
```

### 每周 GTM 风险报告

```text
使用 $switchbot-japan-campaign 的 EXECUTION 模式，读取最新 GitHub main 并解析当前 Active Projects。
只输出相较上周新增/变化的状态、P0/P1、未来两周里程碑、Owner、Deadline、影响和 Next Action。
缺口一次性按 Owner 分组，不逐项询问；不修改正式日期、价格、Offer 或发布状态。
```

### 2026 秋促：建立活动项目

```text
当前仓库还没有正式的 2026 Autumn Campaign Project。
先按 PROJECT_BOOTSTRAP_REQUIRED 处理：整理来源、目标、Owner、日期、产品/Offer、渠道和历史参考，
生成项目建档 Review Pack，不自动创建正式 Product Truth、价格、Claim 或发布状态。
审核通过后再建立 project.yaml 和 Project Memory。
```

### Campaign 数据复盘

```text
使用 $switchbot-japan-campaign 的 REVIEW 模式，读取活动数据、口径和 Product Knowledge。
先做数据质量检查，再输出管理结论、渠道/产品/阶段表现、原因诊断、继续/调整/停止/新增动作及 Owner。
总比例按分子分母汇总，不平均渠道比例；不能确认的归因保持 Unverified。
```

## 默认自动化边界

系统默认自动继续以下工作：

- 项目解析、来源定位、格式转换和重复项清理；
- 在已锁定范围内选择执行模式、内部模块和已验证模板；
- 生成内部 Draft、Brief、Review HTML 和 QA 报告；
- 最多两轮安全的文案去重、长度、排版和移动端修复；
- 将多个缺口合并为按 Owner 分类的一次性补证清单；
- 保留已批准内容，只做最小必要修改。

只在以下情况停下：

- Product / Variant / Bundle / Offer 无法唯一确定；
- 需要批准或扩大 Claim、价格、折扣、日期、认证、合规或外部链接；
- 没有可继承的视觉决定且 Visual Router 低置信度或冲突；
- 需要批准精确最终素材、Visual Freeze、EDM Final、ESP、外部发送或发布；
- 两次自动修复后仍未通过硬性 QA。

完整规则见 [`operator/review-policy.yaml`](operator/review-policy.yaml)。

## 当前正式项目入口

| Project ID | 项目 |
|---|---|
| `s30-mini` | S30 mini Japan |
| `lock-ultra-max` | Lock Ultra Max Japan |
| `daily-station` | Daily Station Japan |
| `homerunpet` | homerunPET Japan |

项目当前状态必须从最新 `projects/<project-id>/project.yaml` 动态读取，不以此页面或历史聊天为准。

根据过往工作识别、但尚未正式建档的候选项目见 [`projects/PROJECT_INBOX.md`](projects/PROJECT_INBOX.md)。候选项不等于 Active Project。

## 重要边界

- 飞书和官方资料是 Source of Record；GitHub 保存规则、可追溯状态和可版本管理能力。
- GitHub `main` 是正式 Runtime Authority；`$CODEX_HOME/skills` 只是安装镜像。
- ChatGPT 历史聊天可以帮助发现需求，但不能覆盖 Product Knowledge、Project Memory、Decision 或 Manifest。
- 面向日本消费者的文案使用自然日语；解释和内部 Review 默认使用中文。
- 公司名统一为 `SWITCHBOT株式会社`；产品名使用 `SwitchBot + 正式产品名`；日语中的 hub 使用「ハブ」。
- AI 不得重画正式产品本体；场景层、产品层、文字/图形层必须分开。
- Candidate、QA PASS 或视觉完成都不等于可正式发布。

## 进一步查看

- 工作流索引：[`docs/workflow/README.md`](docs/workflow/README.md)
- 完整操作手册：[`docs/workflow/OPERATOR_PLAYBOOK.zh-CN.md`](docs/workflow/OPERATOR_PLAYBOOK.zh-CN.md)
- 统一 Brief：[`docs/workflow/BRIEF_FACTORY_PLAYBOOK.zh-CN.md`](docs/workflow/BRIEF_FACTORY_PLAYBOOK.zh-CN.md)
- AI 视觉生产：[`docs/workflow/VISUAL_AI_PLAYBOOK.zh-CN.md`](docs/workflow/VISUAL_AI_PLAYBOOK.zh-CN.md)
- KOL / PR 专项：[`docs/workflow/KOL_PR_PLAYBOOK.zh-CN.md`](docs/workflow/KOL_PR_PLAYBOOK.zh-CN.md)
- GTM 周度管理：[`docs/workflow/GTM_WEEKLY_OPERATING_RHYTHM.zh-CN.md`](docs/workflow/GTM_WEEKLY_OPERATING_RHYTHM.zh-CN.md)
- 四个 Skill 入口：[`skills/README.md`](skills/README.md)
- Project Context 规则：[`docs/architecture/PROJECT_CONTEXT_SYSTEM.md`](docs/architecture/PROJECT_CONTEXT_SYSTEM.md)
- ChatGPT 读取规则：[`chatgpt/PROJECT_INSTRUCTIONS.md`](chatgpt/PROJECT_INSTRUCTIONS.md)
