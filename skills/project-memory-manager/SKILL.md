---
name: project-memory-manager
description: Maintain source-linked Project Memory for ongoing marketing work. Use when discovering current or historical projects from Feishu/local assets, creating or refreshing project context, recording a confirmed project decision, checking stale/conflicting project context, reading project background before executing a named product/GTM/campaign/PR/KOL/Amazon task, or capturing durable post-task learnings. Trigger for requests such as 沉淀项目, 同步项目记忆, 记录决策, 更新项目状态, 检查项目记忆, 读取项目背景, 项目快照, 检查过期信息, 扫描近期项目, or continuing a named project.
---

# Project Memory Manager

Use Project Memory as the current, source-linked project-context layer:

`Feishu = source` → `Project Memory = structured current context` → `Skills = execution`.

Do not make it a document backup or a product-fact authority. Product specs, prices, release status, compatibility, competitor facts, and external Claims remain governed by Product Knowledge and their canonical sources.

## Start

1. For an existing named repository project, first run `project-context-resolver` and read `projects/<project-id>/project.yaml`.
2. Follow the Manifest's `sources.project_memory` and `sources.decisions` pointers. In this repository they resolve under `memory/project-memory/`; do not assume a root-level `project-memory/PROJECT_INDEX.md` exists.
3. Read only the task-relevant Project Memory, decision, and source records returned by the Context Package.
4. Check `Status`, `Last Updated`, `Confidence`, source dates, and open questions before relying on context.
5. Keep `FACT`, `DECISION`, `HYPOTHESIS`, `RECOMMENDATION`, `UNVERIFIED`, and `OUTDATED` distinct.

Use the legacy generated `PROJECT_INDEX.md` workflow only for bootstrap/full audit outputs created by this Skill. Do not make it a prerequisite for existing `marketing-ai-workspace` projects.

If the repository does not exist, or a full audit is requested, use the bootstrap workflow below.

## Bootstrap and refresh

Use the existing local Feishu catalog first. Do not rescan or download original documents indiscriminately.

```bash
# Refresh source metadata first when a fresh Feishu pass is required.
python3 knowledge_base/scripts/refresh_codex_knowledge_pack.py --resume --batch-size 12

# Build or refresh the Project Memory repository.
python3 "$HOME/.codex/skills/project-memory-manager/scripts/project_memory.py" --workspace . --mode initial
python3 "$HOME/.codex/skills/project-memory-manager/scripts/project_memory.py" --workspace . --mode incremental
python3 "$HOME/.codex/skills/project-memory-manager/scripts/project_memory.py" --workspace . --mode check
```

Read [references/governance.md](references/governance.md) before resolving conflict, writing a decision, or promoting an item to Current Truth. Read [references/integration.md](references/integration.md) before connecting another Skill.

## Matching and write-back

- Match by `project_id` and source evidence; do not infer a project from a vague product/category mention.
- Use the source registry to avoid re-reading unchanged sources.
- Treat a changed Critical/High source as a review proposal. Update source metadata, activity score, changelog, and review queue automatically; never silently replace positioning, pricing, product definition, launch strategy, Key Message, or final decision.
- Record a decision only when the source states the decision is accepted/final. Preserve superseded decisions with a link to their replacement.
- After another Skill finishes a project task, write back only a durable fact, confirmed decision, learning, risk, or major result with a source pointer. Otherwise leave no memory change.

## QA and output

Run `--mode check` after each write. It must verify source references, project links, state files, duplicate project IDs, and generated-file integrity.

Expected outputs are `PROJECT_INDEX.md`, per-project context/decisions/sources/changelog, `registry/source_registry.json`, `registry/project_registry.json`, `registry/update_state.json`, `project_discovery_report.md`, and `memory_update_review.md`.
