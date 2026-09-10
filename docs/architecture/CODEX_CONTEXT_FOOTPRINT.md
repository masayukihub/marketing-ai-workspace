# Codex Context Footprint

Sizes below are repository bytes unless marked estimated or unavailable. Bytes are a useful pressure indicator, not a token count; encoding, tool schemas, images, and model serialization change the final token footprint.

| Context Source | Size | Always Loaded | Task-specific | Risk | Action |
|---|---:|---|---|---|---|
| Root `AGENTS.md` | 9.3 KB before this amendment | Yes | No | Medium | Keep Context Resilience addition short; detailed rules live in architecture docs. |
| Nested `AGENTS.md` | 0 found | No | No | Low | Do not create nested duplicates without a scoped need. |
| `operator/` | 30.3 KB / 4 files | No | Project preflight | Medium | Read routing/review sections once; do not paste them into Handoffs. |
| ChatGPT Project Instructions | 6.5 KB | ChatGPT only | Project | Low | Keep as routing contract, not project truth. |
| Skill names/descriptions | Metadata size unavailable; 12 global Skill directories | Client-dependent | Yes | Medium | Preserve four user entries and route internal Skills lazily. |
| All repository `SKILL.md` files | 118.8 KB / 12 files | No | Yes | High if bulk loaded | Read only selected Skill and required references. |
| MCP tool schemas | Exact bytes/tools unavailable; 3 servers configured | Client-dependent | Yes | High/Unverified | Do not remove connections; enable only task-relevant MCPs and avoid verbose inventory in chat. |
| Memory/Chronicle injection | Enabled; exact size unavailable | Client-dependent | Yes | Medium/Unverified | GitHub files override memory; avoid re-injecting old narrative. |
| IDE automatic context | Configuration not exposed by CLI | Client-dependent | Yes | High/Unverified | Attach only files needed for the current Deliverable; do not attach directories or large generated files. |
| One Project Manifest | 2.5–5.4 KB | No | Yes | Low | Always resolve first, then follow only available source pointers. |
| All 4 Manifests | 13.6 KB | No | No | Medium if repeated | Never load all projects for a single-project task. |
| All Project Memory Markdown | 54.4 KB / 28 files | No | Yes | High if bulk loaded | Read only manifest-selected project/task files once. |
| Product Knowledge Markdown | 95.1 KB / 53 files | No | Yes | High if bulk loaded | Query the minimum unit; canonical verification only when needed. |
| Decision files | Included in Project Memory | No | Yes | Medium | Store only accepted Decision ID/source in Handoff. |
| Feishu body | Variable; potentially very large | No | Yes | Critical | Persist source snapshots privately; chat receives metadata/delta summaries only. |
| HTML | 166.6 KB / 24 files in current tree | No | Yes | High | Review via file/browser; return path and findings, never full HTML. |
| Images | Binary/multimodal size varies | No | Yes | High | Inspect only the required frames/assets and avoid repeated attachment. |
| Git Diff | Unbounded | No | Yes | High | Inline maximum 80 lines; write full patch/log to private runtime. |
| Test logs | Unbounded | No | Yes | Critical | Always use `contextctl capture` for full regressions; inline maximum 40 lines. |
| Browser/Playwright output | Unbounded | No | Yes | High | Save screenshots/reports to artifacts; summarize only failures. |
| Failed historical rollouts | 75 KB–456 MB | No | Historical | Critical | Never use old rollout as recovery source; use Handoff instead. |

## Minimum-load rule

```text
AGENTS.md
→ Project Manifest (if named project)
→ Latest Handoff
→ git status
→ only task-scoped formal Sources
→ one execution Skill
```

The CLI cannot programmatically read the active Desktop thread's remaining-context percentage. The 70/80/90 thresholds in `runtime/context-policy.yaml` are therefore Operator rules driven by the client status line; unknown remains unknown.
