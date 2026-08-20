#!/usr/bin/env python3
"""Inventory every supported campaign data file and workbook sheet."""

from __future__ import annotations

import argparse
from pathlib import Path

from common import configure_logging, inventory_dataframe, scan_input_directory, write_json


def inspect_files(input_dir: Path, output_dir: Path) -> Path:
    tables = scan_input_directory(input_dir)
    inventory = inventory_dataframe(tables)
    output_dir.mkdir(parents=True, exist_ok=True)
    csv_path = output_dir / "source_inventory.csv"
    inventory.to_csv(csv_path, index=False, encoding="utf-8-sig")
    write_json(output_dir / "source_inventory.json", inventory.to_dict(orient="records"))
    return csv_path


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-dir", type=Path, default=Path("."), help="Directory containing campaign source files")
    parser.add_argument("--output-dir", type=Path, default=Path("output/_intermediate"), help="Directory for inventory files")
    parser.add_argument("--verbose", action="store_true")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    configure_logging(args.verbose)
    path = inspect_files(args.input_dir.resolve(), args.output_dir.resolve())
    print(path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
