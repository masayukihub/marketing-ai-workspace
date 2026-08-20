#!/usr/bin/env python3
"""Compare two Feishu discovery snapshots without changing canonical product facts."""

from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--previous", required=True, type=Path)
    parser.add_argument("--current", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    previous, current = load(args.previous), load(args.current)
    old = {row.get("token"): row for row in previous.get("documents", []) if row.get("token")}
    new = {row.get("token"): row for row in current.get("documents", []) if row.get("token")}
    changes = []
    for token, row in sorted(new.items()):
        prior = old.get(token)
        status = "new" if not prior else "modified" if any(row.get(key) != prior.get(key) for key in ("modified_time", "revision_id", "content_hash")) else "unchanged"
        if status != "unchanged":
            changes.append({"status": status, "token": token, "title": row.get("title"), "type": row.get("type"), "url": row.get("url"), "previous": prior, "current": row, "next_action": "extract_and_review"})
    for token, row in sorted(old.items()):
        if token not in new:
            changes.append({"status": "not_seen", "token": token, "title": row.get("title"), "type": row.get("type"), "url": row.get("url"), "next_action": "confirm_access_or_deprecation"})
    payload = {"schema_version": "1.0", "kind": "product_knowledge_change_set", "generated_at": datetime.now().astimezone().isoformat(timespec="seconds"), "previous_snapshot": str(args.previous), "current_snapshot": str(args.current), "changes": changes, "summary": {kind: sum(item["status"] == kind for item in changes) for kind in ("new", "modified", "not_seen")}}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    markdown = ["# Product Knowledge Change Set", "", f"- Previous: {args.previous}", f"- Current: {args.current}", "", "| Status | Document | Type | Next action |", "|---|---|---|---|"]
    markdown.extend(f"| {item['status']} | {item.get('title') or item['token']} | {item.get('type') or '-'} | {item['next_action']} |" for item in changes)
    args.output.with_suffix(".md").write_text("\n".join(markdown) + "\n", encoding="utf-8")
    print(json.dumps({"ok": True, "changes": len(changes), "output": str(args.output)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
