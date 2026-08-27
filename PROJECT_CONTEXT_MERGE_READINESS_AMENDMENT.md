# Project Context Merge Readiness Amendment

- Date: 2026-08-27
- Branch: `feature/project-context-resolver`
- Pull Request: `#6`
- Scope: minimum runtime-readiness amendment only
- Explicit exclusions: no PR merge, no Feishu scan, no Project Memory body refresh, no business Product Truth/Claim/Decision/Visual Freeze/project-approval change

## Executive result

The four identified runtime risks are addressed without creating a new business project or promoting any business state. The checked-in repository Skill is now the formal Project Memory runtime; project state freshness is independent from Manifest edit time; task routing is token-aware; and unknown projects return a safe discovery-review route instead of a generic error or automatic creation.

## 1. Repository / Global Skill Drift

- Formal command: `python3 skills/project-memory-manager/scripts/project_memory.py --workspace .`
- `$HOME/.codex/skills/project-memory-manager/` is an installation mirror only.
- `verify_global_mirror.py` compares SHA-256 for `SKILL.md`, UI metadata, governance, integration, and `project_memory.py`.
- Any missing or mismatched runtime file returns `GLOBAL_SKILL_DRIFT`, keeps `execution_source: repository`, and sets `global_auto_use: false`.

Actual check on 2026-08-27: **GLOBAL_SKILL_DRIFT**. The installed global script itself matched, but the global `SKILL.md` and integration contract did not match the repository. The global copy was not executed or updated.

## 2. Project State Freshness

The Manifest remains version `1.0` and retains `last_updated` for compatibility. It now also records:

- `manifest_updated_at`: navigation-file maintenance time;
- `state_as_of`: date of actual project-state verification;
- `freshness_status`: `current`, `stale`, or `unknown`;
- `freshness_sources`: real state-source paths.

The active-project threshold is 7 days. All four Manifests preserve their business state at `state_as_of: 2026-08-20`; the 2026-08-27 Manifest amendment does not change that date. Evaluated on 2026-08-27 they are exactly 7 days old and remain `current`; from 2026-08-28 they evaluate as `stale` unless the state sources are reviewed.

For `stale` or `unknown` state:

- allowed: `read_only_audit`, `source_refresh`, `human_review_preparation`;
- blocked: `state_dependent_execution`;
- warning: `PROJECT_STATE_STALE` or `PROJECT_STATE_UNKNOWN`.

## 3. Token-aware Task Routing

ASCII task patterns now use alphanumeric boundaries and separator-aware phrase matching. Short tokens such as `PR` and `LP` no longer match inside `project`, `product`, or `help`. CJK task phrases retain direct phrase matching.

Verified routes:

| Input | Task type |
| --- | --- |
| `继续 S30 mini project` | GTM, not PR |
| `S30 mini product page` | GTM, not PR |
| `help with S30 mini` | GTM, not Website |
| `继续 S30 mini PR` | PR |
| `S30 mini PR TIMES 新闻稿` | PR |
| `继续 S30 mini Amazon` | Amazon |
| `继续 S30 mini Review` / `customer review` | Review / VOC |

## 4. Unknown Project Bootstrap

`继续 AI MindClip` returns:

```yaml
resolution_status: PROJECT_BOOTSTRAP_REQUIRED
recommended_skill: project-memory-manager
auto_create: false
allowed_action: prepare_project_discovery_review
```

The route contains no execution-Skill list. Tests confirm that it does not create `projects/ai-mindclip/`, alter the checked-in project list, or change Product Knowledge.

## 5. S20 mini Routing Alias

`S20 mini`, `SwitchBot S20 mini`, and `s20-mini` route to project `s30-mini`. The returned package emits `PROJECT_ROUTING_ALIAS_ONLY` and states that the mapping does not approve an external product name. Product Truth, approved Claims, decisions, and visual approval files are unchanged. No additional Lock Ultra alias was added.

## 6. Actual Context Package Review

All five packages were generated through the real CLI with `--as-of 2026-08-27`; no output was written into a project directory.

| Input | Resolution | Freshness | Task / next route | Safety result |
| --- | --- | --- | --- | --- |
| `继续 S30 mini` | `s30-mini` | current, age 7 | GTM → `S30-P0-SOURCE-AUDIT` | read-only audit; Product Truth remains blocked |
| `继续 S20 mini Amazon` | `s30-mini` via routing alias | current, age 7 | Amazon → `jp-commerce-content-flow` | alias-only warning; Product Truth/Claims/assets remain missing |
| `继续 Lock Ultra Max` | `lock-ultra-max` | current, age 7 | GTM → `LUM-P0-NAMING-AUDIT` | read-only audit; no S30 context |
| `S30 mini product page` | `s30-mini` | current, age 7 | GTM, not PR | no short-token false match |
| `继续 AI MindClip` | bootstrap required | not applicable | Project Memory discovery review only | no auto-create or execution Skill |

## 7. Tests added

- Repository runtime is the default Project Memory command.
- Matching mirror returns `GLOBAL_SKILL_IN_SYNC`.
- Hash mismatch or missing mirror returns `GLOBAL_SKILL_DRIFT` without fallback.
- Active state becomes stale after the configured threshold.
- Stale read-only audit remains permitted.
- Unknown freshness blocks state-dependent execution.
- Required PR/LP boundary cases.
- S20 alias routes only to S30 project identity.
- Unknown project bootstrap is non-mutating.
- Existing S30/Lock isolation, Amazon scoping, Review/VOC distinction, Human Review, and decision-conflict tests remain active.

## 8. Validation

- Manifest validation: 4/4 passed
- Resolver tests: 15 passed
- Project Memory Manager tests: 4 passed
- Full Skill regression: 116 pytest cases passed; Amazon/EDM regressions and Ruby syntax passed
- Visual System regression: 9 unittest cases passed
- Workspace validation: structure, memory, links, secrets, and large-files passed
- Skill validation: resolver and Project Memory Manager passed
- GitHub Actions: authoritative result is the PR #6 check suite for this amendment commit

The full run emitted 14 existing matplotlib/pyparsing deprecation warnings and no failures.

## Remaining risks

- The four active project states become stale on 2026-08-28 unless their existing state sources are reviewed; this amendment intentionally does not refresh them.
- The installed global Project Memory Manager is currently drifted and should not be used until explicitly synchronized through a separate installation action.
- AI MindClip remains a Product Knowledge entity without a project Manifest; discovery review is the only permitted next route.
- S30 Product Truth/approved Claims/assets remain missing, and its Visual Freeze remains Candidate/inactive.
- Lock Ultra Max Product Truth/approved Claims remain missing, and no Visual Freeze exists.
