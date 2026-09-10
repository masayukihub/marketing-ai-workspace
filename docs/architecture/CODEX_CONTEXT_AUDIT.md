# Codex Context Root Cause Audit

## Executive conclusion

The observed failures are real local session events, not inferred from chat memory. A redacted scan of recent persisted sessions found **5 `context_window_exhausted` events and 2 `remote_compact_failure` events across 5 threads**. Four of those threads had rollout files above 5 MB; two historical threads reached 221 MB and 456 MB. Two recent failures contained a single record of about 15.4 MB. This supports a primary diagnosis of oversized thread history and tool/content records, compounded by multi-phase work and repeated context loading.

This repository cannot change the service-side context window or remote compaction implementation. It can prevent avoidable growth, persist state before boundaries, and make recovery independent from old chat history.

## Verified environment

| Item | Observed state | Interpretation |
|---|---|---|
| Codex CLI | 0.153.4 | Local CLI supports stable lifecycle Hooks. |
| Desktop | Installed and running; build 26.903.61454 | Primary interactive surface detected. |
| Model | `gpt-6-astra` from redacted `codex doctor` | No repository override is added. |
| Context usage | Not programmatically exposed to this non-interactive audit | Do not invent a percentage; use the configured status line and Operator thresholds. |
| Context overrides | No `model_context_window`, auto-compact limit/scope, or model catalog override | Preserve Codex defaults. |
| Hooks before this change | No user-level hooks file; project Hooks absent | Project-local Hooks can be added without global pollution, but require client trust review. |
| MCP | 3 configured, 1 disabled; exact tool count not exposed by `codex mcp list --json` | Keep connections; use task-specific enablement and avoid loading irrelevant schemas. |
| Skills | 13 repository directories, 12 global directories, 7 overlapping locked mirrors | Locked mirrors are currently exact; Repository remains execution authority. |
| Runtime | `RUNTIME_IN_SYNC` for all 7 locked Skills | No mirror repair was needed or performed. |
| Session store | 960 active rollout files, about 3.69 GB | Long-lived history is a material footprint risk. |

Configuration and session evidence are stored only as redacted summaries under `private-runtime/context-resilience/`. No credential values or full event payloads are committed.

## Event evidence

| Date | Error | Redacted thread | Rollout size | Largest record | Phase signal |
|---|---|---|---:|---:|---|
| 2026-09-10 | context window exhausted + 2 remote compact failures | `fd9e1129...` | 15.5 MB | 15.4 MB | Initial/attachment-heavy task; one record dominates. |
| 2026-09-10 | context window exhausted | `1893ddc0...` | 15.5 MB | 15.4 MB | Initial/attachment-heavy task; one record dominates. |
| 2026-09-10 | context window exhausted | `b64d9c49...` | 75 KB | 46 KB | Cause not proven from size alone; preserve as a non-large counterexample. |
| 2026-08-13 | context window exhausted | `c34c9cea...` | 456 MB | 15.4 MB | Very long implementation thread, 21,430 records. |
| 2026-06-27 | context window exhausted | `959a3d9e...` | 221 MB | 6.7 MB | Very long implementation thread, 12,494 records. |

The table records correlation, not a claim that file size alone caused every failure.

## Ranked root causes

1. **Long-lived, multi-phase threads.** Historical failure threads contain thousands of records and hundreds of megabytes of persisted history.
2. **Oversized single records and inline outputs.** Recent failures coincide with approximately 15.4 MB records; full HTML, attachments, MCP responses, logs, screenshots, and diffs can create this shape.
3. **Recovery tied to conversation history.** Without a file-backed Handoff, a new thread must re-read sources or rely on compacted history, repeating context cost and decisions.
4. **Repeated broad context loading.** Root instructions, Operator files, multiple complete Skills, Project Memory, Product Knowledge, and channel artifacts can be reloaded even when only a small task slice is needed.
5. **Duplicate runtime discovery surfaces.** Repository Skills and global mirrors are intentionally duplicated on disk. They are exact today, but both must not be treated as independent authorities or loaded together.
6. **Large tool-schema surface.** MCP/plugin schemas add fixed cost when enabled. The current CLI exposes server count but not a reliable total tool-schema size, so the exact contribution remains `UNVERIFIED`.
7. **Automatic IDE attachment.** Historical sessions are recorded as VS Code-originated and some failures have attachment-sized records. The exact IDE attachment policy is not exposed by the current diagnostic API, so this is a risk signal, not a proven cause.

## Configuration decision

- Keep Codex model/context/compaction defaults. No unsupported numeric override is written.
- Configure a project-local TUI status line for model, branch, context-used percentage, and thread ID.
- Add only project-local deterministic Hooks for PreCompact, PostCompact, and SessionEnd.
- Do not remove MCP connections or user Skills. Recommend task-scoped enablement instead.

## Remediation map

| Risk | Control |
|---|---|
| Long thread | One Deliverable/Gate/PR phase per thread; required Handoff at boundaries. |
| Compact failure | Mechanical PreCompact checkpoint plus file-backed manual Handoff; no repeated compact retry. |
| Large output | `contextctl capture` writes redacted full output to ignored storage and prints at most 40 lines. |
| Re-scan on resume | `contextctl resume` emits a pointer-only prompt with one Next Action and at most 12 reads. |
| Runtime duplication | Existing Skill Lock and one-way mirror verifier remain authoritative. |
| Secret leakage | Redaction before log/Handoff persistence plus repository secret scan. |
| Untrusted Hooks | Do not claim activation until Codex shows the project Hook hash as trusted. |
