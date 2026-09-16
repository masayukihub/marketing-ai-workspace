#!/usr/bin/env python3
"""Build deterministic repository Skill inventory and generated Skill catalog."""

from __future__ import annotations

import argparse
import csv
import io
import sys
from pathlib import Path

import yaml

from runtime_contract import load_skill_lock, repository_file_hashes, tree_hash


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_LOCK = ROOT / "runtime/skill-lock.json"
DEFAULT_INVENTORY = ROOT / "inventory/skill_inventory.csv"
DEFAULT_CATALOG = ROOT / "docs/SKILL_CATALOG.md"
FIELDS = [
    "skill_name",
    "repository_path",
    "role",
    "user_visible",
    "runtime_locked",
    "repository_tree_hash",
    "global_mirror_path",
    "mirror_required",
    "mirror_status",
    "skill_md",
    "agents",
    "references",
    "scripts",
    "tests",
    "runtime_authority",
    "last_verified_commit",
    "recommended_action",
]


def skill_frontmatter(path: Path) -> dict:
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---\n"):
        return {}
    _, frontmatter, _ = text.split("---", 2)
    value = yaml.safe_load(frontmatter)
    return value if isinstance(value, dict) else {}


def build_rows(workspace: Path, lock_path: Path) -> list[dict[str, str]]:
    lock = load_skill_lock(lock_path)
    locked = {item["name"]: item for item in lock["skills"]}
    rows: list[dict[str, str]] = []
    for skill_md in sorted((workspace / "skills").glob("*/SKILL.md")):
        directory = skill_md.parent
        repository_path = directory.relative_to(workspace).as_posix()
        metadata = skill_frontmatter(skill_md)
        name = str(metadata.get("name") or directory.name)
        lock_entry = locked.get(name)
        hashes = repository_file_hashes(workspace, repository_path)
        is_locked = lock_entry is not None
        mirror_required = bool(lock_entry and lock_entry.get("mirror_required"))
        rows.append({
            "skill_name": name,
            "repository_path": repository_path,
            "role": lock_entry["role"] if lock_entry else "repository_skill_unlocked",
            "user_visible": str(bool(lock_entry and lock_entry.get("user_visible"))).lower(),
            "runtime_locked": str(is_locked).lower(),
            "repository_tree_hash": tree_hash(hashes),
            "global_mirror_path": f"$CODEX_HOME/skills/{name}" if mirror_required else "",
            "mirror_required": str(mirror_required).lower(),
            "mirror_status": "verify_codex_runtime_required" if mirror_required else "not_required",
            "skill_md": "yes",
            "agents": "yes" if (directory / "agents/openai.yaml").is_file() else "no",
            "references": "yes" if (directory / "references").is_dir() else "no",
            "scripts": "yes" if (directory / "scripts").is_dir() else "no",
            "tests": "yes" if (directory / "tests").is_dir() else "no",
            "runtime_authority": "repository",
            "last_verified_commit": lock_entry["last_verified_commit"] if lock_entry else "",
            "recommended_action": (
                "verify or sync from clean main" if mirror_required
                else "keep repository-owned; add to Skill Lock only when runtime-critical"
            ),
        })
    missing_sources = sorted(set(locked) - {row["skill_name"] for row in rows})
    if missing_sources:
        raise RuntimeError(f"LOCKED_SKILL_SOURCE_MISSING:{','.join(missing_sources)}")
    return rows


def csv_text(rows: list[dict[str, str]]) -> str:
    output = io.StringIO(newline="")
    writer = csv.DictWriter(output, fieldnames=FIELDS, lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    return output.getvalue()


def catalog_text(rows: list[dict[str, str]]) -> str:
    locked = [row for row in rows if row["runtime_locked"] == "true"]
    other = [row for row in rows if row["runtime_locked"] == "false"]
    lines = [
        "# Skill Catalog",
        "",
        "> GENERATED FILE — 由 `scripts/build_skill_inventory.py` 从 `runtime/skill-lock.json` 与仓库 `skills/*/SKILL.md` 生成。不要手工维护。",
        "",
        "GitHub repository 是正式 Runtime Authority；`$CODEX_HOME/skills` 仅为安装镜像，实时状态由 `scripts/verify_codex_runtime.py` 验证。",
        "",
        "## Runtime-locked Skills",
        "",
        "| Skill | Role | User-visible | Mirror | Repository path |",
        "| --- | --- | --- | --- | --- |",
    ]
    for row in locked:
        lines.append(
            f"| `{row['skill_name']}` | `{row['role']}` | {row['user_visible']} | {row['mirror_status']} | `{row['repository_path']}` |"
        )
    lines.extend([
        "",
        "## Other repository Skills",
        "",
        "这些目录拥有仓库源码与 `SKILL.md`，但尚未进入 Runtime Lock；它们不是由本机安装状态反向认定的正式 Runtime。",
        "",
        "| Skill | Repository path | Lock status |",
        "| --- | --- | --- |",
    ])
    for row in other:
        lines.append(f"| `{row['skill_name']}` | `{row['repository_path']}` | not locked |")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workspace", default=str(ROOT))
    parser.add_argument("--lock", default=str(DEFAULT_LOCK))
    parser.add_argument("--inventory", default=str(DEFAULT_INVENTORY))
    parser.add_argument("--catalog", default=str(DEFAULT_CATALOG))
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    workspace = Path(args.workspace).resolve()
    inventory_path = Path(args.inventory).resolve()
    catalog_path = Path(args.catalog).resolve()
    try:
        rows = build_rows(workspace, Path(args.lock).resolve())
        inventory = csv_text(rows)
        catalog = catalog_text(rows)
        if args.check:
            errors = []
            if not inventory_path.is_file() or inventory_path.read_text(encoding="utf-8") != inventory:
                errors.append("SKILL_INVENTORY_OUT_OF_DATE")
                for row in rows:
                    if row["skill_name"] == "amazon-listing-creative":
                        print("EXPECTED_AMAZON_LISTING_CREATIVE_ROW=" + ",".join(row[field] for field in FIELDS))
            if not catalog_path.is_file() or catalog_path.read_text(encoding="utf-8") != catalog:
                errors.append("SKILL_CATALOG_OUT_OF_DATE")
            if errors:
                print("\n".join(errors))
                return 1
            print("SKILL_INVENTORY_REPRODUCIBLE")
            return 0
        inventory_path.parent.mkdir(parents=True, exist_ok=True)
        catalog_path.parent.mkdir(parents=True, exist_ok=True)
        inventory_path.write_text(inventory, encoding="utf-8")
        catalog_path.write_text(catalog, encoding="utf-8")
        print(f"wrote {inventory_path.relative_to(workspace)} ({len(rows)} records)")
        print(f"wrote {catalog_path.relative_to(workspace)}")
        return 0
    except (OSError, RuntimeError) as exc:
        print(f"SKILL_INVENTORY_ERROR:{exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
