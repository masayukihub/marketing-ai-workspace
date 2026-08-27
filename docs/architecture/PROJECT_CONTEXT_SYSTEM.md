# Project Context System

## Authority and responsibility

```text
Feishu / official sources
        ↓
project-memory-manager
        ↓
Project Memory / Source Registry
        ↓
Project Manifest
        ↓
project-context-resolver
        ↓
Execution Skill
        ↓
Writeback proposal / Human Review
```

- Product Knowledge owns reusable product facts, price, compatibility, and approved Claims.
- Project Memory owns durable project context, source-linked learnings, risks, and accepted project decisions.
- `project.yaml` owns project identity, source navigation, current mapped gate state, blockers, and next-action routing.
- `project-context-resolver` decides what the current task needs to read; it does not scan Feishu or replace either memory system.
- Execution Skills own task artifacts and their internal gate files.

## Project Manifest contract

Machine schema: [`schemas/project-manifest.schema.yaml`](../../schemas/project-manifest.schema.yaml).

The Manifest is intentionally lightweight. It may contain source paths and a short blocker/action summary, but it must not copy specifications, Claims, customer evidence, creative assets, or full decisions. A missing authority is `null`, not an inferred path.

`projects/<project-id>/project.yaml` is the version-controlled formal status for resolver conflicts. Project Memory remains the descriptive source behind it.

## Context Package contract

Machine schema: [`schemas/project-context-package.schema.yaml`](../../schemas/project-context-package.schema.yaml).

```yaml
project:
task_type:
current_stage:
current_truth:
approved_decisions:
blocking_items:
required_sources:
relevant_skills:
next_valid_actions:
warnings:
```

The package contains paths and status, not copied source bodies. The consuming Skill reads only `required_sources` marked `available` for the selected task type.

## Task-scoped source selection

| Task type | Minimum source kinds |
| --- | --- |
| GTM | Project Memory, decisions, Product Truth, approved Claims |
| Amazon | Project Memory, decisions, Product Truth, approved Claims, Visual Profile, Visual Freeze, assets |
| PR / KOL / Campaign | Project Memory, decisions, Product Truth, approved Claims, assets |
| VOC / Competitor | Project Memory, decisions, Product Truth |
| Design / Visual | Project Memory, decisions, Product Truth, approved Claims, Visual Profile, Visual Freeze, assets |
| Product Knowledge | Product Truth, approved Claims, Project Memory |
| Website / SEO | Project Memory, decisions, Product Truth, approved Claims, assets |
| Review | Project Memory and decisions; task-specific sources are added only when named |

## Shared state model

### Lifecycle stage

`discovery` → `planning` → `validation` → `production` → `launch` → `live` → `review` → `archived`

### Gate status

`not_started`, `in_progress`, `blocked`, `ready_for_review`, `approved`, `rejected`, `superseded`

### Artifact status

`draft`, `candidate`, `review`, `approved`, `frozen`, `published`, `deprecated`

### Compatibility mapping

| Existing state | Shared state | Rule |
| --- | --- | --- |
| `NOT_STARTED` | `not_started` | direct |
| `PARTIAL`, `IN_PROGRESS`, `CONDITIONAL` | `in_progress` | unless an explicit blocker controls the current gate |
| `BLOCKED`, `FAIL`, `NO-GO`, `NOT_PROMOTED` | `blocked` | direct fail-closed mapping |
| `PENDING_FINAL_HUMAN_REVIEW`, `HUMAN_REVIEW_REQUIRED` | `ready_for_review` | approval still required |
| `PASS`, `APPROVED`, `HUMAN_ACCEPTED` | `approved` | only when the named gate has authoritative evidence |
| `REJECTED` | `rejected` | direct |
| `SUPERSEDED`, `OUTDATED` | `superseded` | history retained |
| `DRAFT` | artifact `draft` | artifact only; not a gate pass |
| `CANDIDATE` | artifact `candidate` | artifact only; not a gate pass |
| `FROZEN` | artifact `frozen` | does not imply published |
| `PUBLISHED`, `LIVE` | artifact `published`; lifecycle `live` | only with release evidence |

Structural validation, browser QA, and file existence never promote a Human Review or publication gate.

## Before Task contract

For a named project task:

