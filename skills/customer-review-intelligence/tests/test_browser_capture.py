from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "validate_browser_capture.py"


def test_x_browser_capture_can_never_be_complete(tmp_path: Path) -> None:
    shot = tmp_path / "frame.png"
    dom = tmp_path / "frame.txt"
    shot.write_bytes(b"png")
    dom.write_text("visible post", encoding="utf-8")
    sha = lambda path: hashlib.sha256(path.read_bytes()).hexdigest()
    manifest = {
        "schema_version": "1.0", "batch_id": "b", "product_id": "ai_art_canvas", "source": "x",
        "frames": [{
            "frame_id": "f1", "url": "https://x.com/search?q=test", "captured_at": "2026-08-03T10:00:00+09:00",
            "screenshot_path": str(shot), "screenshot_sha256": sha(shot),
            "dom_snapshot_path": str(dom), "dom_snapshot_sha256": sha(dom),
            "unique_ids_visible": ["1"], "status": "Captured",
        }],
        "unique_record_ids": ["1"], "failed_boundaries": [], "end_reached": True,
        "count_reconciled": True, "coverage_status": "Complete",
    }
    source = tmp_path / "manifest.json"
    output = tmp_path / "report.json"
    source.write_text(json.dumps(manifest), encoding="utf-8")
    completed = subprocess.run([sys.executable, str(SCRIPT), "--manifest", str(source), "--output", str(output)], check=True, capture_output=True, text=True)
    report = json.loads(output.read_text())
    assert report["computed_coverage_status"] == "Partial"
    assert any(item["code"] == "COMPLETE_NOT_SUPPORTED" for item in report["findings"])
