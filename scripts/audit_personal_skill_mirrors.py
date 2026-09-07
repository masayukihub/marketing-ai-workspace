#!/usr/bin/env python3
"""Read-only audit of repository entry skills installed in a personal skill catalog.

This checks instruction packages, not renderer availability or production readiness.
The existing verify_codex_runtime.py remains authoritative for named CLI mirrors.
"""

from __future__ import annotations

import argparse
import copy
import json
import re
from pathlib import Path, PurePosixPath

import yaml

from runtime_contract import (
    RuntimeContractError, compare_hashes, load_skill_lock,
    repository_file_hashes, sha256_file, tree_hash,
)

ROOT = Path(__file__).resolve().parents[1]
UI_PRODUCTS = {"chatgpt", "codex", "api", "atlas"}
ICON_FIELDS = ("icon_small", "icon_large")


class UniqueLoader(yaml.SafeLoader):
    pass


def unique_mapping(loader, node, deep=False):
    result = {}
    for key_node, value_node in node.value:
        key = loader.construct_object(key_node, deep=deep)
        if key in result:
            raise RuntimeContractError("DUPLICATE_YAML_KEY")
        result[key] = loader.construct_object(value_node, deep=deep)
    return result


UniqueLoader.add_constructor(yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, unique_mapping)


def read_yaml(path: Path, frontmatter=False):
    if path.is_symlink() or not path.is_file() or path.stat().st_size > 128 * 1024:
        raise RuntimeContractError("INVALID_METADATA_FILE")
    text = path.read_text(encoding="utf-8")
    if frontmatter:
        match = re.match(r"\A---\r?\n(.*?)\r?\n---(?:\r?\n|\Z)", text, re.S)
        if not match:
            raise RuntimeContractError("INVALID_SKILL_FRONTMATTER")
        text = match.group(1)
    value = yaml.load(text, Loader=UniqueLoader)
    if not isinstance(value, dict):
        raise RuntimeContractError("METADATA_MUST_BE_MAPPING")
    return value


def catalog_entries(root: Path):
    active, disabled = {}, {}
    if root.is_symlink() or not root.is_dir():
        raise RuntimeContractError("PERSONAL_SKILLS_ROOT_MISSING_OR_UNSAFE")
    for parent, output in ((root, active), (root / "uninstalled", disabled)):
        if parent.is_symlink():
            raise RuntimeContractError("SYMLINK_CATALOG_DIRECTORY")
        if not parent.exists():
            continue
        for directory in sorted(parent.iterdir()):
            if directory.name.startswith(".") or directory.name == "uninstalled":
                continue
            if directory.is_symlink():
                raise RuntimeContractError("SYMLINK_SKILL_DIRECTORY")
            skill_md = directory / "SKILL.md"
            if not directory.is_dir() or not skill_md.exists():
                continue
            name = read_yaml(skill_md, frontmatter=True).get("name")
            if not isinstance(name, str) or not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", name):
                raise RuntimeContractError("INVALID_SKILL_NAME")
            output.setdefault(name, []).append(directory)
    return active, disabled


def personal_hashes(root: Path):
    hashes = {}
    for path in sorted(root.rglob("*")):
        relative = path.relative_to(root)
        if path.is_symlink():
            raise RuntimeContractError("SYMLINK_PERSONAL_SKILL_FILE")
        if any(part in {".git", "__pycache__", ".pytest_cache"} for part in relative.parts):
            continue
        if path.is_file():
            hashes[relative.as_posix()] = sha256_file(path)
    return hashes


