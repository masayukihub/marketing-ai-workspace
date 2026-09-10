# Codex Context Resilience System

## Purpose and authority

This is internal Runtime/Workflow Infrastructure. It reduces preventable context growth and makes thread recovery file-based. It does not replace Project Manifest, Project Memory, Product Knowledge, Decision Log, or GitHub `main`.

Authority remains:

```text
GitHub main / Product Knowledge / Project Memory / accepted Decision
> Project Manifest navigation
> Thread Handoff
> Chat history or memory
```

A Handoff is a recovery pointer, never a Product Truth, Claim, price, date, Visual Freeze, approval, or publication authority.

## Operating contract

Use one thread for one Deliverable, Material Gate, or PR phase. Create a new thread when the project changes or an architecture task switches to business execution.

When context percentage is visible:

- 70% used: prepare a Handoff.
- 80% used: stop new broad reads and large outputs.
- 90% used: create the Handoff and move to a new thread.

When the percentage is unavailable, do not estimate it. Use boundary triggers and obvious large-output signals.

Automatic phase-ending triggers are PR creation/merge, Material Human Gate, project/phase switch, large source discovery completion, full regression completion, Compact request/failure, and SessionEnd.

## Commands

Health check:

```bash
python3 scripts/contextctl.py doctor
```

Create a manual Handoff:

```bash
python3 scripts/contextctl.py handoff \
  --project s30-mini \
  --task "Amazon EBC validation" \
  --next-action "Run mobile A+ raster QA"
```

An optional temporary YAML may add `goal`, `success_criteria`, `completed`, accepted/final Decision references, `generated_artifacts`, `tests`, `blockers`, `unresolved`, and `forbidden_changes`:

```bash
python3 scripts/contextctl.py handoff --project s30-mini --task "Amazon EBC validation" --input private-runtime/handoff-input.yaml
```

Resume in a new thread:

```bash
python3 scripts/contextctl.py resume --project s30-mini --latest
```

Capture a large command without flooding chat:

```bash
python3 scripts/contextctl.py capture --name full-regression -- bash tests/run_skill_tests.sh
```

Validate repository contracts:

```bash
python3 scripts/contextctl.py verify
```

## Lifecycle Hooks

`.codex/hooks.json` configures deterministic `PreCompact`, `PostCompact`, and `SessionEnd` command Hooks. Each invokes `scripts/codex_context_hook.py`, performs only local Git/file inspection, stores selected mechanical fields under `private-runtime/thread-handoffs/_automatic/`, and never stores the full Event Payload.

Hooks do not call a model, network, Feishu, or MCP; do not edit business files; do not commit; and return success even if checkpoint persistence fails. The 2-second command timeout prevents the Hook from delaying normal work.

Codex requires trust for new or changed project Hooks. A checked-in Hook is only **configured** until the client reviews its hash and marks it trusted. Use the Codex Hooks screen/command to review; never bypass trust. After trust, rerun `contextctl doctor` or the client hook inventory. A changed Hook hash requires review again.

## Status line and configuration

Project `.codex/config.toml` configures these supported Codex 0.153.4 TUI items:

- current model with reasoning;
- current Git branch;
- context-used percentage when available;
- thread ID.

Desktop surfaces may render status differently. The repository does not set `model_context_window` or auto-compact token values and preserves client defaults.

## Large-output boundary

`contextctl capture` streams combined stdout/stderr into a redacted ignored `*.context.log`, preserves the child exit code, supports timeout, and prints only status, key failures, and the log path. Never paste the resulting full log back into chat.

HTML, screenshots, full patches, raw source bodies, and browser traces use the same rule: persist privately, inspect locally, return a concise finding and path.

## Recovery after Compact failure

1. Do not repeatedly retry Compact.
2. Check `private-runtime/thread-handoffs/_automatic/` for the latest mechanical checkpoint.
3. Create or verify one manual Handoff for the current Deliverable.
   For a local failure simulation/checkpoint, run `python3 scripts/codex_context_hook.py --event compact-failed`; this is not registered as a Codex lifecycle event.
4. Start a new thread and paste only `contextctl resume` output.
5. Read `AGENTS.md`, Project Manifest, Handoff, and Git status in that order.
6. Continue only the one `next_action`; do not rescan the repository or repeat accepted decisions.

## Privacy and Git boundary

`private-runtime/`, `.codex-local/`, and `*.context.log` are ignored. Full logs, Handoffs, local config backups, Feishu source bodies, tokens, cookies, credentials, and event payloads must never enter Git.
