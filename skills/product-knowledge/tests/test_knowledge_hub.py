from __future__ import annotations

import csv
import json
import shutil
import subprocess
import sys
from pathlib import Path


SKILL_DIR = Path(__file__).resolve().parents[1]


def copy_skill(tmp_path: Path) -> Path:
    target = tmp_path / "product-knowledge"
    shutil.copytree(SKILL_DIR, target, ignore=shutil.ignore_patterns("__pycache__"))
    return target


def test_hub_builds_derived_marketing_knowledge(tmp_path: Path) -> None:
    skill = copy_skill(tmp_path)
    result = subprocess.run(
        [sys.executable, str(skill / "scripts" / "build_knowledge_hub.py"), "--skill-dir", str(skill), "--as-of", "2026-08-07", "--write-baseline-snapshot"],
        text=True, capture_output=True,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    with (skill / "knowledge" / "product_index.csv").open(encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    assert len(rows) == 18
    assert {row["product_id"] for row in rows} >= {"hub_3", "lock_ultra", "ai_mindclip"}
    mindclip = (skill / "knowledge" / "products" / "ai_mindclip.md").read_text(encoding="utf-8")
    assert "Channel Reuse" in mindclip
    assert "Approved Claim" in mindclip
    assert list((skill / "snapshots").glob("hub-baseline-*.json"))


def test_discovery_plan_uses_registered_feishu_folder(tmp_path: Path) -> None:
    skill = copy_skill(tmp_path)
    output = tmp_path / "plan.json"
    result = subprocess.run(
        [sys.executable, str(skill / "scripts" / "discover_feishu_sources.py"), "--skill-dir", str(skill), "--product-id", "hub_3", "--output", str(output)],
        text=True, capture_output=True,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    payload = json.loads(output.read_text(encoding="utf-8"))
    assert payload["status"] == "planned"
    assert payload["folder_token"] == "fldcnqu1zEMnHKiIO3ibO9Ad5Kb"
    assert any(item["query"] == "Hub 3" for item in payload["query_plan"])


def test_change_set_detects_new_and_modified_documents(tmp_path: Path) -> None:
    previous = tmp_path / "previous.json"
    current = tmp_path / "current.json"
    output = tmp_path / "change-set.json"
    previous.write_text(json.dumps({"documents": [{"token": "doc_1", "title": "Old", "modified_time": "1"}]}), encoding="utf-8")
    current.write_text(json.dumps({"documents": [{"token": "doc_1", "title": "Old", "modified_time": "2"}, {"token": "doc_2", "title": "New", "modified_time": "1"}]}), encoding="utf-8")
    result = subprocess.run(
        [sys.executable, str(SKILL_DIR / "scripts" / "build_change_set.py"), "--previous", str(previous), "--current", str(current), "--output", str(output)],
        text=True, capture_output=True,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    payload = json.loads(output.read_text(encoding="utf-8"))
    assert payload["summary"] == {"new": 1, "modified": 1, "not_seen": 0}
