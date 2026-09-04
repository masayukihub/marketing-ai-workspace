#!/usr/bin/env python3
"""Compatibility adapter for the repository-wide Codex Runtime verifier."""

from __future__ import annotations

import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "scripts"))

from runtime_contract import resolve_codex_home  # noqa: E402
from verify_codex_runtime import verify_runtime  # noqa: E402


def main() -> int:
    result = verify_runtime(
        ROOT,
        ROOT / "runtime/skill-lock.json",
        resolve_codex_home(),
        selected_skills={"project-memory-manager"},
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["status"] == "RUNTIME_IN_SYNC" else 2


if __name__ == "__main__":
    sys.exit(main())
