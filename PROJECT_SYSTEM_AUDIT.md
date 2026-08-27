# Project System Audit

- Audit date: 2026-08-27
- Repository: `marketing-ai-workspace`
- Scope: `projects/`, `memory/`, `skills/`, `automations/`, `AGENTS.md`, project YAML/Markdown, Product Memory, Project Memory, Decision Log, and visual-pattern records
- Constraint: this audit does not change existing business facts, decisions, claims, assets, or channel outputs

## Executive conclusion

The repository already has the correct conceptual layers, including the newly checked-in Phase 1 `visual-system/`, but the runtime entry contract is incomplete. Project entrypoints, Project Memory, Product Knowledge, Skill-specific state files, and project visual contracts exist in parallel without one lightweight resolver. The highest-impact defect is a path and contract mismatch: the repository stores Project Memory under `memory/project-memory/`, while the checked-in `project-memory-manager` expects `<workspace>/project-memory/PROJECT_INDEX.md`; that index does not exist here.

The incremental fix is therefore:

1. make `projects/<project-id>/project.yaml` the project-navigation and current-gate entry;
2. keep Product Knowledge, Project Memory, Decision Log, approved Claims, assets, and visual records in their existing owners;
3. resolve only task-relevant sources through `project-context-resolver`;
4. preserve all existing Skill states through explicit mappings rather than renaming or deleting them.

## 1. Current projects

Four repository projects have both a `projects/` entry and Project Memory. They are treated as Active because their current records are not archived and describe ongoing discovery or validation work.

| Project | Existing project entry | Existing Project Memory | Current state before migration | Next Action source |
| --- | --- | --- | --- | --- |
| S30 mini Japan | `projects/s30-mini/README.md` | `memory/project-memory/s30-mini/` | Context migration / Gate 1 evidence review; `PARTIAL`; blocked by unapproved Product Truth and commercial facts | `memory/project-memory/s30-mini/TODO.md` |
| Lock Ultra Max Japan | `projects/lock-ultra-max/README.md` | `memory/project-memory/lock-ultra-max-jp/` | Discovery / context consolidation; `PARTIAL`; naming, Product Definition, Claim, and launch status pending | `memory/project-memory/lock-ultra-max-jp/TODO.md` |
| Daily Station Japan | `projects/daily-station/README.md` | `memory/project-memory/daily-station-jp/` | Discovery / context consolidation; `PARTIAL`; Product Truth, Claim, and asset approval pending | `memory/project-memory/daily-station-jp/TODO.md` |
| homerunPET Japan | `projects/homerunpet/README.md` | `memory/project-memory/homerunpet-jp/` | Discovery / context consolidation; `PARTIAL`; objective, Japan facts, and current decisions pending | `memory/project-memory/homerunpet-jp/TODO.md` |

`Video Doorbell` and `AI MindClip` appear as Product Knowledge entities, but they do not currently have `projects/` entries or Project Memory in this repository. They are therefore products, not Active Projects for this migration. No repository project was found for a `2026 Autumn Campaign`.

Workspace-local, untracked files such as `projects/s30-mini/japan-listing-demo/` are not promoted into the versioned project system by this change.

## 2. Current project entrypoints

Before this migration, each project entry was a short README that linked directly to `PROJECT.md`. Phase 1 Visual Pattern Memory added `project-context.yaml` plus Visual Profile/Freeze files for S30 mini and Lock Ultra Max, but those contracts are scoped to visual routing and do not expose the full project aliases, Product/Project Memory navigation, formal gate status, blockers, Skill routing, or priority actions.

The new compatibility entry is `projects/<project-id>/project.yaml`. Existing README, Project Memory, and visual contracts remain valid and are not moved. `project-context.yaml` remains the Visual Router input; it is not a second general project Manifest.

## 3. Product Truth location

The governed Product Truth layer is `skills/product-knowledge/`:

- normalized canonical records: `skills/product-knowledge/references/`;
- readable product profiles: `skills/product-knowledge/products/` and `skills/product-knowledge/knowledge/products/`;
- runtime entity index and validation: `skills/product-knowledge/outputs/`.

`memory/product-memory/README.md` is only an interface placeholder. It explicitly does not contain product facts. S30 mini and Lock Ultra Max do not have promoted Product Knowledge profiles in the checked-in runtime, so their Manifest pointers remain `null` rather than pointing to draft artifacts.

## 4. Project Memory location

Project Memory is stored under `memory/project-memory/<memory-id>/` with:

- `PROJECT.md`: durable context and open questions;
- `STATUS.md`: current stage/readiness/blockers;
- `DECISIONS.md`: project-specific accepted decision history;
- `SOURCES.md`: source registry view;
- `TODO.md`: P0/P1/P2 actions;
- `CHANGELOG.md`: generated refresh history where present.

Directory IDs are not fully normalized: `lock-ultra-max` points to `lock-ultra-max-jp`, `daily-station` to `daily-station-jp`, and `homerunpet` to `homerunpet-jp`. The Manifest alias layer absorbs this without moving directories.

## 5. Decision location

