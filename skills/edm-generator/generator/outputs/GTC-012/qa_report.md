# GTC-012 QA Report

- Automated Test: **PASS**
- Design Spec QA: **BLOCKED_FOR_PRODUCTION**
- Production: **BLOCKED**
- Template Match: **PASS**
- Determinism: **PASS**
- Fake Claims / Prices / Deadlines: **0 / 0 / 0**
- Unsafe Generator Hard-rule Violations: **0**

## Production Blocking Conditions

- `PRODUCT_KNOWLEDGE_NOT_EXTERNAL_READY`
- `APPROVED_CLAIM_REQUIRED`
- `TEST_FIXTURE_NOT_PRODUCTION_ASSET`
- `CTA_FIXTURE_NOT_PRODUCTION_URL`

## Hard Rules

- [x] `R-BRAND-001` — PASS: Validated at Generator design-spec stage; Renderer-specific evidence remains out of scope.
- [x] `R-WEIGHT-001` — PASS: Validated at Generator design-spec stage; Renderer-specific evidence remains out of scope.
- [x] `R-PRODUCT-001` — PASS: Test fixture used only for logic; real provenance remains a production gate.
- [x] `R-ASSET-001` — PASS: Test fixture used only for logic; real provenance remains a production gate.
- [x] `R-ASSET-002` — PASS: Validated at Generator design-spec stage; Renderer-specific evidence remains out of scope.
- [x] `R-AI-001` — PASS: No AI product or UI redraw is requested.
- [x] `R-AI-002` — PASS: No AI product or UI redraw is requested.
- [x] `R-CLAIM-001` — PASS: Unapproved claims, prices, and dates are omitted and retained as verification states.
- [x] `R-CLAIM-002` — PASS: Validated at Generator design-spec stage; Renderer-specific evidence remains out of scope.
- [x] `R-CTA-001` — PASS: Validated at Generator design-spec stage; Renderer-specific evidence remains out of scope.
- [x] `R-CTA-004` — PASS: CTA intent resolved; fixture is not a final URL.
- [x] `R-MODULE-001` — PASS: Validated at Generator design-spec stage; Renderer-specific evidence remains out of scope.
- [x] `R-PROMO-002` — PASS: Validated at Generator design-spec stage; Renderer-specific evidence remains out of scope.
- [x] `R-COPY-002` — PASS: Unapproved claims, prices, and dates are omitted and retained as verification states.
- [x] `R-DESKTOP-001` — PASS: Validated at Generator design-spec stage; Renderer-specific evidence remains out of scope.
- [x] `R-EVIDENCE-001` — PASS: Validated at Generator design-spec stage; Renderer-specific evidence remains out of scope.
- [x] `R-QA-001` — PASS: Unresolved inputs are surfaced in blocking_conditions; no Final artifact is emitted.
- [x] `R-QA-002` — PASS: Experimental rules are advisory and Soft rhythm deviations are explain-only.

## Soft Deviations

- None

## Experimental Advisories

- `R-HERO-003` — ADVISORY_ONLY
- `R-MOBILE-001` — ADVISORY_ONLY
- `R-MOBILE-002` — ADVISORY_ONLY
- `R-MOBILE-003` — ADVISORY_ONLY
- `R-CTA-003` — ADVISORY_ONLY
