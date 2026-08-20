#!/usr/bin/env python3
"""Validate screenshot/DOM browser captures before VOC import."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path


def digest(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    manifest_path = Path(args.manifest).resolve()
    payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    findings: list[dict[str, str]] = []

    def add(severity: str, code: str, message: str) -> None:
        findings.append({"severity": severity, "code": code, "message": message})

    source = str(payload.get("source") or "")
    frames = payload.get("frames") or []
    if source not in {"amazon_jp", "youtube", "x"}:
        add("Critical", "SOURCE_INVALID", "Browser capture source must be amazon_jp, youtube, or x.")
    if not payload.get("batch_id") or not payload.get("product_id"):
        add("Critical", "IDENTITY_MISSING", "batch_id and product_id are required.")
    if not frames:
        add("Critical", "FRAMES_MISSING", "At least one capture frame is required.")

    seen_frame_ids: set[str] = set()
    seen_record_ids: set[str] = set()
    duplicate_visible_ids: set[str] = set()
    for number, frame in enumerate(frames, 1):
        frame_id = str(frame.get("frame_id") or "")
        if not frame_id or frame_id in seen_frame_ids:
            add("Critical", "FRAME_ID_INVALID", f"Frame {number} has a missing or duplicate frame_id.")
        seen_frame_ids.add(frame_id)
        if not str(frame.get("url") or "").startswith("http"):
            add("Critical", "URL_MISSING", f"Frame {number} lacks an auditable HTTP(S) URL.")
        captured_at = str(frame.get("captured_at") or "")
        if not re.match(r"^20\d{2}-\d{2}-\d{2}T", captured_at):
            add("High", "CAPTURE_TIME_INVALID", f"Frame {number} captured_at is missing or invalid.")
        for kind, path_field, hash_field in (
            ("screenshot", "screenshot_path", "screenshot_sha256"),
            ("DOM snapshot", "dom_snapshot_path", "dom_snapshot_sha256"),
        ):
            raw_path = str(frame.get(path_field) or "")
            path = Path(raw_path) if raw_path else None
            if not path or not path.exists():
                add("Critical", "EVIDENCE_FILE_MISSING", f"Frame {number} {kind} is missing: {raw_path}")
                continue
            expected = str(frame.get(hash_field) or "")
            actual = digest(path)
            if not expected or expected != actual:
                add("Critical", "HASH_MISMATCH", f"Frame {number} {kind} SHA-256 does not match.")
        ids = [str(value) for value in (frame.get("unique_ids_visible") or []) if str(value)]
        for record_id in ids:
            if record_id in seen_record_ids:
                duplicate_visible_ids.add(record_id)
            seen_record_ids.add(record_id)
        if frame.get("status") not in {"Captured", "Partial", "Blocked", "Failed"}:
            add("High", "FRAME_STATUS_INVALID", f"Frame {number} has an invalid status.")

    declared_ids = {str(value) for value in (payload.get("unique_record_ids") or []) if str(value)}
    if declared_ids != seen_record_ids:
        add("High", "ID_RECONCILIATION_FAILED", f"Manifest unique_record_ids ({len(declared_ids)}) does not equal visible frame IDs ({len(seen_record_ids)}).")
    if duplicate_visible_ids:
        add("Medium", "OVERLAPPING_FRAMES", f"{len(duplicate_visible_ids)} IDs repeat across frames; deduplicate during import.")

    requested_status = str(payload.get("coverage_status") or "Partial")
    computed_status = requested_status
    if findings and any(item["severity"] == "Critical" for item in findings):
        computed_status = "Blocked"
    elif payload.get("failed_boundaries"):
        computed_status = "Partial"
    elif source == "x":
        computed_status = "Partial"
    elif not payload.get("end_reached") or not payload.get("count_reconciled"):
        computed_status = "Partial"
    elif source in {"amazon_jp", "youtube"}:
        computed_status = "Complete"
    if requested_status == "Complete" and computed_status != "Complete":
        add("High", "COMPLETE_NOT_SUPPORTED", f"Requested Complete is not supported; computed {computed_status}.")

    report = {
        "ok": not any(item["severity"] == "Critical" for item in findings),
        "source": source,
        "batch_id": payload.get("batch_id", ""),
        "frame_count": len(frames),
        "unique_visible_ids": len(seen_record_ids),
        "computed_coverage_status": computed_status,
        "findings": findings,
    }
    output = Path(args.output).resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
