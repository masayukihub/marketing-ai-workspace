# Resolver contracts

Read these repository-level contracts when changing resolver behavior or connecting another Skill:

- Project Manifest schema: `../../../schemas/project-manifest.schema.yaml`
- Context Package schema: `../../../schemas/project-context-package.schema.yaml`
- Architecture, task-source matrix, state mapping, and writeback: `../../../docs/architecture/PROJECT_CONTEXT_SYSTEM.md`
- Current-system audit: `../../../PROJECT_SYSTEM_AUDIT.md`

The Manifest is the current navigation/status contract. It does not replace the source files it points to.

An accepted Human Decision may appear under `approved_decisions`, but it does not itself update a gate. If the decision is intended to change formal execution state, `latest_decision` also declares `target_gate` and `expected_status`. The resolver reports a conflict only when accepted decision evidence exists and the checked-in Manifest differs; unrelated accepted decisions do not imply overall approval.
