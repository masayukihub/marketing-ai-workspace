# Codex Working Rules

## 执行顺序

1. GitHub `main` 的仓库内 Skill 与脚本是正式执行版本；不得默认调用 `$CODEX_HOME/skills/`。全局目录只是安装镜像，必须通过 `runtime/skill-lock.json` 和 `scripts/verify_codex_runtime.py` 验证；`RUNTIME_DRIFT` 或 `MIRROR_MISSING` 时不得静默使用。
2. 项目型任务先通过 `skills/project-context-resolver/` 解析 `projects/<project-id>/project.yaml`。
3. 只读取 Context Package 返回的最小必要来源；再读取对应 `memory/project-memory/<project>/`。
4. 区分 `manifest_updated_at`、`state_as_of` 与 `freshness_status_at_manifest_update`；运行时只使用 Resolver 生成的 `effective_freshness_status`。状态 stale/unknown 时只允许只读审计、Source Refresh 和 Human Review Preparation。
5. 产品事实优先使用 Product Knowledge 和官方 Source；Manifest 不充当产品事实库。
6. 验证 Freshness 与当前 Gate，再执行目标 Skill；Human Approval 未完成时停在 Review Package。
7. 区分 `FACT`、`DECISION`、`HYPOTHESIS`、`RECOMMENDATION`。
8. 找不到证据时写 `UNKNOWN` 或 `NEED_CONFIRMATION`，不得补全。
9. 飞书、正式数据库和官方素材库是只读 Source of Record，除非用户明确授权写入。

## ChatGPT Project Bootstrap

1. 讨论具名项目、Skill、“继续”或“下一步”时，先确认最新 GitHub `main` HEAD，再读取 `AGENTS.md`、项目 Manifest 与任务相关 Sources。
2. `projects/*/chatgpt-context.md` 是生成型只读快照，不是 Truth Source；ChatGPT Memory 和历史聊天不得覆盖 GitHub Product Knowledge、Project Memory 或 Decision。
3. 无法确认 GitHub `main` 时输出 `GITHUB_CONTEXT_UNVERIFIED`，不得把快照或聊天内容提升为当前状态。
4. 对话中的批准只有写入相应正式文件并合并到 GitHub `main` 后，才成为 Formal State。

## Git 与变更

1. `main` 只保存稳定版本。
2. 大型修改前使用 `feature/`、`fix/` 或 `experiment/` 分支。
3. 不重构与任务无关的目录，不破坏成熟 Skill。
4. 修改 Skill 后必须运行工作空间验证和 Skill 自带测试。
5. 测试失败不得合并 `main`。
6. 每次重大修改更新对应 `STATUS.md`；仅在决策已被明确确认时更新 `DECISIONS.md`。

## 安全

1. 禁止提交任何 Secret、Token、Cookie、私钥或真实 `.env`。
2. 禁止提交个人隐私数据、KOL 私人联系方式和未授权客户数据。
3. 发现敏感文件时只报告路径和风险类型，不输出内容。
4. 外部发布、正式数据写入和权限变更必须遵守最小权限原则。

## QA

- Fact QA：未知信息是否被误写为事实？
- Source QA：重要结论是否有来源？
- Logic QA：结论是否由证据支持？
- Japan QA：日本市场表达是否自然且准确？
- Regression QA：是否影响现有 Skill？
- Secret QA：是否可能泄露凭证或个人数据？
