# Feishu Miaoda Integration

Use Miaoda as the reviewed collaboration layer, not as the scraper or classifier.

## Architecture

```text
Public pages / exports / authorized browser evidence
  -> Customer Review Intelligence Skill
  -> immutable raw + normalized history + audit decisions
  -> Miaoda bundle
  -> Miaoda dashboard, owner workflow, deadlines, validation results
```

The Skill remains the system of record for immutable raw evidence and analysis history. Miaoda may store a reviewed evidence copy for application queries, but source-language text, source IDs, source URL, raw snapshot reference, and capture batch are evidence-managed and read-only in the front end. Miaoda owns human workflow fields such as owner, status, due date, triage note, correction note, and validation result.

## App choice

- Use `html` only for a read-only snapshot without login, database, or collaborative state.
- Use `full_stack` for multi-user review, assignments, status changes, reminders, database persistence, or external `/api/open` integration.
- For a new app, confirm whether development is local code or Miaoda cloud AI generation before initialization. Do not silently choose.

## Safe import

1. Read `manifest.json`; verify every file hash and coverage status.
2. Create or inspect tables before import.
3. Upsert evidence-managed rows by stable keys. Never delete rows merely because a Partial batch omitted them.
4. Preserve Miaoda-owned collaboration fields on repeated imports.
5. Display sample size, denominator, confidence, and coverage limitation beside every proportion or trend.
6. Link issues to review IDs and reviews to source URLs.
7. Import source-language review text into a dedicated immutable field. Never map a summary, translation, cleaned excerpt, or generated quote into that field.
8. Keep raw fields and derived fields visibly separated in the schema and UI.
9. Product and marketing recommendations must carry real evidence IDs and source-language quotations; missing evidence is displayed as `Evidence Insufficient`.
10. A Miaoda page that resembles a Base table is not a Feishu Base connection. Show sync placeholders as `not_synced` until an actual Base and sync path exist.

## Decision dashboard additions

- Voice Library and Issue Center each include a filter-aware analysis summary with evidence-layer labels.
- Product Backlog and Marketing Application show one to three linked original quotations per recommendation.
- A requested Japanese word cloud is secondary to Pareto and trend analysis, uses distinct-review frequency, and drills into matching voices.
- A channel ledger page separates seven channel inputs from one unified analytical view. Original evidence fields are read-only; manual workflow fields are editable and audited.

## Publication boundary

Generating a bundle is local and reversible. Creating an app, changing its database, importing data, publishing HTML, or releasing a full-stack version changes external state and requires explicit authorization and the target app ID.
