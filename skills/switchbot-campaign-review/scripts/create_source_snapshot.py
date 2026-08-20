#!/usr/bin/env python3
"""Create an immutable local snapshot from a Feishu-aware source registry."""

from __future__ import annotations

import argparse
import json
import os
import shutil
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, List, Optional
from urllib.parse import urlparse

from export_feishu_document import export_document
from fetch_feishu_bitable import fetch_bitable
from fetch_feishu_sheet import fetch_sheet
from feishu_common import (
    CommandRunner,
    FetchError,
    FetchResult,
    copy_read_only,
    envelope_data,
    file_sha256,
    load_registry,
    now_iso,
    redact,
    registry_fingerprint,
    relative_to,
    run_lark_cli,
    safe_name,
    write_json,
)
from parse_feishu_url import extract_feishu_urls, parse_feishu_url

BrowserFallback = Callable[
    [dict[str, Any], Path, FetchError],
    Optional[List[FetchResult]],
]


def _status_rank(status: str) -> int:
    return {
        "Complete": 0,
        "Complete with Warnings": 1,
        "Unverified": 2,
        "Partial": 3,
        "Permission Required": 4,
        "Failed": 5,
    }.get(status, 5)


def _write_integrity_report(
    snapshot_dir: Path,
    registry: dict[str, Any],
    entries: list[dict[str, Any]],
) -> Path:
    required_by_id = {
        str(source["id"]): bool(source.get("required", True))
        for source in registry["sources"]
    }
    counts: dict[str, int] = {}
    for entry in entries:
        counts[entry["status"]] = counts.get(entry["status"], 0) + 1
    lines = [
        "# Source Integrity Report",
        "",
        f"- Snapshot: `{snapshot_dir.name}`",
        f"- Retrieval cutoff: `{max((entry.get('retrieval_time') or '' for entry in entries), default=now_iso())}`",
        f"- Manifest entries: {len(entries)}",
        f"- Status counts: {json.dumps(counts, ensure_ascii=False, sort_keys=True)}",
        "",
        "## Source Status",
        "",
        "| Source | Object | Required | Type | Status | Rows | Columns | Method | Warning / Error |",
        "|---|---|---:|---|---|---:|---:|---|---|",
    ]
    for entry in entries:
        warning = "; ".join(entry.get("warning") or [])
        error = str(entry.get("error") or "")
        detail = (warning + ("; " if warning and error else "") + error).replace("|", "\\|")
        lines.append(
            f"| {entry['source_id']} | {entry.get('table_or_sheet_name') or entry.get('document_name') or ''} "
            f"| {'Yes' if required_by_id.get(entry['source_id'], True) else 'No'} "
            f"| {entry['source_type']} | {entry['status']} "
            f"| {entry.get('row_count') if entry.get('row_count') is not None else ''} "
            f"| {entry.get('column_count') if entry.get('column_count') is not None else ''} "
            f"| {entry.get('retrieval_method') or ''} | {detail} |"
        )
    material = [
        entry
        for entry in entries
        if required_by_id.get(entry["source_id"], True)
        and _status_rank(entry["status"]) >= _status_rank("Partial")
    ]
    lines.extend(["", "## Decision Boundary", ""])
    if material:
        lines.append(
            "- [Risk] One or more required sources are Partial, Failed, Permission Required, or Unverified. "
            "Supported analysis may continue, but missing values must remain unavailable and confidence must be lowered."
        )
    else:
        lines.append("- [Fact] No required source has a material completeness failure in this snapshot.")
    lines.append(
        "- [Risk] Completeness describes the captured snapshot only; it does not prove that upstream owners supplied every relevant source."
    )
    path = snapshot_dir / "source_integrity_report.md"
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


