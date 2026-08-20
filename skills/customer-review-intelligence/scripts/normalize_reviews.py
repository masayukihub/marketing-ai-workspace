#!/usr/bin/env python3
"""Normalize CSV/JSON records into the canonical review schema."""

from __future__ import annotations

import argparse
from pathlib import Path

from review_core import REVIEW_COLUMNS, batch_id_now, load_input_records, normalize_record, write_csv_rows


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--batch-id", default="")
    args = parser.parse_args()
    batch_id = args.batch_id or batch_id_now()
    rows = [normalize_record(row, batch_id=batch_id, raw_file_path=str(Path(args.input).resolve())) for row in load_input_records(Path(args.input))]
    write_csv_rows(Path(args.output), rows, REVIEW_COLUMNS)
    print(f"normalized={len(rows)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

