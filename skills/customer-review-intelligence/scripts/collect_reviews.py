#!/usr/bin/env python3
"""Collect configured public review pages and immutable raw manifests."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from review_core import batch_id_now, collect_public_pages, load_yaml


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--workspace", required=True)
    parser.add_argument("--products", default="")
    parser.add_argument("--modules", default="ec")
    parser.add_argument("--batch-id", default="")
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    workspace = Path(args.workspace).resolve()
    records, manifest = collect_public_pages(
        workspace,
        load_yaml(workspace / "config" / "products.yaml"),
        load_yaml(workspace / "config" / "sources.yaml"),
        {item for item in args.products.split(",") if item},
        {item for item in args.modules.split(",") if item},
        args.batch_id or batch_id_now(),
    )
    Path(args.output).write_text(json.dumps({"records": records, "manifest": manifest}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"records={len(records)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

