#!/usr/bin/env python3
"""Assign duplicate groups without deleting evidence."""

from __future__ import annotations

import argparse
from pathlib import Path

from review_core import REVIEW_COLUMNS, assign_duplicates, read_csv_rows, write_csv_rows


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    rows = assign_duplicates(read_csv_rows(Path(args.input)))
    write_csv_rows(Path(args.output), rows, REVIEW_COLUMNS)
    print(f"duplicates={sum(bool(row.get('duplicate_type')) for row in rows)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

