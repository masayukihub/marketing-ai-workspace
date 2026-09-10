# Codex Working Rules

## 1. Runtime Authority

1. GitHub `main` 的仓库内 Skill、脚本、Project Manifest 和已合并 Decision 是正式版本控制 Authority。
2. `$CODEX_HOME/skills/` 只是安装镜像，不得默认作为源码或反向写回仓库。
3. 使用全局镜像前必须通过 `runtime/skill-lock.json` 和 `scripts/verify_codex_runtime.py` 验证；出现 `RUNTIME_DRIFT`、`MIRROR_MISSING` 或 `REPOSITORY_RUNTIME_MISSING` 时不得静默使用。
4. 实际镜像同步只允许从 clean `main` 单向执行。

## 2. 每个任务的固定执行顺序

### 具名项目

```text
确认最新 main HEAD
→ 读取 AGENTS.md
→ 读取 operator/profile.yaml
→ 读取 operator/task-routing.yaml
→ 读取 operator/review-policy.yaml
→ 解析 projects/<project-id>/project.yaml
→ 生成最小 Context Package
→ 读取任务相关正式 Sources
→ 路由到四个中文入口之一
→ 执行到下一个 Material Human Gate
```

### 非具名任务

1. 先判断是项目外临时任务，还是需要 `PROJECT_BOOTSTRAP_REQUIRED`。
2. 检查 `projects/PROJECT_INBOX.md` 和现有别名，避免重复建档。
3. 未经 Human Review 不自动创建 Formal Project、Product Truth、Decision 或 Gate 状态。

## 3. Operator Layer

`operator/` 只决定执行偏好、任务路由和 Human Gate，不决定产品事实。

Authority 顺序：

```text
Product Knowledge / Official Source / Project Memory / Accepted Decision / project.yaml
>
Operator defaults
>
Chat history / ad-hoc prompt / model inference
```

必须遵守：

- 内部说明默认简体中文；面向日本消费者和合作方的正式内容使用自然日语。
- 公司名写 `SWITCHBOT株式会社`；产品名采用 `SwitchBot + 正式产品名`；日语中的 hub 写「ハブ」。
- 普通用户只需要使用四个中文入口，不要求其选择内部 Skill、Renderer、Template 或脚本。
- KOL、PR、Campaign Review、Visual Router、Amazon Renderer、EDM Runtime 等由 `operator/task-routing.yaml` 自动选择。
- 稳定跨项目偏好写入 Operator；单项目事实、Owner、Deadline、阶段和决策写入该项目正式治理位置。

## 4. 四个用户入口

| 任务 | 用户入口 |
|---|---|
| 日本市场、关键词、竞品、VOC、评论、Listing 证据 | `$jp-commerce-insights` |
| Amazon JP Gallery、A+、Listing、卖点图、Review HTML | `$jp-commerce-content-flow` |
| GTM、项目管理、KOL/PR、Tracking、活动策划与复盘 | `$switchbot-japan-campaign` |
| 日本 EDM 文案、Brief、HTML、视觉和发送前 QA | `$switchbot-japan-edm` |

只有当一个能力拥有完全不同的用户任务、输入契约和正式交付物时，才提出新增用户可见 Skill；不要为现有内部模块再创造入口。

## 5. Project Context 与 Freshness

1. 项目型任务先通过 `skills/project-context-resolver/` 解析 `projects/<project-id>/project.yaml`。
2. 只读取 Context Package 返回且标记为 available 的最小必要来源，再读取对应 Project Memory。
3. 区分 `manifest_updated_at`、`state_as_of` 与 `freshness_status_at_manifest_update`；运行时只使用 Resolver 的 `effective_freshness_status`。
4. 状态 stale / unknown 时，只允许只读审计、Source Refresh 和 Human Review Preparation。
5. Manifest 只负责项目身份、导航、Gate、Blocker 和 Next Action，不充当 Product Truth 或完整 Project Memory。
6. Product Knowledge 管可复用产品事实、Claim、价格与兼容性；Project Memory 管项目背景、决策、风险、Owner、状态和长期学习。
7. `project-context.yaml` 是 Visual Router 输入，不是通用 Project Manifest。

