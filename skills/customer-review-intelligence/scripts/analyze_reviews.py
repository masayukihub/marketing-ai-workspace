#!/usr/bin/env python3
"""Rebuild analytical outputs from the normalized database."""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--workspace", required=True)
    parser.add_argument("--product-knowledge-dir", required=True)
    args = parser.parse_args()
    script = Path(__file__).with_name("run_review_intelligence.py")
    return subprocess.run([
        sys.executable, str(script), "--workspace", args.workspace,
        "--product-knowledge-dir", args.product_knowledge_dir, "--analyze-only",
    ]).returncode


if __name__ == "__main__":
    raise SystemExit(main())

