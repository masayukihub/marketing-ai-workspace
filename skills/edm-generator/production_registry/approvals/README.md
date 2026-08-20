# Approval audit

- `pending_approvals.yaml` is the current human queue definition.
- `approval_ledger.jsonl` is append-only and is created by the write-back script on the first applied decision.
- `history/` receives a before/after YAML snapshot for every applied decision.
- An approval row is ignored if its `approval_id + decision + reviewer + decision_at` audit key already exists.
- `Modify` updates the proposed value only when a target has a `value_path`; its status becomes `DRAFT` and requires a later approval.
- `Needs Evidence` writes `UNVERIFIED`; `Reject` writes `REJECTED`.