def normalize_ui(source: Path, target: Path, expected, actual):
    """Allow only catalog icon assets and the known catalog product list.

    All instructions, scripts, references, prompts, dependency declarations and
    allow_implicit_invocation remain authoritative and are compared unchanged.
    """
    metadata = "agents/openai.yaml"
    if metadata not in expected or metadata not in actual:
        return []
    source_yaml = read_yaml(source / metadata)
    target_yaml = read_yaml(target / metadata)
    normalized = copy.deepcopy(target_yaml)
    source_interface = source_yaml.get("interface", {})
    target_interface = normalized.get("interface", {})
    if not isinstance(source_interface, dict) or not isinstance(target_interface, dict):
        raise RuntimeContractError("INVALID_UI_INTERFACE")
    icon_paths = set()
    for field in ICON_FIELDS:
        value = target_interface.get(field)
        if value is None:
            continue
        if not isinstance(value, str) or "\\" in value:
            raise RuntimeContractError("INVALID_ICON_PATH")
        path = PurePosixPath(value)
        if path.is_absolute() or ".." in path.parts or not path.parts or path.parts[0] != "assets":
            raise RuntimeContractError("INVALID_ICON_PATH")
        relative = path.as_posix()
        if relative not in actual:
            raise RuntimeContractError("MISSING_CATALOG_ICON")
        if field not in source_interface:
            target_interface.pop(field)
        icon_paths.add(relative)
    source_policy = source_yaml.get("policy", {})
    target_policy = normalized.get("policy", {})
    if not isinstance(source_policy, dict) or not isinstance(target_policy, dict):
        raise RuntimeContractError("INVALID_UI_POLICY")
    if "products" not in source_policy and "products" in target_policy:
        products = target_policy["products"]
        if not isinstance(products, list) or any(not isinstance(item, str) for item in products):
            raise RuntimeContractError("INVALID_CATALOG_PRODUCTS")
        if len(products) != len(UI_PRODUCTS) or set(products) != UI_PRODUCTS:
            raise RuntimeContractError("UNEXPECTED_CATALOG_PRODUCTS")
        target_policy.pop("products")
    if normalized != source_yaml:
        return []
    actual[metadata] = expected[metadata]
    allowed = []
    for relative in sorted(icon_paths - expected.keys()):
        actual.pop(relative)
        allowed.append(relative)
    return allowed


def audit(workspace: Path, lock_path: Path, personal_root: Path, selected=None):
    lock = load_skill_lock(lock_path)
    entries = [item for item in lock["skills"] if item.get("user_visible") is True]
    names = {item["name"] for item in entries}
    if selected and not set(selected).issubset(names):
        raise RuntimeContractError("SELECTION_REQUIRES_LOCKED_USER_ENTRY")
    active, disabled = catalog_entries(personal_root)
    rows = []
    for entry in entries:
        name = entry["name"]
        if selected and name not in selected:
            continue
        source = workspace / entry["repository_path"]
        row = {"name": name, "status": "PERSONAL_ENTRY_MISSING"}
        if source.is_symlink() or any(path.is_symlink() for path in source.rglob("*")):
            raise RuntimeContractError("SYMLINK_REPOSITORY_SKILL_FILE")
        expected = repository_file_hashes(workspace, entry["repository_path"])
        if tree_hash(expected) != entry["repository_tree_hash"] or any(
            path not in expected for path in entry["required_runtime_files"]
        ):
            row["status"] = "REPOSITORY_LOCK_MISMATCH"
        elif len(active.get(name, [])) > 1 or (name in active and name in disabled):
            row["status"] = "PERSONAL_ENTRY_AMBIGUOUS"
        elif name not in active and name in disabled:
            row["status"] = "PERSONAL_ENTRY_DISABLED"
        elif name in active:
            target = active[name][0]
            actual = personal_hashes(target)
            row["catalog_ui_assets"] = normalize_ui(source, target, expected, actual)
            row["mismatches"] = compare_hashes(expected, actual)
            row["status"] = "PERSONAL_ENTRY_IN_SYNC" if not row["mismatches"] else "PERSONAL_ENTRY_DRIFT"
        rows.append(row)
    if not rows:
        raise RuntimeContractError("NO_LOCKED_USER_ENTRIES")
    return {
        "status": "PERSONAL_ENTRIES_IN_SYNC" if all(
            row["status"] == "PERSONAL_ENTRY_IN_SYNC" for row in rows
        ) else "PERSONAL_ENTRIES_NEED_ATTENTION",
        "verification_scope": "personal_entry_packages_only",
        "runtime_execution_verified": False,
        "writes_performed": False,
        "skills": rows,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workspace", type=Path, default=ROOT)
    parser.add_argument("--lock", type=Path)
    parser.add_argument("--personal-skills-root", type=Path, required=True)
    parser.add_argument("--skill", action="append", default=[])
    args = parser.parse_args()
    try:
        result = audit(args.workspace.resolve(), args.lock or args.workspace / "runtime/skill-lock.json",
                       args.personal_skills_root.expanduser(), set(args.skill) or None)
    except (OSError, ValueError, TypeError, RecursionError, yaml.YAMLError, RuntimeContractError):
        # Do not echo source bodies or malformed metadata values into logs.
        result = {"status": "PERSONAL_AUDIT_BLOCKED", "writes_performed": False,
                  "runtime_execution_verified": False,
                  "error": "Invalid source lock, catalog metadata, or unsafe/missing path."}
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["status"] == "PERSONAL_ENTRIES_IN_SYNC" else 2


if __name__ == "__main__":
    raise SystemExit(main())
