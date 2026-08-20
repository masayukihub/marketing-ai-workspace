#!/usr/bin/env python3
"""Build a non-sensitive inventory of selected source Skills."""

from __future__ import annotations

import csv
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCES = [
    ("amazon-japan-pdp-generator", Path("/Users/lai/.codex/skills/amazon-japan-pdp-generator"), "migrated"),
    ("edm-generator", Path("/Users/lai/Documents/marketing/edm-visual-generator"), "curated migration"),
    ("product-knowledge", Path("/Users/lai/.codex/skills/product-knowledge"), "migrated"),
    ("switchbot-campaign-review", Path("/Users/lai/Documents/marketing/.agents/skills/switchbot-campaign-review"), "migrated"),
    ("customer-review-intelligence", Path("/Users/lai/Documents/marketing/.agents/skills/customer-review-intelligence"), "migrated"),
    ("amazon-listing-creative", Path("/Users/lai/.codex/skills/amazon-listing-creative"), "migrated"),
    ("project-memory-manager", Path("/Users/lai/.codex/skills/project-memory-manager"), "migrated"),
    ("influencer-marketing", Path("/Users/lai/Documents/marketing/.agents/skills/influencer-marketing"), "migrated"),
    ("kol-database", Path("/Users/lai/Documents/homerun pet/homerunpet_japan_project/KOL_Master.xlsx"), "not migrated: personal-data review required"),
]


def flag(path: Path, name: str) -> str:
    return "yes" if (path / name).exists() else "no"


def main() -> None:
    rows = []
    for name, path, migration in SOURCES:
        is_dir = path.is_dir()
        stat = path.stat() if path.exists() else None
        rows.append({
            "skill_name": name,
            "source_path": str(path),
            "last_modified": datetime.fromtimestamp(stat.st_mtime).isoformat(timespec="seconds") if stat else "Not Available",
            "readme": flag(path, "README.md") if is_dir else "no",
            "skill_md": flag(path, "SKILL.md") if is_dir else "no",
            "references": flag(path, "references") if is_dir else "no",
            "scripts": flag(path, "scripts") if is_dir else "no",
            "tests": flag(path, "tests") if is_dir else "no",
            "migration_status": migration,
        })
    target = ROOT / "inventory/skill_inventory.csv"
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)
    print(f"wrote {target.relative_to(ROOT)} ({len(rows)} records)")


if __name__ == "__main__":
    main()
