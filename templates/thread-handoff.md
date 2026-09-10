# Thread Handoff

本模板用于说明 `schemas/thread-handoff.schema.yaml` 的人工可读含义。实际 Handoff 由 `scripts/contextctl.py handoff` 生成到 `private-runtime/thread-handoffs/`，不提交 Git，也不是 Truth Source。

```yaml
schema_version: "1.0"
handoff_id: generated-id
created_at: ISO-8601 timestamp
repository:
  base_commit: origin-main-sha
  head_commit: current-head-sha
  branch: current-branch
  worktree: repository-relative-or-redacted-path
  git_status: []
project:
  project_id: project-id-or-general
  task_type: task-type
  manifest: projects/project-id/project.yaml
  effective_freshness: current-or-stale-or-unknown
goal: one bounded deliverable or gate
success_criteria: []
completed: []
accepted_decisions: []
changed_files: []
generated_artifacts: []
tests: []
blockers: []
unresolved_questions: []
next_action: exactly one primary action
required_reads:
  - AGENTS.md
forbidden_changes: []
resume:
  recommended_new_thread_name: concise thread name
  bootstrap_prompt: generated pointer-only prompt under 6000 characters
```

Rules:

- `accepted_decisions` 只保存正式 Decision ID 和来源路径；Recommendation 不得写入。
- 禁止保存完整聊天、日志、Diff、HTML、飞书正文或 Secret。
- `required_reads` 最多 12 个；`next_action` 只能描述一个首要动作。
- 新线程必须先读 `AGENTS.md`、Project Manifest 和 Handoff，再检查 Git 状态。
