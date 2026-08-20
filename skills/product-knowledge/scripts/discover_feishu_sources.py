#!/usr/bin/env python3
"""Discover Feishu source candidates incrementally; never import whole documents."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
from datetime import datetime
from pathlib import Path

from product_data import load_rows, normalize_alias


def default_folder(config_path: Path) -> str:
    match = re.search(r"(?m)^\s*(?:-\s*)?folder_token:\s*([^\s#]+)", config_path.read_text(encoding="utf-8"))
    if not match:
        raise ValueError("config/product_mapping.yaml has no primary source folder")
    return match.group(1)


def run(command: list[str]) -> tuple[bool, dict, str]:
    result = subprocess.run(command, text=True, capture_output=True)
    try:
        payload = json.loads(result.stdout) if result.stdout.strip() else {}
    except json.JSONDecodeError:
        payload = {"raw_stdout": result.stdout}
    ok = result.returncode == 0 and payload.get("ok", True) is not False
    return ok, payload, result.stderr.strip()


def result_rows(payload: dict) -> list[dict]:
    data = payload.get("data", payload)
    return data.get("results", data.get("files", [])) if isinstance(data, dict) else []


def product_terms(skill_dir: Path, product_id: str) -> list[str]:
    _, products = load_rows(skill_dir / "references" / "product_master.xlsx")
    _, aliases = load_rows(skill_dir / "references" / "product_aliases.xlsx")
    product = next((row for row in products if row.get("product_id") == product_id), None)
    if not product:
        raise ValueError(f"Unknown product_id: {product_id}")
    values = [product.get(key, "") for key in ("official_name_en", "official_name_ja", "official_name_zh", "short_name", "model_number")]
    values.extend(row.get("alias", "") for row in aliases if row.get("product_id") == product_id and row.get("usage_status") == "current")
    result, seen = [], set()
    for value in values:
        token = normalize_alias(value)
        if value and token not in seen:
            seen.add(token)
            result.append(value)
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--skill-dir", required=True)
    parser.add_argument("--product-id")
    parser.add_argument("--folder-token")
    parser.add_argument("--execute", action="store_true", help="Call Feishu read APIs; without this flag emit only the query plan.")
    parser.add_argument("--output")
    args = parser.parse_args()
    skill_dir = Path(args.skill_dir).resolve()
    folder = args.folder_token or default_folder(skill_dir / "config" / "product_mapping.yaml")
    _, products = load_rows(skill_dir / "references" / "product_master.xlsx")
    product_ids = [args.product_id] if args.product_id else [row["product_id"] for row in products]
    plan = []
    for product_id in product_ids:
        terms = product_terms(skill_dir, product_id)
        for term in terms[:2]:
            plan.append({"product_id": product_id, "query": term, "scope": "folder"})
            for suffix in ("仕様", "PR", "FAQ", "launch", "比較"):
                if len(plan) < len(product_ids) * 12:
                    plan.append({"product_id": product_id, "query": f"{term} {suffix}", "scope": "folder"})
    snapshot = {
        "schema_version": "1.0",
        "kind": "feishu_discovery",
        "generated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "folder_token": folder,
        "mode": "execute" if args.execute else "plan_only",
        "product_ids": product_ids,
        "query_plan": plan,
        "documents": [],
        "errors": [],
    }
    if args.execute:
        seen = set()
        commands = [["lark-cli", "drive", "files", "list", "--params", json.dumps({"folder_token": folder, "page_size": 200}), "--as", "user", "--format", "json"]]
        commands.extend([["lark-cli", "drive", "+search", "--query", item["query"], "--folder-tokens", folder, "--as", "user", "--format", "json"] for item in plan])
        for command in commands:
            ok, payload, stderr = run(command)
            if not ok:
                error = payload.get("error", {}) if isinstance(payload, dict) else {}
                snapshot["errors"].append({"command": command[2:4], "message": error.get("message") or stderr or payload})
                continue
            for row in result_rows(payload):
                token = row.get("token") or row.get("doc_token") or row.get("id")
                if not token or token in seen:
                    continue
                seen.add(token)
                snapshot["documents"].append({
                    "token": token,
                    "title": row.get("name") or row.get("title"),
                    "type": row.get("type") or row.get("doc_type"),
                    "url": row.get("url"),
                    "modified_time": row.get("modified_time") or row.get("edit_time") or row.get("updated_at"),
                    "source_scope": "registered_folder",
                })
        if snapshot["errors"]:
            snapshot["status"] = "partial" if snapshot["documents"] else "blocked"
        else:
            snapshot["status"] = "complete"
    else:
        snapshot["status"] = "planned"
    output = Path(args.output) if args.output else skill_dir / "snapshots" / f"feishu-discovery-{datetime.now().strftime('%Y%m%d-%H%M%S')}.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(snapshot, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"ok": not snapshot["errors"], "status": snapshot["status"], "documents": len(snapshot["documents"]), "output": str(output)}, ensure_ascii=False))
    return 0 if not snapshot["errors"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
