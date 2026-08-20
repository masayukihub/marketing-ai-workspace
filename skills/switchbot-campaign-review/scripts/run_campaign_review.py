#!/usr/bin/env python3
"""Fetch Feishu sources into a snapshot, then run the existing review engine."""

from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path

from build_report import build_report
from common import configure_logging
from create_source_snapshot import create_snapshot
from feishu_common import file_sha256, load_registry, registry_fingerprint


def _resolve_snapshot(value: Path) -> Path:
    path = value.resolve()
    if path.is_file() and path.name == "manifest.json":
        path = path.parent
    if not (path / "manifest.json").is_file():
        raise FileNotFoundError(f"Snapshot manifest not found: {path / 'manifest.json'}")
    if not (path / "normalized").is_dir():
        raise FileNotFoundError(f"Snapshot normalized directory not found: {path / 'normalized'}")
    return path


def _validate_snapshot_registry(snapshot: Path, sources: Path) -> dict:
    manifest = json.loads((snapshot / "manifest.json").read_text(encoding="utf-8"))
    current_fingerprint = registry_fingerprint(load_registry(sources.resolve()))
    snapshot_fingerprint = manifest.get("source_registry_fingerprint") or manifest.get("registry_fingerprint")
    if snapshot_fingerprint != current_fingerprint:
        raise ValueError(
            "Snapshot/source registry mismatch: use --force-refresh or the registry that created this snapshot"
        )
    normalized_hashes: dict[str, str] = {}
    declared_files: set[str] = set()
    hashed_files: set[str] = set()
    for entry in manifest.get("sources", []):
        expected_hashes = entry.get("normalized_sha256") or {}
        declared_files.update(str(path) for path in entry.get("normalized_file", []))
        for relative_path, expected in expected_hashes.items():
            hashed_files.add(str(relative_path))
            target = snapshot / relative_path
            if not target.is_file():
                raise ValueError(f"Snapshot normalized file is missing: {relative_path}")
            actual = file_sha256(target)
            if actual != expected:
                raise ValueError(f"Snapshot normalized file checksum mismatch: {relative_path}")
            normalized_hashes[f"{entry.get('source_id')}:{relative_path}"] = actual
    actual_files = {
        str(path.relative_to(snapshot))
        for path in (snapshot / "normalized").rglob("*")
        if path.is_file()
    }
    if declared_files != hashed_files or declared_files != actual_files:
        raise ValueError(
            "Snapshot normalized file set mismatch: manifest declarations, checksums, and directory contents must match"
        )
    expected_fingerprint = manifest.get("snapshot_content_fingerprint")
    if expected_fingerprint != registry_fingerprint(normalized_hashes):
        raise ValueError("Snapshot content fingerprint mismatch")
    return manifest


def _prepare_fetch_only_output(output_dir: Path, snapshot: Path) -> Path:
    output_dir = output_dir.resolve()
    if output_dir.exists() and any(output_dir.iterdir()):
        raise FileExistsError(f"Output directory is not empty; refusing to overwrite: {output_dir}")
    output_dir.mkdir(parents=True, exist_ok=True)
    shutil.copy2(snapshot / "source_integrity_report.md", output_dir / "source_integrity_report.md")
    (output_dir / "snapshot_pointer.json").write_text(
        json.dumps({"snapshot": str(snapshot)}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return output_dir


def run_campaign_review(
    *,
    sources: Path,
    output_dir: Path,
    fetch_only: bool = False,
    analyze_only: bool = False,
    snapshot: Path | None = None,
    force_refresh: bool = False,
    source_ids: set[str] | None = None,
    browser_fallback: bool = False,
    language: str = "zh-CN",
    mapping_file: Path | None = None,
    current_period: str | None = None,
    comparison_period: str | None = None,
    currency: str | None = None,
    product_knowledge_dir: Path | None = None,
    snapshot_root: Path | None = None,
) -> Path:
    sources = sources.resolve()
    registry = load_registry(sources)
    if analyze_only:
        if snapshot is None:
            raise ValueError("--analyze-only requires --snapshot")
        snapshot_dir = _resolve_snapshot(snapshot)
        manifest = _validate_snapshot_registry(snapshot_dir, sources)
    elif snapshot is not None and not force_refresh:
        snapshot_dir = _resolve_snapshot(snapshot)
        manifest = _validate_snapshot_registry(snapshot_dir, sources)
    else:
        snapshot_dir = create_snapshot(
            sources,
            snapshot_root=snapshot_root,
            source_ids=source_ids,
            force_refresh=force_refresh,
            browser_fallback=browser_fallback,
        )
        manifest = json.loads((snapshot_dir / "manifest.json").read_text(encoding="utf-8"))
    if fetch_only:
        return _prepare_fetch_only_output(output_dir, snapshot_dir)

    normalized_files = [path for path in (snapshot_dir / "normalized").rglob("*") if path.is_file()]
    if not normalized_files:
        _prepare_fetch_only_output(output_dir, snapshot_dir)
        raise RuntimeError(
            "No analyzable normalized files were captured; source integrity report was generated"
        )
    campaign_name = str(registry.get("project", {}).get("name") or sources.stem)
    result = build_report(
        input_dir=snapshot_dir / "normalized",
        campaign_name=campaign_name,
        output_dir=output_dir,
        language=language,
        mapping_file=mapping_file,
        currency=currency or registry.get("project", {}).get("currency"),
        current_period=current_period,
        comparison_period=comparison_period,
        product_knowledge_dir=product_knowledge_dir,
        snapshot_manifest=snapshot_dir / "manifest.json",
    )
    shutil.copy2(snapshot_dir / "source_integrity_report.md", result / "source_integrity_report.md")
    run_manifest_path = result / "_intermediate" / "run_manifest.json"
    run_manifest = json.loads(run_manifest_path.read_text(encoding="utf-8"))
    run_manifest["source_snapshot"]["source_integrity_report"] = str(
        (result / "source_integrity_report.md").resolve()
    )
    run_manifest["source_snapshot"]["manifest_status"] = manifest.get("status")
    run_manifest_path.write_text(
        json.dumps(run_manifest, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return result


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sources", type=Path, required=True)
    parser.add_argument("--output", type=Path, default=Path("output"))
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--fetch-only", action="store_true")
    mode.add_argument("--analyze-only", action="store_true")
    parser.add_argument("--snapshot", type=Path)
    parser.add_argument("--snapshot-root", type=Path)
    parser.add_argument("--force-refresh", action="store_true")
    parser.add_argument("--source-id", action="append")
    parser.add_argument("--browser-fallback", action="store_true")
    parser.add_argument("--language", default="zh-CN")
    parser.add_argument("--mapping-file", type=Path)
    parser.add_argument("--current-period")
    parser.add_argument("--comparison-period")
    parser.add_argument("--currency")
    parser.add_argument("--product-knowledge-dir", type=Path)
    parser.add_argument("--verbose", action="store_true")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    configure_logging(args.verbose)
    try:
        output = run_campaign_review(
            sources=args.sources,
            output_dir=args.output,
            fetch_only=args.fetch_only,
            analyze_only=args.analyze_only,
            snapshot=args.snapshot,
            force_refresh=args.force_refresh,
            source_ids=set(args.source_id or []),
            browser_fallback=args.browser_fallback,
            language=args.language,
            mapping_file=args.mapping_file,
            current_period=args.current_period,
            comparison_period=args.comparison_period,
            currency=args.currency,
            product_knowledge_dir=args.product_knowledge_dir,
            snapshot_root=args.snapshot_root,
        )
    except (FileNotFoundError, FileExistsError, ValueError, RuntimeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    print(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
