#!/usr/bin/env python3
"""Build the compact review index from normalized data and a raw manifest."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from review_core import build_index, read_csv_rows


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--manifest", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    payload = build_index(read_csv_rows(Path(args.input)), json.loads(Path(args.manifest).read_text(encoding="utf-8")), {"new": 0, "updated": 0, "unchanged": 0})
    Path(args.output).write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"records": payload["record_count"], "status": payload["status"]}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

