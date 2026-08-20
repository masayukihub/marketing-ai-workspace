# Product Knowledge Hub Maintenance

This is the maintenance runbook for the SwitchBot Japan Product Knowledge Hub. Feishu remains the source system; the Skill stores only normalized facts, source metadata, review decisions, derived marketing knowledge, and incremental snapshots. Generated indexes and reports are never canonical sources.

## Layer contract

| Layer | Role | May it create an external claim? |
|---|---|---|
| Feishu | Discovery and evidence | No, without Claim approval |
| `references/` | Canonical normalized facts | No, without Claim approval |
| `knowledge/` | Generated marketer-facing summaries | No |
| `snapshots/` | Incremental discovery and Change Sets | No |
| `outputs/` | Runtime index and validation reports | No |

## Update workflow

```text
新产品资料进入
→ 登记 source_registry
→ 保存 URL/token、revision、采集时间、保密等级和允许用途
→ 更新 product_master / product_facts / product_specs
→ 按需更新 pricing / compatibility / positioning / competitor
→ 更新 claim / FAQ / compliance / known issues
→ 创建或更新产品 Profile
→ 运行 validation
→ 处理 conflict
→ 生成 product_index
→ 完成人工审核
```

Do not mark imported material `Approved` merely because it is official or readable. Approval requires explicit evidence of external-use approval. Close historical records with `valid_to`; do not overwrite them.

## Source handling

- Register the source before copying facts from it.
- Record Feishu document revision when available. For a sheet, record workbook token, sheet ID/range, and read time.
- Keep confidential internal sources internal. `allowed_use=internal_verification` does not permit external quotation.
- A search result or search summary is discovery evidence, not a product-fact source.
- When sources conflict, retain both source references and create a conflict record. Do not silently resolve by priority.

## Review responsibilities

- Product/Data owner: validates product identity, model, specifications, dependencies, market, and firmware.
- Marketing/PR owner: approves externally usable wording and allowed channels.
- Compliance/Legal owner: approves regulated, privacy, biometric, AI, award, No.1, and performance-test statements.
- Price owner: validates channel, tax basis, price type, and effective dates.

Blank owner fields mean approval has not been completed.

## Commands

Run from the skill directory using the bundled workspace Python:

```bash
"$PYTHON" scripts/validate_product_data.py --skill-dir . --output outputs/validation_report.md
"$PYTHON" scripts/check_conflicts.py --skill-dir . --as-of 2026-07-30
"$PYTHON" scripts/build_product_index.py --skill-dir .
"$PYTHON" scripts/check_copy_claims.py --skill-dir . --input <draft.txt> --output outputs/claim_lint_report.md
"$PYTHON" scripts/build_knowledge_hub.py --skill-dir . --write-baseline-snapshot
```

Plan a Feishu refresh without network access or data changes:

```bash
"$PYTHON" scripts/discover_feishu_sources.py --skill-dir . --product-id hub_3
```

When the current user identity can read Feishu, create a read-only metadata snapshot and then compare it to the preceding snapshot:

```bash
"$PYTHON" scripts/discover_feishu_sources.py --skill-dir . --product-id hub_3 --execute
"$PYTHON" scripts/build_change_set.py \
  --previous snapshots/<previous>.json \
  --current snapshots/<current>.json \
  --output snapshots/change-set-<timestamp>.json
```

The discovery command records source identity and modified time only. Use the matching Feishu reader to inspect new or modified content and turn it into atomic, source-cited proposals. Apply only facts permitted by `config/update_rules.yaml`.

Preview a verification-date update:

```bash
"$PYTHON" scripts/update_last_verified.py \
  --skill-dir . \
  --product-id hub_3 \
  --source-revision-id 1188 \
  --date 2026-07-30
```

Apply only after reviewing the dry-run output:

```bash
"$PYTHON" scripts/update_last_verified.py \
  --skill-dir . \
  --product-id hub_3 \
  --source-revision-id 1188 \
  --date 2026-07-30 \
  --apply
```

## Output interpretation

- `validation_report.md`: schema, enum, referential-integrity, source, date, URL, and approval-condition issues.
- `conflict_report.md`: conflicting facts, alias ambiguity, feature-owner problems, profile drift, overlapping price periods, expired prices, and status contradictions.
- `product_index.json`: runtime entity index. Regenerate only after critical issues are cleared.

The index exposes top-level and product-level publication readiness. `validation_status: pass` means the structure is internally consistent; it never means a product, price, comparison, or Claim is approved for external publication.

## Safe external use

External PR, advertising, EDM, SNS, KOL, product-page, and sales copy may directly use only `Approved` claims. `Conditional` claims require every listed condition. Other statuses must be omitted or presented as internal review notes, never as confirmed customer-facing facts.
