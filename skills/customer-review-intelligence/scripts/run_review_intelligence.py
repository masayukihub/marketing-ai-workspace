#!/usr/bin/env python3
"""Run the end-to-end Customer Review Intelligence pipeline."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from review_core import (
    REVIEW_COLUMNS, batch_id_now, classify_rows, collect_public_pages,
    load_input_records, load_product_index, load_yaml, map_products,
    merge_incremental, normalize_record, now_iso, read_csv_rows, validate_rows,
    write_reports,
)


def latest_manifest(workspace: Path) -> dict:
    paths = list((workspace / "raw").glob("manifest-*.json"))
    if not paths:
        return {"batch_id": "analysis-only", "collected_at": now_iso(), "coverage": [], "files": []}
    return json.loads(max(paths, key=lambda path: path.stat().st_mtime_ns).read_text(encoding="utf-8"))


def main() -> int:
    parser = argparse.ArgumentParser(description="Collect and analyze auditable Japanese VOC.")
    parser.add_argument("--workspace", required=True)
    parser.add_argument("--config-dir", default="", help="Shared configuration directory; defaults to <workspace>/config.")
    parser.add_argument("--product-knowledge-dir", required=True)
    parser.add_argument("--mode", choices=["full", "incremental"], default="incremental")
    parser.add_argument("--initial-full", action="store_true", help="Alias for the first full-history run.")
    parser.add_argument("--modules", default="ec,sns,kol,pr,official,competitor")
    parser.add_argument("--products", default="")
    parser.add_argument("--date-from", default="", help="Requested inclusive review-date boundary (YYYY-MM-DD).")
    parser.add_argument("--date-to", default="", help="Requested inclusive review-date boundary (YYYY-MM-DD).")
    parser.add_argument("--input", action="append", default=[])
    parser.add_argument("--input-manifest", default="", help="Audited manifest to preserve when importing compiled snapshots.")
    parser.add_argument("--analyze-only", action="store_true")
    parser.add_argument("--batch-id", default="")
    parser.add_argument("--output-dir", default="", help="Optional report output directory; database remains in workspace.")
    args = parser.parse_args()

    workspace = Path(args.workspace).resolve()
    skill_dir = Path(__file__).resolve().parents[1]
    product_knowledge_dir = Path(args.product_knowledge_dir).resolve()
    workspace.mkdir(parents=True, exist_ok=True)
    if args.initial_full:
        args.mode = "full"
    batch_id = args.batch_id or batch_id_now()
    selected_modules = {item.strip() for item in args.modules.split(",") if item.strip()}
    selected_products = {item.strip() for item in args.products.split(",") if item.strip()}
    config_dir = Path(args.config_dir).resolve() if args.config_dir else workspace / "config"
    products_config = load_yaml(config_dir / "products.yaml")
    sources_config = load_yaml(config_dir / "sources.yaml")
    sentiment_rules = load_yaml(config_dir / "sentiment_rules.yaml")
    taxonomy = load_yaml(config_dir / "taxonomy.yaml")
    product_index = load_product_index(product_knowledge_dir / "outputs" / "product_index.json")
    state_path = workspace / "state" / "last_success.json"
    prior_state = json.loads(state_path.read_text(encoding="utf-8")) if state_path.exists() else {}

    raw_records: list[dict] = []
    if args.analyze_only:
        manifest = latest_manifest(workspace)
    elif args.input:
        manifest_path = workspace / "raw" / f"manifest-{batch_id}.json"
        if args.input_manifest:
            manifest = json.loads(Path(args.input_manifest).resolve().read_text(encoding="utf-8"))
            coverage = list(manifest.get("coverage", []))
            files = list(manifest.get("files", []))
        elif manifest_path.exists():
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            coverage = list(manifest.get("coverage", []))
            files = list(manifest.get("files", []))
        else:
            coverage = []
            files = []
        for input_name in args.input:
            path = Path(input_name).resolve()
            imported = load_input_records(path)
            raw_records.extend(imported)
            import_status = (
                "Partial"
                if any(row.get("coverage_status") in {"Partial", "Blocked", "Incomplete"} for row in imported)
                else "Complete"
            )
            if not args.input_manifest:
                coverage.append({
                "product_id": "multiple",
                "source": "user_import",
                "module": "import",
                "url": str(path),
                "required": True,
                "coverage_status": import_status,
                "records": len(imported),
                "http_status": "",
                "failure_reason": "",
                "pagination_boundary": "User-provided file",
                })
        manifest = dict(manifest) if args.input_manifest else {
            "schema_version": "1.0", "batch_id": batch_id, "collected_at": now_iso(),
            "coverage": coverage, "files": files,
        }
        manifest["batch_id"] = batch_id
        manifest_path.parent.mkdir(parents=True, exist_ok=True)
        manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    else:
        raw_records, manifest = collect_public_pages(
            workspace, products_config, sources_config,
            selected_products, selected_modules, batch_id,
        )
    manifest["requested_window"] = {
        "date_from": args.date_from or prior_state.get("collection_cutoff", ""),
        "date_to": args.date_to,
        "prior_success_batch": prior_state.get("batch_id", ""),
    }
    if not args.analyze_only:
        manifest_path = workspace / "raw" / f"manifest-{batch_id}.json"
        manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    if args.analyze_only:
        current = read_csv_rows(workspace / "normalized" / "reviews.csv")
        refreshed = classify_rows(map_products(current, product_index), sentiment_rules, taxonomy)
        canonical, _, _ = merge_incremental(workspace, refreshed)
        counts = {"new": 0, "updated": 0, "unchanged": len(canonical)}
    else:
        normalized = [
            normalize_record(
                record,
                batch_id=batch_id,
                raw_file_path=record.get("_raw_file_path", args.input[0] if len(args.input) == 1 else ""),
                default_source=record.get("source", "user_import"),
                default_product_id=record.get("product_id", ""),
                coverage_status=record.get("coverage_status", "Complete"),
            )
            for record in raw_records
        ]
        if args.date_from or args.date_to:
            def in_window(row: dict[str, str]) -> bool:
                value = row.get("review_date", "")[:10]
                if not value:
                    return True
                return (not args.date_from or value >= args.date_from) and (not args.date_to or value <= args.date_to)
            normalized = [row for row in normalized if in_window(row)]
        mapped = map_products(normalized, product_index)
        classified = classify_rows(mapped, sentiment_rules, taxonomy)
        canonical, _, counts = merge_incremental(workspace, classified)

    issues = validate_rows(canonical, product_index)
    outputs = write_reports(
        workspace, canonical, manifest, counts, issues,
        skill_dir / "assets" / "report_template.html",
        Path(args.output_dir).resolve() if args.output_dir else None,
        persist_state=not args.analyze_only,
    )
    result = {
        "ok": not any(issue["severity"] == "Critical" for issue in issues),
        "mode": args.mode,
        "batch_id": batch_id,
        "records": len(canonical),
        "incremental": counts,
        "critical_issues": sum(issue["severity"] == "Critical" for issue in issues),
        "outputs": {key: str(value) for key, value in outputs.items()},
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
