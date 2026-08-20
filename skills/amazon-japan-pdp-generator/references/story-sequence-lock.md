# Story Sequence Lock

## Lock point

When Story Gate becomes Approved, persist a deterministic fingerprint of:

- ordered Gallery IDs;
- ordered A+ Module IDs;
- ordered Unit IDs inside each Module.

The fingerprint is stored in the Spec and mirrored in `PROJECT_STATE.json`. DESIGN and PRODUCE compare the state fingerprint, Spec fingerprint and recomputed sequence fingerprint. Removing or rewriting the Spec lock cannot cause a silent re-sign; it fails closed.

## Allowed after approval

- add Reference annotations and provenance;
- map an approved record to an available Primitive;
- enrich explanation, adaptation and “not copied” trace;
- update non-structural layout metadata without changing the approved sequence.

## Forbidden after approval

- reorder Gallery, A+ Modules or Units;
- insert or delete any of them;
- merge or split Modules/Units;
- silently apply a new Reference structure.

DESIGN and PRODUCE recompute the fingerprint and fail closed on any mismatch.

## Required reset path

To change structure:

1. explicitly reset Story Gate to pending;
2. clear the sequence lock;
3. rerun PLAN/Reference Adapter;
4. regenerate Story Review;
5. obtain a new Story Approval and lock;
6. rerun DESIGN and Layout Approval.

`--force` and `internal-test` do not bypass fingerprint integrity. Legacy projects without lock fields may continue in Reference OFF fallback until the next approved PLAN creates the lock.
