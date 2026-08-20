from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))

from clean_marketing_data import apply_product_knowledge


def create_index(tmp_path: Path) -> Path:
    skill_dir = tmp_path / "product-knowledge"
    outputs = skill_dir / "outputs"
    outputs.mkdir(parents=True)
    payload = {
        "generated_at": "2026-07-30T00:00:00+09:00",
        "validation_status": "pass",
        "products": [
            {"product_id": "lock_ultra"},
            {"product_id": "hub_3"},
        ],
        "alias_lookup": {
            "Lock Ultra": ["lock_ultra"],
            "Hub 3": ["hub_3"],
        },
        "excluded_aliases": [
            {"alias": "Keypad Vision", "product_id": "keypad_vision_pro", "usage_status": "ambiguous"}
        ],
    }
    (outputs / "product_index.json").write_text(json.dumps(payload), encoding="utf-8")
    return skill_dir


def test_exact_product_is_resolved_and_raw_value_is_preserved(tmp_path: Path) -> None:
    skill = create_index(tmp_path)
    frame = pd.DataFrame({"product": ["Lock Ultra"], "spend": [100]})
    issues = []
    resolved, metadata = apply_product_knowledge(frame, issues, skill)
    assert resolved.loc[0, "product_raw"] == "Lock Ultra"
    assert resolved.loc[0, "product_id"] == "lock_ultra"
    assert resolved.loc[0, "product"] == "lock_ultra"
    assert metadata["recognition_rate"] == 1
    assert metadata["index_validation_status"] == "pass"
    assert metadata["resolution_status"] == "pass"
    assert metadata["product_analysis_allowed"] is True


def test_unknown_product_fails_closed(tmp_path: Path) -> None:
    skill = create_index(tmp_path)
    frame = pd.DataFrame({"product": ["Lock Ultra", "Imaginary Lock"]})
    issues = []
    resolved, metadata = apply_product_knowledge(frame, issues, skill)
    assert resolved.loc[0, "product_id"] == "lock_ultra"
    assert pd.isna(resolved.loc[1, "product_id"])
    assert resolved["product"].tolist() == ["Lock Ultra", "Imaginary Lock"]
    assert metadata["product_analysis_allowed"] is False
    assert metadata["validation_status"] == "pass"
    assert metadata["index_validation_status"] == "pass"
    assert metadata["resolution_status"] == "critical"
    assert metadata["unrecognized_products"] == ["Imaginary Lock"]


def test_ambiguous_product_fails_closed(tmp_path: Path) -> None:
    skill = create_index(tmp_path)
    frame = pd.DataFrame({"product": ["Keypad Vision"]})
    issues = []
    _, metadata = apply_product_knowledge(frame, issues, skill)
    assert metadata["product_analysis_allowed"] is False
    assert metadata["ambiguous_products"] == ["Keypad Vision"]


def test_missing_knowledge_base_fails_closed(tmp_path: Path) -> None:
    frame = pd.DataFrame({"product": ["Lock Ultra"]})
    issues = []
    _, metadata = apply_product_knowledge(frame, issues, tmp_path / "missing")
    assert metadata["validation_status"] == "critical"
    assert metadata["index_validation_status"] == "missing"
    assert metadata["product_analysis_allowed"] is False


def test_no_product_dimension_allows_channel_analysis(tmp_path: Path) -> None:
    frame = pd.DataFrame({"product": [pd.NA], "channel": ["Google Ads"]})
    issues = []
    _, metadata = apply_product_knowledge(frame, issues, tmp_path / "missing")
    assert metadata["validation_status"] == "not_applicable"
    assert metadata["product_analysis_allowed"] is True
