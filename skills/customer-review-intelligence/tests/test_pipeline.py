from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import yaml

SKILL = Path(__file__).resolve().parents[1]
SOURCE_WORKSPACE = SKILL
PRODUCT_KNOWLEDGE = SKILL.parent / "product-knowledge"


def test_import_pipeline_and_second_run_are_idempotent(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    (workspace / "config").mkdir(parents=True)
    for name in ("sources.yaml", "products.yaml", "taxonomy.yaml", "sentiment_rules.yaml"):
        (workspace / "config" / name).write_text((SOURCE_WORKSPACE / "config" / name).read_text(encoding="utf-8"), encoding="utf-8")
    input_path = tmp_path / "reviews.json"
    input_path.write_text(json.dumps([
        {
            "source": "amazon_jp",
            "source_review_id": "REALISTIC-1",
            "product_id": "hub_3",
            "review_url": "https://example.com/reviews/REALISTIC-1",
            "review_body": "設定は簡単で便利です",
            "rating": 5,
            "review_date": "2026-07-01",
        }
    ], ensure_ascii=False), encoding="utf-8")
    command = [
        sys.executable,
        str(SKILL / "scripts" / "run_review_intelligence.py"),
        "--workspace", str(workspace),
        "--product-knowledge-dir", str(PRODUCT_KNOWLEDGE),
        "--input", str(input_path),
    ]
    first = subprocess.run(command + ["--batch-id", "test-first"], text=True, capture_output=True)
    assert first.returncode == 0, first.stdout + first.stderr
    second = subprocess.run(command + ["--batch-id", "test-second"], text=True, capture_output=True)
    assert second.returncode == 0, second.stdout + second.stderr
    result = json.loads(second.stdout)
    assert result["incremental"]["unchanged"] == 1
    assert result["records"] == 1
    assert (workspace / "outputs" / "latest_review_summary.html").is_file()
    assert (workspace / "outputs" / "product_summary.csv").is_file()
    assert (workspace / "outputs" / "channel_comparison.csv").is_file()
    assert (workspace / "outputs" / "trend_analysis.csv").is_file()
    assert (workspace / "reports" / "biweekly" / "latest.md").is_file()
    manual_header = (workspace / "reports" / "manual_review" / "manual_review_queue.csv").read_text(encoding="utf-8-sig").splitlines()[0]
    assert "reviewer_display_name" not in manual_header
    state = json.loads((workspace / "state" / "last_success.json").read_text(encoding="utf-8"))
    assert state["record_count"] == 1
    assert state["incremental"]["unchanged"] == 1
    assert state["prior_success_batch"] == "test-first"
    manifest = json.loads((workspace / "raw" / "manifest-test-second.json").read_text(encoding="utf-8"))
    assert manifest["requested_window"]["prior_success_batch"] == "test-first"
    assert manifest["requested_window"]["date_from"]
    reviews_header = (workspace / "normalized" / "reviews.csv").read_text(encoding="utf-8-sig").splitlines()[0]
    assert "source_url" in reviews_header
