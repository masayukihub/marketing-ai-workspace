---
snapshot_contract: chatgpt-project-context-v1
snapshot_authority: generated_read_only_not_truth_source
project_id: lock-ultra-max
current_main_commit: 2d2bea6dad5c937310b4f800b0a9cf2dd9ad9882
generated_as_of: '2026-08-28'
state_as_of: '2026-08-20'
effective_freshness_status: stale
lifecycle_stage: discovery
accepted_decisions: []
blockers:
- blocker_id: LUM-PRODUCT-DEFINITION
  summary: Japan naming and Product Definition remain Pending Verification.
  status: blocked
  source: ../../memory/project-memory/lock-ultra-max-jp/STATUS.md
- blocker_id: LUM-LAUNCH-STATUS
  summary: Claim and launch status remain Pending Verification.
  status: blocked
  source: ../../memory/project-memory/lock-ultra-max-jp/STATUS.md
next_actions:
- priority: p0
  action_id: LUM-P0-NAMING-AUDIT
  action: Review canonical sources for the Japan official name and Product Definition.
  status: not_started
  requires_human_approval: false
  blocked_by: []
  source: ../../memory/project-memory/lock-ultra-max-jp/TODO.md
- priority: p0
  action_id: LUM-P0-CONFLICT-REVIEW
  action: Resolve Product Knowledge conflicts through the human review process.
  status: not_started
  requires_human_approval: true
  blocked_by: []
  source: ../../memory/project-memory/lock-ultra-max-jp/TODO.md
- priority: p1
  action_id: LUM-P1-GTM-GATE
  action: Confirm the current GTM and Amazon production gate.
  status: not_started
  requires_human_approval: true
  blocked_by: []
  source: ../../memory/project-memory/lock-ultra-max-jp/TODO.md
required_github_source_paths:
- memory/project-memory/lock-ultra-max-jp/DECISIONS.md
- memory/project-memory/lock-ultra-max-jp/PROJECT.md
- memory/project-memory/lock-ultra-max-jp/STATUS.md
- memory/project-memory/lock-ultra-max-jp/TODO.md
- projects/lock-ultra-max/project-context.yaml
- projects/lock-ultra-max/project.yaml
- projects/lock-ultra-max/visual-profile.yaml
---
