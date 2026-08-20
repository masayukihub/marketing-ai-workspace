# Feishu Sync Contract

Feishu is the discovery and evidence system. Product Knowledge is the normalized, traceable marketing knowledge layer. Do not copy whole documents into this Skill.

## Incremental flow

1. Run `discover_feishu_sources.py` for one product or for the registered folder.
2. Keep the generated snapshot. It records only searchable metadata and source identity.
3. Run `build_change_set.py` against the preceding snapshot.
4. Fetch only new or modified candidate documents, then extract atomic facts with a source ID, revision, market, validity date, and evidence location.
5. Apply only P1 facts that satisfy `config/update_rules.yaml`; send all claims, prices, privacy, firmware, compatibility, performance, certification, awards, and conflicts to review.
6. Regenerate the hub and the runtime index.

## Candidate extraction schema

```json
{
  "source_id": "SRC-XXX",
  "source_revision_id": "<Feishu revision or modified time>",
  "product_id": "hub_3",
  "market": "JP",
  "information_type": "specification",
  "field": "matter_support",
  "value": "<explicit source value>",
  "conditions": "<firmware, app, device, test, or regional conditions>",
  "evidence_location": "<section, table, or cell>",
  "source_priority": "P1",
  "proposed_review_status": "verified"
}
```

Never promote an extracted proposal to an externally usable Claim merely because it came from Feishu. External use requires the existing Claim approval gate.
