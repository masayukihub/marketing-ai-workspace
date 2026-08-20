#!/usr/bin/env python3
"""Apply fail-closed Product Knowledge entity mapping."""

from __future__ import annotations

import argparse
from pathlib import Path

from review_core import REVIEW_COLUMNS, load_product_index, map_products, read_csv_rows, write_csv_rows


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--product-index", required=True)
    args = parser.parse_args()
    rows = map_products(read_csv_rows(Path(args.input)), load_product_index(Path(args.product_index)))
    write_csv_rows(Path(args.output), rows, REVIEW_COLUMNS)
    print(f"mapped={sum(row.get('mapping_status') == 'Confirmed' for row in rows)} total={len(rows)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

