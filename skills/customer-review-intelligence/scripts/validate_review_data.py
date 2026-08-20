#!/usr/bin/env python3
"""Validate canonical review data and write an auditable issue report."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from review_core import load_product_index, read_csv_rows, validate_rows


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--product-index", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    issues = validate_rows(read_csv_rows(Path(args.input)), load_product_index(Path(args.product_index)))
    Path(args.output).write_text(json.dumps(issues, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"issues={len(issues)} critical={sum(item['severity'] == 'Critical' for item in issues)}")
    return 1 if any(item["severity"] == "Critical" for item in issues) else 0


if __name__ == "__main__":
    raise SystemExit(main())

