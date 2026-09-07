# Marketing AI Workspace

个人 Codex 技能与本仓库的结合点、版本检查和安全更新方法见 [Flow × Codex 衔接与同步](docs/workflow/CODEX_FLOW_INTEGRATION.zh-CN.md)。入口包一致不等于 Renderer、浏览器 QA 或发布就绪。

这是面向 **SwitchBot 日本市场营销** 的长期 AI 工作空间，用来管理可复用 Skills、Project Memory、Product Knowledge、视觉系统、自动化脚本、测试和项目状态。

日常使用先打开：

## [START_HERE.md：从这里开始](START_HERE.md)

你只需要告诉 ChatGPT 或 Codex：

```text
项目：
要解决的问题：
可用来源：
期望输出：
```

系统应自动确认最新状态、解析项目、选择正确的 Skill/内部模块，并执行到下一个真正需要人工判断的 Gate。你不需要先判断该调用哪个旧 Skill、Renderer、模板或测试命令。

本仓库不是飞书或正式产品资料的替代品。飞书与官方资料仍是 Source of Record；Product Knowledge 和 Project Memory 负责治理事实与项目状态；GitHub `main` 保存经过审核、可版本管理的执行能力、Manifest、Decision 和规则。

## 日常只使用四个入口

| 业务任务 | 统一入口 | 常见输出 |
|---|---|---|
| 日本市场、关键词、竞品、VOC、评论、Listing 证据 | `$jp-commerce-insights` | Commerce Insight Pack、Creative Handoff、证据缺口 |
| Amazon JP Gallery、A+、Listing 文案、卖点图、Review HTML | `$jp-commerce-content-flow` | Storyline、Brief、Visual Candidate、Standalone HTML、QA |
| GTM、Launch Readiness、项目管理、KOL/PR、Tracking、活动复盘 | `$switchbot-japan-campaign` | Campaign Context、风险周报、素材计划、KOL/PR Pack、复盘 |
| 日本 EDM 文案、Brief、HTML、视觉和发送前 QA | `$switchbot-japan-edm` | 日语 Copy、600px HTML、Desktop/Mobile Preview、ESP Gate |

Product Knowledge、Project Memory、Project Context Resolver、Visual Router、Amazon Renderer、Campaign Review Runtime、EDM Runtime、Customer Review 和 Influencer Marketing 等能力属于内部模块，由系统自动路由。

## 默认工作逻辑

```text
飞书 / 官方来源
→ Source / Product Truth / Project Memory
→ Project Manifest + Context Resolver
→ 四个中文入口 Skill
→ Draft / Brief / HTML / Visual Candidate
→ Automated QA
→ 一次性 Human Review
→ 受控写回或人工发布
```

默认采用：

```text
AUTONOMOUS_TO_NEXT_MATERIAL_HUMAN_GATE
```

系统自动完成低风险、可逆、已批准范围内的读取、整理、路由、模板选择、Draft、Render、QA 和最多两轮安全修复；只在 Product/Offer、Claim/价格/日期/合规、核心策略、视觉方向、精确最终资产和外部发布等实质节点停下。

这些偏好由 [`operator/`](operator/README.md) 统一管理：

- [`operator/profile.yaml`](operator/profile.yaml)：语言、命名、来源、输出和视觉偏好；
- [`operator/task-routing.yaml`](operator/task-routing.yaml)：将常见需求路由到四个入口；
- [`operator/review-policy.yaml`](operator/review-policy.yaml)：自动继续与 Human Gate 的边界。

Operator 只决定“怎么执行”，不能覆盖 Product Knowledge、Project Memory、Decision 或项目 Manifest。

## 目录说明

| 目录 | 用途 |
|---|---|
| `operator/` | 面向你日常工作的稳定偏好、任务路由和审核边界 |
| `skills/` | 正式 Skill 源码、脚本、测试和内部 Runtime |
| `projects/` | 各营销项目的 Manifest 和工作入口，不复制全部原始素材 |
| `memory/` | Project Memory、产品记忆接口和决策日志 |
| `visual-system/` | 页面类 Skill 共用的 Visual Pattern Memory、Router、Registry 与 Channel Adapter；不作为用户入口 |
| `runtime/` | 关键 Skill 的版本和 Tree Hash 锁定 |
| `chatgpt/` | ChatGPT 读取 GitHub 项目状态时的只读契约 |
| `data/` | 可安全版本管理的结构化数据；默认不放个人信息和原始密钥 |
| `automations/` | 监测与同步任务 |
| `apps/` | Dashboard、报告和内部工具 |
| `docs/` | 工作流、标准、架构与操作手册 |
| `tests/` | 工作空间级验证脚本 |
| `.github/` | Actions、Issue 和 PR 模板 |

## 当前正式项目

| Project ID | 项目 |
|---|---|
| `s30-mini` | S30 mini Japan |
| `lock-ultra-max` | Lock Ultra Max Japan |
| `daily-station` | Daily Station Japan |
| `homerunpet` | homerunPET Japan |

