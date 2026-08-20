import csv
import hashlib
import importlib.util
import json
import subprocess
import sys
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "export_miaoda_bundle.py"
MULTICHANNEL_SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "export_multichannel_miaoda_bundle.py"


def load_module():
    spec = importlib.util.spec_from_file_location("export_miaoda_bundle", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader
    spec.loader.exec_module(module)
    return module


def test_coverage_status_aliases():
    module = load_module()
    assert module.coverage_status({"status": "部分完整"}) == "Partial"
    assert module.coverage_status({"coverage_status": "Complete"}) == "Complete"
    assert module.coverage_status({}) == "Unverified"


def test_export_bundle_is_traceable_and_private(tmp_path):
    dashboard = tmp_path / "dashboard"
    dashboard.mkdir()
    payload = {
        "meta": {"product": "Example", "market": "JP", "status": "部分完整"},
        "kpis": {}, "ratings": {}, "sentiments": {}, "executive": [],
        "quality": {"missing": 1},
        "voices": [{"review_id": "r1", "date": "2026-01-01", "source": "Amazon Japan", "rating": 2, "sentiment": "Strong Negative", "title": "x", "text": "本文", "url": "https://example.test/r1", "issues": ["brightness"], "values": [], "scenarios": [], "owner": "Product", "confidence": "High", "manual_review": True}],
        "issues": [{"name": "brightness", "count": 1}],
        "backlog": [{"Issue ID": "ISS-01"}],
        "marketing": [{"类型": "购买顾虑"}],
    }
    (dashboard / "dashboard_data.json").write_text(json.dumps(payload), encoding="utf-8")
    output = tmp_path / "bundle"
    subprocess.run([sys.executable, str(SCRIPT), "--dashboard-dir", str(dashboard), "--output", str(output)], check=True)
    manifest = json.loads((output / "manifest.json").read_text())
    assert manifest["coverage_status"] == "Partial"
    assert manifest["review_count"] == 1
    assert manifest["contains_personal_display_names"] is False
    for item in manifest["files"]:
        path = output / item["path"]
        assert hashlib.sha256(path.read_bytes()).hexdigest() == item["sha256"]
    with (output / "data" / "review.csv").open(encoding="utf-8-sig", newline="") as handle:
        row = next(csv.DictReader(handle))
    assert "reviewer_display_name" not in row
    assert row["review_id"] == "r1"


def test_multichannel_record_type_is_canonicalized():
    spec = importlib.util.spec_from_file_location("export_multichannel_miaoda_bundle", MULTICHANNEL_SCRIPT)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader
    spec.loader.exec_module(module)
    assert module.canonical_record_type("video_comment") == "comment"
    assert module.canonical_record_type("social_post") == "sns_post"
    assert module.canonical_record_type("ec_review") == "ec_review"


def test_multichannel_taxonomy_terms_are_atomic():
    spec = importlib.util.spec_from_file_location("export_multichannel_miaoda_bundle", MULTICHANNEL_SCRIPT)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader
    spec.loader.exec_module(module)
    assert module.split_terms("Display Quality; Content Capacity", "Display Quality", "") == [
        "Display Quality",
        "Content Capacity",
    ]
