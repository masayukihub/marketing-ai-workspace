# Phase 5 Renderer Pilot Issue Log

Updated: 2026-08-19  
Scope: four Pilot cases only. Frozen Design Standard v1.0, Design System v1.0 and Generator Logic v1.0 were not modified.

| Issue ID | Pilot | Severity | Domain | Evidence | Required resolution | Owner / source | Current effect |
|---|---|---:|---|---|---|---|---|
| ISSUE-P5-001 | P01 | BLOCKING | Product Knowledge / Asset / Campaign | S30 mini formal identity, approved publishable claims, official main product asset, period and CTA destination are unresolved. S20 assets are explicitly not reusable. | Confirm final Japanese identity and publishable claims; register approved S30 mini assets; provide campaign period and live CTA URL; rerun Truth Gate. | Product Knowledge + Product Marketing + Asset owner | `BLOCKED`; wireframe only; no Final HTML. |
| ISSUE-P5-002 | P03 | BLOCKING | Campaign Truth | Recovered SBG_006 is an ended 2026 Prime Day email; original tracking URLs were removed and current price/inventory were not reverified. | Provide a current campaign brief, current offer/price evidence, current period and live CTA destinations, or keep strictly as historical evidence. | Campaign owner + EC owner | `BLOCKED`; historical screenshot only; cannot be republished. |
| ISSUE-P5-003 | P02 | PUBLISH BLOCKER | Product Knowledge / Design-System input | Frozen conversion sequence calls for proof/comparison confidence, but no approved Review Proof, warranty or service proof was available. Renderer omitted it instead of fabricating evidence. | Register an approved proof source or explicitly approve a proof-free variant for this campaign. | Product Knowledge + CRM / Service owner | Internal `CONDITIONAL` render is valid; external delivery remains blocked. |
| ISSUE-P5-004 | P02, P04 | PUBLISH BLOCKER | Asset / Legal / CRM | Production legal/footer asset and approved delivery-management wording are not registered. Current footer is an internal non-production boundary. | Supply approved production footer, legal/company text, unsubscribe and delivery-management requirements. | CRM Operations + Legal + Brand | Preview may be reviewed; Final Publish is blocked. |
| ISSUE-P5-005 | P02, P04 | PUBLISH BLOCKER | Copy Localization / Product Knowledge | Several renderer-localized Japanese support lines remain `UNVERIFIED`; campaign audience is also `UNVERIFIED`. | Human Japanese copy approval plus source/claim readback; confirm campaign audience before Final. | Japan Marketing + Product Knowledge | Copy is suitable for internal visual review, not final delivery. |
| ISSUE-P5-006 | P02, P04 | ITERATION 2 | Renderer | Current output is editable responsive HTML, not yet a production email-client compatibility build with table fallback, CSS inlining, dark-mode/client matrix and ESP validation. | Add email-safe compilation and client QA after visual direction is approved. | Renderer | Not a Pilot hard-rule failure; blocks direct ESP handoff. |
| ISSUE-P5-007 | P02, P04 | HUMAN REVIEW | Visual / Renderer | P02 has excessive empty black space in the official lifestyle image and small embedded detail text; P04 product scale is modest and message repeats inside an official image. Both cases have limited proof depth. | Use Human Review to decide crop/module/rhythm revisions; do not alter official product pixels or redraw UI. | Japan Marketing + Design + Renderer | Determines Iteration 2 priorities and Deliverable status. |

## Ownership boundary

- **Renderer-owned:** layout rhythm, crop container, responsive behavior, CTA rendering, email-client compilation and visual refinements that do not alter official product/UI pixels.
- **Asset / Product Knowledge-owned:** approved product identity, claims, prices, campaign period, CTA destination, product/lifestyle/detail/UI assets, proof, disclaimers and legal footer.
- Renderer must not compensate for truth gaps by inventing claims, prices, product pixels, UI or promotion facts.