def _browser_directory_fallback(
    source: dict[str, Any],
    snapshot_dir: Path,
    error: FetchError,
) -> list[FetchResult] | None:
    fallback_root = os.environ.get("FEISHU_BROWSER_FALLBACK_DIR")
    if not fallback_root:
        return None
    directory = Path(fallback_root).expanduser().resolve()
    candidates = sorted(directory.glob(f"{safe_name(str(source['id']))}.*"))
    if not candidates:
        return None
    raw_dir = snapshot_dir / "raw" / safe_name(str(source["id"])) / "browser"
    normalized_dir = snapshot_dir / "normalized"
    raw_dir.mkdir(parents=True, exist_ok=True)
    normalized_dir.mkdir(parents=True, exist_ok=True)
    normalized_files: list[str] = []
    raw_files: list[str] = []
    for candidate in candidates:
        raw_path = copy_read_only(candidate, raw_dir / candidate.name)
        raw_files.append(relative_to(raw_path, snapshot_dir))
        if candidate.suffix.lower() in {".xlsx", ".xls", ".csv", ".tsv", ".json", ".md", ".pdf"}:
            normalized = copy_read_only(
                candidate,
                normalized_dir / f"{safe_name(str(source['id']))}__browser{candidate.suffix.lower()}",
            )
            normalized_files.append(relative_to(normalized, snapshot_dir))
    return [
        FetchResult(
            source_id=str(source["id"]),
            source_name=str(source.get("name") or source["id"]),
            source_url=str(source.get("url") or ""),
            source_type=str(source.get("source_type") or "unknown"),
            retrieval_method="browser-export",
            retrieval_time=now_iso(),
            status="Unverified",
            warning=[
                f"CLI fetch failed: {error}",
                "Browser-export completeness could not be proven automatically; infinite-scroll capture is never treated as complete.",
            ],
            snapshot_file=raw_files,
            normalized_file=normalized_files,
        )
    ]


def _expand_file_sources(registry: dict[str, Any], registry_path: Path) -> dict[str, Any]:
    expanded: list[dict[str, Any]] = []
    known_urls = {str(item.get("url", "")) for item in registry["sources"]}
    for source in registry["sources"]:
        expanded.append(source)
        source_type = str(source.get("source_type") or "auto")
        raw_location = str(source.get("url") or "")
        local_path = Path(raw_location)
        if not local_path.is_absolute():
            local_path = (registry_path.parent / local_path).resolve()
        if source_type not in {"file", "auto"} or not local_path.is_file():
            continue
        if local_path.suffix.lower() not in {".md", ".txt", ".yaml", ".yml", ".json"}:
            continue
        for index, parsed in enumerate(
            extract_feishu_urls(local_path.read_text(encoding="utf-8", errors="replace")),
            start=1,
        ):
            if parsed["original_url"] in known_urls:
                continue
            known_urls.add(parsed["original_url"])
            expanded.append(
                {
                    "id": f"{source['id']}-link-{index}",
                    "name": f"{source.get('name', source['id'])} link {index}",
                    "url": parsed["original_url"],
                    "source_type": parsed["source_type"],
                    "required": bool(source.get("required", True)),
                    "notes": f"Discovered from {local_path.name}",
                }
            )
    registry["sources"] = expanded
    return registry


def _fetch_local_file(source: dict[str, Any], snapshot_dir: Path, registry_path: Path) -> list[FetchResult]:
    location = Path(str(source.get("url") or ""))
    if not location.is_absolute():
        location = (registry_path.parent / location).resolve()
    if not location.is_file():
        raise FetchError(f"Local source file not found: {location}")
    raw = copy_read_only(
        location,
        snapshot_dir / "raw" / safe_name(str(source["id"])) / location.name,
    )
    normalized_files: list[str] = []
    if location.suffix.lower() in {".xlsx", ".xls", ".csv", ".tsv", ".json", ".md", ".pdf"}:
        normalized = copy_read_only(
            location,
            snapshot_dir / "normalized" / f"{safe_name(str(source['id']))}__{location.name}",
        )
        normalized_files.append(relative_to(normalized, snapshot_dir))
    return [
        FetchResult(
            source_id=str(source["id"]),
            source_name=str(source.get("name") or source["id"]),
            source_url=str(source.get("url") or ""),
            source_type="file",
            retrieval_method="local-copy",
            retrieval_time=now_iso(),
            status="Complete",
            document_name=location.name,
            snapshot_file=[relative_to(raw, snapshot_dir)],
            normalized_file=normalized_files,
        )
    ]


def _route_wiki(
    source: dict[str, Any],
    snapshot_dir: Path,
    runner: CommandRunner,
) -> list[FetchResult]:
    payload = runner(
        [
            "wiki",
            "+node-get",
            "--node-token",
            str(source["url"]),
            "--as",
            "user",
            "--format",
            "json",
        ],
        snapshot_dir / "raw",
    )
    resolution_path = snapshot_dir / "raw" / safe_name(str(source["id"])) / "wiki_resolution.json"
    write_json(resolution_path, payload)
    data = envelope_data(payload)
    node = data.get("node") if isinstance(data.get("node"), dict) else data
    object_type = str(node.get("obj_type") or node.get("object_type") or "").lower()
    object_token = node.get("obj_token") or node.get("object_token")
    if not object_type or not object_token:
        raise FetchError("Wiki node did not resolve to an object type and token", status="Unverified")
    routed = dict(source)
    routed["source_type"] = {"sheet": "sheet", "bitable": "bitable", "doc": "docx", "docx": "docx"}.get(
        object_type, "unknown"
    )
    host = urlparse(str(source["url"])).netloc
    routed["url"] = f"https://{host}/{object_type}/{object_token}"
    if routed["source_type"] == "sheet":
        results = fetch_sheet(routed, snapshot_dir, runner=runner)
    elif routed["source_type"] == "bitable":
        results = fetch_bitable(routed, snapshot_dir, runner=runner)
    elif routed["source_type"] == "docx":
        results = export_document(routed, snapshot_dir, runner=runner)
    else:
        raise FetchError(f"Unsupported Wiki object type: {object_type}", status="Partial")
    for result in results:
        result.source_type = "wiki"
        result.metadata["resolved_object_type"] = object_type
        result.metadata["wiki_resolution_file"] = relative_to(resolution_path, snapshot_dir)
    return results


