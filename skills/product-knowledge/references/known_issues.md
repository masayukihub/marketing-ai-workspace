# Known Issues

## ISSUE-001 — Lock Ultra bundle feature attribution

- Products: lock_ultra; keypad_vision_pro
- Severity: Critical
- Status: Resolved in canonical fact model; source conflict remains documented
- Issue: SRC-001 lists face, fingerprint, and transit-card unlock methods inside a Lock Ultra selling-point row while its Keypad section attributes biometric capability to the keypad.
- Canonical Handling: Face recognition is owned by `keypad_vision_pro`; Lock Ultra references it only through `required_product_id`.
- External Impact: Block any copy that says Lock Ultra itself performs face recognition.
- Source ID: SRC-001; SRC-003
- Last Verified: 2026-07-30

## ISSUE-002 — Keypad naming inconsistency

- Products: keypad_vision_pro
- Severity: High
- Status: Pending Verification
- Issue: Internal source headings use both Keypad Vision and Keypad Vision Pro.
- Canonical Handling: Use the task-specified `Keypad Vision Pro` as a provisional canonical name and retain `Keypad Vision` as a former/ambiguous alias.
- External Impact: Confirm the current official JP product name before publication.
- Source ID: SRC-001; SRC-003
- Last Verified: 2026-07-30

## ISSUE-003 — Current pricing not yet approved

- Products: All initial-scope products
- Severity: High
- Status: Pending Verification
- Issue: Discoverable price sheets do not by themselves establish channel, tax basis, price type, and effective dates for every product.
- Canonical Handling: `pricing.xlsx` contains no current-price assertions in the initial release.
- External Impact: Price output requires a dated channel-specific read.
- Source ID: SRC-012
- Last Verified: 2026-07-30

## ISSUE-004 — AI and future-feature status

- Products: ai_mindclip; kata_friends; homerunpet_series
- Severity: High
- Status: Pending Verification
- Issue: AI, App integration, OpenAPI, recording, privacy, and availability details may differ by region, account, firmware, subscription, or release stage.
- Canonical Handling: Keep affected facts `unknown`, `announced`, or `pending_verification` until product-owner review.
- External Impact: Do not turn roadmap or draft language into released functionality.
- Source ID: SRC-005; SRC-011; SRC-014
- Last Verified: 2026-07-30
