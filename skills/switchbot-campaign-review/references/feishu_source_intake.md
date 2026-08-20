# Feishu Source Intake

Use this reference whenever the task includes a Feishu/Lark URL, `sources.yaml`, or a project note containing Feishu links.

## Non-negotiable boundary

1. Discover sources from the registry and supported project-description files.
2. Resolve every `/base/`, `/sheets/`, `/docx/`, and `/wiki/` URL.
3. Check access and capture every relevant table, worksheet, field, view, record, document section, and structured table.
4. Write an immutable local batch under `snapshots/YYYY-MM-DD_HHMMSS/`.
5. Run integrity checks and generate `manifest.json`, `fetch_log.md`, and `source_integrity_report.md`. Create a fresh batch for each fetch; reuse is allowed only through an explicit `--snapshot` analyze-only run.
6. Analyze only `snapshots/<batch>/normalized/`. Never use a live Feishu page as the formal analytical dataset.
7. Trace report conclusions to the snapshot batch and analysis cutoff.

Missing, partial, or inaccessible data remains `Not Available`, `Not Comparable`, or a Data Gap. Never substitute zero.

## Retrieval priority

Use the first available read-only method:

1. Configured authenticated `lark-cli` or MCP connector.
2. OpenAPI or the CLI's official export wrapper.
3. Official export through an authenticated Browser/Chrome session.
4. Ask for a manual export only after automated paths fail.

For every fallback, record method, error category, permission state, volume/completeness limit, and whether another attempt is possible.

## Object rules

### Base

- Resolve the URL, then read Base metadata.
- List all tables. For each table, list fields and views.
- Read records by serial pagination until `has_more` is false. Never parallelize pages.
- Preserve `record_id`; retain scalar values and serialize complex fields as lossless JSON strings.
- Save raw page envelopes plus normalized CSV files.
- A configured view limits completeness to that view and must create a warning.

### Sheets

- Call workbook-info first and enumerate every worksheet.
- Read the full used range for every accessible grid sheet, including hidden sheets.
- Retain official XLSX when export succeeds; normalize every worksheet to its own CSV.
- Record physical dimensions, used range, visibility, unsupported embedded object types, and unreadable sheets.
- Normalized CSV contains displayed/typed values. Use the retained XLSX when formula provenance matters.

### Docs and Wiki

- Export Docs as structured XML/JSON and Markdown; retain heading hierarchy, tables, and media references.
- A Wiki URL must first resolve to its true object type and token, then route to the Base, Sheet, or Doc reader.
- Embedded Sheet/Base references inside a Doc require separate source entries when their internal data is needed.

## Browser fallback

Browser/Chrome takeover is read-only:

- Confirm login, title, and object type.
- Prefer an official export.
- Do not change source filters, views, records, or document content.
- Do not treat infinite scroll as complete.
- Do not use screenshot OCR as the analytical dataset.
- If completeness cannot be proved, set status to `Unverified` or `Partial`.

The Python runner consumes a browser export only from `FEISHU_BROWSER_FALLBACK_DIR`, named `<source-id>.<extension>`. If no export is present, it writes `browser_fallback_request.json` for the agent to execute using the browser skill and rerun.

## Credentials and logs

- Keep real credentials in environment variables, an approved credential manager, MCP, or authenticated CLI session.
- Never place credentials in source registries, Skill files, snapshots, reports, tests, or Git.
- Redact access tokens, refresh tokens, authorization headers, cookies, sessions, and app secrets recursively.
- Never print full CLI environments or credential values.

## Integrity status

- `Complete`: all configured scope was captured and completeness verified.
- `Complete with Warnings`: complete, with a non-blocking issue.
- `Partial`: some relevant data was captured but scope is incomplete.
- `Failed`: no usable capture due to a non-permission failure.
- `Permission Required`: authentication or authorization blocks access.
- `Unverified`: content exists but completeness or identity cannot be proven.

Required sources at `Partial` or worse lower report confidence and must be disclosed in the Executive Summary/Data Limitations. Optional failures are disclosed but do not block supported analysis.

The manifest stores SHA-256 for every normalized file and a combined content fingerprint. `--analyze-only` must reject missing or changed normalized files. A `--source-id` filter does not erase other configured sources: omitted required sources remain explicit `Partial` entries.

## Commands

Fetch and analyze:

```bash
python scripts/run_campaign_review.py --sources sources.yaml --output output/
```

Fetch only:

```bash
python scripts/run_campaign_review.py --sources sources.yaml --output output/ --fetch-only
```

Analyze a fixed batch without network access:

```bash
python scripts/run_campaign_review.py \
  --sources sources.yaml \
  --snapshot snapshots/2026-07-30_120000 \
  --analyze-only \
  --output output/
```