Video Doorbell Vision、Hub 4、AI MindClip 和 2026 Autumn Campaign 等历史需求目前只列在 [`projects/PROJECT_INBOX.md`](projects/PROJECT_INBOX.md) 中。它们必须先完成 Project Bootstrap Review，不能因历史聊天或旧输出自动成为 Active Project。

## 如何让 Codex 工作

Codex 必须按以下顺序：

```text
读取 AGENTS.md
→ 读取 operator/profile.yaml、task-routing.yaml、review-policy.yaml
→ 解析 projects/<project-id>/project.yaml
→ 生成最小 Context Package
→ 读取任务所需 Product Knowledge / Project Memory / Decision / Asset
→ 自动选择四个入口之一
→ 执行到下一个 Material Human Gate
```

示例：

```text
读取最新 GitHub main，解析 S30 mini 项目。
使用 $jp-commerce-content-flow，只继续 Amazon.co.jp 水箱版 G01-WT、G02、G03 当前允许范围。
继承已接受的 Visual Planning Decision，不使用未批准 Claim，不混入 Mini 水基站能力。
自动执行到下一个内容或视觉 Human Gate；普通过程只汇报已完成、待处理、下一步。
```

完整业务手册见：

- [`docs/workflow/OPERATOR_PLAYBOOK.zh-CN.md`](docs/workflow/OPERATOR_PLAYBOOK.zh-CN.md)
- [`docs/workflow/BRIEF_FACTORY_PLAYBOOK.zh-CN.md`](docs/workflow/BRIEF_FACTORY_PLAYBOOK.zh-CN.md)
- [`docs/workflow/VISUAL_AI_PLAYBOOK.zh-CN.md`](docs/workflow/VISUAL_AI_PLAYBOOK.zh-CN.md)
- [`docs/workflow/KOL_PR_PLAYBOOK.zh-CN.md`](docs/workflow/KOL_PR_PLAYBOOK.zh-CN.md)
- [`docs/workflow/GTM_WEEKLY_OPERATING_RHYTHM.zh-CN.md`](docs/workflow/GTM_WEEKLY_OPERATING_RHYTHM.zh-CN.md)

## Runtime Authority

GitHub `main` 下的 `skills/` 是正式 Runtime Authority；`runtime/skill-lock.json` 锁定关键 Runtime。`$CODEX_HOME/skills/` 只作为安装镜像，不得反向覆盖仓库。

检查：

```bash
python3 scripts/verify_codex_runtime.py
python3 scripts/sync_codex_skill_mirror.py --dry-run
```

出现 `RUNTIME_DRIFT`、`MIRROR_MISSING` 或 `REPOSITORY_RUNTIME_MISSING` 时不得静默使用 Global Mirror。实际同步只允许从 clean `main` 单向执行。

ChatGPT 项目读取规则见 [`chatgpt/PROJECT_INSTRUCTIONS.md`](chatgpt/PROJECT_INSTRUCTIONS.md)。`projects/*/chatgpt-context.md` 是可重复生成的阅读快照，不是 Product Truth、Decision 或 Approval。

## 新增 Project

1. 先检查 `projects/PROJECT_INBOX.md` 和现有别名，避免重复项目。
2. 对未知项目返回 `PROJECT_BOOTSTRAP_REQUIRED`，先生成建档 Review Pack。
3. 审核后从 `memory/project-memory/_template/` 创建 Project Memory。
4. 在 `projects/<project-id>/project.yaml` 建立轻量 Manifest。
5. 分别记录 `manifest_updated_at`、`state_as_of` 与 Freshness 来源。
6. 未确认内容使用 `UNKNOWN` / `NEED_CONFIRMATION`，Source 指针使用 `null`。
7. Resolver、测试和 PR 通过并合并 `main` 后，才成为 Formal Project。

## 更新 Skill 或规则

1. 从最新、干净的 `main` 创建 `feature/`、`fix/` 或 `docs/` 分支；
2. 只修改本次任务需要的最小范围；
3. 修改 Skill 时同步更新测试和版本记录；
4. 运行工作空间验证和受影响 Skill 测试；
5. 测试通过后创建 Pull Request；
6. 测试失败不得合并或覆盖 `main`。

## 回退版本

优先使用可追溯的反向提交：

```bash
git log --oneline
git revert <commit-id>
```

不要对共享 `main` 使用 `git reset --hard` 或强制推送。

## 绝对不能上传

- `.env`、API Key、Access Token、Refresh Token、Cookie、密码和私钥；
- 用户个人信息、KOL 私人联系方式和未授权客户数据；
- 浏览器 Profile、Keychain 导出和登录 Session；
- 未获授权的大体积原始图片、视频、邮件正文和飞书导出备份；
- 未发布产品事实、真实价格审批、正式飞书快照和未授权产品素材。

占位配置只能写入 `.env.example`，且值必须为空或使用 `YOUR_..._HERE`。

首次 clone 后运行：

```bash
bash scripts/setup_local_git.sh
```

它会启用本地 `pre-push` 检查并阻止直接推送 `main`。当前 Private Repository 所属的 GitHub 方案不支持服务端 Branch Protection，因此 Pull Request 和通过 Actions 是必须遵守的工作规则。
