# Project Memory Governance

## Classification

| Class | Meaning | Automatic handling |
|---|---|---|
| FACT | Explicitly supported by an authoritative source | Store with source and freshness; do not convert planning material into fact. |
| DECISION | Accepted/final team decision | Add a dated decision record with source. |
| HYPOTHESIS | Plausible but unconfirmed | Keep out of Current Truth. |
| RECOMMENDATION | AI or marketing proposal | Keep separate from facts and decisions. |
| UNVERIFIED | Missing, ambiguous, or single-source content | Retain as an open question. |
| OUTDATED | Historically valid but superseded | Keep in changelog/decision history, not Current Truth. |

## Conflict order

Prefer only as a review recommendation: Final Official > Final Internal > Approved Meeting Decision > Draft > Discussion. Do not silently choose a winner. Record unresolved cases as `CONFLICT` in `memory_update_review.md` and the project's Open Questions.

## Major-change gate

Pricing, Product Definition, core specifications, compatibility, target user, positioning, launch date, PVT/MP, GTM stage, Key Message, channel strategy, major campaign result, and final decisions require a review record. Update metadata and changelog automatically, but replace Current Truth only after evidence is reviewed.