def create_snapshot(
    sources_path: Path,
    snapshot_root: Path | None = None,
    *,
    source_ids: set[str] | None = None,
    force_refresh: bool = False,
    browser_fallback: bool = False,
    runner: CommandRunner = run_lark_cli,
    browser_adapter: BrowserFallback | None = None,
    timestamp: str | None = None,
) -> Path:
    sources_path = sources_path.resolve()
    base_registry = load_registry(sources_path)
    source_registry_fingerprint = registry_fingerprint(base_registry)
    registry = _expand_file_sources(base_registry, sources_path)
    all_sources = list(registry["sources"])
    if source_ids:
        selected_sources = [
            source for source in all_sources if str(source["id"]) in source_ids
        ]
        if not selected_sources:
            raise ValueError("No configured sources matched --source-id")
    else:
        selected_sources = all_sources
    snapshot_root = (snapshot_root or sources_path.parent / "snapshots").resolve()
    snapshot_root.mkdir(parents=True, exist_ok=True)
    fingerprint = registry_fingerprint(
        {
            "registry": registry,
            "selected_source_ids": sorted(str(source["id"]) for source in selected_sources),
        }
    )
    batch = timestamp or datetime.now().strftime("%Y-%m-%d_%H%M%S")
    snapshot_dir = snapshot_root / batch
    if snapshot_dir.exists():
        raise FileExistsError(f"Snapshot batch already exists: {snapshot_dir}")
    (snapshot_dir / "raw").mkdir(parents=True)
    (snapshot_dir / "normalized").mkdir()
    write_json(snapshot_dir / "source_registry.json", registry)
    fetch_log: list[str] = [
        "# Fetch Log",
        "",
        f"- Started: `{now_iso()}`",
        f"- Registry: `{sources_path}`",
        "- Priority: configured lark-cli/MCP → OpenAPI/export wrapper → browser export → manual handoff.",
        "",
    ]
    results: list[FetchResult] = []
    adapter = browser_adapter or _browser_directory_fallback
    for source in selected_sources:
        source_id = str(source["id"])
        parsed = parse_feishu_url(str(source.get("url") or ""))
        source_type = str(source.get("source_type") or "auto")
        if source_type == "auto":
            source_type = parsed["source_type"]
        if source_type == "auto":
            source_type = "unknown"
        try:
            if source_type == "file" or (
                source_type == "unknown"
                and Path(str(source.get("url") or "")).suffix.lower()
            ):
                fetched = _fetch_local_file(source, snapshot_dir, sources_path)
            elif source_type == "bitable":
                fetched = fetch_bitable(source, snapshot_dir, runner=runner)
            elif source_type == "sheet":
                fetched = fetch_sheet(source, snapshot_dir, runner=runner)
            elif source_type == "docx":
                fetched = export_document(source, snapshot_dir, runner=runner)
            elif source_type == "wiki":
                fetched = _route_wiki(source, snapshot_dir, runner)
            else:
                raise FetchError("Unsupported or unrecognized source URL", status="Unverified")
            results.extend(fetched)
            fetch_log.append(f"- `{source_id}`: {', '.join(item.status for item in fetched)} via {', '.join(sorted({item.retrieval_method for item in fetched}))}")
        except FetchError as exc:
            fallback_results = adapter(source, snapshot_dir, exc) if browser_fallback else None
            if fallback_results:
                results.extend(fallback_results)
                fetch_log.append(f"- `{source_id}`: browser fallback used after {exc.status} ({redact(str(exc))})")
            else:
                results.append(
                    FetchResult(
                        source_id=source_id,
                        source_name=str(source.get("name") or source_id),
                        source_url=str(source.get("url") or ""),
                        source_type=source_type,
                        retrieval_method=exc.method,
                        retrieval_time=now_iso(),
                        status=exc.status,
                        error=str(redact(str(exc))),
                    )
                )
                fetch_log.append(f"- `{source_id}`: {exc.status} via {exc.method}; {redact(str(exc))}")
                if browser_fallback:
                    request = {
                        "source_id": source_id,
                        "url": source.get("url"),
                        "instructions": [
                            "Use an authenticated Browser/Chrome session read-only.",
                            "Confirm title and object type, then prefer official export.",
                            "Save the export as <source-id>.<supported-extension> in FEISHU_BROWSER_FALLBACK_DIR.",
                            "Do not treat infinite-scroll or screenshot OCR as a complete snapshot.",
                        ],
                    }
                    write_json(snapshot_dir / "raw" / safe_name(source_id) / "browser_fallback_request.json", request)
        except (OSError, ValueError, TypeError, KeyError, json.JSONDecodeError) as exc:
            safe_error = FetchError(f"Unexpected source read failure: {redact(str(exc))}")
            results.append(
                FetchResult(
                    source_id=source_id,
                    source_name=str(source.get("name") or source_id),
                    source_url=str(source.get("url") or ""),
                    source_type=source_type,
                    retrieval_method="local-or-lark-cli",
                    retrieval_time=now_iso(),
                    status="Failed",
                    error=str(safe_error),
                )
            )
            fetch_log.append(f"- `{source_id}`: Failed; {safe_error}")
    selected_ids = {str(source["id"]) for source in selected_sources}
    for source in all_sources:
        source_id = str(source["id"])
        if source_id in selected_ids:
            continue
        results.append(
            FetchResult(
                source_id=source_id,
                source_name=str(source.get("name") or source_id),
                source_url=str(source.get("url") or ""),
                source_type=str(source.get("source_type") or "auto"),
                retrieval_method="not-fetched",
                retrieval_time=now_iso(),
                status="Partial" if bool(source.get("required", True)) else "Unverified",
                error="Source omitted by --source-id filter",
            )
        )
    entries = [result.as_manifest_entry() for result in results]
    required_lookup = {
        str(source["id"]): bool(source.get("required", True))
        for source in all_sources
    }
    for entry in entries:
        entry["required"] = required_lookup.get(entry["source_id"], True)
        entry["normalized_sha256"] = {
            relative_path: file_sha256(snapshot_dir / relative_path)
            for relative_path in entry.get("normalized_file", [])
            if (snapshot_dir / relative_path).is_file()
        }
    required_ids = {
        str(source["id"]) for source in all_sources if bool(source.get("required", True))
    }
    material_required = [
        entry
        for entry in entries
        if entry["source_id"] in required_ids
        and _status_rank(entry["status"]) >= _status_rank("Partial")
    ]
    manifest_status = (
        "Partial"
        if material_required
        else (
            "Complete with Warnings"
            if any(entry["status"] != "Complete" for entry in entries)
            else "Complete"
        )
    )
    normalized_hashes = {
        f"{entry['source_id']}:{path}": digest
        for entry in entries
        for path, digest in entry.get("normalized_sha256", {}).items()
    }
    manifest = {
        "schema_version": "1.0",
        "project": registry.get("project", {}),
        "registry_file": str(sources_path),
        "registry_snapshot_file": "source_registry.json",
        "registry_fingerprint": fingerprint,
        "source_registry_fingerprint": source_registry_fingerprint,
        "snapshot_batch": batch,
        "created_at": now_iso(),
        "analysis_cutoff": max((entry.get("retrieval_time") or "" for entry in entries), default=now_iso()),
        "status": manifest_status,
        "source_count": len(all_sources),
        "selected_source_count": len(selected_sources),
        "selected_source_ids": sorted(selected_ids),
        "manifest_entry_count": len(entries),
        "snapshot_content_fingerprint": registry_fingerprint(normalized_hashes),
        "sources": entries,
    }
    write_json(snapshot_dir / "manifest.json", manifest)
    (snapshot_dir / "fetch_log.md").write_text("\n".join(fetch_log) + "\n", encoding="utf-8")
    _write_integrity_report(snapshot_dir, registry, entries)
    return snapshot_dir


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sources", type=Path, required=True)
    parser.add_argument("--snapshot-root", type=Path)
    parser.add_argument("--source-id", action="append")
    parser.add_argument("--force-refresh", action="store_true")
    parser.add_argument("--browser-fallback", action="store_true")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    snapshot = create_snapshot(
        args.sources,
        args.snapshot_root,
        source_ids=set(args.source_id or []),
        force_refresh=args.force_refresh,
        browser_fallback=args.browser_fallback,
    )
    print(snapshot)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