1. resolve the project by Manifest ID/name/alias;
2. validate the Manifest;
3. infer or accept the task type;
4. emit a minimal Context Package;
5. validate the relevant project gate;
6. let the execution Skill read only the returned sources.

If no exact project can be resolved, stop with `PROJECT_NOT_FOUND` or `PROJECT_AMBIGUOUS`. Do not fuzzy-create a project.

## Next Action resolver

For `继续`, `下一步`, `接着做`, or `继续这个项目`:

1. select the first incomplete P0, then P1, then P2 action;
2. preserve blocker dependencies;
3. if the action requires Human Approval, return `human_review_required` and generate a blank Human Review Package when an output directory is requested;
4. never execute or approve the action inside the resolver.

## Writeback contract

| Result type | Owner | Allowed writeback |
| --- | --- | --- |
| Artifact | execution project/output directory | write the artifact and its own QA/state file |
| Durable Fact | Product Knowledge or Project Memory, depending on fact type | source-linked review proposal; major facts require review |
| Human Decision | project `DECISIONS.md` or cross-project Decision Log | only accepted/final evidence; preserve superseded history |
| Project stage change | `project.yaml` | update only with authoritative evidence; record source |
| New blocker | `project.yaml.blocking_items` | add source and mapped gate state |
| New next action | `project.yaml.next_actions` | add priority, status, source, approval requirement |

An execution Skill must not update Product Knowledge, Project Memory, Decision Log, and Manifest in one uncontrolled operation. It should write its artifact first, then produce one scoped writeback proposal for the responsible owner.

## Skill integration matrix

| Skill | Resolver preflight | Context consumed | Writeback owner |
| --- | --- | --- | --- |
| `product-knowledge` | named project only | project identity, Product Truth pointer, blockers | Product Knowledge; Manifest only after reviewed stage/blocker change |
| `project-memory-manager` | always for named projects | Manifest, Project Memory, decisions | Project Memory review proposal; then Manifest navigation/status |
| `amazon-japan-pdp-generator` | required | Amazon-scoped truth, Claims, visual, freeze, assets | Amazon artifacts; approved gate changes proposed to Manifest |
| `amazon-listing-creative` | required | Amazon-scoped truth, Claims, visual, assets | creative artifacts; no direct truth promotion |
| `switchbot-campaign-review` | required | campaign-scoped Project Memory, decisions, Product Truth | campaign artifact; durable result proposal to Project Memory |
| `customer-review-intelligence` | required | VOC-scoped Project Memory and Product Truth | VOC artifacts; learning/risk proposal to Project Memory |
| `influencer-marketing` | required | KOL-scoped Project Memory, decisions, Product Truth | KOL artifact; confirmed result/decision proposal |
| visual pattern records | through Design/Visual/Amazon task | Visual Profile/Freeze when present | reference library or project visual artifact; never Product Truth |
| installed `jp-commerce-*` Skills | shared contract defined; repository adapter pending | Amazon/Competitor/VOC package selected by task type | their existing artifact gates; reviewed changes return through the owning memory layer |
| installed media/PR Skills | shared contract defined; repository adapter pending | PR-scoped Project Memory, decisions, Product Truth, Claims, assets | PR/media artifact; confirmed decision or result proposal |

The `jp-commerce-*` and media/PR Skills are installed outside this repository, so this branch does not silently edit those runtime copies. Their next checked-in revision should add the same five-step Before Task contract. Placeholder directories without a canonical `SKILL.md` remain compatibility references and are not selected as primary runtime Skills.

## Incremental migration plan

1. **Phase 1 — compatibility:** add Manifests, resolver, schemas, and Before/After contracts; keep all old paths.
2. **Phase 2 — adoption:** make canonical project Skills consume Context Packages; compare results with existing direct lookup.
3. **Phase 3 — status convergence:** update Manifest only from reviewed Product/Project Memory and accepted decisions.
4. **Phase 4 — cleanup proposal:** after usage evidence, propose removal of duplicate status summaries or placeholder routing. No deletion occurs automatically.

## Conflict rule

When an accepted Human Decision declares `target_gate` and `expected_status` and the version-controlled current Manifest disagrees, `project.yaml` is used for current execution state and the resolver emits `FORMAL_STATUS_DECISION_CONFLICT`. The decision is retained as evidence; reconciliation requires a reviewed Manifest update rather than silently overriding either record. Accepted decisions without an explicit gate expectation do not imply overall project approval.