## 6. 事实和来源规则

1. 产品事实优先使用 Product Knowledge、当前官方 Source 和已接受项目 Decision。
2. Feishu、官方数据库和素材库默认只读，除非用户明确授权写入。
3. 成功认证、工具存在或只返回标题，不等于真实读取了飞书正文或结构化数据。
4. 研究、竞品、VOC、KOL、媒体、历史输出和聊天记忆不能自动升级为 Product Truth 或 Approved Claim。
5. 区分 `FACT`、`DECISION`、`HYPOTHESIS`、`RECOMMENDATION`、`DATA_GAP` 和 `RISK`。
6. 找不到证据时使用 `UNKNOWN`、`NEED_CONFIRMATION`、`CONFLICT` 或 `PENDING_VERIFICATION`，不得补全或写成 0。
7. 历史资料只能继承结构、经验和可比证据，不能覆盖当前产品、Offer、价格、日期、Claim 或资产。

## 7. 默认自主执行

默认模式：

```text
AUTONOMOUS_TO_NEXT_MATERIAL_HUMAN_GATE
```

以下工作无需逐步询问：

- 项目解析、来源定位、格式规范化和去重；
- 在正式范围内选择执行模式和内部模块；
- 继承有效 Visual Freeze、Planning Decision、Formula、Template 或 Pattern；
- 生成内部 Draft、Brief、Review HTML、Run Manifest 和 QA；
- 最多两轮不改变事实/范围的文案去重、缩短、排版和移动端修复；
- 将多个缺口合并为按 Owner 分类的一次性 Action Pack；
- 保留已批准内容，只重开最小必要范围。

不要在普通步骤问“是否继续”。用户说“继续”“下一步”“接着做”时，解析当前正式 Next Action，并进入下一个允许阶段。

详细自动化边界以 `operator/review-policy.yaml` 为准。

## 8. 必须停下的 Material Human Gate

以下任一情况必须停在 Review Package：

- Product、Variant、Bundle、Offer、SKU、ASIN、颜色或 BOM 无法唯一确定；
- 新增/扩大 Claim、价格、折扣、促销期、日期、认证、法务或外部链接；
- 修改 Target、Positioning、Primary Message、Channel Scope 或 Required Asset Set；
- 没有可继承视觉决定且 Router 低置信度、冲突或关键素材缺失；
- 选择精确最终资产、批准 Whole-set、Visual Freeze、Final Content；
- 飞书正式写回、Product Knowledge canonical write、Bitly、Amazon 上传、ESP 发送、社媒/PR 发布或权限变化；
- 两次自动修复后仍未通过硬性 QA。

Human Review 不得由结构验证、浏览器 QA、文件存在或模型自评替代。

## 9. 视觉与资产规则

1. 正式产品本体、Logo、App UI、包装、配件和安装关系只能使用官方或批准素材。
2. AI 可以生成背景、人物、环境、道具、光线和氛围，但不得重画正式产品层。
3. Scene Layer、Product Layer 和 Graphic/Copy Layer 必须分开。
4. 相同 Art Direction 不等于相同 Composition；Whole-set 必须检查节奏和重复。
5. Candidate、视觉完成或 QA PASS 都不等于 Publish Ready。
6. 未实际运行 Renderer、Pillow、Playwright、浏览器或正式 Runtime 时，不得声称相应 QA 已通过。

## 10. 用户沟通

普通阶段只显示：

```text
已完成：
待处理：
下一步：
```

只有 `BLOCKED`、`PARTIAL`、风险较高或用户要求审计时，才展开 Gate、Schema、Hash、Provenance 和完整日志。

建议必须具体到页面、模块、句子、素材、Owner、Deadline 或执行动作，避免只写“优化”“加强曝光”“提升质感”。