Project decisions belong in `memory/project-memory/<memory-id>/DECISIONS.md`. The cross-project `memory/decision-log/` currently contains only a README and no accepted entries. Existing project decision files contain no confirmed business decision for the four Active Projects.

## 6. Current status expression

The closest current project-level status source is `memory/project-memory/<memory-id>/STATUS.md`. Status is also repeated inside some `PROJECT.md` files and many execution Skills use their own state artifacts, for example:

- Amazon: `PROJECT_STATE.json`, Story/Layout/Publish gates;
- campaign/VOC: run manifests and completeness states;
- EDM: production truth, readiness, asset and Human Review states;
- automation READMEs: `NOT_IMPLEMENTED` or `PARTIAL`.

There was no common state vocabulary or explicit authority rule between these layers.

## 7. Next Action availability

All four Active Projects have `TODO.md`. Daily Station, Lock Ultra Max, and homerunPET also repeat generic Next Actions inside `PROJECT.md`. S30 mini uses a shorter custom `PROJECT.md`. Priority exists, but action status, approval requirement, and blocker dependency were not machine-readable.

## 8. How Skills currently find project context

| Skill/layer | Current lookup behavior | Gap |
| --- | --- | --- |
| `project-memory-manager` | expects `<workspace>/project-memory/PROJECT_INDEX.md`, then `project_context.md` | path/file contract does not match this repository |
| `product-knowledge` | resolves product entity from `outputs/product_index.json` and canonical records | no project stage, blockers, or decisions |
| `amazon-japan-pdp-generator` | reads task inputs, Knowledge Units, Product Knowledge, and its own `PROJECT_STATE.json` | no shared project manifest preflight |
| `amazon-listing-creative` | checks Knowledge Pack/Product Knowledge | no shared project/decision preflight |
| `jp-commerce-content-flow` | restores its own project state and Visual Router inputs | unified user entry, but no general project Manifest preflight before this migration |
| `jp-commerce-insights` | selects research mode and builds its own evidence pack | no shared project gate/blocker preflight before this migration |
| `switchbot-japan-campaign` | builds a Campaign Context and restores project files | no shared general project Manifest preflight before this migration |
| `switchbot-campaign-review` | accepts source registry/local task and Product Knowledge | no shared current project gate |
| `customer-review-intelligence` | reads local config and Product Knowledge | no project-level blocker/next-action routing |
| `influencer-marketing` | searches `.agents/product-marketing.md` or legacy context files | bypasses repository Project Memory |
| `visual-system/` | reads project-scoped visual contracts, ranks registered Patterns, and preserves Human Review gates | only S30 mini and Lock Ultra Max have Visual Context/Profile; S30 Freeze is Candidate, not approved |
| automations | each README defines local status only | no project manifest read/write contract |

## 9. Duplicate or conflicting Sources of Truth

### P0

1. **Project Memory path mismatch.** The Skill expects a different repository layout and a missing `PROJECT_INDEX.md`.
2. **Project status has no explicit winner.** `STATUS.md`, `PROJECT.md`, execution-state JSON/YAML, and human decision files can disagree.
3. **Draft Product Truth shadows the governed layer.** Amazon/EDM/project artifacts can contain product-truth-like content but are outputs or candidates, not Product Knowledge authority.

### P1

1. Project directory IDs and Project Memory IDs differ for three projects.
2. Next Actions are duplicated between `PROJECT.md` and `TODO.md` and lack executable/approval metadata.
3. Decision storage is split between per-project files and an empty cross-project layer without routing rules.
4. `project.yaml` and the Visual Router's `project-context.yaml` can be confused by name unless their authority boundary is explicit. Only S30 mini currently has a Freeze file, and it is Candidate/inactive.
5. The repository contains placeholders such as `campaign-review`, `voc-analyzer`, and `kol-database` beside mature Skills, which can confuse routing.

### P2

1. Automation status is prose-only.
2. Product Memory is an interface statement without version pointers.
3. The workspace Skill catalog is currently an untracked local file, so it cannot serve as a GitHub Source of Truth in this PR.

## Migration boundary

This change adds navigation and compatibility only. It does not:

- move or rename existing projects, memories, or Skills;
- promote `Pending Verification`, draft, or untracked material;
- rewrite validated Amazon, EDM, campaign, or VOC workflows;
- update Product Knowledge facts or Project Memory business content;
- merge the branch or approve a gate.

## Remaining risks

- The four Manifests describe the latest checked-in state; their source `STATUS.md` files were last updated on 2026-08-20 and may be stale.
- S30 mini and Lock Ultra Max lack promoted Product Knowledge entities in the repository runtime.
- S30 mini and Lock Ultra Max have generated Visual Profiles that require Human Review; S30's Candidate Freeze is inactive, and Daily Station/homerunPET have no project visual contracts.
- Cross-project Decision Log and automation writeback still require real accepted decisions/runs before they can be exercised.
- Installed global Skills can drift from their GitHub copies; this PR only changes the repository versions.
- The checked-in `jp-commerce-*` and unified Campaign entries now have the shared preflight adapter. Dedicated media/PR runtime Skills remain outside this repository and require a later reviewed adapter migration.
