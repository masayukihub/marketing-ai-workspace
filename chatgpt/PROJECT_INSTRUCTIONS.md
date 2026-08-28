# ChatGPT Project Context Contract

本目录用于让 ChatGPT 读取 GitHub 项目状态，但不创建新的 Truth Source。

## Runtime Authority

1. GitHub `main` 是项目、Skill 和正式状态的唯一版本控制 Authority。
2. 讨论具名项目、Skill、“继续”或“下一步”时，必须先确认最新 `main` HEAD。
3. 依次读取最新 `main` 的 `AGENTS.md`、`projects/<project-id>/project.yaml`，再读取 Manifest 指向的任务相关 Sources。
4. `projects/<project-id>/chatgpt-context.md` 只是生成型阅读快照，不是 Product Truth、Project Memory、Decision 或 Approval。
5. ChatGPT Memory 与历史聊天不得覆盖 GitHub Product Knowledge、Project Memory、Decision 或 Manifest。
6. 无法读取或确认 GitHub `main` 时，输出 `GITHUB_CONTEXT_UNVERIFIED`，不得把快照或历史聊天提升为当前正式状态。
7. 对话中出现的批准，只有在相应 Decision/状态写入 GitHub 并合并到 `main` 后，才成为 Formal State。

## Truth Precedence

```text
GitHub Product Knowledge / Project Memory / Decision
>
ChatGPT generated snapshot
>
Chat history / ChatGPT Memory
```

发生冲突时保留差异并以更高层级为准；不得静默回写或自动批准 Product Truth、Claim、价格、上市信息、Visual Freeze、Asset、Send 或 Publication。

## Minimum Read Procedure

1. 获取并记录 `main` HEAD。
2. 读取根目录 `AGENTS.md`。
3. 用 `project-context-resolver` 解析项目和任务类型。
4. 读取 Context Package 中标记为 available 的最小 Sources。
5. 检查 `effective_freshness_status`、Blocker、Human Approval 与 Next Action。
6. 快照 commit 与最新 `main` 不一致时，先重新生成或直接读取最新 GitHub Sources。
