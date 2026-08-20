#!/usr/bin/env python3
"""Produce explainable sentiment, topic, severity, and review-queue labels."""

from __future__ import annotations

import argparse
from pathlib import Path

from review_core import REVIEW_COLUMNS, classify_rows, load_yaml, read_csv_rows, write_csv_rows


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--sentiment-rules", required=True)
    parser.add_argument("--taxonomy", required=True)
    args = parser.parse_args()
    rows = classify_rows(read_csv_rows(Path(args.input)), load_yaml(Path(args.sentiment_rules)), load_yaml(Path(args.taxonomy)))
    write_csv_rows(Path(args.output), rows, REVIEW_COLUMNS)
    print(f"classified={len(rows)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