## 11. Git 与变更

1. `main` 只保存稳定版本。
2. 修改前从最新、干净的 `main` 创建 `feature/`、`fix/`、`docs/` 或 `experiment/` 分支。
3. 当前已有开放 PR 或用户未提交文件时，优先使用独立 worktree，不覆盖、stash 或误提交用户内容。
4. 不重构与任务无关的目录，不破坏成熟 Skill。
5. 修改 Skill 后必须运行工作空间验证和 Skill 自带测试。
6. 测试失败不得合并 `main`。
7. 每次重大项目状态变化更新对应 `STATUS.md`；只有明确接受的决定才能写入 `DECISIONS.md`。
8. 外部产物、私有 Runtime、飞书快照和未发布素材不得误带入 PR。

## 12. Writeback

Execution Skill 先生成任务 Artifact，再输出一个由对应 Owner 接收的 scoped writeback proposal。

不得在一次无控制操作中同时修改：

```text
Product Knowledge
Project Memory
Decision Log
Project Manifest
```

对话中的批准只有写入正式 Decision/状态并合并 `main` 后，才成为 Formal State。

## 13. 安全

1. 禁止提交 Secret、Token、Cookie、私钥、真实 `.env` 和登录 Session。
2. 禁止提交个人隐私数据、KOL 私人联系方式和未授权客户数据。
3. 发现敏感文件时只报告路径与风险类型，不输出内容。
4. 外部发布、正式数据写入和权限变更遵守最小权限原则。
5. GitHub 只保存可版本管理规则、Schema、脚本、空模板、脱敏报告和合成 Fixture。

## 14. QA

- Fact QA：未知信息是否被误写为事实？
- Source QA：重要结论是否有来源、时间和适用范围？
- Scope QA：Product / Variant / Bundle / Offer / Channel 是否混淆？
- Logic QA：结论是否由证据支持？
- Japan QA：日本市场表达是否自然且准确？
- Claim QA：是否越过批准、条件或适用范围？
- Asset QA：产品层是否真实、授权且绑定正确？
- Mobile QA：是否真实检查目标宽度和交互？
- Regression QA：是否影响现有 Skill、项目或已批准资产？
- Secret QA：是否可能泄露凭证、私人联系方式或未授权数据？

## 15. Context Resilience

1. 一个线程默认只处理一个 Deliverable、Material Gate 或 PR 阶段；项目切换、Architecture 转 Business 时开新线程。
2. PR 创建/合并、Human Gate、Phase 切换、大型 Source Discovery、完整回归、Compact 请求或失败后生成 Handoff。
3. Context 使用量可见时：70% 准备 Handoff，80% 停止新的大范围读取，90% 强制新线程；不可见时不得伪造百分比。
4. 超过 `runtime/context-policy.yaml` 限制的日志、Diff、JSON、HTML、飞书正文和测试输出必须落入 `private-runtime/`。
5. 聊天只返回结论、关键失败和文件路径；不得回显完整 Event Payload、长日志或大段正文。
6. 使用 `python3 scripts/contextctl.py capture --name <name> -- <command>` 捕获大型命令输出。
7. 使用 `python3 scripts/contextctl.py handoff` 保存当前 Branch、Project、Goal、唯一 Next Action、Blocker 与测试路径。
8. 新线程只从 `AGENTS.md + project.yaml + Handoff + git status` 恢复，不依赖旧聊天、ChatGPT Memory 或 `/resume` 作为正式状态。
9. Compact Failure 后不要反复 Retry；读取最新 Handoff 并使用 `contextctl.py resume --project <id> --latest` 开新线程。
10. Handoff 不得保存完整聊天、日志、Diff、HTML、飞书正文、Secret，也不得把 Recommendation 变成 Decision。
11. 生成 Handoff 后提示使用新线程，并只给出下一线程的唯一动作。

详细契约见 `docs/architecture/CODEX_CONTEXT_RESILIENCE.md`。
