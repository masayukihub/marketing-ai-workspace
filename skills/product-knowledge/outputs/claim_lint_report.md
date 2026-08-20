# Draft Claim Lint Report

- Generated At: 2026-07-30T18:11:34+08:00
- Overall Status: FAIL
- Detected Products: lock_ultra
- Publication Decision: BLOCK

## Summary

- Critical: 3
- High: 0
- Medium: 0
- Low: 0

## Findings

- [Critical] `CAPABILITY_OWNER_COPY_ERROR` — Face recognition is attributed to Lock Ultra without the Keypad Vision Pro capability owner.
- [Critical] `NUMERIC_PERFORMANCE_REQUIRES_APPROVED_CLAIM` — Draft contains a performance-like number; link an Approved Claim and every test condition before publication. (matches=0.3秒, 12ヶ月)
- [Critical] `PRODUCT_NOT_PUBLICATION_READY` — Detected product is not ready to support external factual claims. (product_id=lock_ultra; reasons=profile_not_verified, profile_conflict, lifecycle_not_verified_active, no_approved_external_claim, facts_not_fully_verified)
