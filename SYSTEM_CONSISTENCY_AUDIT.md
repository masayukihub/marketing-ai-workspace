# Marketing AI Workspace System Consistency Audit

- Baseline GitHub `main`: `2d2bea6dad5c937310b4f800b0a9cf2dd9ad9882`
- Audit date: `2026-08-28`
- Runtime authority: GitHub repository
- Global mirror policy: one-way installation mirror; never a writeback source
- Business-state boundary: no Product Truth, Approved Claim, price, launch fact, Visual Freeze, or business approval was changed by this hardening audit

## Executive findings

1. Repository Skill ownership was stated in `AGENTS.md`, but runtime verification covered only Project Memory Manager. There was no repository-wide Skill Lock.
2. All seven required Global Skill Mirrors currently differ from the repository. The safe runtime remains the repository; Global auto-use is disabled.
3. `scripts/build_skill_inventory.py` hard-coded local machine paths and could not reproduce the committed Inventory. The CSV also mixed repository Skills with source-missing local interfaces.
4. Four Chinese user-entry Skills have repository source. `project-context-resolver`, `project-memory-manager`, and `product-knowledge` are internal governance/runtime components.
5. ChatGPT had no versioned bootstrap or snapshot contract. Historical chat or memory could therefore be mistaken for current project state.
6. All four active Manifests recorded a static `freshness_status: current` even though their `state_as_of` became stale on `2026-08-28` under the seven-day threshold.
7. The merged S30 Manifest represented the EDM unlock Gate as the only project blocker. Product Truth and Commercial blockers were missing from the project-wide state.

## Locked Runtime matrix

| Repository Skill | Repository Tree Hash | Global Skill Path | Global Tree Hash | Sync Status | User-visible / Internal | Runtime Authority | Recommended Action |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `project-context-resolver` | `7bd37bf916ffd8cb00ec9785a95e57925039f61e660642708af51e050782d448` | `$CODEX_HOME/skills/project-context-resolver` | `8c09439e00b048ccccd7b0e832f3cc0a51bd679c03890a106fe4550f89df5442` | `RUNTIME_DRIFT` | Internal | repository | Merge, update clean `main`, then sync mirror from repository |
| `project-memory-manager` | `4ac381d12fb1c1fb9a5c96dd5c3fdab0d8a7e34e76cf5de35428a3041e8471f7` | `$CODEX_HOME/skills/project-memory-manager` | `b31abb7fd319a98a3a7d6660c1077562b4ad4eef548b7d63862a0cfde17ec052` | `RUNTIME_DRIFT` | Internal | repository | Merge, update clean `main`, then sync mirror from repository |
| `product-knowledge` | `26470a010d1d8157f5cefcab99c30d9bbf4b116eec20b2b60a006695335e50ac` | `$CODEX_HOME/skills/product-knowledge` | `a61413080fffa83dbc27ec1c83d68b67602ab7c81c35e20ef186f66a9abc4bd6` | `RUNTIME_DRIFT` | Internal | repository | Merge, update clean `main`, then sync mirror from repository |
| `jp-commerce-insights` | `1abddc920858c12d08e56d8c7af1f39f686a6e3c36c3c76f997105134e1f9e1e` | `$CODEX_HOME/skills/jp-commerce-insights` | `85f1830ef119765f099306fe0651c0e4138396083194793e54cc81836eb55f22` | `RUNTIME_DRIFT` | User-visible | repository | Merge, update clean `main`, then sync mirror from repository |
| `jp-commerce-content-flow` | `1fa786441a63323b0eaa40771c0ee9042c921603fc776e5163c6e9f06173c36c` | `$CODEX_HOME/skills/jp-commerce-content-flow` | `e7b0d7f9ba40faee0af906b356e2448abed6e9a22371c8ed5192f552318a219d` | `RUNTIME_DRIFT` | User-visible | repository | Merge, update clean `main`, then sync mirror from repository |
| `switchbot-japan-campaign` | `c964c1e261b12b3607cc1f87b9d5e1806b380ee47f1183bfbf77f4096f181f03` | `$CODEX_HOME/skills/switchbot-japan-campaign` | `a259761c414deb37bb57c7c00bdaedcdede0ece99078509bf266773fd0ceda3c` | `RUNTIME_DRIFT` | User-visible | repository | Merge, update clean `main`, then sync mirror from repository |
| `switchbot-japan-edm` | `ce88ec906e46f22cac8b7e219d7abd9a8d4259b8a77db11d7a920ba8ec73454b` | `$CODEX_HOME/skills/switchbot-japan-edm` | `de14c4ad6d4a2b60a1241704f90a7a006dbe53570d2d3096eabfb0951fc82090` | `RUNTIME_DRIFT` | User-visible | repository | Replace legacy/extra mirror files only after clean-main dry run |

