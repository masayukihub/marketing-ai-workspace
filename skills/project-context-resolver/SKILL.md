---
name: project-context-resolver
description: Resolve a named marketing project from projects/*/project.yaml, select the minimum task-specific context, validate current gates, and identify the next permitted action. Use before GTM, Amazon, PR, KOL, campaign, VOC, competitor, design, visual, Product Knowledge, website, SEO, review, EDM, or commercial work on an existing project. Do not use it to scan Feishu, create Product Truth, or replace Project Memory.
---

# Project Context Resolver

Use this Skill as the single preflight for named project work. It is a navigation and state-resolution layer, not a knowledge store.

## Workflow

1. Identify the project by exact `project_id`, `project_name`, or Manifest alias.
2. Read and validate only `projects/<project-id>/project.yaml`.
3. Evaluate `state_as_of` independently from the Manifest edit time.
4. Identify the task type with token-aware matching.
5. Resolve only the source kinds required for that task.
6. Return a Context Package.
7. Validate freshness and the current gate before invoking the relevant execution Skill.

Do not fuzzy-create a project when no exact alias matches. An unknown project returns `PROJECT_BOOTSTRAP_REQUIRED`, recommends `project-memory-manager`, sets `auto_create: false`, and permits only `prepare_project_discovery_review`. Ambiguous aliases still return `PROJECT_AMBIGUOUS`.

## Supported task types

`GTM`, `Amazon`, `PR`, `KOL`, `Campaign`, `VOC`, `Competitor`, `Design`, `Visual`, `Product Knowledge`, `Website`, `SEO`, `Review`, `EDM`, and `Commercial`.

For generic continuation requests such as `继续 S30 mini`, use the Manifest's priorities. The resolver may default the context type to `GTM`, but it must report that default in `warnings`.

## Run

From the repository root:

```bash
python3 skills/project-context-resolver/scripts/resolve_project_context.py \
  --workspace . \
  --request "继续 S30 mini Amazon"
```

Validate every checked-in Manifest:

```bash
python3 skills/project-context-resolver/scripts/resolve_project_context.py \
  --workspace . \
  --validate-all
```

Use `--output <context-package.yaml>` when a durable task artifact is needed. If the selected action requires approval, also pass `--human-review-dir <directory>`; the resolver writes a blank Human Review Package and does not execute the action.

Use `--as-of YYYY-MM-DD` only for deterministic audit/testing. Normal execution evaluates freshness on the current date using `config/freshness.yaml`.

## Context consumption

Consume only `required_sources` whose status is `available`. A `missing` source remains a blocker or warning; it is not permission to search the whole repository. Product facts must still pass `product-knowledge`. Project context and durable writeback must still pass `project-memory-manager`.

`manifest_updated_at` records navigation-file maintenance; `state_as_of` records when project state was actually verified; `freshness_status_at_manifest_update` is only the maintenance-time assessment. Runtime execution must use the Context Package's dynamic `effective_freshness_status`. For active projects beyond the configured threshold, emit `PROJECT_STATE_STALE`. With `stale` or `unknown` state, allow only `read_only_audit`, `source_refresh`, and `human_review_preparation`; return `blocked_by_freshness` for state-dependent execution.

The Context Package contract is defined in [contracts.md](references/contracts.md).

## Next Action rules

For `继续`, `下一步`, `接着做`, or `继续这个项目`:

1. inspect P0, then P1, then P2;
2. skip completed or superseded actions;
3. preserve `blocked_by` dependencies;
4. apply optional `task_types` scope to Blockers and Actions so a channel Gate does not replace or pollute project-wide state;
5. validate `execution_class` against project freshness;
6. if `requires_human_approval: true`, stop at Human Review;
7. never convert a proposed decision or a technical pass into approval.

Routing aliases identify the project only. An alias note such as S20 mini → S30 mini must be returned as `PROJECT_ROUTING_ALIAS_ONLY`; it never approves a product name, Claim, or external copy.

## Conflict rule

If an accepted Human Decision conflicts with the version-controlled Manifest, keep the Manifest as the current execution state and emit `FORMAL_STATUS_DECISION_CONFLICT`. Reconciliation is a reviewed Manifest update, not a silent override.

## Writeback boundary

- Artifact → execution project/output directory.
- Product fact or Claim → Product Knowledge review flow.
- Durable project learning/risk → Project Memory review proposal.
- Human decision → Decision Log only with accepted/final evidence.
- Stage, blocker, or next action → Manifest only after the responsible source is reviewed.

Never update multiple Truth Sources opportunistically. The resolver itself does not scan Feishu and does not change Product Memory or Project Memory.
