#!/usr/bin/env python3
"""Export a Feishu document as Markdown and structured raw JSON."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any

from feishu_common import (
    CommandRunner,
    FetchError,
    FetchResult,
    envelope_data,
    now_iso,
    relative_to,
    run_lark_cli,
    safe_name,
    write_json,
)

MEDIA_PATTERN = re.compile(r"<(?:img|source|whiteboard)\b[^>]*(?:token|url)=[\"'][^\"']+[\"'][^>]*>")


def export_document(
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

    structured = runner(
        [
            "docs",
            "+fetch",
            "--doc",
            source_url,
            "--doc-format",
            "xml",
            "--detail",
            "with-ids",
            "--scope",
            "full",
            "--as",
            "user",
            "--format",
            "json",
        ],
        raw_dir,
    )
    markdown_payload = runner(
        [
            "docs",
            "+fetch",
            "--doc",
            source_url,
            "--doc-format",
            "markdown",
            "--detail",
            "simple",
            "--scope",
            "full",
            "--as",
            "user",
            "--format",
            "json",
        ],
        raw_dir,
    )
    raw_json = raw_dir / "document_structured.json"
    write_json(raw_json, structured)
    write_json(raw_dir / "document_markdown_response.json", markdown_payload)
    structured_doc = envelope_data(structured).get("document") or envelope_data(structured)
    markdown_doc = envelope_data(markdown_payload).get("document") or envelope_data(markdown_payload)
    content = markdown_doc.get("content") if isinstance(markdown_doc, dict) else None
    if not isinstance(content, str):
        raise FetchError("Document export returned no Markdown content", status="Partial")
    normalized = normalized_dir / f"{safe_name(source_id)}.md"
    normalized.write_text(content, encoding="utf-8")
    structured_content = structured_doc.get("content", "") if isinstance(structured_doc, dict) else ""
    media_refs = MEDIA_PATTERN.findall(str(structured_content))
    write_json(raw_dir / "media_references.json", media_refs)
    document_name = (
        structured_doc.get("title")
        if isinstance(structured_doc, dict)
        else None
    ) or source_name
    return [
        FetchResult(
            source_id=source_id,
            source_name=source_name,
            source_url=source_url,
            source_type="docx",
            retrieval_method="lark-cli",
            retrieval_time=now_iso(),
            status="Complete with Warnings" if media_refs else "Complete",
            document_name=str(document_name),
            warning=(
                ["Media references were recorded but binary media was not used as analytical data."]
                if media_refs
                else []
            ),
            snapshot_file=[
                relative_to(raw_json, snapshot_dir),
                relative_to(raw_dir / "media_references.json", snapshot_dir),
            ],
            normalized_file=[relative_to(normalized, snapshot_dir)],
            metadata={
                "revision_id": structured_doc.get("revision_id") if isinstance(structured_doc, dict) else None,
                "heading_hierarchy_preserved": True,
                "tables_preserved_as_markdown": True,
                "media_reference_count": len(media_refs),
            },
        )
    ]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--url", required=True)
    parser.add_argument("--source-id", default="docx")
    parser.add_argument("--source-name", default="Feishu Document")
    parser.add_argument("--snapshot-dir", type=Path, required=True)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    results = export_document(
        {"id": args.source_id, "name": args.source_name, "url": args.url},
        args.snapshot_dir.resolve(),
    )
    print(json.dumps([item.as_manifest_entry() for item in results], ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
