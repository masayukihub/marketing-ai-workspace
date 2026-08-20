# Standard Run Contract

## Inputs

Every run must declare:

- market, product entity IDs, requested sources, requested date window, and mode (`full` or `incremental`);
- the Product Knowledge index used for product, variant, and bundle resolution;
- source configuration and any user-provided URLs or exports;
- a unique batch ID and the previous successful cutoff for incremental runs.

## Stage gates

1. `resolve`: fail closed on unknown, ambiguous, or conflicting entities.
2. `collect`: save immutable evidence, page/scroll boundaries, hashes, and failure states.
3. `normalize`: preserve raw values and create stable IDs and versions.
4. `classify`: save deterministic candidates, contextual decisions, confidence, and review reasons.
5. `validate`: reconcile source coverage, normalized counts, evidence links, and output counts.
6. `analyze`: create product, channel, trend, risk, action, and marketing outputs.
7. `publish_local`: build offline HTML/XLSX artifacts without overwriting prior versions.
8. `export_miaoda`: package reviewed rows and collaboration-ready schemas; never upload automatically.

A failed gate stops dependent claims but must still write a resumable run state and collection report.

## Completion states

- `Complete`: every configured boundary was traversed and reconciled.
- `Zero Confirmed`: complete traversal succeeded and found no eligible records.
- `Partial`: some evidence was acquired but the configured boundary was not completed.
- `Blocked`: access control, CAPTCHA, rate limit, or technical restriction prevented evidence capture.
- `Not Configured`: no auditable source URL, query, export, or adapter was configured.
- `Unverified`: evidence exists but its identity, date, mapping, or provenance is not yet auditable.

Never aggregate `Partial`, `Blocked`, `Not Configured`, or `Unverified` as zero.

## Standard deliverable contract

Each product run must produce the normalized history, source coverage, quality report, issue and risk queues, product backlog, marketing playbook, and a traceable dashboard. When `export_miaoda` is requested, also create:

```text
miaoda_bundle/
  manifest.json
  data/review.csv
  data/issue.csv
  data/action.csv
  data/marketing_insight.csv
  data/dashboard_summary.json
  migrations/001_create_voc_tables.sql
  docs/app_blueprint.md
  docs/data_dictionary.md
  dashboard/
```

The bundle is an offline handoff. Creating, migrating, importing, releasing, or publishing a Miaoda app is a separate authorized action.
