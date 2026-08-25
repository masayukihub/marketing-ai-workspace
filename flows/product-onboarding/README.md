# Product Onboarding — P0-1

This flow proves one bounded capability: the same reviewed product-source set can produce a traceable Product Truth proposal without inventing or auto-approving Claims.

## Pilot boundary

The only implemented pilot is:

| Field | Value |
| --- | --- |
| Project | `s30-mini` |
| Market | `JP` |
| Locale | `ja-JP` |
| Channel | `Amazon.co.jp` |
| Offer | `水箱版のみ` |
| Terminal gate | `PRODUCT_TRUTH_HUMAN_REVIEW_GATE` |

This flow does not create Amazon Storyline, Gallery assets, images, a final PDP, GTM outputs, EDM, dashboards, monitoring, publication, or production writes.

## Contract chain

```text
Feishu MCP | confirmed Local File | confirmed Manual Snapshot
  -> Source Snapshot
  -> Product Knowledge Change Proposal (proposal only)
  -> Product Truth Proposal (owner schema validation)
  -> Conflict / Missing Report
  -> Claim Human Review Queue
  -> PRODUCT_TRUTH_HUMAN_REVIEW_GATE
```

The Product Truth schema is owned by `jp-commerce-creative-flow`. This repository stores only [`../../contracts/product-truth-schema-reference.json`](../../contracts/product-truth-schema-reference.json), which locks its repository commit, path, `$id`, and SHA-256. Do not copy or recreate that schema here.

## Input adapters

| Requested adapter | Accepted evidence | Fail-closed behavior |
| --- | --- | --- |
| `FEISHU_MCP` | Successful `get_feishu_resource` response in the private runtime | If unavailable, set Feishu status to `BLOCKED`. Continue only with an explicitly confirmed Local File or Manual Snapshot fallback. |
| `LOCAL_FILE` | A human-confirmed, read-only local source with a content hash | Record direct input as `CONFIRMED_LOCAL_INPUT` and fallback as `CONFIRMED_FALLBACK`. Both require `input_confirmation`; never label either as a Feishu read performed by this run. |
| `MANUAL_SNAPSHOT` | A human-confirmed snapshot with source pointer, date, and scope | Direct manual input and fallback both require `input_confirmation`; map it to `human_decision` and keep every extracted fact or Claim in proposal/review state. |

Gateway `resource_type: "sheets"` is not directly compatible with the owner flow's Product Truth source type. A successful Gateway response must preserve `content.sheets[].values` in the private runtime, record `sheets_collection_to_feishu_sheet`, and emit Product Truth source type `feishu_sheet`. A human-confirmed annotated CSV export is a different input: it must use `raw_resource_type: "feishu_sheet_export"`, `payload_shape: "annotated_csv"`, and `annotated_csv_export_to_feishu_sheet`. It must never impersonate a successful Gateway read. A mapping record is evidence of transformation, not evidence that a Claim is approved.

## Private runtime

Pass an absolute runtime directory located outside every Git repository and outside installed Skill roots such as `~/.codex/skills`. Freeze every real input under that run's private `inputs/` directory before execution; the request and seven outputs stay at the run root. The runner hashes those frozen inputs and must reject paths that escape the run directory. Real Feishu body text, price details, approval records, unreleased materials, and generated pilot outputs stay there. Tracked files contain contracts, code, tests, and safe fixtures only.

The runtime produces exactly:

```text
source-snapshot.json
product-knowledge-change-proposal.json
product-truth-proposal.json
conflict-missing-report.json
claim-human-review-queue.json
run-manifest.json
product-truth-review.html
```

All paths inside `run-manifest.json` are relative to that run directory. The manifest does not hash itself; the six other artifacts are recorded with hashes and validation results.

## Run request

The request JSON also stays outside Git. It supplies fixed run scope, acquisition evidence, source file pointers and hashes, three structured extraction tables, selected fact-to-schema mappings, candidate Claim IDs, conflicts, and explicit unknowns. A Feishu call is performed by the orchestrator; its response must be persisted privately and handed to this runner. The runner never claims to have called MCP by itself.

```bash
JP_COMMERCE_CREATIVE_FLOW_DIR=/absolute/path/to/jp-commerce-creative-flow \
  ./.venv/bin/python flows/product-onboarding/scripts/run_product_onboarding.py \
  --request /absolute/private/runtime/request.json \
  --output-dir /absolute/private/runtime/run-id
```

The request must use `request_version: "1.0"`. For a failed Feishu call with fallback, preserve `requested_adapter: "FEISHU_MCP"`, set `adapter_status: "BLOCKED"`, provide the exact non-secret error, set `effective_adapter` to `LOCAL_FILE` or `MANUAL_SNAPSHOT`, and include a complete `fallback_confirmation`. Without that confirmation the runner fails closed as `P0_1_BLOCKED`.

Each source entry points to a frozen file under the run's private `inputs/` directory and may include `expected_sha256`. The runner hashes every source before extraction and rejects drift. A captured Gateway Sheet uses `raw_resource_type: "sheets"`, `normalized_source_type: "feishu_sheet"`, `mapping_rule: "sheets_collection_to_feishu_sheet"`, and `payload_shape: "content.sheets[].values"`. A confirmed export instead uses the export mapping above. A normalized Gate-1 derivative uses `derived_artifact` to `product_knowledge`, declares non-empty `derived_from` lineage to registered upstream sources, and never becomes an official source or approved Claim. Canonical source pointers may remain `NOT_EXTRACTED`; they prove provenance, not that this run read their body.

`product_knowledge_source_priorities` must map every canonical source used by a fact or Claim to Product Knowledge's `P1`–`P5` confidence policy. Do not copy a project-management priority such as `P0` into this field: a technical specification may be `P1`, while a working marketing draft or blocked research lead must remain at its lower confidence tier. The proposal validator rejects values outside `P1`–`P5`.

Every manifest `PASS` check records the validator name, execution time, evidence, and a SHA-256 of its checked subject. A file subject is hashed as raw bytes; a structured or multi-part subject is serialized as deterministic, key-sorted canonical JSON before hashing. Dependency status is run-specific: `PASS` means the locked dependency was actually resolved and checked for this run; `NOT_USED` means it was not part of the effective runtime path. The lock file itself does not prove Gateway availability.

## Review and write boundary

- `product-knowledge-change-proposal.json` is never a canonical Product Knowledge write.
- `product-truth-proposal.json` must validate against the locked owner schema and must keep `approved_claims` empty until the separate, authorized approval process is completed.
- A decision in `claim-human-review-queue.json` accepts or rejects this proposal only. It does not approve an external Claim and does not update Product Knowledge. Each review item separately records its immediate snapshot source refs and canonical upstream `SRC-###` refs.
- Missing, conditional, prohibited, conflicted, stale, or out-of-offer information stays explicit.
- Water-station capabilities must not be attributed to the water-tank-only offer.

The run stops at `PRODUCT_TRUTH_HUMAN_REVIEW_GATE`. Its final state must be exactly one of:

- `P0_1_READY_FOR_REVIEW`
- `P0_1_PARTIAL`
- `P0_1_BLOCKED`

## Verification

Use the repository's only verification entrypoint:

```bash
./scripts/verify.sh
```

It must use the repository `.venv`; invoking system Python is not an accepted verification path.
