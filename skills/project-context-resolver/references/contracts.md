# Resolver contracts

Read these repository-level contracts when changing resolver behavior or connecting another Skill:

- Project Manifest schema: `../../../schemas/project-manifest.schema.yaml`
- Context Package schema: `../../../schemas/project-context-package.schema.yaml`
- Architecture, task-source matrix, state mapping, and writeback: `../../../docs/architecture/PROJECT_CONTEXT_SYSTEM.md`
- Current-system audit: `../../../PROJECT_SYSTEM_AUDIT.md`

The Manifest is the current navigation/status contract. It does not replace the source files it points to.

`manifest_updated_at` is infrastructure metadata. `state_as_of`, `freshness_status`, and `freshness_sources` describe the verified state basis. The resolver recalculates effective freshness using `config/freshness.yaml`; a recent Manifest edit cannot make old state current.

Unknown project names return the non-mutating `PROJECT_BOOTSTRAP_REQUIRED` result. Only `project-memory-manager` discovery review may follow; no project directory, Product Knowledge record, or execution Skill is created or invoked.

An accepted Human Decision may appear under `approved_decisions`, but it does not itself update a gate. If the decision is intended to change formal execution state, `latest_decision` also declares `target_gate` and `expected_status`. The resolver reports a conflict only when accepted decision evidence exists and the checked-in Manifest differs; unrelated accepted decisions do not imply overall approval.
