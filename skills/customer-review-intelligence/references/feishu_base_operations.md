# Feishu Base operating layer

Use this reference only when the user requests a Feishu Base / 多维表格 operating layer. Use `$lark-base` for real Base actions and `$lark-apps` for Miaoda actions. A Miaoda database table is not a Feishu Base.

## Recommended topology

Create one Base with seven channel tables and one unified table:

- Amazon Japan
- 楽天
- Yahoo!ショッピング
- SwitchBot 官网
- YouTube
- X
- 媒体
- 统一汇总

Channel tables are the manual operating layer. The unified table is a reconciled copy keyed by stable `review_id`; it is not a formula union and must be refreshed through an audited import/sync process.

## Field boundary

Evidence-managed, read-only fields:

- source review ID and stable `review_id`
- original Japanese text
- source URL and published time
- rating and public display name
- source/raw record type and relationship type
- raw snapshot reference and capture batch
- VOC eligibility, analysis eligibility, sentiment, issue/value JSON

Human-managed fields:

- `manual_status`: 待审核 / 已确认 / 需补采 / 排除 / 已升级
- manual note, owner, priority, reviewed time
- correction note
- sync status and sync error

Never overwrite original Japanese text. A correction goes into `correction_note` with audit history.

## Import contract

1. Inspect the target Base, tables, and fields before every write.
2. Export or read the reviewed Miaoda/local evidence without mutation.
3. Validate row counts, stable keys, channel mapping, original-text samples, and SHA-256.
4. Dry-run at least one representative batch.
5. Write no more than 200 records per batch and serialize writes to the same Base.
6. Preserve raw enum values in dedicated text fields; map them to business select fields separately.
7. Read back counts with Base cloud aggregation. Do not infer full counts from a single record-list page.
8. A partial write is `Partial`; never treat missing rows as zero or delete them.

## Sync boundary

An initial copy is not continuous synchronization. Do not mark Miaoda as connected until the Base record IDs/table IDs have been written back and a repeatable sync path has been tested. Until then, label the application-side status `not_synced` or `initial_copy_only`.
