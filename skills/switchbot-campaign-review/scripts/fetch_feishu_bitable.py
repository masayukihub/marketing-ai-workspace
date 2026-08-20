#!/usr/bin/env python3
"""Fetch every table, field, view, and record from a Feishu Base snapshot."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from feishu_common import (
    CommandRunner,
    FetchError,
    FetchResult,
    envelope_data,
    list_items,
    now_iso,
    paginated_cli,
    records_to_csv,
    relative_to,
    run_lark_cli,
    safe_name,
    write_json,
)
from parse_feishu_url import parse_feishu_url


def _all_metadata(
    command: str,
    base_token: str,
    runner: CommandRunner,
    table_id: str | None = None,
    page_size: int = 100,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    args = ["base", command, "--base-token", base_token]
    if table_id:
        args.extend(["--table-id", table_id])
    item_keys = {
        "+table-list": ("items", "tables"),
        "+field-list": ("items", "fields"),
        "+view-list": ("items", "views"),
    }.get(command, ("items",))
    return paginated_cli(args, runner, page_size=page_size, item_keys=item_keys)


def fetch_bitable(
    source: dict[str, Any],
    snapshot_dir: Path,
    *,
    runner: CommandRunner = run_lark_cli,
) -> list[FetchResult]:
    source_id = str(source["id"])
    source_name = str(source.get("name") or source_id)
    source_url = str(source["url"])
    raw_dir = snapshot_dir / "raw" / safe_name(source_id)
    normalized_dir = snapshot_dir / "normalized"
    raw_dir.mkdir(parents=True, exist_ok=True)
    normalized_dir.mkdir(parents=True, exist_ok=True)
    parsed = parse_feishu_url(source_url)

    resolved = runner(
        ["base", "+url-resolve", "--url", source_url, "--as", "user", "--format", "json"],
        raw_dir,
    )
    write_json(raw_dir / "url_resolution.json", resolved)
    resolution = envelope_data(resolved)
    base_token = (
        resolution.get("base_token")
        or resolution.get("app_token")
        or resolution.get("bitable_app_token")
        or parsed.get("token")
    )
    if not base_token:
        raise FetchError("Unable to resolve Base token", status="Unverified")

    base_payload = runner(
        ["base", "+base-get", "--base-token", str(base_token), "--as", "user", "--format", "json"],
        raw_dir,
    )
    write_json(raw_dir / "base.json", base_payload)
    base_data = envelope_data(base_payload)
    base_name = str(
        base_data.get("name")
        or (base_data.get("base") or {}).get("name", "")
        or source_name
    )

    tables, table_pages = _all_metadata("+table-list", str(base_token), runner)
    write_json(raw_dir / "tables_pages.json", table_pages)
    configured_table = source.get("table_name") or parsed.get("table_id")
    if configured_table:
        tables = [
            table
            for table in tables
            if str(table.get("table_id") or table.get("id") or table.get("name"))
            == str(configured_table)
            or str(table.get("name")) == str(configured_table)
        ]
    if not tables:
        if configured_table:
            raise FetchError(f"Configured Base table not found: {configured_table}", status="Failed")
        raise FetchError(
            "No accessible Base tables were returned; completeness cannot be verified",
            status="Partial",
        )

    results: list[FetchResult] = []
    for table in tables:
        table_id = str(table.get("table_id") or table.get("id") or table.get("name"))
        table_name = str(table.get("name") or table_id)
        table_dir = raw_dir / safe_name(table_id)
        table_dir.mkdir(parents=True, exist_ok=True)
        fields, field_pages = _all_metadata("+field-list", str(base_token), runner, table_id, 200)
        views, view_pages = _all_metadata("+view-list", str(base_token), runner, table_id, 200)
        write_json(table_dir / "fields_pages.json", field_pages)
        write_json(table_dir / "views_pages.json", view_pages)

        record_args = [
            "base",
            "+record-list",
            "--base-token",
            str(base_token),
            "--table-id",
            table_id,
        ]
        configured_view = source.get("view_name") or parsed.get("view_id")
        if configured_view:
            record_args.extend(["--view-id", str(configured_view)])
        records, record_pages = paginated_cli(
            record_args,
            runner,
            page_size=200,
            item_keys=("items", "records"),
        )
        raw_records = table_dir / "records_pages.json"
        write_json(raw_records, record_pages)
        normalized = normalized_dir / f"{safe_name(source_id)}__{safe_name(table_name)}.csv"
        row_count, column_count = records_to_csv(records, normalized)
        warnings: list[str] = []
        if configured_view:
            warnings.append(
                "A configured view was applied; completeness is relative to that view, not the full table."
            )
        results.append(
            FetchResult(
                source_id=source_id,
                source_name=source_name,
                source_url=source_url,
                source_type="bitable",
                retrieval_method="lark-cli",
                retrieval_time=now_iso(),
                status="Complete with Warnings" if warnings else "Complete",
                document_name=base_name,
                object_name=table_name,
                row_count=row_count,
                column_count=column_count,
                warning=warnings,
                snapshot_file=[
                    relative_to(raw_records, snapshot_dir),
                    relative_to(table_dir / "fields_pages.json", snapshot_dir),
                    relative_to(table_dir / "views_pages.json", snapshot_dir),
                ],
                normalized_file=[relative_to(normalized, snapshot_dir)],
                metadata={
                    "base_token_hash": __import__("hashlib").sha256(str(base_token).encode()).hexdigest()[:12],
                    "table_id": table_id,
                    "field_count": len(fields),
                    "view_count": len(views),
                    "record_id_preserved": True,
                },
            )
        )
    return results


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--url", required=True)
    parser.add_argument("--source-id", default="bitable")
    parser.add_argument("--source-name", default="Feishu Base")
    parser.add_argument("--snapshot-dir", type=Path, required=True)
    parser.add_argument("--table-name")
    parser.add_argument("--view-name")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    source = {
        "id": args.source_id,
        "name": args.source_name,
        "url": args.url,
        "table_name": args.table_name,
        "view_name": args.view_name,
    }
    results = fetch_bitable(source, args.snapshot_dir.resolve())
    print(json.dumps([result.as_manifest_entry() for result in results], ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
