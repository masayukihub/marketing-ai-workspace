# Skill Integration Contract

## Before a project task

1. Use the checked-in repository Skill runtime as the formal execution source. A global installation is only a mirror; validate `runtime/skill-lock.json` with `scripts/verify_codex_runtime.py` and stop on `RUNTIME_DRIFT`, `MIRROR_MISSING`, or `REPOSITORY_RUNTIME_MISSING`.
2. For an existing `marketing-ai-workspace` project, resolve `projects/<project-id>/project.yaml` through `project-context-resolver`.
3. Follow only the returned `project_memory` and `decisions` pointers. Use a generated `PROJECT_INDEX.md` only when operating on a separate bootstrap repository that actually contains it.
4. Read the smallest matching context and relevant decision record.
5. For product facts, invoke Product Knowledge and verify canonical sources as required.

## During a project task

Label conclusions as Fact, Insight, Hypothesis, or Recommendation. Do not present a Project Memory hypothesis as a fact.

## After a project task

Propose a write-back only for a durable fact, confirmed decision, reusable learning, material risk, or major result. Include the source, date, scope, confidence, and whether review is required. Do not overwrite the context directly when the change is major or conflicted.

After the responsible memory/decision review is accepted, update only the corresponding Manifest navigation, gate, blocker, or next-action field. Do not make the execution Skill write every layer itself.

## Recommended consumers

- Product Knowledge: governed product facts, distinct from project context.
- Campaign Review and VOC: durable learnings/risk proposals.
- Amazon, PR, KOL, Launch, Product Marketing, Competitor: project context and decisions before execution.
