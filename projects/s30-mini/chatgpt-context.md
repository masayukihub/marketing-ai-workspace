---
snapshot_contract: chatgpt-project-context-v1
snapshot_authority: generated_read_only_not_truth_source
project_id: s30-mini
current_main_commit: 2d2bea6dad5c937310b4f800b0a9cf2dd9ad9882
generated_as_of: '2026-08-28'
state_as_of: '2026-08-20'
effective_freshness_status: stale
lifecycle_stage: validation
accepted_decisions:
- decision_id: S30-VISUAL-PLANNING-20260827
  summary: Project Visual DNA, EDM intent, Recipe core, and conditional module policy
    are approved for S30 project planning only.
  source: reviews/visual-pattern-recipe-20260827/decision-record.yaml
blockers:
- blocker_id: S30-PRODUCT-TRUTH
  summary: Approved Product Truth, approved JP Claims, and their authoritative sources
    remain unconfirmed or not formally written back.
  status: blocked
  source: ../../memory/project-memory/s30-mini/STATUS.md
- blocker_id: S30-COMMERCIAL
  summary: Japan official product name, SKU, MSRP / Deal Price, Launch Build, and
    Launch Timeline still contain unresolved items.
  status: blocked
  source: ../../memory/project-memory/s30-mini/TODO.md
- blocker_id: S30-CONTENT-CLAIM-ASSET-UNLOCK
  summary: EDM Content, approved Claims, official Assets, CTA, and Legal / Footer
    inputs must be unlocked before entry into the Existing EDM Runtime.
  status: blocked
  source: reviews/visual-pattern-recipe-20260827/asset-gap-register.yaml
next_actions:
- priority: p0
  action_id: S30-P0-SOURCE-AUDIT
  action: Determine the authoritative Product Truth and JP Claim approval sources
    before downstream execution.
  status: not_started
  requires_human_approval: false
  blocked_by: []
  source: ../../memory/project-memory/s30-mini/STATUS.md
- priority: p0
  action_id: S30-P0-COMMERCIAL-REVIEW
  action: Confirm Japan official product name, SKU, MSRP / Deal Price, Launch Build,
    and Launch Timeline from authoritative sources.
  status: not_started
  requires_human_approval: true
  blocked_by: []
  source: ../../memory/project-memory/s30-mini/TODO.md
- priority: p0
  action_id: S30-CONTENT-CLAIM-ASSET-UNLOCK
  action: Resolve S30_CONTENT_CLAIM_ASSET_UNLOCK as one governed handoff before Existing
    EDM Runtime.
  status: not_started
  requires_human_approval: true
  blocked_by:
  - S30-PRODUCT-TRUTH
  - S30-COMMERCIAL
  source: reviews/visual-pattern-recipe-20260827/asset-gap-register.yaml
- priority: p1
  action_id: S30-P1-MIGRATION-SCOPE
  action: Select project documents that can be migrated without copying production
    assets.
  status: not_started
  requires_human_approval: false
  blocked_by: []
  source: ../../memory/project-memory/s30-mini/TODO.md
required_github_source_paths:
- memory/project-memory/s30-mini/DECISIONS.md
- memory/project-memory/s30-mini/PROJECT.md
- memory/project-memory/s30-mini/STATUS.md
- memory/project-memory/s30-mini/TODO.md
- projects/s30-mini/project-context.yaml
- projects/s30-mini/project.yaml
- projects/s30-mini/reviews/visual-pattern-recipe-20260827/asset-gap-register.yaml
- projects/s30-mini/reviews/visual-pattern-recipe-20260827/decision-record.yaml
- projects/s30-mini/visual-freeze.yaml
- projects/s30-mini/visual-profile.yaml
---