`scripts/verify_codex_runtime.py --repository-only` returns `RUNTIME_IN_SYNC`; the full repository-to-mirror check returns `RUNTIME_DRIFT`. No global mirror was used or modified in this branch.

## Three-end consistency matrix

| Layer | Before hardening | Authority after hardening | Verification / regeneration |
| --- | --- | --- | --- |
| GitHub `main` Skills | Repository stated as primary; no universal lock | Formal runtime authority | `runtime/skill-lock.json` + repository-only verifier |
| Codex Repository Runtime | Skill-specific checks; PMM-only mirror logic | Executes directly from repository | `scripts/verify_codex_runtime.py --repository-only` |
| Codex Global Skill Mirror | Installation state could drift independently | Non-authoritative mirror; auto-use false | Full verifier, then clean-main one-way sync |
| ChatGPT Project Context | No versioned bootstrap or snapshot contract | Read-only cache below GitHub sources | `chatgpt/PROJECT_INSTRUCTIONS.md` + generated project snapshots |

## Inventory and user entry audit

- The former generator referenced machine-specific directories and local/private interfaces. Its output was not the source of the committed CSV.
- The new Inventory discovers only repository directories with `SKILL.md`, reads `runtime/skill-lock.json`, and writes symbolic `$CODEX_HOME` paths.
- Formal repository Skill records change from 21 mixed records to 12 source-backed repository Skills.
- Source-missing entries such as local-installed interfaces and private KOL data are no longer represented as formal Skills.
- The four user-visible entries remain:
  - `jp-commerce-insights`
  - `jp-commerce-content-flow`
  - `switchbot-japan-campaign`
  - `switchbot-japan-edm`
- `docs/SKILL_CATALOG.md` is generated by the Inventory builder and explicitly rejects hand maintenance.

## Product Knowledge and Project Manifest audit

- Product Knowledge remains the product-fact and Claim gate. Runtime hardening does not change its canonical facts, Claims, price, launch information, or approval state.
- Active projects: `daily-station`, `homerunpet`, `lock-ultra-max`, and `s30-mini`.
- Each active Manifest now uses `freshness_status_at_manifest_update`; only the Resolver emits `effective_freshness_status`.
- On `2026-08-27`, `state_as_of: 2026-08-20` is current at the seven-day threshold. On `2026-08-28`, it is stale.
- S30 project-level blockers are restored as three coexisting records:
  - `S30-PRODUCT-TRUTH`
  - `S30-COMMERCIAL`
  - `S30-CONTENT-CLAIM-ASSET-UNLOCK` (EDM channel scope)
- The accepted S30 Visual Planning Decision remains approved. Product Truth, Claims, Commercial facts, assets, final layout, Visual Freeze, production, send, and publication remain unapproved.

## ChatGPT Bridge audit

- `chatgpt/PROJECT_INSTRUCTIONS.md` requires latest-main verification before named-project, Skill, “继续”, or “下一步” work.
- Four generated `chatgpt-context.md` files expose only status, accepted decisions, blockers, next actions, freshness, and GitHub source paths.
- Snapshots are marked `generated_read_only_not_truth_source` and are pinned to the main commit current at generation.
- If GitHub cannot be accessed, the required result is `GITHUB_CONTEXT_UNVERIFIED`.
- Conversation approvals do not become Formal State until written to the governed source and merged into GitHub `main`.

## Draft PR #1 cleanup recommendation

Draft PR #1 is still open and its last checks passed, but it predates the Project Manifest/Resolver runtime and introduces a separate root `skills-lock.json` plus overlapping CI changes.

Recommendation: **extract reusable work, then mark the original Draft as superseded and close only after Human Review**.

- Reusable: Product Onboarding contracts, source snapshot schema, anti-spoofing/fail-closed adapters, and isolated tests.
- Must not be merged as-is: root `skills-lock.json`, outdated workflow edits, or any runtime path that bypasses `project-context-resolver`, Product Knowledge review, and the current S30 Manifest.
- Compatibility: the PR's “review only / zero approved external Claims / no canonical writeback” boundary is compatible with the current S30 Project Memory flow. Its integration architecture is not yet compatible with the new Skill Lock, Freshness, Context Package, and writeback routing.
- `rebase` alone is not recommended because it would preserve obsolete competing runtime contracts. Extract the reusable flow into a new reviewed branch after this hardening PR lands.

PR #1 was not modified or closed by this audit.
