#!/usr/bin/env python3
"""Fetch every accessible worksheet and an official XLSX snapshot."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import pandas as pd

from feishu_common import (
    CommandRunner,
    FetchError,
    FetchResult,
    envelope_data,
    list_items,
    now_iso,
    relative_to,
    run_lark_cli,
    safe_name,
    write_json,
)


def _sheet_rows(sheet: dict[str, Any]) -> tuple[list[str], list[list[Any]]]:
    columns = sheet.get("columns") or []
    if columns and isinstance(columns[0], dict):
        column_names = [str(item.get("name") or item.get("id") or f"col{index + 1}") for index, item in enumerate(columns)]
    else:
        column_names = [str(item) for item in columns]
    rows = sheet.get("data")
    if rows is None:
        rows = sheet.get("rows", [])
    return column_names, rows if isinstance(rows, list) else []


def fetch_sheet(
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

    info_payload = runner(
        ["sheets", "+workbook-info", "--url", source_url, "--as", "user", "--format", "json"],
        raw_dir,
    )
    write_json(raw_dir / "workbook_info.json", info_payload)
    info = envelope_data(info_payload)
    info_sheets = list_items(info, "sheets", "items")
    if not info_sheets:
        raise FetchError("Workbook structure returned no sheets", status="Unverified")

    export_path = raw_dir / f"{safe_name(source_id)}.xlsx"
    export_warning: list[str] = []
    try:
        export_payload = runner(
            [
                "sheets",
                "+workbook-export",
                "--url",
                source_url,
                "--file-extension",
                "xlsx",
                "--output-path",
                export_path.name,
                "--as",
                "user",
                "--format",
                "json",
            ],
            raw_dir,
        )
        write_json(raw_dir / "workbook_export.json", export_payload)
        if not export_path.exists():
            export_warning.append(
                "Official XLSX export reported success but no local file was found; typed per-sheet snapshots remain available."
            )
    except FetchError as exc:
        export_warning.append(f"Official XLSX export failed: {exc}")

    exported_sheets: dict[str, pd.DataFrame] = {}
    if export_path.exists():
        try:
            exported_sheets = pd.read_excel(
                export_path,
                sheet_name=None,
                header=None,
                dtype=object,
            )
        except Exception as exc:  # pragma: no cover - defensive around third-party exports
            export_warning.append(f"Official XLSX was retained but could not be normalized: {exc}")

    positional_header_warning: list[str] = []
    try:
        table_payload = runner(
            ["sheets", "+table-get", "--url", source_url, "--as", "user", "--format", "json"],
            raw_dir,
        )
    except FetchError as exc:
        if "duplicate header column name" not in str(exc):
            raise
        table_payload = runner(
            [
                "sheets",
                "+table-get",
                "--url",
                source_url,
                "--no-header",
                "--as",
                "user",
                "--format",
                "json",
            ],
            raw_dir,
        )
        positional_header_warning.append(
            "Workbook contains duplicate header labels; read-only capture retried with --no-header. "
            "Normalized columns use positional names and the original first row is retained as data."
        )
    write_json(raw_dir / "table_get.json", table_payload)
    table_data = envelope_data(table_payload)
    typed_sheets = list_items(table_data, "sheets", "items")
    typed_by_id = {
        str(item.get("sheet_id") or item.get("id") or item.get("name")): item
        for item in typed_sheets
    }
    typed_by_name = {str(item.get("name") or item.get("title")): item for item in typed_sheets}

    results: list[FetchResult] = []
    configured_sheet = source.get("sheet_name")
    for metadata in info_sheets:
        sheet_id = str(metadata.get("sheet_id") or metadata.get("id") or "")
        sheet_name = str(metadata.get("title") or metadata.get("sheet_name") or sheet_id)
        if configured_sheet and str(configured_sheet) not in {sheet_id, sheet_name}:
            continue
        resource_type = str(metadata.get("resource_type") or "sheet")
        hidden = bool(metadata.get("is_hidden"))
        warnings = [*export_warning, *positional_header_warning]
        if hidden:
            warnings.append("Sheet is hidden; it was still included in the read-only snapshot.")
        if resource_type != "sheet":
            warnings.append(f"Unsupported grid type {resource_type}; route separately when coordinates are available.")
            results.append(
                FetchResult(
                    source_id=source_id,
                    source_name=source_name,
                    source_url=source_url,
                    source_type="sheet",
                    retrieval_method="lark-cli",
                    retrieval_time=now_iso(),
                    status="Partial",
                    document_name=str(info.get("title") or source_name),
                    object_name=sheet_name,
                    warning=warnings,
                    snapshot_file=[relative_to(raw_dir / "workbook_info.json", snapshot_dir)],
                    metadata={"sheet_id": sheet_id, "resource_type": resource_type, "is_hidden": hidden},
                )
            )
            continue
        sheet = typed_by_id.get(sheet_id) or typed_by_name.get(sheet_name)
        exported_frame = exported_sheets.get(sheet_name)
        if exported_frame is not None:
            frame = exported_frame.copy()
            frame.columns = [f"col{index + 1}" for index in range(len(frame.columns))]
            normalized = normalized_dir / (
                f"{safe_name(source_id)}__{safe_name(sheet_id)}__{safe_name(sheet_name)}.csv"
            )
            frame.to_csv(normalized, index=False, encoding="utf-8-sig")
            normalized_files = [relative_to(normalized, snapshot_dir)]
            row_count = len(frame)
            column_count = len(frame.columns)
            used_range = sheet.get("range") if sheet else None
            warnings.append(
                "Normalized from the retained official XLSX with positional columns; "
                "the original first row is retained as data."
            )
            status = "Complete with Warnings"
        elif sheet is None:
            warnings.append("Sheet metadata was visible but table-get returned no readable data.")
            status = "Partial"
            normalized_files: list[str] = []
            row_count = None
            column_count = metadata.get("column_count")
            used_range = None
        else:
            columns, rows = _sheet_rows(sheet)
            frame = pd.DataFrame(rows, columns=columns or None)
            normalized = normalized_dir / (
                f"{safe_name(source_id)}__{safe_name(sheet_id)}__{safe_name(sheet_name)}.csv"
            )
            frame.to_csv(normalized, index=False, encoding="utf-8-sig")
            normalized_files = [relative_to(normalized, snapshot_dir)]
            row_count = len(frame)
            column_count = len(frame.columns)
            used_range = sheet.get("range")
            status = "Complete with Warnings" if warnings else "Complete"
        results.append(
            FetchResult(
                source_id=source_id,
                source_name=source_name,
                source_url=source_url,
                source_type="sheet",
                retrieval_method="lark-cli",
                retrieval_time=now_iso(),
                status=status,
                document_name=str(info.get("title") or source_name),
                object_name=sheet_name,
                row_count=row_count,
                column_count=column_count,
                warning=warnings,
                snapshot_file=[
                    relative_to(raw_dir / "workbook_info.json", snapshot_dir),
                    *([relative_to(export_path, snapshot_dir)] if export_path.exists() else []),
                ],
                normalized_file=normalized_files,
                metadata={
                    "sheet_id": sheet_id,
                    "resource_type": resource_type,
                    "is_hidden": hidden,
                    "physical_row_count": metadata.get("row_count"),
                    "physical_column_count": metadata.get("column_count"),
                    "used_range": used_range,
                    "formula_display_note": (
                        "Normalized CSV uses displayed/typed values; official XLSX is retained for formulas when export succeeded."
                    ),
                },
            )
        )
    if configured_sheet and not results:
        raise FetchError(f"Configured sheet not found: {configured_sheet}", status="Failed")
    return results


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--url", required=True)
    parser.add_argument("--source-id", default="sheet")
    parser.add_argument("--source-name", default="Feishu Sheet")
    parser.add_argument("--snapshot-dir", type=Path, required=True)
    parser.add_argument("--sheet-name")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    results = fetch_sheet(
        {
            "id": args.source_id,
            "name": args.source_name,
            "url": args.url,
            "sheet_name": args.sheet_name,
        },
        args.snapshot_dir.resolve(),
    )
    print(json.dumps([item.as_manifest_entry() for item in results], ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
